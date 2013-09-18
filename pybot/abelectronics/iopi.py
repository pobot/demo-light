#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A set of very simple classes to interact with the IOPi board from AB Electronics."""

__author__ = 'Eric PASCUAL for POBOT'
__version__ = '1.0.0'
__email__ = 'eric@pobot.org'

EXPANDER_1 = 0
EXPANDER_2 = 1
PORT_A = 0
PORT_B = 1

# reg addresses suppose that IOCON.BANK is set to 0 (default value)
# and thus that port registers are paired
REG_IODIR = 0x00
REG_IPOL = 0x02
REG_GPINTEN = 0x04
REG_GPPU = 0x0C
REG_GPIO = 0x12
REG_OLAT = 0x14

DIR_OUTPUT = 0
DIR_INPUT = 1

class Board(object):
    """ This class represents the whole expansion board.

    It can be used directly to manipulate the registers of the 4 embedded I/O ports,
    but usually it's simpler to use instances of the Port class for this. This is
    fully equivalent, but user code is more readable this way.

    This costs a small overhead since the Port methods delegates to Board ones, taking
    care of passing them the additional parameters, but unless you have a critical
    performances problem, it should do the trick most of the time.
    """

    def __init__(self, bus, exp1_addr=0x20, exp2_addr=0x21):
        self._bus = bus
        self._addr = (exp1_addr, exp2_addr)

    def write_reg(self, exp, port, reg, data):
        self._bus.write_byte_data(self._addr[exp], reg + port, data & 0xff)

    def read_reg(self, exp, port, reg):
        return self._bus.read_byte_data(self._addr[exp], reg + port) & 0xff


class Port(object):
    def __init__(self, iopi, exp, port):
        if exp not in (EXPANDER_1, EXPANDER_2):
            raise ValueError("invalid expander (%d)" % exp)

        if port not in (PORT_A, PORT_B):
            raise ValueError("invalid port (%d)" % port)

        self._iopi = iopi
        self._exp = exp
        self._port = port

    def set_mode(self, mode):
        self._iopi.write_reg(self._exp, self._port, REG_IODIR, mode)

    def get_mode(self):
        return self._iopi.read_reg(self._exp, self._port, REG_IODIR)

    def set_pullup(self, state):
        self._iopi.write_reg(self._exp, self._port, REG_GPPU, state)

    def get_pullup(self):
        return self._iopi.read_reg(self._exp, self._port, REG_GPPU)

    def set(self, state):
        self._iopi.write_reg(self._exp, self._port, REG_GPIO, state)

    def get(self):
        return self._iopi.read_reg(self._exp, self._port, REG_GPIO)

