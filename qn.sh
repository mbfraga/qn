#!/bin/bash

#Dumb Quick Note Manager

# This script manages notes in a very simplistic way. A single directory is
# managed where every file is a single note. This script can only create text
# files, but can open any filetype; this means that in order to add a jpg, you
# have to move it manually to the note directory. There are no fancy
# functionalities here, it is not meant to replace more robust applications.

# The general behavior of this script is as follows:
#   qn [-options ...]
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
#
# This script creates a relatively complete rofi interface. It is suggested to
# add a qnr alias that runs qn -r.


# Dependencies:
# rofi
# rifle (or falls back on xdg-open)
# i3 (for i3-sensible-terminal...need to change this)
# notify-send


# IMPORTANT: This script doesn't handle files with spaces...and I don't plan on
# changing this any time soon.


# To fix: right now the script is recursive but very naive about directories
#  * This script is hardcoded to vim
#  * Make opening the directory a bit more robust
#  * Add a way of duplicating a note (may be useful for templates)


# DONE
# * Allow files to be deleted (they are moved to $QNTRASH directory -- this
#   directory is ignored while listing notes.
# * Better handling of directories --including creation and deletion
# * Allow renaming of files - never overwrites
# * Open directory


# Some structures inspired by clerk (Credit to github.com/carnager


# Custom rofi keybindings (none yet)
delete="Alt+Backspace"
see_trash="Alt+t"
rename="Alt+Space" #not yet implemented
open_dir="Alt+d"

# user-editable globals Pleaase define this directory. That is the only
# directory that should be touched by this script. Anything else that may be
# created is a bug This directory will not be created by this script...please
# create it before using it
QNDIR="$HOME/syncthing/smalldocs/quicknotes" QNTRASH="$QNDIR/trash"
PERSISTENT=true

# globals
COLOR_URGENT=$(echo $(rofi -dump-xresources | grep "rofi.color-urgent" | \
   cut -d ',' -f2))

# If the quicknote directory does not exist...exit gracefully
if [[ ! -d $QNDIR ]]; then
   echo "Please create your directory as defined by QNDIR!"
   echo "As of now, you set QNDIR to be '$QNDIR'"
   echo "This directory was not found! Exiting..."
   exit 1
fi

# If the trash directory doesn't exist...create it!
if [[ ! -d $QNTRASH ]]; then
   mkdir $QNTRASH
fi


# quicknotes-specific rofi settings
_rofi () {
   rofi -dmenu  -i "$@"
}

_qnterm () {
   i3-sensible-terminal $@
}
# if rifle is installed, use it. Otherwise fallback to xdg-open.
command -v rifle > /dev/null
if [[ $? -eq 0 ]]; then
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
if [[ "0" == "$?" ]]; then
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
   find  $QNDIR/* -not -path "$QNTRASH/*" -type f | sed "s@$QNDIR/@@"
}

qn_printTRASH () {
   find  $QNTRASH/* -type f | sed "s@$QNTRASH/@@"
}

qn_openNote () {
   echo "Opening note: "$QNDIR/$1
   MIME=$(file -b --mime-type $QNDIR"/$@") 
   FMIME=$(echo $MIME | cut -d'/' -f1)
   F2MIME=$(echo $MIME | cut -d'/' -f2)
   #notify-send -t 1 $FMIME
   #notify-send -t 1 $F2MIME
   if [[ $FMIME == 'text' ]]; then
      _qn_editor $QNDIR"/$@"
   elif [[ $F2MIME == 'x-empty' ]]; then
      _qn_editor $QNDIR"/$@"
   else
      _file_launcher $QNDIR"/$@"
   fi
   echo "Note closed."
}

qn_newNote () {
   if [[ $SEL == *\/* ]]; then
      DIR=${SEL%/*}
      echo "Creating directory $DIR"
      mkdir -p $QNDIR/$DIR
   fi

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

_show_rename_menu () {

   NEWNAME=$(echo "" | _rofi -p "(qn rename):" -filter "$@")

   if [[ -z $NEWNAME ]];then
      _show_qn_menu $FILTER
      exit
   elif [[ "$NEWNAME" == "$@" ]];then
      notify-send "name not changed"
      _show_qn_menu $FILTER
      exit
   fi
 
   help_text="<span color=\"${COLOR_URGENT}\">Are you sure you want to rename $SEL to $NEWNAME ?</span>"
   dodelete=$(echo -e "no\nyes" | _rofi -p "(qn rename):" -mesg "${help_text}")

   if [[ -z $dodelete ]]; then _show_qn_menu $FILTER; exit; fi

   if [[ $dodelete == "yes" ]]; then
      if [[ -e $QNDIR/$NEWNAME ]]; then
         notify-send "Can't rename $SEL, $NEWNAME already exists"
         _show_rename_menu $SEL
      else
         if [[ $NEWNAME == *\/* ]]; then
            DIR=${NEWNAME%/*}
            echo "Creating directory $DIR"
            mkdir -p $QNDIR/$DIR
         fi

         mv $QNDIR/$SEL $QNDIR/$NEWNAME || notify-send "failed to rename $QNDIR/$SEL to $QNDIR/$NEWNAME"
         _show_qn_menu $FILTER
      fi

      exit
   else
      _show_qn_menu $FILTER
      exit
   fi

}



_show_trash_menu () {
   SEL=$(qn_printTRASH | _rofi -p "(qn trash):")
   if [[ -z $SEL ]]; then
      _show_qn_menu $FILTER
   fi
}

_show_qn_menu () {
   HELP="\"$delete\" to delete, \"$see_trash\" to show deleted files, \"$rename\" to rename a file"

   SELFS=$(qn_printDB | _rofi -p "(qn): " -format "f;s" \
                  -kb-custom-9 "$delete" \
                  -kb-custom-8 "$see_trash"  \
                  -kb-custom-7 "$rename" \
                  -kb-custom-6 "$open_dir" \
                  -mesg "$HELP" -filter $@)
   val=$?

   FILTER=$(echo $SELFS | cut -d ';' -f 1)
   SEL=$(echo $SELFS | cut -d ';' -f 2)

   case "$val" in
      18)
         _delete_menu $SEL
         exit
         ;;
      17)
         _show_trash_menu
         exit
         ;;
      16)
         _show_rename_menu $SEL
         exit
         ;;
      15)
         _open_dir $SEL
         exit
         ;;
      *)
         if [[ ! -z "$SEL" ]]; then
            if [[ ! -f $QNDIR"/"$SEL ]]; then
               qn_newNote $SEL
            else
               qn_openNote $SEL
            fi   

            if $PERSISTENT; then
            _show_qn_menu $FILTER
            fi
         fi
        
   esac


}

_open_dir () {
   if [[ $@ == *\/* ]]; then
      DIR=${@%/*}
      echo "Moving to $QNDIR/$DIR"
      i3-sensible-terminal -e "ranger $QNDIR/$DIR"
   else
      echo "Moving to $QNDIR"
      i3-sensible-terminal -e "ranger $QNDIR"
   fi
   _show_qn_menu $FILTER
}

_delete_menu () {
   help_text="<span color=\"${COLOR_URGENT}\">Are you sure you want to delete $SEL ?</span>"
   dodelete=$(echo -e "no\nyes" | _rofi -p "(qn delete):" -mesg "${help_text}")

   if [[ -z $dodelete ]]; then _show_qn_menu $FILTER; exit; fi

   if [[ $dodelete == "yes" ]]; then
      _delete $SEL
      exit
   else
      _show_qn_menu $FILTER
      exit
   fi
}

_delete () {
   notify-send "deleting $SEL"
   if [[ $SEL == *\/* ]]; then
      DIR=${SEL%/*}
      if [ ! -d "$QNTRASH/$DIR" ]; then
         mkdir -p $QNTRASH/$DIR
      else
         if [ -e "$QNTRASH/$SEL" ]; then
            now=$(date +"%m%d%Y-%H%M%S")
            mv $QNDIR/$SEL $QNTRASH/$SEL-conflict_$now
            exit
         fi
         mv $QNDIR/$SEL $QNTRASH/$SEL
         #once a file is removed, delete it's directory if empty
         find $QNDIR -type d -empty -delete
         exit
      fi
   fi
   mv $QNDIR/$SEL $QNTRASH/$SEL 
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
         _show_qn_menu
         exit
         ;;

      w)
         if [[ $# -ne 2 ]]; then
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
if [[ -z "$1" ]]; then
   qn_printDB
   exit
fi


#filter results based on keywords in argument
n=0
for var in "$@"; do
   n=$((n+1))
   if [[ $n -eq 1 ]]; then
      results=$(qn_printDB | grep $var)
   else
      results=$(tokenize $results |grep $var)
   fi
done

 # if there are no matches, exit unless there is only one argument, in which
 # case, a note will be create with that name.
 if [[ -z "$results" ]]; then
    if [[ $# -eq 1 ]]; then
       qn_newNote $1
       exit
    else
       exit
    fi
fi

nresult=( $results )
# if there is only one match, open the note with _file_launcher
if [[ ${#nresult[@]} -eq 1 ]]; then
   qn_openNote $results
fi


for res in $results
   do
      echo $res
   done
exit
}

quicknotesr $@
