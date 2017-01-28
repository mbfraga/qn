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
# Show Help and Keybindings
opt_show_help = 'Alt+h'
# Sort by name
opt_sortbyname = 'Alt+1'
# Sort by creation date
opt_sortbycdate = 'Alt+2'
# Sort by modification date
opt_sortbymdate = 'Alt+3'
# Sort by file size
opt_sortbysize = 'Alt+4'

INTERACTIVE = False

rofi_base_command = ['rofi', '-dmenu', '-i', '-width', '50', '-lines', '15', '-p', 'qn:']

default_help_string = 'Press "' + opt_show_help + '" to see a list of hotkeys.'

default_qn_options = {}
default_qn_options['title'] = 'qn:'
default_qn_options['help'] = default_help_string
default_qn_options['position'] = None
default_qn_options['filter'] = None
default_qn_options['sortby'] = qn.SORTBY
default_qn_options['sortrev'] = qn.SORTREV

HELP_ALT = ('"Enter" to edit/create, ' 
            + '"' + opt_force_new + '" to force create, "'
            + '"' + opt_delete    + '" to delete, "'
            + '"' + opt_seetrash  + '" to show trash, "'
            + '"' + opt_rename    + '" to rename'
            + '.')



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


def show_main_rofi(qn_options, file_list=None):
    print(qn_options)

    if file_list:
        file_name_list = file_list
        file_path_list = None
        hotkey_args = []

    else:
        file_repo = qn.file_repo(qn.QNDIR)

        file_repo.sort(qn_options['sortby'], qn_options['sortrev'])
        hotkey_args = ['-kb-custom-19', opt_delete,
                       '-kb-custom-18', opt_seetrash,
                       '-kb-custom-17', opt_rename,
                       '-kb-custom-16', opt_open_dir,
                       '-kb-custom-15', opt_filter_content,
                       '-kb-custom-14', opt_force_new,
                       '-kb-custom-13', opt_seetagm,
                       '-kb-custom-12', opt_seetagb,
                       '-kb-custom-11', opt_addtag,
                       '-kb-custom-10', opt_show_help,
                       '-kb-custom-1', opt_sortbyname,
                       '-kb-custom-2', opt_sortbycdate,
                       '-kb-custom-3', opt_sortbymdate,
                       '-kb-custom-4', opt_sortbysize
                       ]


        file_name_list = file_repo.filenames()
        file_path_list =  file_repo.filepaths()

    rofi_command = rofi_base_command + ['-mesg', qn_options['help']]
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

    if (val == 28):
        show_delete_rofi(SEL)
        sys.exit(0)
    elif (val == 27):
        show_trash_rofi(qn_options)
    elif (val == 26):
        show_rename_rofi(SEL)
    elif (val == 25):
        print('open dir - not yet implemented')
        sys.exit(1)
    elif (val == 24):
        if file_list:
            print('No search function with alternative qn list')
            sys.exit(1)
        else:
            RESULT = show_filtered_rofi(file_path_list, FILTER, qn_options)
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
        show_tagbrowse_rofi(qn_options)
    elif (val == 20):
        show_tagprompt_rofi(SEL)
    elif (val == 19):
        show_help_rofi(qn_options)

    elif (val == 10):
        newsortby='name'
        if qn_options['sortby'] == newsortby:
            qn_options['sortrev'] = not qn_options['sortrev']
        else:
            qn_options['sortrev'] = False
        qn_options['sortby'] = newsortby
        show_main_rofi(qn_options)
    elif (val == 11):
        newsortby='name'
        if qn_options['sortby'] == newsortby:
            qn_options['sortrev'] = not qn_options['sortrev']
        else:
            qn_options['sortrev'] = False
        qn_options['sortby'] = newsortby
        show_main_rofi(qn_options)
    elif (val == 12):
        newsortby='name'
        if qn_options['sortby'] == newsortby:
            qn_options['sortrev'] = not qn_options['sortrev']
        else:
            qn_options['sortrev'] = False
        qn_options['sortby'] = newsortby
        show_main_rofi(qn_options)
    elif (val == 13):
        newsortby='name'
        if qn_options['sortby'] == newsortby:
            qn_options['sortrev'] = not qn_options['sortrev']
        else:
            qn_options['sortrev'] = False
        qn_options['sortby'] = newsortby
        show_main_rofi(qn_options)
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

def show_filtered_rofi(mff, FILTER, qn_options):


    HELP = "List of notes filtered for '" + FILTER + "'."
    raw, fnotes, fcont = qn.find_in_notes(mff, FILTER.strip())
    rofi_command = rofi_base_command + ['-p', 'qn search', '-mesg', HELP, 
            '-columns', '1', '-format', 'i']

    hotkey_args = ['-kb-custom-19', opt_delete,
                   '-kb-custom-18', opt_seetrash,
                   '-kb-custom-17', opt_rename,
                   '-kb-custom-16', opt_open_dir,
                   '-kb-custom-15', opt_filter_content,
                   '-kb-custom-14', opt_force_new,
                   '-kb-custom-13', opt_seetagm,
                   '-kb-custom-12', opt_seetagb,
                   '-kb-custom-11', opt_addtag,
                   '-kb-custom-10', opt_show_help,
                   '-kb-custom-1', opt_sortbyname,
                   '-kb-custom-2', opt_sortbycdate,
                   '-kb-custom-3', opt_sortbymdate,
                   '-kb-custom-4', opt_sortbysize
                   ]


    if not raw and not fnotes and not fcont:
        qn_options['help'] = "No results found for '" + FILTER + "'"
        show_main_rofi(qn_options)

    if FILTER == '':
        show_main_rofi(qn_options)

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


def show_trash_rofi(qn_options):


    HELP = 'Press enter to restore file, "' 
    HELP += opt_seetrash + '" to go back to qn.'
    trash_repo = qn.file_repo(qn.QNTRASH)
    trash_files = trash_repo.filenames()

    rofi_command = rofi_base_command + ['-mesg', HELP]
    SEL,val = call_rofi(rofi_command, trash_files)
    if (SEL == None):
        sys.exit(1)
    if SEL.strip():
        if val == 0:
            show_undelete_rofi(SEL)
        elif val == 27:
            show_main_rofi(qn_options)


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



def show_tagbrowse_rofi(qn_options):


    tl_help = "'Enter' to see all notes with tag."
    tl_title = "qn browse tags:"
    tl_sel = show_tagslist_rofi(tl_help, tl_title)
    filtered_notes = qn.list_notes_with_tags(tl_sel)
    print(filtered_notes)
    qn_options['qb_title'] = "qn browse (" + tl_sel + ")"
    show_main_rofi(qn_options, file_list=filtered_notes)


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

    YESNO_MSG = "Are you sure you want to rename '" + note.strip()
    YESNO_MSG = "' to '" + SEL.strip() + "'?"
    if show_yesno_rofi(YESNO_MSG):
        qn.move_note(note.strip(), SEL.strip(), move_tags=True)
    else:
        pritn("Doing Nothing.")


def show_help_rofi(qn_options):


    HELP = "QNR Keybindings."
    rofi_command = rofi_base_command + ['-mesg', HELP, '-columns', '1'
                        ,'-format', 's']
    help_lines = []
    help_lines.append("Open Note:           " + "Enter")
    help_lines.append("Force Create Note:   " + opt_force_new)
    help_lines.append("Delete Note:         " + opt_delete)
    help_lines.append("Rename Note:         " + opt_rename)
    help_lines.append("")
    help_lines.append("Show Trash:          " + opt_seetrash)
    help_lines.append("")
    help_lines.append("Show Note Tags:      " + opt_seetagb)
    help_lines.append("Filter by Tags:      " + opt_seetagm)
    help_lines.append("Add Tag to Note:     " + opt_addtag)
    help_lines.append("")
    help_lines.append("Grep filter Notes:   " + opt_filter_content)
    help_lines.append("")
    help_lines.append("Show this help menu: " + opt_show_help)

    call_rofi(rofi_command, help_lines)

    show_main_rofi(qn_options)


if __name__ == '__main__':
    qn.check_environment(True)
    show_main_rofi(default_qn_options)
    #args = parser.parse_args()
    #print(args.interactive)
