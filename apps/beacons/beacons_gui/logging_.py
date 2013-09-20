#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Shared logging settings."""

import logging

def setup_logging():
    logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s.%(msecs).3d [%(levelname).1s] %(name)-15.15s > %(message)s',
            datefmt='%H:%M:%S'
            )

