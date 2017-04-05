import os
import sys
from subprocess import Popen,PIPE, call
import struct
import config_parse

import qn
import hotkey_manager as hk


COLS = 1


class QnAppRF(qn.QnApp):


    def call_command(self, entries, additional_args=[]):


        proc = Popen(self.options.command() + additional_args
                     , stdin=PIPE, stdout=PIPE)
        for e in entries:
            proc.stdin.write((e).encode('utf-8'))
            proc.stdin.write(struct.pack('B', 0))
        proc.stdin.close()
        answer = proc.stdout.read().decode("utf-8") 
        exit_code = proc.wait()

        if answer == '':
            return(None, exit_code)

        if self.options.app() == 'fzf':
            answer = answer.split('\x00')
        else:
            answer = answer.strip('\n').split(';')

        return(answer, exit_code)


    def show_note_select(self, instance, additional_args=[]):

        appname = self.options.app()
        if appname == 'rofi':
            applist = self.file_repo[instance].lines()
        elif appname == 'fzf':
            applist = self.file_repo[instance].filenames()
        else:
            print("ERROR: appname '" + appname + "' not implemented")

        proc = Popen(self.options.command() + additional_args, stdin=PIPE
                    , stdout=PIPE)

        for e in applist:
            proc.stdin.write((e).encode('utf-8'))
            proc.stdin.write(struct.pack('B', 0))
        proc.stdin.close()
        answer = proc.stdout.read().decode("utf-8") 
        exit_code = proc.wait()

        if answer == '':
            return(False)

        if appname == 'rofi':
            answer = answer.strip('\n').split(';')
            if not answer:
                return(False)
            if answer[0].strip():
                FILTER = answer[0]
            else:
                FILTER = None
            POS = int(answer[2])
            if POS == -1:
                NOTE = None
            else:
                NOTE = self.file_repo[instance].file_list[POS]['name'].strip()
            if exit_code == 0:
                KEY = None
                OPTSEL = None
            else:
                KEY = True
                if self.hkman:
                    OPTSEL = self.hkman[instance].get_opt(exit_code)
        elif appname == 'fzf':
            answer = answer.split('\x00')
            if not answer:
                return(False)
            if len(answer) < 4:
                FILTER, KEY, MISC = answer[0:3]
                NOTE = None
            else:
                FILTER, KEY, NOTE, MISC = answer
                NOTE = NOTE.strip()
            FILTER = FILTER.strip()
            KEY = KEY.strip()
            if not FILTER:
                FILTER = None
            if KEY:
                if instance in self.hkman:
                    OPTSEL = self.hkman[instance].get_opt(KEY)
                else:
                    OPTSEL = None
            else:
                OPTSEL = None
            POS = None
        else:
            print('Appname "' + appname + '"not implemented.')
            return(False)

        return(NOTE, FILTER, OPTSEL)


    def show_default(self):

        instance = 'default'
        if instance not in self.hkman:
            hkeys = self.options.hotkeys()
            self.hkman['default'] = hk.HotkeyManager(app=self.options.app())
            self.hkman['default'].add_key(*hkeys['forcenew'])
            self.hkman['default'].add_key(*hkeys['delete'])
            self.hkman['default'].add_key(*hkeys['rename'])
            self.hkman['default'].add_key(*hkeys['grep'])
            self.hkman['default'].add_key(*hkeys['showtrash'])
            self.hkman['default'].add_key(*hkeys['showhelp'])
            self.hkman['default'].add_key(*hkeys['sortname'])
            self.hkman['default'].add_key(*hkeys['sortcdate'])
            self.hkman['default'].add_key(*hkeys['sortmdate'])
            self.hkman['default'].add_key(*hkeys['sortsize'])

        hotkey_args = self.hkman[instance].generate_hotkey_args()

        if instance not in self.file_repo:
            self.file_repo[instance] = qn.FileRepo(self.options.QNDIR())
            self.file_repo[instance].scan_files()

        self.file_repo[instance].sort(self.options.sortby()
                                    , self.options.sortrev())

        MESG = 'Press "'  + self.options.hotkeys()['showhelp'][1]
        MESG += '" to see a list of hotkeys.'
        if self.options.help():
            MESG += self.options.help()
        MESG += ' Sorted by: ' + self.options.sortby() 

        if self.options.sortrev():
            MESG += ' [v]'
        else:
            MESG += ' [^]'


        extra_args = self.options.gen_instance_args(instance, alt_help=MESG)
        extra_args.extend(hotkey_args)

        ANSWER = self.show_note_select(instance, extra_args)
        if not ANSWER:
            return(0)

        NOTE, FILTER, OPTSEL = ANSWER

        print(NOTE,'|', FILTER,'|', OPTSEL)
        if not OPTSEL:
            if not NOTE:
                print("Creating file from filter...")
                self.new_note(FILTER)
                return(0)
            else:
                path=os.path.join(self.options.QNDIR(), NOTE)
                print('path', path)
                if os.path.isfile(path):
                    print("file found, editing...")
                    self.open_note(NOTE)
                    return(0)
                else:
                    print("file not found, create...")
                    self.new_note(FILTER)
                    return(0)

        if OPTSEL == 'delete':
            self.show_delete(NOTE)
        elif OPTSEL == 'rename':
            self.show_rename(NOTE)
        elif OPTSEL == 'showtrash':
            self.show_trash()
        elif OPTSEL == 'forcenew':
            if not FILTER.strip():
                sys.exit(0)
            self.force_new_note(FILTER)
        elif OPTSEL == 'grep':
            if not FILTER:
                self.show_default()
            else:
                self.show_filtered(self.file_repo['default'], FILTER)
    #   # elif OPTSEL == 'addtag':
    #   #     print('Add Tag to Note')
    #   # elif OPTSEL == 'showtagb':
    #   #     print('Browse Tags')
    #   # elif OPTSEL == 'showtagm':
    #   #     print('Show Note Tags')
        elif OPTSEL == 'showhelp':
            self.show_help(enter_help="Create/Edit note")
        if OPTSEL == 'sortname':
            self.show_sorted_default('name', True)
        elif OPTSEL == 'sortcdate':
            self.show_sorted_default('cdate')
        elif OPTSEL == 'sortmdate':
            self.show_sorted_default('mdate')
        elif OPTSEL == 'sortsize':
            self.show_sorted_default('size')


    def show_sorted_default(self, sortby, default_sortrev=False):
        if self.options.sortby() == sortby:
            self.options.set_sortrev(not self.options.sortrev())
        else:
            self.options.set_sortrev(default_sortrev)
        self.options.set_sortby(sortby)
        self.show_default()



    def show_yesno(self, MESG, TITLE='qn dialog: '):


        HELP = "<span color=\"red\">"
        HELP += MESG
        HELP += "</span>"
        appname = self.options.app()

        extra_args = self.options.gen_instance_args('default', alt_help=MESG
                                          , alt_title=TITLE)
        ANS, val = self.call_command(['no', 'yes'], extra_args)

        if not ANS:
            sys.exit(0)

        if appname == 'rofi':
            return(ANS[1] == 'yes')
        elif appname == 'fzf':
            return(ANS[2] == 'yes')
        else:
            print("App " + appname + " not implemented.")
            return(False)


    def show_delete(self, note):


        MESG = "Are you sure you want to delete \"" + note + "\"?"

        if self.show_yesno(MESG, 'qn delete:'):
            print("Deleting " + note + "...")
            self.delete_note(note)
        else:
            print("Deletion of \"" + note + "\" cancelled.")


    def show_undelete(self, note):


        MESG = "Are you sure you want to restore \"" + note + "\"?"
        if self.show_yesno(MESG, 'qn undelete:'):
            print("Restoring " + note + "...")
            self.undelete_note(note)
        else:
            print("Restoration of \"" + note + "\" cancelled.")


    def show_rename(self, note):


        MESG = "Please write the new name for this file"

        extra_args = self.options.gen_instance_args('default'
                                , alt_help=MESG, alt_title="qn rename: ")
        if self.options.app() == 'rofi':
            extra_args.extend(['-filter', note])
        elif self.options.app() == 'fzf':
            extra_args.extend(['--query', note])

        ANS, val = self.call_command([''], extra_args)

        if (ANS == None):
            sys.exit(1)

        print(ANS)

        YESNO_MSG = "Are you sure you want to rename '" + note.strip()
        YESNO_MSG += "' to '" + ANS[0].strip() + "'?"
        if self.show_yesno(YESNO_MSG, 'qn rename: '):
            self.move_note(note.strip(), ANS[0].strip())
        else:
            print("Doing Nothing.")
            sys.exit(0)


    def show_trash(self):


        instance = 'trash'
        if instance not in self.hkman:
            self.hkman[instance] = hk.HotkeyManager(self.options.app())
            self.hkman[instance].add_key(*self.options.hotkeys()['showtrash'])
            self.hkman[instance].add_key(*self.options.hotkeys()['showhelp'])
        hotkey_args = self.hkman[instance].generate_hotkey_args()

        MESG = 'Press enter to restore file. "'
        MESG += self.hkman[instance].get_keybinding('showtrash')
        MESG += '" to go back to qn.'

        if instance not in self.file_repo:
            self.file_repo[instance] = qn.FileRepo(self.options.QNTRASH())
            self.file_repo[instance].scan_files()
        self.file_repo[instance].sort('cdate')
        applist = self.file_repo[instance].filenames()

        extra_args = self.options.gen_instance_args('default'
                                        , alt_help=MESG, alt_title='qn trash: ')
        extra_args.extend(hotkey_args)

        ANSWER = self.show_note_select(instance, extra_args)
        if not ANSWER:
            return(0)
        NOTE, FILTER, OPTSEL = ANSWER
        if not OPTSEL:
            if not NOTE:
                return(0)
            else:
                self.show_undelete(NOTE)
        if OPTSEL == 'showtrash':
            self.show_default()



    def show_filtered(self,file_repo, FILTER):

        instance='filtered'
        if instance not in self.hkman:
            self.hkman[instance] = hk.HotkeyManager(self.options.app())
            self.hkman[instance].add_key(*self.options.hotkeys()['grep'])
        hotkey_args = self.hkman[instance].generate_hotkey_args()


        MESG = "List of notes filtered for '" + FILTER + "'."
        MESG += " Press '" + self.hkman[instance].get_keybinding('grep')
        MESG += "' to go back to qn."
        TITLE = 'qn search: '

        extra_args = self.options.gen_instance_args('default'
                                        , alt_help=MESG, alt_title=TITLE)
        extra_args.extend(hotkey_args)



        filters = FILTER.strip().split(" ")
        filtered_repo = file_repo

        if not FILTER:
            self.show_default()
        for f in filters:
            filtered_repo = file_repo.grep_files(f)

        self.file_repo[instance] = filtered_repo
        self.file_repo[instance].lineformat = ['name', 'misc']

        ANSWER = self.show_note_select(instance, extra_args)

        if not ANSWER:
            return(0)

        print(ANSWER)
        NOTE, FILTER, OPTSEL = ANSWER


        if not OPTSEL:
            if not NOTE:
                print("Creating file from filter...")
                self.new_note(FILTER)
                return(0)
            else:
                path=os.path.join(self.options.QNDIR(), NOTE)
                if os.path.isfile(path):
                    print("file found, editing...")
                    self.open_note(NOTE)
                    return(0)
                else:
                    print("file not found, create...")
                    self.new_note(FILTER)
                    return(0)


        if OPTSEL == 'grep':
            if not FILTER:
                self.show_default()
            else:
                self.show_filtered(FILTER)


    def show_help(self, enter_help):

        instance = 'help'
        if instance not in self.hkman:
            self.hkman[instance] = hk.HotkeyManager(self.options.app())
            self.hkman[instance].add_key(*self.options.hotkeys()['showhelp'])
        hotkey_args = self.hkman[instance].generate_hotkey_args()


        MESG = "List of options and corresponding keybindings."
        MESG += " Press '" + self.hkman[instance].get_keybinding('showhelp') 
        MESG += "' to go back to qn."

        TITLE = 'qn help: '

        extra_args = self.options.gen_instance_args('default'
                                        , alt_help=MESG, alt_title=TITLE)
        extra_args.extend(hotkey_args)

        help_lines = self.hkman['default'].generate_help(enter_help)
        ANSWER = self.call_command(help_lines, extra_args)

        if not ANSWER:
            return(0)
        if not ANSWER[0]:
            sys.exit(0)
        else:
            self.show_default()



if __name__ == '__main__':
    qnopts = config_parse.QnOptions(run_parse_config=True)
    qnopts.check_environment()

    qnrf = QnAppRF(qnopts)
    qnrf.show_default()

