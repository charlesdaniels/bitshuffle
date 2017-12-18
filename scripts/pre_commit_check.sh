#!/bin/sh

# .SCRIPTDOC
#
# This script runs *most* of the tests that would normally be run by TravisCI,
# with the exception of those that would require root access or modify the
# filesystem of the host machine. This script should be run before committing.
#
# .ENDOC

. "$(dirname $0)/realpath.sh"
PARENT_DIR="$(realpath_sh $(dirname "$0"))"

"$PARENT_DIR/test_end2end.sh"
RET1=$?
"$PARENT_DIR/test_argument_options.sh"
RET2=$?
"$PARENT_DIR/test_pycodestyle.sh"
RET3=$?
"$PARENT_DIR/test_travis_lint.sh"
RET4=$?

TOTAL_FAILED=$(echo "$RET1 + $RET2 + $RET3 + $RET4" | bc)
echo ""
echo "- - - - -"
echo "$TOTAL_FAILED total test failures"
if [ $TOTAL_FAILED -gt 0 ] ; then
	echo "One or more problems found, please fix these before committing."
else
	echo "Everything looks ok, proceed with commit."
fi

exit $TOTAL_FAILED
