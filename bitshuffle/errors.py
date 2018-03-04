#!/usr/bin/env python

'''Porcelain errors codes for bitshuffle'''

ERRORS = {
    0: "Success",
    1: "No arguments given",
    2: "Bad compression type",
    3: "Bad compression level",
    4: "Bad chunksize",

    101: "Editor not given",
    102: "Could not infer editor",
    103: "Editor not found",
    104: "Could not open input file",
    105: "Could not open output file",
    106: "Could not infer encode/decode",

    201: "Invalid packet",
    202: "No packets given",
    203: "Invalid base64-encoded message",
    204: "Invalid compressed message",
    205: "Packets given out of order",

    301: "Bad packet checksum",
    302: "Bad file checksum",

    401: "Internal: input not a file",
    402: "Internal: output not a file"
}
