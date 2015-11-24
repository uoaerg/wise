from control import Controller
from ThreeBlur import ThreeBlur
from backSub import backSub
from DataWriter import DataWriter
from ConfigParser import SafeConfigParser
import Adafruit_DHT
import os
import picamera
import sensor
import time
import motion
import cv2

def main():
	con = Controller("sample.cfg", "True");
	con.run()

if __name__ == '__main__':
	main()