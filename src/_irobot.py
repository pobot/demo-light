#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" iRobote Create robot interface module.

This module provides a class modeling the robot and handling the communication
with the Create via its serial link. It also includes various additional
definitions and helpers.

Refer to the iRobot Create Open Interface reference document available on
iRobot Web site (http://www.irobot.com/filelibrary/pdfs/hrd/create/Create%20Open%20Interface_v2.pdf)
"""

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "June. 2013"
__status__ = "Development"
__license__ = "LGPL"

import serial
import threading
import time
import struct
import math
from collections import namedtuple

#
# Create physical characteristics
#

WHEEL_TO_WHEEL_DIST = 260 # mm
MAX_ABSOLUTE_SPEED = 500 # mm/sec

#
# Open Interface command opcodes
#

OI_SOFT_RESET				= 7
OI_START 					= 128
OI_MODE_PASSIVE				= OI_START
OI_MODE_SAFE				= 131
OI_MODE_FULL				= 132
OI_DRIVE					= 137
OI_DRIVE_DIRECT				= 145
OI_LEDS						= 139
OI_DIGITAL_OUTPUTS			= 147
OI_LOW_SIDE_DRIVERS			= 138
OI_SEND_IR					= 151
OI_READ_SENSORS				= 142
OI_READ_SENSOR_LIST			= 149
OI_STREAM_SENSOR_LIST		= 148
OI_STREAM_PAUSE_RESUME		= 150
OI_SCRIPT_DEFINE			= 152
OI_SCRIPT_PLAY				= 153
OI_SCRIPT_SHOW				= 154
OI_WAIT_TIME			    = 155
OI_WAIT_DISTANCE			= 156
OI_WAIT_ANGLE				= 157
OI_WAIT_EVENT				= 158

#
# LEDs related defines
#

# power LED color
OI_LED_GREEN	= 0
OI_LED_YELLOW	= 63
OI_LED_ORANGE	= 127
OI_LED_RED		= 255
# power LED pre-defined intensities
OI_LED_OFF		= 0
OI_LED_FULL		= 255
OI_LED_ON		= OI_LED_FULL

# "play" LED bit mask
OI_LED_PLAY		= 2
# "advance" LED bit mask
OI_LED_ADVANCE	= 8

OI_ALL_LEDS     = OI_LED_PLAY | OI_LED_ADVANCE

#
# Buttons masks and names
#

OI_BUTTONS_PLAY			= 1
OI_BUTTONS_ADVANCE		= 4
OI_ALL_BUTTONS          = OI_BUTTONS_PLAY | OI_BUTTONS_ADVANCE

OI_BUTTON_NAMES = {
    1: "play",
    4: "advance"
}

#
# Digital outputs
#

OI_DOUT_0		= 1
OI_DOUT_1		= 2
OI_DOUT_2		= 4
OI_ALL_DOUTS    = OI_DOUT_0 | OI_DOUT_1 | OI_DOUT_2

#
# Low side drivers
#

OI_DRIVER_0		= 1
OI_DRIVER_1		= 2
OI_DRIVER_2		= 4
OI_ALL_DRIVERS  = OI_DRIVER_0 | OI_DRIVER_1 | OI_DRIVER_2

#
# Special values for the radius parameter of the "drive" command
#

OI_DRIVE_STRAIGHT		= 0x8000
OI_SPIN_CW				= 0xFFFF
OI_SPIN_CCW				= 0x0001

#
# Logic sensors masks
#

OI_BUMPER_RIGHT			= 0x01
OI_BUMPER_LEFT			= 0x02
OI_WHEEL_DROP_RIGHT		= 0x04
OI_WHEEL_DROP_LEFT		= 0x08
OI_CASTER_DROP			= 0x10
OI_ALL_SENSORS          = 0x1f

#
# Drivers and wheel overcurrent flags masks
#

OI_OVERCURRENT_DRV_0    = 0x02
OI_OVERCURRENT_DRV_1    = 0x01
OI_OVERCURRENT_DRV_2    = 0x04
OI_OVERCURRENT_WHEEL_R  = 0x08
OI_OVERCURRENT_WHEEL_L  = 0x10

#
# Sensor packets
#

OI_PACKET_GROUP_0					= 0

OI_PACKET_GROUP_1					= 1
OI_PACKET_GROUP_SENSOR_STATES		= OI_PACKET_GROUP_1

OI_PACKET_BUMPS_AND_WHEEL_DROPS		= 7
OI_PACKET_WALL						= 8
OI_PACKET_CLIFF_LEFT				= 9
OI_PACKET_CLIFF_FRONT_LEFT			= 10
OI_PACKET_CLIFF_FRONT_RIGHT			= 11
OI_PACKET_CLIFF_RIGHT				= 12
OI_PACKET_VIRTUAL_WALL				= 13
OI_PACKET_OVERCURRENT               = 14
OI_PACKET_UNUSED_1					= 15
OI_PACKET_UNUSED_2					= 16

OI_PACKET_GROUP_2					= 2
OI_PACKET_GROUP_UI_AND_ODOMETRY     = OI_PACKET_GROUP_2

OI_PACKET_RECEIVED_IR_BYTE			= 17
OI_PACKET_BUTTONS					= 18
OI_PACKET_DISTANCE					= 19
OI_PACKET_ANGLE						= 20

OI_PACKET_GROUP_3					= 2
OI_PACKET_GROUP_BATTERY				= OI_PACKET_GROUP_3

OI_PACKET_CHARGING_STATE			= 21
OI_PACKET_BATTERY_VOLTAGE			= 22
OI_PACKET_BATTERY_CURRENT			= 23
OI_PACKET_BATTERY_TEMPERATURE		= 24
OI_PACKET_BATTERY_CHARGE			= 25
OI_PACKET_BATTERY_CAPACITY			= 26

OI_PACKET_GROUP_4					= 4
OI_PACKET_GROUP_SIGNALS				= OI_PACKET_GROUP_4

OI_PACKET_WALL_SIGNAL				= 27
OI_PACKET_CLIFF_LEFT_SIGNAL			= 28
OI_PACKET_CLIFF_FRONT_LEFT_SIGNAL	= 29
OI_PACKET_CLIFF_FRONT_RIGHT_SIGNAL	= 30
OI_PACKET_CLIFF_RIGHT_SIGNAL		= 31
OI_PACKET_CARGO_BAY_DIGITAL_IN		= 32
OI_PACKET_CARGO_BAY_ANALOG_IN		= 33
OI_PACKET_CHARGING_SOURCES			= 34

OI_PACKET_GROUP_5					= 5
OI_PACKET_GROUP_MISC   				= OI_PACKET_GROUP_5

OI_PACKET_CURRENT_MODE				= 35
OI_PACKET_SONG_NUMBER				= 36
OI_PACKET_SONG_PLAYING				= 37
OI_PACKET_STREAM_PACKETS_COUNT		= 38
OI_PACKET_REQUESTED_VELOCITY		= 39
OI_PACKET_REQUESTED_RADIUS			= 40
OI_PACKET_REQUESTED_VELOCITY_RIGHT	= 41
OI_PACKET_REQUESTED_VELOCITY_LEFT	= 42

OI_PACKET_GROUP_6					= 6
OI_PACKET_GROUP_ALL					= OI_PACKET_GROUP_6

OI_PACKET_MIN                       = OI_PACKET_GROUP_0
OI_PACKET_MAX                       = OI_PACKET_REQUESTED_VELOCITY_LEFT

# 
# Packet sizes array, indexed by packets ids
#

OI_PACKET_SIZES = [
    26, 10, 6, 10, 14, 12, 52,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
    1, 1, 2, 2,
    1, 2, 2, 1, 2, 2,
    2, 2, 2, 2, 2, 1, 2, 1,
    1, 1, 1, 1, 2, 2, 2, 2
]

# Packet header byte when straming is used

OI_PACKET_HEADER		= 19

#
# Array of the npack formats for packet groups,
# indexed by the group id

PACKET_STRUCT_FORMATS = [
    None,
    '!BBBBBBBBBB',
    '!BBhh',
    '!BHhbHH',
    '!HHHHHBHB',
    '!BBBBhhhh',
    None
]
# compute the formats of compound packets
PACKET_STRUCT_FORMATS[0] = \
        PACKET_STRUCT_FORMATS[1] + \
        PACKET_STRUCT_FORMATS[2][1:] + \
        PACKET_STRUCT_FORMATS[3][1:]
PACKET_STRUCT_FORMATS[6] = \
        PACKET_STRUCT_FORMATS[0] + \
        PACKET_STRUCT_FORMATS[4][1:] + \
        PACKET_STRUCT_FORMATS[5][1:]

#
# Named tuples used for packet groups friendly unpacking
#

GroupPacket1 = namedtuple('GroupPacket1', [
    'bumps_and_wheels',
    'wall',
    'cliff_left',
    'cliff_front_left',
    'cliff_front_right',
    'cliff_right',
    'virtual_wall',
    'overcurrents',
    'unused1',
    'unused2'
])

GroupPacket2 = namedtuple('GroupPacket2', [
    'ir_byte',
    'buttons',
    'distance',
    'angle'
])

GroupPacket3 = namedtuple('GroupPacket3', [
    'charging_state',
    'voltage',
    'current',
    'battery_temp',
    'battery_charge',
    'battery_capacity'
])

GroupPacket4 = namedtuple('GroupPacket4', [
    'wall_signal',
    'cliff_left_signal',
    'cliff_front_left_signal',
    'cliff_front_right_signal',
    'cliff_right_signal',
    'user_dins',
    'user_ain',
    'charging_sources'
])

GroupPacket5 = namedtuple('GroupPacket5', [
    'oi_mode',
    'song_number',
    'song_playing',
    'nb_of_stream_packets',
    'velocity',
    'radius',
    'right_velocity',
    'left_velocity'
])

# Index of namedtuples, keyed by the corresponding group packet id

GROUP_PACKET_CLASSES = [
    None,
    GroupPacket1,
    GroupPacket2,
    GroupPacket3,
    GroupPacket4,
    GroupPacket5
]

#
# Stream listener FSM states (internal use)
#

_STATE_IDLE = 0
_STATE_GOT_HEADER = 1
_STATE_GOT_LENGTH = 2
_STATE_IN_PACKET = 3
_STATE_IN_CHECKSUM = 4

#
# Wait events
#

OI_WAIT_WHEEL_DROP              = 1
OI_WAIT_FRONT_WHEEL_DROP        = 2
OI_WAIT_LEFT_WHEEL_DROP         = 3
OI_WAIT_RIGHT_WHEEL_DROP        = 4
OI_WAIT_BUMP                    = 5
OI_WAIT_LEFT_BUMP               = 6
OI_WAIT_RIGHT_BUMP              = 7
OI_WAIT_VIRTUAL_WALL            = 8
OI_WAIT_WALL                    = 9
OI_WAIT_CLIFF                   = 10
OI_WAIT_LEFT_CLIFF              = 11
OI_WAIT_FRONT_LEFT_CLIFF        = 12
OI_WAIT_FRONT_RIGHT_CLIFF       = 13
OI_WAIT_RIGHT_CLIFF             = 14
OI_WAIT_HOME_BASE               = 15
OI_WAIT_BTN_ADVANCE             = 16
OI_WAIT_BTN_PLAY                = 17
OI_WAIT_DIN0                    = 18
OI_WAIT_DIN1                    = 19
OI_WAIT_DIN2                    = 20
OI_WAIT_DIN3                    = 21
OI_WAIT_PASSIVE_MODE            = 22

OI_WAIT_EVENT_MIN               = OI_WAIT_WHEEL_DROP
OI_WAIT_EVENT_MAX               = OI_WAIT_PASSIVE_MODE

def inverse(b):
    """ Two-complement inverse value computation, use to wait
    for the negation of a given event in the above list."""
    return (~b & 0xff) + 1


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
        return [OI_DRIVE] + _int16_to_bytes(velocity) + _int16_to_bytes(radius)

    @staticmethod
    def drive_direct(velocity_right, velocity_left):
        return [OI_DRIVE_DIRECT] + _int16_to_bytes(velocity_right) + _int16_to_bytes(velocity_left)

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
        return [OI_WAIT_DISTANCE] + _int16_to_bytes(distance)

    @staticmethod
    def wait_angle(angle):
        return [OI_WAIT_ANGLE] + _int16_to_bytes(angle)

    @staticmethod
    def wait_event(event):
        return [OI_WAIT_EVENT, event & 0xff]

def _hex_format(b):
    return '%02x' % ord(b)

def _dec_format(b):
    return str(ord(b))

class IRobotCreate(object):
    """ Models the Create robot and provides convenient methods to interact with it.

    Note that this class does not make use of the Command one to avoid stacking
    too many method calls. It could have be done to avoid duplicating in some
    way the command definitions, but the benefit didn't compensate the drawbacks.
    """

    def __init__(self, port, baudrate=57600, debug=False, simulate=False, hexdebug=False):
        """ Constructor:

        Arguments:
            port:
                the serial port used for the serial link with it
            baudrate:
                serial link speed (default: 57600)
            debug:
                if True, activates the trace of serial data exchanges and various
                other debugging help
            simulate:
                if True, simulate data exchanges
            hexdebug:
                displays bytes in hex format in the trace (default format is
                decimal, since used by all the examples included in the documentation)
        """
        self._serial = serial.Serial(port, baudrate=baudrate, timeout=0.5)
        self._serial.flushInput()
        self._serial.flushOutput()

        # I/O serialization lock to be as much thread safe as possible
        self._lock = threading.Lock()

        self._debug = debug
        self._debug_fmt = _hex_format if hexdebug else _dec_format
        self._hexdebug = hexdebug
        self._simulate = simulate

        self._stream_listener = None
        self._timer = None

    @property
    def serial(self):
        """ Access to the serial link instance."""
        return self._serial

    @property
    def debug_settings(self):
        """ Provides the current debug settings as a tuple containing :
            - the debug status
            - the debug format for serial data trace
            - the simulate option state
        """
        return (self._debug, self._debug_fmt, self._simulate)

    def _send_block(self, data):
        if not isinstance(data, str):
            # stringify a byte list
            data = ''.join([chr(b) for b in data])

        if self._debug or self._simulate:
            print(':Tx> %s' % ' '.join(self._debug_fmt(b) for b in data))
        if self._simulate:
            return
        with self._lock:
            self._serial.write(data)
            self._serial.flush()

    def _send_byte(self, byte):
        self._send_block(chr(byte))

    def _get_reply(self, nbytes):
        if self._simulate:
            print ('<Rx: -- no Rx data when running in simulated I/O mode --')
            return []

        with self._lock:
            data = ''
            cnt = 0
            maxwait = time.time() + self._serial.timeout
            while cnt < nbytes and time.time() < maxwait:
                data = data + self._serial.read(nbytes - cnt)
                cnt = len(data)
            self._serial.flushInput()

        if self._debug:
            rx = ' '.join(self._debug_fmt(b) for b in data)
            print('<Rx: %s' % rx)

        return data

    def start(self, mode=OI_MODE_PASSIVE):
        """ Initializes the Create.

        Includes a short pause for letting enough time to the beast for
        getting ready.

        Parameters:
            mode:
                the mode in which to place the Create (default: passive)

        Raises:
            ValueError if mode parameter is not of the expected ones
        """
        self._send_byte(OI_START)
        if mode != OI_MODE_PASSIVE:
            self.set_mode(mode)
        time.sleep(1)

    def reset(self):
        """ Soft reset of the Create."""
        self._send_byte(OI_SOFT_RESET)

    def set_mode(self, mode):
        """ Sets the operating mode of the Create.

        Parameters:
            mode:
                the mode in which to place the Create (default: passive)

        Raises:
            ValueError if mode parameter is not of the expected ones
        """
        if mode in [OI_MODE_PASSIVE, OI_MODE_SAFE, OI_MODE_FULL]:
            self._send_byte(mode)
            # force the power LED to stay on in full mode (otherwise one may
            # think the beast has been turned off
            if mode == OI_MODE_FULL:
                self.set_leds(0, OI_LED_GREEN, OI_LED_FULL)
        else:
            raise ValueError('invalid mode (%s)' % mode)

    def passive_mode(self):
        """ Shorthand form for passive mode setting."""
        self.set_mode(OI_MODE_PASSIVE)

    def safe_mode(self):
        """ Shorthand form for safe mode setting."""
        self.set_mode(OI_MODE_SAFE)

    def full_mode(self):
        """ Shorthand form for full mode setting."""
        self.set_mode(OI_MODE_FULL)

    def _delayed_stop_move(self):
        self.stop_move()
        self._timer = None

    def _cancel_delayed_stop_move(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None

    def drive(self, velocity, radius=OI_DRIVE_STRAIGHT, distance=None):
        """ Makes the robot drive, based on speed and path curvature.

        If a distance is provided, a delayed stop is initiated (using a Timer),
        based on the time for this distance to be traveled using the requested
        speed.

        If no distance is provided, it is up to the caller to manage when to stop
        or change the move.

        In both cases, the methods exits immediatly.

        Note:
            The distance checking is implemented using a poor man's strategy
            based on the ETA (estimated time of arrival).
            Another strategy would be to create a short script using a wait_distance
            command and run it. Although it has chances to be more accurate, this
            has the nasty drawback to "mute the line" while the script is running,
            and thus preventing any event (such as bumper hit) or commands to be
            exchanged.

        Parameters:
            velocity:
                robot's center velocity (in mm/sec)
            radius:
                radius (in mm) of the path to be folowed
                (defaut: special value corresponding to a straight path
            distance:
                distance to be traveled (in mm). If provided, the method
                will exists only after this distance is supposed to be traveled,
                based on the requested speed. If no distance is provided, the
                method exists at once, leaving to robot moving.

        Raises:
            ValueError if velocity is outside valid range
        """
        # be sure we will not get a pending stop during the move
        self._cancel_delayed_stop_move()

        if distance is not None and distance == 0:
            return

        if not -MAX_ABSOLUTE_SPEED <= velocity <= MAX_ABSOLUTE_SPEED:
            raise ValueError('invalid velocity (%f)' % velocity)

        self._send_block([OI_DRIVE] + _int16_to_bytes(velocity) + _int16_to_bytes(radius))
        if distance:
            self._timer = threading.Timer(
                time_for_distance(distance, velocity),
                self._delayed_stop_move
            )
            self._timer.start()

    def drive_direct(self, left_vel, right_vel):
        """ Makes the robot drive by directly setting the wheel speeds.

        No distance control is proposed here.

        Parameters:
            left_vel, right_vel:
                wheel velocities (in mm/sec)
        """
        # be sure we will not get a pending stop during the move
        self._cancel_delayed_stop_move()

        self._send_block([OI_DRIVE_DIRECT] + _int16_to_bytes(left_vel) + _int16_to_bytes(right_vel))

    def stop_move(self):
        """ Stops any current move."""
        self._cancel_delayed_stop_move()
        self.drive_direct(0, 0)

    def spin(self, velocity, spin_dir=OI_SPIN_CW, angle=None):
        """ Makes the robot spin on itself at a given speed.

        If a spin angle is provided, the method will wait for the time for this angle
        to be reached (based on the requested speed) and then stops the robot and exit.
        In addition, the provided spin direction (if any) is ignored, and replaced by
        the one infered from the angle sign (positive = CCW)

        If no angle is provided, the move is initiated and the method exits immédiatly,
        leaving the robot moving. It is the responsabilitéy of the caller to handle
        what should happen then.

        See drive() method documentation for implementation note about the strategy
        used to track the angle.

        Parameters:
            velocity:
                robot's wheels velocity (in mm/sec)
            spin_dir:
                the spin direction (CW or CCW) (default: CW)
            angle:
                optional spin angle (in degrees)

        Raises:
            ValueError if spin direction is invalid
        """
        # be sure we will not get a pending stop during the move
        self._cancel_delayed_stop_move()

        if angle is not None:
            if angle != 0:
                spin_dir = OI_SPIN_CCW if angle > 0 else OI_SPIN_CW
            else:
                return
        elif spin_dir not in [OI_SPIN_CCW, OI_SPIN_CW]:
            raise ValueError('invalid spin direction (%d)' % spin_dir)

        self.drive(velocity, spin_dir)
        if angle:
            self._timer = threading.Timer(
                time_for_angle(angle, velocity),
                self._delayed_stop_move
            )
            self._timer.start()

    def set_leds(self, led_bits, pwr_color, pwr_lvl):
        """ Changes the state of the Create LEDs.

        Parameters:
            led_bits:
                a bits mask providing the ON status of the PLAY and ADVANCE LEDs
            pwr_color:
                the color of the POWER LED
            pwr_level:
                the intensity of the POWER LED
        """
        self._send_block([OI_LEDS,
                        led_bits & OI_ALL_LEDS,
                        pwr_color & 0xff,
                        pwr_lvl & 0xff
                        ])

    def set_digital_outs(self, states):
        """ Changes the state of the Create digital outputs.

        Parameters:
            states:
                a bit mask containing the state of the DOUTs
        """
        self._send_block([OI_DIGITAL_OUTPUTS,
                        states & OI_ALL_DOUTS
                        ])

    def set_low_side_drivers(self, states):
        """ Changes the state of the Create low-side drivers.

        Parameters:
            states:
                a bit mask containing the state of the LSDs
        """
        self._send_block([OI_LOW_SIDE_DRIVERS,
                        states & OI_ALL_DRIVERS
                        ])

    def send_ir(self, data):
        """ Emits an IR byte.

        Parameters:
            data:
                the byte to be sent
        """
        self._send_block([OI_SEND_IR,
                        data & 0xff
                        ])

    def get_sensor_packet(self, packet_id):
        """ Gets a sensor packet or packets group.

        Parameters:
            packet_id:
                the id of the requested packet or group

        Returns:
            the reply returned by the Create

        Raises:
            ValueError if invalid packet id
        """
        if not OI_PACKET_MIN <= packet_id <= OI_PACKET_MAX:
            raise ValueError('invalid packet id (%d)' % packet_id)

        self._send_block([OI_READ_SENSORS,
                        packet_id & 0xff
                        ])
        return self._get_reply(OI_PACKET_SIZES[packet_id])


    def get_unpacked_sensor_packet(self, packet_id):
        """ Convenience method wich returns an unpacked form for some
        of the packet groups.

        It only works for groups 1 to 5.

        Parameters:
            packet_id:
                the requested packet group id

        Returns:
            the reply unpacked as the corresponding namedtuple

        Raises:
            ValueError in packet_id is out of range
        """
        if not 1 <= packet_id <= 5:
            raise ValueError('out of range packet id (%d)' % packet_id)

        data = self.get_sensor_packet(packet_id)
        return GROUP_PACKET_CLASSES[packet_id]._make(   #pylint: disable=W0212
            struct.unpack_from(PACKET_STRUCT_FORMATS[packet_id], data)
        )

    def get_sensor_packet_list(self, packet_ids):
        """ Gets a list of sensor packets.

        Parameters:
            packed_ids:
                a list containing the ids of the requested packets

        Returns:
            a list containing the corresponding packets returned by the Create
        """
        self._send_block([OI_READ_SENSOR_LIST, len(packet_ids)] + packet_ids)
        nbytes = reduce(
            lambda x, y: x + y,
            [OI_PACKET_SIZES[id_] for id_ in packet_ids if 0 <= id_ <= 42]
        )
        return self._get_reply(nbytes)

    def get_unpacked_sensor_packet_list(self, packet_ids):
        """ Same as get_unpacked_sensor_packet, but for a list of packets.

        Same restrictions apply for the packet ids.

        Parameters:
            packet_ids:
                a list containing the ids of the requested packets
        """
        data = self.get_sensor_packet_list(packet_ids)
        res = []
        pos = 0

        for id_ in packet_ids:
            if not 1 <= id_ <= 5:
                raise ValueError('out of range packet id (%d)' % id_)

            lg = OI_PACKET_SIZES[id_]
            res.append(
                GROUP_PACKET_CLASSES[id_]._make(        #pylint: disable=W0212
                    struct.unpack_from(
                        PACKET_STRUCT_FORMATS[id_],
                        data[pos : pos + lg]
                    )
                )
            )
            pos += lg
        return res

    def get_buttons(self):
        """ Gets the current state of the buttons, as the list of pressed ones.

        The returned list contains the button ids (OI_BUTTONS_xxx) and can be
        empty if no button is currently pressed.
        """
        reply = self.get_sensor_packet(OI_PACKET_BUTTONS)
        return byte_to_buttons(reply[0])

    def get_bumpers(self):
        """ Gets the current state of the bumper, as the list of pressed parts.

        The returned list contains the bumper part ids (OI_BUMPER_xxx) and can be
        empty if the bumper is currently not pressed.
        """
        reply = self.get_sensor_packet(OI_PACKET_BUMPS_AND_WHEEL_DROPS)
        return byte_to_bumpers(reply[0])

    def get_wheel_drops(self):
        """ Gets the current state of the wheel drop sensors, as the list of
        dropped ones.

        The returned list contains the drop sensor (OI_WHEEL_DROP_xxx, OI_CASTER_DROP)
        and can be empty if all wheels are on the ground.
        """
        reply = self.get_sensor_packet(OI_PACKET_BUMPS_AND_WHEEL_DROPS)
        return byte_to_wheel_drops(reply[0])

    def define_script(self, script):
        """ Records a script to be played later.

        The Command class can be used to make easier the building of the
        script bytes sequence.

        Parameters:
            script:
                the script, as its bytes sequence
        """
        self._send_block([OI_SCRIPT_DEFINE, len(script) & 0xff] + script)

    def play_script(self):
        """ Plays the previously recorded script."""
        self._send_byte(OI_SCRIPT_PLAY)

    def _start_stream_listener(self, packet_event):
        self._stream_listener = StreamListener(self, packet_event)
        self._stream_listener.start()

    def _kill_stream_listener(self):
        self._stream_listener.stop()
        self._stream_listener = None

    def stream_packets(self, packet_ids, packet_event):
        """ Starts the continuous stream of sensor packets.

        Parameters:
            packet_ids:
                the list of the ids of the packet to be streamed
            packet_event:
                an instance of threading.Event used to signal the availability
                of packets and communicate them to the caller
        """
        if not self._stream_listener:
            self._start_stream_listener(packet_event)
        self._send_block([OI_STREAM_SENSOR_LIST, len(packet_ids) & 0xff] + packet_ids)

    def stream_pause(self, paused):
        """ Pauses or resumes the packets streaming."""
        self._send_block([OI_STREAM_PAUSE_RESUME, 1 if paused else 0])

    def stream_shutdown(self):
        """ Shutdowns an ongoing packet streaming.

        It is a good habit to call this method before leaving the application,
        to avoid letting orphan threads alive. Calling it if not streaming is
        active does not harm, since not done.
        """
        if self._stream_listener:
            self.stream_pause(True)
            self._kill_stream_listener()

class StreamListener(threading.Thread):
    """ The packet stream listener.

    This class is internal use only and is not supposed to be used
    by the application.
    """
    def __init__(self, robot, packet_event):
        threading.Thread.__init__(self)
        self.name = 'stream_listener'
        self._stopevent = threading.Event()
        self._robot = robot
        self._packet_event = packet_event

    def run(self):
        _serial = self._robot.serial
        debug, _dbgfmt, _siumlate = self._robot.debug_settings
        _serial.flushInput()
        state = _STATE_IDLE
        packets = []
        total_expected = expected_bytes = 0
        packet_id = 0
        packet_data = ''
        while not self._stopevent.isSet():
            while _serial.inWaiting():
                b = ord(_serial.read()[0])
                if debug:
                    print('<Rx: %d - state=%d - total_expected=%d - expected_bytes=%d' %
                          (b, state, total_expected, expected_bytes)
                          )
                if state == _STATE_IDLE:
                    if b == OI_PACKET_HEADER:
                        packets = []
                        state = _STATE_GOT_HEADER

                elif state == _STATE_GOT_HEADER:
                    total_expected = b
                    state = _STATE_GOT_LENGTH

                elif state == _STATE_GOT_LENGTH:
                    packet_id = b
                    packet_data = ''
                    expected_bytes = OI_PACKET_SIZES[packet_id]
                    total_expected -= 1
                    state = _STATE_IN_PACKET

                elif state == _STATE_IN_PACKET:
                    packet_data += chr(b)
                    total_expected -= 1
                    expected_bytes -= 1
                    if expected_bytes == 0:
                        packets.append((packet_id, packet_data))
                        if total_expected == 0:
                            state = _STATE_IN_CHECKSUM

                elif state == _STATE_IN_CHECKSUM:
                    # don't care checking for the moment

                    # notify a set of packets is available
                    self._packet_event.packets = packets
                    self._packet_event.set()

                    state = _STATE_IDLE

            # check if someone requested us to stop
            self._stopevent.wait(0.01)

    def stop(self):
        self._stopevent.set()

def _int16_to_bytes(v):
    """ Convenience function to convert a 16 bits int into the corresponding
    bytes sequence."""
    i16 = int(v)
    return [(i16 & 0xff00) >> 8, i16 & 0xff]

def byte_to_buttons(byte):
    """ Convenience function to convert a bit mask byte into a list of button ids."""
    return [b for b in [OI_BUTTONS_PLAY, OI_BUTTONS_ADVANCE] if b & int(byte)]

def byte_to_bumpers(byte):
    """ Convenience function to convert a bit mask byte into a list of bumper parts."""
    return [b for b in [OI_BUMPER_LEFT, OI_BUMPER_RIGHT] if b & int(byte)]

def byte_to_wheel_drops(byte):
    """ Convenience function to convert a bit mask byte into a list of wheel drop sensors."""
    return [b for b in [OI_WHEEL_DROP_LEFT, OI_WHEEL_DROP_RIGHT, OI_CASTER_DROP] if b & int(byte)]

def leds_to_byte(leds):
    """ Convenience function to convert a list of LEDs to the corresponding bit mask."""
    return reduce(lambda x, y : x | y, int(leds))

def dump_group_packets(gpackets):
    """ Helper function printing a list of packets in a friendly way.

    Works only for packets havind a namedtuple associated representation.
    """
    if type(gpackets) is not list:
        gpackets = [gpackets]
    for pkt in gpackets:
        print("%s : " % type(pkt).__name__)
        for k, v in pkt._asdict().iteritems():          #pylint: disable=W0212
            print(" - %s : %s" % (k, v))

def time_for_distance(dist_mm, velocity):
    """ Returns the theoritical time required to travel a given distance
    at a given speed."""
    return abs(float(dist_mm) / velocity)

def time_for_angle(angle_deg, velocity):
    """ Returns the theoritical time required to spin  a given angle
    with a given wheel speed."""
    return time_for_distance(
        math.radians(angle_deg) * WHEEL_TO_WHEEL_DIST / 2,
        velocity
    )

def make_script(*commands):
    """ Returns the bytes sequence of a script composed of the given commands."""
    return reduce(lambda x, y: x + y, commands)

