'''Usage-independent functions'''

from __future__ import division, generators, print_function, absolute_import

import re
import bz2
import gzip
import string
import base64
import logging
from hashlib import sha256
from sys import exit as exit_with_code
from .errors import ERRORS

VERSION = '0.0.1-git'
DEBUG = False
COMPATLEVEL = "1"
DEFAULT_MSG = "This is encoded with BitShuffle, which you can download" + \
    " from https://github.com/charlesdaniels/bitshuffle "

try:  # does nothing if python3
    assert gzip.compress
    assert gzip.decompress
except AttributeError:  # python2
    import io
    # taken straight from gzip.py
    # pylint: disable=invalid-name

    def gzip_compress(data, compresslevel=5):
        # pylint: disable=missing-docstring
        buf = io.BytesIO()
        c = compresslevel
        with gzip.GzipFile(fileobj=buf, mode='wb', compresslevel=c) as f:
            f.write(data)
        return buf.getvalue()

    def gzip_decompress(data):
        # pylint: disable=missing-docstring
        with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
            return f.read()

    gzip.compress = gzip_compress
    gzip.decompress = gzip_decompress
    del gzip_compress, gzip_decompress


# By default, format is '%(levelname)s:%(name)s:%(message)s',
logging.basicConfig(format='%(name)s: %(levelname)s: %(message)s',
                    level=(logging.DEBUG if DEBUG else logging.WARN))

# idiomatic way is __name__, but logger is also called from main
LOG = logging.getLogger('bitshuffle')


def log_fmt(integer, *argv):
    '''
    int -> str
    Format a string for use with `LOG.ger`.
    Integer is the error code to show.
    Prepends colon to every successive argument given
    '''
    error = "%d: %s" % (integer, ERRORS[integer])
    for arg in argv:
        error += ": " + arg
    return error


def exit_with_error(integer, *argv, **kwargs):
    '''Issue a warning and exit with return code `integer`.
    Each successive argument is added to the warning, prepended by a colon.'''
    if 'severity' not in kwargs.keys():
        kwargs['severity'] = 3
    LOG.log(kwargs['severity'] * 10, log_fmt(integer, *argv))
    exit_with_code(integer)


def exit_successfully():
    '''exit, successfully'''
    exit_with_error(0, severity=0)


def shasum(data):
    '''Return sha256 sum of input, encdoded in base16'''
    return sha256(data).hexdigest()


def encode_data(data, chunksize=2048, compresslevel=5, compress=bz2.compress):
    """encode_data

    Compress the given data (which should be bytes), chunk it into chunksize
    sized chunks, base64 encode the chunks, and return the lot as a list of
    chunks, which are strings.

    :param data: bytes
    :param compresstype: string: bz2 or gzip
    :param compresslevel: int: 1-9 inclusive
    """

    data = compress(data, compresslevel=compresslevel)
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

    return [chunk for chunk in chunks if len(chunk) > 0]


def encode_packet(data, seqnum, seqmax, compress=bz2.compress, msg=DEFAULT_MSG,
                  file_hash=None):
    """encode_packet

    Take an already encoded data string and encode it to a BitShuffle data
    packet.

    :param data: bytes
    """

    encoding = "base64"
    packet_hash = shasum(data)
    data = data.decode()

    fmt = "((<<{}|{}|{}|{}|{}|{}|{}|{}"
    packet = fmt.format(msg, COMPATLEVEL, encoding, compress.__module__,
                        seqnum, seqmax, packet_hash, data)
    if file_hash is not None:
        packet += '|'
        packet += file_hash
    packet += '>>))'
    return packet


def encode_file(fhandle, chunksize=2048, compresslevel=5,
                compress=bz2.compress, msg=DEFAULT_MSG):
    """encode_file

    Encode the file from fhandle and return a list of strings containing
    BitShuffle data packets.

    :param fhandle:
    """

    try:
        # Python 3
        data = fhandle.buffer.read()
    except AttributeError:
        data = fhandle.read()
    file_hash = shasum(data)
    chunks = encode_data(data, chunksize, compresslevel, compress)
    seqmax = len(chunks) - 1
    seqnum = 0
    packets = []
    for chunk in chunks:
        if seqnum == 0 or seqnum == seqmax:
            packet = encode_packet(chunk, seqnum, seqmax, compress, msg,
                                   file_hash)
        else:
            packet = encode_packet(chunk, seqnum, seqmax, compress, msg)
        packets.append(packet)

        seqnum += 1

    return packets


def decode(message):
    '''Decode any number of packets previously encoded with bitshuffle
    Assumes all packets are part of the same message'''
    _, _, _, compression, seq_num, \
        _, packet_hash, chunk, file_hash = range(9)

    try:
        packets = re.findall(r'\(\(<<(.*)>>\)\)', message,
                             flags=re.MULTILINE)
    except IndexError:
        exit_with_error(201)

    if not packets:
        exit_with_error(202)

    # delete unused whitespace and separators
    packets = [re.sub("|".join(string.whitespace), "", p)
               for p in packets if p.strip() != '']

    num_chunks_wrong = 0

    # each chunk will be appended and original will be returned
    payload = bytes()
    overall_hash = None
    for index, packet in enumerate(packets):
        try:
            packet = packet.split("|")
            if packet[seq_num] != str(index):
                LOG.warning(log_fmt(205,
                                    "Given number %d does not match actual %d"
                                    % (packet[seq_num], index), "Skipping"))
                continue
        except IndexError:
            LOG.warning(log_fmt(201,
                                "Packet %d is invalid for decoding." % index,
                                "Skipping"))
            continue

        if len(packet) - 1 == file_hash:
            if overall_hash is None:
                overall_hash = packet[file_hash]
            elif packet[file_hash] != overall_hash:
                LOG.warning(log_fmt(302, "Packet" + index))

        hashed = shasum(packet[chunk].encode(encoding='ascii'))
        if hashed != packet[packet_hash]:
            num_chunks_wrong += 1
            LOG.warning(log_fmt(301,
                                ("Given hash for packet %d does not "
                                 + "match actual '%s'")
                                % (index, packet[packet_hash])))

        payload += base64.b64decode(packet[chunk])
    # pylint: disable=undefined-loop-variable
    payload = (bz2.decompress(payload) if packet[compression] == "bz2"
               else gzip.decompress(payload))

    file_hash_ok = (num_chunks_wrong == 0
                    or (overall_hash is not None
                        and shasum(payload) == overall_hash))

    if not file_hash_ok:
        if overall_hash is not None:
            LOG.warning(
                log_fmt(302, "Given hash '%s' " % overall_hash
                        + "for file does not match actual AND "
                        + "one or more chunks corrupted"))
        else:
            LOG.warning(log_fmt(301, "One or more chunks corrupted."))
    return payload, file_hash_ok
