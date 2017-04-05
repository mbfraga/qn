# qn - Quick Notes

Note management application that doesn't impose strict formats or requirements.
qn defines a note to be any file within the configured notes directory. While
text files with any syntax are preferred, you can put any type of file and qn
will open it via rifle or xdg-open. Fancy functionalities are kept to a
minimum, and no per-file metadata is ever created. The only application data
created is kept in a .qn directory inside the notes directory.

There are currently two interfaces for the underlying functionalites, one built
on top of [rofi](https://github.com/DaveDavenport/rofi), and the other built on
top of [fzf](https://github.com/junegunn/fzf). However, I'd like to make it
easy to switch the underlying applications. 

At its most elemental level, qn is more about a philosophy of managing notes. I
suggest everyone to try building their own note-taking app. We are all
different, and these rudimentary tasks are best tailored to those personal
idiosyncracies. qn started as a bash script (see qn.sh) and is now composed of
a few python scripts that put together terminal and graphical applications.

This application is naive and simple by design, but I do intend to implement a
few niceties.

Note On syncing: This is left to the user for now. I use syncthing and have
been doing so for the past year--it works beautifuly. Personally, I keep a
syncthing folder almost exclusively for qn...this makes it very portable and I
can even sync it to devices with very little storage.

# Features
* rofi or fzf(cli) interfaces
   - Quickly filter notes
   - Open/Create New/Delete/Rename Notes
   - Nondestructive. Deleted files are moved to a trash directory, and
     conflicts are stored.
   - Quickly grep files (e.g., type a query in qnr, and press alt-s)
   - Rudimentary tag management (qn-specific, no metadata is stored in files)

# Dependencies

* rofi (pretty much any version) for qnr.py, fzf for qnf.py
* rifle (from ranger file manager--if not installed xdg-open will be used)
* python-configargparse

# Todo

* Make this app a bit more user friendly
   - Create a help page for both rofi and fzf apps, with a comprehensive set of
       explanations of the features.
   - Look into $XDG_HOME_CONFIG/.qn and ~/.qn for configuration files.
   - Make a better presentation of this tool.
   - Allow a way to pass rofi commands to qnr
   - Modify qnf keybindings to feel more natural and closer to qnr
   - Implement CLI (Very low priority, fzf is close enough)
   - Implement way to permanently delete notes in the trash

# Installation
I will make the installation easier soon.

1. git clone https://github.com/mbfraga/qn

2. (For Rofi) create a file ~/bin/qnr that runs the python script qnr.py 

2. (For fzf) create a file ~/bin/qnf that runs the python script qnf.py

3. Edit qn.py and change the qn directory (QNDIR)

Note: Check the keybindings at the beginning of qnr.py and qnf.py to see the
keybindings. I will make help screens in the near future.

