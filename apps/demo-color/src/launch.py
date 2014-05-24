#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Color sensing demonstrator web application.
"""

__author__ = 'Eric Pascual (for POBOT)'

import logging
import os
import json

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
            '-D', '--debug',
            help='activates debug mode',
            dest='debug',
            action='store_true')
        parser.add_argument(
            '-S', '--simul',
            help='simulates hardware',
            dest='simulated_hw',
            action='store_true')
        parser.add_argument(
            '-p', '--port',
            help='listen on port',
            dest='port',
            default=8080)
        parser.add_argument(
            '--blinkm-addr',
            help='BlinkM I2C address',
            type=int,
            dest='blinkm_addr',
            default=0x09)
        parser.add_argument(
            '--adc1-addr',
            help='ADC1 I2C address',
            type=int,
            dest='adc1_addr',
            default=0x68)
        parser.add_argument(
            '--adc2-addr',
            help='ADC2 I2C address',
            type=int,
            dest='adc2_addr',
            default=0x69)
        parser.add_argument(
            '--adc-bits',
            help='ADC resolution',
            type=int,
            dest='adc_bits',
            default=12)

        cli_args = parser.parse_args()

        if cli_args.debug:
            log.warn('debug mode activated')


        runtime_settings = None
        if os.getuid() == 0:
            cfg_file_path = os.path.join('/etc/', _CONFIG_FILE_NAME)
        else:
            cfg_file_path = os.path.expanduser('~/.' + _CONFIG_FILE_NAME)
        if os.path.exists(cfg_file_path):
            runtime_settings = json.load(file(cfg_file_path, 'rt'))

        # updates the app settings dictionary from the CLI args
        cli_settings = dict([
            (k, getattr(cli_args, k)) for k in dir(cli_args) if not k.startswith('_')
        ])
        log.info("command line arguments : %s", cli_settings)

        if runtime_settings:
            runtime_settings.update(cli_settings)
        else:
            runtime_settings = cli_settings

        log.info("runtime settings : %s", runtime_settings)

        ctrl = DemonstratorController(runtime_settings)

        app = DemoColorApp(ctrl, runtime_settings)
        app.start()

    except Exception as e:
        log.exception('unexpected error - aborting')

    else:
        log.info('terminated')