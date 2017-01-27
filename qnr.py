import os
import sys
from subprocess import Popen,PIPE,call
import struct
import argparse

import qn

# User Settings
COLS = 3
# Delete note.
opt_delete = 'Alt+r'
# See trashed notes with the ability to restore them.
opt_seetrash = 'Alt+t'
# Rename note.
opt_rename = 'Alt+space'
# Open selected note's directory (not yet implemented).
opt_open_dir = 'Alt+d'
# Grep notes (not yet implemented).
opt_filter_content = 'Alt+s'
# Force create a note.
opt_force_new = 'Alt+Return'
# Enter tag menu.
opt_seetagm = 'Alt+u'
# Browse tags.
opt_seetagb = 'Alt+i'
# Add Tag to note.
opt_addtag = 'Alt+n'

INTERACTIVE = False

rofi_base_command = ['rofi', '-dmenu', '-i', '-width', '50', '-lines', '15', '-p', 'qn:']

HELP_M = ('"Enter" to edit/create, ' 
          + '"' + opt_force_new + '" to force create, "'
          + '"' + opt_delete    + '" to delete, "'
          + '"' + opt_seetrash  + '" to show trash, "'
          + '"' + opt_rename    + '" to rename'
          + ', "' + opt_filter_content + '" to search'
          + ', "' + opt_seetagm      + '" to see note\'s tags'
          + ', "' + opt_seetagb      + '" to see tag browse'
          + ', "' + opt_addtag       + '" to add tag.')
HELP_ALT = ('"Enter" to edit/create, ' 
            + '"' + opt_force_new + '" to force create, "'
            + '"' + opt_delete    + '" to delete, "'
            + '"' + opt_seetrash  + '" to show trash, "'
            + '"' + opt_rename    + '" to rename'
            + '.')



#parser = argparse.ArgumentParser(description='Quick note manager')
#parser.add_argument('-I', dest='interactive', action='store_true')


# call_rofi code borrowed from
def call_rofi(rofi_command, entries, additional_args=[]):


    additional_args.extend([ '-kb-custom-19', opt_delete,
                             '-kb-custom-18', opt_seetrash,
                             '-kb-custom-17', opt_rename,
                             '-kb-custom-16', opt_open_dir,
                             '-kb-custom-15', opt_filter_content,
                             '-kb-custom-14', opt_force_new,
                             '-kb-custom-13', opt_seetagm,
                             '-kb-custom-12', opt_seetagb,
                             '-kb-custom-11', opt_addtag,
                             '-sep', '\\0',
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


def show_main_rofi(prev_filter=None, file_list=None
                   , title_s=None, help_s=None
                   , sortby=qn.SORTBY, sortrev=qn.SORTREV):


    if file_list:
        if not title_s:
            title_s = "qn alt list:"
        if help_s:
            help_m = ['-mesg', help_s]
        else:
            help_m = []
        file_name_list = file_list
        file_path_list = None

    else:
        if not title_s:
            title_s = "qn:"
        if help_s:
            help_m = ['-mesg', help_s]
        else:
            help_m = ['-mesg', HELP_M]
        file_repo = qn.file_repo(qn.QNDIR)

        if sortby:
            file_repo.sort(sortby=sortby, sortrev=sortrev)

        file_name_list = file_repo.filenames()
        file_path_list =  file_repo.filepaths()

    rofi_command = rofi_base_command + help_m + ['-format', 'f;s',
                                                 '-p', title_s]

    if prev_filter:
        rofi_command += ['-filter', prev_filter]

    SELFS,val = call_rofi(rofi_command, file_name_list)
    if (SELFS == None):
        sys.exit(1)
    FILTER,SEL = SELFS.split(';')
    print('sel:' + SEL)
    print('val:' + str(val))

    if (val == 28):
        show_delete_rofi(SEL)
        sys.exit(0)
    elif (val == 27):
        show_trash_rofi()
    elif (val == 26):
        show_rename_rofi(SEL)
    elif (val == 25):
        print('open dir - not yet implemented')
        sys.exit(1)
    elif (val == 24):
        print("DEBUG")
        if file_list:
            print('No search function with alternative qn list')
            sys.exit(1)
        else:
            RESULT = show_filtered_rofi(file_path_list, FILTER)
            print("Opening " + RESULT + "...")
            qn.open_note(RESULT, INTERACTIVE)
    elif (val == 23):
        # Force Open
        if not FILTER.strip():
            sys.exit(0)
        file_path = os.path.join(qn.QNDIR, FILTER.strip())
        if os.path.isfile(file_path):
            print(file_path + " is already a file...opening normally.")
            qn.open_note(FILTER, INTERACTIVE)
        elif os.path.isdir(file_path):
            print(file_path + " is a directory...doing nothing")
        else:
            print("Creating note " + FILTER + "...")
            qn.new_note(FILTER, INTERACTIVE)
    elif (val == 22):
        show_tagmenu_rofi(SEL)
    elif (val == 21):
        show_tagbrowse_rofi()
    elif (val == 20):
        print("add new tag")
        show_tagprompt_rofi(SEL)
    else:
        if SEL.strip():
            path=os.path.join(qn.QNDIR, SEL)
            if os.path.isfile(path):
                print("file found, edit...")
                qn.open_note(SEL, INTERACTIVE)
            else:
                print("file not found, create...")
                qn.new_note(SEL, INTERACTIVE)

    sys.exit(0)

def show_filtered_rofi(mff, FILTER):


    HELP = "List of notes filtered for '" + FILTER + "'."
    raw, fnotes, fcont = qn.find_in_notes(mff, FILTER.strip())
    rofi_command = rofi_base_command + ['-p', 'qn search', '-mesg', HELP, 
            '-columns', '1', '-format', 'i']

    if not raw and not fnotes and not fcont:
        show_main_rofi(help_s = "No results found for '" + FILTER + "'")

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
    trash_repo = qn.file_repo(qn.QNTRASH)
    trash_files = trash_repo.filenames()

    rofi_command = rofi_base_command + ['-mesg', HELP]
    SEL,val = call_rofi(rofi_command, trash_files)
    if (SEL == None):
        sys.exit(1)
    if SEL.strip():
        show_undelete_rofi(SEL)


def show_tagmenu_rofi(notename):


    HELP = 'Tag menu for "' + notename + '"\n'
    HELP += "'Enter' to edit tag, '" + opt_delete + "' to delete tag"
    TITLE = 'qn tag menu:'

    rofi_command = rofi_base_command[0:2] + ['-mesg', HELP, '-p', TITLE
                    , '-columns', '1', '-format', 's']

    OPTIONS = []
    existing_tags = qn.list_note_tags(notename)
    OPTIONS += existing_tags # for now, I'm just showing tags
    SEL,val = call_rofi(rofi_command, OPTIONS)

    if SEL == None:
        sys.exit(0)
    print('sel:' + SEL)
    print('val:' + str(val))

    if (val == 28):
        qn.del_note_tag(SEL, notename)
        print('deleted tag ' + SEL + '...')
    elif (val == 20):
        TAG = show_tagprompt_rofi(notename)
        print('Added "' + TAG + '" tag to note "' + notename +'"')
    else:
        sys.exit(0)

    sys.exit(0)


def show_tagprompt_rofi(notename):


    HELP = "Write tag you wish to add to " + notename + "."
    HELP += "'" + opt_force_new + "' to force add tag"
    title = 'qn add tag:'
    existing_tags = qn.list_tags()
    rofi_command = rofi_base_command + ['-mesg', HELP, '-p', title,
                        '-format', 'f;s', '-columns', '1']
    FSEL, val = call_rofi(rofi_command, existing_tags)
    if not FSEL:
        sys.exit(0)
    FILTER,SEL = FSEL.split(';')
    if (val == 23):
        print("Force add tag '" + FILTER + "'")
        qn.add_note_tag(FILTER, notename)
        return(FILTER)
    else:
        print("Adding tag '" + SEL + "'")
        qn.add_note_tag(SEL, notename)
        return(SEL)

    sys.exit(0)



def show_tagbrowse_rofi():


    tl_help = "'Enter' to see all notes with tag."
    tl_title = "qn browse tags:"
    tl_sel = show_tagslist_rofi(tl_help, tl_title)
    filtered_notes = qn.list_notes_with_tags(tl_sel)
    print(filtered_notes)
    tb_title = "qn browse (" + tl_sel + ")"
    show_main_rofi(file_list=filtered_notes, title_s=tb_title)


def show_tagslist_rofi(HELP_MSG, ROFI_TITLE='qn taglist:'):


    rofi_command = rofi_base_command[0:2] + ['-p', ROFI_TITLE,
                        '-columns', '1', '-mesg', HELP_MSG]
    tagslist = qn.list_tags()
    SEL,val = call_rofi(rofi_command, tagslist)
    if not SEL:
        sys.exit(0)
    return(SEL)


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
        qn.delete_note(note)
    else:
        print("Not Deleting " + note)


def show_undelete_rofi(note):


    HELP_MSG = "Are you sure you want to restore \"" + note + "\"?"
    if show_yesno_rofi(HELP_MSG):
        print("Restoring " + note)
        qn.undelete_note(note)
    else:
        print("Not Restoring " + note)


def show_rename_rofi(note):


    HELP = "Please write the new name for this file"
    rofi_command = rofi_base_command + ['-mesg', HELP, '-columns', '1',
                    '-p', 'qn', 'rename', '-filter', note]
    SEL, val = call_rofi(rofi_command, [''])
    if (SEL == None):
        sys.exit(1)
    qn.move_note(note.strip(), SEL.strip(), move_tags=True)


if __name__ == '__main__':
    qn.check_environment(True)
    show_main_rofi()
    #args = parser.parse_args()
    #print(args.interactive)
