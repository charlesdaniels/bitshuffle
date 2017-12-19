#!/bin/sh

# .SHELLDOC
#
# Checks all shell scripts under the project TLD for compliance with
# ShellCheck.
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
# the grep -v '.git' prevents git's default hooks from causing ShellCheck
# defects.
find "$PROJECT_ROOT" -print | grep -v '.git' | while read -r line ; do
	if file "$line" | grep -i 'shell script' > /dev/null 2>&1 ; then
		echo "shellcheck for file '$line': "
		shellcheck -s sh "$line"
		RETCODE=$?
		echo ""

		# while loops are implemented as a subshell
		TOTAL="$(echo "$RETCODE + $TOTAL" | bc)"
		echo "$TOTAL" > "$TEMPFILE"
	fi
done

TOTAL="$(cat "$TEMPFILE")"
echo "$TOTAL defective files"
rm -f "$TEMPFILE"
exit "$TOTAL"
