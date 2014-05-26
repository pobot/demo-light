#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = 'Eric Pascual'

from tornado.web import RequestHandler
import os

class UIHandler(RequestHandler):
    def get_template_args(self):
        return {
            'app_title':"Capteurs de lumière et de couleur"
        }

    def get(self, *args, **kwargs):
        """ By default, the get method displays the "Not yet implemented message".
        """
        self.render(
            os.path.join(self.application.template_home, "nyi.html"),
            **self.get_template_args()
        )


class UIHome(UIHandler):
    def get(self, *args, **kwargs):
        self.render(
            os.path.join(self.application.template_home, "home.html"),
            **self.get_template_args()
        )


class UIHBarrier(UIHandler):
    def get(self, *args, **kwargs):
        template_args = self.get_template_args()
        template_args['demo_title'] = "Barrière optique"

        self.render(
            os.path.join(self.application.template_home, "barrier.html"),
            **template_args
        )


class UIWBDetector(UIHandler):
    def get(self, *args, **kwargs):
        template_args = self.get_template_args()
        template_args['demo_title'] = "Détecteur noir/blanc"

        self.render(
            os.path.join(self.application.template_home, "bwdetector.html"),
            **template_args
        )


class UIColorDetector(UIHandler):
    pass


class UICalibration(UIHandler):
    def get(self, *args, **kwargs):
        self.render(
            os.path.join(self.application.template_home, "calibration.html"),
            **self.get_template_args()
        )


