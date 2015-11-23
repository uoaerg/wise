/*
 * Cyril Danilevski 13/08/2012
 * Last Update: 22/08/2012 By: Cyril
 *
 * EndDevice.c .
 * This is the software to go on the end device.
 *
 * I assume that you know that contiki is event driven. Thus, in the later documentation,
 * an 'event' refers to a contiki event, and 'something happening' refers to a real-life
 * event, where the sensors are triggered.
 *
 * It will wait for an event coming from the PIR, wait for a confirmation from the XBand
 * and then send a UDP packet to the Camera node.
 *
 *
 * The three processes are:
 *     - PIR sends event to XBand
 *     - XBand sends event UDP Process
 *     - UDP sends packet when event is recieved
 *
 * For the moment, it compiles to 220kb, which is too big to fit on the ATmega128RFA1,
 * but I *believe* that's due to stdio.h. That won't be required once oneboard.
 */

/* System */
#include "contiki.h"
#include "contiki-lib.h"
#include <string.h>
#include <stdio.h>

/* For networking */
#include "contiki-net.h"
#define MAX_PAYLOAD_LEN     40

/* For the sensors */
#include "lib/sensors.h"
#include "wise/pir-sensor.h"
#include "wise/xband-sensor.h"

/* Tools for debugging. It will print out the messages over serial. */
#define PRINTF(...) printf(__VA_ARGS__)
#define PRINT6ADDR(addr) PRINTF(" %02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x ", ((u8_t *)addr)[0], ((u8_t *)addr)[1], ((u8_t *)addr)[2], ((u8_t *)addr)[3], ((u8_t *)addr)[4], ((u8_t *)addr)[5], ((u8_t *)addr)[6], ((u8_t *)addr)[7], ((u8_t *)addr)[8], ((u8_t *)addr)[9], ((u8_t *)addr)[10], ((u8_t *)addr)[11], ((u8_t *)addr)[12], ((u8_t *)addr)[13], ((u8_t *)addr)[14], ((u8_t *)addr)[15])

/* Global variables */
static struct uip_udp_conn *client_conn;
const struct pir_sensor *pir;
const struct xband_sensor *xband;

static process_event_t pir_event;
static process_event_t xband_event;
static process_event_t battery_event;
static process_event_t rtc_event;
static process_event_t temperature_event;
static process_event_t monitor_event;

/* Processes setup */

/* Sensors */
PROCESS(pir_reader, "PIR Activation Process");
PROCESS(xband_reader, "XBand Activation Process");
PROCESS(photocell_reader, "Photocell Information Process");

/* Monitoring */
PROCESS(rtc_reader, "RTC Information Process");
PROCESS(sd_writer, "SD Card Process");
PROCESS(temp, "Temperature Information Process");

/* Communication */
PROCESS(monitor, "Monitoring Process");
PROCESS(udp_send, "UDP Send");

/*--------------------------  PIR  ---------------------------*/

PROCESS_THREAD(pir_reader, ev, data);{
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

/*-----------------------------------------------------------*/

PROCESS_THREAD(xband_reader, ev, data);{
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
                /* yield the data to the monitoring process. */
                process_post_synch(&monitor, xband_event, "pir+xband");
            }
        }
    }
    PROCESS_END();
}

/*-----------------------------------------------------------*/

PROCESS_THREAD(photocell_reader, ev, data);{

}

/*-----------------------------------------------------------*/

PROCESS_THREAD(rtc_reader, ev, data);{}

/*-----------------------------------------------------------*/

PROCESS_THREAD(sd_writer, ev, data);{}

/*-----------------------------------------------------------*/

PROCESS_THREAD(temp, ev, data);{}

/*------------------------  MONITOR  ------------------------*/

PROCESS_THREAD(monitor, ev, data);{
	PROCESS_BEGIN();
	/* for debugging purposes. */
    PRINTF("+++++++++++++++\n");
    PRINTF("Monitor Process started\n");
    monitor_event = process_alloc_event();

    for(;;){
    	PROCESS_WAIT_EVENT();
    	switch(ev){
    		case &xband_event:
    			break;
    		default:
    			continue;
    	}
    }
}

/*---------------------  NETWORKING  ------------------------*/

static void set_connection_address(uip_ipaddr_t *ipaddr){
    /* This method is used to set what address the process has to connect to. */
#define _QUOTEME(x) #x
#define QUOTEME(x) _QUOTEME(x)
#ifdef UDP_CONNECTION_ADDR

      if(uiplib_ipaddrconv(QUOTEME(UDP_CONNECTION_ADDR), ipaddr) == 0){
        PRINTF("UDP client failed to parse address '%s'\n", QUOTEME(UDP_CONNECTION_ADDR));
      }
        /* Set the IPv6 address to connect to. */
        uip_ip6addr(ipaddr,0xfe80,0,0,0,0x11,0x22ff,0xfe33,0x4402);
}

PROCESS_THREAD(udp_send, ev, data);{
	uip_ipaddr_t ip;

    PROCESS_BEGIN();
    PRINTF("UDP Send started\n");

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

    /* That sends the packet, I have yet to implement the syslog here */
    for(;;){
        PROCESS_WAIT_EVENT_UNTIL(ev == monitor_event);
        uip_send(data, sizeof(data));
    }

    PROCESS_END();
}
