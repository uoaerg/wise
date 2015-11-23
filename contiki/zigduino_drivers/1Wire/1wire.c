/*=============================================================================
#     FileName: 1WIRE.C
#         Desc: 1-Wire library for DS2438, based of Peter Dannegger's.
#       Author: Cyril Danilevski
#        Email: cydanil@gmail.com
#     HomePage: http://cydanil.net
#      Version: 0.0.1
#   LastChange: 2012-09-12 15:09:25
#      History: Proof read, let me know if you want Arduino syntax
=============================================================================*/


#ifndef W1_PIN
#define W1_PIN	PD6
#define W1_IN	PIND
#define W1_OUT	PORTD
#define W1_DDR	DDRD
#endif


bit w1_reset(void){
  /* This function is used to reset the bus, in case things goes wrong. */
  bit err;

  W1_OUT &= ~(1<<W1_PIN);
  W1_DDR |= 1<<W1_PIN;
  DELAY(DELAY_US(480));
  cli();
  W1_DDR &= ~(1<<W1_PIN);
  DELAY( DELAY_US(66));
  /* No 1-Wire device found */
  err = W1_IN & (1<<W1_PIN);
  sei();
  DELAY(DELAY_US( 480 - 66));
  if((W1_IN & (1<<W1_PIN)) == 0){
    err = 1;
  }
  return err;
}


uchar w1_bit_io(bit b){
  cli();
  W1_DDR |= 1<<W1_PIN;
  DELAY( DELAY_US(1));
  if(b){
    W1_DDR &= ~(1<<W1_PIN);
  }
  DELAY( DELAY_US(15 - 1));
  if((W1_IN & (1<<W1_PIN)) == 0){
    b = 0;
  }
  DELAY( DELAY_US(60 - 15));
  W1_DDR &= ~(1<<W1_PIN);
  sei();
  return b;
}


uint w1_byte_wr(uchar b){
  uchar i = 8, j;
  do{
    j = w1_bit_io(b & 1);
    b >>= 1;
    if(j){
      b |= 0x80;
    }
  }while(--i);
  return b;
}


uint w1_byte_rd(void){
  return w1_byte_wr(0xFF);
}


uchar w1_rom_search(uchar diff, uchar idata *id){
  uchar i, j, next_diff;
  bit b;

  if(w1_reset()){
    /* No device found */
    return PRESENCE_ERR;
  }
  /* Search for a 1-Wire device ROM */
  w1_byte_wr(SEARCH_ROM);
  next_diff = LAST_DEVICE;
  /* Sets 8 bytes */
  i = 8 * 8;
  do{
    /* Sets 8 bits */
    j = 8;
    do{
      /* Read bit and its complement */
      b = w1_bit_io(1);
      if( w1_bit_io(1)){
	       if(b){
          /* Data error, better leave */
	         return DATA_ERR;
          }
      }
      else{
        /* If there are two devices, find out which is which */
	       if(!b){
	         if(diff > i || ((*id & 1) && diff != i)){
	           b = 1;				// now 1
	           next_diff = i;			// next pass 0
	         }
	       }
      }
      /* Write a bit to the 1-Wire Device */
      w1_bit_io(b);
      *id >>= 1;
      if(b){			// store bit
	       *id |= 0x80;
      }
      i--;
    }while(--j);
    id++;					// next byte
  }while(i);
  /* Continues searching */
  return next_diff;	
}


void w1_command(uchar command, uchar idata *id){
  /* This function allows you to send commands to the 1-Wire device. */
  uchar i;
  w1_reset();
  if(id){
    /* If that's the device we want to talk to, send the command. */
    w1_byte_wr(MATCH_ROM);
    i = 8;
    do{
      w1_byte_wr(*id);
      id++;
    } while(--i);
  }
  else{
    /* That's not the right device, so skip, and go to the next one. */
    w1_byte_wr(SKIP_ROM);
  }
  w1_byte_wr(command);
}
