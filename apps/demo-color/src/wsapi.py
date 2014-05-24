#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import json
import time

import tornado

from controller import DemonstratorController

BARRIER_LDR_INPUT_ID = 1
BW_DETECTOR_LDR_INPUT_ID = 2


class WSHBarrierGetSample(tornado.web.RequestHandler):
    def get(self):
        try:
            current_mA, detection = self.application.controller.analyze_barrier_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA,
                "detection": detection
            }))


class WSHBarrierActivateLight(tornado.web.RequestHandler):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_barrier_light(status);


class WSHReflexActivateLight(tornado.web.RequestHandler):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_reflex_light(status);


class WSHCalibrationBarrier(tornado.web.RequestHandler):
    def get(self, level):
        level = int(level)
        self.application.controller.set_barrier_light(level == DemonstratorController.LIGHTENED);
        time.sleep(1)
        try:
            current_mA, _ = self.application.controller.analyze_barrier_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (barrier)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA
            }))
        finally:
            if level:
                self.application.controller.set_barrier_light(False)

    def post(self):
        self.application.controller.set_barrier_reference_levels(
            float(self.get_argument('ambient')),
            float(self.get_argument('lightened'))
        )


class WSHCalibrationBWDetector(tornado.web.RequestHandler):
    def get(self):
        self.application.controller.set_bw_detector_light(True);
        time.sleep(1)
        try:
            current_mA, _ = self.application.controller.analyze_bw_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (bw_detector)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA
            }))
        finally:
            self.application.controller.set_bw_detector_light(False)

    def post(self):
        self.application.controller.set_bw_detector_reference_levels(
            float(self.get_argument('b')),
            float(self.get_argument('w'))
        )
