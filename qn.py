import os
import sys
import subprocess
from subprocess import Popen,PIPE
import struct
import magic

#import notify2

# TO IMPLEMENT
# * Find in notes (grep)
# * Rename note
# * open note's directory in ranger


QNDIR = os.path.expanduser("~") + "/syncthing/smalldocs/quicknotes"
QNDIR = os.path.expanduser("~") + "/qn_test"
#PERSISTENT = False
COLS=3
QNTERMINAL='urxvt'
#QNBROWSER=chromium
QNEDITOR='nvim'

opt_delete = 'Alt+Backspace'
opt_seetrash = 'Alt+t'
opt_rename = 'Alt+Space'
opt_open_dir = 'Alt+d'
opt_filter_content = 'Alt+s'
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
    #trim whitespace
    if answer == '':
        return(None, exit_code)
    else:
        return(answer.strip('\n'), exit_code)

# linux only
def cmd_exists(cmd):
    return subprocess.call("type " + cmd, shell=True, 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE) == 0



# Preprocess stuff
if not os.path.isdir(QNDIR):
    print( "Please create your directory as defined by QNDIR!")
    print( "As of now, you set QNDIR to be '$QNDIR'")
    print( "This directory was not found! Exiting...")
    sys.exit(1)

if not os.path.exists(QNDATA):
    os.makedirs(QNDATA, exist_ok=True)

if not os.path.exists(QNTRASH):
    os.makedirs(QNTRASH, exist_ok=True)

if cmd_exists('rifle'):
    file_launcher = 'rifle'
else:
    file_launcher = 'xdg-open'

if sys.stdin.isatty():
    TERM_INTER=True
    #text_editor = [QNEDITOR]
    text_editor = QNEDITOR
    #subprocess.Popen(['notify-send', 'interactive'])
else:
    TERM_INTER=False
    #text_editor = [QNTERMINAL, '-e', QNEDITOR]
    text_editor = QNTERMINAL + ' -e ' + QNEDITOR
    #subprocess.Popen(['notify-send', 'not interactive'])


# outdated option? Still best it seems
def file_mime_type(filename):
    m = magic.open(magic.MAGIC_MIME_TYPE)
    m.load()
    return(m.file(filename))

def _list_files(path):
    list_files = [] 
    for root, dirs, files in os.walk(path, topdown=True):
        for name in files:
            fp = os.path.join(root, name)
            list_files.append(os.path.relpath(fp, path))
    return(list_files)

# old method
def _neat_move_file(note, dirs, dirt, newname=None):
    if ( '/' in note):
        print(note.rsplit('/'))
        subpath,notename = note.rsplit('/', 1)
        
        full_dirs_sp = os.path.join(dirs, subpath)
        full_dirt_sp = os.path.join(dirt, subpath)
        full_dirs_np = os.path.join(full_dirs_sp, notename)
        if newname:
            full_dirt_np = os.path.join(full_dirt_sp, newname)
        else:
            full_dirt_np = os.path.join(full_dirt_sp, notename)


        if ( os.path.isdir(full_dirs_sp) ):
            if not ( os.path.isdir(full_dirt_sp)):
                print('creating ' + full_dirt_sp)
                os.makedirs(full_dirt_sp)

        try:
            os.rename(full_dirs_np, full_dirt_np)
            print('Moved ' + full_dirs_np + ' to ' + full_dirt_np)
        except OSError:
            sys.exit(1)

        try:
            os.rmdir(full_dirs_sp)
        except OSError:
            sys.exit(1)

        sys.exit(0)

    try:
        full_dirs_np = os.path.join(dirs, note)
        if newname:
            full_dirt_np = os.path.join(dirt, newname)
        else:
            full_dirt_np = os.path.join(dirt, notename)

        os.rename(full_dirs_np, full_dirt_np)
        print('Moved ' + full_dirs_np + ' to ' + full_dirt_np)

        sys.exit(0)
    except OSError:
        sys.exit(1)


def _delete_note(note):
    _move_note(note, note, dest1=QNDIR, dest2=QNTRASH)

def _undelete_note(note):
    _move_note(note, note, dest1=QNTRASH, dest2=QNDIR)

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
        #print(note_dir)
        if not os.path.isdir(note_dir):
            os.makedirs(os.path.join(QNDIR, note_dir), exist_ok=True)

    os.system(text_editor + " " + os.path.join(QNDIR, note))

    return(1)


def qnFindInNotes(strings):
    if (isinstance(strings, basestring)):
        print('Searching in notes for ' + strings)

        proc = Popen(rofi_command + additional_args, stdin=PIPE, stdout=PIPE)

        proc.stdin.write((strings).encode('utf-8'))
        proc.stdin.write(struct.pack('B', 0))

        proc.stdin.close()
        answer = proc.stdout.read().decode("utf-8")
        exit_code = proc.wait()
        print(answer)
 

    #for var in strings:


#def qnDelNote(note):

     



def show_main_rofi(starting_filter=None):
    HELP  = "\"Enter\" to edit/create, \"" + opt_delete + "\" to delete, "
    HELP += opt_seetrash + "\" to show trash, "
    HELP += " \"" + opt_rename + "\" to rename"

    main_files = _list_files(QNDIR)
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
        print('open dir')
    elif (val == 14):
        print('find content')
        qnFindInNotes([FILTER])
    elif (val == 13):
        if SEL.strip():
            print("creating file " + FILTER + "...")
            qnNewNote(FILTER)

    else:
        if SEL.strip():
            path=QNDIR + "/" + SEL
            #print(path)
            if os.path.isfile(path):
                print("file found, edit...")
                qnOpenNote(SEL)
            else:
                print("file not found, create...")
                qnNewNote(SEL)

def show_trash_rofi():
    HELP = 'Press enter to restore file'
    trash_files = _list_files(QNTRASH)
    print(trash_files)
    rofi_command = rofi_base_command + ['-mesg', HELP]
    SEL,val = call_rofi(rofi_command, trash_files)

    if (SEL == None):
        sys.exit(1)

    if SEL.strip():
        print(SEL)
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
#print(_delete_note('del/file1'))
#print(_undelete_note('del/file1'))
#print(show_yesno_rofi('are you sure you want to delete this?'))
#show_undelete_rofi('del/file1')
