from subprocess import Popen,PIPE,call
import qn
import os
import sys
import struct

COLS=3

# delete note
opt_delete = 'Alt+Backspace'
# see trashed notes with the ability to restore them
opt_seetrash = 'Alt+t'
# rename note
opt_rename = 'Alt+Space'
# Open selected note's directory (not yet implemented)
opt_open_dir = 'Alt+d'
# Grep notes (not yet implemented)
opt_filter_content = 'Alt+s'
# Force create a note
opt_force_new = 'Alt+Return'


rofi_base_command = ['rofi', '-dmenu', '-p', 'qn:']

# code borrowed from
# https://github.com/DaveDavenport/Rofication/blob/master/rofication-gui.py
def call_rofi(rofi_command, entries, additional_args=[]):
    additional_args.extend([ '-kb-custom-9', opt_delete,
                             '-kb-custom-8', opt_seetrash,
                             '-kb-custom-7', opt_rename,
                             '-kb-custom-6', opt_open_dir,
                             '-kb-custom-5', opt_filter_content,
                             '-kb-custom-4', opt_force_new,
                             '-markup-rows',
                             '-sep', '\\0',
#                             '-format', 'i',
                             '-columns', str(COLS),
#                             '-lines', '4',
#                             '-eh', '2',
#                             '-location', '2', '-width', '100' ])
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


def show_main_rofi(starting_filter=None):
    HELP  = "\"Enter\" to edit/create, \"" 
    HELP += opt_force_new + "\" to force create, \""
    HELP += opt_delete + "\" to delete, \""
    HELP += opt_seetrash + "\" to show trash, \""
    HELP += opt_rename + "\" to rename, \""
    HELP += opt_filter_content + "\" to search"

    main_files,main_files_full = qn._list_files(qn.QNDIR)
    rofi_command = rofi_base_command + ['-mesg', HELP, '-format', 'f;s']
    if starting_filter:
        rofi_command += ['-filter', starting_filter]

    SELFS,val = call_rofi(rofi_command,main_files)

    if (SELFS == None):
        sys.exit(1)

    FILTER,SEL = SELFS.split(';')
    #print('sel:' + SEL)
    #print('val:' + str(val))

    if (val == 18):
        show_delete_rofi(SEL)
        sys.exit(0)
    elif (val == 17):
        show_trash_rofi()
    elif (val == 16):
        show_rename_rofi(SEL)
    elif (val == 15):
        print('open dir - not yet implemented')
    elif (val == 14):
        print('find content - not yet implemented')
        RESULT = show_filtered_rofi(main_files_full, FILTER)
        print("Opening " + RESULT + "...")
        qn.qn_open_note(RESULT)

    elif (val == 13):
        if SEL.strip():
            print("creating note " + FILTER + "...")
            qn.qn_new_note(FILTER)
    else:
        if SEL.strip():
            path=os.path.join(qn.QNDIR, SEL)
            if os.path.isfile(path):
                print("file found, edit...")
                qn.qn_open_note(SEL)
            else:
                print("file not found, create...")
                qn.qn_new_note(SEL)

def show_filtered_rofi(mff, FILTER):
    HELP = "List of notes filtered for '" + FILTER + "'."
    raw, fnotes, fcont = qn_find_in_notes(mff, FILTER.strip())
    rofi_command = rofi_base_command + ['-p', 'qn search', '-mesg', HELP, 
            '-columns', '1', '-format', 'i']

    if FILTER == '':
        show_main_rofi()

    final_list = []
    n = 0
    for fn in fnotes:
        fn_rel = os.path.relpath(fn, qn.QNDIR)
        if len(fn_rel) > 21:
            fn_rel = fn_rel[0:10] + '…' + fn_rel[-11:len(fn_rel)]

        fn_rel += "  :  " + fcont[n]
        final_list.append(fn_rel)
        n += 1

    SEL,val = call_rofi(rofi_command, final_list)
    if SEL == None:
        sys.exit(0)
    
    return(fnotes[int(SEL)])

def show_trash_rofi():
    HELP = 'Press enter to restore file'
    trash_files, trash_files_full = qn._list_files(qn.QNTRASH)
    rofi_command = rofi_base_command + ['-mesg', HELP]
    SEL,val = call_rofi(rofi_command, trash_files)
    if (SEL == None):
        sys.exit(1)
    if SEL.strip():
        show_undelete_rofi(SEL)

def show_yesno_rofi(HELP_MSG):
    HELP="<span color=\"red\">"
    HELP+=HELP_MSG
    HELP+="</span>"
    rofi_command = rofi_base_command + ['-mesg', HELP, '-columns', '1']
    SEL,val = call_rofi(rofi_command, ['no','yes'])
    
    if SEL:
        return(SEL == 'yes')
    else:
        sys.exit(1)

def show_delete_rofi(note):
    HELP_MSG = "Are you sure you want to delete \"" + note + "\"?"
    if show_yesno_rofi(HELP_MSG):
        print("Deleting " + note)
        qn._delete_note(note)
    else:
        print("Not Deleting " + note)

def show_undelete_rofi(note):
    HELP_MSG = "Are you sure you want to restore \"" + note + "\"?"
    if show_yesno_rofi(HELP_MSG):
        print("Restoring " + note)
        qn._undelete_note(note)
    else:
        print("Not Restoring " + note)

def show_rename_rofi(note):
    HELP = "Please write the new name for this file"
    rofi_command = rofi_base_command + ['-mesg', HELP, '-columns', '1',
                    '-p', 'qn', 'rename', '-filter', note]

    SEL, val = call_rofi(rofi_command, [''])

    if (SEL == None):
        sys.exit(1)

    qn._move_note(note.strip(), SEL.strip())

if __name__ == '__main__':
    qn.check_environment(True)
    show_main_rofi()