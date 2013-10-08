#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os, sys
if not os.getuid() == 0:
    sys.exit('Needs to be root for running this script.')

import RPi.GPIO as GPIO
import time
import subprocess

BTN_IO = 4
GPIO.setmode(GPIO.BCM)
GPIO.setup(BTN_IO, GPIO.IN, GPIO.PUD_UP)

print('monitoring started')
while True:
    pressed = (GPIO.input(BTN_IO) == 0)
    if pressed:
        time.sleep(4)
        pressed = (GPIO.input(BTN_IO) == 0)
        if pressed:
            break
    else:
        time.sleep(0.1)


print('Shutdown button pressed. System is going to halt now')
subprocess.Popen('/sbin/halt')
