#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import json
import time

from tornado.web import RequestHandler

BARRIER_LDR_INPUT_ID = 1
BW_DETECTOR_LDR_INPUT_ID = 2


class WSBarrierSample(RequestHandler):
    def get(self):
        light = self.get_argument('light', None)
        if light in (0, 1):
            self.application.controller.set_barrier_light(light == 1)
            time.sleep(1)

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


class WSBarrierLight(RequestHandler):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_barrier_light(status);


class WSBarrierCalibration(RequestHandler):
    def post(self):
        self.application.controller.set_barrier_reference_levels(
            float(self.get_argument('ambient')),
            float(self.get_argument('lightened'))
        )


class WSBWDetectorSample(RequestHandler):
    def get(self):
        light = self.get_argument('light', None)
        if light in (0, 1):
            self.application.controller.set_barrier_light(light == 1)
            time.sleep(1)

        try:
            current_mA, color = self.application.controller.analyze_bw_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (bw_detector)")
            self.finish()
        else:
            self.finish(json.dumps({
                "current": current_mA,
                "color": "white" if color else "black"
            }))


class WSBWDetectorLight(RequestHandler):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.controller.set_bw_detector_light(status);


class WSBWDetectorCalibration(RequestHandler):
    def post(self):
        self.application.controller.set_bw_detector_reference_levels(
            float(self.get_argument('b')),
            float(self.get_argument('w'))
        )
