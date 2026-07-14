#!/bin/bash
set -eu

case "$0" in
  */*) SCRIPT_LOCATION=${0%/*} ;;
  *) SCRIPT_LOCATION=. ;;
esac
SCRIPT_DIR=$(CDPATH= cd -- "$SCRIPT_LOCATION" && pwd)
ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../.." && pwd)
HELPER="$ROOT/scripts/ai/workflow_helper.py"

invalid_prepare() {
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"PRE_DONE_CLAIM","result":"POLICY_VIOLATION","reason":"INVALID_DONE_CLAIM_ARGUMENTS","errors":[],"data":null}'
  exit 4
}

invalid_recovery() {
  printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"FINALIZATION_RECOVERY","result":"POLICY_VIOLATION","reason":"INVALID_FINALIZATION_RECOVERY_ARGUMENTS","errors":[],"data":null}'
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
  if [ "${FINALIZATION_RECOVERY:-0}" = 1 ]; then
    printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"FINALIZATION_RECOVERY","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'
  else
    printf '%s\n' '{"$schema":"ai/schemas/gateway-result.schema.json","$id":"ai/gateway-result.json","schemaVersion":1,"operation":"PRE_DONE_CLAIM","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'
  fi
  exit 3
}

if [ "$#" -eq 4 ] && [ "$1" = prepare ] && [ "$3" = --claim ]; then
  run_helper done-claim-prepare --repository-root "$ROOT" --run-id "$2" --claim "$4"
fi

if [ "$#" -eq 2 ] && [ "$1" = verify-finalized ]; then
  run_helper verify-finalized --repository-root "$ROOT" --run-id "$2"
fi

if [ "$#" -eq 2 ] && [ "$1" = recover-finalization ]; then
  FINALIZATION_RECOVERY=1 run_helper finalization-recover --repository-root "$ROOT" --run-id "$2"
fi

if [ "$#" -gt 0 ] && [ "$1" = recover-finalization ]; then
  invalid_recovery
fi

invalid_prepare
