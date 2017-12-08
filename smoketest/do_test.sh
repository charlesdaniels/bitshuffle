#!/bin/sh

# .SHELLDOC

# Basic smoketests for BitShuffle. Exit code is # of failed tests.

# .ENDOC

PARENT_DIR="$(dirname "$0")"
BITSHUFFLE="$PARENT_DIR/../bitshuffle.py"

if [ ! -x "$BITSHUFFLE" ] ; then
	echo "FATAL: '$BITSHUFFLE' does not exist"
	exit 9999
fi

make_random () {
	dd if=/dev/urandom of="$1" bs=1024 count=4 > /dev/null 2>&1
}

printf "Running tests...\n"

TESTS_FAILED=0
printf "Basic encode/decode test... "

LOG_FILE="/tmp/$(uuidgen)"
TEMPFILE_SRC="/tmp/$(uuidgen)"
TEMPFILE_DST="/tmp/$(uuidgen)"
make_random "$TEMPFILE_SRC"
TEMPFILE_SRC_SHA="$(shasum "$TEMPFILE_SRC" 2>&1 | cut -d ' ' -f 1)"
"$BITSHUFFLE" --encode --input "$TEMPFILE_SRC" | \
	"$BITSHUFFLE" --decode --output "$TEMPFILE_DST" > "$LOG_FILE" 2>&1
TEMPFILE_DST_SHA="$(shasum "$TEMPFILE_DST" 2>&1 | cut -d ' ' -f 1)"
if [ "$TEMPFILE_DST_SHA" = "$TEMPFILE_SRC_SHA" ] ; then
	printf "PASSED\n"
else
	printf "FAILED\n"
	printf "\n"
	printf "\t$TEMPFILE_SRC_SHA does not match $TEMPFILE_DST_SHA\n"
	printf "\n"
	while read -r ln  ; do
		printf "\t$ln\n"
	done < "$LOG_FILE"
	printf "\n\n"
	TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
fi
rm -f "$LOG_FILE"
rm -f "$TEMPFILE_SRC"
rm -f "$TEMPFILE_DST"

printf "\n"
printf "$TESTS_FAILED tests failed\n"
exit $TESTS_FAILED
