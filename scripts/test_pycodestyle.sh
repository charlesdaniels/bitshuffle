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

TOTAL=0
RETCODE=0
TEMPFILE="/tmp/$(uuidgen)"
echo "Checking python codestyle... "
find "$PROJECT_ROOT" -print | while read -r line ; do
	if file "$line" | grep -i 'python script' > /dev/null 2>&1 ; then
		pycodestyle "$line"
		RETCODE=$?
		TOTAL="$(echo "$RETCODE + $TOTAL" | bc)"
		echo "$TOTAL" > "$TEMPFILE"
	fi
done

TOTAL="$(cat "$TEMPFILE")"
if [ "$TOTAL" -ne 0 ] ; then
	echo "$TOTAL total defects across all files"
else
	echo "PASSED"
fi
rm -f "$TEMPFILE"
exit "$TOTAL"
