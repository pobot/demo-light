#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json

__author__ = 'Eric Pascual (for POBOT)'

import tornado.ioloop
import tornado.web
import tornado.log
from tornado.web import HTTPError

import os
import logging

import uimodules
import api

APP_NAME = 'pjc-compmgr'

_here = os.path.dirname(__file__)


ADCPi = None
BlinkM = None
GPIO = None


def set_simulation_mode(simul):
    global ADCPi
    global BlinkM
    global GPIO

    if not simul:
        from ABElectronics_ADCPi import ADCPi
        from pyblinkm import BlinkM
        import RPi.GPIO as GPIO
    else:
        from simulation import ADCPi, BlinkM
        import simulation
        GPIO = simulation.GPIO()


class WSHUIHandler(tornado.web.RequestHandler):
    def get_template_args(self):
        return {
            'app_title':"Capteurs de lumière et de couleur"
        }

    def get(self, *args, **kwargs):
        """ By default, the get method displays the "Not yet implemented message".
        """
        self.render(
            os.path.join(self.application.template_home, "nyi.html"),
            **self.get_template_args()
        )


class WSHHome(WSHUIHandler):
    def get(self, *args, **kwargs):
        self.render(
            os.path.join(self.application.template_home, "home.html"),
            **self.get_template_args()
        )


class WSHWhiteBlackDetection(WSHUIHandler):
    pass


class WSHColorDetection(WSHUIHandler):
    pass


class WSHCalibration(WSHUIHandler):
    def get(self, *args, **kwargs):
        self.render(
            os.path.join(self.application.template_home, "calibration.html"),
            **self.get_template_args()
        )


class WSHOptoFence(WSHUIHandler):
    def get(self, *args, **kwargs):
        template_args = self.get_template_args()
        template_args['demo_title'] = "Barrière optique"

        self.render(
            os.path.join(self.application.template_home, "opto_fence.html"),
            **template_args
        )


class DemoColorApp(tornado.web.Application):
    """ The Web application
    """
    _CONFIG_FILE_NAME = "demo-color.cfg"

    _res_home = os.path.join(_here, "static")
    _templates_home = os.path.join(_here, "templates")

    handlers = [
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(_res_home, 'css')}),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(_res_home, 'js')}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(_res_home, 'img')}),

        (r"/", WSHHome),

        (r"/settings/calibration", WSHCalibration),
        (r"/settings/calibration/barrier/(?P<level>[0-1])", api.WSHCalibrationBarrier),
        (r"/settings/calibration/bw_detector/(?P<level>[0-1])", api.WSHCalibrationBWDetector),

        (r"/demo/opto_fence", WSHOptoFence),
        (r"/demo/opto_fence/(?P<input_id>[1-3])", api.WSHOptoFenceGetSample),
        (r"/demo/opto_fence/light", api.WSHOptoFenceActivateLight),
        (r"/demo/wb_detection", WSHWhiteBlackDetection),
        (r"/demo/color_detection", WSHColorDetection),
    ]

    def __init__(self, settings_override):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.INFO)
        self.log.info('starting')

        settings = {
            'debug': False,
            'simul': False,
            'template_path': self._templates_home,
            'ui_modules': uimodules,
            'blinkm_addr': 0x09,
            'adc1_addr': 0x68,
            'adc2_addr': 0x69,
            'adc_bits': 12,
            'adc_barrier': 1,
            'gpio_barrier': 12,
            'adc_bw_detector': 2,
            'gpio_bw_detector': 13,
            'shunts': [10000] * 3,
            'thresholds': [4.2] * 3,
            'port':8080
        }

        if os.getuid() == 0:
            cfg_file_path = os.path.join('/etc/', self._CONFIG_FILE_NAME)
        else:
            cfg_file_path = os.path.expanduser('~/.' + self._CONFIG_FILE_NAME)
        if os.path.exists(cfg_file_path):
            cfg = json.load(file(cfg_file_path, 'rt'))
            settings.update(cfg)

        settings.update(settings_override)
        self.debug = settings['debug']
        if self.debug:
            self.log.setLevel(logging.DEBUG)

        set_simulation_mode(settings['simul'])

        self._blinkm = BlinkM(addr=settings['blinkm_addr'])
        self._blinkm.reset()

        self._adc = ADCPi(settings['adc1_addr'], settings['adc2_addr'], settings['adc_bits'])

        GPIO.setmode(GPIO.BOARD)

        self._adc_barrier = settings['adc_barrier']
        self._gpio_barrier = settings['gpio_barrier']

        GPIO.setup(self._gpio_barrier, GPIO.OUT)

        self._adc_bw_detector = settings['adc_bw_detector']
        self._gpio_bw_detector = settings['gpio_bw_detector']

        GPIO.setup(self._gpio_bw_detector, GPIO.OUT)

        self._port = settings['port']

        self._shunts = settings['shunts']
        self._thresholds = settings['thresholds']

        self._barrier_level_voltage = [0, 0]
        self._wb_detector_level_voltage = [0, 0]
        self._white_component_voltage = {'R': 0, 'G': 0, 'B': 0}
        self._black_component_voltage = {'R': 0, 'G': 0, 'B': 0}

        super(DemoColorApp, self).__init__(self.handlers, **settings)

    @property
    def template_home(self):
        return self._templates_home

    @property
    def blinkm(self):
        return self._blinkm

    @property
    def adc(self):
        return self._adc

    @property
    def gpio(self):
        return self._gpio

    def shunt(self, input_id):
        return self._shunts[input_id]

    def threshold(self, input_id):
        return self._thresholds[input_id]

    def start(self):
        """ Starts the application
        """
        self.listen(self._port)
        try:
            self.log.info('listening on port %d', self._port)
            tornado.ioloop.IOLoop.instance().start()

        except KeyboardInterrupt:
            print # cosmetic to keep log messages nicely aligned
            self.log.info('SIGTERM caught')

        finally:
            GPIO.cleanup()

    def set_barrier_light(self, on):
        GPIO.output(self._gpio_barrier, 1 if on else 0)

    def get_barrier_input(self):
        return self.adc.readVoltage(self._adc_barrier)

    def set_barrier_level_voltage(self, level, voltage):
        if level not in (0, 1):
            raise ValueError('invalid level (%d)' % level)
        self._barrier_level_voltage[level] = voltage

    def set_bw_detector_light(self, on):
        GPIO.output(self._gpio_bw_detector, 1 if on else 0)

    def get_bw_detector_input(self):
        return self.adc.readVoltage(self._adc_bw_detector)

    def set_bw_detector_level_voltage(self, level, voltage):
        if level not in (0, 1):
            raise ValueError('invalid level (%d)' % level)
        self._wb_detector_level_voltage[level] = voltage

    def set_white_component_voltage(self, component, voltage):
        if component not in self._white_component_voltage:
            raise ValueError('invalid component (%s)' % component)
        self._white_component_voltage[component] = voltage

    def set_black_component_voltage(self, component, voltage):
        if component not in self._black_component_voltage:
            raise ValueError('invalid component (%s)' % component)
        self._black_component_voltage[component] = voltage