# !/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import os
import json

APP_NAME = 'demo-light-sensors'

class Configuration(object):
    def get_default_path(self):
        if os.getuid() == 0:
            return os.path.join('/etc', APP_NAME, self.CONFIG_FILE_NAME)
        else:
            return os.path.expanduser(os.path.join('~', '.' + APP_NAME, self.CONFIG_FILE_NAME))

    def load(self, path=None):
        if not path:
            path = self._path
        self._data.update(json.load(file(path, 'rt')))

    def save(self, path=None):
        if not path:
            path = self._path
        json.dump(self._data, file(path, 'wt'), indent=4)


class SystemConfiguration(Configuration):
    CONFIG_FILE_NAME = "system.cfg"

    def __init__(self):
        self._data = {
            'listen_port': 8080,
            'blinkm_addr': 0x09,
            'adc1_addr': 0x68,
            'adc2_addr': 0x69,
            'adc_bits': 12,
            'shunts': [10000] *3
        }
        self._path = self.get_default_path()

    @property
    def listen_port(self):
        return self._data['listen_port']

    @listen_port.setter
    def listen_port(self, value):
        self._data['listen_port'] = value

    @property
    def blinkm_addr(self):
        return self._data['blinkm_addr']

    @blinkm_addr.setter
    def blinkm_addr(self, value):
        self._data['blinkm_addr'] = value

    @property
    def adc1_addr(self):
        return self._data['adc1_addr']

    @adc1_addr.setter
    def adc1_addr(self, value):
        self._data['adc1_addr'] = value

    @property
    def adc2_addr(self):
        return self._data['adc2_addr']

    @adc2_addr.setter
    def adc2_addr(self, value):
        self._data['adc2_addr'] = value

    @property
    def adc_bits(self):
        return self._data['adc_bits']

    @adc_bits.setter
    def adc_bits(self, value):
        self._data['adc_bits']

    @property
    def shunts(self):
        return self._data['shunts']

    @shunts.setter
    def shunts(self, value):
        self._data['shunts'] = value[:]


class CalibrationConfiguration(Configuration):
    CONFIG_FILE_NAME = "calibration.cfg"

    def __init__(self):
        self._data = {
            'barrier': [0, 0],
            'bw_detector': [0, 0],
            'color_detector': {
                'b': [0] * 3,
                'w': [0] * 3
            }
        }
