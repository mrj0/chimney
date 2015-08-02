#!/usr/bin/env python
# -*- coding: utf-8 -*-
import codecs
from setuptools import setup
import os


def read_file(name):
    return codecs.open(os.path.join(os.path.dirname(__file__), name), encoding='utf-8').read()


setup(
    author='Mike Johnson',
    author_email='mike@mrj0.com',
    name='chimney',
    description='Compile web assets',
    long_description=read_file('README.md'),
    version='0.4',
    url='https://github.com/mrj0/chimney/',
    license='GPL',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
    ],
    packages=['chimney'],
    install_requires=['six>=1.3', 'futures', 'watchdog', 'path.py'],
)
