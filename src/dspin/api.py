#!/usr/bin/env python
# -*- coding: utf-8 -*-
#pylint: disable=W0401,W0614

""" dSpin (aka STMicroElectronics L6470) interface.

API classes.

This module is written for the Raspberry Pi but can be adapted easily.

Reference documentation available at:
    http://www.st.com/internet/analog/product/248592.jsp
Have also a look at this article:
    http://www.pobot.org/Driver-evolue-pour-moteur-pas-a.html
"""

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "July. 2013"
__status__ = "Development"
__license__ = "LGPL"

import spi
import time
import RPi.GPIO as GPIO
import logging

import pybot.log as log

from .defs import *
from .utils import *

RASPI_SPI_DEVICE = '/dev/spidev0.0'

class DSPin(object):
    """ dSPIN control and interface class.

    Internally relies on spi and RPi.GPIO modules.

    """
    def __init__(self, cs, stdby, not_busy=None,
                 debug=False, trace=False):
        """ Constructor.

        IMPORTANT: Signal pin numbers above use the P1 header numbering (and not the
        processor pins one).

        Parameters:
            cs:
                pin number of the /CHIP SELECT signal
            stdby:
                pin number of the /STANDBY signal
            not_busy:
                (optional) pin number of the /BUSY signal if used to monitor the moves
            debug:
                debug messages activation flag
                default: False
            trace:
                SPI data exchanges trace activation flag (requires debug=True)
                Warning: can slow down things
                default: False

        """
        self._debug = debug

        self._log = log.getLogger(type(self).__name__)
        if self._debug:
            self._log.setLevel(logging.DEBUG)
        self._trace = debug and trace

        self._port = RASPI_SPI_DEVICE

        GPIO.setmode(GPIO.BOARD)
        GPIO.setwarnings(False)

        self._cs = cs
        GPIO.setup(cs, GPIO.OUT)

        self._stdby = stdby
        GPIO.setup(stdby, GPIO.OUT)

        self._not_busy = not_busy
        if not_busy:
            GPIO.setup(not_busy, GPIO.IN)

        GPIO.output(self._cs, 1)

    def init(self):
        """ Context initialization.

        Must be called before any attempt to use the dSPIN.
        """
        self.reset_chip()
        spi.openSPI(device=self._port, bits=8, mode=3)
        if self._debug:
            self._log.debug('dSPIN interface initialized')

    def shutdown(self):
        """ Final cleanup.

        Not really mandatory, but strongly suggested when closing the application,
        at least for avoiding letting some GPIOs as outputs and risking shorting them and
        frying th RasPi.
        """
        if self._debug:
            self._log.debug('shutdown dSPIN interface')
        self.soft_hiZ()
        spi.closeSPI()
        for ch in [ ch for ch in (self._cs, self._stdby, self._not_busy) if ch]:
            GPIO.setup(ch, GPIO.IN)

    def reset_chip(self):
        """ dSPIN chip initialization sequence."""
        if self._debug:
            self._log.debug('resetting dSPIN chip')
        GPIO.output(self._stdby, 1)
        time.sleep(0.001)
        GPIO.output(self._stdby, 0)
        time.sleep(0.001)
        GPIO.output(self._stdby, 1)
        time.sleep(0.001)

    def _spi_write(self, b):
        """ Writes a single byte of data too SPI.

        Don't forget that the dSPIN version of the SPI protocol is
        a bit special, since it requires to toggle the CS signal
        *for each* byte of data to be written, and not around the whole
        message.

        Parameters:
            b:
                the byte to be sent (value is coerced as a byte)
        """
        if self._trace:
            self._log.debug(':SPI Wr> %0.2x', b)

        GPIO.output(self._cs, 0)
        spi.transfer((b & 0xff,))
        GPIO.output(self._cs, 1)

    def _spi_write_int24(self, v, max_value):
        """ 'Packaged' SPI write of a 3 bytes long integer value.

        Parameters:
            v:
                the value to be written
            max_value:
                the upper bound the provided value will be clamped to
        """
        if (v > max_value):
            v = max_value
        self._spi_write(v >> 16)
        self._spi_write(v >> 8)
        self._spi_write(v)

    def _spi_read(self):
        """ Reads a single byte from SPI.

        Returns:
            the byte
        """
        GPIO.output(self._cs, 0)
        res = spi.transfer((0,))[0] & 0xff
        GPIO.output(self._cs, 1)

        if self._trace:
            self._log.debug(':SPI Rd> %0.2x', res)

        return res

    def set_register(self, reg, value):
        """ Sets the value of a dSPIN register.

        The SPI operations are driven by the register descriptors stored in
        the dSPIN_REG_DESCR table of the dpsin.defs module."

        Parameters:
            reg:
                the register number
            value:
                the value to be set
        """
        lg, mask = dSPIN_REG_DESCR[reg]

        if value > mask:
            value = mask

        self._spi_write(dSPIN_CMD_SET_PARAM | reg)
        # we could have factored statements by using successive
        # length tests, but this implementation is more efficient
        if lg == 3:
            self._spi_write(value >> 16)
            self._spi_write(value >> 8)
            self._spi_write(value)
        elif lg == 2:
            self._spi_write(value >> 8)
            self._spi_write(value)
        elif lg == 1:
            self._spi_write(value)

    def get_register(self, reg):
        """ Returns the current value of a register.

        Parameters:
            reg:
                the register number

        Returns:
            the register value
        """
        lg, mask = dSPIN_REG_DESCR[reg]

        self._spi_write(dSPIN_CMD_GET_PARAM | reg)

        value = 0
        for _i in xrange(lg):
            value = (value << 8) | self._spi_read()
        return value & mask

    def get_status(self):
        """ Returns the dSPIN status as a 16 bits integer value."""
        self._spi_write(dSPIN_CMD_GET_STATUS)
        res = self._spi_read() << 8
        res |= self._spi_read()
        return res

    def get_config(self):
        """ Returns the dSPIN current configuration."""
        return self.get_register(dSPIN_REG_CONFIG)

    def get_current_speed(self):
        """ Returns the current motor speed, in steps per second."""
        steps_per_tick = self.get_register(dSPIN_REG_SPEED)
        return (int) (steps_per_tick * 0.0149)

    def enable_low_speed_optimization(self, enabled):
        """ Controls the low speed optimization mechanism."""
        self.set_register(dSPIN_REG_MIN_SPEED, (0x1000 if enabled else 0))

    def step_clock(self, direction):
        """ Moves the motor one step in the provided direction."""
        self._spi_write(dSPIN_CMD_STEP_CLOCK | direction)

    def move(self, n_step, direction):
        """ Moves the motor from the current position.

        Parameters:
            n_step:
                the step count
            direction:
                the move direction
        """
        self._spi_write(dSPIN_CMD_MOVE | (direction & 0x01))
        self._spi_write_int24(n_step, MASK_22)

    def run(self, stepsPerSec, direction):
        """ Runs the motor at a given speed in a given direction.

        Parameters:
            stepsPerSec:
                the target speed
            direction:
                the move direction
        """
        self._spi_write(dSPIN_CMD_RUN | (direction & 0x01))
        self._spi_write_int24(speed_steps_to_par(stepsPerSec), MASK_20)

    def goto_pos(self, pos, direction=None):
        """ Moves the motor to an absolute position, using the currently configured max speed.

        Parameters:
            pos:
                the target position (as a step count)
            direction:
                if provided, forces the move direction . If unset, the minimal physical path
                is used (see documentation paragraph 6.7.2)
        """
        if direction:
            self._spi_write(dSPIN_CMD_GOTO_DIR | (direction & 0x01))
        else:
            self._spi_write( dSPIN_CMD_GOTO)
        self._spi_write_int24(pos, MASK_22)

    def go_until_switch(self, action, direction, stepsPerSec):
        """ Runs the motor until the switch input state changes to low.

        Parameters:
            action:
                action on completion (dSPIN_ACTION_xxx)
            direction:
                move direction
            stepsPerSec:
                move speed
        """
        self._spi_write(dSPIN_CMD_GO_UNTIL | action | direction)
        self._spi_write_int24(speed_steps_to_par(stepsPerSec), MASK_22)

    def release_switch(self, action, direction):
        """ Runs the motor at minimum speed until the switch is released.

        Parameters:
            action:
                action on completion (dSPIN_ACTION_xxx)
            direction:
                move direction
        """
        self._spi_write(dSPIN_CMD_RELEASE_SW | action | direction)

    def go_home(self):
        """ Returns to stored home position, using the currently configured maximum speed."""
        self._spi_write( dSPIN_CMD_GO_HOME)

    def reset_pos(self):
        """ Resets the position register to 0."""
        self._spi_write( dSPIN_CMD_RESET_POS)

    def go_mark(self):
        """ Moves to the previously marked position."""
        self._spi_write( dSPIN_CMD_GO_MARK)

    def reset_device(self):
        """ Resets the device."""
        self._spi_write( dSPIN_CMD_RESET_DEVICE)

    def soft_stop(self):
        """ Decelerates and stops the motor using the currently configured deceleration rate.

        Motors remains energized after stop.
        """
        self._spi_write( dSPIN_CMD_SOFT_STOP)

    def hard_stop(self):
        """ Immediately stops the motor.

        Motors remains energized after stop.
        """
        self._spi_write( dSPIN_CMD_HARD_STOP)

    def soft_hiZ(self):
        """ Decelerates and stops the motor using the currently configured deceleration rate.

        Motor is no more energized after stop (outputs in HiZ state).
        """
        self._spi_write( dSPIN_CMD_SOFT_HIZ)

    def hard_hiZ(self):
        """ Immediately stops the motor.

        Motor is no more energized after stop (outputs in HiZ state).
        """
        self._spi_write( dSPIN_CMD_SOFT_HIZ)
        self._spi_write( dSPIN_CMD_HARD_HIZ)

    def wait_untill_not_busy(self):
        """ Blocks until the busy signal is set."""
        if self._not_busy:
            while not GPIO.input(self._not_busy):
                time.sleep(0.001)
        else:
            if self._log:
                self._log.warn("busy pin not set")

    def is_busy(self):
        """ Tells if we are busy for the moment."""
        return not GPIO.input(self._not_busy) if self._not_busy else False

    def get_absolute_position(self):
        """ Returns the current absolute position."""
        return self.get_register(dSPIN_REG_ABS_POS)

    def get_step_mode(self):
        """ Returns the current settings of the step mode.

        Returned value is one of dSPIN_STEP_SEL_xxx
        """
        return self.get_register(dSPIN_REG_STEP_MODE) & dSPIN_STEP_MODE_STEP_SEL

    def set_step_mode(self, step_sel):
        """ Sets the step mode.

        Parameters:
            step_sel:
                the step mode selector (one of dSPIN_STEP_SEL_xxx)
        """
        val = \
            (self.get_register(dSPIN_REG_STEP_MODE) & ~dSPIN_STEP_MODE_STEP_SEL) | \
            (step_sel & dSPIN_STEP_MODE_STEP_SEL)
        self.set_register(dSPIN_REG_STEP_MODE, val)

    def set_max_speed(self, stepsPerSec):
        """ Sets the maximum speed.

        Parameters:
            stepsPerSec:
                the speed, in steps per second
        """
        self.set_register(dSPIN_REG_MAX_SPEED, maxspeed_steps_to_par(stepsPerSec))

    def set_acceleration(self, stepsPerSec2):
        """ Sets the maximum acceleration rate.

        Parameters:
            stepsPerSec2:
                the acceleration, in steps per second^2
        """
        self.set_register(dSPIN_REG_ACC, accdec_steps_to_par(stepsPerSec2))

    def set_deceleration(self, stepsPerSec2):
        """ Sets the maximum deceleration rate.

        Parameters:
            stepsPerSec2:
                the deceleration, in steps per second^2
        """
        self.set_register(dSPIN_REG_DEC, accdec_steps_to_par(stepsPerSec2))

