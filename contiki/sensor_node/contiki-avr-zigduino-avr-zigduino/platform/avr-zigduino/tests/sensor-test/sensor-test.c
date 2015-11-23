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

#define XBAND_PERIOD 30
#define ENV_INTERVAL 900
#define DEBUG_REFRESH 10
#define PIR_WAIT 30

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
long int xbandStarted = 0;
long int lastEnvReport = 0;
long int lastDebugRefresh = 0;

/*---------------------------------------------------------------------------*/
void
setupPins() {

    DDRE &= 0b00000000;
    DDRE |= 0b00000100;
    PORTE &= 0b00000000;

    /// ADC is PORT G

}
/*---------------------------------------------------------------------------*/
int
readPIR() { // PIR should be connected to digital pin 3

    return ( PINE & 0b00100000 ) ? 1 : 0;

}
/*---------------------------------------------------------------------------*/
int
readXBand() { // XBand should be connected to digital pin 2

    return ( PINE & 0b01000000 ) ? 1 : 0;

}
/*---------------------------------------------------------------------------*/
void
activateXBand() {

    PORTE |= 0b00000100;
    xbandActive = 1;

}
/*---------------------------------------------------------------------------*/
void
deactivateXBand() {

    PORTE &= 0b11111011;
    xbandActive = 0;

}
/*---------------------------------------------------------------------------*/
static void
reportPIRTrigger()
{
  char data[2];
  data[0] = 1; //Version
  data[1] = 2; //Type - Temperature Report
  uip_udp_packet_send(client_conn, data, sizeof(data));
  ++pirTriggers;
}
/*---------------------------------------------------------------------------*/
static void
reportXBandTrigger()
{
  char data[2];
  data[0] = 1; //Version
  data[1] = 3; //Type - Temperature Report
  uip_udp_packet_send(client_conn, data, sizeof(data));
  ++xbandTriggers;
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
    uip_ip6addr(&ip, 0xfd8d, 0xd5f9, 0x9279, 0x0001, 0, 0, 0, 0x0010);

    /* Create UDP connection to server */
    client_conn = udp_new(&ip, UIP_HTONS(3000), NULL);

    printf("\033[2J\033[?25l");
    
    for ( ;; ) {

	int pir = readPIR();
	int xband = readXBand();
	int temp = temperature_sensor.value(0);
	int tempH = temp / 100;
	int tempL = temp % 100;
	long int clock = clock_seconds();

	if ( xbandActive == 0 && pir > 0 && clock > xbandStarted + PIR_WAIT ) {
	    activateXBand();
	    reportPIRTrigger();
	    xbandStarted = clock;
	}

	if ( xbandActive == 1 && xband > 0 ) {
	    reportXBandTrigger();
	    deactivateXBand();
	}

	if ( xbandActive == 1 && ( clock > xbandStarted + XBAND_PERIOD ) ) {
	    deactivateXBand();
	}
	
	if ( ( clock % ENV_INTERVAL == 0 ) && ( clock > lastEnvReport ) ) {
	    reportTemperature(temp);
	    envReports += 1;
	    lastEnvReport = clock;
	}
	
	if ( ( clock % DEBUG_REFRESH == 0 ) && ( clock > lastDebugRefresh ) ) {
	    printf("\033[2J\033[?25l");
	    lastDebugRefresh = clock;
	}

	printf("\033[1;1H");
	printf("+-----------------------------------------------+\n");
	printf("| WiSE Sensor Node %d  Uptime: %10ld s      |\n", NODE, clock);
	printf("+-----------------------------------------------+\n");
	printf("| PIR Sensor:  %d	   <%s>	     |\n", pir, (xbandActive) ? "IGNORE" : "ACTIVE");
	printf("| XBand Radar: %d	   <%s>	     |\n", xband, ( xbandActive ) ? "ACTIVE" : "DISABL");
	printf("+-----------------------------------------------+\n");
	printf("| Onboard Temperature: %d.%d C		  |\n", tempH, tempL);
	printf("+-----------------------------------------------+\n");
	printf("| Communications Sent:			  |\n");
	printf("| PIR Triggers    |  %9d		  |\n", pirTriggers);
	printf("| XBand Triggers  |  %9d		  |\n", xbandTriggers);
	printf("| Env. Reports    |  %9d		  |\n", envReports);
	printf("+-----------------------------------------------+\n");
	printf("| Last Debug Refresh: %10ld		|\n", lastDebugRefresh);
	printf("| Last Env. Report:   %10ld		|\n", lastEnvReport);
	printf("+-----------------------------------------------+\n");

	PROCESS_PAUSE();

    }

    PROCESS_END();
}
/*---------------------------------------------------------------------------*/

