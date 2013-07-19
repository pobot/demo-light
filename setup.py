#!/usr/bin/env python
# -*- coding: utf-8 -*-

from distutils.core import setup
import glob

setup(name='pybot',
      version='1.0',
      description='A collection of packages and modules for robotics and RasPi',
      long_description="""
      This collection of packages and modules are primarly intended for developping
      robotics systems with Python on a Raspberry PI.

      It contains interfacing modules with various kind of hardwares.

      Even if developped with the RasPi in mind, some of the modules can be used in
      other environments.

      In any case, most of the 'leaf' features are independant, and you can tailor the
      library by removing stuff you don't need, which are most of the time organized as
      sub-packages.
      """,
      author='Eric Pascual',
      author_email='eric@pobot.org',
      url='http://www.pobot.org',
      download_url='https://github.com/Pobot/PyBot',
      packages=[
          'pybot',
          'pybot.abelectronics',
          'pybot.irobot',
          'pybot.dbus',
          'pybot.dmxl',
          'pybot.dspin'
      ],
      scripts= \
        glob.glob('./bin/*.py') + \
        glob.glob('./demo/*.py')
      )
