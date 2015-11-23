/**
 * @file
 * @author  Iain Learmonth <iain.learmonth.09@aberdeen.ac.uk>
 * @version 0.1
 *
 * @section LICENSE
 *
 * This program is the intellectual property of the Computing Science Department
 * of the University of Aberdeen.
 *
 * @section DESCRIPTION
 *
 * This file contains a Contiki description for the CoAP client application.
 *
 * $Id:$
 *
 */

#include "sys/dsc.h"
/*-----------------------------------------------------------------------------------*/
#if CTK_CONF_ICON_BITMAPS
static unsigned char coapclienticon_bitmap[3*3*8] = {
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,

  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
};
#endif /* CTK_CONF_ICON_BITMAPS */

#if CTK_CONF_ICON_TEXTMAPS
static char coapclienticon_textmap[9] = {
  'C', 'o', '\',
  '\', 'A', 'P',
  '\', '\', '\'
};
#endif /* CTK_CONF_ICON_TEXTMAPS */

#if CTK_CONF_ICONS
static struct ctk_icon webserver_icon =
  {CTK_ICON("Coap client", coapclienticon_bitmap, coapclienticon_textmap)};
#endif /* CTK_CONF_ICONS */
/*-----------------------------------------------------------------------------------*/
DSC(coapclient_dsc,
    "The CoAP Client",
    "coapclient.prg",
    coapclient_process,
    &coapclient_icon);
/*-----------------------------------------------------------------------------------*/
