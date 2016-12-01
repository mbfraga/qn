import os
import sys
from subprocess import Popen, PIPE, call
import struct

import qn



fzf_base_command = ['fzf']
HELP_M = ""
HELP_ALT = ""

keybindings = {}
keybindings['alt-bspace'] = 'opt_delete'
keybindings['alt-t'] = 'opt_seetrash'
keybindings['alt-space'] = 'opt_rename'
keybindings['alt-d'] = 'opt_open_dir'
keybindings['alt-f'] = 'opt_filter_content' #alt-s is eaten by terminal
keybindings['alt-return'] = 'opt_force_new'
keybindings['alt-o'] = 'opt_seetagm' #alt-u is eaten by terminal
keybindings['alt-p'] = 'opt_seetagb' #alt-i is eaten by terminal
keybindings['alt-n'] = 'opt_addtag'
keybindings['alt-h'] = 'opt_help'

def call_fzf(fzf_command, entries, additional_args=[]):


    expect_keys=None
    for key in keybindings.keys():
        if not expect_keys:
            expect_keys = key
        else:
            expect_keys += ',' + key

    additional_args.extend(['--read0',
                            '--expect',expect_keys,
                            '--print-query',
                            '--print0'
                            ])


    proc=Popen(fzf_command + additional_args, stdin=PIPE, stdout=PIPE)
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
        answer_l = answer.split('\x00')
        return(answer_l, exit_code)


def show_main_fzf(prev_filter=None, files_l=None, title_s=None, help_s=None):

    if files_l:
        if not title_s:
            TITLE = "--prompt=qn alt list > "
        else:
            TITLE = "--prompt=" + title_s
        if help_s:
            HELP = '--header=' + help_s
        else:
            HELP = '--header=' + HELP_ALT 
        main_files = files_l
        main_files_full = None
    else:
        if not title_s:
            TITLE = "--prompt=qn > "
        else:
            TITLE = "--prompt=" + title_s
        if help_s:
            HELP = '--header=' + help_s
        else:
            HELP = '--header=' + HELP_M
        main_files,main_files_full = qn.list_files(qn.QNDIR)

    fzf_command = fzf_base_command + [TITLE, HELP]

    if prev_filter:
        fzf_command += ['--query=' + prev_filter]

    ANS, VAL = call_fzf(fzf_command, main_files)

    if not ANS:
        sys.exit(0)
    if len(ANS) < 4:
        FILTER, KEY, MISC = ANS[0:3]
        SEL = None
    else:
        FILTER, KEY, SEL, MISC = ANS

    if not KEY:
        if not SEL:
            print("file not found, create...")
            qn.new_note(FILTER)
        else:
            path=os.path.join(qn.QNDIR, SEL.strip())
            if os.path.isfile(path):
                print("file found, edit...")
                qn.open_note(SEL)
            else:
                print("file not found, create...")
                qn.new_note(FILTER)

    else:
        key_action = keybindings[KEY]
        if key_action == "opt_force_new":
            pass
            # Force Open
            if not FILTER.strip():
                sys.exit(0)
            file_path = os.path.join(qn.QNDIR, FILTER.strip())
            if os.path.isfile(file_path):
                print(file_path + " is already a file...opening normally.")
                qn.open_note(FILTER)
            elif os.path.isdir(file_path):
                print(file_path + " is a directory...doing nothing")
            else:
                print("Creating note " + FILTER + "...")
                qn.new_note(FILTER)
        elif key_action == 'opt_filter_content':
            if files_l:
                print('No search fucntion with alternative qn list')
                sys.exit(0)
            else:
                RESULT=show_filtered_fzf(main_files_full, FILTER)
                print("Opening " + RESULT + "...")
                qn.open_note(RESULT)
        elif key_action == 'opt_seetrash':
            show_trash_fzf()
        elif key_action == 'opt_delete':
            show_delete_fzf(SEL)
        elif key_action == 'opt_rename':
            show_rename_fzf(SEL)
        elif key_action == 'opt_seetagm':
            show_tagmenu_fzf(SEL)
        elif key_action == 'opt_addtag':
            show_tagprompt_fzf(SEL)
        elif key_action == 'opt_seetagb':
            show_tagbrowse_fzf()
        else:
            print ("Action for '" + key_action + "' not implemented.")
            sys.exit(0)


def show_trash_fzf():


    HELP = 'Press enter to restore file'
    trash_files, trash_files_full = qn.list_files(qn.QNTRASH)
    fzf_command = fzf_base_command + ['--header=' + HELP]
    ANS,val = call_fzf(fzf_command, trash_files)
    if ( not ANS ):
        sys.exit(1)
    elif (len(ANS) < 4):
        sys.exit(1)
    else:
        SEL = ANS[2].strip()
        if SEL:
            show_undelete_fzf(SEL)
            sys.exit(0)


def show_undelete_fzf(note):


    HELP = "Are you sure you want to restore \"" + note + "\"?"
    if show_yesno_fzf(HELP):
        print("Restoring " + note)
        qn.undelete_note(note)
    else:
        print("Not Restoring " + note)


def show_delete_fzf(note):
    HELP = "Are you sure you want to delete \"" + note + "\"?"
    if show_yesno_fzf(HELP):
        print("Deleting " + note)
        qn.delete_note(note)
    else:
        print("Not Deleting " + note)


def show_rename_fzf(note):


    HELP = "Please write the new name for this file"
    fzf_command = fzf_base_command + ['--header=' + HELP, '--query=' + note]
    ANS, val = call_fzf(fzf_command, [''])

    if val == 130:
        show_main_fzf()
    if not ANS:
        sys.exit(1)

    FILTER=ANS[0].strip()

    if ANS:
        qn.move_note(note.strip(), FILTER, move_tags=True)
    else:
        sys.exit(0)


def show_filtered_fzf(mff, FILTER):


    HELP = "List of notes filtered for '" + FILTER + "'."
    raw, fnotes, fcont = qn.find_in_notes(mff, FILTER.strip())
    fzf_command = fzf_base_command + ['--header=' + HELP ]

    if not raw and not fnotes and not fcont:
        show_main_fzf(help_s = "No results found for '" + FILTER + "'")
        sys.exit

    if FILTER == '':
        show_main_fzf()

    final_list = []
    n = 0
    for fn in fnotes:
        fn_rel = os.path.relpath(fn, qn.QNDIR)
        if len(fn_rel) > 21:
            fn_rel = fn_rel[0:10] + '…' + fn_rel[-11:len(fn_rel)]
        fn_rel += "  :  " + fcont[n]
        final_list.append(fn_rel)
        n += 1

    ANS,val = call_fzf(fzf_command, final_list)

    if not ANS or len(ANS) < 4:
        print("No note from filtered list was selected, filter was '" 
              + FILTER + "'.")
        sys.exit(0)

    RAW_SEL = ANS[2]
    SEL = RAW_SEL.split(':')[0].strip()

    return(SEL)


def show_yesno_fzf(HELP_MSG):

    HELP = HELP_MSG
    fzf_command = fzf_base_command + ['--header=' + HELP]
    ANS, val = call_fzf(fzf_command, ['no','yes'])
    if val == 130 or len(ANS) < 4:
        show_main_fzf()

    SEL = ANS[2]
    if SEL:
        return(SEL == 'yes')
    else:
        sys.exit(1)


def show_tagmenu_fzf(notename):


    HELP = 'Tag menu for "' + notename + '"'
    TITLE = 'qn tag menu > '

    fzf_command = fzf_base_command + ['--header=' + HELP, '--prompt=' + TITLE ]

    OPTIONS = []
    existing_tags = qn.list_note_tags(notename)
    OPTIONS += existing_tags # for now, I'm just showing tags
    ANS,val = call_fzf(fzf_command, OPTIONS)

    if ANS == None:
        sys.exit(0)

    FILTER,KEY,SEL,MISC=[None,None,None,None]
    if len(ANS) < 4:
        FILTER,KEY,MISC = ANS
    else:
        FILTER,KEY,SEL,MISC = ANS

    if KEY:
        key_action = keybindings[KEY]
        if key_action == 'opt_delete':
            if SEL:
                qn.del_note_tag(SEL, notename)
            else:
                print('Tried to delete nonexisting tag from note: ' + notename)
        elif key_action == 'opt_addtag':
            show_tagprompt_fzf(notename)
        else:
            sys.exit(0)

    else:
        sys.exit(0)

    sys.exit(0)


def show_tagprompt_fzf(notename):
#
#
    HELP = "Write tag you wish to add to " + notename + "."
#    HELP += "'" + opt_force_new + "' to force add tag"
    TITLE = 'qn add tag > '
    existing_tags = qn.list_tags()
    fzf_command = fzf_base_command + ['--header=' + HELP, '--prompt', TITLE]

    ANS, val = call_fzf(fzf_command, existing_tags)
    if not ANS:
        sys.exit(0)

    FILTER,KEY,SEL,MISC=[None,None,None,None]
    if len(ANS) < 4:
        FILTER,KEY,MISC = ANS
    else:
        FILTER,KEY,SEL,MISC = ANS

    if KEY:
        key_action = keybindings[KEY]
        if key_action == 'opt_force_new':
            print("Force add tag '" + FILTER + "'")
            qn.add_note_tag(FILTER, notename)
        else:
            print('Key, "' + KEY + '" does nothing here.')
            sys.exit(0)
    elif SEL:
        print("Adding tag '" + SEL + "'")
        qn.add_note_tag(SEL, notename)
    else:
        if FILTER:
            print("Adding tag '" + FILTER + "'")
            qn.add_note_tag(FILTER, notename)

        sys.exit(1)


def show_tagbrowse_fzf():


    HELP = "Select tag to see all corresponding notes."
    TITLE = "qn browse tags > "
    TAG_SEL = show_tagslist_fzf(HELP, TITLE)
    filtered_notes = qn.list_notes_with_tags(TAG_SEL)
    tb_title = "qn browse (" + TAG_SEL + ") > "
    show_main_fzf(files_l=filtered_notes, title_s=tb_title)


def show_tagslist_fzf(HELP, TITLE='qn taglist:'):


    fzf_command = fzf_base_command + ['--prompt=' + TITLE, '--header=' + HELP]
    tagslist = qn.list_tags()
    ANS,val = call_fzf(fzf_command, tagslist)

    if not ANS:
        sys.exit(0)
    if len(ANS) < 4:
        sys.exit(0)
    else:
        FILTER,KEY,SEL,MISC = ANS
    return(SEL.strip())


if __name__ == '__main__':
    qn.check_environment(False)
    show_main_fzf()

