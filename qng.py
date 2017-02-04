import os
import sys
from subprocess import Popen,PIPE, call
import struct

import qn
import hotkey_manager as hk


COLS = 1



def call_command(qn_options, entries, additional_args=[]):


    proc = Popen(qn_options['command'] + additional_args, stdin=PIPE, stdout=PIPE)
    for e in entries:
        proc.stdin.write((e).encode('utf-8'))
        proc.stdin.write(struct.pack('B', 0))
    proc.stdin.close()
    answer = proc.stdout.read().decode("utf-8") 
    exit_code = proc.wait()

    if answer == '':
        return(None, exit_code)

    if qn_options['app'] == 'fzf':
        answer = answer.split('\x00')
    else:
        answer = answer.strip('\n').split(';')

    return(answer, exit_code)


def show_default(qn_options):

    appname = qn_options['app']

    #Load Hotkeys
    hkman = hk.HotkeyManager(app=qn_options['app'])
    hkman.add_key(*qn_options['hotkeys']['forcenew'])
    hkman.add_key(*qn_options['hotkeys']['delete'])
    hkman.add_key(*qn_options['hotkeys']['rename'])
    hkman.add_key(*qn_options['hotkeys']['addtag'])
    hkman.add_key(*qn_options['hotkeys']['grep'])
    hkman.add_key(*qn_options['hotkeys']['showtrash'])
    hkman.add_key(*qn_options['hotkeys']['showtagb'])
    hkman.add_key(*qn_options['hotkeys']['showtagm'])
    hkman.add_key(*qn_options['hotkeys']['showhelp'])
    hkman.add_key(*qn_options['hotkeys']['sortname'])
    hkman.add_key(*qn_options['hotkeys']['sortcdate'])
    hkman.add_key(*qn_options['hotkeys']['sortmdate'])
    hkman.add_key(*qn_options['hotkeys']['sortsize'])

    hotkey_args = hkman.generate_hotkey_args()

    file_repo = qn.FileRepo(qn.QNDIR)
    file_repo.scan_files()
    file_repo.sort(qn_options['sortby'], qn_options['sortrev'])

    if appname == 'rofi':
        applist = file_repo.lines()
    else:
        applist = file_repo.filenames()

    MESG = 'Press "'  + qn_options['hotkeys']['showhelp'][1]
    MESG += '" to see a list of hotkeys.'
    MESG += qn_options['help'] + ' Sorted by: ' + qn_options['sortby']
    if qn_options['sortrev']:
        MESG += ' [v]'
    else:
        MESG += ' [^]'

    extra_args = qn.gen_instance_args(qn_options, 'default', alt_help=MESG)
    extra_args.extend(hotkey_args)

    answer,exit_code = call_command(qn_options, applist, extra_args)

    if not answer:
        return(0)

    if appname == 'rofi':
        if answer[0].strip():
            FILTER = answer[0]
        else:
            FILTER = None
        POS = int(answer[2])
        if POS == -1:
            NOTE = None
        else:
            NOTE = file_repo.file_list[POS]['name'].strip()
        if exit_code == 0:
            KEY = None
        else:
            KEY = True
        OPTSEL = hkman.get_opt(exit_code)

    elif appname == 'fzf':
        if not answer:
            return(0)
        if len(answer) < 4:
            FILTER, KEY, MISC = answer[0:3]
            NOTE = None
        else:
            FILTER, KEY, NOTE, MISC = answer
            NOTE = NOTE.strip()
        FILTER = FILTER.strip()
        KEY = KEY.strip()
        if not FILTER:
            FILTER = None
        if KEY:
            OPTSEL = hkman.get_opt(KEY)
        else:
            OPTSEL = None
        POS = None

    print('FILTER: ' , FILTER)
    print('NOTE: ' , NOTE)
    print('POS: ' , POS)
    print('OPTSEL: ' , OPTSEL)


    if not OPTSEL:
        if not NOTE:
            print("Creating file from filter...")
            qn.new_note(FILTER, qn_options['interactive'])
            return(0)
        else:
            path=os.path.join(qn.QNDIR, NOTE)
            if os.path.isfile(path):
                print("file found, editing...")
                qn.open_note(NOTE, qn_options['interactive'])
                return(0)
            else:
                print("file not found, create...")
                qn.new_note(FILTER, qn_options['interactive'])
                return(0)
        show_default(qn_options)

#    if OPTSEL == 'delete':
#        show_delete_rofi(SEL)
#    elif OPTSEL == 'rename':
#        show_rename_rofi(SEL)
#    elif OPTSEL == 'showtrash':
#        show_trash_rofi(qn_options)
#    elif OPTSEL == 'forcenew':
#        if not FILTER.strip():
#            sys.exit(0)
#        qn.force_new_note(FILTER,INTERACTIVE)
#    elif OPTSEL == 'grep':
#        show_filtered_rofi(file_repo, FILTER, qn_options)
#    elif OPTSEL == 'addtag':
#        print('Add Tag to Note')
#    elif OPTSEL == 'showtagb':
#        print('Browse Tags')
#    elif OPTSEL == 'showtagm':
#        print('Show Note Tags')
#    elif OPTSEL == 'showhelp':
#        show_help_rofi(default_hotkeys, qn_options, 'Open Note')
    if OPTSEL == 'sortname':
        show_sorted_default(qn_options, 'name', True)
    elif OPTSEL == 'sortcdate':
        show_sorted_default(qn_options, 'cdate')
    elif OPTSEL == 'sortmdate':
        show_sorted_default(qn_options, 'mdate')
    elif OPTSEL == 'sortsize':
        show_sorted_default(qn_options, 'size')


def show_sorted_default(qn_options, sortby, default_sortrev=False):
    if qn_options['sortby'] == sortby:
        qn_options['sortrev'] = not qn_options['sortrev']
    else:
        qn_options['sortrev'] = default_sortrev
    qn_options['sortby'] = sortby
    show_default(qn_options)



def show_trash(app, qn_options):


    HELP = 'Press enter to restore file."'
    trash_repo = qn.FileRepo(qn.QNTRASH)
    trash_repo.scan_files()
    applist = trash_repo.filenames()


if __name__ == '__main__':
    qn.check_environment(True)

    options = qn.generate_options('fzf')
#    options = qn.generate_options('rofi')
    show_default(options)

