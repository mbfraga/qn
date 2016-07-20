#!/bin/bash

#Dumb Quick Note Manager

# This script manages notes in a very simplistic way. A single directory is
# managed where every file is a single note. This script can only create text
# files, but can open any filetype; this means that in order to add a jpg, you
# have to move it manually to the note directory. There are no fancy
# functionalities here, it is not meant to replace orgnotes or tomboy.

# The general behavior of this script is as follows:
#   dnm [-options ...]
#   -h   prints help text
#   -r   lists all notes using rofi and opens the selected note
#   -w   Creates a new note (using vim)
#   
#   If no argument is provided, this script lists all notes
#   If a single argument is provided, there are two possible outcomes
#      If the argument leads to a single match, the matched note is opened
#      If there are no matches, or there are multiple matches, a new note is
#      opened with the argument as its name
#   If multiple matches occur, they are listed to the output

# Dependencies:
# rofi
# rifle (or falls back on xdg-open)


# IMPORTANT: This script doesn't handle files with spaces...and I don't plan on
# changing this any time soon.


# To fix: right now the script is recursive but very naive about directories
#  If a directory doesn't exist and you try to open a note in it...you can't
#  save our note. 

# Custom rofi keybindings (none yet)

# global
   # Pleaase define this directory. That is the only directory that should be
   # touched by this script. Anything else that may be created is a bug
   # This directory will not be created...please create it before using it
   QNDIR="$HOME/syncthing/smalldocs/quicknotes"

# Some structures inspired by clerk (Credit to github.com/carnager


# dumbnotes-specific rofi settings
_rofi () {
   rofi "$@"
}

# if rifle is install, use it. Otherwise fallback to xdg-open
command -v rifle > /dev/null
if [ $? -eq 0 ]; then
   _file_launcher () {
      rifle "$@"
   }
else
   _file_launcher () {
      xdg-open "$@"
   }
fi

# check if running in interactive terminal or not
tty -s
if [ "0" == "$?" ]; then
   TERM_INTER=true
   _qn_editor () {
      vim $@
   }
else
   TERM_INTER=false
   _qn_editor () {
      notify-send -t 1 $@
      $TERMINAL -e "vim $@"
   }
fi



qn_printDB () {
   find  $QNDIR/* | sed "s@$QNDIR/@@" 
}

qn_openNote () {
   echo "Opening note: "$QNDIR/$1
   FMIME=$(file -b --mime-type $QNDIR"/$@" | cut -d'/' -f1) 
   #   notify-send -t 1 $FMIME
   if [ $FMIME == 'text' ]; then
      _qn_editor $QNDIR"/$@"
   else
      _file_launcher $QNDIR"/$@"
   fi
   echo "Note closed."
}

qn_newNote () {
   echo "Opening note: "$QNDIR/$1
   _qn_editor $QNDIR"/$@"
   echo "Note closed."
}

tokenize () {
   filter=($@)
   for each in "${filter[@]}"; do
     echo "$each"
   done
}

quicknotesr () {
while getopts ":hurcw" opt; do
   case $opt in
      h)
         echo "quicknotesr usage:" >&2
         echo "      quicknotesr [-options ...]" >&2
         echo "" >&2
         echo "Options:" >&2
         echo "      -h       Print this help text" >&2
#         echo "      -u       Update database" >&2
         echo "      -r       List notes with rofi and open selected note" >&2
         echo "      -w       Create new note (with vim)" >&2
         echo "" >&2

         exit
         
         ;;
      u)
#         qn_update
         exit
         ;;

      r)
         SEL=$(qn_printDB | rofi -dmenu -i)
         if [ ! -z "$SEL" ]; then
            if [ ! -f $QNDIR"/"$SEL ]; then
               qn_newNote $SEL
            else
               qn_openNote $SEL
            fi   
         fi
         echo AA
         exit
         ;;

      w)
         if [ $# -ne 2 ]; then
            echo "No spaces allowed in file names. Only two arguments allowed"
            echo "quicknotesr -w {filename}"
         else
            qn_newNote $2
         fi
         exit
         ;;

      \?)
         echo "Invalid option: -$OPTARG" >&2
         ;;
   esac
done

#if no argument, just print out the list of notes
if [ -z "$1" ]; then
   qn_printDB
   exit
fi


#filter results based on keywords in argument
n=0
for var in "$@"; do
   n=$((n+1))
   if [ $n -eq 1 ]; then
      results=$(qn_printDB | grep $var)
   else
      results=$(tokenize $results |grep $var)
   fi
done

 # if there are no matches, exit unless there is only one argument, in which
 # case, a note will be create with that name.
 if [ -z "$results" ]; then
    if [ $# -eq 1 ]; then
       qn_newNote $1
       exit
    else
       exit
    fi
fi

nresult=( $results )
# if there is only one match, open the note with _file_launcher
if [ ${#nresult[@]} -eq 1 ]; then
   qn_openNote $results
fi


for res in $results
   do
      echo $res
   done
exit
}

quicknotesr $@
