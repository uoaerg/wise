#!/usr/bin/env python2.7

import time
import RPi.GPIO as GPIO
import os
#import picamera
import control

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)


PIR_PIN = 24 #pin for PIR
IRLED_PIN = 25 #pin for enabling IR LED panel
ETH_PORT_ENABLE_PIN = 17 #pin to power-on the USB of Rpi(through switch outside of box) 
HUMIDITY_TEMP_PIN = 23 #for DHT22
POWER_OFF_PIN = 27 #lilypad toggles the pin for RPi to switch-off (in case of low battery)
CAM_LED = 32 #to switch-off the camera LED


def initGPIO():  #for setting pins (as input/output) other than PIR and Radar
    #to be init in constr GPIO.setup(PIR_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) ##input with pull-down, input  pin to detect motion through PIR
    GPIO.setup(IRLED_PIN, GPIO.OUT, pull_up_down=GPIO.PUD_DOWN) #output pin for switching-on the IR LED
    GPIO.setup(ETH_PORT_ENABLE_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #HIGH means the switch outside the box is ON, implying switch on the USB/ETH port 
    GPIO.setup(HUMIDITY_TEMP_PIN, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)   #input pin for reading humidity and temperature
    GPIO.setup(POWER_OFF_PIN, GPIO.IN,pull_up_down=GPIO.PUD_DOWN)   #HIGH means request from Lilypad to power down
    GPIO.setup(CAM_LED, GPIO.OUT, initial=False) 

#process shut-down request from Lilypad
def processShutdownRequest():
    if (GPIO.input(POWER_OFF_PIN) == True):
        print 'System going to shut down ....'
        os.system('sudo poweroff')
        return True
    else:
        #print 'request to shut down not received '
        return False

#process enabling ethernet port request from switch outside the box
def enableEthPort():
    if (GPIO.input(ETH_PORT_ENABLE_PIN) == True):
        #print 'Switching on the Ethernet port....'
        #call activate usb script
        return True
    else:
        #print 'ethernet switch on '
        return False


def activateIRLED():
    GPIO.output(IRLED_PIN, True) #enable the IRLED for night vision


def deactivateIRLED():
    GPIO.output(IRLED_PIN, False) #disable the IRLED


class PIR():
    def __init__(self, pin, direction):
        self._sigPin = pin
        self._count = 0   #ALERT attempt
        GPIO.setup(self._sigPin, GPIO.IN, pull_up_down= direction) #pin direction as GPIO.PUD_DOWN for PIR 
        print 'PIR constructor'
    def getTrigCount(self):
        return self._count #return the number of triggers
    def reset(self):
        self._count = 0

    def enableInterrupt(self, func):
        GPIO.add_event_detect(self._sigPin, GPIO.FALLING) #enable detection
        GPIO.add_event_callback(self._sigPin, func)  
        
    def disableInterrupt(self, func):
        GPIO.remove_event_detect(self._sigPin)
    def callbackPIR(self, channel): #count the PIR activations
        self._count  = self._count + 1
        #print 'count incremented'
        #print 'pir triggered enableInterrupt'

'''
initGPIO()
pir = PIR(PIR_PIN, GPIO.PUD_DOWN)
pir.enableInterrupt(pir.callbackPIR)
while(1):
    print 'sleeping & listening'
    time.sleep(15)
    if pir.getTrigCount() > 0:
        print "pir triggered", pir.getTrigCount()
        
    pir.reset()
    print 'pir count after reset', pir.getTrigCount()
'''


