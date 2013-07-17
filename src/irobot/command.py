#!/usr/bin/env python
# -*- coding: utf-8 -*-
#pylint: disable=W0401,W0614

""" iRobote Create robot interface package.

Refer to the iRobot Create Open Interface reference document available on
iRobot Web site (http://www.irobot.com/filelibrary/pdfs/hrd/create/Create%20Open%20Interface_v2.pdf)

Command builder utility class
"""

from .defs import *
from .utils import *

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "June. 2013"
__status__ = "Development"
__license__ = "LGPL"

#
# Command builder
#

class Command(object):
    """ The Command class is a collection of static methods returning the
    bytes sequence corresponding to a given command.

    It allows a more friendly and readable elaboration of commands, especially
    when defining scripts.

    Commands naming is based on the content of the "Open Interface Command
    Reference" chapter of the documentation. Please refer to this document for
    a full explanation of the commands parameters.
    """
    @staticmethod
    def start():
        return [OI_START]

    @staticmethod
    def reset():
        return [OI_SOFT_RESET]

    @staticmethod
    def mode(mode):
        if mode in [OI_MODE_FULL, OI_MODE_PASSIVE, OI_MODE_SAFE]:
            return [mode]
        else:
            raise ValueError('invalid mode')

    @staticmethod
    def drive(velocity, radius=OI_DRIVE_STRAIGHT):
        return [OI_DRIVE] + int16_to_bytes(velocity) + int16_to_bytes(radius)

    @staticmethod
    def drive_direct(velocity_right, velocity_left):
        return [OI_DRIVE_DIRECT] + int16_to_bytes(velocity_right) + int16_to_bytes(velocity_left)

    @staticmethod
    def stop():
        return Command.drive_direct(0, 0)

    @staticmethod
    def leds(led_bits, power_color=OI_LED_GREEN, power_level=OI_LED_FULL):
        return [OI_LEDS, led_bits & OI_ALL_LEDS, power_color & 0xff, power_level & 0xff]

    @staticmethod
    def digital_outputs(states):
        return [OI_DIGITAL_OUTPUTS, states & OI_ALL_DOUTS]

    @staticmethod
    def low_side_drivers(states):
        return [OI_LOW_SIDE_DRIVERS, states & OI_ALL_DRIVERS]

    @staticmethod
    def send_ir(data):
        return [OI_SEND_IR, data & 0xff]

    @staticmethod
    def sensors(packet_id):
        if OI_PACKET_MIN <= packet_id <= OI_PACKET_MAX:
            return [OI_READ_SENSORS, packet_id]
        else:
            raise ValueError('invalid packet id (%d)' % packet_id)

    @staticmethod
    def query_list(packet_ids):
        return [OI_READ_SENSOR_LIST, len(packet_ids)] + packet_ids

    @staticmethod
    def stream(packet_ids):
        return [OI_STREAM_SENSOR_LIST, len(packet_ids)] + packet_ids

    @staticmethod
    def stream_pause_resume(state):
        return [OI_STREAM_PAUSE_RESUME, state & 0x01]

    @staticmethod
    def define_script(script):
        return [OI_SCRIPT_DEFINE, len(script)] + script

    @staticmethod
    def play_script():
        return [OI_SCRIPT_PLAY]

    @staticmethod
    def wait_time(delay):
        return [OI_WAIT_TIME, delay & 0xff]

    @staticmethod
    def wait_distance(distance):
        return [OI_WAIT_DISTANCE] + int16_to_bytes(distance)

    @staticmethod
    def wait_angle(angle):
        return [OI_WAIT_ANGLE] + int16_to_bytes(angle)

    @staticmethod
    def wait_event(event):
        return [OI_WAIT_EVENT, event & 0xff]

