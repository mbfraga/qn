#!/usr/bin/env python3

from setuptools import setup
from os import geteuid

data_files = []
if geteuid() == 0:
    data_files.append(('/etc/qn', ['config.example']))

setup(name='qn',
      version='0.1',
      description='Quick note manager with fzf/rofi interfaces.',
      author='mbfraga',
      author_email='mbfraga@gmail.com',
      url='https://www.github.com/mbfraga/qn/',
      packages=['qn'],
      scripts=['bin/qnr', 'bin/qnf'],
      data_files=data_files,
      install_requires=['configargparse'],
      )
