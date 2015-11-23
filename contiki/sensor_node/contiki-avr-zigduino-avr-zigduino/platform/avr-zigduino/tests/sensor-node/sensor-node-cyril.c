/*=============================================================================
#     FileName: EndDevice.c
#         Desc: This is the software to go on the end device.
#       Author: Cyril Danilevski
#        Email: cydanil@gmail.com
#     HomePage: http://www.erg.abdn.ac.uk/groups/wiseproject/
#      Version: 0.0.1
#   LastChange: 2012-09-05 14:59:49
#      History: Made it compile
===============================================================================
# I assume that you know that contiki is event driven. Thus, in the later documentation,
# an 'event' refers to a contiki event, and 'something happening' refers to a real-life
# event, where the sensors are triggered.
#
# It will wait for an event coming from the PIR, wait for a confirmation from the XBand
# and then send a UDP packet to the Camera node.
#
#
# The three processes are:
#     - PIR sends event to XBand
#     - XBand sends event UDP Process
#     - UDP sends packet when event is recieved
==============================================================================*/

/* System */
#include "contiki.h"
#include "contiki-lib.h"
#include "string.h"
#include "stdio.h"
#include "stdlib.h"


/* For networking */
#include "contiki-net.h"
#define MAX_PAYLOAD_LEN     40

/* For the sensors */
#include "lib/sensors.h"

/* Tools for debugging. It will print out the messages over serial. */
#define PRINTF(...) printf(__VA_ARGS__)
#define PRINT6ADDR(addr) PRINTF(" %02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x:%02x%02x ", ((uint8_t *)addr)[0], ((uint8_t *)addr)[1], ((uint8_t *)addr)[2], ((uint8_t *)addr)[3], ((uint8_t *)addr)[4], ((uint8_t *)addr)[5], ((uint8_t *)addr)[6], ((uint8_t *)addr)[7], ((uint8_t *)addr)[8], ((uint8_t *)addr)[9], ((uint8_t *)addr)[10], ((uint8_t *)addr)[11], ((uint8_t *)addr)[12], ((uint8_t *)addr)[13], ((uint8_t *)addr)[14], ((uint8_t *)addr)[15])

/* Global variables */
struct uip_udp_conn *client_conn;
const struct pir_sensor *pir;
const struct xband_sensor *xband;

static process_event_t pir_event;
static process_event_t xband_event;
static process_event_t battery_event;
static process_event_t monitor_event;

/* Processes setup */

/* Sensors */
char pir_desc[] = "PIR Activation Process";
char xband_desc[] = "XBand Activation Process";
PROCESS(pir_reader, pir_desc);
PROCESS(xband_reader, xband_desc);

/* Communication */
char monitor_desc[] = "Monitoring Process";
char udp_send_desc[] = "UDP Send";
PROCESS(monitor, monitor_desc);
PROCESS(udp_send, udp_send_desc);

AUTOSTART_PROCESSES(&pir_reader, &xband_reader, &monitor, &udp_send);

/*--------------------------  Functions  ---------------------------*/

void getDate(char *date){
    char d[16] = "Jan 01 00:00:01";
    strcpy(date, d);
}

void getIP(char *ip_addr){
     //strcpy(ip_addr, uip_debug_ipaddr_print(&ip->ipaddr));
}

char checkBattery(){
    return 0;
}

void checkTelemetry(char *msg){
    char t[] = "nil";
    strcpy(msg, t);
}


void syslog(char *log[], char *str[]){
    char level;
    char *date;
    char *ip_addr;
    char *msg;
    getIP(ip_addr);
    getDate(date);

    if(str == xband_desc){
        level = '1';
        msg = "XBand activated";
    }
    if(str == monitor_desc){
        checkTelemetry(msg);
    }
    
    strcpy(log, sprintf("<%s> %s %s %s", level, date, ip_addr, msg));
}

/*--------------------------  PIR  ---------------------------*/

PROCESS_THREAD(pir_reader, ev, data){
    PROCESS_BEGIN();
    /* for debugging purposes. */
    //SENSORS_ACTIVATE(pir_sensor);
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

/*------------------------  XBAND  --------------------------*/

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
                /* yield the data to the monitoring process. */
                process_post_synch(&monitor, xband_event, "pir+xband");
            }
        }
    }
    PROCESS_END();
}

/*------------------------  MONITOR  ------------------------*/

char informations[];
PROCESS_THREAD(monitor, ev, data){
    PROCESS_BEGIN();
    monitor_event = process_alloc_event();

    for(;;){
        PROCESS_WAIT_EVENT();
        if(ev == sensors_event){
            if(data == &xband){
                syslog(&informations, &xband_desc);
            }
        }
        process_post_synch(&udp_send, monitor_event, informations);
    }
    PROCESS_END();
}

/*---------------------  NETWORKING  ------------------------*/

void set_connection_address(uip_ipaddr_t *ipaddr){
        /* Set the IPv6 address to connect to. */
        uip_ip6addr(ipaddr,0xfe80,0,0,0,0x11,0x22ff,0xfe33,0x4402);
}

PROCESS_THREAD(udp_send, ev, data){
    uip_ipaddr_t ip;
    uip_ip6addr(&ip,0xfe80,0,0,0,0x11,0x22ff,0xfe33,0x4402);

    PROCESS_BEGIN();
    /* Create a new connection to the remote host.
     * Takes as arguments: the remote ip address,
     * the port (to be converted in order to go accross the network),
     * and the data to send.
     */
    client_conn = udp_new(&ip, UIP_HTONS(3000), NULL);
    udp_bind(client_conn, UIP_HTONS(3001));

    for(;;){
        PROCESS_WAIT_EVENT_UNTIL(ev == monitor_event);
        uip_send(data, sizeof(data));
    }

    PROCESS_END();
}
