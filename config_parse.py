import os
import sys
from subprocess import Popen,PIPE, call
import configargparse
import hotkey_manager


# Globals
#_TAGF_PATH = os.path.join(_QNDATA, 'tags.pickle')
_DEFAULT_QNDIR = '~/qn/'
_FALLBACK_TERMINAL = 'xterm'
_FALLBACK_EDITOR = 'vi'

_IMPLEMENTED_APPS = ('rofi', 'fzf')
_SORT_OPTS = ('cdate', 'mdate', 'name', 'size')
_HOTKEY_COMMANDS = ('forcenew', 'rename', 'delete', 'grep', 'showtrash'
                    ,'showhelp', 'sortcdate', 'sortname', 'sortmdate'
                    , 'sortsize')

_INTERACTIVE={'rofi':False, 'fzf':True}
_DEFAULT_CONFIG='~/.config/qn/config'
_DEFAULT_COMMAND = {}
_DEFAULT_COMMAND['rofi'] = ['rofi', '-sep', '\\0', '-columns', '1'
                , '-dmenu', '-i'
                , '-kb-custom-1', 'Alt+Shift+1' #remove previous bindings
                , '-kb-custom-2', 'Alt+Shift+2' #remove previous bindings
                , '-kb-custom-3', 'Alt+Shift+3' #remove previous bindings
                , '-kb-custom-4', 'Alt+Shift+4' #remove previous bindings
                ]
_DEFAULT_COMMAND['fzf'] = ['fzf'
                   ,'--read0'
                   ,'--print-query'
                   ,'--print0'
                   ,'--exact'
                   ,'--expect', 'alt-t'
                ]
_DEFAULT_HOTKEYS = {}
_DEFAULT_HOTKEYS['rofi'] = {
  'forcenew'  :['forcenew'  ,'Alt-Return' , 'Force Create New Note'],
  'delete'    :['delete'    ,'Alt-d'      , 'Delete Note'],
  'rename'    :['rename'    ,'Alt-space'  , 'Rename Note'],
  'grep'      :['grep'      ,'Alt-s'      , 'Grep Notes'],
  'showtrash' :['showtrash' ,'Alt-t'      , 'Show Trash'],
  'showhelp'  :['showhelp'  ,'Alt-h'      , 'Show Help'],
  'sortcdate' :['sortcdate' ,'Alt-2'      , 'Sort by Creation Date'],
  'sortname'  :['sortname'  ,'Alt-1'      , 'Sort By Name'],
  'sortmdate' :['sortmdate' ,'Alt-3'      , 'Sort by Modificatin Date'],
  'sortsize'  :['sortsize'  ,'Alt-4'      , 'Sort by Size'],
  }

_DEFAULT_HOTKEYS['fzf'] = {
  'forcenew'  :['forcenew'  ,'Alt-Return' , 'Force Create New Note'],
  'delete'    :['delete'    ,'Alt-d'      , 'Delete Note'],
  'rename'    :['rename'    ,'Alt-space'  , 'Rename Note'],
  'grep'      :['grep'      ,'Alt-s'      , 'Grep Notes'],
  'showtrash' :['showtrash' ,'Alt-t'      , 'Show Trash'],
  'addtag'    :['addtag'    ,'Alt-n'      , 'Add Tag to Note (Not Implemented)'],
  'showtagb'  :['showtagb'  ,'Alt-j'      , 'Show Note Tags (Not Implemented)'],
  'showtagm'  :['showtagm'  ,'Alt-k'      , 'Filter By Tags (Not Implemented)'],
  'showhelp'  :['showhelp'  ,'Alt-h'      , 'Show Help'],
  'sortname'  :['sortname'  ,'Alt-1'      , 'Sort By Name'],
  'sortcdate' :['sortcdate' ,'Alt-2'      , 'Sort by Creation Date'],
  'sortmdate' :['sortmdate' ,'Alt-3'      , 'Sort by Modificatin Date'],
  'sortsize'  :['sortsize'  ,'Alt-4'      , 'Sort by Size']
  }






class QnOptions():


    def __init__(self, app=None, qndir=None, run_parse_config = False, 
                 config_file_only = False):

        self.config_file_only = config_file_only
        self.__app = None
        self.__force_app = app
        self.__qndir = qndir
        self.__qndata = None
        self.__qntrash = None
        self.__options = {}
        self.__options['title_header'] = ''
        self.__options['title_suffix'] = ''
        self.__options['terminal'] = None
        self.__options['editor'] = None
        self.__options['launcher'] = None
        self.__options['help'] = None
        self.__options['position'] = None
        self.__options['filter'] = None
        self.__options['sortby'] = None
        self.__options['sortrev'] = None
        self.__options['command'] = None
        self.__options['command_extra'] = None
        self.__options['interactive'] = None
        self.__options['hotkeys'] = None

        if run_parse_config:
            self.parse_config()
        else:
            self.configure_defaults()


    def configure_defaults(self):

        if self.__force_app:
            self.__app = self.__force_app
        else:
            self.__app = 'rofi'

        if self.__app not in _IMPLEMENTED_APPS:
            print("Error: interface application, " + app 
                    + "not implemented.")
            sys.exit(1)

        if not self.__qndir:
            self.__qndir = os.path.expanduser(_DEFAULT_QNDIR)

        self.__qndata = os.path.join(self.__qndir, '.qn')
        self.__qntrash = os.path.join(self.__qndata, 'trash')

        self.__options['title_header'] = 'qn'
        self.__options['title_suffix'] = ':'


        self.__options['terminal'] = _FALLBACK_TERMINAL 
        self.__options['editor'] = _FALLBACK_EDITOR

        # Define application launcher
        if cmd_exists('rifle'):
            self.__options['launcher'] = 'rifle'
        else:
            self.__options['launcher'] = 'xdg-open'

        self.__options['help'] = None

        self.__options['position'] = None
        self.__options['filter'] = None

        self.__options['sortby'] = 'cdate'
        self.__options['sortrev'] = False



        self.__options['command'] = _DEFAULT_COMMAND[self.__app]
        self.__options['interactive'] = _INTERACTIVE[self.__app]

        self.__options['hotkeys'] = _DEFAULT_HOTKEYS[self.__app]

    def app(self):
        return(self.__app)

    def title(self, subtext=''):
        return(self.__options['title_header'] + subtext
                + self.__options['title_suffix'])

    def help(self):
        return(self.__options['help'])

    def position(self):
        return(self.__options['filter'])

    def filter(self):
        return(self.__options['filter'])

    def terminal(self):
        return(self.__options['terminal'])

    def editor(self):
        return(self.__options['editor'])

    def launcher(self):
        return(self.__options['launcher'])

    def sortby(self):
        return(self.__options['sortby'])
    
    def sortrev(self):
        return(self.__options['sortrev'])

    def command(self):
        command = self.__options['command']
        if self.__options['command_extra']:
            command.extend(self.__options['command_extra'])
        return(command)

    def interactive(self):
        return(self.__options['interactive'])

    def hotkeys(self):
        return(self.__options['hotkeys'])

    def QNDIR(self):
        return(self.__qndir)

    def QNDATA(self):
        return(self.__qndata)

    def QNTRASH(self):
        return(self.__qntrash)


    def set_title(self, title):
        self.__options['title_header'] = title

    def set_help(self, help_msg):
        self.__options['help'] = help_msg

    def set_position(self, position):
        self.__options['position'] = position

    def set_filter(self, new_filter):
        self.__options['filter'] = new_filter

    def set_sortby(self, sortby):
        self.__options['sortby'] = sortby

    def set_sortrev(self, sortrev):
        self.__options['sortrev'] = sortrev

    def set_interactive(self, interactive):
        self.__interactive = interactive


    def print_options(self):

        print("Interface App   =", self.__app)
        print("interactive     =", self.interactive())
        print()
        print("qndir           =", self.QNDIR())
        print("qndata          =", self.QNDATA())
        print("qntrash         =", self.QNTRASH())
        print()
        print("terminal        =", self.terminal())
        print("editor          =", self.editor())
        print("launcher        =", self.launcher())
        print()
        print("title           =", self.title())
        print("help            =", self.help())
        print("sortby          =", self.sortby())
        print("sortrev         =", self.sortrev())
        print("position        =", self.position())
        print("filter          =", self.filter())
        print()
        print("command         =", self.__options['command'])
        print("command_extra   =", self.__options['command_extra'])
        print()
        print("keyboard        = ...")

        print("    " + "".ljust(12) + "[command, keybinding, help]")
        for key,value in self.__options['hotkeys'].items():
            print("    " + str(key).ljust(12) + "" + str(value))


    def parse_config(self, argv=None): 

        default_config_path_expanded = os.path.expanduser(_DEFAULT_CONFIG)
        config_used=None

#        options = argument_parser()

        p = configargparse.ArgParser(default_config_files=[_DEFAULT_CONFIG])
        p.add('-c', '--config', is_config_file=True
                , help='config file path')
        p.add('-d', '--qndir', default='~/qn/', help='qn directory path')
        p.add('--terminal', default=_FALLBACK_TERMINAL
                , help='default terminal to use')
        p.add('--text-editor', default=_FALLBACK_EDITOR
                , help='default text editor to use')
        p.add('--default-interface', default='rofi'
                , help='default interface (rofi/fzf) to use')
        p.add('-r', default=False, action='store_true', help='run as rofi')
        p.add('-f', default=False, action='store_true', help='run as fzf')
        p.add('--interactive', default="default", help='if false, runs text editor' + 
                            ' from terminal (default/True/False)')
        p.add('--sortby', default='cdate'
                , help='type of default sorting (cdate, mdate, name, size)')
        p.add('--sortrev', default=False, help='reverse sorting (True/False)')
        p.add('--rofi-settings', default=False
                , help="rofi settings to append. Format as: '-width 1 -lines 15'"
                    + ", surround by '( )' if using command line argument"
                    + ". In config, exclude quotes.")
        p.add('--rofi-custom-command', default=False
                , help="define path to rofi command to use. e.g., /usr/bin/rofi")
        p.add('--fzf-custom-command', default=False
                , help="define path to fzf command to use. e.g., /usr/bin/fzf")
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

        if self.config_file_only:
            options = p.parse_known_args()[0]
        else:
            options = p.parse_args()


        if not os.path.isfile(default_config_path_expanded):
            if not options.config:
                print("Default config file not found at " 
                        + default_config_path_expanded + ", and no config file"
                        + " defined via -c.\n")
                config_used = 'defaults'
            else:
                config_used = options.config
        else:
            config_used = default_config_path_expanded

        # Check that in
        if options.default_interface not in _IMPLEMENTED_APPS:
            print("ERROR with config '" + config_used + "': default interface, " 
                + options.default_interface + " not implemented.")
            sys.exit(1)

        if options.r:
            self.__app = 'rofi'
        elif options.f:
            self.__app = 'fzf'
        else:
            if self.__force_app:
                self.__app = self.__force_app
            else:
                self.__app = options.default_interface

        if options.interactive == "default":
            self.__options['interactive'] = _INTERACTIVE[self.__app]
        else:
            self.__options['interactive'] = options.interactive

        self.__options['command'] = _DEFAULT_COMMAND[self.__app]
        self.__options['hotkeys'] = _DEFAULT_HOTKEYS[self.__app]

        if options.rofi_custom_command and self.__app == 'rofi':
            print(self.__options['command'])
            self.__options['command'][0] = options.rofi_custom_command
        if options.fzf_custom_command  and self.__app == 'fzf':
            self.__options['command'][0] = options.fzf_custom_command



        self.__qndir = os.path.expanduser(options.qndir)
        self.__qndata = os.path.join(self.__qndir, '.qn')
        self.__qntrash = os.path.join(self.__qndata, 'trash')

        command_extra = False
        keybindings_extra = False
        rofi_extra_settings = options.rofi_settings
        rofi_keybindings = options.rofi_keybindings
        if self.__app == 'rofi':
            if rofi_extra_settings:
                if rofi_extra_settings[0] == "(":
                    command_extra = rofi_extra_settings[1:-1]
                else:
                    command_extra = rofi_extra_settings
            if rofi_keybindings:
                if rofi_keybindings[0] == "(":
                    keybindings_extra = rofi_keybindings[1:-1]
                else:
                    keybindings_extra = rofi_keybindings
        fzf_extra_settings = options.fzf_settings
        fzf_keybindings = options.fzf_keybindings
        if self.app == 'fzf':
            if fzf_extra_settings:
                if fzf_extra_settings[0] == "(":
                    command_extra = fzf_extra_settings[1:-1]
                else:
                    command_extra = fzf_extra_settings
            if fzf_keybindings:
                if fzf_keybindings[0] == "(":
                    keybindings_extra = fzf_keybindings[1:-1]
                else:
                    keybindings_extra = fzf_keybindings
        if command_extra:
            self.__options['command_extra'] = command_extra.split()

        if keybindings_extra:
            for binding in keybindings_extra.split(';'):
                try:
                    commb,keyb = binding.split('=')
                except ValueError:
                    print("ERROR: Invalid binding '" + binding + "'.")
                    print("Use 'command;binding' syntax")
                    print("Ignoring binding")
                    continue

                self.__options['hotkeys'][commb][1] = keyb



        # Check if command used for terminal and text editors exist
        if not cmd_exists(options.terminal):
            print("WARNING with config '" + config_used + "': terminal app, "
                    + options.terminal + " is not installed. Using default.")
            self.__options['terminal'] = _FALLBACK_TERMINAL
        else:
            self.__options['terminal'] = options.terminal

        if not cmd_exists(options.text_editor):
            print("WARNING with config '" + config_used + "': text editor app, "
                    + options.text_editor + " is not installed. Using default.")
            self.__options['editor'] = _FALLBACK_EDITOR
        else:
            self.__options['editor'] = options.text_editor

        # Define application launcher
        if cmd_exists('rifle'):
            self.__options['launcher'] = 'rifle'
        else:
            self.__options['launcher'] = 'xdg-open'


        if options.sortby not in _SORT_OPTS:
            print("WARNING with config '" + config_used + "': sorty option, "
                    + options.sortby + " is not valid. Using cdate")
            self.__options['sortby'] = 'cdate'
        else:
            self.__options['sortby'] = options.sortby

        self.__options['sortrev'] = (options.sortrev == 'True')


    def check_environment(self):

        # This needs to be more robust
        QNDIR = self.QNDIR()
        QNDATA = self.QNDATA()
        QNTRASH = self.QNTRASH()
        # Make sure everything is ready for qn
        if os.path.exists(QNDIR):
            if os.path.isfile(QNDIR):
                print("ERROR: path '" + QNDIR 
                        + "' exists but is a file. Exiting...")
                sys.exit(1)
        else:
            HELP_MSG = " Do you want to create the qn directory: " + QNDIR + "?"

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
        # FOR TAGS
        #if not os.path.isfile(_TAGF_PATH):
        #    tagfile = open(_TAGF_PATH, 'wb')
        #    pickle.dump({'__taglist':[]}, tagfile)
        #    tagfile.close()


    def gen_instance_args(self, instance, alt_help=None
                                    , alt_title=None):


        if alt_help:
            helpn = alt_help
        else:
            helpn = self.help()
        if alt_title:
            titlen = alt_title
        else:
            titlen = self.title()

        appname = self.__app
        arguments = []
        if instance == 'default':
            if appname == 'rofi':
                arguments.extend(['-mesg', helpn
                                , '-format', 'f;s;i'
                                ,'-p', titlen])
                if self.filter():
                    arguments.extend(['-filter', self.filter()])
                if self.position():
                    arguments.extend(['-selected-row', self.position()])

            elif appname == 'fzf':
                arguments.extend(['--header', helpn
                                ,'--prompt', titlen])
                if self.filter():
                    arguments.extend(['-filter', self.filter()])

        return(arguments)






# Check if program exists - linux only
def cmd_exists(cmd):


    return call("type " + cmd, shell=True, 
        stdout=PIPE, stderr=PIPE) == 0




if __name__ == '__main__':
    qno = QnOptions(run_parse_config=True)
    print(qno.print_options())

