import os
import sys
import subprocess
from subprocess import Popen,PIPE
import struct
import magic # to detect mimetypes

import mmap

import time
timea = time.time()

#import notify2

# TO IMPLEMENT
# * Find in notes (grep)
# * Rename note
# * open note's directory in ranger

# User-defined Globals

QNDIR = os.path.join(os.path.expanduser("~"), "syncthing/smalldocs/quicknotes")
#QNDIR = os.path.join(os.path.expanduser("~"), "qn_test")
COLS=3
QNTERMINAL='urxvt'
#QNBROWSER=chromium # not used
QNEDITOR='nvim'


# Globals

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

QNDATA = os.path.join(QNDIR, '.qn')
QNTRASH = os.path.join(QNDATA, 'trash')
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

# Check if program exists - linux only
def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0



# Make sure everything is ready for qn

#print("Checking qn directory " + QNDIR + "...")
if not os.path.isdir(QNDIR):
    print( "Please create your directory as defined by QNDIR!")
    print( "As of now, you set QNDIR to be '$QNDIR'")
    print( "This directory was not found! Exiting...")
    sys.exit(1)
if not os.path.exists(QNDATA):
    os.makedirs(QNDATA, exist_ok=True)
if not os.path.exists(QNTRASH):
    os.makedirs(QNTRASH, exist_ok=True)

# Define application launcher
if cmd_exists('rifle'):
    file_launcher = 'rifle'
else:
    file_launcher = 'xdg-open'

# Check if interactive terminal or not
if sys.stdin.isatty():
    TERM_INTER=True
    text_editor = QNEDITOR
else:
    TERM_INTER=False
    text_editor = QNTERMINAL + ' -e ' + QNEDITOR


# outdated option to detect mimetype? Still best it seems
def file_mime_type(filename):
    m = magic.open(magic.MAGIC_MIME_TYPE)
    m.load()
    return(m.file(filename))

# Right now it includes hidden files - this needs to be fixed
def _list_files(path):
    file_l = [] 
    file_full_l = []

    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            fp = os.path.join(root, name)
            fp_rel = os.path.relpath(fp, path)
            if (fp_rel[0] == '.'):
                continue
            file_l.append(fp_rel)
            file_full_l.append(fp)
    return(file_l, file_full_l)

def _move_note(name1, name2, dest1=QNDIR, dest2=QNDIR):
    has_sp1 = False
    has_sp2 = False

    if ( '/' in name1):
        has_sp1 = True
        sd1,sn1 = name1.rsplit('/',1)
        td1 = os.path.join(dest1, sd1)
    else:
        sn1 = name1
        td1 = dest1

    if ( '/' in name2):
        has_sp2 = True
        sd2,sn2 = name2.rsplit('/',1)
        td2 = os.path.join(dest2, sd2)
    else:
        sn2 = name2
        td2 = dest2

    full_dir1 = os.path.join(td1, sn1)
    full_dir2 = os.path.join(td2, sn2)

    if (full_dir1 == full_dir2):
        print('Source and destination are the same. Doing nothing')
        sys.exit(0)

    # check if destination already exists
    if os.path.exists(full_dir2):
        import datetime
        print('Note with same name found, creating conflict')
        full_dir2 += "-conflict-" 
        full_dir2 += datetime.datetime.now().strftime('%Y%m%d_%H%M%S')

    if has_sp2:
        if not ( os.path.isdir(td2)):
            print('creating ' + td2)
            os.makedirs(td2)
    # move the file
    try:
        os.rename(full_dir1, full_dir2)
        print('Moved ' + full_dir1 + ' to ' + full_dir2)
    except OSError:
        sys.exit(1)

    if has_sp1:
        try:
            os.rmdir(td1)
            print('deleted ' + td1)
        except OSError:
            sys.exit(1)

    sys.exit(0)


def _delete_note(note):
    _move_note(note, note, dest1=QNDIR, dest2=QNTRASH)

def _undelete_note(note):
    _move_note(note, note, dest1=QNTRASH, dest2=QNDIR)

#def notify_send(noti):
#    notify2.init('qn')
#    n = notify2.Notification(noti)
#    n.show()

# Opens everything in text...mimetypes pls
def qnOpenNote(note):
    fulldir = os.path.join(QNDIR, note)

    if os.path.isfile(fulldir):
        mime = file_mime_type(fulldir).split('/')
        if (mime[0] == 'text'):
            os.system(text_editor + " " + fulldir)
        elif (mime[1] == 'x-empty'):
            os.system(text_editor + " " + fulldir)
        else:
            os.system(file_launcher + " " + fulldir)
    else:
        sys.exit(1)


def qnNewNote(note):
    if '/' in note:
        note_dir = note.rsplit('/',1)[0]
        if not os.path.isdir(note_dir):
            os.makedirs(os.path.join(QNDIR, note_dir), exist_ok=True)

    os.system(text_editor + " " + os.path.join(QNDIR, note))
    return(0)


# In implementation - not yet working
def qnFindInNotes(file_list, f_string):
    grep_path = os.path.join(QNDIR, '*')
    filt = f_string.strip().split(" ") 
    filtered_list = file_list
    for f in filt:
        keyword =  f 
        proc = subprocess.Popen(['grep', '-i', '-I',  keyword] + filtered_list, stdout=PIPE)
        answer = proc.stdout.read().decode('utf-8')
        exit_code = proc.wait()
        # trim whitespace
        if answer == '':
            return(None, exit_code)

        filtered_list = []
        filtered_content = []
        raw_lines = []
        
        for ans in answer.split('\n'):
            if ans.strip() == '':
                continue
    #        print(ans)
            raw_lines.append(ans)
            note_name, note_content = ans.split(':', 1)
            if note_name in filtered_list:
                continue
            else:
                filtered_list.append(note_name)
                filtered_content.append(note_content)

    return(raw_lines, filtered_list, filtered_content)

    



def show_main_rofi(starting_filter=None):
    HELP  = "\"Enter\" to edit/create, \"" + opt_delete + "\" to delete, "
    HELP += opt_seetrash + "\" to show trash, "
    HELP += " \"" + opt_rename + "\" to rename"

    main_files,main_files_full = _list_files(QNDIR)
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
        qnOpenNote(RESULT)

    elif (val == 13):
        if SEL.strip():
            print("creating note " + FILTER + "...")
            qnNewNote(FILTER)
    else:
        if SEL.strip():
            path=os.path.join(QNDIR, SEL)
            if os.path.isfile(path):
                print("file found, edit...")
                qnOpenNote(SEL)
            else:
                print("file not found, create...")
                qnNewNote(SEL)

def show_filtered_rofi(mff, FILTER):
    HELP = "List of notes filtered for '" + FILTER + "'."
    raw, fnotes, fcont = qnFindInNotes(mff, FILTER.strip())
    rofi_command = rofi_base_command + ['-p', 'qn search', '-mesg', HELP, 
            '-columns', '1', '-format', 'i']

    if FILTER == '':
        show_main_rofi()

    final_list = []
    n = 0
    for fn in fnotes:
        fn_rel = os.path.relpath(fn, QNDIR)
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
    trash_files, trash_files_full = _list_files(QNTRASH)
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
        _delete_note(note)
    else:
        print("Not Deleting " + note)

def show_undelete_rofi(note):
    HELP_MSG = "Are you sure you want to restore \"" + note + "\"?"
    if show_yesno_rofi(HELP_MSG):
        print("Restoring " + note)
        _undelete_note(note)
    else:
        print("Not Restoring " + note)

def show_rename_rofi(note):
    HELP = "Please write the new name for this file"
    rofi_command = rofi_base_command + ['-mesg', HELP, '-columns', '1',
                    '-p', 'qn', 'rename', '-filter', note]

    SEL, val = call_rofi(rofi_command, [''])

    if (SEL == None):
        sys.exit(1)

    _move_note(note.strip(), SEL.strip())




def start_qn ():

    show_main_rofi()

start_qn()
timeb = time.time()
print('delta t: ' + str(timeb-timea))
#print(_delete_note('del/file1'))
#print(_undelete_note('del/file1'))
#print(show_yesno_rofi('are you sure you want to delete this?'))
#show_undelete_rofi('del/file1')
