#################
BitShuffle README
#################

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
``a-zA-Z0-9``, as well as ``:``, ``/``, ``+``, ``-``. Again, keep in mind that
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
* Name of encoded file
* BitShuffle data checksum (encoded)
* BitShuffle data chunk (encoded)


Segments marked as *encoded* indicate their contents is arbitrary data which
has been compressed with the specified compression type, and encoded with the
specified encoding format.

An example of a BitStream data packet might be::

        ((<<an informative message|1|base64|bz2|1|1|coolstuf.zip|encoded checksum|encoded data chunk>>))


