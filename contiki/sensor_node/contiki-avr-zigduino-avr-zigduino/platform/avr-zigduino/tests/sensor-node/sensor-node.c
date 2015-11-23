/*
 * Copyright (c) 2002, Adam Dunkels.
 * All rights reserved. 
 *
 * Redistribution and use in source and binary forms, with or without 
 * modification, are permitted provided that the following conditions 
 * are met: 
 * 1. Redistributions of source code must retain the above copyright 
 *    notice, this list of conditions and the following disclaimer. 
 * 2. Redistributions in binary form must reproduce the above
 *    copyright notice, this list of conditions and the following
 *    disclaimer in the documentation and/or other materials provided
 *    with the distribution. 
 * 3. The name of the author may not be used to endorse or promote
 *    products derived from this software without specific prior
 *    written permission.  
 *
 * THIS SOFTWARE IS PROVIDED BY THE AUTHOR ``AS IS'' AND ANY EXPRESS
 * OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
 * WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
 * ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY
 * DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE
 * GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
 * INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
 * WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
 * NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
 * SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.  
 *
 * This file is part of the Contiki desktop environment
 *
 * $Id: wget.c,v 1.4 2010/10/31 22:43:06 oliverschmidt Exp $
 *
 */

#include <stdio.h>
#include <string.h>

#include <avr/io.h>

#include "contiki-net.h"
#include "cfs/cfs.h"
#include "lib/petsciiconv.h"

#include "dev/temperature-sensor.h"

PROCESS(temperature_process, "Temperature");

AUTOSTART_PROCESSES(&temperature_process);

static struct uip_udp_conn *client_conn;

static void
report_temperature(void)
{

  /* Get temperature sensor reading */
  int tempValue = 0; //temperature_sensor.value(0);

  /* Get current "time" */
  int clockSeconds = clock_seconds();

  /* Print on serial output */
  printf("Time: %d\tTemperature: %d\n", clockSeconds, tempValue);

  char data[10];
  data[0] = 1; //Version
  data[1] = 1; //Type - Temperature Report
  sprintf(&(data[2]), "%d", tempValue);
  uip_udp_packet_send(client_conn, data, sizeof(data));
}
/*-----------------------------------------------------------------------------------*/
PROCESS_THREAD(temperature_process, ev, data)
{
  PROCESS_BEGIN();

  PROCESS_PAUSE();

  static int interval = 3;
  static struct etimer et;
  
  /* IP address to report to */
  uip_ipaddr_t ip;
  uip_ip6addr(&ip, 0xfd8d, 0xd5f9, 0x9279, 0x0001, 0, 0, 0, 0x0001);

  /* Create UDP connection to server */
  client_conn = udp_new(&ip, UIP_HTONS(3000), NULL);
  printf("local/remote port %u/%u\n", UIP_HTONS(client_conn->lport), UIP_HTONS(client_conn->rport));

  etimer_set(&et, CLOCK_SECOND*interval);

  while(1) {

    PROCESS_WAIT_EVENT();
  
    //if(ev == tcpip_event) {
    //  Handle incoming packets
    //}

    if(etimer_expired(&et)) {
      report_temperature();
      etimer_reset(&et);
    }

  }

  PROCESS_END();
}

