#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Color sensing demonstrator web application.
"""

__author__ = 'Eric Pascual (for POBOT)'

import logging
import sys

from webapp import DemoColorApp
from controller import DemonstratorController

_CONFIG_FILE_NAME = "demo-color.cfg"

if __name__ == '__main__':
    import argparse

    logging.basicConfig(
        format="%(asctime)s.%(msecs).3d [%(levelname).1s] %(name)s > %(message)s",
        datefmt='%H:%M:%S'
    )

    log = logging.getLogger()
    log.setLevel(logging.INFO)

    try:
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.ArgumentDefaultsHelpFormatter
        )
        parser.add_argument(
            '-p', '--port',
            help='HTTP server listening port',
            dest='listen_port',
            default=8080)
        parser.add_argument(
            '-D', '--debug',
            help='activates debug mode',
            dest='debug',
            action='store_true')
        parser.add_argument(
            '-c', '--cfgdir',
            help='configuration files directory path',
            dest='cfg_dir',
            default=None)
        parser.add_argument(
            '-S', '--simul',
            help='simulates hardware',
            dest='simulation',
            action='store_true')

        cli_args = parser.parse_args()

        if cli_args.debug:
            log.warn('debug mode activated')

        log.info("command line arguments : %s", cli_args)

        ctrl = DemonstratorController(debug=cli_args.debug, simulation=cli_args.simulation, cfg_dir=cli_args.cfg_dir)

        app = DemoColorApp(ctrl, debug=cli_args.debug)
        app.start(listen_port=cli_args.listen_port)

    except Exception as e:
        log.exception('unexpected error - aborting')
        sys.exit(1)

    else:
        log.info('terminated')