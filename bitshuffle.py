#!/usr/bin/env python3

# .SHELLDOC
#
# BitShuffle command-line client. Supports encoding & decoding.
#
# .ENDOC

import os
import sys
import argparse
import base64
import bz2
import hashlib
import re
import string

stderr = sys.stderr
stdout = sys.stdout
stdin = sys.stdin


def encode_data(data, chunksize, compresslevel):
    """encode_data

    Compress the given data (which should be bytes), chunk it into chunksize
    sized chunks, base64 encode the chunks, and return the lot as a list of
    chunks, which are strings.

    :param data:
    :param compresslevel:
    """

    data = bz2.compress(data, compresslevel)

    chunks = []
    chunkptr = 0
    while True:
        chunk = data[chunkptr:chunkptr + chunksize - 1]
        chunkptr += chunksize

        chunks.append(base64.b64encode(chunk))

        if chunkptr > len(data):
            chunks.append(base64.b64encode(data[chunkptr:]))
            break

    chunksfinal = []
    for c in chunks:
        if len(c) > 0:
            chunksfinal.append(c)

    return chunksfinal


def encode_packet(data, filename, checksum, seqnum, seqmax):
    """encode_packet

    Take an already encoded data string and encode it to a BitShuffle data
    packet.

    :param data:
    """

    msg = "This is a BitShuffle encoded file, download BitShuffle " + \
        "from https://github.com/charlesdaniels/bitshuffle"
    compatlevel = "1"
    encoding = "base64"
    compression = "bz2"
    data = data.decode(encoding="ascii")

    fmt = "((<<{}|{}|{}|{}|{}|{}|{}|{}|{}>>))"
    packet = fmt.format(msg, compatlevel, encoding, compression, seqnum,
                        seqmax, filename, checksum, data)
    return packet


def encode_file(fhandle, chunksize, compresslevel, filename):
    """encode_file

    Encode the file from fhandle and return a list of strings containing
    BitShuffle data packets.

    :param fhandle:
    """

    data = fhandle.read()
    checksum = hashlib.sha1(data).hexdigest()
    chunks = encode_data(data, chunksize, compresslevel)
    seqmax = len(chunks) - 1
    seqnum = 0
    packets = []
    for c in chunks:
        packets.append(encode_packet(c, filename, checksum, seqnum, seqmax))
        seqnum += 1

    return packets


def main():
    have_term = stdin.isatty()

    parser = argparse.ArgumentParser(description="")

    parser.add_argument("--input", "-i", default="/dev/stdin",
                        help="Input file. Default is stdin.")
    parser.add_argument("--output", "-o", default="/dev/stdout",
                        help="Output file. Default is stdout.")

    parser.add_argument("--filename", "-f", default=None,
                        help="Set filename to use when encoding " +
                        "explicitly")

    iochoice = parser.add_mutually_exclusive_group(required=True)

    iochoice.add_argument("--encode", "-e", action="store_true",
                          help="Generate a BitShuffle data packet from " +
                          "the input file")

    iochoice.add_argument("--decode", "-d", "-D", action="store_true",
                          help="Extract a BitShuffle data packet.")

    parser.add_argument("--chunksize", "-c", type=int, default=2048,
                        help="Chunk size in bytes")

    parser.add_argument("--compresslevel", '-m', type=int, default=5,
                        help="bz2 compression level when encoding")

    args = parser.parse_args()

    if args.filename is None:
        args.filename = os.path.basename(args.input)

    if args.encode:
        with open(args.input, 'rb') as f:
            packets = encode_file(f, args.chunksize, args.compresslevel,
                                  args.filename)
            for p in packets:
                with open(args.output, 'w') as of:
                    of.write(p)
                    of.write("\n")

    elif args.decode:
        with open(args.input, 'rb') as f:
            f = decode(f.read().decode('ascii'))
            with open(args.output, 'w') as of:
                    of.write(f)
                    of.write('\n')


def decode(message):
        comment, compatibility, encoding, compression, seq_num, seq_end, name, checksum, chunk = range(9)

        message = re.sub("|".join(string.whitespace) + "|>>\)\)", "", message) # delete unused whitespace and seperators
        try:
            packets = re.split('\(\(<<(.*)>>\)\)', message, flags=re.MULTILINE)
        except IndexError:
            quit("Invalid packet to decode. Aborting.")

        segments = [None]*len(packets) # ordered by index of packets
        original = "" # each chunk will be appended and original will be returned
        for index, packet in enumerate(packets):
             try:
                 segments[index] = re.split("\|", packet, flags=re.MULTILINE)
                 if segments[index][seq_num] != str(index):
                     raise RuntimeWarning("Sequence number %s does not match actual order %d" % (segments[index][seq_num], index))
             except IndexError:
                 return "Packet %d is invalid for decoding. Aborting." % index
                 print(segments[index][chunk], file=stderr)
             reversed = base64.b64decode(segments[index][chunk])
             original += bz2.decompress(reversed).decode('ascii')
        return verify(original.encode(), segments[index][checksum])


def verify(data, given_hash):
    """verify:
    Ensure that hash of data and given hash match up. Currently, only a warning is emmitted if they do not.
    :param data: byte-like object
    :param given_hash: string
    """
    if hashlib.sha1(data).hexdigest() != given_hash:
        raise RuntimeWarning("Hashes do not match. Continuing, but you may want to investigate.", file=stderr);
        return False;
    return True;


if __name__ == "__main__":
    main()
