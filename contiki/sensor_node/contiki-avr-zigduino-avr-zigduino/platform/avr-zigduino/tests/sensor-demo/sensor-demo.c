//
//
//
// Expected Connections:
//
//   Pin 2: XBand Output
//   Pin 3: PIR Output
//   Pin 4: XBand Enable
//
//
//

#define ENV_INTERVAL 60
#define DEBUG_REFRESH 10
#define XBAND_WAIT 30

#include <avr/io.h>
#include "contiki.h"

#include "dev/temperature-sensor.h"

#include <stdio.h> /* For printf() */
#include <string.h>

#include "contiki-net.h"
#include "cfs/cfs.h"
#include "lib/petsciiconv.h"

static struct uip_udp_conn *client_conn;

int pirTriggers = 0;
int xbandTriggers = 0;
int envReports = 0;
int xbandActive = 0;
long int lastXBandTrigger = 0 - XBAND_WAIT;
long int lastEnvReport = 0 - ENV_INTERVAL;
long int lastDebugRefresh = 0 - DEBUG_REFRESH;

/*---------------------------------------------------------------------------*/
void
setupPins() {
    DDRE  = 0b00000000;
    PORTE = 0b00000000;
}
/*---------------------------------------------------------------------------*/
int
readXBand() { // XBand should be connected to digital pin 2, XBand enable should be tied to 5 volt line
    return ( PINE & 0b01000000 ) ? 1 : 0;
}
/*---------------------------------------------------------------------------*/
static void
reportXBandTrigger(void)
{
    if ( clock_seconds() > lastXBandTrigger + XBAND_WAIT ) {
        char data[2];
        data[0] = 1; //Version
        data[1] = 3; //Type - XBand Trigger
        uip_udp_packet_send(client_conn, data, sizeof(data));
        xbandTriggers += 1;
        lastXBandTrigger = clock_seconds();
    }
}
/*---------------------------------------------------------------------------*/
static void
reportTemperature(int tempValue)
{
  char data[10];
  data[0] = 1; //Version
  data[1] = 1; //Type - Temperature Report
  sprintf(&(data[2]), "%d", tempValue);
  uip_udp_packet_send(client_conn, data, sizeof(data));
}
/*---------------------------------------------------------------------------*/
PROCESS(main_process, "Main process");
AUTOSTART_PROCESSES(&main_process);
/*---------------------------------------------------------------------------*/
PROCESS_THREAD(main_process, ev, data)
{
    PROCESS_BEGIN();


    clock_init();
    setupPins();

    /* IP address to report to */
    uip_ipaddr_t ip;
    uip_ip6addr(&ip, 0xfd8d, 0xd5f9, 0x9279, 0x0001, 0, 0, 0, 0x0001);

    /* Create UDP connection to server */
    client_conn = udp_new(&ip, UIP_HTONS(3000), NULL);

    for ( ;; ) {

        int xband = readXBand();
        int temp = temperature_sensor.value(0);
        int tempH = temp / 100;
        int tempL = temp % 100;
        long int clock = clock_seconds();

        if ( xband > 0 ) {
            reportXBandTrigger();
        }

        if ( ( clock % ENV_INTERVAL == 0 ) && ( clock > lastEnvReport ) ) {
            reportTemperature(temp);
            envReports += 1;
            lastEnvReport = clock;
        }
        
        if ( ( clock % DEBUG_REFRESH == 0 ) && ( clock > lastDebugRefresh ) ) {
            printf("\033[2J\033[?25l"); // Clear the screen
            lastDebugRefresh = clock;
        }

        printf("\033[1;1H"); // Reset cursor to 1,1 on terminal
        printf("+-----------------------------------------------+\n");
        printf("| WiSE Sensor Node %d  Uptime: %10ld s      |\n", NODE, clock);
        printf("+-----------------------------------------------+\n");
        printf("| XBand Radar: %d                                |\n", xband);
        printf("+-----------------------------------------------+\n");
        printf("| Onboard Temperature: %d.%d C                  |\n", tempH, tempL);
        printf("+-----------------------------------------------+\n");
        printf("| Communications Sent:                          |\n");
        printf("| XBand Triggers  |  %9d                  |\n", xbandTriggers);
        printf("| Env. Reports    |  %9d                  |\n", envReports);
        printf("+-----------------------------------------------+\n");

        PROCESS_PAUSE();

    }

    PROCESS_END();
}
/*---------------------------------------------------------------------------*/

