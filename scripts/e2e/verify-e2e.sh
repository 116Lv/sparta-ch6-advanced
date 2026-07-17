#!/bin/sh
set -eu

if [ "$#" -ne 0 ]; then
    printf '%s\n' 'Usage: scripts/e2e/verify-e2e.sh' >&2
    exit 64
fi

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
printf '%s\n' '=== E2E scenario 1/2: single instance ==='
sh "$SCRIPT_DIR/verify-single-instance.sh"
printf '%s\n' '=== E2E scenario 2/2: multi instance with k6 ==='
sh "$SCRIPT_DIR/verify-multi-instance.sh"
printf '%s\n' 'All registered E2E scenarios completed.'
