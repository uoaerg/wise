'''
The pin assignments are as follows
GPIO Pin 18(12)-PIR1
GPIO Pin 17(11)-PIR2
GPIO Pin 21(13)-PIR3
GPIO Pin 23(16)-XBAND1
GPIO Pin 24(18)-XBAND2
GPIO Pin 25(22)-XBAND3
'''

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
PIR2Count=0
PIR3Count=0
XBAND1Count=0
XBAND2Count=0
XBAND3Count=0

time_stamp=time()
time_stamp_PIR1=time()
time_stamp_PIR2=time()
time_stamp_PIR3=time()
time_stamp_XBAND1=time()
time_stamp_XBAND2=time()
time_stamp_XBAND3=time()

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
		f.write("LOG file statistics at : %s\n\n"%log_time)
		f.write('Sensor,Date,Time,No of triggers\n')
		f.close()
		break

GPIO.setmode(GPIO.BOARD)
GPIO.setup(12,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(11,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(13,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(18,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(22,GPIO.IN,pull_up_down=GPIO.PUD_DOWN)
 
""" the PIR1 is connected to GPIO pin 18 (12) """

def PIR1(channel):
		global PIR1Count,time_stamp_PIR1
		PIR1Count += 1
		time_now=time()
                if(time_now-time_stamp_PIR1) >= 1:
			print("PIR1 Triggered ")
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

""" the PIR2 is connected to GPIO pin 17 (11) """

def PIR2(channel):
                global PIR2Count,time_stamp_PIR2
                PIR2Count += 1
                time_now=time()
                if(time_now-time_stamp_PIR2) >= 1:
			print("PIR2 Triggered ")
                        PIR2_timestamp=strftime("PIR2,%Y-%m-%d,%H:%M:%S", gmtime())
                        PIR2=PIR2_timestamp+','+str(PIR2Count)
                        f=open(filename,'r+')
                        f.seek(-2, 2)
                        if f.read(2)=='\n\n':
                                f.seek(-1,1)
                        f.write('\n')
                        f.write(PIR2)
                        f.close
                        capture_image(PIR2_timestamp)
                        time_stamp_PIR2=time()
                        PIR2Count=0

""" the PIR1 is connected to GPIO pin 21 (13) """

def PIR3(channel):
                global PIR3Count,time_stamp_PIR3
                PIR3Count += 1
                time_now=time()
                if(time_now-time_stamp_PIR3) >= 1:
                        print("PIR3 Triggered ")
			PIR3_timestamp=strftime("PIR3,%Y-%m-%d,%H:%M:%S", gmtime())
                        PIR3=PIR3_timestamp+','+str(PIR3Count)
                        f=open(filename,'r+')
                        f.seek(-2, 2)
                        if f.read(2)=='\n\n':
                                f.seek(-1,1)
                        f.write('\n')
                        f.write(PIR3)
                        f.close
                        capture_image(PIR3_timestamp)
                        time_stamp_PIR3=time()
                        PIR3Count=0
	
def capture_image(trigger):
		global time_stamp
		time_now_cam=time()
		if(time_now_cam-time_stamp) >= 1.5:		
				time_stamp=time()
				print("trigger")
				picture_name=directory_path+trigger+".jpg" 			
				subprocess.call(["raspistill","-o",picture_name,"-t","1"])
				time_stamp=time()
				picture_name=''
				
			
			

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

""" the XBAND2 is connected to GPIO pin 24 (18) """

def XBAND2(channel):
                global XBAND2Count,time_stamp_XBAND2
                XBAND2Count += 1
                time_now=time()
                if(time_now-time_stamp_XBAND2) >= 1:
                        print("Xband2 Triggered ")
                        XBAND2_timestamp=strftime("XBAND2,%Y-%m-%d,%H:%M:%S", gmtime())
                        XBAND2=XBAND2_timestamp+','+str(XBAND2Count)
                        f=open(filename,'r+')
                        f.seek(-2,2)
                        if f.read(2)=='\n\n':
                                 f.seek(-1,1)
                        f.write('\n')
                        f.write(XBAND2)
                        f.close
                        capture_image(XBAND2_timestamp)
                        time_stamp_XBAND2=time()
                        XBAND2Count=0


""" the XBAND1 is connected to GPIO pin 25 (22) """

def XBAND3(channel):
                global XBAND3Count,time_stamp_XBAND3
                XBAND3Count += 1
                time_now=time()
                if(time_now-time_stamp_XBAND3) >= 1:
                        print("Xband3 Triggered ")
                        XBAND3_timestamp=strftime("XBAND3,%Y-%m-%d,%H:%M:%S", gmtime())
                        XBAND3=XBAND3_timestamp+','+str(XBAND3Count)
                        f=open(filename,'r+')
                        f.seek(-2,2)
                        if f.read(2)=='\n\n':
                                 f.seek(-1,1)
                        f.write('\n')
                        f.write(XBAND3)
                        f.close
                        capture_image(XBAND3_timestamp)
                        time_stamp_XBAND3=time()
                        XBAND3Count=0

# when a falling edge is detected on port 17, regardless of whatever
# else is happening in the program, the function my_callback will be run
GPIO.add_event_detect(12, GPIO.RISING, callback=PIR1, bouncetime=200)
GPIO.add_event_detect(11, GPIO.RISING, callback=PIR3, bouncetime=200)
GPIO.add_event_detect(13, GPIO.RISING, callback=PIR2, bouncetime=200)
GPIO.add_event_detect(16, GPIO.RISING, callback=XBAND1, bouncetime=200)
GPIO.add_event_detect(18, GPIO.RISING, callback=XBAND3, bouncetime=200)
GPIO.add_event_detect(22, GPIO.RISING, callback=XBAND2, bouncetime=200)

try:
        while (var):
			print ("program executing")
			var=raw_input("enter cntl+c to exit \n")
except KeyboardInterrupt:
	print "Quit"
	#Reset GPIO settings
	GPIO.cleanup()
  
