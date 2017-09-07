#!/usr/bin/env python3
# -*- Mode: Python; coding: utf-8; indent-tabs-mode: nil; tab-width: 4 -*-

import os
import sys
import locale
from os.path import realpath, dirname, normpath

LAUNCH_PATH = dirname(realpath(__file__))
if LAUNCH_PATH != "/usr/bin":
    sys.dont_write_bytecode = True
    SOURCE_PATH = normpath(os.path.join(LAUNCH_PATH, '..'))
    sys.path.insert(0, SOURCE_PATH)

locale.setlocale(locale.LC_ALL, locale.getlocale())

from qn import config_parser

qno = config_parser.QnOptions()
print('* prompt change')
print(qno.prompt)
qno.set_prompt('test prompt')
print(qno.prompt)
print('---------------')

print('* set_help')
print(qno.help)
qno.set_help('test help')
print(qno.help)
print('---------------')

print('* set_selected_row')
print(qno.selected_row)
qno.set_selected_row('6')
print(qno.selected_row)
print('---------------')


print('* set_filter')
print(qno.filter)
qno.set_filter('test filter')
print(qno.filter)
print('---------------')


print('* set_sortby')
print(qno.sortby)
qno.set_sortby('date')
print(qno.sortby)
print('---------------')

print('* set_sortrev')
print(qno.sortrev)
qno.set_sortrev('True')
print(qno.sortrev)
print('---------------')

print('* set_interactive')
print(qno.interactive)
qno.set_interactive('True')
print(qno.interactive)
print('---------------')

print('* print_options')
qno.print_options()
print('---------------')
