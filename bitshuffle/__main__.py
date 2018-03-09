#!/usr/bin/env python

'''
BitShuffle command-line client. Supports encoding & decoding.
Run with --help for usage information.
'''

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
    parser = argparse.ArgumentParser(description=main.__doc__)

    parser.add_argument("--input", "-i",
                        help="Input file. Defaults to stdin. If the only " +
                        "argument, implies --encode")

    parser.add_argument("--output", "-o",
                        help="Output file. Defaults to stdout. If the only " +
                        "argument, and stdin is not a tty, implies " +
                        "--decode")

    parser.add_argument("--encode", "-e", action="store_true",
                        help="Generate a BitShuffle data packet from" +
                        "the input file and write it to the output.")

    parser.add_argument("--decode", "-d", "-D", action="store_true",
                        help="Extract BitShuffle data packet(s) from the " +
                        "the input file, and write the decoded file to the " +
                        "output file.")

    parser.add_argument("--version", "-v", action="store_true",
                        help="Displays the current version of bitshuffle.")

    parser.add_argument("--chunksize", "-c", type=int,
                        help="Chunk size in bytes. Defaults to 2048.")

    parser.add_argument("--compresslevel", '-l', type=int,
                        help="Compression level when encoding. " +
                        "1 is lowest, 9 is highest. Defaults to 5. " +
                        "Ignore if specified compresstype does not support" +
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


def main():

    """A tool for encoding and decoding arbitrary binary data as
ASCII text suitable for transmission over common communication protocols"""

    parser = create_parser()
    args = parser.parse_args()

    # Checks if no parameters were passed
    if not argv[1:]:
        parser.print_help()
        if DEBUG:
            exit_with_error(1, 0)
        else:
            exit_successfully()

    elif args.version:
        print("Version: bitshuffle v{0}".format(VERSION))
        exit_successfully()

    # Encode & Decode inference
    args = infer_mode(args)

    # Set default values. Note that this ensures that args.input and
    # args.output are open file handles (or crashes the script if not).
    args = set_defaults(args)

    assert isinstance(args.input, file)
    assert isinstance(args.output, file)

    # Main
    if args.encode:
        if args.compresstype not in ['bz2', 'gzip']:
            parser.print_help()
            exit_with_error(2, args.compresstype)
        elif args.compresstype == 'bz2':
            compress = bz2.compress
        else:
            compress = gzip.compress

        packets = encode(args.input, args.chunksize, args.compresslevel,
                         compress, args.message)
        for packet in packets:
            args.output.write(packet)
            args.output.write("\n\n")

        args.output.flush()
        args.input.close()
        args.output.close()
        exit_successfully()

    else:

        # set to True for infile to be deleted after decoding
        is_tmp = False
        if stdin.isatty() and args.input is stdin:
            # ask the user to paste the packets into $VISUAL
            is_tmp = True
            if not args.editor:
                args.editor = find_editor()

            if not check_for_file(args.editor):
                exit_with_error(103, args.editor)

            if DEBUG:
                stderr.write("editor is %s\n" % args.editor)

            tmpfile = mkstemp()[1]
            with open(tmpfile, 'w') as tempfile:
                tempfile.write("Paste your BitShuffle packets in this file. " +
                               "You do not need to delete this message.\n\n")
                tempfile.flush()
            subprocess.call([args.editor, tmpfile])
            args.input = open(tmpfile, 'r')

        payload, checksum_ok = decode(args.input.read())
        try:
            # python 3
            args.output.buffer.write(payload)
        except AttributeError:
            # python 2
            args.output.write(payload)

        if is_tmp and tmpfile:
            os.remove(tmpfile)

        args.input.close()
        args.output.close()

        if checksum_ok:
            exit_successfully()
        else:
            exit_with_error(302, severity=2)


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

    elif any((args.compresstype, args.compresslevel,
              args.chunksize)):
        args.encode = True

    # this is a submenu: could specify editor to compose
    # TODO: check editor when encoding as well as decoding

    elif args.editor:
        args.decode = True

    elif args.input:
        # pylint: disable=simplifiable-if-statement
        if args.output:
            args.decode = True
        else:
            args.encode = True

    elif not args.output and not stdin.isatty():
        args.encode = True

    else:
        args.decode = True

    return args


def set_defaults(args):
    '''Set default arguments for BitShuffle
    TODO: make this part of argparse'''

    defaults = {'input': stdin, 'output': stdout,
                'editor': find_editor(), 'chunksize': 2048,
                'compresslevel': 5, 'compresstype': 'bz2'}

    for arg in args.__dict__:
        if arg in defaults and not args.__dict__[arg]:
            args.__dict__[arg] = defaults[arg]

    # open args.input and args.output so they are file handles
    if not isinstance(args.input, file):
        try:
            args.input = open(args.input, 'rb')
        except IOError as err:
            exit_with_error(104, args.input, str(err), severity=4)

    if not isinstance(args.output, file):
        try:
            args.output = open(args.output, 'wb')
        except IOError as err:
            exit_with_error(105, args.output, str(err), severity=4)

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


if __name__ == "__main__":
    main()
