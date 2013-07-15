#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dmxl-setid.py
#  
#  Copyright 2013 Eric PASCUAL <eric <at> pobot <dot> org>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  


''' Sets the id of a connected Dynamixel servo. 

A broadcast command is used to allow setting a new id without having 
to know the current one, and thus the command will work only if there
is a single servo connected to the bus.
'''

import argparse
from pybot.dmxl import classes as dmxl, cli as dmxl_cli
from pybot import cli

__author__ = 'Eric PASCUAL (POBOT)'

def main(args):
    try:
        intf = dmxl.DynamixelBusInterface(port=args.port,
                baudrate=args.baudrate, timeout=args.timeout)
    except Exception as e:
        cli.die(e)
    
    if not args.force:
        print('Scanning bus on %s to find connected servos...' % args.port)
        nb_servos = len(intf.scan())

        if nb_servos == 0:
            cli.print_err('no servo found on the bus')
            return 1
            
        if nb_servos > 1:
            cli.print_err('only ONE servo must be connected to the bus (%d servos found)' % nb_servos)
            return 1
        
    intf.write_register(dmxl.DynamixelBusInterface.BROADCASTING_ID, dmxl.Register.Id, args.newid)
    print("Servo id changed to %d." % args.newid)
    return 0

if __name__ == '__main__':
    parser = dmxl_cli.get_argument_parser(description=__doc__)

    group = parser.add_argument_group('Command options')
    group.add_argument('-i', '--newid', dest='newid', 
        type=dmxl_cli.dmxl_id,
        required=True,
        help='the new id to set')

    group.add_argument('-F', '--force', action='store_true', dest='force', 
        help='if used, no check will be done to see if more than one servo is connected')

    args = parser.parse_args()
    
    main(args)

