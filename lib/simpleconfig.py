#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" A simple parser for simple configuration of parameters files."""

import os

__author__ = "Eric Pascual"
__email__ = "eric@pobot.org"
__copyright__ = "Copyright 2013, POBOT"
__version__ = "1.0"
__date__ = "July. 2013"
__status__ = "Development"
__license__ = "LGPL"

def parse(files, defaults=None, sep=':'):
    """ Parse a list of files containing key/value pairs, and returns the loaded data as
    a dictionary.

    Parameters:
        files:
            the list of file paths which are loaded in turn, each one overriding previously
            read vales. '~' symbol is expanded using the usual rules
        defaults:
            a dictionary providing default values for missing parameters
            default: none
        sep:
            the character used to split the key and the value part of a parameter record
            default: ':'

    Returns:
        a dictionary containing the values read for the provided file(s), augmented by the
        provided defaults if any

    Raises:
        ValueError if a record of the parsed files does not conform to the expected syntax
    """

    cfg = defaults if defaults else {}

    for path in [p for p in [os.path.expanduser(p) for p in files] if os.path.exists(p)]:
        with open(path, 'r') as f:
            for line in [l for l in [l.strip() for l in f.readlines()] if not l.startswith('#')]:
                parts = line.split(sep, 1)
                if len(parts) == 2:
                    key, value = parts
                    cfg[key.strip()] = value.strip()
                else:
                    raise ValueError('invalid key/value record (%s)' % line)

    return cfg



