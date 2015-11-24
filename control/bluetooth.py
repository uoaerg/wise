import serial
from time import sleep

bluetoothSerial = serial.Serial( "/dev/rfcomm0", baudrate=9600 )
"""
count = None
while count != None:
    try:
        count = int(raw_input( "Please enter the number of times to blink the Led"))
    except:
        pass    # Ignore any errors that may occur and try again


bluetoothSerial.write( str(count) )
print bluetoothSerial.readline()
"""

def listenForData():
	dataIn  = bluetoothSerial.readline()
	print dataIn


if __name__ == "__main__":
	listenForData()


