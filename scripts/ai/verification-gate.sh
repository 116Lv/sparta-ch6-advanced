#!/bin/bash
set -eu

leaf_results_file=
if [ "$#" -eq 6 ] && [ "$1" = "--change-type" ] && [ "$3" = "--entry-point" ] && [ "$5" = "--output" ]; then
  change_type=$2
  entry_point=$4
  output=$6
elif [ "$#" -eq 8 ] && [ "$1" = "--change-type" ] && [ "$3" = "--entry-point" ] && [ "$5" = "--leaf-results-file" ] && [ "$7" = "--output" ]; then
  change_type=$2
  entry_point=$4
  leaf_results_file=$6
  output=$8
else
  printf '%s\n' '{"$schema":"ai/schemas/verification-gate-result.schema.json","$id":"ai/verification-gate-result.json","schemaVersion":1,"operation":"VERIFICATION_GATE","result":"POLICY_VIOLATION","reason":"INVALID_VERIFICATION_GATE_ARGUMENTS","errors":[{"code":"INVALID_VERIFICATION_GATE_ARGUMENTS","instancePath":"","schemaPath":"","message":"verification-gate accepts only --change-type, --entry-point, optional --leaf-results-file, and --output"}],"data":null}'
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
      if [ -n "$leaf_results_file" ]; then
        exec "$candidate" scripts/ai/workflow_helper.py verification-gate --repository-root "$ROOT" --change-type "$change_type" --entry-point "$entry_point" --leaf-results-file "$leaf_results_file" --output "$output"
      fi
      exec "$candidate" scripts/ai/workflow_helper.py verification-gate --repository-root "$ROOT" --change-type "$change_type" --entry-point "$entry_point" --output "$output"
      ;;
  esac
done
printf '%s\n' '{"$schema":"ai/schemas/verification-gate-result.schema.json","$id":"ai/verification-gate-result.json","schemaVersion":1,"operation":"VERIFICATION_GATE","result":"NOT_CONFIGURED","reason":"HELPER_RUNTIME_UNAVAILABLE","errors":[{"code":"HELPER_RUNTIME_UNAVAILABLE","instancePath":"","schemaPath":"","message":"Python 3 jsonschema helper runtime is unavailable"}],"data":null}'
exit 3
