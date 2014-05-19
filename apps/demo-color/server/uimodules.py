#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import namedtuple
import datetime
import os.path
from operator import itemgetter

from tornado.web import UIModule

from pjc.tournament import Tournament


__author__ = 'eric'


class UIModuleBase(UIModule):
    """ Base class for tournament UI modules implementation.

    Shares the rendering process common operations so that concrete module implementations
    have no boiler plate code to repeat over and over.
    """
    TEMPLATE_DIRECTORY = "uimodules"

    @property
    def template_name(self):
        """ Returns the name (without extension and path) of the body template.

        To be overridden by subclasses.
        """
        raise NotImplementedError()

    def get_template_args(self, application, **kwargs):
        """ Returns the keyword arguments to be passed to the body template as a dictionary.

        :rtype: dict
        """
        return {}

    def make_template_path(self):
        name = self.template_name
        if not name.endswith('.html'):
            name += '.html'
        return os.path.join(self.TEMPLATE_DIRECTORY, name)

    def render(self, application, *args, **kwargs):
        return self.render_string(
            self.make_template_path(),
            **self.get_template_args(application, *args, **kwargs)
        )


class DemoPageTitle(UIModuleBase):
    @property
    def template_name(self):
        return "demo_page_title"

    def render(self, title):
        return self.render_string(
            self.make_template_path(),
            title=title
        )


class FormButtons(UIModuleBase):
    @property
    def template_name(self):
        return "form_buttons"

    def render(self, *args):
        return self.render_string(
            self.make_template_path()
        )


class CalibrationStep(UIModuleBase):
    @property
    def template_name(self):
        return "calibration_step"

    def render(self, step_id, step_label):
        return self.render_string(
            self.make_template_path(),
            step_id=step_id,
            step_label=step_label
        )


class CalibrationButton(UIModuleBase):
    @property
    def template_name(self):
        return "calibration_button"

    def render(self):
        return self.render_string(
            self.make_template_path()
        )
