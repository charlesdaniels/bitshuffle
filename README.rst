#################
BitShuffle README
#################

.. contents::

Build Status
============

.. image:: https://travis-ci.org/charlesdaniels/bitshuffle.svg?branch=master
    :target: https://travis-ci.org/charlesdaniels/bitshuffle

Introduction
============

BitShuffle is a protocol for transmitting arbitrary bitstreams over
bitstream-hostile transmission mediums. In particular, it is designed for use
with applications such as instant messaging program or e-mail. The use case is
for transmitting arbitrary files through services that restrict files that can
be sent. For example:

* Email systems that restrict what types of files can be attached to emails.
* Instant messaging services that allow only certain types of files to be sent,
  or none at all.

FAQ
---

Why Not Use Dropbox/Google Drive/MediaFire/Etc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These services are inconvenient to use for very small or transient files; i.e.
"let me show you this cool shell script I wrote".

Why Not Use PasteBin/HasteBin/Sprunge/Etc
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These services are designed specifically for transferring plain text data, and
often mangle binary data. They usually have size limitations, and do not
support multiple files.

CONTRIBUTING
---

The only thing needed to run the executable is python (2 or 3). However,
the tests require `bc`, `uuidgen`, and `shasum`. On debian-based systems, these
can be installed with `sudo apt-get install bc uuid-runtime coreutils`.

BitShuffel Data Packet Specification
====================================

A BitShuffle data packet is a sequence of ASCII text. A data packet may be
arbitrarily long. A data backed may contain arbitrary whitespace, which is
stripped during processing.

A BitShuffle packet is surrounded by special sigil characters:

* It is preceeded by the string literal ``((<<`` (opening token)
* It is succeeded by the string literal ``>>))`` (closing token)

These string literals are deliberately selected to avoid common markup
characters, such as ``#``, ``@``, and ``*``, which are frequency used by
messaging services to denote special formatting for messages.

The data packed is comprised of several *segments*. A *segment* begins with
either the opening token or the ``|`` character. A segment ends with either the
closing token or a ``|`` character. A segment may contain only the characters
``a-zA-Z0-9``, as well as ``=``, ``:``, ``/``, ``+``, ``-``. Again, keep in mind that
whitespace is ignored entirely.

The data packed contains the following segments, in order:

* Message indicating that this a BitShuffle data packet, with a link to
  download BitShuffle.
* BitShuffle data packet format compatibility level (currently set to ``1``).
* BitShuffle data encoding format (current set to ``base64``).
* BitShuffle data compression type (currently set to ``bz2``).
* BitShuffle packet sequence number (i.e. `23`).
* BitShuffle packet sequence end (the sequence number of the last packet in the
  message).
* BitShuffle data checksum (encoded)
* BitShuffle data chunk (encoded)


Segments marked as *encoded* indicate their contents is arbitrary data which
has been compressed with the specified compression type, and encoded with the
specified encoding format.

As an example, the following BitShuffle packets encode a tarball of the
BitShuffle source code and this README::

        ((<<This is a BitShuffle encoded file, download BitShuffle from https://github.com/charlesdaniels/bitshuffle|1|base64|bz2|0|1|874c105c72b670fc3b659fe1808a09eae31c7417|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>>))
        ((<<This is a BitShuffle encoded file, download BitShuffle from https://github.com/charlesdaniels/bitshuffle|1|base64|bz2|1|1|bitshuffle.tar|874c105c72b670fc3b659fe1808a09eae31c7417|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>>))
