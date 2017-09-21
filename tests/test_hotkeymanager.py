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

from qn import hotkey_manager


qnhk = hotkey_manager.HotkeyManager()
qnhk.add_key('run', 'alt-r', 'run a command')
qnhk.add_key('open', 'alt-o')
print("* self.__keys")
print(qnhk.keys)
print("-------")
print("* self.__app")
print(qnhk.launcher)
print("-------")
print("* get_opt 28")
print(qnhk.get_opt(28))
print("-------")
print("* get_keybinding 'run'")
print(qnhk.get_keybinding('run'))
print("-------")
print("* generate_hotkey_args --default is for rofi")
print(qnhk.generate_hotkey_args())
print("-------")
print("* generate_help")
print(qnhk.generate_help())
