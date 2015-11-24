
#!/bin/bash
#Code to start
echo 0x1 > /sys/devices/platform/bcm2708_usb/buspower;
echo .Bus power starting.
sleep 2;
/etc/init.d/networking start

