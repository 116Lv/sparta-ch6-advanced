#!/bin/bash
set -eu

runtime_snapshot=
bypass_attempts=
runtime_snapshot_supplied=false
bypass_attempts_supplied=false
if [ "$#" -eq 6 ] && [ "$1" = "--task-key" ] && [ "$3" = "--gate-invocation-id" ] && [ "$5" = "--output" ]; then
  task_key=$2
  gate_invocation_id=$4
  output=$6
elif [ "$#" -eq 8 ] && [ "$1" = "--task-key" ] && [ "$3" = "--gate-invocation-id" ] && [ "$5" = "--runtime-snapshot" ] && [ "$7" = "--output" ]; then
  task_key=$2
  gate_invocation_id=$4
  runtime_snapshot=$6
  runtime_snapshot_supplied=true
  output=$8
elif [ "$#" -eq 8 ] && [ "$1" = "--task-key" ] && [ "$3" = "--gate-invocation-id" ] && [ "$5" = "--bypass-attempts" ] && [ "$7" = "--output" ]; then
  task_key=$2
  gate_invocation_id=$4
  bypass_attempts=$6
  bypass_attempts_supplied=true
  output=$8
elif [ "$#" -eq 10 ] && [ "$1" = "--task-key" ] && [ "$3" = "--gate-invocation-id" ] && [ "$5" = "--runtime-snapshot" ] && [ "$7" = "--bypass-attempts" ] && [ "$9" = "--output" ]; then
  task_key=$2
  gate_invocation_id=$4
  runtime_snapshot=$6
  bypass_attempts=$8
  runtime_snapshot_supplied=true
  bypass_attempts_supplied=true
  output=${10}
else
  printf '%s\n' '{"$schema":"ai/schemas/native-adapter-result.schema.json","$id":"ai/native-adapter-result.json","schemaVersion":1,"operation":"NATIVE_ADAPTER_GATE","result":"BLOCKED","phase2cLeafResult":"BLOCKED","reason":"INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS","data":{"hostId":"unknown-host","hostVersion":"0.0.0","surfaces":[{"surface":"COMMAND","status":"NOT_CONFIGURED","reasonCode":"INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS"},{"surface":"FILE_READ","status":"NOT_CONFIGURED","reasonCode":"INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS"},{"surface":"SEARCH","status":"NOT_CONFIGURED","reasonCode":"INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS"},{"surface":"TOOL_CALL","status":"NOT_CONFIGURED","reasonCode":"INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS"}],"bypassAttemptRefs":[],"repositoryOnlyQualification":true,"phase2CLeafResult":"BLOCKED"}}'
  exit 2
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
      command=("$candidate" scripts/ai/workflow_helper.py native-adapter-gate --repository-root "$ROOT" --task-key "$task_key" --gate-invocation-id "$gate_invocation_id")
      if [ "$runtime_snapshot_supplied" = true ]; then
        command+=(--runtime-snapshot "$runtime_snapshot")
      fi
      if [ "$bypass_attempts_supplied" = true ]; then
        command+=(--bypass-attempts "$bypass_attempts")
      fi
      command+=(--output "$output")
      exec "${command[@]}"
      ;;
  esac
done
printf '%s\n' '{"$schema":"ai/schemas/native-adapter-result.schema.json","$id":"ai/native-adapter-result.json","schemaVersion":1,"operation":"NATIVE_ADAPTER_GATE","result":"NOT_CONFIGURED","phase2cLeafResult":"NOT_CONFIGURED","reason":"HELPER_RUNTIME_UNAVAILABLE","data":{"hostId":"unknown-host","hostVersion":"0.0.0","surfaces":[{"surface":"COMMAND","status":"NOT_CONFIGURED","reasonCode":"HELPER_RUNTIME_UNAVAILABLE"},{"surface":"FILE_READ","status":"NOT_CONFIGURED","reasonCode":"HELPER_RUNTIME_UNAVAILABLE"},{"surface":"SEARCH","status":"NOT_CONFIGURED","reasonCode":"HELPER_RUNTIME_UNAVAILABLE"},{"surface":"TOOL_CALL","status":"NOT_CONFIGURED","reasonCode":"HELPER_RUNTIME_UNAVAILABLE"}],"bypassAttemptRefs":[],"repositoryOnlyQualification":true,"phase2CLeafResult":"NOT_CONFIGURED"}}'
exit 3
