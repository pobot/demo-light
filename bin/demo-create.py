#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Several simple demos illustrating usages of the irobot module."""

import traceback
import sys
from functools import wraps
import textwrap
import random
import time
import os

from pybot import cli, irobot, log, simpleconfig

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "July. 2013"
__status__ = "Development"
__license__ = "LGPL"

_all_demos = {}

def demo_method(meth):
    """ Decorator for declaring methods implementing a demo scenario.

    Store the method docstring in the global dictionary, keying it with
    the method name as demo name.
    """
    _all_demos[meth.__name__] = meth.__doc__

    @wraps(meth)
    def wrapped(*args, **kwargs):
        return meth(*args, **kwargs)

    return wrapped

class Demo(object):
    """ A class which runs a demo, bundles all existing ones, and takes care of common tasks.

    For executing a given demo, just instantiate it, passing the name of the demo to be
    executed, and its arguments if any. Then call the run() method. That's it.
    """

    def __init__(self, name, args):
        """ Constructor.

        Parameters:
            name:
                the name of the demo, used to select the method which implements it

            args:
                the args to be passed to the method
        """
        self._logger = log.getLogger('demo-create')
        self._name = name
        self._meth = getattr(self, self._name)
        self._args = args

    def run(self):
        """ Run the demo. """
        self._logger.info("Initializing robot..")
        robot = irobot.IRobotCreate(
            port=self._args.port,
            debug=self._args.debug,
            trace=self._args.trace
        )
        robot.start(irobot.OI_MODE_FULL)

        self._logger.info("Starting demo '%s'...", self._name)
        self._meth(robot, log.getLogger(self._name))
        self._logger.info('Demo complete.')

    @demo_method
    def square(self, robot, _log):
        """ Drive along an almost 30 cm wide square, finishing the ride by a reverse
        direction spin to untwist the cables, in case the robot is tethered.
        """
        square_size = 300
        linear_velocity = 300
        angular_velocity = linear_velocity * 0.66

        for _ in xrange(3):
            robot.drive(velocity=linear_velocity, distance=square_size)
            robot.spin(velocity=angular_velocity, spin_dir=irobot.OI_SPIN_CCW, angle=90)

        robot.drive(velocity=linear_velocity, distance=square_size)
        robot.spin(velocity=angular_velocity, spin_dir=irobot.OI_SPIN_CW, angle=270)

        robot.stop_move()

    @demo_method
    def script_leds(self, robot, _log):
        """ Execute a script which lights the "play" LED when the bumper is pressed."""
        robot.define_script(irobot.make_script(
            irobot.Command.wait_event(irobot.OI_WAIT_BUMP),
            irobot.Command.wait_event(irobot.inverse(irobot.OI_WAIT_BUMP)),
            irobot.Command.leds(irobot.OI_LED_PLAY, irobot.OI_LED_OFF, irobot.OI_LED_OFF),
            irobot.Command.wait_event(irobot.OI_WAIT_BUMP),
            irobot.Command.wait_event(irobot.inverse(irobot.OI_WAIT_BUMP)),
            irobot.Command.leds(irobot.OI_LED_OFF, irobot.OI_LED_OFF, irobot.OI_LED_OFF),
            irobot.Command.play_script()
        )
        )
        robot.play_script()

    @demo_method
    def script_square(self, robot, _log):
        """ Same as 'square' demo, but using a script with 'wait distance'
        and 'wait angle' statements."""
        robot.define_script(irobot.make_script(
            # 1st side
            irobot.Command.drive(200),
            irobot.Command.wait_distance(300),
            irobot.Command.drive(200, irobot.OI_SPIN_CCW),
            irobot.Command.wait_angle(90),
            # 2nd side
            irobot.Command.drive(200),
            irobot.Command.wait_distance(300),
            irobot.Command.drive(200, irobot.OI_SPIN_CCW),
            irobot.Command.wait_angle(90),
            irobot.Command.drive(200),
            # 3rd side
            irobot.Command.wait_distance(300),
            irobot.Command.drive(200, irobot.OI_SPIN_CCW),
            irobot.Command.wait_angle(90),
            irobot.Command.drive(200),
            # 4th side, ended by a reciprocal spi
            irobot.Command.wait_distance(300),
            irobot.Command.drive(200, irobot.OI_SPIN_CW),
            irobot.Command.wait_angle(-270),
            # that's all folks
            irobot.Command.stop()
        )
        )
        robot.play_script()


    @demo_method
    def stream_packets(self, robot, _log):
        """ Use packet streaming to listen for button events and light the LEDs
        accordingly."""
        unexpected = None
        evt = robot.evt_packets
        robot.stream_packets([irobot.OI_PACKET_BUTTONS])
        _log.info('Press PLAY or ADVANCE buttons. Ctrl-C to end.')
        last_state = 0
        while True:
            try:
                if evt.wait():
                    _id, pkt = evt.packets[0]
                    btn_state = ord(pkt[0])
                    if btn_state != last_state:
                        _log.info("Buttons state changed to : %s" %
                              [irobot.OI_BUTTON_NAMES[b] for b in irobot.byte_to_buttons(btn_state)]
                              )
                        last_state = btn_state

                        led_play = (irobot.OI_BUTTONS_PLAY & btn_state) != 0
                        led_advance = (irobot.OI_BUTTONS_ADVANCE & btn_state) != 0
                        robot.set_leds(led_play, led_advance)
                    evt.clear()

            except KeyboardInterrupt:
                print # cosmetic: to maintain log messages properly lined up
                _log.info('*** interrupted ***')
                break
            except Exception as e:
                unexpected = (e,)
                break

        robot.stream_shutdown()
        robot.set_leds(play=False, advance=False)
        if unexpected:
            raise unexpected[0]

    @demo_method
    def pwm_control(self, robot, _log):
        """ Controls a motor connected on driver 2 via its PWM settings."""

        for pwm in [25, 50, 75, 100, 75, 50, 25]:
            _log.info("setting PWM to %d%%", pwm)
            robot.low_side_driver_pwm(drv2=pwm)
            time.sleep(3)

        _log.info("That's all folks")
        robot.set_low_side_driver(0)


    @demo_method
    def avoid_obstacles(self, robot, _log):
        """ Drive until an obstacle is hit. Back a bit and spin randomly before resuming
        the cruise."""
        unexpected = None
        evt_packets = robot.evt_packets
        evt_move = robot.evt_move
        robot.stream_packets([irobot.OI_PACKET_BUMPS_AND_WHEEL_DROPS])
        _log.info('Start wandering around. Ctrl-C to end.')
        last_state = 0
        robot.drive(velocity=200)
        while True:
            try:
                if evt_packets.wait():
                    _id, pkt = evt_packets.packets[0]
                    new_state = ord(pkt[0])
                    if new_state != last_state:
                        bumpers = irobot.byte_to_bumpers(new_state)
                        if bumpers:
                            _log.info("Hit bumpers on : %s" %
                                  [irobot.OI_BUMPER_NAMES[b] for b in bumpers]
                                  )
                            robot.set_leds(
                                play=irobot.OI_BUMPER_LEFT in bumpers,
                                advance=irobot.OI_BUMPER_RIGHT in bumpers
                            )
                            # escape
                            robot.drive(velocity=-200, distance=random.randint(50, 100))
                            if not evt_move.wait(2):
                                _log.error('timeout while waiting for drive completion')

                            if len(bumpers) == 1:
                                escape_dir = -1 if irobot.OI_BUMPER_LEFT in bumpers else +1
                            else:
                                escape_dir = random.choice([-1, +1])
                            robot.spin(200, angle=escape_dir * random.randint(30, 110))
                            if not evt_move.wait(2):
                                _log.error('timeout while waiting for spin completion')

                            # resume cruising
                            robot.drive(velocity=200)
                            robot.set_leds(play=False, advance=False)

                        last_state = new_state

                    evt_packets.clear()

            except KeyboardInterrupt:
                print # cosmetic: to maintain log messages properly lined up
                _log.info('*** interrupted ***')
                break
            except Exception as e:
                unexpected = (e,)
                break

        robot.stop_move()
        robot.stream_shutdown()
        robot.set_leds(play=False, advance=False)
        if unexpected:
            raise unexpected[0]

    @demo_method
    def play_music(self, robot, _log):
        """ Play some music."""
        s = irobot.Song()
        s.encode([
            ('D', 3, 11),
            ('D', 3, 11),
            ('D', 3, 11),
            ('G', 3, 66),
            ('D', 4, 66),
            ('C', 4, 11),
            ('B', 3, 11),
            ('A', 3, 11),
            ('G', 5, 66),
            ('D', 4, 66),
            ('C', 4, 11),
            ('B', 3, 11),
            ('A', 3, 11),
            ('G', 5, 66),
            ('D', 4, 66),
            ('C', 4, 11),
            ('B', 3, 11),
            ('C', 4, 11),
            ('A', 3, 66),
            ('D', 3, 25),
            ('D', 3,  8),
            ('G', 3, 66),
            ('D', 4, 66),
            ('C', 4, 11),
            ('B', 3, 11),
            ('A', 3, 11),
            ('G', 5, 66),
            ('D', 4, 66),
            ('C', 4, 11),
            ('B', 3, 11),
            ('A', 3, 11),
            ('G', 5, 66),
            ('D', 4, 66),
            ('C', 4, 11),
            ('B', 3, 11),
            ('C', 4, 11),
            ('A', 3, 33),
        ])
        sequence = robot.song_sequence_record(0, s.score)
        robot.song_sequence_play(sequence)


if __name__ == '__main__':
    dflt_search_path = [
        '/etc/demo-create.cfg',
        os.path.expanduser('~/.demo-create.cfg')
    ]

    cfg = simpleconfig.parse(files=dflt_search_path, defaults={
        'port' : '/dev/ttyUSB0'
    })

    parser = cli.get_argument_parser(
        description="Demonstration of controlling a iRobot Create robot with Python scripts."
    )
    parser.add_argument(dest='demo',
                        metavar='DEMO_NAME',
                        choices=_all_demos.keys() + ['?'],
                        nargs=1,
                        help="demonstration selector. Use '?' for a detailed list"
                        )
    parser.add_argument('-p', '--port',
                        help="Create connection serial port",
                        dest='port',
                        default=cfg['port']
                        )
    parser.add_argument('-T', '--trace',
                        help="""Trace the communications with the Create and set the display format
                        ('d' = decimal, 'h' = hex)""",
                        choices=['d', 'h'],
                        dest='trace',
                        default=None
                        )

    _args = parser.parse_args()

    demo_name = _args.demo[0]
    if demo_name == '?':
        wrapper = textwrap.TextWrapper(initial_indent='  | ', subsequent_indent='  | ')
        print("%s available demos :\n" % parser.prog)
        for _name, _doc in _all_demos.iteritems():
            txt = '\n'.join(l.strip() for l in _doc.split('\n'))
            print('- %s :\n%s\n' % (_name, wrapper.fill(txt)))
        sys.exit(0)

    try:
        demo = Demo(demo_name, _args)
        demo.run()

    except ValueError as e: #pylint: disable=W0703
        cli.die('demo error : %s' % e)

    except:
        cli.die(traceback.format_exc())


