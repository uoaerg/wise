#!/bin/bash
#Code to stop
/etc/init.d/networking stop
echo 0x0 > /sys/devices/platform/bcm2708_usb/buspower;
echo .Bus power stopping.



