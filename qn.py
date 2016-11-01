import os
import sys
from subprocess import Popen,PIPE, call

try:
    import magic # to detect mimetypes
except OSError:
    print("Please install python-magic. Exiting...")
    sys.exit(1)

#import mmap

#import time
#timea = time.time()

#import notify2

# TO IMPLEMENT
# * Find in notes (grep)
# * Rename note
# * open note's directory in ranger

# User-defined Globals

QNDIR = os.path.join(os.path.expanduser("~"), "syncthing/smalldocs/quicknotes")
#QNDIR = os.path.join(os.path.expanduser("~"), "qn_test2")
QNTERMINAL='urxvt'
#QNBROWSER=chromium # not used
QNEDITOR='nvim'


# Globals
QNDATA = os.path.join(QNDIR, '.qn')
QNTRASH = os.path.join(QNDATA, 'trash')
TERM_INTER = False


# Check if program exists - linux only
def cmd_exists(cmd):
    return call("type " + cmd, shell=True, 
        stdout=PIPE, stderr=PIPE) == 0

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
def qn_open_note(note):
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


def qn_new_note(note):
    if '/' in note:
        note_dir = note.rsplit('/',1)[0]
        if not os.path.isdir(note_dir):
            os.makedirs(os.path.join(QNDIR, note_dir), exist_ok=True)

    os.system(text_editor + " " + os.path.join(QNDIR, note))
    return(0)


# In implementation - not yet working
def qn_find_in_notes(file_list, f_string):
    grep_path = os.path.join(QNDIR, '*')
    filt = f_string.strip().split(" ") 
    filtered_list = file_list
    for f in filt:
        keyword =  f 
        proc = Popen(['grep', '-i', '-I',  keyword] + filtered_list, stdout=PIPE)
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

def check_environment(in_rofi=False):
    # Make sure everything is ready for qn

    #print("Checking qn directory " + QNDIR + "...")
    if not os.path.isdir(QNDIR):
        HELP_MSG = " Do you want to create the qn directory: " + QNDIR + "?"
        if in_rofi:
            from qnr import show_yesno_rofi # this doesn't seem like the right approach...but for now it works(tm)
            if show_yesno_rofi(HELP_MSG):

                print("Creating directory: " + QNDIR + "...")
                os.makedirs(QNDIR)
            else:
                print("qn directory" + QNDIR + " does not exist. Exiting...")
                sys.exit(1)
        else:
            s = input(HELP_MSG + " (y/N) ")
            if s and (s[0] == "Y" or s[0] == "y"):
                print("Creating directory: " + QNDIR + "...")
                os.makedirs(QNDIR)
            else:
                print("qn directory" + QNDIR + " does not exist. Exiting...")
                sys.exit(1)

    if not os.path.exists(QNDATA):
        print("Creating directory: " + QNDATA + "...")
        os.makedirs(QNDATA, exist_ok=True)
    if not os.path.exists(QNTRASH):
        print("Creating directory: " + QNTRASH + "...")
        os.makedirs(QNTRASH, exist_ok=True)


#def start_qnr ():
#    in_rofi = True
#    check_environment(in_rofi)
#    show_main_rofi()

#start_qnr()
#timeb = time.time()
