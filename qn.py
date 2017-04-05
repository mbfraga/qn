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


    # Scans the directory for files and populates the file list and linebs
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





class QnApp ():
    # Must pass class of type QnOptions
    def __init__(self, qnoptions):
        self.options = qnoptions
        self.__app = qnoptions.app()
        self.__QNDIR = qnoptions.QNDIR()
        self.__QNTRASH = qnoptions.QNTRASH()
        self.hkman = {}
        self.file_repo = {}


    def move_note(self, name1, name2, dest1=None, dest2=None
                    , move_tags=False):


        if not dest1:
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


        inter = self.options.interactive()
        fulldir = os.path.join(self.__QNDIR, note)
        if os.path.isfile(fulldir):
            mime = file_mime_type(note).split("/")

            if (mime[0] == 'text' or mime[0] == 'None'):
                if inter:
                    os.system(self.options.editor() + " " + fulldir)
                else:
                    os.system(self.options.terminal() + " -e "
                              + self.options.editor() + " " + fulldir)
            elif (mime[1] == 'x-empty'):
                if inter:
                    os.system(self.options.editor() + " " + fulldir)
                else:
                    os.system(self.options.terminal() + " -e " 
                              + self.options.editor() + " " + fulldir)
            else:
                os.system(self.options.launcher() + " " + fulldir)
        else:
            print(fulldir + " is not a note")
            sys.exit(1)


    def new_note(self, note):

        inter = self.options.interactive()
        if '/' in note:
            note_dir = note.rsplit('/',1)[0]
            if not os.path.isdir(note_dir):
                os.makedirs(os.path.join(self.__QNDIR, note_dir), exist_ok=True)
        if inter:
            os.system(self.options.editor() + " " 
                        + os.path.join(self.__QNDIR, note))
        else:
            os.system(self.options.terminal() + " -e " + self.options.editor() 
                      + " " + os.path.join(self.__QNDIR, note))
        return(0)


    def force_new_note(self, note):
        inter = self.options.interactive()
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
#        if key == '__taglist':
#            continue
#        if tagname in value:
#            filtered_list.append(key)
#
#    return(filtered_list)


 

if __name__ == '__main__':
    qn_options = config_parse.QnOptions(run_parse_config=True)
    qn_options.check_environment()
    qn = QnApp(qn_options)
    qn.move_note("undelete", 'test2')

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



