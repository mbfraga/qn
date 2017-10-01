# qn - Quick Notes

Note management application that doesn't impose strict formats or requirements.
**qn** defines a note to be any file within the configured notes directory. While
text files with any syntax are preferred, you can put any type of file and qn
will open it via rifle or xdg-open. Fancy functionalities are kept to a
minimum, and no per-file metadata is ever created. The only application data
created is kept in a .qn directory inside the notes directory--it can be
deleted at any time without losing data (except trashed notes).

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

## Features
* rofi or fzf(cli) interfaces
   - Quickly filter notes
   - Open/Create/Delete/Rename Notes
   - Nondestructive. Deleted files are moved to a trash directory, and
     conflicts are stored (with suffixes).
   - Quickly grep files (e.g., type a query in qnr, and press alt-s)
   - qnf works beautifully on android using **Termux**. It still
     requires the right python libraries, fzf and an editor like neovim.

## Dependencies

* rofi for qnr
* fzf for qnf
* python3-configargparse
* rifle (from ranger file manager--if not installed xdg-open will be used)
* python3-pip -- to install. Not a hard requirement, but it's the easy way to
  get qn up and running.

## Todo

* Make this app a bit more user friendly.
   - Make a better presentation of this tool.
* Implement CLI (Very low priority, fzf is close enough).
* Implement way to permanently delete notes in the trash.
* Tags -- they were implemented in a previous incarnation of **qn**. I prefer to
  keep the name informative rather than rely on tags (very low priority).
* Clean up configuration.

## Installation via local pip

Note: qn is not in the python repos, so pip won't find it. We are using pip
here because it affords us better ability to uninstall **qn** cleanly. easy_install
also works.

1. git clone https://github.com/mbfraga/qn

2. go to qn directory. `cd qn`

3. Run `sudo pip3 install ./`

4. copy /etc/qn/config.example to ~/.config/qn/config. `cp 

## Upgrade via pip

1. git pull 

2. go to **qn** directory

2. Run `sudo pip3 install ./ --upgrade`

## Set up without pip

You can set up **qn** without pip. Running qnr or qnf from the bin/ directory in
the repo will work. You can create symlinks if you prefer this type of local install.

An example setup would be as follows:

1. We will set it up in ~/opt and put launchers in ~/bin. Make sure ~/bin is in
your **$PATH**

2. Go to ~/opt. `cd ~/opt`

3. Clone qn. `git clone https://github.com/mbfraga/qn`

4. Create symlinks for the qnr and qnf executables.

   ```bash
   ln -s ~/opt/qn/bin/qnr ~/
   ln -s ~/opt/qn/bin/qnf ~/
   ```
5. Create config directory. `mkdir ~/.config/qn`

6. Copy the config file. `cp config.example ~/.config/qn/`

## Misc Notes

* Termux setup:

   - Only qnf will work.

   - termux doesn't have xdg-mime, so python's mimetypes is used. Python's
     mimetypes is not very reliable on some types of files. Text-based files should be ok.
     
   - termux doesn't have /etc, so while pip will work, it will not want to install the
     default config file. Copy it directly from the repo to your $XDG_HOME_CONFIG.
