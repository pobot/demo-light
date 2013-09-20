#!/usr/bin/env python
# -*- coding: utf-8 -*-
#pylint: disable=C0302

""" Localization beacons demonstrator embedded controller.

An automatic service location server is implemented, so that the client
application does not need to know our IP address. It just has to broadcast
an UDP request for the service(s) it needs, and active servers implementing
them will reply with their address.

Important:
    This code is developed for the RasPi, and no cross-system portability
    consideration is taken in account, since this has no real meaning here.
    A limited fall-back mode is handled for development context, but is not
    intended for a normal use (no sensor interface supported).
"""

import threading
import select
import time
from argparse import ArgumentTypeError
import socket
import SocketServer
import errno
from collections import namedtuple
import signal

import pybot.dmxl.classes as dmxl
import pybot.cli as cli
import pybot.log as log
log.NAME_WIDTH = 10

import findsvc

import platform
if platform.machine().startswith('armv6'):
    # we are on the RasPi, so we can import HW support modules
    import pybot.abelectronics.iopi as iopi
    import pybot.i2c as i2c
else:
    iopi = None
    i2c = None

__author__ = 'Eric PASCUAL for POBOT'
__version__ = '1.0.0'
__email__ = 'eric@pobot.org'

CW = 0
CCW = 1

def angle_to_pos(arg):
    """ Degrees to AX12 position conversion.

    Important:
        Angles origin is taken at the median position (ie 511) of the AX12
    """
    if type(arg) is tuple:
        return tuple(angle_to_pos(a) for a in arg)
    else:
        return int(511 + 1024. * arg / 300)

def pos_to_angle(pos):
    """ AX12 position to degrees conversion."""
    return (pos - 511) / 1024. * 300.

IO_Specs = namedtuple('IO_Specs', 'port ios')

class Beacon(object):
    """ Beacon 'driver' class."""

    def __init__(self,
                 ident,
                 span,
                 dmxlintf,
                 dmxlid,
                 sensors_input,
                 sensors_enable=None,
                 laser_enable=None,
                 controller=None
                 ):
        """ Constructor.

        Parameters:
            ident:
                (str) symbolic identifier of the beacon
            span:
                (tuple) scanning angle span
            dmxlintf:
                instance of the DMXL bus interface used to
                dialog with the beacon servo
            dmxlid:
                (int) id of the beacon AX12 servo
            sensors_input:
                (IO_Specs) IOPi port and IO ids of inputs from sensors
            sensors_enable:
                (IO_Specs) IOPi port and IO ids of outputs controlling the
                activation of the sensors
            laser_enable:
                (IO_Specs) IOPi port and IO id of output controlling the
                activation of the laser
            controller:
                instance of the owning beacons controller managing
                the beacon
        """
        self._ident = ident

        self._dmxlintf = dmxlintf
        self._dmxlid = dmxlid

        if type(span) is tuple:
            self._scan_limits = angle_to_pos(span)
        else:
            raise TypeError('span must be a tuple')

        self._sensors_input = sensors_input
        # compute and cache masks for faster processing while active
        ios = sensors_input.ios
        self._sensors_ios_masks = tuple(1 << (io - 1) for io in ios)
        self._sensors_ios_gmask = reduce(lambda x, y : x | y, self._sensors_ios_masks)
        self._sensors_ios_shift = min(ios) - 1
        self._last_echos = 0

        self._sensors_enable = sensors_enable
        if self._sensors_enable:
            ios = sensors_enable.ios
            self._sensors_enable_masks = tuple(1 << (io - 1) for io in ios)

        self._laser_enable = laser_enable
        if self._laser_enable:
            io = laser_enable.ios
            self._laser_enable_mask = 1 << (io - 1)

        self._scan_thread = None
        self._active = False
        self._scan_speed = 180 # deg/s

        self._init_servo(dmxlid)
        self._mode_method = self._mode_wipe

        self._controller = controller
        self._sim_echo_pos = None

        self._position_errmax = 3

    @property
    def ident(self):
        return self._ident

    @property
    def active(self):
        return self._active

    def _init_servo(self, dmxlid):
        intf = self._dmxlintf
        for reg, value in [
            (dmxl.Register.ReturnDelay, 0),
            (dmxl.Register.MaxTorque, 1023),
            (dmxl.Register.TorqueLimit, 1023),
            (dmxl.Register.CWComplianceMargin, 1),
            (dmxl.Register.CWComplianceSlope, 32),
            (dmxl.Register.CCWComplianceMargin, 1),
            (dmxl.Register.CCWComplianceSlope, 32),
            (dmxl.Register.Punch, 32),
            (dmxl.Register.CWAngleLimit, self._scan_limits[CW]),
            (dmxl.Register.CCWAngleLimit, self._scan_limits[CCW])
        ]:
            intf.write_register(dmxlid, reg, value)

    def enable_sensors(self, state, selectors=None):
        """ Enables or disables beacon sensor(s).

        Do nothing if no sensor enabling interface has been set.

        Parameters:
            state:
                True for enabling sensors, False for disabling
            selectors:
                the list of indexes (0 based) of involved sensors
                If not specified (or None), process all sensors.
        """
        if not self._sensors_enable:
            return

        all_ = xrange(len(self._sensors_input.ios))
        if selectors is None:
            selectors = all_
        elif len(selectors) == 0:
            # do nothing if the list is empty
            return
        else:
            # check selectors
            if not all(sel in all_ for sel in selectors):
                raise ValueError('invalid sensor selector(s)')

        port, _ios = self._sensors_enable
        self._change_port_bits(
            port,
            reduce(lambda x,y : x | y, (
                self._sensors_enable_masks[ndx] for ndx in selectors)
            ),
            state
        )

    def enable_laser(self, state):
        """ Enables or disables the beacon direction display laser.

        Parameters:
            state:
                True for laser enabling, False otherwise
        """
        if not self._laser_enable:
            return

        port, _io = self._laser_enable
        self._change_port_bits(port, self._laser_enable_mask, state)

    @staticmethod
    def _change_port_bits(port, mask, state):
        io_states = port.get()
        if state:
            io_states = (io_states | mask) & 0xff
        else:
            io_states = (io_states & ~mask) & 0xff
        port.set(io_states)


    def set_scan_angles(self, angles):
        """ Sets the bounds of the beacon span.

        Parameters:
            angles:
                a tuple containing the min and max angles,
                given in degrees
        """
        if type(angles) is not tuple:
            raise TypeError('angles must be a tuple')

        self._scan_limits = angle_to_pos(angles)
        self._dmxlintf.write_register(
            self._dmxlid,
            dmxl.Register.CWAngleLimit, min(self._scan_limits)
        )
        self._dmxlintf.write_register(
            self._dmxlid,
            dmxl.Register.CCWAngleLimit, max(self._scan_limits)
        )

    def set_scan_speed(self, deg_s):
        """ Sets the beacon scan speed.

        Parameters:
            deg_s:
                the speed, in degrees per second (must be in [1, 180])
        """
        if 1 <= deg_s <= 180:
            self._scan_speed = deg_s
        else:
            raise ValueError('scan speed must between 1 and 180 deg/s')

    def set_mode(self, mode):
        """ Sets the beacon mode.

        Supported modes are given by methods which name starts with
        '_mode_'.

        Parameters:
            mode:
                a mode name
        """
        try:
            self._mode_method = getattr(self, '_mode_' + mode)
        except AttributeError:
            raise ValueError('invalid beacon mode : %s' % mode)

    def scan(self, scan_dir=CW):
        """ Starts to scan.

        If already scanning, do nothing.

        Parameters:
            scan_dir:
                scan start direction
                (default: clockwise)
        """
        if self._scan_thread:
            return

        self.enable_sensors(True)
        #self.enable_laser(True)

        self._scan_thread = threading.Thread(
            target=self,
            args=(self._scan_limits, scan_dir)
        )
        self._scan_thread.start()

    def __call__(self, *args, **kwargs):
        """ Makes us a callable, so that we can be passed to the Thread
        constructor.

        Here we call the method selected by a previous set_mode() call.
        """
        self._mode_method(*args, **kwargs)

    def stop(self):
        """ Stops the scan.

        Do nothing if not currently scanning.
        """
        if self._scan_thread:
            self._active = False
            self._scan_thread.join(1)
            self._scan_thread = None

            self.enable_sensors(False)
            self.enable_laser(False)

    def point_to(self, deg, sync=True):
        """ Points the beacon in a given direction.

        Parameters:
            deg:
                the direction (in degrees)
            sync:
                if True, the method waits for the position to be
                reached. If False, it exists at once.
                (default: True)
        """
        intf = self._dmxlintf
        id_ = self._dmxlid
        target_pos = angle_to_pos(deg)
        intf.write_register(
            id_,
            dmxl.Register.GoalPosition,
            target_pos
        )
        if sync:
            # wait until the target is reached
            pos = 9999
            while abs(pos - target_pos) > 2:
                time.sleep(0.01)
                pos = intf.read_register(id_, dmxl.Register.CurrentPosition)

    def coast(self):
        """ De-energize the beacon (ie don't try to hold the position
        and sets its driver in free-wheeling mode)
        """
        self._dmxlintf.write_register(
            self._dmxlid,
            dmxl.Register.TorqueEnable,
            0
        )

    def simulate_detection_for_angle(self, angle):
        """ Debug method simulating a detection for a given direction."""
        if angle:
            self._sim_echo_pos = angle_to_pos(angle)
        else:
            self._sim_echo_pos = None

    def _check_detections(self, cur_pos):
        """ Computes the right aligned bit pattern reflecting if detections reported
        by I/R sensors.

        Bits will be set for a detection, whatever is the logic (positive or
        negative) used by the sensor.
        """
        if self._sensors_input:
            # we are on the real HW => get the inputs
            # remember that sensors output uses negative logic
            port = self._sensors_input.port
            ios = ~port.get() & self._sensors_ios_gmask
            echos = ios >> self._sensors_ios_shift

        elif self._sim_echo_pos != None and abs(cur_pos - self._sim_echo_pos) < 3:
            # simulate an echo on first sensor if in angular range
            echos = 1
        else:
            echos = 0

        if echos != self._last_echos and self._controller:
            self._controller.notify_hit(self._ident, pos_to_angle(cur_pos), echos)
            self._last_echos = echos

    HEADING_NOTIFY_PERIOD = 0.1

    def _mode_wipe(self, scan_limits, scan_dir):
        """ 'Wipe' mode handler.

        In wipe mode, the beacon travels over its whole span, reverting its
        move direction only when reaching the bounds.

        Its notifies its position periodically (period defined by the
        HEADING_NOTIFY_PERIOD constant).
        """
        self._active = True
        self._dmxlintf.write_register(
            self._dmxlid,
            dmxl.Register.MovingSpeed,
            min(int(round(self._scan_speed / 684. * 1023)), 0x3FF)
        )
        cur_limit = scan_limits[scan_dir]
        self._dmxlintf.write_register(
            self._dmxlid,
            dmxl.Register.GoalPosition,
            cur_limit
        )
        hdg_sent_at = 0
        hdg_refresh_period = self.HEADING_NOTIFY_PERIOD
        while self._active:
            cur_pos = self._dmxlintf.read_register(
                self._dmxlid,
                dmxl.Register.CurrentPosition
            )

            self._check_detections(cur_pos)

            now = time.time()
            if now - hdg_sent_at > hdg_refresh_period:
                self._controller.send_beacon_heading(self._ident, pos_to_angle(cur_pos))
                hdg_sent_at = now

            if abs(cur_pos - cur_limit) < 3:
                scan_dir ^= 1
                cur_limit = scan_limits[scan_dir]
                self._dmxlintf.write_register(
                    self._dmxlid,
                    dmxl.Register.GoalPosition,
                    cur_limit
                )
            time.sleep(0.001)

        self._dmxlintf.write_register(
            self._dmxlid,
            dmxl.Register.TorqueEnable,
            0
        )

class Side(object):
    LEFT, RIGHT = xrange(2)
    ALL = (LEFT, RIGHT)

    _to_str = ('LEFT', 'RIGHT')

    _to_side = {
        'L' : LEFT,
        'LEFT' : LEFT,
        'R' : RIGHT,
        'RIGHT' : RIGHT
    }

    @classmethod
    def to_str(cls, side):
        return cls._to_str[side]

    @classmethod
    def to_side(cls, s):
        try:
            return cls._to_side[s.upper()]
        except KeyError:
            raise ValueError()

    @classmethod
    def is_valid_str(cls, s):
        return s.upper() in cls._to_side


class BeaconsController(object):
    """ A beacons controller.

    In charge of controlling two localization beacons via the DMXL bus, and
    managing their sensors via a AB Electronics IOPi expansion board.

    It is remotely controlled by en embedded TCP socket server, handling
    commands sent by a connected client.
    """
    def __init__(self, run_args):
        self._log = log.getLogger('controller')

        dmxl_intf = dmxl.USB2AX(run_args.port, debug=run_args.debug)
        # check passed servos id
        for _id in (run_args.left_id, run_args.right_id):
            if not dmxl_intf.ping(dmxlid=_id):
                raise ValueError('no servo found with id=%d' % _id)

        if i2c and iopi:
            i2cbus = i2c.SMBusI2CBus()
            io_board = iopi.Board(i2cbus)
            io_port_in = iopi.Port(io_board, iopi.EXPANDER_1, iopi.PORT_A)
            io_port_out = iopi.Port(io_board, iopi.EXPANDER_1, iopi.PORT_B)
            io_port_out.set_mode(iopi.DIR_OUTPUT)
            self._log.info('using real GPIOs')
        else:
            i2cbus = io_board = io_port_in = io_port_out = None
            self._log.warn('not running on a RasPi. GPIOs will be simulated.')

        self._beacons = [
            Beacon(
                ident='L',
                span=(-80, 0),
                dmxlid=run_args.left_id,
                dmxlintf=dmxl_intf,
                sensors_input=IO_Specs(io_port_in, (1, 2)),
                sensors_enable=IO_Specs(io_port_out, (8, 7)),
                laser_enable=IO_Specs(io_port_out, 4),
                controller=self
            ),
            Beacon(
                ident='R',
                span=(0, 80),
                dmxlid=run_args.right_id,
                dmxlintf=dmxl_intf,
                sensors_input=IO_Specs(io_port_in, (3, 4)),
                sensors_enable=IO_Specs(io_port_out, (6, 5)),
                laser_enable=IO_Specs(io_port_out, 3),
                controller=self
            )
        ]
        # be sure sensors and laser are off until we start scanning
        for beacon in self._beacons:
            beacon.enable_sensors(False)
            beacon.enable_laser(False)

        self._control_server = None
        self._listen_port = run_args.listen_port
        self._evtlistener_socket = None
        self._notify_lock = threading.Lock()

    def run(self):
        self._log.info('starting')

        class ControlServer(SocketServer.TCPServer):
            """ Inner TCP socket server for listening to remote
            control commands.

            Implemented as a modified version of the standard TCPServer
            serve_forever() method, to be able to shutdown itself in response
            to the corresponding remote command.
            """
            _log = None
            _stop_request = None
            owner = None

            def server_activate(self):
                """ Starts the control server."""
                self._log = log.getLogger('server')
                self._stop_request = threading.Event()
                SocketServer.TCPServer.server_activate(self)

            def serve_forever(self, poll_interval=0.5):
                """ Modified implementation to be able to shutdown oneself
                in response to a remote command."""
                self._log.info('requests service loop started')
                srvfd = self.fileno()
                try:
                    while not self._stop_request.isSet():
                        try:
                            ready = select.select([srvfd], [], [], poll_interval)
                        except select.error as e:
                            if e[0] == 4:   # interrupted system call
                                self._log.info('!! Interrupted system call !!')
                                self.shutdown()
                            else:
                                raise
                        else:
                            if srvfd in ready[0]:
                                self.handle_request()
                except KeyboardInterrupt:
                    self._log.info('!! Keyboard interrupt !!')
                    self.shutdown()

                self._log.info('requests service loop terminated')

            def shutdown(self):
                """ Request for shutdown."""
                self._stop_request.set()

        ControlServer.allow_reuse_address = True
        self._control_server = ControlServer(
            ('', self._listen_port),
            ControlServerHandler,
            bind_and_activate=False
        )
        self._control_server.owner = self

        self._log.info('start listening for commands on port %s...', self._listen_port)
        self._control_server.server_bind()
        self._control_server.server_activate()
        self._control_server.serve_forever()

        self.deactivate_beacons()
        if self._evtlistener_socket:
            self.evtlistener_unregister()

        self._control_server = None
        self._log.info('shutdown complete')

    def shutdown(self):
        """ Request for shutdown the control server."""
        if self._control_server:
            self._control_server.shutdown()

    def activate_beacons(self, sides=None):
        """ Starts beacon scanning.

        Parameters:
            sides:
                list of the sides of beacons to be started
                (default: all the beacons)
        """
        start_dirs = {
            Side.LEFT : CW,
            Side.RIGHT : CCW
        }
        if not sides:
            sides = Side.ALL
        for side in sides:
            self._log.info('start scan for beacon %s', Side.to_str(side))
            beacon = self._beacons[side]
            beacon.scan(scan_dir=start_dirs[side])
            self.notify_scan(beacon.ident, True)

    def deactivate_beacons(self, sides=None):
        """ Stops beacon scanning.

        Parameters:
            sides:
                list of the sides of beacons to be stopped
                (default: all the beacons)
        """
        if not sides:
            sides = Side.ALL
        for side in sides:
            self._log.info('stop scan for beacon %s', Side.to_str(side))
            beacon = self._beacons[side]
            beacon.stop()
            self._log.info('reset position for beacon %s', Side.to_str(side))
            beacon.point_to(0, sync=True)
            beacon.coast()

            self.notify_scan(beacon.ident, False)

    def set_beacons_mode(self, mode):
        """ Sets the beacons scanning mode.

        Parameters:
            mode:
                beacon scanning mode (see Beacon.set_mode() for details)
        """
        for beacon in self._beacons:
            beacon.set_mode(mode)

    def evtlistener_register(self, addr):
        """ Register a listener for events we can emit.

        Parameters:
            addr:
                the IP address of the listener
                (the port is fixed to 1235)
        """
        self._log.info('%s registered as event listener' % addr)
        if not self._evtlistener_socket:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.connect((addr, 1235))
            except socket.error as e:
                raise e
            else:
                self._evtlistener_socket = sock
                self._log.info('done')

                for beacon in self._beacons:
                    self.notify_scan(beacon.ident, beacon.active)

        else:
            raise RuntimeError('already registered')

    def evtlistener_unregister(self):
        """ Unregisters an event listener."""
        self._log.info('unregistering event listener')
        if self._evtlistener_socket:
            self._evtlistener_socket.shutdown(socket.SHUT_RDWR)
            self._evtlistener_socket.close()
            self._evtlistener_socket = None
            self._log.info('done')
        else:
            raise RuntimeError('not registered')

    def notify_hit(self, beacon_ident, angle, sensor_states):
        """ Sends an event for notifying an echo on the target.

        This method is intended to be used by the controlled beacons.

        Parameters:
            beacon_ident:
                identifier of the sending beacon
            angle:
                echo direction
            sensor_states:
                bit masks containing the sensors state
        """
        self._post_event(
            'HIT:%s\t%0.1f\t%d\n' %
            (beacon_ident, angle, sensor_states)
        )

    def notify_scan(self, beacon_ident, status):
        """ Sends an event giving the current scanning status of the beacon.

        Parameters:
            beacon_ident:
                identifier of the sending beacon
            status:
                scanning status (0/1)
        """
        self._post_event(
            'SCAN:%s\t%d\n' %
            (beacon_ident, 1 if status else 0)
        )

    def send_beacon_heading(self, beacon_ident, heading):
        """ Sends an event giving the current heading of the beacon.

        Parameters:
            beacon_ident:
                identifier of the sending beacon
            heading:
                beacon heading (degrees)
        """
        self._post_event(
            'HDG:%s\t%0.1f\n' %
            (beacon_ident, heading)
        )

    def _post_event(self, event):
        if self._evtlistener_socket:
            with self._notify_lock:
                try:
                    self._evtlistener_socket.sendall(event)
                except IOError as e:
                    if e.errno == errno.EPIPE:
                        self._log.error('connection closed by peer')
                        self._evtlistener_socket.close()
                        self._evtlistener_socket = None

    def simulate_detections(self, detections):
        """ Simulate echo detections.

        Parameters:
            detections:
                a list of tuple containing the beacon identification (side) and
                the heading (degrees) of the simulated detection.
        """
        for side, angle in enumerate(detections):
            self._beacons[side].simulate_detection_for_angle(angle)
            self._log.info('simulate echo at pos=%s for beacon=%s',
                           self._beacons[side]._sim_echo_pos,    #pylint: disable=W0212
                           Side.to_str(side)
                           )

    def point_to(self, side, angle):
        """ Points a beacon in a given direction.

        Parameters:
            side:
                beacon side (Side.LEFT, Side.RIGHT)
            angle:
                direction in degrees
        """
        self._beacons[side].point_to(deg=angle, sync=True)


    def enable_sensors(self, side, state, selectors):
        """ Enables or disables beacon sensors.

        Parameters:
            side:
                beacon side (Side.LEFT, Side.RIGHT)
            state:
                True for enabling, False for disabling
            selectors:
                index list of targeted beacon sensors
                If set to None, processes all sensors
        """
        self._beacons[side].enable_sensors(state, selectors)

    def enable_laser(self, side, state):
        """ Enables or disables beacon laser.

        Parameters:
            side:
                beacon side (Side.LEFT, Side.RIGHT)
            state:
                True for enabling, False for disabling
        """
        self._beacons[side].enable_laser(state)


#pylint: disable=W0613
class ControlServerHandler(SocketServer.StreamRequestHandler):
    """ Request handler for the controller TCP socket server.

    A request is a string composed of a command verb, optionally followed by
    parameters. Command verb and parameters are separated by a single space.
    Parameters syntax depends on the command.

    The <side> parameter is one of 'L', 'R', 'LEFT', 'RIGHT' (case insensitive).

    The <angle> parameter is a float number of degrees, which sign uses the
    usual trigonometric convention, and the origin begin taken at the beacon idle
    position.

    The supported commands are indicated by the methods which name is prefixed
    by '_cmd_'.

    Note:
    The handler is implemented as a forever one, ie it is started on reception
    of the first command, and is kept running until the shutdown command is
    received. The reason is that I didn't find how to do the same with single
    shot handlers.
    """
    _log = log.getLogger('handler')
    _ctl_connected = False
    _shutdown_requested = False

    def _cmd_shutdown(self, parms, ctrl):
        """ Shutdown the controller.

        Syntax :
            shutdown
        """
        self._log.info('shutdown requested')
        self._ctl_connected = False
        self._shutdown_requested = True

    def _cmd_mode(self, parms, ctrl):
        """ Set beacon mode

        Syntax :
            mode <mode_name>
        with:
            <mode_name> :
                see Beacon.set_mode()
        """
        try:
            ctrl.set_beacons_mode(parms[0].lower())
        except IndexError:
            raise ValueError('missing mode value')

    def _cmd_scan(self, parms, ctrl):
        """ Start beacon(s) scanning

        Syntax :
            scan <side> [...]
        """
        try:
            sides = [Side.to_side(s) for s in parms if s]
        except ValueError:
            raise ValueError('invalid command parms : %s' % parms)
        else:
            ctrl.activate_beacons(sides)

    def _cmd_stop(self, parms, ctrl):
        """ Stop beacon(s) scanning

        Syntax :
            stop <side> [...]
        """
        try:
            sides = [Side.to_side(s) for s in parms if s]
        except ValueError:
            raise ValueError('invalid command parms : %s' % parms)
        else:
            ctrl.deactivate_beacons(sides)

    def _cmd_register(self, parms, ctrl):
        """ Register an event listener

        Syntax :
            register
        """
        client_addr = self.client_address[0]
        ctrl.evtlistener_register(client_addr)

    def _cmd_unregister(self, parms, ctrl):
        """ Unregister the event listener

        Syntax :
            unregister
        """
        ctrl.evtlistener_unregister()

    def _cmd_disc(self, parms, ctrl):
        """ Close the control socket

        Syntax :
            disc
        """
        self._ctl_connected = False

    def _cmd_simul(self, parms, ctrl):
        """ Simulate target echos

        Syntax :
            simul <side>:<angle> [...]
        """
        sim_detections = [None, None]
        for stmt in parms:
            try:
                side, angle = stmt.split(':')
                side = Side.to_side(side)
                angle = float(angle)
            except:
                raise ValueError('invalid command parms : %s' % parms)
            else:
                sim_detections[side] = angle

        ctrl.simulate_detections(sim_detections)

    def _cmd_hdg(self, parms, ctrl):
        """ Make beacon(s) point to a given direction

        Syntax :
            simul <side>:<angle> [...]
        """
        for stmt in parms:
            try:
                tokens = stmt.split(':')
                side = Side.to_side(tokens[0])
                angle = int(tokens[1])
            except:
                raise ValueError('invalid command parms : %s' % parms)
            else:
                ctrl.point_to(side, angle)

    def _cmd_sensor(self, parms, ctrl):
        """ Enable/Disable beacon(s) sensor(s)

        Syntax :
            sensor <side>:<selectors>:<state> [...]
        with:
            <selectors>:
                a comma separated list of 0 based indexes specifying which
                beacons sensors are involved. A '*' is a shorthand for 'all'.
        """
        for stmt in parms:
            try:
                side, sel, state = stmt.split(':')
                side = Side.to_side(side)
                if sel is '*':
                    sel = None
                else:
                    sel = [int(ndx) for ndx in sel.split(',')]
                state = state is '1'
            except:
                raise ValueError('invalid command parms : %s' % parms)
            else:
                ctrl.enable_sensors(side, state, sel)

    def _cmd_laser(self, parms, ctrl):
        """ Enable/Disable beacon(s) laser

        Syntax :
            laser <side>:<state> [...]
        """
        for stmt in parms:
            try:
                side, state = stmt.split(':')
                side = Side.to_side(side)
                state = state is '1'
            except:
                raise ValueError('invalid command parms : %s' % parms)
            else:
                ctrl.enable_laser(side, state)

    def _cmd_help(self, parms, ctrl):
        if parms:
            cmde = parms[0]
            try:
                reply = getattr(self, '_cmd_' + cmde).__doc__
            except AttributeError:
                raise ValueError('command does not exist : %s' % cmde)
        else:
            reply = [s[5:] for s in dir(self) if s.startswith('_cmd_')]
        return reply

    def handle(self):
        self._ctl_connected = True
        self._log.info('control session opened for client %s' % self.client_address[0])
        try:
            while self._ctl_connected:
                data = self.rfile.readline().strip()
                if not data:
                    continue
                self._log.info('[Rx] %s -> %s' % (self.client_address[0], data))

                tokens = data.split()
                cmde = tokens[0].lower()
                parms = tokens[1:]
                beacons_ctrl = self.server.owner

                try:
                    cmd_hndlr = getattr(self, '_cmd_' + cmde)

                except AttributeError:
                    reply = 'ERR command not found : %s' % cmde
                    self._log.error('[Tx] %s' % reply)

                else:
                    try:
                        res = cmd_hndlr(parms, beacons_ctrl)

                    except (RuntimeError, ValueError, socket.error) as e:
                        reply = 'ERR %s' % e
                        self._log.error('[Tx] %s' % reply)

                    except Exception as e:  #pylint: disable=W0703
                        self._log.exception(e)
                        reply = 'ERR %s:%s' % (e.__class__.__name__, e)
                        self._log.error('[Tx] %s' % reply)

                    else:
                        reply = 'OK'
                        if res:
                            reply += ' '+ str(res)
                        self._log.info('[Tx] %s' % reply)

                self.request.sendall(reply + '\n')

            self._log.info('control session closed')

        except KeyboardInterrupt:
            self._log.info('!! Keyboard interrupt !!')
            self._shutdown_requested = True

        if self._shutdown_requested:
            self.server.shutdown()


def _servo_id(s):
    """ DMXL servo id CLI argument type checker."""
    try:
        dmxlid = int(s)
        if 1 <= dmxlid <= 250:
            return dmxlid
        else:
            raise ValueError()
    except ValueError:
        raise ArgumentTypeError('must be a positive integer')

def sigterm_handler(signum, frame):
    log.getLogger('sighandler').info('!! SIGTERM caught !!')
    ControlServerHandler._shutdown_requested = True #pylint: disable=W0212

if __name__ == '__main__':
    parser = cli.get_argument_parser(description='Dual beacons controller')

    parser.add_argument('-l', '--left_id',
                        help='id of left (from rear) beacon servo',
                        default=1,
                        type=_servo_id,
                        dest='left_id'
                        )
    parser.add_argument('-r', '--right_id',
                        help='id of right (from rear) beacon servo',
                        default=2,
                        type=_servo_id,
                        dest='right_id'
                        )
    parser.add_argument('-p', '--port',
                        help='port of the DMXL bus interface',
                        default='/dev/ttyACM0',
                        dest='port'
                        )
    parser.add_argument('-L', '--listen-port',
                        help='TCP listening port for commands',
                        default=1234,
                        dest='listen_port'
                        )

    cli_args = parser.parse_args()

    try:
        _ctrl = BeaconsController(cli_args)
    except Exception as e: #pylint: disable=W0703
        cli.die(e)
    else:
        # Starts the "find service" daemon to be able to reply to clients
        # looking for a beacon controllers service on the network
        _findsvc_daemon = findsvc.FindServiceDaemon(
            services=['demo.pobot:beacons@%d' % cli_args.listen_port],
            log=log.getLogger('findsvc')
        )
        _findsvc_daemon.start()
        try:
            # starts the beacons controller
            signal.signal(signal.SIGTERM, sigterm_handler)
            _ctrl.run()

        finally:
            _findsvc_daemon.shutdown()

