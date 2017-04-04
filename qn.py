import os
import sys
import argparse
from subprocess import Popen,PIPE, call
import pickle
from datetime import datetime
import mimetypes
from stat import ST_CTIME, ST_ATIME, ST_MTIME, ST_SIZE
from operator import itemgetter
import configargparse


# TO IMPLEMENT
# * open note's directory in ranger

# User-defined Globals
QNDIR = os.path.join(os.path.expanduser("~"), "syncthing/smalldocs/quicknotes")
SORTBY='cdate'
SORTREV=False
QNTERMINAL='urxvt'
QNEDITOR='vim'

# Globals
_QNDATA = os.path.join(QNDIR, '.qn')
_QNTRASH = os.path.join(_QNDATA, 'trash')
_TAGF_PATH = os.path.join(_QNDATA, 'tags.pickle')
_FALLBACK_TERMINAL = 'xterm'
_FALLBACK_EDITOR = 'vi'

_IMPLEMENTED_APPS = ('rofi', 'fzf')
_SORT_OPTS = ('cdate', 'mdate', 'name', 'size')

def gen_default_options(appname):


    qn_options = {}
    qn_options['title'] = 'qn:'
    qn_options['qndir'] = None
    qn_options['terminal'] = None
    qn_options['editor'] = None
    qn_options['help'] = None
    qn_options['position'] = None
    qn_options['filter'] = None
    qn_options['sortby'] = SORTBY
    qn_options['sortrev'] = SORTREV

    if appname not in _IMPLEMENTED_APPS:
        raise ValueError('App "%r" not implemented.' % (appname))
    if appname == 'rofi':
        qn_options['app'] = 'rofi'
        qn_options['interactive'] = False 
        qn_options['help'] = ''
        qn_options['command'] = ['rofi', '-sep', '\\0', '-columns', '1'
                        , '-dmenu', '-i'
                        , '-kb-custom-1', 'Alt+Shift+1' #remove previous bindings
                        , '-kb-custom-2', 'Alt+Shift+2' #remove previous bindings
                        , '-kb-custom-3', 'Alt+Shift+3' #remove previous bindings
                        , '-kb-custom-4', 'Alt+Shift+4' #remove previous bindings
                        ]
        qn_options['hotkeys'] = {
                    'forcenew'  :['forcenew'  ,'Alt+Return' , 'Force Create New Note'],
                    'rename'    :['rename'    ,'Alt+space'  , 'Rename Note'],
                    'delete'    :['delete'    ,'Alt+r'      , 'Delete Note'],
                    'grep'      :['grep'      ,'Alt+g'      , 'Grep Notes'],
                    'showtrash' :['showtrash' ,'Alt+t'      , 'Show Trash'],
                    'showhelp'  :['showhelp'  ,'Alt+h'      , 'Show Help'],
                    'sortcdate' :['sortcdate' ,'Alt+2'      , 'Sort by Creation Date'],
                    'sortname'  :['sortname'  ,'Alt+1'      , 'Sort By Name'],
                    'sortmdate' :['sortmdate' ,'Alt+3'      , 'Sort by Modificatin Date'],
                    'sortsize'  :['sortsize'  ,'Alt+4'      , 'Sort by Size'],
                    'addtag'    :['addtag'    ,'Alt+n'      , 'Add Tag to Note (Not Implemented)'],
                    'showtagb'  :['showtagb'  ,'Alt+i'      , 'Show Note Tags (Not Implemented)'],
                    'showtagm'  :['showtagm'  ,'Alt+u'      , 'Filter By Tags (Not Implemented)']
                    }


    elif appname == 'fzf':
        qn_options['app'] = 'fzf'
        qn_options['interactive'] = True 
        qn_options['help'] = ''
        qn_options['title'] = 'qn: '
        qn_options['command'] = ['fzf'
                   ,'--read0'
                   ,'--print-query'
                   ,'--print0'
                   ,'--exact'
                   ,'--expect', 'alt-t'
                    ]
        qn_options['hotkeys'] = {
                    'forcenew'  :['forcenew'  ,'alt-return' , 'Force Create New Note'],
                    'delete'    :['delete'    ,'alt-r'      , 'Delete Note'],
                    'rename'    :['rename'    ,'alt-space'  , 'Rename Note'],
                    'addtag'    :['addtag'    ,'alt-n'      , 'Add Tag to Note (Not Implemented)'],
                    'grep'      :['grep'      ,'alt-g'      , 'Grep Notes'],
                    'showtrash' :['showtrash' ,'alt-t'      , 'Show Trash'],
                    'showtagb'  :['showtagb'  ,'alt-j'      , 'Show Note Tags (Not Implemented)'],
                    'showtagm'  :['showtagm'  ,'alt-k'      , 'Filter By Tags (Not Implemented)'],
                    'showhelp'  :['showhelp'  ,'alt-h'      , 'Show Help'],
                    'sortname'  :['sortname'  ,'alt-1'      , 'Sort By Name'],
                    'sortcdate' :['sortcdate' ,'alt-2'      , 'Sort by Creation Date'],
                    'sortmdate' :['sortmdate' ,'alt-3'      , 'Sort by Modificatin Date'],
                    'sortsize'  :['sortsize'  ,'alt-4'      , 'Sort by Size']
                    }
    return(qn_options)


def gen_instance_args(qn_options, instance, alt_help=None, alt_title=None):


    if alt_help:
        helpn = alt_help
    else:
        helpn = qn_options['help']
    if alt_title:
        titlen = alt_title
    else:
        titlen = qn_options['title']

    appname = qn_options['app']
    arguments = []
    if instance == 'default':
        if appname == 'rofi':
            arguments.extend(['-mesg', helpn
                             , '-format', 'f;s;i'
                             ,'-p', titlen])
            if qn_options['filter']:
                arguments.extend(['-filter', qn_options['filter']])
            if qn_options['position']:
                arguments.extend(['-selected-row', qn_options['position']])

        elif appname == 'fzf':
            arguments.extend(['--header', helpn
                             ,'--prompt', titlen])
            if qn_options['filter']:
                arguments.extend(['-filter', qn_options['filter']])

    return(arguments)


def parse_config(): 


    default_config_path = '~/.config/qn/config'
    default_config_path_expanded = default_config_path
    config_used=None

    p = configargparse.ArgParser(default_config_files=[default_config_path])
    p.add('-c', '--config', is_config_file=True
            , help='config file path')
    p.add('-d', '--qndir', default='~/qn/', help='qn directory path')
    p.add('--terminal', default='xterm', help='default terminal to use')
    p.add('--text-editor', default='vim', help='default text editor to use')
    p.add('--default-interface', default='rofi'
            , help='default interface (rofi/fzf) to use')
    p.add('-r', default=False, action='store_true', help='run as rofi')
    p.add('-f', default=False, action='store_true', help='run as fzf')
    p.add('--sortby', default='cdate'
            , help='type of default sorting (cdate, mdate, name, size)')
    p.add('--sortrev', default=False, help='reverse sorting (True/False)')
    p.add('--rofi-settings', default=False
            , help="rofi settings to append. Format as: '-width 1 -lines 15'"
                + ", surround by '( )' if using command line argument"
                + ". In config, exclude quotes.")
    p.add('--fzf-settings', default=False
            , help="rofi settings to append. Format as: '--height=100; --border'"
                + ", surround by '( )' if using command line argument"
                + ". In config, exclude quotes.")
    # Need to improve formatting on this...but not sure how
    p.add('--rofi-keybindings', default=False, help="define keybindings. Format as:"
                + " command=keybinding; e.g., forcenew=Alt+Return;rename=Alt+space."
                + " Possible commands: forcenew,rename,delete,grep,showtrash"
                + " ,showhelp,sortcdate,sortname,sortmdate,sortsize")
    p.add('--fzf-keybindings', default=False, help="define keybindings. Format as:"
                + " command=keybinding; e.g., forcenew=alt-Return;rename=alt+space."
                + " Possible commands: forcenew,rename,delete,grep,showtrash"
                + " ,showhelp,sortcdate,sortname,sortmdate,sortsize")

    options = p.parse_args()

    if not os.path.isfile(default_config_path_expanded):
        if not options.config:
            print("Default config file not found at " 
                    + default_config_path_expanded + ", and no config file"
                    + " defined via -c. Using default values.\n")
            config_used = 'defaults'
        else:
            config_used = options.config
    else:
        config_used = default_config_path_expanded

    # Check interface selected and that it is implemented
    if options.default_interface not in _IMPLEMENTED_APPS:
        print("ERROR with config '" + config_used + "': default interface, " 
              + options.default_interface + " not implemented.")
        sys.exit(1)

    # Check if command used for terminal and text editors exist
    if not cmd_exists(options.terminal):
        print("WARNING with config '" + config_used + "': terminal app, "
                + options.terminal + " is not installed. Using default.")
        options.terminal = _FALLBACK_TERMINAL

    if not cmd_exists(options.text_editor):
        print("WARNING with config '" + config_used + "': text editor app, "
                + options.text_editor + " is not installed. Using default.")
        options.text_editor = _FALLBACK_EDITOR

    if options.sortby not in _SORT_OPTS:
        print("WARNING with config '" + config_used + "': sorty option, "
                + options.sortby + " is not valid. Using cdate")
        options.sortby = 'cdate'


    return(options)



# Check if program exists - linux only
def cmd_exists(cmd):


    return call("type " + cmd, shell=True, 
        stdout=PIPE, stderr=PIPE) == 0


# Define application launcher
if cmd_exists('rifle'):
    file_launcher = 'rifle'
else:
    file_launcher = 'xdg-open'


def file_mime_type(filename):

    mtype,menc = mimetypes.guess_type(filename)
    # If type is not detected, just open as plain text
    if not mtype:
        mtype = 'None/None'
    return(mtype)


class FileRepo:
    def __init__(self, dirpath=None):
        self.path = dirpath
        self.file_list = []
        self.sorttype = "none"
        self.sortrev = False
        self.filecount = 0

        self.tags = None

        self.lineformat = ['name', 'cdate']
        self.linebs = {}
        self.linebs['name'] = 40
        self.linebs['adate'] = 18
        self.linebs['cdate'] = 18
        self.linebs['mdate'] = 18
        self.linebs['size'] = 15
        self.linebs['misc'] = 100
        self.linebs['tags'] = 50



    def scan_files(self):
        self.filecount = 0
        for root, dirs, files in os.walk(self.path, topdown=True):
            for name in files:
                fp = os.path.join(root, name)
                fp_rel = fp[len(self.path)+1:]

                if (fp_rel[0] == '.'):
                    continue
                try:
                    stat = os.stat(fp)
                except:
                    continue

                file_props = {}
                file_props['size'] = stat[ST_SIZE]
                file_props['adate'] = stat[ST_ATIME]
                file_props['mdate'] = stat[ST_MTIME]
                file_props['cdate'] = stat[ST_CTIME]
                file_props['name'] = fp_rel
                file_props['fullpath'] = fp
                file_props['misc'] = None
                file_props['tags'] = None

                self.file_list.append(file_props)
                self.filecount += 1


    def add_file(self, filepath, misc_prop=None):
        if not os.path.isfile(filepath):
            print(filepath + " is not a file.")
            return

        fp_rel = filepath[len(self.path)+1:]

        try:
            stat = os.stat(filepath)
        except:
            return

        file_props = {}
        file_props['size'] = stat[ST_SIZE]
        file_props['adate'] = stat[ST_ATIME]
        file_props['mdate'] = stat[ST_MTIME]
        file_props['cdate'] = stat[ST_CTIME]
        file_props['name'] = fp_rel
        file_props['fullpath'] = filepath
        file_props['misc'] = misc_prop

        self.file_list.append(file_props)
        self.filecount += 1

    def sort(self, sortby='name', sortrev=False):
        if sortby not in ['size', 'adate', 'mdate', 'cdate', 'name']:
            print("Key '" + sortby + "' is not valid.")
            print("Choose between size, adate, mdate, cdate or name.")

        self.file_list = sorted(self.file_list, 
                            key=itemgetter(sortby), reverse=not sortrev)
        self.sorttype=sortby
        self.sortrev=sortrev

    def get_property_list(self, prop='name'):
        return(list(itemgetter(prop)(filen) for filen in self.file_list))

    def filenames(self):
        return(self.get_property_list('name'))

    def filepaths(self):
        return(self.get_property_list('fullpath'))

    def lines(self, format_list=None):
        lines = []
        if not format_list:
            format_list = self.lineformat
        for filen in self.file_list:
            line = ""
            for formatn in format_list:
                if formatn in ['adate', 'mdate', 'cdate']:
                    block = datetime.utcfromtimestamp(filen[formatn])
                    block = block.strftime('%d/%m/%Y %H:%M')
                else:
                    block = str(filen[formatn])

                blocksize = self.linebs[formatn]
                if len(block) >= blocksize:
                    block = block[:blocksize-2] + '…'

                block = block.ljust(blocksize)
                line += block

            lines.append(line)

        return(lines)


    def grep_files(self, filters_string):
        if not self.file_list:
            print("No files added to file repo")
            return(1)

        proc = Popen(['grep', '-i', '-I', filters_string] + self.filepaths() 
                     , stdout=PIPE)
        answer = proc.stdout.read().decode('utf-8')
        exit_code = proc.wait()

        grep_file_repo = FileRepo(self.path)
        temp_files = []
        if answer == '':
            return(None)

        for ans in answer.split("\n"):
            if ans:
                ans = ans.split(':', 1)
                if not ans[0] in temp_files:
                    grep_file_repo.add_file(ans[0], ans[1])
                    temp_files.append(ans[0])

        return(grep_file_repo)



def move_note(name1, name2, dest1=QNDIR, dest2=QNDIR, move_tags=False):


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
        print('Source and destination are the same. Doing nothing.')
        sys.exit(0)

    # check if destination already exists
    if os.path.exists(full_dir2):
        print('Note with same name found, creating conflict.')
        appended = "-conflict-" 
        appended += datetime.now().strftime('%Y%m%d_%H%M%S')
        full_dir2 +=  appended
        name2 += appended

    if has_sp2:
        if not ( os.path.isdir(td2)):
            print('creating ' + td2)
            os.makedirs(td2)
    # move the file
    try:
        os.rename(full_dir1, full_dir2)
        if move_tags:
            tagsdict = load_tags()
            if name1 in tagsdict:
                tagsdict[name2] = tagsdict[name1]
                tagsdict.pop(name1)
                save_tags(tagsdict)
        print('Moved ' + full_dir1 + ' to ' + full_dir2)
    except OSError:
        sys.exit(1)

    if has_sp1:
        try:
            os.rmdir(td1)
            print('deleted ' + td1)
        except OSError:
            print('not deleted ' + td1)
            sys.exit(0)

    sys.exit(0)


def delete_note(note):


    move_note(note, note, dest1=QNDIR, dest2=_QNTRASH)


def undelete_note(note):


    move_note(note, note, dest1=_QNTRASH, dest2=QNDIR)


def open_note(note, inter=False):


    fulldir = os.path.join(QNDIR, note)
    if os.path.isfile(fulldir):
        mime = file_mime_type(note).split("/")

        if (mime[0] == 'text' or mime[0] == 'None'):
            if inter:
                os.system(QNEDITOR + " " + fulldir)
            else:
                os.system(QNTERMINAL + " -e " + QNEDITOR + " " + fulldir)
        elif (mime[1] == 'x-empty'):
            if inter:
                os.system(QNEDITOR + " " + fulldir)
            else:
                os.system(QNTERMINAL + " -e " + QNEDITOR + " " + fulldir)
        else:
            os.system(file_launcher + " " + fulldir)
    else:
        print(fulldir + " is not a note")
        sys.exit(1)


def new_note(note, inter=False):


    if '/' in note:
        note_dir = note.rsplit('/',1)[0]
        if not os.path.isdir(note_dir):
            os.makedirs(os.path.join(QNDIR, note_dir), exist_ok=True)
    if inter:
        os.system(QNEDITOR + " " + os.path.join(QNDIR, note))
    else:
        os.system(QNTERMINAL + " -e " + QNEDITOR + " " + os.path.join(QNDIR, note))
    return(0)


def force_new_note(note, inter=False):
    filepath = os.path.join(QNDIR, note.strip())
    if os.path.isfile(filepath):
        open_note(note, inter)
    else:
        new_note(note, inter)
    return(0)



def check_environment():

    conf_options = parse_config()
    if conf_options.r:
        app='rofi'
    elif conf_options.f:
        app='fzf'
    else:
        app=conf_options.default_interface

    print(conf_options)
    qn_options = gen_default_options(app)
    qn_options['qndir'] = os.path.expanduser(conf_options.qndir)
    qn_options['terminal'] = conf_options.terminal
    qn_options['editor'] = conf_options.text_editor
    qn_options['sortby'] = conf_options.sortby
    qn_options['sortrev'] = conf_options.sortrev
    command_extra = False
    rofi_extra_settings = conf_options.rofi_settings
    if rofi_extra_settings and app == 'rofi':
        if rofi_extra_settings[0] == "(":
            command_extra = rofi_extra_settings[1:-1]
        else:
            command_extra = rofi_extra_settings
    fzf_extra_settings = conf_options.fzf_settings
    if fzf_extra_settings and app == 'fzf':
        if fzf_extra_settings[0] == "(":
            command_extra = fzf_extra_settings[1:-1]
        else:
            command_extra = fzf_extra_settings

    if command_extra:
        qn_options['command'].extend(command_extra.split())

    # Make sure everything is ready for qn
    if not os.path.isdir(QNDIR):
        HELP_MSG = " Do you want to create the qn directory: " + QNDIR + "?"

        s = input(HELP_MSG + " (y/N) ")
        if s and (s[0] == "Y" or s[0] == "y"):
            print("Creating directory: " + QNDIR + "...")
            os.makedirs(QNDIR)
        else:
            print("qn directory" + QNDIR + " does not exist. Exiting...")
            sys.exit(1)

    if not os.path.exists(_QNDATA):
        print("Creating directory: " + _QNDATA + "...")
        os.makedirs(_QNDATA, exist_ok=True)
    if not os.path.exists(_QNTRASH):
        print("Creating directory: " + _QNTRASH + "...")
        os.makedirs(_QNTRASH, exist_ok=True)
    if not os.path.isfile(_TAGF_PATH):
        tagfile = open(_TAGF_PATH, 'wb')
        pickle.dump({'__taglist':[]}, tagfile)
        tagfile.close()

    return(qn_options)


# FOR TAG SUPPORT
def load_tags():


    tagfile = open(_TAGF_PATH, 'rb')
    tagdict = pickle.load(tagfile)
    tagfile.close()

    return(tagdict)


def save_tags(newdict):


    tagfile = open(_TAGF_PATH, 'wb')
    pickle.dump(newdict, tagfile)
    tagfile.close()


def list_tags():


    tagslist = load_tags()['__taglist']
    return(tagslist)


def create_tag(tagname):


    tagsdict = load_tags()
    if not tagname in tagsdict['__taglist']:
        tagsdict['__taglist'].append(tagname)
        save_tags(tagsdict)

    return(tagsdict)


def add_note_tag(tagname, notename, tagsdict=None):


    if not os.path.isfile(os.path.join(QNDIR, notename)):
        print('Note does not exist. No tag added.')
        sys.exit(0)
    tagsdict = create_tag(tagname)
    if notename in tagsdict:
        if tagname in tagsdict[notename]:
            print('Note already has tag. Doing nothing')
        else:
            tagsdict[notename].append(tagname)
            save_tags(tagsdict)
    else:
        tagsdict[notename] = [tagname]
        save_tags(tagsdict)

    return(tagsdict)


def del_note_tag(tagname, notename, tagsdict=None):


    if not os.path.isfile(os.path.join(QNDIR, notename)):
        print('Note does not exist. No tag removed.')
        sys.exit(0)

    if not tagsdict:
        tagsdict = load_tags()
    
    if notename in tagsdict:
        if tagname in tagsdict[notename]:
            tagsdict[notename].remove(tagname)
            if not list_notes_with_tags(tagname, tagsdict):
                tagsdict['__taglist'].remove(tagname)
            save_tags(tagsdict)
    else:
        pass

    return(tagsdict)


def clear_note_tags(notename, tagsdict=None):


    if not os.path.isfile(os.path.join(QNDIR, notename)):
        print('Note does not exist. Doing nothing.')
        sys.exit(0)
    if not tagsdict:
        tagsdict = load_tags()
    tagsdict.pop(notename, None)

    return(tagsdict)


def list_note_tags(notename):


    if not os.path.isfile(os.path.join(QNDIR, notename)):
        print('Note does not exist.')
        sys.exit(0)

    tagsdict = load_tags()
    if notename in tagsdict:
        return(tagsdict[notename])
    else:
        return([])


def list_notes_with_tags(tagname, tagsdict=None):


    if not tagsdict:
        tagsdict = load_tags()
    
    filtered_list = []
    for key,value in tagsdict.items():
        if key == '__taglist':
            continue
        if tagname in value:
            filtered_list.append(key)

    return(filtered_list)


 

if __name__ == '__main__':
    qn_options = check_environment()
    print("---------")

    for key,value in qn_options.items():
        print(key, "|", value)

#    parser = argparse.ArgumentParser(prog='qn', 
#                        description="Quick Note Manager.")
#    parser.add_argument('-l', '--list-notes', action='store_true', default=False
#                , help='list notes in note directory')
#    parser.add_argument('-s', '--search', nargs='*', default=-1
#                , help='search for note')
#    parser.add_argument('-o', '--open-note', action='store_true', default=False
#                , help='open')
#
#    args = parser.parse_args()
#    #print(args)
#
#    check_environment()
#    filerepo = FileRepo(QNDIR)
#    filerepo.scan_files()
#    if args.list_notes:
#        for filen in filerepo.filenames():
#            print(filen)
#        sys.exit(0)
#    if args.search != -1:
#        search_list = filerepo.filenames()
#        for filen in filerepo.filenames():
#            bool_list = []
#            for search_string in args.search:
#                bool_list.append(search_string in filen)
#            if all(bool_list):
#                print(filen)
#
#        sys.exit(0)



