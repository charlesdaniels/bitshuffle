#!/bin/sh

# .SHELLDOC

# Basic end-to-end tests for BitShuffle. Exit code is # of failed tests.

# .ENDOC

PARENT_DIR="$(dirname "$0")"
BITSHUFFLE="$PARENT_DIR/../bitshuffle/bitshuffle.py"
BITSHUFFLE2="python2 $BITSHUFFLE"
BITSHUFFLE3="python3 $BITSHUFFLE"
if [ ! -x "$BITSHUFFLE" ] ; then
	echo "FATAL: '$BITSHUFFLE' does not exist"
	exit 9999
fi

make_random () {
	dd if=/dev/urandom of="$1" bs=1024 count=64 > /dev/null 2>&1
}

do_test () {
	# requires $1 to be a string literal of the test you wish to execute.
	# see below for examples
	LOG_FILE="/tmp/$(uuidgen)"
	TEMPFILE_SRC="/tmp/$(uuidgen)"
	TEMPFILE_DST="/tmp/$(uuidgen)"
	make_random "$TEMPFILE_SRC"
	TEMPFILE_SRC_SHA="$(shasum "$TEMPFILE_SRC" 2>&1 | cut -d ' ' -f 1)"
	eval "$1" > "$LOG_FILE" 2>&1
	TEMPFILE_DST_SHA="$(shasum "$TEMPFILE_DST" 2>&1 | cut -d ' ' -f 1)"
	if [ "$TEMPFILE_DST_SHA" = "$TEMPFILE_SRC_SHA" ] ; then
		echo "PASSED"
	else
		printf "FAILED\n\n"

		printf "\t$TEMPFILE_SRC_SHA does not match $TEMPFILE_DST_SHA\n"
		echo
		while read -r ln  ; do
			printf "\t$ln\n"
		done < "$LOG_FILE"
		printf "\n\n"
		TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
	fi
	rm -f "$LOG_FILE"
	rm -f "$TEMPFILE_SRC"
	rm -f "$TEMPFILE_DST"
}

all_tests () {

    printf "Basic encode/decode test... "
    do_test '$BITSHUFFLE --encode --input "$TEMPFILE_SRC" | \
        $BITSHUFFLE --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1'


    printf "Basic encode/decode test (large chunk size)... "
    do_test '$BITSHUFFLE --encode --input "$TEMPFILE_SRC" --chunksize 16384 | \
        $BITSHUFFLE --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1'


    printf "Basic encode/decode test (small chunk size)... "
    do_test '$BITSHUFFLE --encode --input "$TEMPFILE_SRC" --chunksize 8 | \
        $BITSHUFFLE --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1'


    printf "Double encode/decode test... "
    do_test '$BITSHUFFLE --encode --input "$TEMPFILE_SRC" | \
        $BITSHUFFLE --encode | $BITSHUFFLE --decode | \
        $BITSHUFFLE --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1'


    printf "GZIP test... "
    do_test '$BITSHUFFLE --encode --compresstype "gzip" --input "$TEMPFILE_SRC" | \
        $BITSHUFFLE --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1'


    printf "BZIP test... "
    do_test '$BITSHUFFLE --encode --compresstype "bz2" --input "$TEMPFILE_SRC" | \
        $BITSHUFFLE --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1'

}

echo "Running tests..."

TESTS_FAILED=0

printf "\nChecking for valid .travis.yml config... "
LOG_FILE="/tmp/$(uuidgen)"
if travis lint .travis.yml 1>$LOG_FILE 2>&1; then
    echo "PASSED"
else
    echo "FAILED"
    TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
    while read -r ln; do
        printf "\t$ln\n"
    done < "$LOG_FILE"
fi

printf "\nRunning Python2 tests...\n"
BITSHUFFLE="$BITSHUFFLE2"
all_tests

printf "\nRunning Python3 tests...\n"
BITSHUFFLE="$BITSHUFFLE3"
all_tests

printf "\n$TESTS_FAILED tests failed\n"
exit $TESTS_FAILED