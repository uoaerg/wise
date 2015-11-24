#!/usr/bin/env python2.7

# System modules
import time
import math
import os
import datetime
import subprocess

# Third part modules
import picamera
import cv2
import cv2.cv as cv
import numpy as np
from PIL import Image, ImageStat
from scipy import ndimage

# Project modules
import motion
from sensor import *


class ImageProcessor():

    def __init__(self, save_images=False):
        self._static_ref_picture = None
        self._currImg = None
        self._brightness = 100  # initially consider it daylight
        self._brightness_threshold = 15  # lower values to be considered dark
        self._time = None  # time for the image capture
        self._RPIcam = picamera.PiCamera()
        self._RPIcam.resolution = (640, 480)  # set the camera resolution here
        self._percentage_thresh = 25
        self._save_images = save_images

    def __del__(self):
        self._RPIcam.close()

    def takePicture(self, type):
        self._time = datetime.datetime.now()
        timeStamp = self._time.strftime('%Y%m%d-%H%M%S')
        if self._brightness <= self._brightness_threshold:  # its dark
            activateIRLED()  # switch-on the IR LEDs
        if type == 'static':
            imgName = timeStamp + '-static.jpg'
            self._RPIcam.capture(imgName)
            self._static_ref_picture = cv2.imread(imgName)
            print 'static image taken', imgName
        else:
            imgName = timeStamp + '.jpg'
            self._RPIcam.capture(imgName)
            self._currImg = cv2.imread(imgName)
            print 'motion image taken', imgName
        deactivateIRLED()  # switch off the IR LEDs

    def set_precentage_threshold(self, a_percentage_threshold):
        self._percentage_thresh = a_percentage_threshold

    def calculateBrightness(self):
        self._RPIcam.capture("refImg.jpg")
        im = Image.open("refImg.jpg").convert('L')
        stat = ImageStat.Stat(im)
        # scales a no from min (0 black) to max (255 white) range to 0-100
        self._brightness = (int)(((100-0)*(stat.rms[0] - 0))/(255-0)) + 0
        return self._brightness

    def processImage(self):
        timestamp = self._time.strftime('%Y%m%d-%H%M%S-')
        # TODO Figure out if this needs to be "refactored away"
        thresh = (self._percentage_thresh/100.0) * \
            ((255.0*self._brightness)/100.0)

        motionDiff = motion.simple2Diff(self._static_ref_picture,
                                        self._currImg, timestamp,
                                        [(20, 190), (620, 460)], thresh,
                                        True)

        blobs, numBlobs, contours, hierarchy = \
            motion.getBlobStatistics(motionDiff)

        maxArea = motion.getMaxAreaFromContours(contours)

        verdict = motion.evalMotionBlobCountMaxArea(numBlobs, maxArea, 30, 200)

        return timestamp, self._brightness, thresh, numBlobs, maxArea, \
            verdict
