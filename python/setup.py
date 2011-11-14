#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# License info goes here
#
# Author: John Hampton <pacopablo@pacopablo.com>

from setuptools import setup

setup(
    name='youtrack',
    version='3.0.4',
    packages=['youtrack',],
    author='Jet Brains',
    description='YouTrack Client Library',
# TODO: figure out how best to package the various migration scripts
#    scripts=['scripts/'],
    url='http://confluence.jetbrains.net/display/YTD3/Python+Client+Library',
    license='???',
    zip_safe = False,
    install_requires = ['Requests',],
)

