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

# Dependencies

* rofi (pretty much any version) for qnr.py, fzf for qnf.py
* rifle (from ranger file manager--if not installed xdg-open will be used)
* python-configargparse

# Todo

* Make this app a bit more user friendly
   - Make a better presentation of this tool.
   - Implement CLI (Very low priority, fzf is close enough)
   - Implement way to permanently delete notes in the trash

# Installation
I will make the installation easier soon.

1. git clone https://github.com/mbfraga/qn

2. go to qn directory

3. sudo pip3 install ./

4. copy /etc/qn/config.example to ~/.config/qn/config


