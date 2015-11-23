CONTIKI_PROJECT = sensor-test
all: $(CONTIKI_PROJECT)

TARGET = avr-zigduino

CFLAGS += -DNODE=$(NODE)

CONTIKI = ../../../..
UIP_CONF_IPV6 = 1

include $(CONTIKI)/Makefile.include
