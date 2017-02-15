


IMPLEMENTED_APPS = ['rofi', 'fzf']
class HotkeyManager:
    def __init__(self, app='rofi'):

        if app not in IMPLEMENTED_APPS:
            raise ValueError('App %r not implemented.' % (app))
        else:
            self.app = app

        self.keys = []
        self.hotkey_ct = 19

    def add_key(self, optname, keybinding, keyhelp=''):
        if self.app == 'rofi':
            if self.hotkey_ct < 1:
                print('Too many keybindings. Key"' +  optname + '" not added.')
                return(False)
        keyprops = {}
        keyprops['optname'] = optname
        keyprops['keybinding'] = keybinding
        keyprops['keyhelp'] = keyhelp
        keyprops['keyval'] = self.hotkey_ct+9
        self.keys.append(keyprops)
        if self.app == 'rofi':
            self.hotkey_ct -= 1

    def get_opt(self, val):
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


hk = HotkeyManager('rofi')


