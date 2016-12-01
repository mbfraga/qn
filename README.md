# qn

# Quick Notes

Note management application that doesn't impose strict formats or requirements.
qn defines a note to be any file within the configured notes directory. While
text files with any syntax are preferred, you can put any type of file and qn
will open it via rifle or xdg-open. Fancy functionalities are kept to a
minimum, and no per-file metadata is ever created. The only application data
created is kept in a .qn directory inside the notes directory.

As of right now, this application relies on rofi. However, I'd like to make it
easy to switch the underlying applications. qn is composed of a few python
scripts that puts together terminal and graphical applications.

This application is naive and simple by design, but I do intend to implement a
few niceties.

# Features
* rofi or fzf(cli) interface
   - Quickly filter notes
   - Open/Create New/Delete/Rename Notes
   - Nondestructive. Deleted files are moved to a trash directory, and
     conflicts are stored.
   - Quickly grep files (e.g., type a query in qnr, and press alt-s)
   - Rudimentary tag management (qn-specific, no metadata is stored in files)

# Dependencies

* rofi (pretty much any version)
* rifle (from ranger file manager--if not installed xdg-open will be used)
* python-magic for mimetype detection

# Installation
I will make the installation easier soon.

1. git clone https://github.com/mbfraga/qn

2. create a file ~/bin/qnr that runs the python script qnr.py 

3. Edit qn.py and change the qn directory (QNDIR)

Note: Check the keybindings at the beginning of qnr.py and qnf.py to see the
keybindings. I will make help screens in the near future.

