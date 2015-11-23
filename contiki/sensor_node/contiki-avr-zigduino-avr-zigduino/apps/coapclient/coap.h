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
 * This file contains the common data structures and function prototypes for CoAP
 * applications.
 *
 * $Id:$
 *
 */

#include <stdint.h>

/**
 * CoAP message is a confirmable message.
 */
#define COAP_TYPE_CONFIRMABLE 0

/**
 * CoAP message is a non-confirmable message.
 */
#define COAP_TYPE_NONCONFIRMABLE 1

/**
 * CoAP message is an acknowledgement message.
 */
#define COAP_TYPE_ACKNOWLEDGEMENT 2

/**
 * CoAP message is a reset message.
 */
#define COAP_TYPE_RESET 3

/**
 * CoAP message is a GET request.
 */
#define COAP_CODE_REQ_GET 1

/**
 * CoAP message is a POST request.
 */
#define COAP_CODE_REQ_POST 2

/**
 * CoAP message is a PUT request.
 */
#define COAP_CODE_REQ_PUT 3

/**
 * CoAP message is a DELETE request.
 */
#define COAP_CODE_REQ_DELETE 4

/**
 * CoAP message structure.
 *
 * To build a CoAP request, use the following sequence of function calls:
 *
 * * coap_msg_init()
 * * coap_msg_set_token() - optional
 * * coap_msg_set_uri()
 * * coap_msg_add_param()
 * * coap_msg_add_payload()
 */
typedef struct coap_msg_t {
	int len;
	uint8_t buffer[255];
	uint8_t lastopc;
} coap_msg;

/**
 * Initialise a CoAP message.
 *
 * This function initialises a CoAP message structure. The value for code should
 * be one of:
 *
 * * COAP_CODE_REQ_GET
 * * COAP_CODE_REQ_POST
 * * COAP_CODE_REQ_PUT
 * * COAP_CODE_REQ_DELETE
 *
 * @param msg CoAP message structure
 * @param code CoAP Message Code
 */
void coap_msg_init(coap_msg* msg, uint8_t code);

/**
 * Set the type of a CoAP message.
 *
 * This function sets the type of a CoAP message. The value for type should be one of:
 *
 * * COAP_TYPE_CONFIRMABLE
 * * COAP_TYPE_NONCONFIRMABLE
 * * COAP_TYPE_ACKNOWLEDGEMENT
 * * COAP_TYPE_RESET
 *
 * @param msg CoAP message structure
 * @param type CoAP Message Type
 */
void coap_msg_set_type(coap_msg* msg, uint8_t type);

/**
 * Set the token of a CoAP message.
 *
 * @param msg CoAP message structure
 * @param len CoAP token length
 * @param token CoAP Token
 */
void coap_msg_set_token(coap_msg* msg, uint8_t len, uint8_t* token);

/**
 * Set the destination for the CoAP message by URI.
 *
 * @param msg CoAP message structure
 * @param uri CoAP URI
 */
void coap_msg_set_uri(coap_msg* msg, char* uri);

/**
 * Add a parameter to a CoAP request message.
 *
 * @param msg CoAP message structure
 * @param name parameter name
 * @param value parameter value
 */
void coap_msg_add_param(coap_msg* msg, char* name, char* value);

/**
 * Add the payload to a CoAP message.
 *
 * This function adds the payload to a CoAP message. This function should only
 * be called once the destination of the message and any parameters have been
 * set in the CoAP message structure.
 *
 * @param msg CoAP message structure
 * @param len payload length
 * @param payload the payload
 */
void coap_msg_add_payload(coap_msg* msg, uint8_t len, uint8_t* payload);

/**
 * Add an option to the CoAP message.
 *
 * This function should not be called directly but is used by coap_msg_set_uri(),
 * coap_msg_set_uri() and coap_msg_add_param().
 *
 * @param msg CoAP message structure
 * @param opc CoAP option code
 * @param value Option value
 */
void coap_msg_add_option(coap_msg* msg, uint8_t opc, char* value);


