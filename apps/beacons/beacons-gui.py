#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Graphical user interface for the localization beacons demonstrator.

It computes and displays the target position, based on the echo signaled by the
scaning sensors. It also provides interactions with the contraption : clicking a
beacon starts or stops it,...
"""

import argparse
import os
import sys
import math
from collections import namedtuple
import SocketServer
import select
import threading
import re
import Queue
import logging
import socket

import pygame

import findsvc

from beacons_gui.guiobjs import Logo, Hud, Beacon, Target, Help
from beacons_gui.logging_ import setup_logging

class ThreadedTCPServer(SocketServer.ThreadingMixIn, SocketServer.TCPServer):
    pass

class BeaconEventListener(threading.Thread):
    """ Listener for beacon events.

    The beacon controller notifies various events such as beacons position,
    echo detections,... by sending event to a TCP socket it connects to on demand.

    This class implements the corresponding listener as a threaded TCP socket server,
    using the BeaconEventHandler class for handling requests.

    Because of the concurrency of all the involved processes, the target echo events
    are queue so that they are not missed if the consumer does not pick them at the
    exact moment the echo is seen.

    Events are ASCII strings terminated by a newline char. Their first field is the event
    type, optionaly followed by its parameters. The event type field is separated from
    the rest of the string by a colon (':'), the parameter values being tab separated.
    """

    def __init__(self, listen_port=1235, use_2_sensors=False, debug=False):
        """ Constructor.

        Parameters:
            listen_port:
                the port on which we will listen for events
                (default: 1235)
            use_2_sensors:
                if True, each beacon uses both I/R sensors for detecting the target.
                If False, only the first one is used (LSB of the IO mask).
        """
        super(BeaconEventListener, self).__init__()
        self._srv_addr = ('', listen_port)
        self._scan_status = [False, False]
        self._beacon_headings = [0, 0]
        self._echo_queue = Queue.Queue()
        self._lock = threading.Lock()
        self._tcpsrvr = None
        self._terminated = False
        self._use_2_sensors = use_2_sensors

        self._log = logging.getLogger('listener')
        self._log.setLevel(logging.DEBUG if debug else logging.INFO)

    @property
    def terminated(self):
        return self._terminated

    def terminate(self):
        """ Terminates the socket server."""
        if self._tcpsrvr:
            self._log.info('terminate requested')
            self._terminated = True
            self._tcpsrvr.shutdown()

    @property
    def use_2_sensors(self):
        return self._use_2_sensors

    def run(self):
        """ Thread run process.

        It consists in running the socket server until this one is
        terminated by a call to our terminate() method.
        """
        self._log.info(
            'start listening for controller events on port %s...',
            self._srv_addr[1]
        )
        ThreadedTCPServer.allow_reuse_address = True
        self._tcpsrvr = ThreadedTCPServer(
            self._srv_addr,
            BeaconEventHandler
        )
        BeaconEventHandler.owner = self

        self._log.info('listening for events...')
        self._tcpsrvr.serve_forever()
        self._log.info('no more listening')
        self._tcpsrvr = None

    def post_echo_event(self, side, angle, state):
        """ Queues a tuple reporting an echo event.

        Parameters:
            side:
                the beacon side (left or side)
            angle:
                the echo direction
            state:
                True if echo start, False if echo end
        """
        self._echo_queue.put((side, angle, state))

    def get_echo_event(self):
        """ Get the next echo event (if any) from the queue."""
        try:
            return self._echo_queue.get(block=False)
        except Queue.Empty:
            return None

    def set_scan_status(self, side, status):
        """ Sets if a given beacon is currently scanning."""
        with self._lock:
            self._scan_status[side] = status

    def get_scan_status(self, side):
        """ Returns if a given beacon is currently scanning."""
        with self._lock:
            return self._scan_status[side]

    def update_beacon_heading(self, side, angle):
        """ Updates the current heading of a beacon."""
        self._beacon_headings[side] = angle

    @property
    def beacon_headings(self):
        return self._beacon_headings

class BeaconEventHandler(SocketServer.StreamRequestHandler):
    """ Request handler for the TCP server used to listen to beacon events."""
    owner = None
    _log = logging.getLogger('listener_hdl')

    def handle(self):
        """ Handling method.

        The handler is created by the server for the first event it recieves. We
        use this to open a listening session, which is kept alive until the death of
        the server. As a consequence, the handler never exits before.
        """
        self._log.info('client connected : %s' % str(self.client_address))
        self._log.info('started')
        broken_pipe = False

        sensor_mask = 0x03 if self.owner.use_2_sensors else 0x01

        # Run until our server is stopped or the connection is broken.
        # We use a select based mechanism to avoid dead locks in case the
        # socket is closed by the other side.
        while not (self.owner.terminated or broken_pipe):
            rd, _, _ = select.select([self.rfile], [], [], 0.5)
            if self.rfile not in rd:
                continue

            rxbuff = self.request.recv(4096)
            if not rxbuff:
                self._log.info('connection closed by client')
                broken_pipe = True
                break

            for data in rxbuff.strip().split('\n'):
                self._log.debug('received event : %s' % data)
                evt, parms = data.split(':')

                if evt == 'HIT':
                    # echo detection event
                    # Event parameters:
                    #   side :
                    #       'L' or 'R'
                    #   direction:
                    #       echo direction as a float giving its angle in degrees
                    #   detections:
                    #       bit pattern giving the sensor detections
                    side, angle, echo = parms.split('\t')
                    side = 0 if side == 'L' else 1
                    echo = int(echo) & sensor_mask
                    self.owner.post_echo_event(side, float(angle), echo)

                elif evt == 'SCAN':
                    # scanning status change event
                    # Event parameters:
                    #   side:
                    #       'L' or 'R'
                    #   status:
                    #       1 or 0 to indicate if the beacon is now scanning or not
                    side, status = parms.split('\t')
                    side = 0 if side == 'L' else 1
                    self.owner.set_scan_status(side, status == '1')

                elif evt == 'HDG':
                    # heading reporting event
                    # Event parameters:
                    #   side:
                    #       'L' or 'R'
                    #   angle:
                    #       current heading of the beacon, as a float number of degrees
                    side, angle = parms.split('\t')
                    side = 0 if side == 'L' else 1
                    self.owner.update_beacon_heading(side, float(angle))

        self._log.info('terminated')

_SIDES = ('L', 'R')

class Application(object):
    """ The application global object.
    """

    #pylint: disable=W0212
    def __init__(self, args):   #pylint: disable=W0621
        self._debug = args.debug

        log_level = logging.DEBUG if args.debug else logging.INFO
        self._log = logging.getLogger('app')
        self._log.setLevel(log_level)
        BeaconEventHandler._log.setLevel(log_level)

        self._wndgeom = args.geom
        self._window = pygame.display.set_mode(self._wndgeom.size)
        pygame.display.set_caption('Tracking beacons demo - by POBOT')

        wnd_icon = pygame.image.load('res/pobot-logo-right.png').convert_alpha()
        pygame.display.set_icon(wnd_icon)

        self._listen_port = args.listen_port

        self._ctrl_name = args.ctrl_name
        self._ctrl_host = args.ctrl_host
        self._ctrl_port = args.ctrl_port
        self._ctrl_socket = None
        self._ctrl_rfile = None

        self._logo = Logo(self._wndgeom.size)
        self._hud = Hud(pygame.Rect(10, 10, 300, 120))
        self._help = None

        lg = math.sqrt(self._wndgeom.w * self._wndgeom.w + self._wndgeom.h * self._wndgeom.h)
        self._beacons = (
            Beacon(
                (Beacon.SIZE / 2, self._wndgeom.h - Beacon.SIZE / 2),
                (-90, 0),
                'alpha',
                ray_length=lg,
                debug=args.debug
            ),
            Beacon(
                (self._wndgeom.w - Beacon.SIZE / 2, self._wndgeom.h - Beacon.SIZE / 2),
                (0, 90),
                'beta',
                ray_length=lg,
                debug=args.debug
            )
        )

        self._origin = self._beacons[0].location
        self._target = Target()
        self._clock = pygame.time.Clock()
        self._beacon_listener = None
        self._use_2_sensors = args.use_2_sensors

    def _ctl_command(self, cmde):
        """ Sends a command to the beacons controller."""
        self._log.info('cmd: %s' % cmde)
        self._ctrl_socket.sendall(cmde + '\n')
        _reply = self._ctrl_rfile.readline().strip()
        self._log.info('.... %s' % _reply)

    def _open_control_socket(self, host, port):
        """ Opens a socket with the beacons controller."""
        self._ctrl_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._ctrl_socket.connect((host, port))
        self._ctrl_rfile = self._ctrl_socket.makefile(mode='rt', bufsize=1024)

    def _close_control_socket(self):
        """ Closes the beacon controller socket."""
        if self._ctrl_socket:
            self._ctrl_socket.shutdown(socket.SHUT_RDWR)
            self._ctrl_socket.close()

    def run(self):
        """ Application main process."""
        if self._beacon_listener:
            return

        # set up a listener for beacon events
        self._beacon_listener = BeaconEventListener(
            listen_port=self._listen_port,
            use_2_sensors=self._use_2_sensors,
            debug=self._debug)
        self._beacon_listener.start()

        # set up a connection with the beacons controller
        try:
            self._open_control_socket(self._ctrl_host, self._ctrl_port)

        except socket.error:
            self._log.error('cannot connect to beacons controller')

        else:
            ghba = socket.gethostbyaddr(self._ctrl_host)
            # use the hostname returned by the controller itself instead of gethostbyaddr()
            # result one, since the later contains what is set in /etc/hosts
            self._hud.controller = (self._ctrl_name, ghba[1], ghba[2])

            # hook ourself to the controller as an event listener
            self._ctl_command('register')

            try:
                echo_starts = [None, None]
                scanning = [False, False]
                while True:
                    mouse_pos = pygame.mouse.get_pos()
                    mouse_cursor = DEFAULT_CURSOR

                    if not self.handle_events():
                        break

                    echo = self._beacon_listener.get_echo_event()
                    if echo:
                        self._log.debug('got echo event : %s' % str(echo))
                        echo_side, echo_heading, echo_start = echo
                    else:
                        echo_side, echo_heading, echo_start = None, None, None

                    for side, beacon in enumerate(self._beacons):
                        if echo_side == side:
                            # got an echo start or end for this beacon
                            if echo_start:
                                echo_starts[side] = echo_heading
                            elif echo_starts[side] != None:
                                beacon.target_heading = (echo_starts[side] + echo_heading) / 2.0
                                self._log.debug(
                                    'target heading: %f (%f, %f)' %
                                    (beacon.target_heading, echo_starts[side], echo_heading)
                                )

                        scanning[side] = self._beacon_listener.get_scan_status(side)
                        if scanning[side]:
                            # if beacon is scanning, update its sprite heading
                            beacon.heading = self._beacon_listener.beacon_headings[side]
                        else:
                            # otherwise make beacon sprite point upwards
                            beacon.heading = 0

                        # handle mouse interaction with beacons
                        if beacon.collidepoint(mouse_pos):
                            beacon.hilited = True
                            mouse_cursor = HAND_CURSOR
                        else:
                            beacon.hilited = False

                    # updates the mouse cursor to give a feedback of
                    # interactions
                    pygame.mouse.set_cursor(*mouse_cursor)

                    alpha, beta = [beacon.target_heading for beacon in self._beacons]
                    self._hud.alpha = -alpha if alpha != None else None
                    self._hud.beta = beta if beta != None else None

                    # if we have two echoes available, we can compute the
                    # target position and display it
                    if all(scanning) and alpha != None and beta != None:
                        alpha = math.radians(-alpha)
                        beta = math.radians(beta)
                        l = self._beacons[1]._location[0] - self._beacons[0]._location[0]
                        tga_tgb = math.tan(alpha) + math.tan(beta)
                        x = l * math.tan(alpha) / tga_tgb
                        y = l / tga_tgb
                        self._target.location = (
                            self._origin[0] + x,
                            self._origin[1] - y
                        )
                        self._target.visible = True

                        self._hud.target_location = (x, y)

                    else:
                        self._target.visible = False
                        self._hud.target_location = None


                    self._hud.fps = int(round(self._clock.get_fps()))

                    # redraw the display
                    self.display_update()

                    self._clock.tick(60)

            except KeyboardInterrupt:
                self._log.info('!! Keyboard interrupt in application !!')

            except Exception as e:
                self._log.exception(e)

            # time for the final housekeeping
            self._ctl_command('stop')
            self._ctl_command('unregister')
            self._ctl_command('disc')

            self._close_control_socket()

        finally:
            self._beacon_listener.terminate()
            self._beacon_listener = None

    def handle_events(self):
        """ User interaction events handling.

        In addition to the standard termination signals, we handle the following
        events:
            click on a beacon:
                starts or stops scanning, depending on its current status
                (if SHIFT pressed, both beacons are involved)
            key 'L':
                enables beacon lasers
            key 'l':
                disables beacon lasers
            key 'S':
                starts scanning for both beacons
            key 's':
                stops scanning for both beacons
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                self.handle_click(event.pos)

            elif event.type == pygame.KEYDOWN:
                self.handle_key(event.key)

        return True

    def handle_click(self, pos):
        """ Mouse click events handling.

        Parameters:
            pos:
                mouse position as a coordinates tuple

        """
        change_all = pygame.key.get_mods() & pygame.KMOD_SHIFT
        for side, beacon in enumerate(self._beacons):
            if beacon.collidepoint(pos):
                cmde = 'stop' if self._beacon_listener.get_scan_status(side) else 'scan'
                if change_all:
                    self._ctl_command(cmde)
                    break
                else:
                    self._ctl_command('%s %s' % (cmde, _SIDES[side]))

    def handle_key(self, key):
        """ Keyboard event handling.

        Parameters:
            key:
                the pressed key
        """
        k_shift = pygame.key.get_mods() & pygame.KMOD_SHIFT
        if key == pygame.K_l:
            state = 1 if k_shift else 0
            self._ctl_command('laser L:%d R:%d' % (state, state))

        elif key == pygame.K_s:
            cmde = 'scan' if k_shift else 'stop'
            self._ctl_command('%s L R' % cmde)

        elif key in (pygame.K_h, pygame.K_QUESTION):
            self.display_help()

        elif self._help and key == pygame.K_ESCAPE:
            self._help = None

    def display_update(self):
        """ Graphical display drawing."""
        #self._window.blit(self._bkgnd, (0, 0))
        self._window.fill((0, 0, 0))

        for beacon in self._beacons:
            beacon.draw(self._window)

        self._hud.draw(self._window)
        self._logo.draw(self._window)
        self._target.draw(self._window)

        if self._help:
            self._help.draw(self._window)

        pygame.display.flip()

    def display_help(self):
        if not self._help:
            help_w = 640
            help_h = 480
            x = (self._wndgeom.w - help_w) / 2
            y = (self._wndgeom.h - help_h) / 2
            self._help = Help(pygame.Rect(x, y, help_w, help_h))


Size = namedtuple('Size', 'w h')
Point = namedtuple('Point', 'x y')

class WindowGeometry(object):
    """ Helper class for managing a window geometry (position and size).

    This classes knows how to parse the format commonly used for specifying a window
    geometry in the X world (see constructor for details).
    """
    _attrs = ('w', 'h', 'x', 'y')
    w = h = x = y = 0

    def __init__(self, s):
        """ Constructor.

        Paramaters:
            s:
                specification string, in X format (<width>x<height>+<xpos>+<ypos>)
        """
        match = WindowGeometry.parse(s)
        if match:
            for n, v in enumerate(match.groups()):
                setattr(self, self._attrs[n], int(v))
        else:
            raise ValueError()

    def __getitem__(self, ndx):
        if type(ndx) is int:
            return getattr(self, self._attrs[ndx])
        else:
            return [getattr(self, attr) for attr in self._attrs[ndx]]

    @property
    def size(self):
        return (self.w, self.h)

    @property
    def origin(self):
        return (self.x, self.y)

    @staticmethod
    def parse(s):
        return re.match(r'^(\d+)x(\d+)(\+\d+)?(\+\d+)?$', s)


def geometry(s):
    """ WindowGeometry CLI argument type checker."""
    try:
        if WindowGeometry.parse(s):
            return s
        else:
            raise argparse.ArgumentTypeError('invalid gemetry settings (%s)' % s)
    except re.error:
        raise argparse.ArgumentTypeError('invalid gemetry settings (%s)' % s)

if __name__ == '__main__':
    setup_logging()
    _log = logging.getLogger('main')

    parser = argparse.ArgumentParser(
            description='Graphical client for localization beacons demo',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
            )
    parser.add_argument(
        '--geom',
        dest='geom',
        type=geometry,
        default='1024x768+150+100',
        help='Display window geometry'
    )
    parser.add_argument(
        '-l', '--listen-port',
        dest='listen_port',
        type=int,
        default=1235,
        help="listening port for beacon events"
    )
    parser.add_argument(
        dest='ctrl_host',
        nargs='?',
        help="beacons controller host. If not given, I will try to find one."
    )
    parser.add_argument(
        '-p', '--ctrl-port',
        dest='ctrl_port',
        type=int,
        default=1234,
        help="beacons controller port"
    )
    parser.add_argument(
        '--findsvc-port',
        dest='findsvc_port',
        default=5555,
        help='findsvc querying port'
    )
    parser.add_argument(
        '-2', '--use-2-sensors',
        dest='use_2_sensors',
        action='store_true',
        default=False,
        help='use both sensors of each beacon for target detection'
    )

    parser.add_argument(
        '-D', '--debug',
        dest='debug',
        action='store_true',
        default=False,
        help='activate debug log messages'
    )
    args = parser.parse_args()

    args.geom = WindowGeometry(args.geom)

    if not args.ctrl_host:
        reply = findsvc.find_services('demo.pobot:beacons', udp_port=args.findsvc_port)
        if not reply:
            print('[ERROR] could not find a beacons controller and none has been ' +
                  'provided with the command'
            )
            sys.exit(1)

        args.ctrl_name, addr, svc_list = reply
        args.ctrl_host = addr[0]
        _log.info('using beacons controller %s (%s)', args.ctrl_name, args.ctrl_host)

    os.environ['SDL_VIDEO_WINDOW_POS'] = '%d,%d' % (args.geom.x, args.geom.y)
    pygame.init()

    DEFAULT_CURSOR = pygame.mouse.get_cursor()

#pylint: disable=W0511
    _HAND_CURSOR = (
        "     XX         ",
        "    X..X        ",
        "    X..X        ",
        "    X..X        ",
        "    X..XXXXX    ",
        "    X..X..X.XX  ",
        " XX X..X..X.X.X ",
        "X..XX.........X ",
        "X...X.........X ",
        " X.....X.X.X..X ",
        "  X....X.X.X..X ",
        "  X....X.X.X.X  ",
        "   X...X.X.X.X  ",
        "    X.......X   ",
        "     X....X.X   ",
        "     XXXXX XX   ")
    _HCURS, _HMASK = pygame.cursors.compile(_HAND_CURSOR, ".", "X")
    HAND_CURSOR = ((16, 16), (5, 1), _HCURS, _HMASK)

    demo = Application(args)
    _log.info('application started')
    demo.run()

    _log.info('the end')
