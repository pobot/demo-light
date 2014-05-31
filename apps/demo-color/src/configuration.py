# !/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import os
import json

APP_NAME = 'demo-light-sensors'


class Configuration(object):
    CONFIG_FILE_NAME = None
    _data = None
    _path = None

    def __init__(self, autoload=False, cfg_dir=None):
        self._cfg_dir = cfg_dir
        self._path = self.get_default_path()

        if autoload:
            self.load()

    def get_default_path(self):
        if self._cfg_dir:
            return os.path.join(self._cfg_dir,  self.CONFIG_FILE_NAME)
        elif os.getuid() == 0:
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

    def __init__(self, *args, **kwargs):
        self._data = {
            'listen_port': 8080,
            'blinkm_addr': 0x09,
            'adc1_addr': 0x68,
            'adc2_addr': 0x69,
            'adc_bits': 12,
            'shunts': [10000] * 3,
            'barrier_adc': 1,
            'bw_detector_adc': 2,
            'color_detector_adc': 3,
            'barrier_led_gpio': 12,
            'bw_detector_led_gpio': 13,
        }
        super(SystemConfiguration, self).__init__(*args, **kwargs)

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
        self._data['adc_bits'] = value

    @property
    def shunts(self):
        return self._data['shunts'][:]

    @shunts.setter
    def shunts(self, value):
        self._data['shunts'] = value[:]

    @property
    def barrier_adc(self):
        return self._data['barrier_adc']

    @barrier_adc.setter
    def barrier_adc(self, value):
        self._data['barrier_adc'] = value

    @property
    def bw_detector_adc(self):
        return self._data['bw_detector_adc']

    @bw_detector_adc.setter
    def bw_detector_adc(self, value):
        self._data['bw_detector_adc'] = value

    @property
    def color_detector_adc(self):
        return self._data['color_detector_adc']

    @color_detector_adc.setter
    def color_detector_adc(self, value):
        self._data['color_detector_adc'] = value

    @property
    def barrier_led_gpio(self):
        return self._data['barrier_led_gpio']

    @barrier_led_gpio.setter
    def barrier_led_gpio(self, value):
        self._data['barrier_led_gpio'] = value

    @property
    def bw_detector_led_gpio(self):
        return self._data['bw_detector_led_gpio']

    @bw_detector_led_gpio.setter
    def bw_detector_led_gpio(self, value):
        self._data['bw_detector_led_gpio'] = value


class CalibrationConfiguration(Configuration):
    CONFIG_FILE_NAME = "calibration.cfg"
    _V2_0 = [0] * 2
    _V3_0 = [0] * 3

    def __init__(self, *args, **kwargs):
        self._data = {
            'barrier': [0, 0],      # (free, occupied)
            'bw_detector': [0, 0],  # (black, white)
            'color_detector': {
                'b': [0] * 3,       # (R, G, B)
                'w': [0] * 3
            }
        }
        super(CalibrationConfiguration, self).__init__(*args, **kwargs)

    @property
    def barrier(self):
        return self._data['barrier'][:]

    @barrier.setter
    def barrier(self, value):
        self._data['barrier'] = value[:]

    def barrier_is_set(self):
        return self._data['barrier'] != self._V2_0

    @property
    def bw_detector(self):
        return self._data['bw_detector'][:]

    @bw_detector.setter
    def bw_detector(self, value):
        self._data['bw_detector'] = value[:]

    def bw_detector_is_set(self):
        return self._data['bw_detector'] != self._V2_0

    @property
    def color_detector_black(self):
        return self._data['color_detector']['b'][:]

    @color_detector_black.setter
    def color_detector_black(self, value):
        self._data['color_detector']['b'] = value[:]

    @property
    def color_detector_white(self):
        return self._data['color_detector']['w'][:]

    @color_detector_white.setter
    def color_detector_white(self, value):
        self._data['color_detector']['w'] = value[:]

    def color_detector_is_set(self):
        return self.color_detector_white != self._V3_0 \
            and self.color_detector_black != self._V3_0

    def is_complete(self):
        return self.barrier_is_set() and self.bw_detector_is_set() and self.color_detector_is_set()

    def is_new(self):
        return not self.barrier_is_set() and not self.bw_detector_is_set() and not self.color_detector_is_set()

    def as_dict(self):
        return self._data