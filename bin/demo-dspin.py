#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Demonstration script for the dSpin package."""

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "July. 2013"
__status__ = "Development"
__license__ = "LGPL"

import os
import textwrap
import argparse
from functools import wraps

from pybot import cli, dspin, log, simpleconfig

_all_demos = []

def demo_method(meth):
    """ Decorator for declaring methods implementing a demo scenario.

    Store the method docstring in the global dictionary, keying it with
    the method name as demo name.
    """
    _all_demos.append((meth.__name__, meth.__doc__))

    @wraps(meth)
    def wrapped(*args, **kwargs):
        return meth(*args, **kwargs)

    return wrapped

class Demo(object):
    """ A class which runs a demo, bundles all existing ones, and takes care of common tasks.

    For executing a given demo, just instantiate it, passing the name of the demo to be
    executed, and its arguments if any. Then call the run() method. That's it.
    """

    def __init__(self, name, _dspin, args):
        """ Constructor.

        Parameters:
            name:
                the name of the demo, used to select the method which implements it

            _dspin:
                the dSPIN interface object

            args:
                the command line arguments (containing various setting for the motor and the dSPIN)
        """
        self._logger = log.getLogger('demo-dspin')
        self._name = name
        self._meth = getattr(self, self._name)
        self._dspin = _dspin
        self._args = args

    def run(self):
        """ Run the demo. """
        sep = '-'*50
        banner = '\n%s\n%%s\n%s\n' % (sep, sep)
        print(banner % ("Starting demo '%s'..." % self._name))
        self._meth()
        print(banner % 'Demo ended.')

    @demo_method
    def config(self):
        """ Displays the current configuration of the dSPIN.  """
        print('* CONFIG register')
        regval = self._dspin.get_config()
        for k, v in dspin.unpack_config_reg(regval).iteritems():
            print("- %-15s : %s" % (k, v))

        print('\n* STEP_MODE register')
        regval = self._dspin.get_register(dspin.dSPIN_REG_STEP_MODE)
        for k, v in dspin.unpack_step_mode_reg(regval).iteritems():
            print("- %-15s : %s" % (k, v))

    @demo_method
    def status(self):
        """ Displays the current dSPIN status.  """
        _status = self._dspin.get_status()
        for k, v in dspin.unpack_status_reg(_status).iteritems():
            print("- %-15s : %s" % (k, v))

    @demo_method
    def move_to_pos(self):
        """ Moves the motor to a given position.  """

        steps_mul = 2 ** self._args.step_mode
        print('Moving 1 turn ahead...')
        self._dspin.goto_pos(self._args.resolution * steps_mul)
        self._dspin.wait_untill_not_busy()
        print('Done.')

        print('Going back to home position...')
        self._dspin.go_home()
        self._dspin.wait_untill_not_busy()
        print('Done.')


def display_demos_list():
    indent = ' '*5
    wrapper = textwrap.TextWrapper(initial_indent=indent, subsequent_indent=indent)
    sep = '-'*50
    print("\n%s\nAvailable demos :" % sep)
    for num, demo in enumerate(_all_demos):
        _name, _doc = demo
        txt = '\n'.join(l.strip() for l in _doc.split('\n'))
        print('\n[%2d] %s\n%s' % (num, _name, wrapper.fill(txt)))
    print(sep)
    print

def run_demo(args):
    _dspin = dspin.DSPin(
        cs=args.cs_gpio, stdby=args.stdby_gpio, not_busy=args.not_busy_gpio,
        debug=args.debug, trace=args.trace
    )
    _dspin.init()
    _dspin.set_max_speed(args.max_speed)
    _dspin.set_step_mode(args.step_mode)
    print('dSPIN initialized and configured with following settings :')
    print('- resolution = %d steps/turn' % args.resolution)
    print('- max speed  = %d steps/sec' % args.max_speed)
    print('- step mode  = 1/%d step' % 2 ** args.step_mode)

    display_demos_list()

    try:
        while True:
            cmde = raw_input("Demo number ('?' for help, 'q' for quit) > ").lower()
            if cmde in ['q', 'quit']:
                break
            elif cmde == '?':
                display_demos_list()

            else:
                try:
                    num = int(cmde)
                except ValueError:
                    print('*** invalid input ***')
                    continue

                try:
                    demo = Demo(_all_demos[num][0], _dspin, args)
                except IndexError:
                    print('*** invalid demo number ***')
                else:
                    demo.run()

    finally:
        print('Shutting down dSPIN...')
        _dspin.shutdown()

def step_mode(s):
    try:
        v = int(s)
    except ValueError:
        raise argparse.ArgumentTypeError('must be numeric')
    else:
        if v in xrange(8):
            return v
        else:
            raise argparse.ArgumentTypeError('must be in range [0..7]')

if __name__ == '__main__':
    CFG_FILE_NAME = os.path.splitext(os.path.basename(__file__))[0] + '.cfg'
    dflt_search_path = [
        '/etc/' + CFG_FILE_NAME,
        os.path.expanduser('~/.' + CFG_FILE_NAME)
    ]

    cfg = simpleconfig.parse(files=dflt_search_path, defaults={
        'port' : dspin.RASPI_SPI_DEVICE,
        'max_speed' : 1000,
        'step_mode' : 7,
        'resolution' : 400,
        'stdby_gpio' : 24,
        'cs_gpio' : 26,
        'not_busy_gpio' : 22
    })

    parser = cli.get_argument_parser(
        description="Demonstration of controlling a stepper motor with a dSPIN chip via SPI."
    )
    parser.add_argument('-R', '--resolution',
                        help="Stepper motor resolution (steps/turn)",
                        dest='resolution',
                        type=int,
                        default=cfg['resolution']
                        )
    parser.add_argument('-M', '--max-speed',
                        help="Maximum speed (steps/sec)",
                        dest='max_speed',
                        type=int,
                        default=cfg['max_speed']
                        )
    parser.add_argument('-S', '--step-mode',
                        help="Step mode (in range 0=full step,... 7=1/128 step)",
                        dest='step_mode',
                        type=step_mode,
                        default=cfg['step_mode']
                        )
    parser.add_argument('-s', '--stdby',
                        help="STDBY signal GPIO header pin",
                        dest='stdby_gpio',
                        type=int,
                        default=cfg['stdby_gpio']
                        )
    parser.add_argument('-c', '--cs',
                        help="CS signal GPIO header pin",
                        dest='cs_gpio',
                        type=int,
                        default=cfg['cs_gpio']
                        )
    parser.add_argument('-b', '--not_busy',
                        help="NOT_BUSY signal GPIO header pin",
                        dest='not_busy_gpio',
                        type=int,
                        default=cfg['not_busy_gpio']
                        )
    parser.add_argument('-T', '--trace',
                        help="Trace the communications with the dSpin",
                        action='store_true',
                        dest='trace',
                        default=False
                        )

    _args = parser.parse_args()

    run_demo(_args)
