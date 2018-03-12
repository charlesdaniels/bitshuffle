#!/usr/bin/env python

"""A tool for encoding and decoding arbitrary binary data as
ASCII text suitable for transmission over common communication protocols"""

from __future__ import division, generators, print_function, absolute_import

import os
import io
import argparse
import bz2
import subprocess
from tempfile import mkstemp
from sys import stdin, stdout, stderr, argv

from bitshuffle import VERSION, decode, encode
from .library import (gzip, DEFAULT_MSG, DEBUG,
                      exit_successfully, exit_with_error)

try:
    from shutil import which
except ImportError:  # python2
    from distutils.spawn import find_executable as which

try:
    assert file
except NameError:
    # pylint: disable=invalid-name
    file = io.IOBase


def create_parser():
    '''Argument options for CLI tool'''
    parser = argparse.ArgumentParser(description=__doc__)

    action = parser.add_mutually_exclusive_group()
    action.add_argument("--encode", "-e", action="store_true",
                        help="Generate a BitShuffle data packet from" +
                        "the input file and write it to the output.")

    action.add_argument("--decode", "-d", "-D", action="store_true",
                        help="Extract BitShuffle data packet(s) from " +
                        "the input file, and write the decoded file to the " +
                        "output file.")

    parser.add_argument("--version", "-v", action="version", version=VERSION)

    parser.add_argument("--chunksize", "-c", type=int,
                        help="Chunk size in bytes. Defaults to 2048.")

    parser.add_argument("--compresslevel", '-l', type=int,
                        help="Compression level when encoding. " +
                        "1 is lowest, 9 is highest. Defaults to 5. " +
                        "Ignored if specified compresstype does not support" +
                        " multiple compression levels.")

    parser.add_argument("--editor", "-E",
                        help="Editor to use for pasting packets. " +
                        "If not specified, defaults in this order:\n" +
                        "\t$VISUAL, $EDITOR, mimeopen, nano, vi, " +
                        "emacs, micro, notepad, notepad++")

    parser.add_argument("--compresstype", '-t',
                        help="Type of compression to use. Defaults to bz2. " +
                        "Ignored if decoding packets. " +
                        "Currently supported: 'bz2', 'gzip'.")

    parser.add_argument("--message", "-m", default=DEFAULT_MSG,
                        help="Override message displayed in every packet." +
                        " (default: " + DEFAULT_MSG + ")")
    return parser


# pylint: disable=inconsistent-return-statements
def find_editor():
    '''Attempt to find a suitable editor for decoding packets
    Extremely system-dependent.'''
    if 'VISUAL' in os.environ:
        return which(os.environ['VISUAL'])
    if 'EDITOR' in os.environ:
        return which(os.environ['EDITOR'])

    selected_editor = os.path.join(os.path.expanduser("~"), '.selected_editor')
    if os.path.isfile(selected_editor):
        # note: throws exception if selected_editor is unreadable
        with open(selected_editor) as selected:
            selected.readline()  # comment
            editor = selected.readline().split('=')[1].strip().replace('"', '')
            return which(editor)  # does nothing if already absolute path

    for program in ['mimeopen', 'nano', 'vi', 'emacs', 'notepad++', 'notepad',
                    'micro', 'kate', 'gedit', 'kwrite']:
        editor = which(program)
        if editor:
            return editor

    exit_with_error(102, "Please specify with '--editor' or set the EDITOR "
                    + "variable in your shell.")


def infer_mode(args):
    """If encode/decode is unknown, return which it 'should' be,
    based on various heuristics.
    TODO: return error if both encode and decode are specified
    """
    if args.encode or args.decode:
        return args

    # TODO: check if stdin looks like a packet (#55)
    elif any((args.compresstype, args.compresslevel,
              args.chunksize, stdin.isatty(), not argv[1:])):
        args.encode = True

    else:
        args.decode = True

    return args


def set_defaults(args):
    '''Set default arguments for BitShuffle
    TODO: make this part of argparse'''

    defaults = {'editor': find_editor(), 'chunksize': 2048,
                'compresslevel': 5, 'compresstype': 'bz2'}

    for arg in args.__dict__:
        if arg in defaults and not args.__dict__[arg]:
            args.__dict__[arg] = defaults[arg]

    return args


def check_for_file(filename):
    '''Ensure that the given file exists and is writable'''
    if isinstance(filename, file):
        return True
    try:
        open(filename).close()
        return True
    except IOError:
        return False


PARSER = create_parser()
ARGS = PARSER.parse_args()

# Checks if no parameters were passed
if stdin.isatty() and not argv[1:]:
    PARSER.print_help()
    if DEBUG:
        exit_with_error(1, 0)
    else:
        exit_successfully()

# Encode & Decode inference
ARGS = infer_mode(ARGS)
ARGS = set_defaults(ARGS)

# Main
if ARGS.encode:
    if ARGS.compresstype not in ['bz2', 'gzip']:
        PARSER.print_help()
        exit_with_error(2, ARGS.compresstype)
    elif ARGS.compresstype == 'bz2':
        COMPRESS = bz2.compress
    else:
        COMPRESS = gzip.compress

    for packet in encode(stdin, ARGS.chunksize, ARGS.compresslevel,
                         COMPRESS, ARGS.message):
        stdout.write(packet)
        stdout.write("\n\n")

    exit_successfully()

# else
# set to True for infile to be deleted after decoding
IS_TMP = False
if stdin.isatty():
    # ask the user to paste the packets into $VISUAL
    IS_TMP = True
    if not ARGS.editor:
        ARGS.editor = find_editor()

    if not check_for_file(ARGS.editor):
        exit_with_error(103, ARGS.editor)

    if DEBUG:
        stderr.write("editor is %s\n" % ARGS.editor)

    TMPFILE = mkstemp()[1]
    with open(TMPFILE, 'w') as tempfile:
        tempfile.write("Paste your BitShuffle packets in this file. " +
                       "You do not need to delete this message.\n\n")
        tempfile.flush()
    subprocess.call([ARGS.editor, TMPFILE])
    stdin = open(TMPFILE, 'r')

PAYLOAD, CHECKSUM_OK = decode(stdin.read())
try:
    # python 3
    stdout.buffer.write(PAYLOAD)
except AttributeError:
    # python 2
    stdout.write(PAYLOAD)

if IS_TMP and TMPFILE:
    os.remove(TMPFILE)

if not CHECKSUM_OK:
    exit_with_error(302, severity=2)

exit_successfully()
