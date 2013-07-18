#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A couple of convenience settings and functions for using the logging facility
in a homogeneous way accross applications."""

import logging

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "June. 2013"
__status__ = "Development"
__license__ = "LGPL"

logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s.%(msecs).3d [%(levelname).1s] %(name)s > %(message)s',
        datefmt='%H:%M:%S'
        )

def getLogger(name, name_width=15):
    logger = logging.getLogger(name.ljust(name_width)[:name_width])
    logger.addHandler(logging.NullHandler())
    return logger

