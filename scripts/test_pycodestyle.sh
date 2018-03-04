#!/bin/sh

# .SCRIPTDOC
#
# Run PyCodeStyle on every python file under the project root.
#
# .ENDOC

set -u

# shellcheck disable=SC1090
. "$(dirname "$0")/realpath.sh"
PARENT_DIR="$(realpath_sh "$(dirname "$0")")"
PROJECT_ROOT="$PARENT_DIR/.."

TEMPFILE="/tmp/$(uuidgen)"
echo "Checking python codestyle... "
for line in $PROJECT_ROOT/**.py; do
	if file "$line" | grep -i 'python script' > /dev/null 2>&1 ; then
		pycodestyle "$line"
		RETCODE=$?
		EXCEPTIONS="$(grep 'except\( Exception\)\?:' "$line" | tee /dev/tty | wc -l)"
		echo "$EXCEPTIONS + $RETCODE" | bc > "$TEMPFILE"
	fi
done

TOTAL="$(cat "$TEMPFILE")"

# error code increases by 1 for each 10% off
# score is out of 10
SCORE="$(pylint -f colorized "$PROJECT_ROOT/bitshuffle" 2>/dev/null | tee /dev/tty | tail -2 | head -1 | cut -d ' ' -f 7 | cut -d / -f 1)"
PERCENT_WRONG="$(echo "100 - $SCORE * 10" | bc | xargs printf %.0f)"
TOTAL="$(echo "$PERCENT_WRONG / 10 + $TOTAL" | bc)"

if [ "$TOTAL" -ne 0 ] ; then
	echo "$TOTAL total defects across all files"
else
	echo "PASSED"
fi
rm -f "$TEMPFILE"
exit "$TOTAL"
