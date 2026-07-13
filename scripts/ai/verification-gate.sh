#!/bin/bash
set -eu

change_type_set=0
entry_point_set=0
task_key_set=0
gate_invocation_id_set=0
leaf_results_file_set=0
runtime_snapshot_set=0
bypass_attempts_set=0
output_set=0

while [ "$#" -gt 0 ]; do
  [ "$#" -ge 2 ] || break
  case "$1" in
    --change-type)
      [ "$change_type_set" -eq 0 ] || break
      change_type=$2
      change_type_set=1
      ;;
    --entry-point)
      [ "$entry_point_set" -eq 0 ] || break
      entry_point=$2
      entry_point_set=1
      ;;
    --task-key)
      [ "$task_key_set" -eq 0 ] || break
      task_key=$2
      task_key_set=1
      ;;
    --gate-invocation-id)
      [ "$gate_invocation_id_set" -eq 0 ] || break
      gate_invocation_id=$2
      gate_invocation_id_set=1
      ;;
    --leaf-results-file)
      [ "$leaf_results_file_set" -eq 0 ] || break
      leaf_results_file=$2
      leaf_results_file_set=1
      ;;
    --runtime-snapshot)
      [ "$runtime_snapshot_set" -eq 0 ] || break
      runtime_snapshot=$2
      runtime_snapshot_set=1
      ;;
    --bypass-attempts)
      [ "$bypass_attempts_set" -eq 0 ] || break
      bypass_attempts=$2
      bypass_attempts_set=1
      ;;
    --output)
      [ "$output_set" -eq 0 ] || break
      output=$2
      output_set=1
      ;;
    *) break ;;
  esac
  shift 2
done

if [ "$#" -ne 0 ] || [ "$change_type_set" -ne 1 ] || [ "$entry_point_set" -ne 1 ] \
  || [ "$task_key_set" -ne 1 ] || [ "$gate_invocation_id_set" -ne 1 ] || [ "$output_set" -ne 1 ]; then
  printf '%s\n' '{"$schema":"ai/schemas/verification-gate-result.schema.json","$id":"ai/verification-gate-result.json","schemaVersion":1,"operation":"VERIFICATION_GATE","result":"POLICY_VIOLATION","reason":"INVALID_VERIFICATION_GATE_ARGUMENTS","errors":[{"code":"INVALID_VERIFICATION_GATE_ARGUMENTS","instancePath":"","schemaPath":"","message":"verification-gate requires --change-type, --entry-point, --task-key, --gate-invocation-id, and --output; only --leaf-results-file, --runtime-snapshot, and --bypass-attempts are optional"}],"data":null}'
  exit 4
fi

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
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
    3\|Draft202012Validator\|FormatChecker)
      set -- "$candidate" scripts/ai/workflow_helper.py verification-gate \
        --repository-root "$ROOT" --change-type "$change_type" --entry-point "$entry_point" \
        --task-key "$task_key" --gate-invocation-id "$gate_invocation_id"
      if [ "$leaf_results_file_set" -eq 1 ]; then
        set -- "$@" --leaf-results-file "$leaf_results_file"
      fi
      if [ "$runtime_snapshot_set" -eq 1 ]; then
        set -- "$@" --runtime-snapshot "$runtime_snapshot"
      fi
      if [ "$bypass_attempts_set" -eq 1 ]; then
        set -- "$@" --bypass-attempts "$bypass_attempts"
      fi
      set -- "$@" --output "$output"
      exec "$@"
      ;;
  esac
done
printf '%s\n' '{"$schema":"ai/schemas/verification-gate-result.schema.json","$id":"ai/verification-gate-result.json","schemaVersion":1,"operation":"VERIFICATION_GATE","result":"NOT_CONFIGURED","reason":"HELPER_RUNTIME_UNAVAILABLE","errors":[{"code":"HELPER_RUNTIME_UNAVAILABLE","instancePath":"","schemaPath":"","message":"Python 3 jsonschema helper runtime is unavailable"}],"data":null}'
exit 3
