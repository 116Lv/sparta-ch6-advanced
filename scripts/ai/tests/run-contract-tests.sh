#!/usr/bin/env bash
set -eu

PATH=/usr/bin:/bin:$PATH
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

/usr/bin/bash "$SCRIPT_DIR/test-runtime-preflight.sh"
/usr/bin/bash "$SCRIPT_DIR/test-command-runner.sh"
