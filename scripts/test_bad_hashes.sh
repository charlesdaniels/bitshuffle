#!/bin/sh

# .SHELLDOC

# Smoketests for checksum handling. Exit code is # of failed tests.
# Heavily influenced by existing smoketests.

# .ENDOC

# shellcheck disable=SC1090
. "$(dirname "$0")"/realpath.sh
TEST_DIR="$(realpath_sh "$(dirname "$0")")"
BITSHUFFLE="$TEST_DIR/../bitshuffle/bitshuffle.py"

if [ ! -r "$BITSHUFFLE" ] ; then
        echo "FATAL: '$BITSHUFFLE' does not exist"
        exit 9999
fi

print_log_file() {
# takes 1 parameter, a text file
        while read -r line; do
                printf "\t%s\n" "$line"
        done < "$1"
        printf "\n\n"
}

expect_empty_file() {
# takes 1 parameter, a text file
if [ -z "$(cat "$1")" ]; then
	echo "PASSED"
else
	printf "FAILED\n\n"
	echo "$1 is not empty:"
	print_log_file "$1"
	TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
	rm -f "$1"
fi
}

cd "$TEST_DIR/../bitshuffle" || exit 999

TESTS_FAILED=0

LOG_FILE="/tmp/$(uuidgen)"
printf "Ignores missing file hash... "
python -c 'from bitshuffle import decode
decode("((<<This is encoded with BitShuffle, which you can download from https://github.com/charlesdaniels/bitshuffle|1|base64|bz2|0|0|4987450aeb4a67414aa0547d0f1e4bb3eae3dd86|QlpoNTFBWSZTWSgWZeAAAAbRgAAQQAAC45wAIAAiAAyEDQNB46s3DIBBbxdyRThQkCgWZeA=>>))")' \
> "$LOG_FILE" 2>&1
expect_empty_file "$LOG_FILE"

LOG_FILE="/tmp/$(uuidgen)"
printf "Ignores bad file hash if chunks are OK... "
python -c 'from bitshuffle import decode
decode("((<<This is encoded with BitShuffle, which you can download from https://github.com/charlesdaniels/bitshuffle|1|base64|bz2|0|0|4987450aeb4a67414aa0547d0f1e4bb3eae3dd86|QlpoNTFBWSZTWSgWZeAAAAbRgAAQQAAC45wAIAAiAAyEDQNB46s3DIBBbxdyRThQkCgWZeA=|bad file hash>>))")' \
> "$LOG_FILE" 2>&1
expect_empty_file "$LOG_FILE"

LOG_FILE="/tmp/$(uuidgen)"
printf "Warns of bad chunk hash... "
python -c 'from bitshuffle import decode
decode("((<<This is encoded with BitShuffle, which you can download from https://github.com/charlesdaniels/bitshuffle|1|base64|bz2|0|0|bad packet hash|QlpoNTFBWSZTWQxmjYsAAAlRgAAQQAAC55wAIAAiBqMmZQgGgCRGntZoXLR8Ep+LuSKcKEgGM0bFgA|075053ad253678f9f5c6f2dc662c967979e4ee67==>>))")' \
> "$LOG_FILE" 2>&1
if grep -i "WARNING: Given hash for packet .* does not match actual" \
	"$LOG_FILE" > /dev/null 2>&1; then
	echo "PASSED"
else
	printf "FAILED\n\n"
	print_log_file "$LOG_FILE"
	TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
	rm -f "$LOG_FILE"
fi


LOG_FILE="/tmp/$(uuidgen)"
printf "Warns if both file and chunk hash bad... "
python -c 'from bitshuffle import decode
decode("((<<This is encoded with BitShuffle, which you can download from https://github.com/charlesdaniels/bitshuffle|1|base64|bz2|0|0|bad packet hash|QlpoNTFBWSZTWaeQs/cAAAPRgAAQQAAqCUSAIAAxADAgA2ogxC5DeLuSKcKEhTyFn7g=|bad file hash>>))")' \
> "$LOG_FILE" 2>&1
if grep -i 'WARNING: Given hash .* for file does not match' "$LOG_FILE" \
	> /dev/null 2>&1; then
	echo "PASSED"
else
	printf "FAILED\n\n"
	print_log_file "$LOG_FILE"
	TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
	rm -f "$LOG_FILE"
fi

LOG_FILE="/tmp/$(uuidgen)"
printf "Warns missing file hash with bad packet hash..."
python -c 'from bitshuffle import decode
decode("((<<This is encoded with BitShuffle, which you can download from https://github.com/charlesdaniels/bitshuffle|1|base64|bz2|0|0|bad packet hash|QlpoNTFBWSZTWaeQs/cAAAPRgAAQQAAqCUSAIAAxADAgA2ogxC5DeLuSKcKEhTyFn7g=>>))")' \
> "$LOG_FILE" 2>&1
if grep -i 'WARNING: Given hash for packet [0-9]\+ does not match actual hash \S\+' "$LOG_FILE" \
	> /dev/null 2>&1; then
	echo "PASSED"
else
	printf "FAILED\n\n"
	print_log_file "$LOG_FILE"
	TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
	rm -f "$LOG_FILE"
fi

printf "\n%s tests failed.\n" "$TESTS_FAILED"
exit "$TESTS_FAILED"