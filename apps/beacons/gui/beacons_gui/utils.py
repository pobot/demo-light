#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os.path

RES_DIR = 'res'

def make_resource_path(resname):
    return os.path.join(RES_DIR, resname)

class Point(object):
    def __init__(self, *args):
        if len(args) == 1:
            if type(args[0]) is Point:
                self.x, self.y = args[0].xy
            else:
                self.x, self.y = args[0]
        else:
            self.x, self.y = args[0], args[1]

    def move(self, dx, dy=None):
        if dy == None:
            dy = dx
        self.x += dx
        self.y += dy
        return self

    def scale(self, sx, sy=None):
        if sy == None:
            sy = sx
        self.x *= sx
        self.y *= sy
        return self

    @property
    def xy(self):
        return (self.x, self.y)

    def __str__(self):
        return str(self.xy)

    def __repr__(self):
        return str(self)
