/*=============================================================================
#     FileName: uart.c
#         Desc: uart for WiSE
#       Author: Cyril Danilevski
#        Email: cydanil@gmail.com
#     HomePage: http://cydanil.net
#      Version: 0.0.1
#   LastChange: 2012-09-12 17:55:31
#      History: Made it!
=============================================================================*/
#define BAUD  19200
/* Sets the Baud rate, see: http://www.appelsiini.net/2011/simple-usart-with-avr-libc */
#define bauddivider (uint)(1.0 * XTAL / BAUD / 16 - 0.5)

void uinit(void){
  /* Set the baudrate */
  UBRRL = bauddivider;
  UBRRH = bauddivider >> 8;
  /* Shall we double up the speed of UART (U2X)? */
  UCSRA = 0;
  /* Setting up 8bit communication */
  UCSRC = 1<<URSEL^1<<UCSZ1^1<<UCSZ0;
  /* Enable Rx and Tx */
  UCSRB = 1<<RXEN^1<<TXEN;
}


void uputchar(char c){
  /* Sends a single character over serial */
  while((UCSRA & 1<<UDRE) == 0);
  UDR = c;
}


void uputs(char *s){
  /* Sends a whole string over serial */
  while(*s)
    uputchar(*s++);
}


void uputsnl(char *s){
  /* Sends a whole string over serial, 
      and adds newline */
  uputs(s);
  uputchar(0x0D);
}
