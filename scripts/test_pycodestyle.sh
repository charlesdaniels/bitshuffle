#!/bin/sh

# .SCRIPTDOC
#
# Run PyCodeStyle on every python file under the project root.
#
# .ENDOC

set -u

. "$(dirname $0)/realpath.sh"
PARENT_DIR="$(realpath_sh $(dirname "$0"))"
PROJECT_ROOT="$PARENT_DIR/.."

TOTAL=0
RETCODE=0
TEMPFILE="/tmp/$(uuidgen)"
find "$PROJECT_ROOT" -print | while read -r line ; do
	if file "$line" | grep -i 'python script' > /dev/null 2>&1 ; then
		echo "pycodestyle for file '$line': "
		pycodestyle "$line"
		RETCODE=$?
		echo ""

		TOTAL="$(echo "$RETCODE + $TOTAL" | bc)"

		# this is a totally disgusting hack to exfiltrate data from the
		# subshell that gets spawned by this while loop
		echo "$TOTAL" > "$TEMPFILE"
	fi
done

TOTAL="$(cat "$TEMPFILE")"
echo "$TOTAL total defects across all files"

rm "$TEMPFILE"
exit $TOTAL


