#!/bin/bash
set -eu

case "$0" in
  */*) SCRIPT_LOCATION=${0%/*} ;;
  *) SCRIPT_LOCATION=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_LOCATION" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
if [ ! -f "$ROOT/scripts/ai/workflow_helper.py" ]; then
  printf '%s\n' '{"operation":"PREFLIGHT","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'
  exit 3
fi

invalid_arguments=0
if [ "$#" -gt 1 ] || { [ "$#" -eq 1 ] && [ "$1" != "--record" ]; }; then
  invalid_arguments=1
fi

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
    3\|Draft202012Validator\|FormatChecker) ;;
    *) continue ;;
  esac
  if [ "$invalid_arguments" = "1" ]; then
    exec "$candidate" "$ROOT/scripts/ai/workflow_helper.py" preflight --repository-root "$ROOT" --runtime-command "$candidate_name" --invalid-arguments
  fi
  if [ "$#" -eq 1 ]; then
    exec "$candidate" "$ROOT/scripts/ai/workflow_helper.py" preflight --repository-root "$ROOT" --runtime-command "$candidate_name" --record
  fi
  exec "$candidate" "$ROOT/scripts/ai/workflow_helper.py" preflight --repository-root "$ROOT" --runtime-command "$candidate_name"
done

printf '%s\n' '{"operation":"PREFLIGHT","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'
exit 3
