#!/bin/bash
set -eu

[ "$#" -eq 0 ] || exit 5
case "$0" in
  */*) SCRIPT_LOCATION=${0%/*} ;;
  *) SCRIPT_LOCATION=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_LOCATION" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
cd "$ROOT"
probe='import sys; from jsonschema import Draft202012Validator, FormatChecker; print(f"{sys.version_info.major}|{Draft202012Validator.__name__}|{FormatChecker.__name__}")'
for candidate_name in python3 python; do
  candidate=$(command -v "$candidate_name" 2>/dev/null || true)
  case "$candidate" in
    /*) ;;
    *) continue ;;
  esac
  [ -f "$candidate" ] && [ -x "$candidate" ] || continue
  result=$("$candidate" -c "$probe" 2>/dev/null || true)
  case "$result" in
    3\|Draft202012Validator\|FormatChecker) exec "$candidate" -m unittest scripts/ai/tests/test_workflow_helper.py -v ;;
  esac
done
exit 3
