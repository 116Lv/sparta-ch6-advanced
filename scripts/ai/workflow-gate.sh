#!/bin/bash
set -eu

case "$0" in
  */*) SCRIPT_LOCATION=${0%/*} ;;
  *) SCRIPT_LOCATION=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_LOCATION" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
HELPER="$ROOT/scripts/ai/workflow_helper.py"

invalid_run_start() {
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"RUN_START","result":"POLICY_VIOLATION","reason":"INVALID_RUN_START_ARGUMENTS","errors":[],"data":null}'
  exit 4
}

invalid_pre_command() {
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"PRE_COMMAND","result":"POLICY_VIOLATION","reason":"INVALID_PRE_COMMAND_ARGUMENTS","errors":[],"data":null}'
  exit 4
}

invalid_post_command() {
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"POST_COMMAND","result":"POLICY_VIOLATION","reason":"INVALID_POST_COMMAND_ARGUMENTS","errors":[],"data":null}'
  exit 4
}

run_helper() {
  operation=$1
  shift
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
      3\|Draft202012Validator\|FormatChecker) exec "$candidate" "$HELPER" "$operation" "$@" ;;
    esac
  done
  case "$operation" in
    run-start) gateway_operation=RUN_START ;;
    pre-command) gateway_operation=PRE_COMMAND ;;
    post-command) gateway_operation=POST_COMMAND ;;
  esac
  printf '%s\n' "{\"\$schema\":\"ai/schemas/gateway-result.schema.json\",\"\$id\":\"ai/gateway-result.json\",\"schemaVersion\":1,\"operation\":\"$gateway_operation\",\"result\":\"NOT_CONFIGURED\",\"reason\":\"helper runtime unavailable\",\"errors\":[],\"data\":null}"
  exit 3
}

if [ "$#" -eq 5 ] && [ "$1" = RUN_START ] && [ "$2" = --run-id ] && [ "$4" = --task-key ]; then
  run_helper run-start --repository-root "$ROOT" --run-id "$3" --task-key "$5"
fi
if [ "${1:-}" = RUN_START ]; then
  invalid_run_start
fi

if [ "$#" -eq 5 ] && [ "$1" = POST_COMMAND ] && [ "$2" = --run-id ] && [ "$4" = --attempt-id ]; then
  run_helper post-command --repository-root "$ROOT" --run-id "$3" --attempt-id "$5"
fi
if [ "${1:-}" = POST_COMMAND ]; then
  invalid_post_command
fi

if [ "$#" -eq 5 ] && [ "$1" = PRE_COMMAND ] && [ "$2" = --run-id ] && [ "$4" = --command-id ]; then
  run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5"
fi
if [ "$#" -eq 7 ] && [ "$1" = PRE_COMMAND ] && [ "$2" = --run-id ] && [ "$4" = --command-id ]; then
  case "$6" in
    --parameters-file) run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5" --parameters-file "$7" ;;
    --rerun-reason-file) run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5" --rerun-reason-file "$7" ;;
    --approval-ref) run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5" --approval-ref "$7" ;;
  esac
fi
if [ "$#" -eq 9 ] && [ "$1" = PRE_COMMAND ] && [ "$2" = --run-id ] && [ "$4" = --command-id ]; then
  if [ "$6" = --parameters-file ] && [ "$8" = --rerun-reason-file ]; then
    run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5" --parameters-file "$7" --rerun-reason-file "$9"
  fi
  if [ "$6" = --parameters-file ] && [ "$8" = --approval-ref ]; then
    run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5" --parameters-file "$7" --approval-ref "$9"
  fi
  if [ "$6" = --rerun-reason-file ] && [ "$8" = --approval-ref ]; then
    run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5" --rerun-reason-file "$7" --approval-ref "$9"
  fi
fi
if [ "$#" -eq 11 ] && [ "$1" = PRE_COMMAND ] && [ "$2" = --run-id ] && [ "$4" = --command-id ] \
  && [ "$6" = --parameters-file ] && [ "$8" = --rerun-reason-file ] && [ "${10}" = --approval-ref ]; then
  run_helper pre-command --repository-root "$ROOT" --run-id "$3" --command-id "$5" \
    --parameters-file "$7" --rerun-reason-file "$9" --approval-ref "${11}"
fi
if [ "${1:-}" = PRE_COMMAND ]; then
  invalid_pre_command
fi
invalid_run_start
