#!/usr/bin/env python
import subprocess
import sys
import os
subprocess.call(["python", "-m", "bitshuffle"] + sys.argv[1:],
                stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr,
                cwd=os.path.dirname(os.path.realpath(__file__)))
