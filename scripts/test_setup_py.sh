#!/bin/sh

# .SHELLDOC

# This script tests that BitShuffle's setup.py implementation is working
# correctly.

# .ENDOC

set -e
set -u

PARENT_DIR="$(dirname "$0")"
PROJECT_TLD="$PARENT_DIR/.."

cd "$PROJECT_TLD"
if [ ! -e "./bitshuffle" ] ; then
	echo "PANIC: failed to locate bitshuffle module directory"
	exit 999
fi

if [ ! -e "./setup.py" ] ; then
	echo "PANIC: failed to locate setup.py"
	exit 999
fi

# .DOCUMENTS do_test
#
# Tests that BitShuffle can be installed and run with a particular Python
# binary.
#
# .SYNTAX
#
# $1 . . . . Python binary to use (i.e. 'python', or '/bin/python2')
#
# .ENDOC
do_test () {

	PYTHON_BIN="$(which "$1")"
	if [ ! -x "$PYTHON_BIN" ] ; then
		echo "PANIC: failed to locate Python binary at '$PYTHON_BIN'"
		exit 999
	fi

	echo "Testing BitShuffle setup.py with '$PYTHON_BIN'"

	if [ ! -e "./bitshuffle" ] ; then
		echo "PANIC: failed to locate bitshuffle module directory"
		exit 999
	fi

	if [ ! -e "./setup.py" ] ; then
		echo "PANIC: failed to locate setup.py"
		exit 999
	fi

	if ! "$PYTHON_BIN" ./setup.py install ; then
		echo "FAIL: failed to install BitShuffle with Python '$PYTHON_BIN'"
		exit 1
	fi

	cd /

	if ! "$PYTHON_BIN" -m bitshuffle.bitshuffle --version ; then
		echo "FAIL: failed to execute BitShuffle with Python '$PYTHON_BIN'"
		exit 2
	fi

	echo "Test finished without error."

}

do_test 'python2'
do_test 'python3'
