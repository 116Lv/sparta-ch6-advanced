#!/bin/bash
set -eu

if [ "$#" -ne 2 ] || [ "$1" != "--output" ]; then
  printf '%s\n' '{"$schema":"ai/schemas/repo-intake-result.schema.json","$id":"ai/repo-intake-result.json","schemaVersion":1,"operation":"REPO_INTAKE","result":"POLICY_VIOLATION","reason":"INVALID_REPO_INTAKE_ARGUMENTS","errors":[{"code":"INVALID_REPO_INTAKE_ARGUMENTS","instancePath":"","schemaPath":"","message":"repo-intake accepts only --output"}],"data":null}'
  exit 4
fi

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
    3\|Draft202012Validator\|FormatChecker) exec "$candidate" scripts/ai/workflow_helper.py repo-intake --repository-root "$ROOT" --output "$2" ;;
  esac
done
printf '%s\n' '{"$schema":"ai/schemas/repo-intake-result.schema.json","$id":"ai/repo-intake-result.json","schemaVersion":1,"operation":"REPO_INTAKE","result":"NOT_CONFIGURED","reason":"HELPER_RUNTIME_UNAVAILABLE","errors":[{"code":"HELPER_RUNTIME_UNAVAILABLE","instancePath":"","schemaPath":"","message":"Python 3 jsonschema helper runtime is unavailable"}],"data":null}'
exit 3
