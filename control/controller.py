#!/usr/bin/env python2.7

from sensor import *
from image import *
from smssend import *
import os
import glob
import csv
import Adafruit_DHT
import sys

import resource
import gc


def sendSMS():
    sms = TextMessage("07796530493", "Message from Pi")
    sms.connectPhone()
    sms.sendMessage()
    sms.disconnectPhone()
    print "message sent successfully"


class Controller():

    def __init__(self):  # class initialization
        initGPIO()
        self._param = []  # create an empty list
        # initilaized on reading the config file
        self._timeBetweenImages = None
        self._readConfigFile()  # populate param from configuration file
        # assign values from config file
        self._pimg = ImageProcessor(True)
        self._pir = PIR(PIR_PIN, GPIO.PUD_DOWN)
        self._image_data_file = open('imageData.csv', 'a')
        self._image_writer = csv.writer(self._image_data_file)
        # TODO This is bad. Will add a new line with this every time the file
        # is loaded.
        self._image_writer.writerow(["Serial", "Image", "Brightness",
                                     "Threshold", "PIR Count",
                                     "No of Blobs", "Largest Blob Size",
                                     "verdict"])
        self._hourly_data_file = open('HourlyData.csv', 'a')
        self._hourly_writer = csv.writer(self._hourly_data_file)
        # TODO This is bad. Will add a new line with this every time the file
        # is loaded.
        self._hourly_writer.writerow(["Serial", "dateTime", "Brightness",
                                      "temperature External (C)",
                                      "humidity"])
        self._ser = 1

    def __del__(self):  # class destructor
        pass

    def _readConfigFile(self):
        idx = 0
        with open('config.txt') as fp:
            for line in fp:
                line = line.partition(':')[2]
                # print line  #ALERT if values of parameters are to be printed
                # to screen as well
                self._param.insert(idx, int(line.rstrip()))
                idx = idx + 1
            # print "index", idx
            self._timeBetweenImages = self._param[0]
            # print 'param', self._param[0]
            # for x  in range(0, idx):
            #    print self._param[x]*2

    def deleteHelperFiles(self):
        print 'deleting files'
        for file in glob.glob("./*motion*.jpg"):
            cmd = 'sudo rm ' + file
            os.system(cmd)
        for file in glob.glob("./*static*.jpg"):
            cmd = 'sudo rm ' + file
            os.system(cmd)
        for file in glob.glob("./*diff*.jpg"):
            cmd = 'sudo rm ' + file
            os.system(cmd)

    def run(self):
        print 'initializing ...'
        GPIO.output(CAM_LED, False)  # switch off camera LED

        time.sleep(2)
        self._pimg.takePicture('static')
        CAP_PIC = False
        # variables to check passage of an hour to record environmental data
        prevHour = currHour = 0
        serial = 1  # used for recording hourly temperatures
        # start listening for activations
        self._pir.enableInterrupt(self._pir.callbackPIR)

        while(1):
            # check for a condition to send sms
            # sendSMS()
            processShutdownRequest()  # shut down request from lilypad
            time.sleep(0.05)  # sleep for 50 ms

            if (self._pir.getTrigCount() > 0):  # motion detected by PIR
                start = time.time()
                self._pimg.takePicture('motion')

                timestamp, brightness, thresh, num_blobs, max_area, verdict = \
                    self._pimg.processImage()

                self._image_writer.writerow([self._ser, timestamp, brightness,
                                             thresh, self._pir.getTrigCount(),
                                             num_blobs, max_area, verdict])
                self._image_data_file.flush()

                self._ser = self._ser + 1

                timeToSleep = self._timeBetweenImages - (time.time()-start)
                if (timeToSleep < 0):  # SAFEGD against -ve values
                    timeToSleep = 1
                # print 'Sleeping for ',timeToSleep
                time.sleep(timeToSleep)

            else:
                lapse = time.strftime('%M')
                if((CAP_PIC == False) and ((int(lapse)) % 2 == 0)):
                    CAP_PIC = True
                    print("time lapse")
                    if ((int(lapse)) % 2 == 0):
                        self.deleteHelperFiles()
                    # an image without IR LEDs
                    brightness = self._pimg.calculateBrightness()
                    self._pimg.takePicture('static')
                    # '%H') #test only, set to %H
                    currHour = time.strftime('%M')
                    dateTime = time.strftime("%Y%m%d-%H%M%S")
                    print('prevHour ' + str(prevHour) + ' currHour ' +
                          str(currHour))
                    # time to record temp and brightness
                    if (prevHour != currHour):
                        # read values from humidity sensor DHT22 at GPIO pin 23
                        humidity, temperature_external = Adafruit_DHT.read_retry(
                            22, 23)
                        self._hourly_writer.writerow([serial, dateTime,
                                                      brightness,
                                                      round(
                                                          temperature_external,
                                                          2),
                                                      round(humidity, 2)])
                        self._hourly_data_file.flush()

                        prevHour = currHour
                        serial = serial + 1
                        # TODO Figure out why enabling EthPort is here
                        enableEthPort()
                elif (int(lapse) % 2 != 0):
                    CAP_PIC = False
            self._pir.reset()  # execute while(1)   ##enable later


def main():
    con = Controller()
    con.run()

if __name__ == '__main__':
    main()
