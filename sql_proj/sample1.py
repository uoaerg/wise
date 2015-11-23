#!/bin/user/python
import RPi.GPIO as GPIO
import subprocess
#import time
import os
import pdb
from time import gmtime, strftime,time,sleep
import sys

# A comment
 
var=1

time_stamp=time()

f=open('PIR1.txt','w')
#f.write('PIR1 Log details\n')
#f.write('Time,Date\n')
f.close


GPIO.setmode(GPIO.BOARD)
GPIO.setup(11,GPIO.OUT)
GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(22,GPIO.IN)

 
""" the PIR1 is connected to GPIO pin 18 (12) """

def PIR1(channel):
		print("PIR1 Triggered ")
		PIR1=strftime("%Y-%m-%d,%H:%M:%S", gmtime())
		f=open('PIR1.txt','r+')
#		f.seek(-2, 2) 
#		if f.read(2)=='\n\n':
#			f.seek(-1,1)
		f.write('\n')
		f.write(PIR1)
		f.close
		capture_image(PIR1,"PIR1")	
	
def capture_image(image_time,trigger):
		global time_stamp	
		time_now=time()
		if(time_now-time_stamp) >= 1.2:			
				image_name=image_name+ ".jpg"                      
				time_stamp=time_now
				subprocess.call(["raspistill","-o",image_name,"-t","0"])
				time_stamp=time()
				image_name=''

""" the XBAND1 is connected to GPIO pin 23 (16) """

def XBAND1(channel):
		print("Xband1 Triggered ")
                XBAND1=strftime("%Y-%m-%d,%H:%M:%S", gmtime())
                f=open('XBAND1.txt','r+')
                f.seek(-2,2)
                if f.read(2)=='\n\n':
                        f.seek(-1,1)
                f.write('\n')
                f.write(XBAND1)
                f.close
		capture_image(XBAND1,"XBAND1")

# when a falling edge is detected on port 17, regardless of whatever
# else is happening in the program, the function my_callback will be run
GPIO.add_event_detect(12, GPIO.RISING, callback=PIR1, bouncetime=200)
GPIO.add_event_detect(16, GPIO.RISING, callback=XBAND1, bouncetime=200)

try:
        while (var):
			print ("program executing")
			var=raw_input("enter cntl+c to exit \n")
except KeyboardInterrupt:
	print "Quit"
	#Reset GPIO settings
	GPIO.cleanup()
  
