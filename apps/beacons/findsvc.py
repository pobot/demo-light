#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Implementation of SLP like features.

The FindServiceDaemon listens for UDP queries on the port defined by the
--listen-port option. Queries are expected to be a comma separated list of one
or more service names. If the list is included in the list of services provided
by the system, its hostname is returned, followed by a newline char.

This is (very) loosely inspired from SLP intentions description and OpenSLP.
Be aware that it is in no mean an implementation of SLP specfications.
"""

import socket
import threading

__author__ = 'Eric PASCUAL for POBOT'
__version__ = '1.0.0'
__email__ = 'eric@pobot.org'

class FindServiceDaemon(threading.Thread):
    """ Responder class.

    Takes care of listening for requests and replying to them if there is a match
    between them and the services declared at instantiation time."""
    def __init__(self, services, listen_port=5555, log=None, *args, **kwargs):
        """ Constructor.

        Parameters:
            services:
                a mandatory and non empty list of service specs (either as a list
                of strings, or as a comma separated string). Each list item is
                composed of the name of the service and the associated port,
                concatenated by a '@'
            listen_port:
                the port listened for requests
                default: 5555
            log:
                an optional logger for execution messages
            args, kwargs:
                anything to be passed to the base class (threading.Thread)

        Raises:
            ValueError if the services list does not comply with constraints
        """
        if not services:
            raise ValueError('services parameter cannot be empty')
        super(FindServiceDaemon, self).__init__(*args, **kwargs)

        self._log = log

        if type(services) is str:
            services = services.strip().split(',')
        self._services = dict([svc.split('@') for svc in services])
        self._log.info('registered services : %s' % self._services)

        self._terminate = False
        self._listen_port = listen_port
        self._socket = None

    def run(self):
        """ Thread.run overriding."""
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._socket.bind(('', self._listen_port))
        self._socket.setblocking(1)
        self._socket.settimeout(0.1)
        try:
            if self._log:
                self._log.info('listening on port %d...', self._listen_port)
            while not self._terminate:
                try:
                    msg, from_addr = self._socket.recvfrom(8192)
                except socket.timeout:
                    continue
                else:
                    msg = msg.strip()
                    if self._log:
                        self._log.info('received "%s" from %s', msg, from_addr)

                    req_svcs = msg.strip().split(',')
                    if all((svc in self._services for svc in req_svcs)):
                        reply = \
                            [socket.gethostname()] + \
                            ['@'.join((n, self._services[n])) for n in req_svcs]
                        reply = ' '.join(reply)

                        self._socket.sendto(reply + '\n', from_addr)
                        if self._log:
                            self._log.info('replied "%s" to %s', reply, from_addr)

        finally:
            self._socket.close()
            if self._log:
                self._log.info('shutdown complete')

    def shutdown(self):
        """ Signals the thread loop that it must terminate.
        """
        if self._log:
            self._log.info('termination requested')
            self._terminate = True


def find_services(services, udp_port=5555):
    """ Sends a request for locating a network node implementing
    a set of services.

    In case of multiple matching nodes, only the first one who replies
    is taken in account.

    Parameters:
        services:
            the services, either as a list or as a comma separated string
        udp_port:
            the UDP port the daemon is supposed to listen
            (default: 5555)

    Returns:
        a tuple containing the host name and its IP address of the node
        matching the request.
    """
    if not services:
        raise ValueError('services parameter cannot be empty')

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    s.settimeout(1)

    if type(services) is list:
        services = ','.join(services)

    s.sendto(services, ('<broadcast>', udp_port))
    try:
        buf, addr = s.recvfrom(udp_port)
    except socket.timeout:
        return None
    else:
        s.close()
        hostname, svc_list = buf.strip().split(' ', 1)
        svc_list = svc_list.split()
        return (hostname, addr, svc_list)
