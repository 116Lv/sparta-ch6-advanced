#!/usr/bin/env bash
set -eu

PATH=/usr/bin:/bin:$PATH
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

cd "$REPOSITORY_ROOT"
python -m unittest scripts.ai.tests.test_workflow_helper -v
/usr/bin/bash "$SCRIPT_DIR/test-runtime-preflight.sh"
/usr/bin/bash "$SCRIPT_DIR/test-command-runner.sh"
