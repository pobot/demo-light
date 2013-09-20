#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""A find-service daemon based on findsvc.FindServiceResponder class.

The list of provided services is defined either :
    - by the CLI option --services
    - or are read from the /etc/svcipd.conf file if exists.

The command line take precedence over the configuration file.
"""

import os
import argparse
import logging
import time

import findsvc

__author__ = 'Eric PASCUAL for POBOT'
__version__ = '1.0.0'
__email__ = 'eric@pobot.org'

class ArgParseHelpFormatter(
    argparse.ArgumentDefaultsHelpFormatter,
    argparse.RawDescriptionHelpFormatter
):
    """ Combination of two help formatters for having default values automatically
    displayed in help, while keeping texts format unchanged (line breaks,...)
    """
    pass

if __name__ == '__main__':
    logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s.%(msecs).3d [%(levelname).1s] %(name)-8.8s > %(message)s',
            datefmt='%H:%M:%S'
            )

    CONFIG_FILE = '/etc/findsvcd.conf'

    _log = logging.getLogger('main')

    svc_list = []
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'rt') as f:
            for line in [line.strip() for line in f.readlines()
                         if not line.strip().startswith('#')
                         ]:
                svc_list.append(line)

    parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=ArgParseHelpFormatter
            )

    parser.add_argument(
        dest='services',
        nargs='*',
        help='the services provided by this system',
        default=' '.join(svc_list)
    )

    parser.add_argument(
        '-l', '--listen-port',
        dest='listen_port',
        type=int,
        default=5555,
        help="listening port"
    )

    parser.add_argument(
        '-D', '--debug',
        dest='debug',
        action='store_true',
        default=False,
        help='activate debug log messages'
    )
    _args = parser.parse_args()

    if _args.services:
        if type(_args.services) is list:
            _services = _args.services
        else:
            _services = _args.services.split(',')
        _log.info('The following service(s) are declared to be provided by this node:')
        for svc in _services:
            _log.info('- %s', svc)
    else:
        parser.error(
            'the list of service must be provided by either the command line ' +
            'or the config file (%s)'
            % CONFIG_FILE
        )

    resp = findsvc.FindServiceResponder(
        services=_services,
        listen_port=_args.listen_port,
        log=_log
    )
    try:
        resp.start()
        _log.info('waiting for server thread to end...')
        while resp.is_alive():
            time.sleep(0.1)
    except KeyboardInterrupt:
        print
        _log.info('!! Keyboard interrupt !!')
        resp.shutdown()

    _log.info('finished')
