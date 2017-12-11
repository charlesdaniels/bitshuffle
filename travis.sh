#!/bin/sh
# basics
sudo apt-get install -y unzip wget

# only 2.0 runs non-graphical installer
sudo dpkg --add-architecture i386
wget -nc https://dl.winehq.org/wine-builds/Release.key
sudo apt-key add Release.key
rm Release.key
echo 'deb https://dl.winehq.org/wine-builds/debian/ debian main' >> /etc/apt/sources.list
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
wine python.exe get-pip.py

# https://pyinstaller.readthedocs.io/en/stable/requirements.html?highlight=windows
wine python -m pip install pyinstaller
