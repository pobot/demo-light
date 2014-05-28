#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'


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

    settings = {
        'debug': False,
        'simulated_hw': False,
        'blinkm_addr': 0x09,
        'adc1_addr': 0x68,
        'adc2_addr': 0x69,
        'adc_bits': 12,
        'adc_barrier': 1,
        'gpio_barrier': 12,
        'adc_bw_detector': 2,
        'gpio_bw_detector': 13,
        'adc_color_detector': 3,
        'shunts': [10000] * 3,
        'thresholds': [0.42] * 3
    }

    COLOR_COMPONENTS = (
        # RGB
        (0, 0, 0),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255)
    )

    def __init__(self, runtime_settings):
        # override default settings with runtime provided ones
        self.settings.update(runtime_settings)

        set_simulation_mode(self.settings['simulated_hw'])

        self._blinkm = BlinkM(addr=self.settings['blinkm_addr'])
        self._blinkm.reset()

        self._adc = ADCPi(self.settings['adc1_addr'], self.settings['adc2_addr'], self.settings['adc_bits'])

        GPIO.setmode(GPIO.BOARD)

        self._adc_barrier = self.settings['adc_barrier']
        self._gpio_barrier = self.settings['gpio_barrier']

        GPIO.setup(self._gpio_barrier, GPIO.OUT)

        self._adc_bw_detector = self.settings['adc_bw_detector']
        self._gpio_bw_detector = self.settings['gpio_bw_detector']

        GPIO.setup(self._gpio_bw_detector, GPIO.OUT)

        self._adc_color_detector = self.settings['adc_color_detector']

        self._port = self.settings['port']

        self._shunts = self.settings['shunts']
        self._thresholds = self.settings['thresholds']

        # barrier sensor input levels for ambient and lightened states
        self._barrier_reference_levels = [0, 0]

        # B/W sensor input levels for ambient and lightened states
        self._bw_detector_reference_levels = [0, 0]

        # color sensor reference levels
        self._color_detector_reference_levels = {
            # white RGB
            'w': (0, 0, 0),
            # black RGB
            'b': (0, 0, 0)
        }

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
        return self._thresholds[input_id]

    def set_barrier_light(self, on):
        GPIO.output(self._gpio_barrier, 1 if on else 0)

    def analyze_barrier_input(self):
        v = self.adc.readVoltage(self._adc_barrier)
        i_mA = v / self._shunts[self.LDR_BARRIER] * 1000.
        detection = i_mA < self._thresholds[self.LDR_BARRIER]
        return i_mA, detection

    def set_barrier_reference_levels(self, level_ambient, level_lightened):
        self._barrier_reference_levels = [level_ambient, level_lightened]
        self._thresholds[self.LDR_BARRIER] = (level_ambient + level_lightened) / 2

    def set_bw_detector_light(self, on):
        GPIO.output(self._gpio_bw_detector, 1 if on else 0)

    def analyze_bw_detector_input(self):
        v = self.adc.readVoltage(self._adc_bw_detector)
        i_mA = v / self._shunts[self.LDR_BW] * 1000.
        color = self.BW_BLACK if i_mA < self._thresholds[self.LDR_BW] else self.BW_WHITE
        return i_mA, color

    def set_bw_detector_reference_levels(self, level_ambient, level_lightened):
        self._bw_detector_reference_levels = [level_ambient, level_lightened]
        self._thresholds[self.LDR_BW] = (level_ambient + level_lightened) / 2

    def set_color_detector_light(self, color):
        self._blinkm.go_to(*(self.COLOR_COMPONENTS[color]))

    def sample_color_detector_input(self):
        v = self.adc.readVoltage(self._adc_color_detector)
        i_mA = v / self._shunts[self.LDR_COLOR] * 1000.
        return i_mA

    def set_color_detector_reference_levels(self, white_or_black, levels):
        if white_or_black in self._color_detector_reference_levels:
            self._color_detector_reference_levels[white_or_black] = levels[:]
        else:
            raise ValueError("invalid white/black option (%s)" % white_or_black)

    def color_detector_calibrated(self):
        return all(any(c > 0 for c in refs) for refs in self._color_detector_reference_levels.itervalues())


    def analyze_color(self, rgb_sample):
        # normalize color components in [0, 1] and in the white-black range
        rgb_sample = [float(s) for s in rgb_sample]
        comps = [max((s - b) / (w - b), 0)
                 for w, b, s in zip(
                self._color_detector_reference_levels['w'],
                self._color_detector_reference_levels['b'],
                rgb_sample
            )]

        sum_comps = sum(comps)
        if sum_comps > 0:
            decomp = [c / sum_comps for c in comps]
        else:
            decomp = [0] * 3

        min_comps, max_comps = min(comps), max(comps)

        if min_comps > 0.9:
            color = self.COLOR_WHITE
        elif max_comps < 0.2:
            color = self.COLOR_BLACK
        else:
            over_50 = [c > 0.5 for c in decomp]
            if any(over_50):
                color = over_50.index(True) + 1
            else:
                color = self.COLOR_UNDEF

        return color, decomp
