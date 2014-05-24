#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import logging
from random import gauss


class ADCPi(object):
    def __init__(self, address=0x68, address2=0x69, rate=18):
        self._log = logging.getLogger('ADCPi')
        self._log.info('creating with address=0x%.2x, address2=0x%.2x, rate=%d', address, address2, rate)

    def readVoltage(self, input_id):
        return gauss(4.2, 0.1)


class BlinkM(object):
    def __init__(self, bus=1, addr=0x09):
        self._log = logging.getLogger('BlinkM')
        self._log.info('created with bus=%d addr=0x%.2x', bus, addr)

    def reset(self):
        self._log.info('reset')


class GPIO(object):
    BOARD = 'board'
    OUT = 'out'
    HIGH = 1
    LOW = 0

    def __init__(self):
        self._log = logging.getLogger('GPIO')

    def setmode(self, mode):
        self._log.info('setting mode to "%s"' % mode)

    def setup(self, pin, mode):
        self._log.info('setup pin %d to mode "%s"', pin, mode)

    def output(self, pin, state):
        self._log.info('setting pin %d to %d', pin, state)

    def cleanup(self, ):
        self._log.info('cleanup')