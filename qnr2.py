import os
import sys
from subprocess import Popen,PIPE,call
import struct
import argparse 
import qn


opt_forcenew  = ('forcenew', 'Alt+Return', 'Force Create New Note')
opt_delete    = ('delete', 'Alt+r', 'Delete Note')
opt_rename    = ('rename', 'Alt+space', 'Rename Note')
opt_addtag    = ('addtag', 'Alt+n', 'Add Tag to Note')
opt_grep      = ('grep', 'Alt+s', 'Grep Notes')
opt_showtrash = ('showtrash', 'Alt+t', 'Show Trash')
opt_showtagb  = ('showtagb', 'Alt+i', 'Show Note Tags')
opt_showtagm  = ('showtagm', 'Alt+u', 'Filter By Tags')
opt_showhelp  = ('showhelp', 'Alt+h', 'Show Help')
opt_sortname  = ('sortname', 'Alt+1', 'Sort By Name')
opt_sortcdate = ('sortcdate', 'Alt+2', 'Sort by Creation Date')
opt_sortmdate = ('sortmdate', 'Alt+3', 'Sort by Modificatin Date')
opt_sortsize  = ('sortsize', 'Alt+4', 'Sort by Size')

COLS = 1
INTERACTIVE = False

rofi_base_command = ['rofi', '-dmenu', '-i', '-width', '50', '-lines', '15'
                     , '-p', 'qn:', '-kb-custom-1', 'Alt+Shift+1'
                     , '-kb-custom-1', 'Alt+Shift+1' #remove previous bindings
                     , '-kb-custom-2', 'Alt+Shift+2' #remove previous bindings
                     , '-kb-custom-3', 'Alt+Shift+3' #remove previous bindings
                     , '-kb-custom-4', 'Alt+Shift+4' #remove previous bindings
                     ]

default_help_string = 'Press "' + opt_showhelp[1] + '" to see a list of hotkeys.'
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

    def get_opt(self, val):
        for key in self.keys:
            if val == key['keyval']:
                return(key['optname'])

        print("No keybinding set to -kb-custom-" + str(val-9) + ".")
        return(None)

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


    file_repo = qn.file_repo(qn.QNDIR)
    file_repo.scan_files()
    file_repo.sort(qn_options['sortby'], qn_options['sortrev'])
    file_name_list = file_repo.filenames()
    file_path_list = file_repo.filepaths()

    MESG = qn_options['help'] + ' Sorted by: ' + qn_options['sortby']
    if qn_options['sortrev']:
        MESG += ' [v]'
    else:
        MESG += ' [^]'

    rofi_command = rofi_base_command.copy()
    rofi_command += ['-mesg', MESG]
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

    if val == 0:
        if SEL.strip():
            path=os.path.join(qn.QNDIR, SEL)
            if os.path.isfile(path):
                print("File found, edit...")
                qn.open_note(SEL, INTERACTIVE)
            else:
                print("File not found, creating...")
                qn.new_note(SEL, INTERACTIVE)
        print('Open Note')
        return(1)

    opt_sel = default_hotkeys.get_opt(val)

    if not opt_sel:
        show_default_rofi(qn_options)

    if opt_sel == 'delete':
        show_delete_rofi(SEL)
    elif opt_sel == 'rename':
        show_rename_rofi(SEL)
    elif opt_sel == 'showtrash':
        show_trash_rofi(qn_options)
    elif opt_sel == 'forcenew':
        if not FILTER.strip():
            sys.exit(0)
        qn.force_new_note(FILTER,INTERACTIVE)
    elif opt_sel == 'grep':
        show_filtered_rofi(file_repo, FILTER, qn_options)
    elif opt_sel == 'addtag':
        print('Add Tag to Note')
    elif opt_sel == 'showtagb':
        print('Browse Tags')
    elif opt_sel == 'showtagm':
        print('Show Note Tags')
    elif opt_sel == 'showhelp':
        show_help_rofi(default_hotkeys, qn_options, 'Open Note')
    elif opt_sel == 'sortname':
        show_sorted_default_rofi(qn_options, 'name', True)
    elif opt_sel == 'sortcdate':
        show_sorted_default_rofi(qn_options, 'cdate')
    elif opt_sel == 'sortmdate':
        show_sorted_default_rofi(qn_options, 'mdate')
    elif opt_sel == 'sortsize':
        show_sorted_default_rofi(qn_options, 'size')


def show_sorted_default_rofi(qn_options, sortby, default_sortrev=False):
    if qn_options['sortby'] == sortby:
        qn_options['sortrev'] = not qn_options['sortrev']
    else:
        qn_options['sortrev'] = default_sortrev
    qn_options['sortby'] = sortby
    show_default_rofi(qn_options)


def show_yesno_rofi(HELP_MSG):


    HELP = "<span color=\"red\">"
    HELP += HELP_MSG
    HELP += "</span>"
    rofi_command = rofi_base_command.copy() + ['-mesg', HELP, '-columns', '1']
    SEL, val = call_rofi(rofi_command, ['no', 'yes'])
    if SEL:
        return(SEL == 'yes')
    else:
        sys.exit(1)

def show_delete_rofi(note):


    HELP_MSG = "Are you sure you want to delete \"" + note + "\"?"
    if show_yesno_rofi(HELP_MSG):
        print("Deleting " + note)
        qn.delete_note(note)
    else:
        print("Deletion of \"" + note + "\" cancelled.")


def show_undelete_rofi(note):


    HELP = "Are you sure you want to restore \"" + note + "\"?"
    if show_yesno_rofi(HELP):
        print("Restoring " + note)
        qn.undelete_note(note)
    else:
        print("Not Restoring " + note)


def show_rename_rofi(note):


    HELP = "Please write the new name for this file"
    rofi_command = rofi_base_command.copy() + ['-mesg', HELP, '-columns', '1',
                    '-p', 'qn', 'rename', '-filter', note]
    SEL, val = call_rofi(rofi_command, [''])
    if (SEL == None):
        sys.exit(1)

    YESNO_MSG = "Are you sure you want to rename '" + note.strip()
    YESNO_MSG += "' to '" + SEL.strip() + "'?"
    if show_yesno_rofi(YESNO_MSG):
        qn.move_note(note.strip(), SEL.strip(), move_tags=True)
    else:
        pritn("Doing Nothing.")



def show_trash_rofi(qn_options):


    HELP = 'Press enter to restore file, "' 
    HELP += opt_showtrash[1] + '" to go back to qn.'
    trash_repo = qn.file_repo(qn.QNTRASH)
    trash_repo.scan_files()
    trash_files = trash_repo.filenames()

    trash_hotkeys = hotkeys()
    trash_hotkeys.add_key(*opt_showtrash)
    hotkey_args = trash_hotkeys.generate_hotkey_args()

    rofi_command = rofi_base_command.copy() + ['-mesg', HELP]
    SEL,val = call_rofi(rofi_command, trash_files, hotkey_args)
    if (SEL == None):
        sys.exit(1)

    if val == 0:
        show_undelete_rofi(SEL)

    opt_sel = trash_hotkeys.get_opt(val)

    if not opt_sel:
        show_trash_rofi(qn_options)

    if opt_sel == 'showtrash':
        show_default_rofi(qn_options)


def show_help_rofi(keybindings, qn_options, enterkey_help=None):


    HELP = "qnr Keybindings."
    rofi_command = rofi_base_command + ['-mesg', HELP, '-columns', '1'
                        ,'-format', 's']
    help_padding = 35

    help_lines = [] 
    if enterkey_help:
        helpl1 = enterkey_help + ":"
        helpl1 = helpl1.ljust(help_padding)
        helpl1 += 'Enter'
        help_lines.append(helpl1)
    for key in keybindings.keys:
        helpl = key['keyhelp'] + ":"
        helpl = helpl.ljust(help_padding)
        helpl += key['keybinding']
        help_lines.append(helpl)


    call_rofi(rofi_command, help_lines)

    show_default_rofi(qn_options)


def show_filtered_rofi(filerepo, FILTER, qn_options):


    HELP = "List of notes filtered for '" + FILTER + "'."
    rofi_command = rofi_base_command + ['-p', 'qn search:', '-mesg', HELP
                                        , '-columns', '1', '-format', 'i']

    filters = FILTER.strip().split(" ")
    filtered_repo = filerepo
    for f in filters:
        filtered_repo = filerepo.grepfiles(f)

    filtered_files = filtered_repo.filenames()

    filtered_hotkeys = hotkeys()
    hotkey_args = filtered_hotkeys.generate_hotkey_args()

    rofi_command = rofi_base_command.copy() + ['-mesg', HELP]
    SEL,val = call_rofi(rofi_command, filtered_files, hotkey_args)

    if (SEL == None):
        sys.exit(1)

    if val == 0:
        if SEL.strip():
            path=os.path.join(qn.QNDIR, SEL)
            if os.path.isfile(path):
                print("File found, edit...")
                qn.open_note(SEL, INTERACTIVE)
            else:
                print("File not found, creating...")
                qn.new_note(SEL, INTERACTIVE)
        print('Open Note')
        return(1)


    opt_sel = trash_hotkeys.get_opt(val)

    if not opt_sel:
        show_trash_rofi(qn_options)

    if opt_sel == 'showtrash':
        show_default_rofi(qn_options)



if __name__ == '__main__':
    qn.check_environment(True)
    show_default_rofi(default_qn_options)

    #print(len(gfilerepo2.file_list))
