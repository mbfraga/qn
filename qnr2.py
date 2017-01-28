import os
import sys
from subprocess import Popen,PIPE,call
import struct
import argparse 
import qn


opt_forcenew  = ('forcenew', 'Alt+Return')
opt_delete    = ('delete', 'Alt+r')
opt_rename    = ('rename', 'Alt+space')
opt_addtag    = ('addtag', 'Alt+n')
opt_grep      = ('grep', 'Alt+s')
opt_showtrash = ('showtrash', 'Alt+t')
opt_showtagb  = ('showtagb', 'Alt+i')
opt_showtagm  = ('showtagm', 'Alt+u')
opt_showhelp  = ('showhelp', 'Alt+h')
opt_sortname  = ('sortname', 'Alt+1')
opt_sortcdate = ('sortcdate', 'Alt+2')
opt_sortmdate = ('sortmdate', 'Alt+3')
opt_sortsize  = ('sortsize', 'Alt+4')

opt_show_help = 'Alt+h'
COLS = 1

rofi_base_command = ['rofi', '-dmenu', '-i', '-width', '50', '-lines', '15', '-p', 'qn:']

default_help_string = 'Press "' + opt_show_help + '" to see a list of hotkeys.'
default_qn_options = {}
default_qn_options['title'] = 'qn:'
default_qn_options['help'] = default_help_string
default_qn_options['position'] = None
default_qn_options['filter'] = None
default_qn_options['sortby'] = qn.SORTBY
default_qn_options['sortrev'] = qn.SORTREV

class hotkeys:
    def __init__(self):
        self.keys = []
        self.hotkey_ct = 19

    def add_key(self, optname, keybinding, keyhelp=''):
        if self.hotkey_ct < 1:
            print('Too many keybindings. Key not added')
            return
        keyprops = {}
        keyprops['optname'] = optname
        keyprops['keybinding'] = keybinding
        keyprops['keyhelp'] = keyhelp
        keyprops['keyval'] = self.hotkey_ct+9
        self.keys.append(keyprops)
        self.hotkey_ct -= 1

    def generate_hotkey_args(self):
        hotkey_args = []
        for key in self.keys:
            arg_string = '-kb-custom-' + str(key['keyval']-9)
            hotkey_args.extend([arg_string, key['keybinding']])

        return(hotkey_args)


# call_rofi code borrowed from
def call_rofi(rofi_command, entries, additional_args=[]):


    additional_args.extend([ '-sep', '\\0',
                             '-columns', str(COLS),
                             ])

    proc = Popen(rofi_command + additional_args, stdin=PIPE, stdout=PIPE)
    for e in entries:
        proc.stdin.write((e).encode('utf-8'))
        proc.stdin.write(struct.pack('B', 0))
    proc.stdin.close()
    answer = proc.stdout.read().decode("utf-8") 
    exit_code = proc.wait()

    # trim whitespace
    if answer == '':
        return(None, exit_code)
    else:
        return(answer.strip('\n'), exit_code)


def show_default_rofi(qn_options):


    print(qn_options)
    file_repo = qn.file_repo(qn.QNDIR)
    default_hotkeys = hotkeys()
    default_hotkeys.add_key(*opt_delete)
    default_hotkeys.add_key(*opt_showtrash)
    default_hotkeys.add_key(*opt_rename)
    default_hotkeys.add_key(*opt_grep)
    default_hotkeys.add_key(*opt_forcenew)
    default_hotkeys.add_key(*opt_showtagm)
    default_hotkeys.add_key(*opt_showtagb)
    default_hotkeys.add_key(*opt_addtag)
    default_hotkeys.add_key(*opt_showhelp)
    default_hotkeys.add_key(*opt_sortname)
    default_hotkeys.add_key(*opt_sortcdate)
    default_hotkeys.add_key(*opt_sortmdate)
    default_hotkeys.add_key(*opt_sortsize)

    hotkey_args = default_hotkeys.generate_hotkey_args()
    print(hotkey_args)

    file_name_list = file_repo.filenames()
    file_path_list = file_repo.filepaths()

    rofi_command = rofi_base_command
    rofi_command += ['-mesg', qn_options['help']]
    rofi_command += ['-format', 'f;s;i']
    rofi_command += ['-p', qn_options['title']]

    if qn_options['filter']:
        rofi_command += ['-filter', qn_options['filter']]
    if qn_options['position']:
        rofi_command += ['-selected-row', qn_options['position']]

    SELFSI,val = call_rofi(rofi_command, file_name_list, hotkey_args)
    if (SELFSI == None):
        sys.exit(1)
    FILTER,SEL,POS = SELFSI.split(';')
    print('sel:' + SEL + ' | val:' + str(val))

    if FILTER:
        qn_options['filter'] = FILTER
    if POS:
        qn_options['position'] = POS

    print(itemgetter(gg 




if __name__ == '__main__':
    qn.check_environment(True)
    show_default_rofi(default_qn_options)
