/*
 * Cyril Danilevski 20/08/2012
 * Last Update: 21/08/2012 By: Cyril
 *
 * CameraDevice.c .
 * This is the software to go onto the camera device.
 *
 * I assume that you know that contiki is event driven. Thus, in the later documentation,
 * an 'event' refers to a contiki event, and 'something happening' refers to a real-life
 * event, where the sensors are triggered.
 *
 * It will wait for the confirmation from two independent sources that something is 
 * happening. In this scenario, I expect the camera device to have its own sensors,
 * in the same configuration as the end devices.
 *
 * It will wait for the PIR to be triggered, wait for a confirmation from the XBand
 * and then send an event. 
 *
 *
 * The n processes are:
 *     - Detecting:
 *          - PIR sends event to XBand
 *          - XBand sends event to main control
 *     - Taking a picture:
 *          - Wait for at least 2 independent inputs (local or remote)
 *          - Snap a picture and save it to the SD card
 *
 */

/* System */
#include "contiki.h"
#include "contiki-lib.h"
#include <string.h>
#include <stdio.h>

/* For networking */
#include "contiki-net.h"
#define MAX_PAYLOAD_LEN     120

/* For the sensors */
#include "lib/sensors.h"
#include "wise/pir-sensor.h"
#include "wise/xband-sensor.h"

/* Tools for debugging. It will print out the messages over serial. */
#define PRINTF(...) printf(__VA_ARGS__)
#define PRINT6ADDR(addr) PRINTF(" %02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x ", ((u8_t *)addr)[0], ((u8_t *)addr)[1], ((u8_t *)addr)[2], ((u8_t *)addr)[3], ((u8_t *)addr)[4], ((u8_t *)addr)[5], ((u8_t *)addr)[6], ((u8_t *)addr)[7], ((u8_t *)addr)[8], ((u8_t *)addr)[9], ((u8_t *)addr)[10], ((u8_t *)addr)[11], ((u8_t *)addr)[12], ((u8_t *)addr)[13], ((u8_t *)addr)[14], ((u8_t *)addr)[15])



/*------------------------------------------------------------*/

// The following creates a uip udp struct. It will be use
// to create a udp packet. This comes from the contiki-net header.
static strucy uip_udp_conn *client_conn;
static struct uip_udp_conn *server_conn;
static process_event_t pir_event;
static process_event_t xband_event;

// The following creates two proccesses, one for udp connectivity
// one for reading from the PIR.

PROCESS(udp_client, "UDP Client Process");
PROCESS(udp_server, "UDP Server Process");
PROCESS(pir_reader, "PIR Activation Process");
PROCESS(xband_reader, "XBand Activation Process");
AUTOSTART_PROCESSES(&udp_server, &pir_reader, &xband_reader);
/*-----------------------------------------------------------*/

static void print_packet(void){
    //This method is used for debugging and will print
    //the content of the packet on the serial port.
    char *string;
    
    if(uip_newdata()){
        string = uip_appdata;
        string[uip_datalen()] = '\0';

        PRINTF("Got: '%s'\n", string);
    }
}


static void print_local_addresses(void){
    /* This method is used for debugging and will print
     * the ip addresses of known nodes.
     * It is also a test of using the uip-ds6.c and see
     * how well can I master that.
     */

    int i;
    uint8_t state;
    PRINTF("Clients IPv6 Adresses: ");
    for(i = 0; i < UIP_DS6_ADDR_NB; ++i){
        state = uip_ds6_if.addr_list[i].state;
        if(uip_ds6_if.addr_list[i].isused &&
        (state == ADDR_TENTATIVE || state == ADDR_PREFERRED)){
            PRINT6ADDR(&uip_ds6_if.addr_list[i].ipaddr);
            PRINTF("\n");
        }
    }
}


#if UIP_CONF_ROUTER
static void set_global_address(void){
    //This method is used if the node is to be a router.
    //which, in my tests, it will be.
    uip_ipaddr_t ipaddr;

    uip_ip6addr(&ipaddr, 0xaaaa, 0, 0, 0, 0, 0, 0, 0);
    uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
    uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);
}
#endif /* UIP_CONF_ROUTER */


static void set_connection_address(uip_ipaddr_t *ipaddr){
    /* This method is used to set what address the process has to connect to. */
#define _QUOTEME(x) #x
#define QUOTEME(x) _QUOTEME(x)
#ifdef UDP_CONNECTION_ADDR

      if(uiplib_ipaddrconv(QUOTEME(UDP_CONNECTION_ADDR), ipaddr) == 0){
        PRINTF("UDP client failed to parse address '%s'\n", QUOTEME(UDP_CONNECTION_ADDR));
      }
        /* Here is set the IPv6 address of the node.
         * If the device is a router, change the UIP_CONF_ROUTER settings.
         * Otherwise, change the bottom line.
         */
#elif UIP_CONF_ROUTER
        uip_ip6addr(ipaddr,0xaaaa,0,0,0,0x0212,0x7404,0x0004,0x0404);
#else
        uip_ip6addr(ipaddr,0xfe80,0,0,0,0x11,0x22ff,0xfe33,0x4402);
#endif /* UDP_CONNECTION_ADDR */
}

/*-------------------------------------------------------------------*/

PROCESS_THREAD(udp_client, ev, data){
    uip_ipaddr_t ip;

    PROCESS_BEGIN();
    PRINTF("UDP client started\n");

#if UIP_CONF_ROUTER /* Is a router */
    set_global_address();
#endif

    print_local_addresses();
    set_connection_address(&ip);

    /* Create a new connection to the remote host.
     * Takes as arguments: the remote ip address,
     * the port (to be converted in order to go accross the network),
     * and the data to send.
     */
    client_conn = udp_new(&ip, UIP_HTONS(3000), NULL);
    udp_bind(client_conn, UIP_HTONS(3001));

    PRINTF("Connected to ");
    PRINT6ADDR(&client_conn->ripaddr);
    PRINTF(" on ports (l/r) %u/%u\n",
            UIP_HTONS(client_conn->lport), UIP_HTONS(client_conn->rport));


    /*Now comes the actual algorithm for sending data accross the network.
     * TODO: 
     * http://contiki.sourceforge.net/docs/2.6/a01793.html#ga04b053a623aac7cd4195157d470661b3
     * uip_send("hello", 5);
     */

    for(;;){
        PROCESS_WAIT_EVENT_UNTIL(ev == xband_event);
        uip_send(data, sizeof(data));
    }

    PROCESS_END();
}
/*-----------------------------------------------------------------*/

PROCESS_THREAD(udp_server, ev, data){
#if UIP_CONF_ROUTER
    uip_ipaddr_t ipaddr;
#endif /* UIP_CONF_ROUTER */

    PROCESS_BEGIN();
    PRINTF("UDP server started\n");

#if UIP_CONF_ROUTER
    uip_ip6addr(&ipaddr, 0xaaaa, 0, 0, 0, 0, 0, 0, 0);
    uip_ds6_set_addr_iid(&ipaddr, &uip_lladdr);
    uip_ds6_addr_add(&ipaddr, 0, ADDR_AUTOCONF);
#endif /* UIP_CONF_ROUTER */

    print_local_addresses();

    server_conn = udp_new(NULL, UIP_HTONS(3001), NULL);
    upd_bind(server_conn, UIP_HTONS(3000));

    for(;;){
        PROCESS_YIELD();
        if(ev == tcpip_event){
            //do shit, camera trigger, & report to higher authorities.
            continue;
        }
    }

    PROCESS_END();
}


/*-----------------------------------------------------------------*/

const struct pir_sensor *pir;

PROCESS_THREAD(pir_reader, ev, data){
    PROCESS_BEGIN();
    /* for debugging purposes. */
    PRINTF("+++++++++++++++\n");
    PRINTF("PIR process started\n");
    /* The following calls pir_sensor.h and activates it. It is a system tool. */
    SENSORS_ACTIVATE(pir_sensor);
    pir_event = process_alloc_event(); /* allocates an event to the process. */

    for(;;){
        PROCESS_WAIT_EVENT();

        if(ev == sensors_event){
            if(data == &pir){
                /* yield the data to the xband process. */
                process_post_synch(&xband_reader, pir_event, "pir");
            }
        }
    }
    PROCESS_END();
}

/*------------------------------------------------------------------*/
const struct xband_sensor *xband;

PROCESS_THREAD(xband_reader, ev, data){
    PROCESS_BEGIN();
    /* for debugging purposes. */
    PRINTF("+++++++++++++++\n");
    PRINTF("XBand process started\n");
    /* The following calls xband_sensor.h and activates it. It is a system tool. */
    //?SENSORS_ACTIVATE(xband_sensor);
    xband_event = process_alloc_event(); /* allocates an event to the process. */

    for(;;){
        PROCESS_WAIT_EVENT_UNTIL(ev == pir_event);

        PROCESS_WAIT_EVENT();
        if(ev == sensors_event){
            if(data == &xband){
                /* yield the data to the udp process. */
                process_post_synch(&udp_client, xband_event, "pir+xband");
            }
        }
    }
    PROCESS_END();
}
