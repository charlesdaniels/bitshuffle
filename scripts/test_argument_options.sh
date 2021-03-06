#!/bin/bash

# .SHELLDOC

# Smoketests for argument handling. Exit code is # of failed tests.
# Heavily influenced by existing smoketests.

# .ENDOC

# shellcheck disable=SC1090
. "$(dirname "$0")/realpath.sh"
TEST_DIR="$(realpath_sh "$(dirname "$0")")"
BITSHUFFLE="$TEST_DIR/../bitshuffle/bitshuffle.py"
TESTS_FAILED=0

if [ ! -x "$BITSHUFFLE" ] ; then
        echo "FATAL: '$BITSHUFFLE' does not exist"
        exit 9999
fi

# Note: of necessity, the following can only test non-interactive
# situations. Interactive tests are not a priority at the current moment.

print_log_file() {
# takes 1 parameter, a text file
        while read -r line; do
                printf "\t%s\n" "$line"
        done < "$1"
        printf "\n\n"
}


expect_usage_error () {
        LOG_FILE="/tmp/$(uuidgen)"
        # shellcheck disable=SC2068
        $BITSHUFFLE $@ > "$LOG_FILE" 2>&1
        if grep -q "usage: .*" "$LOG_FILE" ; then
                echo "PASSED"
        else
                printf "FAILED\n\n"

                printf "\t'usage: .*' does not match logfile\n\n"
                print_log_file "$LOG_FILE"
                TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
                rm -f "$LOG_FILE"
        fi
}

printf "Running tests...\n\n"

printf "When run with no args, prints help... "
expect_usage_error

printf "When run with '-h', prints help... "
expect_usage_error -h

printf "When given bad compresstype, prints help... "
expect_usage_error -t gmander

# Can't be tested non-interactively
#printf "When given bad editor, prints editor not found... "
#LOG_FILE="/tmp/`uuidgen`"
#$BITSHUFFLE --decode --editor /nonexistent > "$LOG_FILE" 2>&1
#if [ "`cat $LOG_FILE`" = "Editor /nonexistent not found" ]; then
#        echo "PASSED"
#else
#        printf "FAILED\n\n"

#        printf "'Editor /nonexistent not found' does not match logfile\n\n"

#        print_log_file $LOG_FILE
#        TESTS_FAILED="`echo $TESTS_FAILED + 1 | bc`"
#        rm -f $LOG_FILE
#fi

LOG_FILE="/tmp/$(uuidgen)"
printf "When given bad input, prints file not found... "
$BITSHUFFLE --input /nonexistent/nope > "$LOG_FILE" 2>&1
if grep -i 'could not open' < "$LOG_FILE" > /dev/null 2>&1 ; then
    echo "PASSED"
else
    printf "FAILED\n\n"

    print_log_file "$LOG_FILE"
    TESTS_FAILED="$(echo "$TESTS_FAILED + 1" | bc)"
    rm -f "$LOG_FILE"
fi

printf "\n%s tests failed.\n" "$TESTS_FAILED"
exit "$TESTS_FAILED"
