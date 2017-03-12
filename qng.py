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


def show_note_select(qn_options, file_repo, additional_args=[]
                     , hk_manager=None):


    appname = qn_options['app']
    if appname == 'rofi':
        applist = file_repo.lines()
    elif appname == 'fzf':
        applist = file_repo.filenames()

    else:
        return(False)

    proc = Popen(qn_options['command'] + additional_args, stdin=PIPE
                 , stdout=PIPE)
    for e in applist:
        proc.stdin.write((e).encode('utf-8'))
        proc.stdin.write(struct.pack('B', 0))
    proc.stdin.close()
    answer = proc.stdout.read().decode("utf-8") 
    exit_code = proc.wait()

    if answer == '':
        return(False)

    if appname == 'rofi':
        answer = answer.strip('\n').split(';')
        if not answer:
            return(False)
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
            OPTSEL = None
        else:
            KEY = True
            if hk_manager:
                OPTSEL = hk_manager.get_opt(exit_code)
    elif appname == 'fzf':
        answer = answer.split('\x00')
        if not answer:
            return(False)
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
            if hk_manager:
               OPTSEL = hk_manager.get_opt(KEY)
            else:
               OPTSEL = None
        else:
            OPTSEL = None
        POS = None
    else:
        print('Appname "' + appname + '"not implemented.')
        return(False)

    return(NOTE, FILTER, OPTSEL)


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

    MESG = 'Press "'  + qn_options['hotkeys']['showhelp'][1]
    MESG += '" to see a list of hotkeys.'
    MESG += qn_options['help'] + ' Sorted by: ' + qn_options['sortby']
    if qn_options['sortrev']:
        MESG += ' [v]'
    else:
        MESG += ' [^]'

    extra_args = qn.gen_instance_args(qn_options, 'default', alt_help=MESG)
    extra_args.extend(hotkey_args)

    ANSWER = show_note_select(qn_options, file_repo, extra_args
                                            , hkman)
    if not ANSWER:
        return(0)

    print(ANSWER)
    NOTE, FILTER, OPTSEL = ANSWER


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


    if OPTSEL == 'delete':
        show_delete(qn_options, NOTE)
    elif OPTSEL == 'rename':
        show_rename(qn_options, NOTE)
    elif OPTSEL == 'showtrash':
        show_trash(qn_options)
    elif OPTSEL == 'forcenew':
        if not FILTER.strip():
            sys.exit(0)
        qn.force_new_note(FILTER,qn_options['interactive'])
    elif OPTSEL == 'grep':
        if not FILTER:
            show_default(qn_options)
        else:
            show_filtered(qn_options, file_repo, FILTER)
#    elif OPTSEL == 'addtag':
#        print('Add Tag to Note')
#    elif OPTSEL == 'showtagb':
#        print('Browse Tags')
#    elif OPTSEL == 'showtagm':
#        print('Show Note Tags')
    elif OPTSEL == 'showhelp':
        show_help(qn_options, hkman, enter_help="Create/Edit note")
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


def show_yesno(qn_options, MESG, TITLE='qn dialog: '):

    HELP = "<span color=\"red\">"
    HELP += MESG
    HELP += "</span>"
    appname = qn_options['app']

    extra_args = qn.gen_instance_args(qn_options, 'default'
                                    , alt_help=MESG, alt_title=TITLE)
    ANS, val = call_command(qn_options, ['no', 'yes'], extra_args)

    if not ANS:
        sys.exit(0)

    if appname == 'rofi':
        return(ANS[1] == 'yes')
    elif appname == 'fzf':
        return(ANS[2] == 'yes')
    else:
        print("App " + appname + " not implemented.")
        return(False)


def show_undelete(qn_options, note):


    MESG = "Are you sure you want to restore \"" + note + "\"?"
    if show_yesno(qn_options, MESG, 'qn undelete:'):
        print("Restoring " + note + "...")
        qn.undelete_note(note)
    else:
        print("Restoration of \"" + note + "\" cancelled.")


def show_delete(qn_options, note):


    MESG = "Are you sure you want to delete \"" + note + "\"?"

    if show_yesno(qn_options, MESG, 'qn delete:'):
        print("Deleting " + note + "...")
        qn.delete_note(note)
    else:
        print("Deletion of \"" + note + "\" cancelled.")


def show_rename(qn_options, note):


    MESG = "Please write the new name for this file"

    extra_args = qn.gen_instance_args(qn_options, 'default'
                            , alt_help=MESG, alt_title="qn rename: ")
    if qn_options['app'] == 'rofi':
        extra_args.extend(['-filter', note])
    elif qn_options['app'] == 'fzf':
        extra_args.extend(['--query', note])

    ANS, val = call_command(qn_options, [''], extra_args)

    if (ANS == None):
        sys.exit(1)

    print(ANS)

    YESNO_MSG = "Are you sure you want to rename '" + note.strip()
    YESNO_MSG += "' to '" + ANS[0].strip() + "'?"
    if show_yesno(qn_options, YESNO_MSG, 'qn rename: '):
        qn.move_note(note.strip(), ANS[0].strip(), move_tags=True)
    else:
        print("Doing Nothing.")
        sys.exit(0)


def show_trash(qn_options):


    hkman = hk.HotkeyManager(qn_options['app'])
    hkman.add_key(*qn_options['hotkeys']['showtrash'])
    hkman.add_key(*qn_options['hotkeys']['showhelp'])
    hotkey_args = hkman.generate_hotkey_args()

    MESG = 'Press enter to restore file. "'
    MESG += hkman.get_keybinding('showtrash') + '" to go back to qn.'
    trash_repo = qn.FileRepo(qn.QNTRASH)
    trash_repo.scan_files()
    trash_repo.sort('cdate')
    applist = trash_repo.filenames()

    extra_args = qn.gen_instance_args(qn_options, 'default'
                                    , alt_help=MESG, alt_title='qn trash: ')
    extra_args.extend(hotkey_args)

    ANSWER = show_note_select(qn_options, trash_repo, extra_args, hkman)
    if not ANSWER:
        return(0)
    NOTE, FILTER, OPTSEL = ANSWER
    if not OPTSEL:
        if not NOTE:
            return(0)
        else:
            show_undelete(qn_options, NOTE)
    if OPTSEL == 'showtrash':
        show_default(qn_options)



def show_filtered(qn_options, file_repo, FILTER):


    hkman = hk.HotkeyManager(qn_options['app'])
    hkman.add_key(*qn_options['hotkeys']['grep'])
    hotkey_args = hkman.generate_hotkey_args()


    MESG = "List of notes filtered for '" + FILTER + "'."
    MESG += " Press '" + hkman.get_keybinding('grep') + "' to go back to qn."
    TITLE = 'qn search: '

    extra_args = qn.gen_instance_args(qn_options, 'default'
                                    , alt_help=MESG, alt_title=TITLE)
    extra_args.extend(hotkey_args)



    filters = FILTER.strip().split(" ")
    filtered_repo = file_repo

    if not FILTER:
        show_default(qn_options)
    for f in filters:
        filtered_repo = file_repo.grep_files(f)

    filtered_repo.lineformat = ['name', 'misc']

    ANSWER = show_note_select(qn_options, filtered_repo, extra_args, hkman)

    if not ANSWER:
        return(0)

    print(ANSWER)
    NOTE, FILTER, OPTSEL = ANSWER


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


    if OPTSEL == 'grep':
        if not FILTER:
            show_default(qn_options)
        else:
            show_filtered(qn_options, file_repo, FILTER)


def show_help(qn_options, hotkey_manager, enter_help):


    hkman = hk.HotkeyManager(qn_options['app'])
    hkman.add_key(*qn_options['hotkeys']['showhelp'])
    hotkey_args = hkman.generate_hotkey_args()


    MESG = "List of options and corresponding keybindings."
    MESG += " Press '" + hkman.get_keybinding('showhelp') + "' to go back to qn."
    TITLE = 'qn help: '

    extra_args = qn.gen_instance_args(qn_options, 'default'
                                    , alt_help=MESG, alt_title=TITLE)
    extra_args.extend(hotkey_args)


    help_lines = hotkey_manager.generate_help(enter_help)

    ANSWER = call_command(qn_options, help_lines, extra_args)


    if not ANSWER:
        return(0)
    if not ANSWER[0]:
        sys.exit(0)
    else:
        show_default(qn_options)



if __name__ == '__main__':
    qn.check_environment(True)

    options = qn.generate_options('fzf')
#    options = qn.generate_options('rofi')
    show_default(options)

