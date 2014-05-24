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
import wsapi


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


class WSHBarrier(WSHUIHandler):
    def get(self, *args, **kwargs):
        template_args = self.get_template_args()
        template_args['demo_title'] = "Barrière optique"

        self.render(
            os.path.join(self.application.template_home, "barrier.html"),
            **template_args
        )


_here = os.path.dirname(__file__)


class DemoColorApp(tornado.web.Application):
    """ The Web application
    """
    _res_home = os.path.join(_here, "static")
    _templates_home = os.path.join(_here, "templates")

    settings = {
        'template_path': _templates_home,
        'ui_modules': uimodules,
        'port':8080
    }

    handlers = [
        (r"/css/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(_res_home, 'css')}),
        (r"/js/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(_res_home, 'js')}),
        (r"/img/(.*)", tornado.web.StaticFileHandler, {"path": os.path.join(_res_home, 'img')}),

        (r"/", WSHHome),

        (r"/settings/calibration", WSHCalibration),
        (r"/settings/calibration/barrier", wsapi.WSHCalibrationBarrier),
        (r"/settings/calibration/barrier/(?P<level>[0-1])", wsapi.WSHCalibrationBarrier),

        (r"/settings/calibration/bw_detector", wsapi.WSHCalibrationBWDetector),
        (r"/settings/calibration/bw_detector/sample", wsapi.WSHCalibrationBWDetector),

        (r"/demo/barrier", WSHBarrier),
        (r"/demo/barrier/sample", wsapi.WSHBarrierGetSample),
        (r"/demo/barrier/light", wsapi.WSHBarrierActivateLight),
        (r"/demo/wb_detection", WSHWhiteBlackDetection),
        (r"/demo/color_detection", WSHColorDetection),
    ]

    def __init__(self, controller, runtime_settings):
        self.log = logging.getLogger(self.__class__.__name__)
        self.log.setLevel(logging.INFO)
        self.log.info('starting')

        self._controller = controller

        self.settings.update(runtime_settings)
        self.debug = self.settings['debug']
        if self.debug:
            self.log.setLevel(logging.DEBUG)

        self._port = self.settings['port']

        super(DemoColorApp, self).__init__(self.handlers, **self.settings)

    @property
    def template_home(self):
        return self._templates_home

    @property
    def controller(self):
        return self._controller

    def start(self):
        """ Starts the application
        """
        self._controller.start()

        self.listen(self._port)
        try:
            self.log.info('listening on port %d', self._port)
            tornado.ioloop.IOLoop.instance().start()

        except KeyboardInterrupt:
            print # cosmetic to keep log messages nicely aligned
            self.log.info('SIGTERM caught')

        finally:
            self._controller.shutdown()

