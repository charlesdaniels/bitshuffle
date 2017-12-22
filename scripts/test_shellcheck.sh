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
TEMPFILE="/tmp/$(uuidgen)"
printf "Checking shellscripts... "
# the grep -v '.git' prevents git's default hooks from causing ShellCheck
# defects.
find "$PROJECT_ROOT" -print | grep -v '.git' | while read -r line ; do
	if file "$line" | grep -i 'shell script' > /dev/null 2>&1 ; then
		shellcheck -s sh "$line"
		RETCODE=$?
		if [ "$RETCODE" -ne 0 ] ; then
			TOTAL="$(echo "$RETCODE + $TOTAL" | bc)"
		fi
		echo "$TOTAL" > "$TEMPFILE"
	fi
done

TOTAL="$(cat "$TEMPFILE")"
if [ "$TOTAL" -ne 0 ] ; then
	printf "\n%s defective files\n" "$TOTAL"
else
	echo "PASSED"
fi
rm -f "$TEMPFILE"
exit "$TOTAL"
