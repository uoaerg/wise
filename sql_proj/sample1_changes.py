#!/bin/user/python
import RPi.GPIO as GPIO
import subprocess
#import time
import os
import pdb
from time import gmtime, strftime,time,sleep
import sys
 
var=1
PIR1Count=0
XBAND1Count=0

time_stamp=time()
time_stamp_PIR1=time()
time_stamp_XBAND1=time()
image_name=''
directory_path='/home/pi/logs/'
log_time=strftime("%Y-%m-%d %H:%M:%S", gmtime())

for num in range(1,100):
	directory=str(num)
	if not os.path.isdir(os.path.join(directory_path,directory)):
		directory_path=directory_path+directory+'/'
		os.mkdir(directory_path)
		filename=directory_path+'LOG1.txt'
		f=open(filename,'w+')
		f.write("LOG file statistics at : %s\n"%log_time)
		f.write('Sensor,Date,Time,No of triggers\n\n')
		f.close()
		break

GPIO.setmode(GPIO.BOARD)
GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)

 
""" the PIR1 is connected to GPIO pin 18 (12) """

def PIR1(channel):
		global PIR1Count,time_stamp_PIR1
		PIR1Count += 1
		time_now=time()
                if(time_now-time_stamp_PIR1) >= 1:
			print(channel)
			PIR1_timestamp=strftime("PIR1,%Y-%m-%d,%H:%M:%S", gmtime())
			PIR1=PIR1_timestamp+','+str(PIR1Count)
			f=open(filename,'r+')
			f.seek(-2, 2) 
			if f.read(2)=='\n\n':
				f.seek(-1,1)
			f.write('\n')
			f.write(PIR1)
			f.close
			capture_image(PIR1_timestamp)	
			time_stamp_PIR1=time()
			PIR1Count=0
	
def capture_image(trigger):
		global time_stamp
		time_now=time()
		if(time_now-time_stamp) >= 1.2:		
				trigger=directory_path+trigger+'.jpg'       			
				time_stamp=time_now
				subprocess.call(["raspistill","-o",trigger,"-t","0"])
				time_stamp=time()
			

""" the XBAND1 is connected to GPIO pin 23 (16) """

def XBAND1(channel):
		global XBAND1Count,time_stamp_XBAND1
		XBAND1Count += 1
		time_now=time()
		if(time_now-time_stamp_XBAND1) >= 1:
			print("Xband1 Triggered ")
        		XBAND1_timestamp=strftime("XBAND1,%Y-%m-%d,%H:%M:%S", gmtime())
			XBAND1=XBAND1_timestamp+','+str(XBAND1Count)
                	f=open(filename,'r+')
                	f.seek(-2,2)
                	if f.read(2)=='\n\n':
                       		 f.seek(-1,1)
            		f.write('\n')
                	f.write(XBAND1)
                	f.close
			capture_image(XBAND1_timestamp)
			time_stamp_XBAND1=time()
			XBAND1Count=0

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
  
