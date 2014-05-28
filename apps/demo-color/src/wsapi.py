#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import json
import time
import logging

from tornado.web import RequestHandler

from controller import DemonstratorController

BARRIER_LDR_INPUT_ID = 1
BW_DETECTOR_LDR_INPUT_ID = 2


class Logged(object):
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)


class WSBarrierSample(RequestHandler, Logged):
    def get(self):
        try:
            current_mA, detection = self.application.controller.analyze_barrier_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (barrier sensor)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA,
                "detection": detection
            }))


class WSBarrierLight(RequestHandler, Logged):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_barrier_light(status);


class WSBarrierCalibrationStep(WSBarrierSample):
    def get(self, step):
        step = int(step)
        self.logger.info("executing calibration step %d", step)

        self.application.controller.set_barrier_light(step == 1);
        time.sleep(2)
        super(WSBarrierCalibrationStep, self).get()

        if step == 1:
            self.application.controller.set_barrier_light(False);


class WSBarrierCalibrationStore(RequestHandler, Logged):
    def post(self):
        ambient, lightened = (float(self.get_argument(a)) for a in ('ambient', 'lightened'))
        self.logger.info("storing references : ambient=%f lightened=%f", ambient, lightened)
        self.application.controller.set_barrier_reference_levels(ambient, lightened)


class WSBWDetectorSample(RequestHandler, Logged):
    def get(self):
        try:
            current_mA, color = self.application.controller.analyze_bw_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (B/W detector sensor)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA,
                "color": "white" if color else "black"
            }))


class WSBWDetectorLight(RequestHandler, Logged):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_bw_detector_light(status);


class WSBWDetectorCalibrationSample(WSBWDetectorSample):
    def get(self):
        self.application.controller.set_barrier_light(True);
        time.sleep(2)
        super(WSBWDetectorCalibrationSample, self).get()
        self.application.controller.set_barrier_light(False);


class WSBWDetectorCalibrationStore(RequestHandler, Logged):
    def post(self):
        black, white = (float(self.get_argument(a)) for a in ('b', 'w'))
        self.logger.info("storing references : black=%f white=%f", black, white)
        self.application.controller.set_bw_detector_reference_levels(black, white)


class WSColorDetectorSample(RequestHandler, Logged):
    COLORS = ('none', 'red', 'green', "blue")
    REQ_PARM_TO_COLOR = {
        'r': DemonstratorController.RED,
        'g': DemonstratorController.GREEN,
        'b': DemonstratorController.BLUE
    }

    def get(self, color):
        self.application.controller.set_color_detector_light(self.REQ_PARM_TO_COLOR[color])
        time.sleep(2)

        try:
            current_mA, color = self.application.controller.analyze_color_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (color detector sensor)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA,
                "color": self.COLORS[color]
            }))


class WSColorDetectorLight(RequestHandler, Logged):
    def post(self):
        color = int(self.get_argument("color"))
        self.application.controller.set_color_detector_light(color);


class WSColorDetectorCalibrationStore(RequestHandler, Logged):
    def post(self, color):
        if color not in ('w', 'b'):
            raise ValueError("invalid color parameter : %s" % color)

        r, g, b = (float(self.get_argument(a)) for a in ('r', 'g', 'b'))
        self.logger.info("storing references : R=%f G=%f B=%f", r, g, b)
        self.application.controller.set_color_detector_reference_levels(color, (r, g, b))