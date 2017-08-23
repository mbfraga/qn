#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import time
timea = time.time()
import os
import sys
import argparse
from subprocess import Popen,PIPE, call
import pickle
from datetime import datetime
import mimetypes
from stat import ST_CTIME, ST_ATIME, ST_MTIME, ST_SIZE
from operator import itemgetter

import config_parse
import hotkey_manager


QNDIR=''


# Check if program exists - linux only
def cmd_exists(cmd):


    return call("type " + cmd, shell=True, 
        stdout=PIPE, stderr=PIPE) == 0


def file_mime_type(filename):


    mtype,menc = mimetypes.guess_type(filename)
    # If type is not detected, just open as plain text
    if not mtype:
        mtype = 'None/None'
    return(mtype)


def file_mime_type_bash(filepath): # This is more reliable it seems...
        proc = Popen(['xdg-mime', 'query', 'filetype', filepath]
                     , stdout=PIPE)
        mtype = proc.stdout.read().decode('utf-8')
        exit_code = proc.wait()
        if not mtype:
            mtype = 'None/None'

        return(mtype)


def terminal_open(terminal, command, title=None):
    if not title:
        title = 'qn: ' + terminal
    else:
        title = 'qn: ' + title

    if terminal in ['urxvt', 'xterm', 'gnome-terminal']:
        generated_command = terminal + ' -title "' + title + '"'
    elif terminal in ['termite', 'xfce-terminal']:
        generated_command = terminal + ' --title "' + title + '"'
    else:
        generated_command = terminal + ' -T "' + title + '"'

    os.system(generated_command + " -e " + command)


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)


class FileRepo:
    def __init__(self, dirpath=None):
        self.__path = os.path.join(dirpath, "")
        self.__path_len = len(self.__path)
        self.__file_list = []    # list of files - dicts
        self.__pfile_list = []  # list of pinned files - dicts
        self.__pinned_filenames = [] #List of filenames that will be pinned 
        self.sorttype = "none"
        self.sortrev = False

        self.__filecount = 0
        self.__pfilecount = 0

        self.__tags = None

        self.__lineformat = ['name', 'cdate']
        self.__linebs = {}
        self.__linebs['name'] = 40
        self.__linebs['adate'] = 18
        self.__linebs['cdate'] = 18
        self.__linebs['mdate'] = 18
        self.__linebs['size'] = 15
        self.__linebs['misc'] = 100
        self.__linebs['tags'] = 50


    # Scans the directory for files and populates the file list and linebs
    def scan_files(self):
        self.__filecount = 0
        self.__pfilecount = 0
        pintot = len(self.__pinned_filenames)
        if pintot != 0:
            temp_pinned_filenames = list(self.__pinned_filenames)
        else:
            temp_pinned_filenames = False

        for root, dirs, files in os.walk(self.__path, topdown=True):
            for name in files:
                fp = os.path.join(root, name)
                fp_rel = fp[self.__path_len:]

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

                if temp_pinned_filenames:
                    if name in temp_pinned_filenames:
                        temp_pinned_filenames.remove(name)
                        self.__pfile_list.append(file_props)
                        self.__pfilecount += 1
                        continue

                    self.__file_list.append(file_props)
                    self.__filecount += 1
                    continue

                #if name in self.pinned_filenames:
                #    self.__pfile_list.append(file_props)
                #    self.__pfilecount += 1
                #else:
                #    self.__file_list.append(file_props)
                #    self.__filecount += 1
                self.__file_list.append(file_props)
                self.__filecount += 1


    def add_file(self, filepath, misc_prop=None):
        if not os.path.isfile(filepath):
            print(filepath + " is not a file.")
            return

        fp_rel = filepath[self.__path_len:]

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

        self.__file_list.append(file_props)
        self.__filecount += 1


    def sort(self, sortby='name', sortrev=False):
        if sortby not in ['size', 'adate', 'mdate', 'cdate', 'name']:
            print("Key '" + sortby + "' is not valid.")
            print("Choose between size, adate, mdate, cdate or name.")

        self.__file_list = sorted(self.__file_list, 
                            key=itemgetter(sortby), reverse=not sortrev)
        self.sorttype=sortby
        self.sortrev=sortrev

    def get_property_list(self, prop='name', pinned_first=True):
        if pinned_first:
            plist = list(itemgetter(prop)(filen) for filen in self.__file_list)
            plist += list(itemgetter(prop)(filen) for filen in self.__pfile_list)
        else:
            plist = list(itemgetter(prop)(filen) for filen in self.__pfile_list)
            plist += list(itemgetter(prop)(filen) for filen in self.__file_list)
        return(plist)

    def filenames(self, pinned_first=True):
        return(self.get_property_list('name', pinned_first))

    def filepaths(self, pinned_first=True):
        return(self.get_property_list('fullpath', pinned_first))

    def filecount(self, include_normal=True, include_pinned=True):
        return(self.__filecount + self.__pfilecount)
        
    def set_lineformat(self, new_lineformat):
        self.__lineformat = new_lineformat

    def lines(self, format_list=None, pinned_first=True):
        lines = []
        if not format_list:
            format_list = self.__lineformat
        for filen in self.__file_list:
            line = ""
            for formatn in format_list:
                if formatn in ['adate', 'mdate', 'cdate']:
                    block = datetime.utcfromtimestamp(filen[formatn])
                    block = block.strftime('%d/%m/%Y %H:%M')
                elif formatn == 'size':
                    size=filen[formatn]
                    block = sizeof_fmt(size)
                else:
                    block = str(filen[formatn])

                blocksize = self.__linebs[formatn]
                if len(block) >= blocksize:
                    block = block[:blocksize-2] + '…'

                block = block.ljust(blocksize)
                line += block

            lines.append(line)

        return(lines)

    def pin_files(self, filelist_topin):
        self.__pinned_filenames = filelist_topin
        return(1)


    def grep_files(self, filters_string):
        if not self.__file_list:
            print("No files added to file repo")
            return(1)

        proc = Popen(['grep', '-i', '-I', filters_string] + self.filepaths() 
                     , stdout=PIPE)
        answer = proc.stdout.read().decode('utf-8')
        exit_code = proc.wait()

        grep_file_repo = FileRepo(self.__path)
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





class QnApp ():
    # Must pass class of type QnOptions
    def __init__(self, qnoptions):
        self.__options = qnoptions
        self.__app = qnoptions.app()
        self.__QNDIR = qnoptions.QNDIR()
        self.__QNTRASH = qnoptions.QNTRASH()
        self.__hkman = {}
        self.__file_repo = {}


    ## CLASS MODIFY METHODS

    def add_repo(self, repopath=None, repoinstance='default',):
        if repopath is None:
            repopath = self.__QNDIR

        self.__file_repo[repoinstance] = FileRepo(repopath)

    def add_existing_repo(self, existing_file_repo, repoinstance):
        self.__file_repo[repoinstance] = existing_file_repo

    ## CLASS INSPECT METHODS

    def app(self):
        return(self.__app)

    def opts(self):
        return(self.__options)

    def hkman(self, instance='default'):
        if instance in self.__hkman.keys():
            return(self.__hkman[instance])
        else:
            return(False)

    def add_hkman(self, instance='default'):
        self.__hkman[instance] = hotkey_manager.HotkeyManager(app=self.__app)


    def file_repo(self, instance='default'):
        if instance in self.__file_repo.keys():
            return(self.__file_repo[instance])
        else:
            return(False)
            #print("Error: File repository '" + instance + "' does not exist."
            #        + " Please add it using add_repo().")
            #sys.exit(1)


    def list_notes(self, printby='filenames', instance='default'
                    , lines_format_list=None, pinned_first=True):
        if printby == 'filenames':
            for filename in self.__file_repo[instance].filenames(pinned_first):
                print(filename)
        elif printby == 'filepaths':
            for filename in self.__file_repo[instance].filepaths(pinned_first):
                print(filename)
        elif printby == 'lines':
            lines = self.__file_repo[instance].lines(lines_format_list
                                                , pinned_first)
            for line in lines:
                print(line)

        else:
            print("Error: '" + printby + "' is not a valid printby setting." +
                    " Use 'filenames', 'filepaths', or 'lines'.")


    def find_note(self,* findstringlist, open_note=False, instance='default'):

        tmp_filelist = self.__file_repo[instance].filenames()[:]
        found_list = []
        for filen in tmp_filelist:
            if all ( (fstring in filen) for fstring in findstringlist[0] ):
                if open_note:
                    found_list.append(filen)
                else:
                    print(filen)

        if open_note:
            found_num = len(found_list)
            if found_num > 1:
                print("Many notes found, select which to open:")
                ct = 0
                for filen in found_list:
                    print('  (' + str(ct) + ') ' + filen)
                    ct += 1
                selection = input('Select between 0-' + str(found_num-1) 
                                    + '> ')
                try:
                    seln = int(selection)
                except (ValueError):
                    print('Invalid selection "' + selection + '".')
                    sys.exit(1)
                if seln not in range(found_num):
                    print('Invalid selection "' + selection + '".')
                    sys.exit(1)
                else:
                    print("Opening " + found_list[seln] + "...")
                    self.open_note(found_list[seln])

            elif found_num == 1:
                print("Opening " + found_list[0] + "...")
                self.open_note(found_list[0])
            else:
                print('No notes found.')
                if len(findstringlist) > 1:
                    print("Search terms were: ")
                    for fstring in findstringlist[0]:
                        print(fstring)
                else:
                    print("Opening " + findstringlist[0][0] + "...")
                    self.new_note(findstringlist[0][0])


    ## FILE MANAGEMENT METHODS

    def move_note(self, name1, name2, dest1=None, dest2=None, move_tags=False):

        if dest1 is None:
            dest1 = self.__QNDIR

        if not dest2:
            dest2 = self.__QNDIR

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


    def delete_note(self, note):


        self.move_note(note, note, dest1=self.__QNDIR, dest2=self.__QNTRASH)


    def undelete_note(self, note):


        self.move_note(note, note, dest1=self.__QNTRASH, dest2=self.__QNDIR)


    def open_note(self, note):


        inter = self.__options.interactive()
        fulldir = os.path.join(self.__QNDIR, note)
        if os.path.isfile(fulldir):
            #mime = file_mime_type(note).split("/")
            mime = file_mime_type_bash(fulldir).strip().split("/")
            fulldir = os.path.join(self.__QNDIR, note).strip()
            editor_command = self.__options.editor() + " '" + fulldir + "'"

            if (mime[0] == 'text' or mime[0] == 'None'):
                if inter:
                    os.system(editor_command)
                else:
                    terminal_open(self.__options.terminal(), editor_command) 
                    #os.system(self.__options.terminal() + " -e "
                    #          + self.__options.editor() + " " + fulldir)
            elif (mime[1] == 'x-empty'):
                if inter:
                    os.system(editor_command)
                else:
                    terminal_open(self.__options.terminal(), editor_command) 
                    #os.system(self.__options.terminal() + " -e " 
                    #          + self.__options.editor() + " " + fulldir)
            else:
                os.system(self.__options.launcher() + " " + fulldir)
        else:
            print(fulldir + " is not a note")
            sys.exit(1)


    def new_note(self, note):


        inter = self.__options.interactive()
        if '/' in note:
            note_dir = note.rsplit('/',1)[0]
            if not os.path.isdir(note_dir):
                os.makedirs(os.path.join(self.__QNDIR, note_dir), exist_ok=True)
        editor_command = self.__options.editor() + " '"
        editor_command += os.path.join(self.__QNDIR, note).strip()
        editor_command += "'"
        if inter:
            os.system(self.__options.editor() + " " 
                        + os.path.join(self.__QNDIR, note))
        else:
            terminal_open(self.__options.terminal(), editor_command, note)
            #os.system(self.__options.terminal() + ' -e ' + self.__options.editor() 
            #          + " " + os.path.join(self.__QNDIR, note))
        return(0)


    def force_new_note(self, note):
        inter = self.__options.interactive()
        filepath = os.path.join(self.__QNDIR, note.strip())
        if os.path.isfile(filepath):
            self.open_note(note)

        else:
            self.new_note(note)
        return(0)




## FOR TAG SUPPORT
#def load_tags():
#
#
#    tagfile = open(_TAGF_PATH, 'rb')
#    tagdict = pickle.load(tagfile)
#    tagfile.close()
#
#    return(tagdict)
#
#
#def save_tags(newdict):
#
#
#    tagfile = open(_TAGF_PATH, 'wb')
#    pickle.dump(newdict, tagfile)
#    tagfile.close()
#
#
#def list_tags():
#
#
#    tagslist = load_tags()['__taglist']
#    return(tagslist)
#
#
#def create_tag(tagname):
#
#
#    tagsdict = load_tags()
#    if not tagname in tagsdict['__taglist']:
#        tagsdict['__taglist'].append(tagname)
#        save_tags(tagsdict)
#
#    return(tagsdict)
#
#
#def add_note_tag(tagname, notename, tagsdict=None):
#
#
#    if not os.path.isfile(os.path.join(QNDIR, notename)):
#        print('Note does not exist. No tag added.')
#        sys.exit(0)
#    tagsdict = create_tag(tagname)
#    if notename in tagsdict:
#        if tagname in tagsdict[notename]:
#            print('Note already has tag. Doing nothing')
#        else:
#            tagsdict[notename].append(tagname)
#            save_tags(tagsdict)
#    else:
#        tagsdict[notename] = [tagname]
#        save_tags(tagsdict)
#
#    return(tagsdict)
#
#
#def del_note_tag(tagname, notename, tagsdict=None):
#
#
#    if not os.path.isfile(os.path.join(QNDIR, notename)):
#        print('Note does not exist. No tag removed.')
#        sys.exit(0)
#
#    if not tagsdict:
#        tagsdict = load_tags()
#    
#    if notename in tagsdict:
#        if tagname in tagsdict[notename]:
#            tagsdict[notename].remove(tagname)
#            if not list_notes_with_tags(tagname, tagsdict):
#                tagsdict['__taglist'].remove(tagname)
#            save_tags(tagsdict)
#    else:
#        pass
#
#    return(tagsdict)
#
#
#def clear_note_tags(notename, tagsdict=None):
#
#
#    if not os.path.isfile(os.path.join(QNDIR, notename)):
#        print('Note does not exist. Doing nothing.')
#        sys.exit(0)
#    if not tagsdict:
#        tagsdict = load_tags()
#    tagsdict.pop(notename, None)
#
#    return(tagsdict)
#
#
#def list_note_tags(notename):
#
#
#    if not os.path.isfile(os.path.join(QNDIR, notename)):
#        print('Note does not exist.')
#        sys.exit(0)
#
#    tagsdict = load_tags()
#    if notename in tagsdict:
#        return(tagsdict[notename])
#    else:
#        return([])
#
#
#def list_notes_with_tags(tagname, tagsdict=None):
#
#
#    if not tagsdict:
#        tagsdict = load_tags()
#    
#    filtered_list = []
#    for key,value in tagsdict.items():
#       if key == '__taglist':
#            continue
#        if tagname in value:
#            filtered_list.append(key)
#
#    return(filtered_list)


 

if __name__ == '__main__':
    # Create an options class that reads the config file and checks
    # the environment.
    qn_options = config_parse.QnOptions(run_parse_config=True)
    qn_options.check_environment()

    # Create a QnApp configured with the QnOptions class above.
    # Populate this QnApp with a File_Repo class
    qn = QnApp(qn_options)
    qn.add_repo()
    pass

    # Pin certain files in the file repo. Pin files before scanning the
    # directory.
    qn.file_repo().pin_files(['pinplease', 'nothing'])

    ## Scan the directory of the file repository and sort it
    qn.file_repo().scan_files()
    qn.file_repo().sort('size', True)
    print(qn.opts().print_options())

#    qn.list_notes()
#    grep = qn.file_repo().grep_files('world')

#    tfile=grep.filenames()[0]
    #qn.open_note('test')

    #qn.list_files('filepaths')
    #qn.list_files('lines', lines_format_list=['name', 'size', 'cdate'])



    ## Print the first ten entries with a header
    #n = 0
    #print("File List (" + str(qn.file_repo().filecount()) + ")")
    #print("---------")
    #for filen in qn.file_repo().filenames():
    #    print(filen)
    #    if n == 10:
    #        print("...\n")
    #        break
    #    n += 1

    ## Print the elapsed time since libraries were loaded
    #timeb = time.time()
    #print('Elapsed time: ' + str(timeb-timea) + ' seconds')

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



