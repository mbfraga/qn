import os
import configargparse


def parse_config(): 
    default_config_path = '~/.config/qn/config2'
    default_config_path_expanded = os.path.join(os.path.expanduser("~"), 
                                                ".config/qn/config2")
    p = configargparse.ArgParser(default_config_files=[default_config_path])
    p.add('-c', '--config', is_config_file=True
            , help='config file path')
    p.add('-d', '--qndir', default='~/qn/', help='qn directory path')
    p.add('--terminal', default='xterm', help='default terminal to use')
    p.add('--text-editor', default='vim', help='default text editor to use')
    p.add('--default-interface', default='rofi'
            , help='default interface (rofi/fzf) to use')
    p.add('--sortby', default='cdate'
            , help='type of default sorting (cdate, mdate, name, size)')
    p.add('--sortrev', default=False, help='reverse sorting (True/False)')
    p.add('--rofi-settings', default=False
            , help="rofi settings to append. Format as: '(-width 1 -lines 15)'"
                + ", quotes included")
    p.add('--fzf-settings', default=False
            , help="rofi settings to append. Format as: '(--height=100; --border)'"
                + ", quotes included")
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
                    + " defined via -c. Using default values.")

    return(options)


options = parse_config()
print(options)
print("----------")
print('config:', options.config)
print('qndir:', options.qndir)
print('terminal:', options.terminal)
print('text-editor:', options.text_editor)
print('default-interface:', options.default_interface)
print('sortby:', options.sortby)
print('sortrev:', options.sortrev)
print('rofi-settings:', options.rofi_settings)
print('fzf-settings:', options.fzf_settings)
