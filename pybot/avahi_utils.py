#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A couple of helper functions and classes for using Avahi tools
(instead of going trhough D-Bus path, which is somewhat less simple).

Note: this will run on Linux only, Sorry guys :/
"""

import sys
if not sys.platform.startswith('linux'):
    raise Exception('this code runs on Linux only')

import subprocess

def whereis(bin_name):
    """ Internal helper for locating the path of a binary.

    Just a wrapper of the system command "whereis".

    Parameters:
        bin_name:
            the name of the binary

    Returns:
        the first reply returned by whereis if any, None otherwise.
    """
    output = subprocess.check_output(['whereis', bin_name])\
                .splitlines()[0]\
                .split(':')[1]\
                .strip()
    if output:
        # returns the first place we found
        return output.split()[0]
    else:
        return None

def find_service(svc_name, svc_type):
    """ Finds a given Avahi service, using the avahi-browse command.

    Parameters:
        svc_name:
            the name of the service, without the leading '_'

        scv_type:
            the type of the service, without the leading '_' and the
            trailing "._tcp' suffix

    Returns:
        a list of matching locations, each entry being a tuple
        composed of:
            - the name of the host on which the service is published
            - its IP  address
            - the port on which the service is accessible
        In case no match is found, an empty list is returned

    Raises:
        AvahiNotFound if the avahi-browse command is not available
    """
    _me = find_service
    try:
        cmdpath = _me.avahi_browse
    except AttributeError:
        cmdpath = _me.avahi_browse = whereis('avahi-browse')
        if not cmdpath:
            raise AvahiNotFound('cannot find avahi-browse')

    locations = []
    output = subprocess.check_output([cmdpath, '_%s._tcp' % svc_type, '-trp']).splitlines()
    for line in [l for l in output if l.startswith('=;')]:
        _netif, _ipver, _name, _type, _domain, hostname, hostaddr, port, _desc = \
                line[2:].split(';')
        if not svc_name or _name == svc_name:
            locations.append((hostname, hostaddr, int(port)))

    return locations

class AvahiService(object):
    """ A simple class wrapping service publishing and unpublishing. """
    _cmdpath = whereis('avahi-publish-service')

    def __init__(self, svc_name, svc_type, svc_port):
        """ Constructor.

        Parameters:
            svc_name:
                the name of the service

            svc_type:
                the type of the service. The leading '_' and trailing
                '._tcp' suffix can be omitted for readability's sake.
                They will be added automatically if needed.

        """
        if not self._cmdpath:
            raise AvahiNotFound('avahi-publish-service not available')
        self._process = None

        self._svc_name = svc_name
        if not (svc_type.startswith('_') and svc_type.endswith('_tcp')):
            self._svc_type = '_%s._tcp' % svc_type
        else:
            self._svc_type = svc_type
        self._svc_port = svc_port

    def publish(self):
        """ Publishes the service.

        Starts the avahi-publish-service in a separate process. Do nothing
        if the service is already published.
        """
        if self._process:
            return

        self._process = subprocess.Popen([
            self._cmdpath,
            self._svc_name, self._svc_type, str(self._svc_port)
        ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if not self._process:
            raise AvahiError('unable to publish service')

    def unpublish(self):
        """ Unpublishes the service, if previously published.

        Do nothing if the service is not yet publisehd.
        """
        if self._process:
            self._process.terminate()
            self._process = None

class AvahiError(Exception):
    """ Root of module specific errors. """
    pass

class AvahiNotFound(AvahiError):
    """ Dedicated error for command not found situations. """
    pass

