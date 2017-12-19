#!/bin/sh

# exit on first failure
# be verbose
set -ev

OLDCWD=`pwd`
WINE_PYTHON="wine ~/.wine/drive_c/python35/python.exe"

# basics
sudo apt-get install -y unzip wget tree

# only 2.0 runs non-graphical installer
sudo dpkg --add-architecture i386
wget -nc https://dl.winehq.org/wine-builds/Release.key
sudo apt-key add Release.key
rm Release.key
sudo sh -c 'echo "deb https://dl.winehq.org/wine-builds/ubuntu/ trusty main" >> /etc/apt/sources.list'
sudo apt-get update
sudo apt install --install-recommends winehq-stable


# make config files on first run
wine
cd ~/.wine/drive_c
mkdir python35
cd python35

# need non-graphical installer i.e. zip file
wget https://www.python.org/ftp/python/3.5.0/python-3.5.0-embed-win32.zip
unzip python-3.5.0-embed-win32.zip
unzip python35.zip
rm -f python35.zip python-3.5.0-embed-win32.zip

# pip is not included in python install
wget https://bootstrap.pypa.io/get-pip.py
$WINE_PYTHON get-pip.py

# https://pyinstaller.readthedocs.io/en/stable/requirements.html?highlight=windows
$WINE_PYTHON -m pip install pyinstaller

# now with regular python
pip install pyinstaller

# actually make the files
cd $OLDCWD
$WINE_PYTHON -m pyinstaller --distpath dist/windows bitshuffle.py
python -m pyinstaller --distpath dist/linux bitshuffle.py

# make archive files
tar -vczf dist/linux/bitshuffle.tar.gz dist/linux/bitshuffle
zip -rA9 dist/windows/bitshuffle.zip dist/windows/bitshuffle

# record build environment to console log
tree .
