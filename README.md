# qn

Quick Notes

This script is meant to manage notes in a directory. A note is defined as any
file within the notes directory. Text files are preferred, but you can put any
file and qnr will be able to open it. No fancy functionalities are implemented
here, it is not meant to replace more robust applications.

This is naive and simple by design, but I would like to implement a few
niceties.

# Features
* rofi interface
   - Quickly filter notes
   - Open/Create New/Delete/Rename Notes
   - Nondestructive. Deleted files are moved to a trash directory, and
     conflicts are stored.

# Dependencies

* rofi (pretty much any version)
* rifle (from ranger file manager--if not installed xdg-open will be used)
* i3 (for i3-sensible-terminal...need to fix this)
* libnotify

# Installation

1. git clone https://github.com/mbfraga/qn

2. cp qn/qn.sh ~/bin/qn

3. My focus at the moment is the rofi interface, o I suggest the following:
   - echo '#!/bin/bash\nsh ~/bin/qn.sh -r' > ~/bin/qnr

4. chmod +x ~/bin/{qn,qnr}

3. Modify the ~/bin/qn script for the following entries
   * QNDIR - notes directory, you must create this directory -- this script
     will not do it for you. (this is the only setting you absolutely need in
     order for the script to work)
   * QNTRASH - trash directory, I suggest leaving the default as "$QNDIR/trash"
      - this directory is excluded from being indexed
      - you can see files in the trash with qnr by pressing Alt+t
   * PERSISTENT (true/false) - this boolean makes it so that whenever you close
     a note, qnr is run again. It can be annoying or useful depending on
     workflow.
