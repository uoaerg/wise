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
 * This file contains the common function implementations for CoAP applications.
 *
 * $Id:$
 *
 */

#include <stdint.h>
#include <string.h>

#include "coap.h"

/**
 * Next CoAP message ID.
 */
static uint16_t coap_message_id = 1;

void coap_msg_init(coap_msg* msg, uint8_t code){

	msg->buffer[0] = 1 << 6; // Set CoAP version to 1
	msg->buffer[1] = code; // Set CoAP code

	msg->buffer[2] = coap_message_id >> 8; // Set CoAP message ID
	msg->buffer[3] = coap_message_id & 0xff;
	coap_message_id++;

	msg->len = 4;

	msg->lastopc = 0; // Reset option delta
}

void coap_msg_set_type(coap_msg* msg, uint8_t type){
	msg->buffer[0] &= 0xcf; // Clear existing type
	msg->buffer[0] |= type << 4; // Set new type
}

void coap_msg_set_token(coap_msg* msg, uint8_t len, uint8_t* token){
	int i;

	msg->buffer[0] &= 0xf0; // Clear existing token length
	msg->buffer[0] |= len; // Set new token length
	
	msg->len = 4; // Reset message length

	for ( i = 0 ; i < len ; ++i ){
		msg->buffer[msg->len + i] = token[i];
	}

	msg->len += len; // Update message length

	msg->lastopc = 0; // Reset option delta
}

void coap_msg_set_uri(coap_msg* msg, char* uri){
	int i, j, p;

	char* port;

	if ( uri[0] == 'c' && uri[1] == 'o' && uri[2] == 'a' && uri[3] == 'p' &&
		uri[4] == ':' && uri[5] == '/' && uri[6] == '/' )
		i = 7;
	else return; // There's really not much I can do if that failed

	for ( j = 0 ; ; ++j ){
		if ( uri[i+j] == '\0' ) { p = 0; break; }
		if ( uri[i+j] == ':' ) 	{ p = 1; uri[i+j] = '\0'; break; }
		if ( uri[i+j] == '/' )  { p = 2; uri[i+j] = '\0'; break; }
	}

	coap_msg_add_option(msg, 3, &uri[i]); // Add Uri-Host option to CoAP message

	i += j + 1; // Update pointer
	j = 0; // Reset

	if ( p == 1 ){
		for ( ; ; ++j ){
			if ( uri[i+j] == '\0' ) { p = 0; break; }
			if ( uri[i+j] == '/' )  { p = 2; uri[i+j] = '\0'; break; }
		}
		port = &uri[i];
	}else{
		port = "5683";
	}

	coap_msg_add_option(msg, 7, port); // Add Uri-Port option to CoAP message

	i += j + 1; // Update pointer

	if ( p == 2 ){
		coap_msg_add_option(msg, 11, &uri[i]);
	}else{
		coap_msg_add_option(msg, 11, "");
	}
}

void coap_msg_add_param(coap_msg* msg, char* name, char* value){
	char opval[255];
	int i, j;

	for ( i = 0 ; i < strlen(name) ; ++i )
		opval[i] = name[i];

	opval[i++] = '=';

	for ( j = 0 ; j < strlen(value); ++j )
		opval[i+j] = value[j];

	opval[i+j] = '\0'; // Terminate string

	coap_msg_add_option(msg, 15, opval);
}

void coap_msg_add_payload(coap_msg* msg, uint8_t len, uint8_t* payload){
	// Actually, don't care about this. Maybe later?	
}

void coap_msg_add_option(coap_msg* msg, uint8_t opc, char* value){
	int i;
	
	msg->buffer[msg->len] = (opc - msg->lastopc) << 4;
	msg->buffer[msg->len] |= strlen(value);

	msg->lastopc = opc;

	msg->len++;

	for ( i = 0 ; i < strlen(value) ; ++i )
		msg->buffer[msg->len++] = value[i];
}

