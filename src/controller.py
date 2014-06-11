#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

import configuration
import logging

ADCPi = None
BlinkM = None
GPIO = None


def set_simulation_mode(simulated_hw):
    global ADCPi
    global BlinkM
    global GPIO

    if not simulated_hw:
        from extlibs.ABElectronics_ADCPi import ADCPi
        from extlibs.pyblinkm import BlinkM
        import RPi.GPIO as GPIO
    else:
        from simulation import ADCPi, BlinkM
        import simulation
        GPIO = simulation.GPIO()


class DemonstratorController(object):
    LDR_BARRIER = 0
    LDR_BW = 1
    LDR_COLOR = 2

    AMBIENT = 0
    LIGHTENED = 1

    BW_BLACK = 0
    BW_WHITE = 1

    COLOR_UNDEF = 0
    COLOR_RED = 1
    COLOR_GREEN = 2
    COLOR_BLUE = 3
    COLOR_BLACK = 4
    COLOR_WHITE = 5

    COLOR_NAMES = (
        'undef',
        'red',
        'green',
        'blue',
        'black',
        'white'
    )

    COLOR_COMPONENTS = (
        # (R, G, B)
        (0, 0, 0),
        (255, 0, 0),
        (0, 128, 0),
        (0, 0, 255),
        (0, 0, 0),
        (255, 255, 255)
    )

    def __init__(self, debug=False, simulation=False, cfg_dir=None):
        self._log = logging.getLogger(self.__class__.__name__)

        self._system_cfg = configuration.SystemConfiguration(
            cfg_dir=cfg_dir,
            autoload=True
        )

        set_simulation_mode(simulation)

        self._blinkm = BlinkM(addr=self._system_cfg.blinkm_addr)
        try:
            self._blinkm.reset()
        except IOError:
            self._log.error("BlinkM reset error. Maybe not here")
            self._blinkm = None

        self._adc = ADCPi(
            self._system_cfg.adc1_addr,
            self._system_cfg.adc2_addr,
            self._system_cfg.adc_bits
        )

        GPIO.setmode(GPIO.BOARD)

        self._barrier_adc = self._system_cfg.barrier_adc
        self._barrier_led_gpio = self._system_cfg.barrier_led_gpio

        GPIO.setup(self._barrier_led_gpio, GPIO.OUT)

        self._bw_detector_adc = self._system_cfg.bw_detector_adc
        self._bw_detector_led_gpio = self._system_cfg.bw_detector_led_gpio

        GPIO.setup(self._bw_detector_led_gpio, GPIO.OUT)

        self._color_detector_adc = self._system_cfg.color_detector_adc

        self._listen_port = self._system_cfg.listen_port

        self._shunts = self._system_cfg.shunts

        # process stored calibration data

        self._barrier_threshold = \
            self._bw_detector_threshold = \
            self._white_rgb_levels = \
            self._black_rgb_levels = None

        self._calibration_cfg = configuration.CalibrationConfiguration(
            cfg_dir=cfg_dir,
            autoload=True
        )

        if self._calibration_cfg.barrier_is_set():
            self.set_barrier_reference_levels(*self._calibration_cfg.barrier)

        if self._calibration_cfg.bw_detector_is_set():
            self.set_bw_detector_reference_levels(*self._calibration_cfg.bw_detector)

        if self._calibration_cfg.color_detector_is_set():
            self.set_color_detector_reference_levels('w', self._calibration_cfg.color_detector_white)
            self.set_color_detector_reference_levels('b', self._calibration_cfg.color_detector_black)

    @property
    def blinkm(self):
        return self._blinkm

    @property
    def adc(self):
        return self._adc

    @property
    def gpio(self):
        return self._gpio

    def start(self):
        pass

    def shutdown(self):
        GPIO.cleanup()

    def shunt(self, input_id):
        return self._shunts[input_id]

    def threshold(self, input_id):
        if input_id == self.LDR_BARRIER:
            return self._barrier_threshold
        elif input_id == self.LDR_BW:
            return self._bw_detector_threshold
        else:
            raise ValueError('no threshold defined for input (%d)' % input_id)

    def sample_barrier_input(self):
        v = self.adc.readVoltage(self._barrier_adc)
        i_mA = v / self._shunts[self.LDR_BARRIER] * 1000.
        return i_mA

    def set_barrier_reference_levels(self, level_free, level_occupied):
        self._calibration_cfg.barrier = [level_free, level_occupied]
        self._barrier_threshold = (level_free + level_occupied) / 2.

    def set_barrier_light(self, on):
        GPIO.output(self._barrier_led_gpio, 1 if on else 0)

    def barrier_is_calibrated(self):
        return self._barrier_threshold is not None

    def analyze_barrier_input(self, i_mA):
        if not self.barrier_is_calibrated():
            raise NotCalibrated('barrier')

        detection = i_mA < self._barrier_threshold
        return detection

    def sample_bw_detector_input(self):
        v = self.adc.readVoltage(self._bw_detector_adc)
        i_mA = v / self._shunts[self.LDR_BW] * 1000.
        return i_mA

    def set_bw_detector_reference_levels(self, level_black, level_white):
        self._calibration_cfg.bw_detector = [level_black, level_white]
        self._bw_detector_threshold = (level_black + level_white) / 2.

    def set_bw_detector_light(self, on):
        GPIO.output(self._bw_detector_led_gpio, 1 if on else 0)

    def bw_detector_is_calibrated(self):
        return self._bw_detector_threshold is not None

    def analyze_bw_detector_input(self, i_mA):
        if not self.bw_detector_is_calibrated():
            raise NotCalibrated('bw_detector')

        color = self.BW_BLACK if i_mA < self._bw_detector_threshold else self.BW_WHITE
        return color

    def sample_color_detector_input(self):
        v = self.adc.readVoltage(self._color_detector_adc)
        i_mA = v / self._shunts[self.LDR_COLOR] * 1000.
        return i_mA

    def set_color_detector_reference_levels(self, white_or_black, levels):
        if white_or_black == 'b':
            self._calibration_cfg.color_detector_black = levels[:]
        elif white_or_black == 'w':
            self._calibration_cfg.color_detector_white = levels[:]
        else:
            raise ValueError("invalid white/black option (%s)" % white_or_black)

    def set_color_detector_light(self, color):
        if self._blinkm:
            self._blinkm.go_to(*(self.COLOR_COMPONENTS[color]))
        else:
            self._log.error("BlinkM not available")

    def color_detector_is_calibrated(self):
        return self._calibration_cfg.color_detector_is_set()

    def analyze_color_input(self, rgb_sample):
        if not self.color_detector_is_calibrated():
            raise NotCalibrated('color_detector')

        # normalize color components in [0, 1] and in the white-black range
        self._log.debug("analyze %s", rgb_sample)
        rgb_sample = [float(s) for s in rgb_sample]
        comps = [max((s - b) / (w - b), 0)
                 for w, b, s in zip(
                self._calibration_cfg.color_detector_white,
                self._calibration_cfg.color_detector_black,
                rgb_sample
            )]
        self._log.debug("--> comps=%s", comps)

        sum_comps = sum(comps)
        if sum_comps > 0:
            relative_levels = [c / sum_comps for c in comps]
        else:
            relative_levels = [0] * 3
        self._log.debug("--> relative_levels=%s", relative_levels)

        min_comps, max_comps = min(comps), max(comps)

        if min_comps > 0.9:
            color = self.COLOR_WHITE
        elif max_comps < 0.2:
            color = self.COLOR_BLACK
        else:
            over_50 = [c > 0.5 for c in relative_levels]
            if any(over_50):
                color = over_50.index(True) + 1
            else:
                color = self.COLOR_UNDEF

        self._log.debug("--> color=%s", self.COLOR_NAMES[color])
        return color, relative_levels

    def save_calibration(self):
        self._calibration_cfg.save()

    def get_calibration_cfg_as_dict(self):
        return self._calibration_cfg.as_dict()


class ControllerException(Exception):
    pass


class NotCalibrated(ControllerException):
    pass