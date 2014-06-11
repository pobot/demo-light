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
            current_mA = self.application.controller.sample_barrier_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (barrier sensor)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA,
            }))


class WSBarrierSampleAndAnalyze(RequestHandler, Logged):
    def get(self):
        try:
            current_mA = self.application.controller.sample_barrier_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (barrier sensor)")
            self.finish()
        else:
            detection = self.application.controller.analyze_barrier_input(current_mA)
            self.finish(json.dumps({
                "current": current_mA,
                "detection": detection
            }))


class WSBarrierLight(RequestHandler, Logged):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_barrier_light(status);


class WSBarrierCalibrationSample(WSBarrierSample):
    def get(self):
        self.application.controller.set_barrier_light(True);
        time.sleep(2)
        super(WSBarrierCalibrationSample, self).get()
        self.application.controller.set_barrier_light(False);


class WSBarrierCalibrationStatus(RequestHandler, Logged):
    def get(self):
        self.finish(json.dumps({
            "calibrated": 1 if self.application.controller.barrier_is_calibrated() else 0
        }))


class WSBarrierCalibrationStore(RequestHandler, Logged):
    def post(self):
        free, occupied = (float(self.get_argument(a)) for a in ('free', 'occupied'))
        self.logger.info("storing references : free=%f occupied=%f", free, occupied)
        self.application.controller.set_barrier_reference_levels(free, occupied)
        self.application.controller.save_calibration()


class WSBWDetectorSample(RequestHandler, Logged):
    def get(self):
        try:
            current_mA = self.application.controller.sample_bw_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (B/W detector sensor)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA
            }))


class WSBWDetectorSampleAndAnalyze(RequestHandler, Logged):
    def get(self):
        try:
            current_mA = self.application.controller.sample_bw_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (B/W detector sensor)")
            self.finish()
        else:
            color = self.application.controller.analyze_bw_detector_input(current_mA)
            self.finish(json.dumps({
                "current": current_mA,
                "color": "white" if color == self.application.controller.BW_WHITE else "black"
            }))


class WSBWDetectorLight(RequestHandler, Logged):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_bw_detector_light(status);


class WSBWDetectorCalibrationSample(WSBWDetectorSample):
    def get(self):
        self.application.controller.set_bw_detector_light(True);
        time.sleep(2)
        super(WSBWDetectorCalibrationSample, self).get()
        self.application.controller.set_bw_detector_light(False);


class WSBWDetectorCalibrationStatus(RequestHandler, Logged):
    def get(self):
        self.finish(json.dumps({
            "calibrated": 1 if self.application.controller.bw_detector_is_calibrated() else 0
        }))


class WSBWDetectorCalibrationStore(RequestHandler, Logged):
    def post(self):
        black, white = (float(self.get_argument(a)) for a in ('b', 'w'))
        self.logger.info("storing references : black=%f white=%f", black, white)
        self.application.controller.set_bw_detector_reference_levels(black, white)
        self.application.controller.save_calibration()


class WSColorDetectorSample(RequestHandler, Logged):
    def get(self):
        color = self.get_argument('color', None)
        if color and color in '0rgb':
            self.application.controller.set_color_detector_light('0rgb'.index(color))
        time.sleep(1)

        try:
            current_mA = self.application.controller.sample_color_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (color_detector)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA
            }))
        finally:
            if color:
                self.application.controller.set_color_detector_light(0)


class WSColorDetectorAnalyze(RequestHandler):
    def get(self):
        sample = [self.get_argument(comp) for comp in ('r', 'g', 'b')]
        color, decomp = self.application.controller.analyze_color_input(sample)
        self.finish(json.dumps({
            "color": DemonstratorController.COLOR_NAMES[color],
            "decomp": [d * 100 for d in decomp]
        }))


class WSColorDetectorLight(RequestHandler, Logged):
    def post(self, color):
        self.application.controller.set_color_detector_light('0rgb'.index(color));


class WSColorDetectorCalibrationStore(RequestHandler, Logged):
    def post(self, color):
        if color not in ('w', 'b'):
            raise ValueError("invalid color parameter : %s" % color)

        r, g, b = (float(self.get_argument(a)) for a in ('r', 'g', 'b'))
        self.logger.info("storing references : R=%f G=%f B=%f", r, g, b)
        self.application.controller.set_color_detector_reference_levels(color, (r, g, b))
        self.application.controller.save_calibration()


class WSColorDetectorCalibrationStatus(RequestHandler, Logged):
    def get(self):
        self.finish(json.dumps({
            "calibrated": 1 if self.application.controller.color_detector_is_calibrated() else 0
        }))


class WSCalibrationData(RequestHandler, Logged):
    def get(self):
        self.finish(self.application.controller.get_calibration_cfg_as_dict())