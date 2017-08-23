#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import qng
import qn
import qng
import config_parse

if __name__ == "__main__":
    qnoptions = config_parse.QnOptions(app='rofi', run_parse_config=True)
    qnoptions.check_environment()
    #qnoptions.print_options()

    qnrf = qng.QnAppRF(qnoptions)
    qnrf.show_default()

