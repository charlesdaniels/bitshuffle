#!/bin/sh
# shellcheck disable=SC2016
# shellcheck disable=SC1004

# SC2016 is disabled because we have lots of string literals that get eval-ed
# later in the script.

# SC1004 is disabled because there are a number of places where we want
# backslash + newline litera in this script.

# .SHELLDOC

# Basic end-to-end tests for BitShuffle. Exit code is # of failed tests.

# .ENDOC

# shellcheck disable=SC1090
. "$(dirname "$0")/realpath.sh"
PARENT_DIR="$(realpath_sh "$(dirname "$0")")"
PROJECT_ROOT="$PARENT_DIR/.."
BITSHUFFLE_FILE="$PROJECT_ROOT/bitshuffle/bitshuffle.py"

# shellcheck disable=SC2034
BITSHUFFLE="python $BITSHUFFLE_FILE"
# this variable appears unused to ShellCheck because it is only used inside
# of eval-ed code.

if [ ! -f "$BITSHUFFLE_FILE" ] ; then
	echo "FATAL: '$BITSHUFFLE_FILE' does not exist"
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

		printf "\t%s does not match %s\n" "$TEMPFILE_SRC_SHA" "$TEMPFILE_DST_SHA"
		echo
		while read -r ln  ; do
			printf "\t%n\n" "$ln"
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

    printf "Test infer encode from --input... "
    do_test '$BITSHUFFLE --input "$TEMPFILE_SRC" | \
        $BITSHUFFLE --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1'

    printf "Test infer decode from --output and non-tty stdin... "
    do_test '$BITSHUFFLE --encode --input "$TEMPFILE_SRC" | \
        $BITSHUFFLE --output "$TEMPFILE_DST"'


}

echo "Running tests..."

TESTS_FAILED=0

all_tests

printf "\n%s tests failed\n" "$TESTS_FAILED"
exit $TESTS_FAILED
