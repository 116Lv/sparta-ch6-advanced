#!/bin/bash
set -eu

case "$0" in
  */*) SCRIPT_LOCATION=${0%/*} ;;
  *) SCRIPT_LOCATION=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_LOCATION" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
HELPER="$ROOT/scripts/ai/workflow_helper.py"
GATE="$SCRIPT_DIR/workflow-gate.sh"

invalid_start() {
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"RUN_START","result":"POLICY_VIOLATION","reason":"INVALID_RUN_START_ARGUMENTS","errors":[],"data":null}'
  exit 4
}

invalid_run() {
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"PRE_COMMAND","result":"POLICY_VIOLATION","reason":"INVALID_EXECUTE_COMMAND_ARGUMENTS","errors":[],"data":null}'
  exit 4
}

run_helper() {
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
      3\|Draft202012Validator\|FormatChecker) exec "$candidate" "$HELPER" "$@" ;;
    esac
  done
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"PRE_COMMAND","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'
  exit 3
}

if [ "$#" -eq 5 ] && [ "$1" = start ] && [ "$2" = --run-id ] && [ "$4" = --task-key ]; then
  exec "$GATE" RUN_START --run-id "$3" --task-key "$5"
fi
if [ "${1:-}" = start ]; then
  invalid_start
fi

if [ "$#" -eq 4 ] && [ "$1" = run ] && [ "$3" = --run-id ]; then
  run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4"
fi
if [ "$#" -eq 6 ] && [ "$1" = run ] && [ "$3" = --run-id ]; then
  case "$5" in
    --parameters-file) run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4" --parameters-file "$6" ;;
    --rerun-reason-file) run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4" --rerun-reason-file "$6" ;;
    --approval-ref) run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4" --approval-ref "$6" ;;
  esac
fi
if [ "$#" -eq 8 ] && [ "$1" = run ] && [ "$3" = --run-id ]; then
  if [ "$5" = --parameters-file ] && [ "$7" = --rerun-reason-file ]; then
    run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4" --parameters-file "$6" --rerun-reason-file "$8"
  fi
  if [ "$5" = --parameters-file ] && [ "$7" = --approval-ref ]; then
    run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4" --parameters-file "$6" --approval-ref "$8"
  fi
  if [ "$5" = --rerun-reason-file ] && [ "$7" = --approval-ref ]; then
    run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4" --rerun-reason-file "$6" --approval-ref "$8"
  fi
fi
if [ "$#" -eq 10 ] && [ "$1" = run ] && [ "$3" = --run-id ] \
  && [ "$5" = --parameters-file ] && [ "$7" = --rerun-reason-file ] && [ "$9" = --approval-ref ]; then
  run_helper execute-command --repository-root "$ROOT" --command-id "$2" --run-id "$4" \
    --parameters-file "$6" --rerun-reason-file "$8" --approval-ref "${10}"
fi
invalid_run
