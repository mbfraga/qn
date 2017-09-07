"""Parse configuration for qn"""

import os
import sys
from subprocess import Popen,PIPE, call
import configargparse

import qn.hotkey_manager


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


def cmd_exists(cmd):
    """Check if a program exists in PATH. Linux only."""
    return call("type " + cmd, shell=True, 
        stdout=PIPE, stderr=PIPE) == 0


class QnOptions():
    """Class that handles options for qn that may be set by default, via a
    config file, or via command line arguments.

    Keyword arguments:
        app -- launcher application name, 'rofi' or 'fzf' (default None).
        qndir -- path to the directory holding the notes (default None).
        run_parse_config -- whether or not to parse config file and command 
                            line arguments when class is initialized. This can
                            be done later. (default False)
        config_file_only -- only parse config file, everything else will be set
                            to defaults. (default False)
    """
    def __init__(self, app=None, qndir=None, run_parse_config = False, 
                 config_file_only = False):

        self.config_file_only = config_file_only
        self.__app = None
        self.__force_app = app
        self.__qndir = qndir
        self.__qndata = None
        self.__qntrash = None
        self.__options = {}
        self.__options['prompt_header'] = ''
        self.__options['prompt_suffix'] = ''
        self.__options['terminal'] = None
        self.__options['editor'] = None
        self.__options['opener'] = None
        self.__options['help'] = None
        self.__options['selected_row'] = None
        self.__options['filter'] = None
        self.__options['sorttype'] = None
        self.__options['sortrev'] = None
        self.__options['command'] = None
        self.__options['command_extra'] = None
        self.__options['interactive'] = None
        self.__options['hotkeys'] = None

        if run_parse_config:
            self.configure_defaults()
            self.parse_config()
        else:
            self.configure_defaults()

    def configure_defaults(self):
        """Configure options using default values."""
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

        self.__options['prompt_header'] = 'qn'
        self.__options['prompt_suffix'] = ':'


        self.__options['terminal'] = _FALLBACK_TERMINAL 
        self.__options['editor'] = _FALLBACK_EDITOR

        # Define file opener (
        if cmd_exists('rifle'):
            self.__options['opener'] = 'rifle'
        else:
            self.__options['opener'] = 'xdg-open'

        self.__options['help'] = None

        self.__options['selected_row'] = None
        self.__options['filter'] = None

        self.__options['sorttype'] = 'cdate'
        self.__options['sortrev'] = False



        self.__options['command'] = _DEFAULT_COMMAND[self.__app]
        self.__options['interactive'] = _INTERACTIVE[self.__app]

        self.__options['hotkeys'] = _DEFAULT_HOTKEYS[self.__app]

    @property
    def app(self):
        return(self.__app)

    @property
    def prompt(self, subtext=''):
        print(self.__options['prompt_header'])
        return(self.__options['prompt_header'] + subtext
                + self.__options['prompt_suffix'])

    @property
    def help(self):
        return(self.__options['help'])

    @property
    def selected_row(self):
        return(self.__options['selected_row'])

    @property
    def filter(self):
        return(self.__options['filter'])

    @property
    def terminal(self):
        return(self.__options['terminal'])

    @property
    def editor(self):
        return(self.__options['editor'])

    @property
    def opener(self):
        return(self.__options['opener'])

    @property
    def sorttype(self):
        return(self.__options['sorttype'])
    
    @property
    def sortrev(self):
        return(self.__options['sortrev'])

    @property
    def command(self):
        command = self.__options['command']
        if self.__options['command_extra']:
            command.extend(self.__options['command_extra'])
        return(command)

    @property
    def interactive(self):
        return(self.__options['interactive'])

    @property
    def hotkeys(self):
        return(self.__options['hotkeys'])

    @property
    def qndir(self):
        return(self.__qndir)

    @property
    def qndata(self):
        return(self.__qndata)

    @property
    def qntrash(self):
        return(self.__qntrash)

    def set_terminal(self, terminal):
        self.__options['terminal'] = terminal

    def set_prompt(self, prompt):
        self.__options['prompt_header'] = prompt

    def set_help(self, help_msg):
        self.__options['help'] = help_msg

    def set_selected_row(self, selected_row):
        self.__options['selected_row'] = selected_row

    def set_filter(self, new_filter):
        self.__options['filter'] = new_filter

    def set_sorttype(self, sorttype):
        self.__options['sorttype'] = sorttype

    def set_sortrev(self, sortrev):
        self.__options['sortrev'] = sortrev

    def set_interactive(self, interactive):
        self.__options['interactive'] = interactive


    def print_options(self):
        """Print options list. Usually for debugging."""
        print("Interface App   =", self.__app)
        print("interactive     =", self.interactive)
        print()
        print("qndir           =", self.qndir)
        print("qndata          =", self.qndata)
        print("qntrash         =", self.qntrash)
        print()
        print("terminal        =", self.terminal)
        print("editor          =", self.editor)
        print("opener          =", self.opener)
        print()
        print("prompt          =", self.prompt)
        print("help            =", self.help)
        print("sorttype          =", self.sorttype)
        print("sortrev         =", self.sortrev)
        print("selected_row    =", self.selected_row)
        print("filter          =", self.filter)
        print()
        print("command         =", self.__options['command'])
        print("command_extra   =", self.__options['command_extra'])
        print()
        print("keyboard        = ...")

        print("    " + "".ljust(12) + "[command, keybinding, help]")
        for key,value in self.__options['hotkeys'].items():
            print("    " + str(key).ljust(12) + "" + str(value))


    def parse_config(self, argv=None): 
        """Parse config file and command line arguments."""
        default_config_path = os.path.expanduser(_DEFAULT_CONFIG)
        if not os.path.isfile(default_config_path):
            default_config_path = os.path.abspath('/etc/qn/config.example')
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
        p.add('--interactive', default="default", help='if False, runs text editor' + 
                            ' from terminal (default/True/False)')
        p.add('--sorttype', default='cdate'
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
                    + " command=keybinding; e.g., forcenew=alt-Return;rename=alt-space."
                    + " Possible commands: forcenew,rename,delete,grep,showtrash"
                    + " ,showhelp,sortcdate,sortname,sortmdate,sortsize")
        p.add('--fzf-keybindings', default=False, help="define keybindings. Format as:"
                    + " command=keybinding; e.g., forcenew=alt-Return;rename=alt-space."
                    + " Possible commands: forcenew,rename,delete,grep,showtrash"
                    + " ,showhelp,sortcdate,sortname,sortmdate,sortsize")

        if self.config_file_only:
            options = p.parse_known_args()[0]
        else:
            options = p.parse_args()

        if not os.path.isfile(default_config_path):
            if not options.config:
                print("Default config file not found at " 
                        + default_config_path + ", and no config file"
                        + " defined via -c.\n")
                config_used = 'defaults'
            else:
                config_used = options.config
        else:
            config_used = default_config_path

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

        # Define file opener
        if cmd_exists('rifle'):
            self.__options['opener'] = 'rifle'
        else:
            self.__options['opener'] = 'xdg-open'


        if options.sorttype not in _SORT_OPTS:
            print("WARNING with config '" + config_used + "': sorty option, "
                    + options.sorttype + " is not valid. Using cdate")
            self.__options['sorttype'] = 'cdate'
        else:
            self.__options['sorttype'] = options.sorttype

        self.__options['sortrev'] = (options.sortrev == 'True')


    def check_environment(self):
        """Check environment to make sure that everything needed for qn is
        there.
        """
        # This needs to be more robust
        qndir = self.qndir
        qndata = self.qndata
        qntrash = self.qntrash
        # Make sure everything is ready for qn
        if os.path.exists(qndir):
            if os.path.isfile(qndir):
                print("ERROR: path '" + qndir 
                        + "' exists but is a file. Exiting...")
                sys.exit(1)
        else:
            HELP_MSG = " Do you want to create the qn directory: " + qndir + "?"

            s = input(HELP_MSG + " (y/N) ")
            if s and (s[0] == "Y" or s[0] == "y"):
                print("Creating directory: " + qndir + "...")
                os.makedirs(qndir)
            else:
                print("qn directory" + qndir + " does not exist. Exiting...")
                sys.exit(1)

        if not os.path.exists(qndata):
            print("Creating directory: " + qndata + "...")
            os.makedirs(qndata, exist_ok=True)
        if not os.path.exists(qntrash):
            print("Creating directory: " + qntrash + "...")
            os.makedirs(qntrash, exist_ok=True)
        # FOR TAGS
        #if not os.path.isfile(_TAGF_PATH):
        #    tagfile = open(_TAGF_PATH, 'wb')
        #    pickle.dump({'__taglist':[]}, tagfile)
        #    tagfile.close()


    def gen_instance_args(self, instance, alt_help=None
                                    , alt_prompt=None):
        """Generate CLI arguments for fzf or rofi.
        Keyword arguments:
        alt_help -- string that will be used as an alternative help message for
                    the instance (default None).
        alt_prompt -- string that will be used as an alternative prompt for the
                    instance (default None).
        """
        if alt_help is not None:
            helpn = alt_help
        else:
            helpn = self.help
        if alt_prompt is not None:
            promptn = alt_prompt
        else:
            promptn = self.prompt

        appname = self.__app
        arguments = []
        if instance == 'default':
            if appname == 'rofi':
                arguments.extend(['-mesg', helpn
                                , '-format', 'f;s;i'
                                ,'-p', promptn])
                if self.filter:
                    arguments.extend(['-filter', self.filter])
                if self.selected_row:
                    arguments.extend(['-selected-row', self.selected_row])

            elif appname == 'fzf':
                arguments.extend(['--header', helpn
                                ,'--prompt', promptn])
                if self.filter:
                    arguments.extend(['-filter', self.filter])

        return(arguments)
