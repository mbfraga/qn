IMPLEMENTED_APPS = ['rofi', 'fzf']
class HotkeyManager:
    """Class that is able to store hotkeys which can be sent to rofi or fzf. It
    helps handle hotkeys for both applications to be used in the same script
    """
    def __init__(self, app='rofi'):

        if app not in IMPLEMENTED_APPS:
            raise ValueError('App %r not implemented.' % (app))
        else:
            self.app = app

        self.keys = []
        self.__hotkey_ct = 19

    def add_key(self, optname, keybinding, keyhelp=''):
        """Add a hotkey.

        Keyword arguments:
        optname -- Name of option, used as a keyword to point to a hotkey.
        keybinding -- Keybinding tied to this optname.
        keyhelp -- String with help information that can then be used to
                   generate a nice list of hotkeys and what they do.
                   (default '')
        """
        if self.app == 'rofi':
            if self.__hotkey_ct < 1:
                print('Too many keybindings. Key"' +  optname + '" not added.')
                return(False)
        keyprops = {}
        keyprops['optname'] = optname
        keyprops['keybinding'] = keybinding
        keyprops['keyhelp'] = keyhelp
        keyprops['keyval'] = self.__hotkey_ct+9
        self.keys.append(keyprops)
        if self.app == 'rofi':
            self.__hotkey_ct -= 1

    def get_opt(self, val):
        """Get the optname of a hotkey from its value. Rofi and fzf generate
        different values.
        """
        if self.app == 'rofi':
            for key in self.keys:
                if val == key['keyval']:
                    return(key['optname'])

            print("No keybinding set to -kb-custom-" + str(val-9) + ".")
            return(None)

        elif self.app == 'fzf':
            for key in self.keys:
                if val == key['keybinding']:
                    return(key['optname'])

    def get_keybinding(self, optname):
        for key in self.keys:
            if key['optname'] == optname:
                return key['keybinding']
        return(None)

    def generate_hotkey_args(self):
        """Generate command line arguments for fzf or rofi, depending on what
        application is enabled."""
        hotkey_args = []
        if self.app == 'rofi':
            for key in self.keys:
                arg_string = '-kb-custom-' + str(key['keyval']-9)
                hotkey_args.extend([arg_string, key['keybinding']])
            return(hotkey_args)

        elif self.app == 'fzf':
            hotkey_args.append('--expect')
            keys_string = None
            for key in self.keys:
                if not keys_string:
                    keys_string = key['keybinding']
                else:
                    keys_string += ',' + key['keybinding']
            hotkey_args.append(keys_string)
            return(hotkey_args)

    def generate_help(self, enter_help=None):
        """Generate a list of help strings, each corresponding to a hotkey. The
        enter_help keyword argument can be used to set a help entry for the 
        "Enter" (or "Return") key.
        """
        help_padding = 35
        help_lines = []
        if enter_help:
            line = enter_help + ":"
            line = line.ljust(help_padding)
            line += 'Enter'
            help_lines.append(line)
        for key in self.keys:
            line = ""
            line += key['keyhelp'] + ":"
            line = line.ljust(help_padding)
            line +=  key['keybinding']
            help_lines.append(line)

        return(help_lines)

