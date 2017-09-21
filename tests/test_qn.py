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
from qn import qn

qno = config_parser.QnOptions(qndir='qntest', run_parse_config=False)
qno.check_environment()
qno.set_interactive(False)
q = qn.QnApp(qno)
q.options.set_terminal('st')
q.add_repo()
q.file_repo().scan_files()
q.list_notes()
print(q.options.command)
