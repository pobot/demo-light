#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import print_function
import sys
import argparse

def print_err(msg, *args):
    '''Prints a message on stderr, prefixing it by [ERROR].
    
    Arguments:
        msg:    
            the message to be printed, which can be a format string
            using the string.format specification
        args:   
            optional values passed to the format method
    '''
    print(("[ERROR] " + str(msg)).format(*args), file=sys.stderr)

def die(*args):
    ''' Prints an error message on stderr and abors execution with return code
    set to 2.
    '''
    print_err(*args)
    sys.exit(2)

def add_argparse_general_options(parser):
    ''' Adds common general options.

    Added options are:
        - verbose
        - debug mode

    Arguments:
        parser:
            the parser being defined
    '''
    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
            help='verbose output')
    parser.add_argument('-D', '--debug', dest='debug', action='store_true',
            help='activates debug mode')

def get_argument_parser(**kwargs):
    ''' Returns a command line parser initialized with common settings.

    Settings used : 
    - general options as defined by add_argparse_general_options

    The parser is also set for displaying default values in help
    '''
    parser = argparse.ArgumentParser(
                formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                **kwargs
                )
    add_argparse_general_options(parser)
    return parser
