#!/usr/bin/env python
import os
import sys
os.chdir(os.path.dirname(os.path.realpath(__file__)))
os.execvp("python", ["python", "-m", "bitshuffle"] + sys.argv[1:])
