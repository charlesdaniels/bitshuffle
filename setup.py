#!/usr/bin/env python

from bitshuffle.bitshuffle import version
from setuptools import setup
from setuptools import find_packages

short_description = \
    'Transmit data over applications that restrict the files that can be sent'

long_description = '''
BitShuffle is a protocol for transmitting arbitrary bitstreams
over bitstream-hostile transmission mediums.
In particular, it is designed for use with applications
such as instant messaging programs or e-mail
which restrict the files that can be sent.
It supports multiple files and binary data,
and automatically compares the checksum
of decoded files to the hash transmitted.
'''.lstrip()  # remove leading newline

classifiers = [
    # see http://pypi.python.org/pypi?:action=list_classifiers
    'Development Status :: 3 - Alpha',
    'Environment :: Console',
    'Intended Audience :: Developers',
    'License :: OSI Approved :: BSD License',
    'Operating System :: POSIX',
    'Programming Language :: Python',
    'Programming Language :: Python :: 2',
    'Programming Language :: Python :: 3',
    'Topic :: Communications :: File Sharing'
    ]

setup(name="bitshuffle",
      version=version,
      description=short_description,
      long_description=long_description,
      author="Charles Daniels",
      author_email="cdaniels@fastmail.com",
      url="https://github.com/charlesdaniels/bitshuffle",
      license='BSD',
      classifiers=classifiers,
      keywords='checksum hash internet transmit file',
      packages=find_packages(exclude=['smoketest']),
      entry_points={'console_scripts':
                    ['bitshuffle=bitshuffle.bitshuffle:main']},
      package_dir={'bitshuffle': 'bitshuffle'},
      platforms=['POSIX']
      )
