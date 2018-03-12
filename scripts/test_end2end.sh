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
BITSHUFFLE="$PARENT_DIR/../wrapper.py"

if [ ! -x "$BITSHUFFLE" ] ; then
	echo "FATAL: '$BITSHUFFLE' does not exist or is not executable"
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
			printf "\t%s\n" "$ln"
		done < "$LOG_FILE"
		printf "\n\n"
		TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
	fi
	rm -f "$LOG_FILE" "$TEMPFILE_SRC" "$TEMPFILE_DST"
}

all_tests () {

    printf "Basic encode/decode test... "
    do_test '$BITSHUFFLE --encode < "$TEMPFILE_SRC" | \
        $BITSHUFFLE --decode > "$TEMPFILE_DST"'

    printf "Basic encode/decode test (non-default message)... "
    do_test '$BITSHUFFLE --encode < "$TEMPFILE_SRC" --message foo | \
        $BITSHUFFLE --decode > "$TEMPFILE_DST"'

    printf "Basic encode/decode test (large chunk size)... "
    do_test '$BITSHUFFLE --encode < "$TEMPFILE_SRC" --chunksize 16384 | \
        $BITSHUFFLE --decode > "$TEMPFILE_DST"'


    printf "Basic encode/decode test (small chunk size)... "
    do_test '$BITSHUFFLE --encode < "$TEMPFILE_SRC" --chunksize 8 | \
        $BITSHUFFLE --decode > "$TEMPFILE_DST"'


    printf "Double encode/decode test... "
    do_test '$BITSHUFFLE --encode < "$TEMPFILE_SRC" | \
        $BITSHUFFLE --encode | $BITSHUFFLE --decode | \
        $BITSHUFFLE --decode > "$TEMPFILE_DST"'

    printf "GZIP test... "
    do_test '$BITSHUFFLE --encode --compresstype "gzip" < "$TEMPFILE_SRC" | \
        $BITSHUFFLE --decode > "$TEMPFILE_DST"'

    printf "BZIP test... "
    do_test '$BITSHUFFLE --encode --compresstype "bz2" < "$TEMPFILE_SRC" | \
        $BITSHUFFLE --decode > "$TEMPFILE_DST"'

    printf "Unicode test... "
    TEMPFILE_SRC="$(uuidgen)"
    TEMPFILE_DST="$(uuidgen)"
    LOG_FILE="$(uuidgen)"
    echo '←↑→↓↔↕↖↗↘↜↛↠↢↮↹⇆⇏⇚⇼⇿∀∁∂∃∄∅∆∈∉∋∎∐∓∗√∦∯∿' > "$TEMPFILE_SRC"
    TEMPFILE_SRC_SHA="$(shasum "$TEMPFILE_SRC" 2>&1 | cut -d ' ' -f 1)"
    ($BITSHUFFLE --encode < "$TEMPFILE_SRC" | \
    $BITSHUFFLE --decode > "$TEMPFILE_DST") > "$LOG_FILE" 2>&1
	TEMPFILE_DST_SHA="$(shasum "$TEMPFILE_DST" 2>&1 | cut -d ' ' -f 1)"
	if [ "$TEMPFILE_DST_SHA" = "$TEMPFILE_SRC_SHA" ] ; then
		echo "PASSED"
	else
		printf "FAILED\n\n"

		printf "\t%s does not match %s\n" "$TEMPFILE_SRC_SHA" "$TEMPFILE_DST_SHA"
		echo
		while read -r ln  ; do
			printf "\t%s\n" "$ln"
		done < "$LOG_FILE"
		printf "\n\n"
		TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
    fi
	rm -f "$LOG_FILE" "$TEMPFILE_SRC" "$TEMPFILE_DST"

    printf "Test infer encode from no arguments and non-interactive tty... "
    do_test '$BITSHUFFLE < "$TEMPFILE_SRC" | \
         $BITSHUFFLE --decode > "$TEMPFILE_DST"'

    # TODO: infer encode/decode from what input looks like
#    printf "Test infer decode from non-tty stdin... "
#    do_test '$BITSHUFFLE --encode < "$TEMPFILE_SRC" | \
#        $BITSHUFFLE > "$TEMPFILE_DST"'

}

echo "Running end-to-end tests..."

TESTS_FAILED=0

all_tests

printf "%s tests failed\n\n" "$TESTS_FAILED"
exit $TESTS_FAILED
