import qng
import qn
import qng
import config_parse

qnoptions = config_parse.QnOptions(app='rofi', run_parse_config=True)
qnoptions.check_environment()

qnrf = qng.QnAppRF(qnoptions)
qnrf.show_default()

