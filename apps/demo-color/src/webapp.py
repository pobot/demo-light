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
import webui


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
        (r"/favicon\.ico", tornado.web.StaticFileHandler, {"path": os.path.join(_res_home, 'img')}),

        # user interface

        (r"/", webui.UIHome),
        (r"/barrier", webui.UIHBarrier),
        (r"/bw_detector", webui.UIWBDetector),
        (r"/color_detector", webui.UIColorDetector),
        (r"/calibration", webui.UICalibration),

        # API wWeb services

        (r"/barrier/sample", wsapi.WSBarrierSample),
        (r"/barrier/light", wsapi.WSBarrierLight),
        (r"/barrier/calibrate", wsapi.WSBarrierCalibration),

        (r"/bw_detector/sample", wsapi.WSBWDetectorSample),
        (r"/bw_detector/light", wsapi.WSBWDetectorLight),
        (r"/bw_detector/calibrate", wsapi.WSBWDetectorCalibration),

        (r"/color_detector/sample", wsapi.WSColorDetectorSample),
        (r"/color_detector/light", wsapi.WSColorDetectorLight),
        (r"/color_detector/calibrate", wsapi.WSColorDetectorCalibration),
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


