CONTIKI_PROJECT = sensor-node
all: $(CONTIKI_PROJECT)

WITH_UIP6=1
UIP_CONF_IPV6=1

CFLAGS += -DNODE=$(NODE)

TARGET=avr-atmega128rfa1

CONTIKI = ../../../..
include $(CONTIKI)/Makefile.include

