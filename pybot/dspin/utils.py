#!/usr/bin/env python
# -*- coding: utf-8 -*-
#pylint: disable=W0401,W0614

""" dSpin (aka STMicroElectronics L6470) interface.

Utility functions.

Reference documentation available at:
    http://www.st.com/internet/analog/product/248592.jsp
Have also a llok at this article:
    http://www.pobot.org/Driver-evolue-pour-moteur-pas-a.html
"""

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "July. 2013"
__status__ = "Development"
__license__ = "LGPL"

from .defs import *

def speed_steps_to_par(stepsPerSec):
    """ Returns the SPEED register value corresponding to a value given
    as a step count per second."""
    return (int) (stepsPerSec * 67.108864 + 0.5)

def accdec_steps_to_par(stepsPerSec):
    """ Returns the ACC and DEC registers value corresponding to a value
    given as a step count per second^2."""
    return (int) (stepsPerSec * 0.068719476736 + 0.5)

def maxspeed_steps_to_par(stepsPerSec):
    """ Returns the MAX_SPEED register value corresponding to a value given
    as a step count per second."""
    return (int) (stepsPerSec * 0.065536 + 0.5)

def minspeed_steps_to_par(stepsPerSec):
    """ Returns the MIN_SPPED register value corresponding to a value given
    as a step count per second.

    This value is used to switch the low speed optimization mechanism.
    """
    return (int) (stepsPerSec * 4.194304 + 0.5)

def fsspeed_steps_to_par(stepsPerSec):
    """ Returns the FS_SPD register value corresponding to a value given
    as a step count per second.
    """
    return (int) (stepsPerSec * 0.065536)

def intspeed_steps_to_par(stepsPerSec):
    """ Returns the INT_SPEED register value corresponding to a value given
    as a step count per second.
    """
    return (int) (stepsPerSec * 4.194304 + 0.5)

def kval_pct_to_par(pct):
    return (int) (pct / 0.390525 + 0.5)

def bemf_slope_pct_to_par(pct):
    return (int) (pct / 0.00156862745098 + 0.5)

def ktherm_to_par(ktherm):
    return (int) ((ktherm - 1) / 0.03125 + 0.5)

def stallth_to_par(mA):
    return (int) ((mA - 31.25) / 31.25 + 0.5)

#
# This dictionary contains the offsets of the fields composing the CONFIG
# register. It is dynamically initialized at module import time by
# introspecting the constants defining the respective bit masks of these
# fields. Shift value is obtained by finding the position of the first 1,
# counting from the right of the mask.
#
_REG_CFG_SHIFTS = dict(
    [(n, bin(eval(n))[::-1].find('1')) for n in globals().keys() if n.startswith('dSPIN_CONFIG_')]
)

def unpack_config_reg(value):
    """ Returns the different bit fields of a CONFIG register value as a dictionary.

    Keys are the names of the bit fields, as defined in the reference documentation
    (and used to defined the dSPIN_CONFIG_xxx constants)
    """
    offs = len('dSPIN_CONFIG_')
    return dict(
        [(k[offs:], (value & eval(k)) >> v) for k, v in _REG_CFG_SHIFTS.iteritems()]
    )

#
# Same for STATUS register values
#
_REG_STATUS_SHIFTS = dict(
    [(n, bin(eval(n))[::-1].find('1')) for n in globals().keys() if n.startswith('dSPIN_STATUS_')]
)

def unpack_status_reg(value):
    offs = len('dSPIN_STATUS_')
    return dict(
        [(k[offs:], (value & eval(k)) >> v) for k, v in _REG_STATUS_SHIFTS.iteritems()]
    )

#
# Same for STEP_MODE register values
#
_REG_STEP_MODE_SHIFTS = dict(
    [(n, bin(eval(n))[::-1].find('1')) for n in globals().keys() if n.startswith('dSPIN_STEP_MODE_')]
)

def unpack_step_mode_reg(value):
    offs = len('dSPIN_STEP_MODE_')
    return dict(
        [(k[offs:], (value & eval(k)) >> v) for k, v in _REG_STEP_MODE_SHIFTS.iteritems()]
    )

