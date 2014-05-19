#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import json
import time

import tornado

BARRIER_LDR_INPUT_ID = 1
WBDETECTOR_LDR_INPUT_ID = 2

class WSHOptoFenceGetSample(tornado.web.RequestHandler):
    def get(self, input_id):
        input_id = int(input_id)
        if input_id not in (1, 2, 3):
            self.set_status(status_code=400, reason="invalid input id: %d" % input_id)
            self.finish()
            return

        try:
            voltage = self.application.read_voltage(input_id)
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (input_id=%d)" % input_id)
            self.finish()
        else:
            self.finish(json.dumps({
                "current": voltage / self.application.shunt(input_id) * 1000,
                "detection": voltage < self.application.threshold(input_id)
            }))


class WSHOptoFenceActivateLight(tornado.web.RequestHandler):
    def post(self):
        status = self.get_argument("status") == '1'
        self.application.activate_barrier_light(status);


class WSHCalibrationBarrier(tornado.web.RequestHandler):
    def get(self, level):
        level = int(level)
        self.application.set_barrier_light(level == 1);
        time.sleep(0.5)
        try:
            voltage = self.application.get_barrier_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (barrier)")
            self.finish()
        else:
            self.application.set_barrier_level_voltage(level, voltage)
            self.finish(json.dumps({
                "voltage": voltage
            }))
        finally:
            if level:
                self.application.set_barrier_light(False)


class WSHCalibrationBWDetector(tornado.web.RequestHandler):
    def get(self, level):
        level = int(level)
        self.application.set_bw_detector_light(level == 1);
        time.sleep(0.5)
        try:
            voltage = self.application.get_bw_detector_input()
        except IOError as e:
            self.set_status(status_code=404, reason="IOError (bw_detector)")
            self.finish()
        else:
            self.application.set_bw_detector_level_voltage(level, voltage)
            self.finish(json.dumps({
                "voltage": voltage
            }))
        finally:
            if level:
                self.application.set_bw_detector_light(False)