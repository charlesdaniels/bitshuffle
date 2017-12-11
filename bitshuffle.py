#!/usr/bin/env python3

# .SHELLDOC
#
# BitShuffle command-line client. Supports encoding & decoding.
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


version = '0.0.1'

stderr = sys.stderr
stdout = sys.stdout
stdin = sys.stdin
compress = None


def encode_data(data, chunksize, compresslevel, compresstype):
    """encode_data

    Compress the given data (which should be bytes), chunk it into chunksize
    sized chunks, base64 encode the chunks, and return the lot as a list of
    chunks, which are strings.

    :param data:
    :param compresslevel:
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


def encode_packet(data, filename, checksum, seqnum, seqmax, compression):
    """encode_packet

    Take an already encoded data string and encode it to a BitShuffle data
    packet.

    :param data:
    """

    msg = "This is encoded with BitShuffle, which you can download " + \
        "from https://github.com/charlesdaniels/bitshuffle"
    compatlevel = "1"
    encoding = "base64"
    data = data.decode(encoding="ascii")

    fmt = "((<<{}|{}|{}|{}|{}|{}|{}|{}|{}>>))"
    packet = fmt.format(msg, compatlevel, encoding, compression, seqnum,
                        seqmax, filename, checksum, data)
    return packet


def encode_file(fhandle, chunksize, compresslevel, compresstype, filename):
    """encode_file

    Encode the file from fhandle and return a list of strings containing
    BitShuffle data packets.

    :param fhandle:
    """

    data = fhandle.read()
    checksum = hashlib.sha1(data).hexdigest()
    chunks = encode_data(data, chunksize, compresslevel, compresstype)
    seqmax = len(chunks) - 1
    seqnum = 0
    packets = []
    for c in chunks:
        packets.append(encode_packet(c, filename, checksum, seqnum,
                                     seqmax, compresstype))
        seqnum += 1

    return packets


def main():
    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input", "-i",
                        help="Input file. Defaults to stdin.")

    parser.add_argument("--output", "-o",
                        help="Output file. Defaults to stdout.")

    parser.add_argument("--filename", "-f",
                        help="Set filename to use when encoding " +
                        "explicitly")

    parser.add_argument("--encode", "-e", action="store_true",
                        help="Generate a BitShuffle data packet " +
                        "from the input file")

    parser.add_argument("--decode", "-d", "-D", action="store_true",
                        help="Extract a BitShuffle data packet.")

    parser.add_argument("--version", "-v", action="store_true",
                        help="Displays the current version of bitshuffle")

    parser.add_argument("--chunksize", "-c", type=int,
                        help="Chunk size in bytes. Defaults to 2048.")

    parser.add_argument("--compresslevel", '-m', type=int,
                        help="Compression level when encoding. " +
                        "1 is lowest, 9 is highest. Defaults to 5.")

    parser.add_argument("--editor", "-E",
                        help="Editor to use for pasting packets. " +
                        "If not specified, defaults in this order:\n" +
                        "\t$VISUAL, $EDITOR, mimeopen, nano, vi, " +
                        "emacs, micro, notepad, notepad++")

    parser.add_argument("--compresstype", '-t',
                        help="Type of compression to use when encoding. "
                             "Defaults to bz2. " +
                             "Currently supported: 'bz2', 'gzip'")

    args = parser.parse_args()

    if len(sys.argv[1:]) == 0:
        parser.print_help()
        exit(0)

    elif args.version:
        print("Version: bitshuffle v%s" % version)
        exit(0)

    # Encode & Decode inference
    args = infer_mode(args)

    # Set default values
    args = set_defaults(args)

    # Main
    if args.encode:

        if args.compresstype not in ['bz2', 'gzip']:
            parser.print_help()
            sys.exit(1)

        if check_for_file(args.input):
            with open(args.input, 'rb') as f:
                packets = encode_file(f, args.chunksize, args.compresslevel,
                                      args.compresstype, args.filename)
                with open(args.output, 'w') as of:
                    for p in packets:
                        of.write(p)
                        of.write("\n\n")

                    of.flush()
        else:
            quit('Error: Input file not found')

    elif args.decode:

        infile = args.input
        # set to True for infile to be deleted after decoding
        is_tmp = False
        if stdin.isatty() and args.input is '/dev/stdin':
            # ask the user to paste the packets into $VISUAL
            is_tmp = True

            tmpfile = tempfile.mkstemp()[1]
            with open(tmpfile, 'w') as tf:
                tf.write("Paste your BitShuffle packets in this file. You " +
                         "do not need to delete this message.\n\n")
                tf.flush()
            subprocess.call([editor, tmpfile])
            infile = tmpfile

        with open(infile, 'r') as f:
            payload, checksum_ok = decode(f.read())
            with open(args.output, 'wb') as of:
                    of.write(payload)

        if is_tmp:
            os.remove(infile)

        if checksum_ok:
            sys.exit(0)
        else:
            sys.exit(8)


def decode(message):
        comment, compatibility, encoding, compression, seq_num, \
            seq_end, name, checksum, chunk = range(9)

        try:
            packets = re.findall('\(\(<<(.*)>>\)\)', message,
                                 flags=re.MULTILINE)
        except IndexError:
            print("Invalid packet to decode. Aborting.")
            sys.exit(2)

        if len(packets) == 0:
            print("Nothing to decode or nothing matched spec. Aborting.")
            sys.exit(2)

        packets_nice = []
        for p in packets:
            p = p.strip()
            if p is not '':
                # delete unused whitespace and separators
                p = re.sub("|".join(string.whitespace), "", p)
                packets_nice.append(p)

        packets = packets_nice

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
    if args.encode or args.decode:
        return args

    elif any((args.compresstype, args.compresslevel,
              args.chunklevel, args.filename)):
        args.encode = True

    # this is a submenu: could specify editor to compose
    # TODO: check editor when encoding as well as decoding

    elif args.editor:
        args.decode = True

    # don't understand the logic past here
    elif stdin.isatty() and not args.input:
        args.decode = True

    elif not args.output:
        args.encode = True

    else:
        parser.print_help()
        quit(1)


def set_defaults(args):

    defaults = {'input': '/dev/stdin', 'output': '/dev/stdout',
                'editor': find_editor(), 'chunksize': 2048,
                'compresslevel': 5, 'compresstype': 'bz2'}

    for arg in args.__dict__:
        if arg in defaults and not args.__dict__[arg]:
            args.__dict__[arg] = defaults[arg]

    if not args.filename:
        args.filename = os.path.basename(args.input)

    return args


def find_editor():
    if 'VISUAL' in os.environ:
        return os.environ['VISUAL']
    elif 'EDITOR' in os.environ:
        return os.environ['EDITOR']
    else:
        for program in ['mimeopen', 'nano', 'vi', 'emacs',
                        'micro', 'notepad', 'notepad++']:
            editor = which(program)
            if editor:
                return editor

        print("Could not find a suitable editor." +
              "Please specify with '--editor'" +
              "or set the EDITOR variable in your shell.")
        sys.exit(1)


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
    try:
        open(filename)
        return True
    except FileNotFoundError:
        return False


if __name__ == "__main__":
    main()
