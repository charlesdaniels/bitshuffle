#!/bin/sh
printf "\nChecking for valid .travis.yml config... "

LOG_FILE="/tmp/$(uuidgen)"
. "$(dirname $0)/realpath.sh"
PARENT_DIR="$(realpath_sh $(dirname "$0"))"
PROJECT_ROOT="$PARENT_DIR/.."

if travis lint "$PROJECT_ROOT/.travis.yml" 1>$LOG_FILE 2>&1; then
    echo "PASSED"
    exit 0
else
    echo "FAILED"
    while read -r ln; do
        printf "\t$ln\n"
    done < "$LOG_FILE"
    exit 1
fi
