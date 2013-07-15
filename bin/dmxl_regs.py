#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  dmxl-regs.py
#
#  Copyright 2013 Eric PASCUAL <eric@pobot.org>
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

'''Displays or modifies Dynamixel servo registers.'''

import argparse
from pybot.dmxl import classes as dmxl, cli as dmxl_cli
from pybot import cli

__author__ = 'Eric Pascual (POBOT)'

def write_register(intf, dmxlid, reg, value):
    try:
        intf.write_register(dmxlid, reg, value)
    except Exception as e:
        cli.print_err(str(e))

def display_register(intf, dmxlid, reg):
    try:
        value = intf.read_register(dmxlid, reg)
        dmxl.Register.dump(reg, value)
    except RuntimeError as e:
        if dmxlid == dmxl.DynamixelBusInterface.INTERFACE_ID:
            pass  # all registers are not relevant for interfaces
        else:
            cli.print_err(str(e))
            raise
    except Exception as e:
        cli.print_err(str(e))
        raise

def main(args):
    try:
        intf = dmxl.DynamixelBusInterface(port=args.port,
                baudrate=args.baudrate, timeout=args.timeout)
    except Exception as e:
        cli.die(e)

    if args.intf or intf.ping(args.id):
        if args.intf:
            print('Interface register(s) :')
        else:
            print('Servo id=%s register(s) :' % args.id)

        if args.value != None:
            # we ask to change a register => check if it is indicated
            if args.regnum != None:
                write_register(intf, args.id, args.regnum, args.value)
            else:
                cli.print_err('no register specified')
                return 1

        if args.regnum != None:
            # we want to read a specific register
            display_register(intf, args.id, args.regnum)
        else:
            # we want to display all registers
            intf.dump_regs(args.id)

    else:
        cli.print_err('no servo found with id=%d' % args.id)


if __name__ == '__main__':
    parser = dmxl_cli.get_argument_parser(description=__doc__)

    group = parser.add_argument_group('Command options')
    group.add_argument('-i', '--id', dest='id', type=dmxl_cli.dmxl_id,
            help='the servo id',
            default=1)
    group.add_argument('-I', '--interface', dest='intf', action='store_true',
            help='if used, command targets the interface instead of a servo (-i ignored in this case)'
            )
    group.add_argument('-r', '--reg', dest='regnum', type=dmxl_cli.dmxl_regnum,
            help='the register to read or write (if not specified, display all regs)',
            )
    group.add_argument('-w', '--write', dest='value', type=int,
            help='writes the value in the register specified by -r/--reg options (if not specified, will display the register indicated by -r/--reg option)',
            )

    args = parser.parse_args()

    # unify target identification
    if args.id == dmxl.DynamixelBusInterface.INTERFACE_ID:
        args.intf = True
    elif args.intf:
        args.id = dmxl.DynamixelBusInterface.INTERFACE_ID

    main(args)
