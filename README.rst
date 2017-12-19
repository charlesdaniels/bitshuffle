#################
BitShuffle README
#################

.. contents::

Build Status
============

TravisCI:

.. image:: https://travis-ci.org/charlesdaniels/bitshuffle.svg?branch=master
    :target: https://travis-ci.org/charlesdaniels/bitshuffle

AppVeyor:

.. image:: https://ci.appveyor.com/api/projects/status/h7h2a8ltcxkk4926?svg=true
   :target: https://ci.appveyor.com/project/charlesdaniels/bitshuffle

Introduction
============

What is it?
-----------

BitShuffle is a program for encoding and decoding arbitrary binary data into
printable ASCII characters for transfer over arbitrary media. In many respects,
it can fill the same purpose as ``base64`` or ``uudecode`` / ``uuencode``,
however it is more sophisticated than these tools. Some key features that
BitShuffle offers include:

* Automatic chunking of data into arbitrary sizes.

* Automatic checksumming of data

* Automatic compression of data (bzip and gzip are both support, see #2)

* Support for both Python 2 and 3

Example Use-Cases
-----------------

* The use case which spawned the project in the first place; copying small
  files over an existing interactive ``ssh`` session without needing to
  re-authenticate when using ``scp``.

* Transferring arbitrary files over chat programs which either don't allow
  attachments, or which restrict what file types are allowed. For example
  sending a small script to a friend over GroupMe.

* Embedding arbitrary binary data in program logs (as an example, one of
  BitShuffle's authors once used a spiritual precursor to BitShuffle to pickle
  and embed live Python objects into a program's debug log for later
  interactive debugging).

* Sending e-mail attachments across e-mail servers that don't allow certain
  file types/extensions (email attachments are really just base64 encoded
  data anyway, but BitShuffle would avoid inspection by most mail services).

FAQ
---


Why Not Use Dropbox/Google Drive/MediaFire/Etc?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These services are inconvenient to use for very small or transient files; i.e.
"let me show you this cool shell script I wrote", or "here look at this 10 line
long log file".


Why Not Use PasteBin/HasteBin/Sprunge/Etc?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These services are designed specifically for transferring plain text data, and
often mangle binary data. They usually have size limitation as well.

Is This Really Useful?
~~~~~~~~~~~~~~~~~~~~~~

The authors of BitShuffle find it useful. Maybe you will too. Maybe not.

Why so Much CI / Testing?
~~~~~~~~~~~~~~~~~~~~~~~~~

The amount of automated tests may seem high for a project as small as
BitShuffle is. However, BitShuffle is intended to be a tool used on a daily
basis (as it is by it's authors), inside of pipelines, and possibly inside of
other automation. It is critical thus that it not break or behave in strange or
unusual ways for the same reason ``ls`` needs to not break on weird edge cases
- it's used too frequently.

Can I Embed BitShuffle in my Project?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Yes, but please wait until we have a stable release. The data packet format may
change without warning until there is at least one stable release.

Does BitShuffle Have a Stable API?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Not at this time, but it will in the future as the project matures a bit. Until
then use BitShuffle as a Python module at your own risk.

Installation
============

Dependancies
------------

To install/run BitShuffle:

* POSIX-ish operating system, or Windows (as of #38).

* Either Python 2, or Python 3.

To run BitShuffle's automated tests locally:

* POSIX ``sh`` compliant shell interpreter
* ``uuidgen``
* ``travis`` (hint: ``gem install travis``)
* ``bc``
* ``/tmp`` must exist and be write-able

Installing with ``setup.py``
----------------------------

Simply run ``python ./setup.py install``.

Installing Manually
-------------------

If you are only going to be using BitShuffle as a script, not as a python
module, you can also just drop ``bitshuffle/bitshuffle.py`` into ``$PATH`` (I
suggest symlinking to ``~/bin/bitshuffle``).

Installing a Binary Release
---------------------------

This is not possible yet, but in the future, there will be static builds of
BitShuffle that can be run standalone. See also #11.

Contributing
============

Contributions are welcome! Simply open a GitHub pull request. All contributions
need to pass the automated TravisCI checks.

If you would like to contribute by sending patches over e-mail, that is fine
to, just get in touch with @charlesdaniels.

Technical Details
=================


BitShuffle Data Packet Specification (compatibilty level 1)
-----------------------------------------------------------

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

Note that the data packet spec is labile to change without warning in
non-release versions of BitShuffle. Any changes made since the last release
will result in a compatibility level bump at time of release. Use non-release
versions at your own risk.

BitShuffle Automated Testing Strategy
-------------------------------------

BitShuffle is tested automatically by multiple CI systems (AppVeyor and
TravisCI), executing a large battery of tests to ensure it is functioning
correctly. These scripts are implemented in POSIX ``sh``, and are stored int
the ``scritps/`` directory. A subset of these tests that are safe to run
locally (do not modify the disk or require ``sudo``) can be executed with the
script ``scripts/pre_commit_check.sh``. **Contributors should not open PRs for
code that does not pass this script**.

Note that Windows support is tested via a PowerShell script in ``scripts/``,
which is intended to run only on AppVeyor. It executes only a few very simple
smoke tests that ensure the program can run successfully on Windows, but does
not exhaustively exercise every feature.

Most of BitShuffle's tests are end-to-end/blackbox tests that aim to validate
real-world use cases. At this time, BitShuffle is too small and monolithic for
actual unit tests to be of value. In the future, a stable public API will be
defined, at which time comprehensive unit tests will need to be written to
avoid regressions (see #39, #5).

In addition to automated functionality tests, we also adhere strictly to PEP8,
which is enforced by `pycodestyle`.

Version Number Conventions
--------------------------

BitShuffle loosely follows [Semantic Versioning](https://semver.org). The
following suffixes are used:

* No suffix - implies this is a stable release.

* ``-git`` - this version is from the BitShuffle git repository, and probably
  has not been tested.

* ``-RCX`` - the is the `Xth` release candidate for the relevant version.
