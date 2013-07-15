#!/usr/bin/env python
# -*- coding: utf-8 -*-

class IOPi(object):
    EXP_1 = 0
    EXP_2 = 1
    PORT_A = 0
    PORT_B = 1

    # reg addresses suppose that IOCON.BANK is set to 0 (default value)
    # and thus that port registers are paired
    IODIR = 0x00
    IPOL = 0x02 
    GPINTEN = 0x04
    GPPU = 0x0C
    GPIO = 0x12
    OLAT = 0x14

    OUTPUT = 0
    INPUT = 1

    def __init__(self, bus, exp1_addr=0x20, exp2_addr=0x21):
        self._bus = bus
        self._addr = (exp1_addr, exp2_addr)

    def write_reg(self, exp, port, reg, data):
        self._bus.write_byte_data(self._addr[exp], reg + port, data & 0xff)

    def read_reg(self, exp, port, reg):
        return self._bus.read_byte_data(self._addr[exp], reg + port) & 0xff


class IOPiPort(object):
    def __init__(self, iopi, exp, port):
        if exp not in (IOPi.EXP_1, IOPi.EXP_2):
            raise ValueError("invalid expander (%d)" % exp)

        if port not in (IOPi.PORT_A, IOPi.PORT_B):
            raise ValueError("invalid port (%d)" % port)

        self._iopi = iopi
        self._exp = exp
        self._port = port

    def set_mode(self, mode):
        self._iopi.write_reg(self._exp, self._port, IOPi.IODIR, mode)

    def get_mode(self):
        return self._iopi.read_reg(self._exp, self._port, IOPi.IODIR)

    def set_pullup(self, state):
        self._iopi.write_reg(self._exp, self._port, IOPi.GPPU, state)

    def get_pullup(self):
        return self._iopi.read_reg(self._exp, self._port, IOPi.GPPU)

    def set(self, state):
        self._iopi.write_reg(self._exp, self._port, IOPi.GPIO, state)

    def get(self):
        return self._iopi.read_reg(self._exp, self._port, IOPi.GPIO)

