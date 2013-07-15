#!/usr/bin/env python
# -*- coding: utf-8 -*-

import dbus.mainloop.glib
import gobject
import os
import argparse
import signal

import pybot.i2c as i2c
from pybot.dbus.lcdconsole import ConsoleService, _logger

def main(args):
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    gobject.threads_init()
    dbus.mainloop.glib.threads_init()
    loop = gobject.MainLoop()
    
    try:
        dbus_bus = dbus.SessionBus() 
        _logger.info('using SessionBus')
    except:
        dbus_bus = dbus.SystemBus() 
        _logger.info('using SystemBus')
    
    if args.iftype == 'smbus':
        i2cbus = i2c.SMBusI2CBus(args.busid)
        _logger.info('using SMBus with bus id = %d' % args.busid)
    else:
        i2cbus = i2c.USB2I2CBus(args.dev)
        _logger.info('using USB2I2CBus on device %s' % args.dev)
        
    console = ConsoleService(i2cbus, dbus_bus=dbus_bus, dbus_loop=loop)
    console.clear()
    console.center_text_at(args.greetings, 1)
    console.center_text_at('-**-', 2)

    def terminate_signal_handler(signum, frame):
        if signum == signal.SIGINT:
            print   # cosmetic, so that next message starts at left margin
            
        _logger.warn('termination signal caught (signum=%d)' % signum)
        console.shutdown()
        
    signal.signal(signal.SIGINT, terminate_signal_handler)
    signal.signal(signal.SIGTERM, terminate_signal_handler)
    
    try:
        console.run()
    
    finally:
        console.clear()
        console.center_text_at('Goodbye', 2)
        console.shutdown()
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Starts the LCD console dbus service',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--iftype', 
                        dest='iftype', 
                        help='interface type',
                        choices=['smbus', 'usb'],
                        default='smbus'
                        )
    parser.add_argument('-d', '--dev',
                        dest='dev',
                        help='the device used to access the USB interface',
                        default='/dev/ttyUSB0'
                        )
    parser.add_argument('-b', '--busid',
                        dest='busid',
                        help='the id of the bus when using SMBus interface',
                        type=int,
                        default='1'
                        )
    parser.add_argument('-g', '--greetings',
                        dest='greetings',
                        help='the greetings message',
                        default='Welcome ;)'
                        )
    args = parser.parse_args()
    
    main(args)
    
