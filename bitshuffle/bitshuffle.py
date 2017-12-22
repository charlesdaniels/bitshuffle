#!/usr/bin/env python

# .SHELLDOC
#
# BitShuffle command-line client. Supports encoding & decoding.
#
# Run with --help for usage information.
#
# .ENDOC

import os
import io
import sys
import argparse
import base64
import bz2
import gzip
import hashlib
import re
import string
import subprocess
import tempfile

try:
    from shutil import which
except ImportError:  # python2
    from distutils.spawn import find_executable as which

try:
    gzip_compress = gzip.compress
    gzip_decompress = gzip.decompress
except AttributeError:  # python2
    # taken straight from gzip.py
    def gzip_compress(data, compresslevel=5):
        buf = io.BytesIO()
        c = compresslevel
        with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=c) as f:
            f.write(data)
        return buf.getvalue()

    def gzip_decompress(data):
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
            return f.read()

try:
    file_type = file
except NameError:
    file_type = io.IOBase


version = '0.0.1-git'

stderr = sys.stderr
stdout = sys.stdout
stdin = sys.stdin
compress = None


def encode_data(data, chunksize, compresslevel, compresstype):
    """encode_data

    Compress the given data (which should be bytes), chunk it into chunksize
    sized chunks, base64 encode the chunks, and return the lot as a list of
    chunks, which are strings.

    :param data: bytes
    :param compresstype: string: bz2 or gzip
    :param compresslevel: int: 1-9 inclusive
    """

    if compresstype == 'bz2':
        data = bz2.compress(data, compresslevel=compresslevel)
    else:
        data = gzip_compress(data, compresslevel=compresslevel)

    chunks = []
    chunkptr = 0
    while True:
        chunk = data[chunkptr:chunkptr + chunksize]
        chunkptr += chunksize

        chunks.append(base64.b64encode(chunk))

        if chunkptr >= len(data):
            chunk = data[chunkptr:]
            chunks.append(base64.b64encode(chunk))
            break

    chunksfinal = []
    for c in chunks:
        if len(c) > 0:
            chunksfinal.append(c)

    return chunksfinal


def encode_packet(data, file_hash, seqnum, seqmax, compression):
    """encode_packet

    Take an already encoded data string and encode it to a BitShuffle data
    packet.

    :param data: bytes
    """

    msg = "This is encoded with BitShuffle, which you can download " + \
        "from https://github.com/charlesdaniels/bitshuffle"
    compatlevel = "1"
    encoding = "base64"
    data = data.decode(encoding="ascii")

    fmt = "((<<{}|{}|{}|{}|{}|{}|{}|{}>>))"
    packet = fmt.format(msg, compatlevel, encoding, compression, seqnum,
                        seqmax, file_hash, data)
    return packet


def encode_file(fhandle, chunksize, compresslevel, compresstype):
    """encode_file

    Encode the file from fhandle and return a list of strings containing
    BitShuffle data packets.

    :param fhandle:
    """

    try:
        # Python 3
        data = fhandle.buffer.read()
    except AttributeError as e:
        data = fhandle.read()
    file_hash = hashlib.sha1(data).hexdigest()
    chunks = encode_data(data, chunksize, compresslevel, compresstype)
    seqmax = len(chunks) - 1
    seqnum = 0
    packets = []
    for c in chunks:
        packets.append(encode_packet(c, file_hash, seqnum,
                                     seqmax, compresstype))
        seqnum += 1

    return packets


def main():
    parser = argparse.ArgumentParser(description="A tool for encoding and " +
                                     "decoding arbitrary binary data to " +
                                     "ASCII text.")

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

    parser.add_argument("--compresslevel", '-m', type=int,
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

    args = parser.parse_args()

    # Checks if no parameters were passed
    if not sys.argv[1:]:
        parser.print_help()
        sys.exit(1)

    elif args.version:
        print("Version: bitshuffle v{0}".format(version))
        sys.exit(0)

    # Encode & Decode inference
    args = infer_mode(args)

    # Set default values. Note that this ensures that args.input and
    # args.output are open file handles (or crashes the script if not).
    args = set_defaults(args)

    assert isinstance(args.input, file_type)
    assert isinstance(args.output, file_type)

    # Main
    if args.encode:
        if args.compresstype not in ['bz2', 'gzip']:
            parser.print_help()
            sys.exit(1)
        else:
            packets = encode_file(args.input, args.chunksize,
                                  args.compresslevel, args.compresstype)
            for p in packets:
                args.output.write(p)
                args.output.write("\n\n")

            args.output.flush()

    elif args.decode:

        # set to True for infile to be deleted after decoding
        is_tmp = False
        tmpfile = None
        if stdin.isatty() and args.input is stdin:
            # ask the user to paste the packets into $VISUAL
            is_tmp = True
            if not args.editor:
                args.editor = find_editor()

            if not check_for_file(args.editor):
                print("Editor %s not found" % args.editor)
                sys.exit(4)

            stderr.write("editor is %s\n" % args.editor)

            tmpfile = tempfile.mkstemp()[1]
            with open(tmpfile, 'w') as tf:
                tf.write("Paste your BitShuffle packets in this file. You " +
                         "do not need to delete this message.\n\n")
                tf.flush()
            subprocess.call([args.editor, tmpfile])
            args.input = open(tmpfile, 'r')

        payload, checksum_ok = decode(args.input.read())
        try:
            # python 3
            args.output.buffer.write(payload)
        except AttributeError as e:
            # python 2
            args.output.write(payload)

        if is_tmp and tmpfile:
            os.remove(tmpfile)

        args.input.close()
        args.output.close()

        if checksum_ok:
            sys.exit(0)
        else:
            sys.exit(8)

    args.input.close()
    args.output.close()


def find_editor():
    if 'VISUAL' in os.environ:
        return which(os.environ['VISUAL'])
    if 'EDITOR' in os.environ:
        return which(os.environ['EDITOR'])

    selected_editor = os.path.join(os.path.expanduser("~"), '.selected_editor')
    if os.path.isfile(selected_editor):
        # note: throws exception if selected_editor is unreadable
        with open(selected_editor) as f:
            f.readline()  # comment
            editor = f.readline().split('=')[1].strip().replace('"', '')
            return which(editor)  # does nothing if already absolute path

    for program in ['mimeopen', 'nano', 'vi', 'emacs', 'notepad++', 'notepad',
                    'micro', 'kate', 'gedit', 'kwrite']:
        editor = which(program)
        if editor:
            return editor

    print("Could not find a suitable editor." +
          "Please specify with '--editor'" +
          "or set the EDITOR variable in your shell.")
    sys.exit(1)


def decode(message):
        comment, compatibility, encoding, compression, seq_num, \
            seq_end, checksum, chunk = range(8)

        try:
            packets = re.findall('\(\(<<(.*)>>\)\)', message,
                                 flags=re.MULTILINE)
        except IndexError:
            print("Invalid packet to decode. Aborting.")
            sys.exit(2)

        if len(packets) == 0:
            print("Nothing to decode or nothing matched spec. Aborting.")
            sys.exit(2)

        # delete unused whitespace and separators
        packets = [re.sub("|".join(string.whitespace), "", p)
                   for p in packets if p.strip() is not '']

        segments = [None] * len(packets)  # ordered by index of packets
        # each chunk will be appended and original will be returned
        payload = bytes()
        for index, packet in enumerate(packets):
            try:
                segments[index] = packet.split("|")
                if segments[index][seq_num] != str(index):
                    stderr.write("WARNING: Sequence number " +
                                 "%s does not match actual order %d\n"
                                 % (segments[index][seq_num], index))
                    continue
            except IndexError:
                stderr.write("WARNING: Packet " +
                             "%d is invalid for decoding.\n" %
                             (index))
                continue

            payload += base64.b64decode(segments[index][chunk])

        if segments[0][compression] == "bz2":
            payload = bz2.decompress(payload)
        else:
            payload = gzip_decompress(payload)

        checksum_ok = verify(payload, segments[0][checksum])
        payload = bytes(payload)
        return payload, checksum_ok


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
        if args.output:
            args.decode = True
        else:
            args.encode = True

    elif stdin.isatty():
        args.decode = True

    elif not args.output:
        args.encode = True

    else:
        args.decode = True

    return args


def set_defaults(args):

    defaults = {'input': stdin, 'output': stdout,
                'editor': find_editor(), 'chunksize': 2048,
                'compresslevel': 5, 'compresstype': 'bz2'}

    for arg in args.__dict__:
        if arg in defaults and not args.__dict__[arg]:
            args.__dict__[arg] = defaults[arg]

    # open args.input and args.output so they are file handles
    if not isinstance(args.input, file_type):
        try:
            args.input = open(args.input, 'rb')
        except IOError as e:
            stderr.write("FATAL: could not open '{}'\n".format(args.input))
            stderr.write("exception was: {}\n".format(e))
            sys.exit(4)

    if not isinstance(args.output, file_type):
        try:
            args.output = open(args.output, 'wb')
        except IOError as e:
            stderr.write("FATAL: could not open '{}'\n".format(args.output))
            stderr.write("exception was: {}\n".format(e))
            sys.exit(4)

    return args


def verify(data, given_hash):
    """verify:
    Ensure that hash of data and given hash match up.
    Currently, only a warning is emmitted if they do not.
    :param data: byte-like object
    :param given_hash: string
    """
    if hashlib.sha1(data).hexdigest() != given_hash:
        stderr.write("WARNING: Hashes do not match. Continuing, but you " +
                     "may want to investigate.\n")
        return False
    return True


def check_for_file(filename):
    if isinstance(filename, file_type):
        return True
    try:
        open(filename).close()
        return True
    except IOError:
        return False


if __name__ == "__main__":
    main()
