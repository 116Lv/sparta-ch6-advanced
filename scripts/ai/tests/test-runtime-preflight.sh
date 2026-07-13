#!/usr/bin/env bash
set -eu
PATH=/usr/bin:/bin:$PATH

SOURCE_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
SOURCE_STATE="$SOURCE_ROOT/ai/project-state.json"
SOURCE_SUMMARY="$SOURCE_ROOT/ai/project-state.md"
SOURCE_EVIDENCE="$SOURCE_ROOT/ai/evidence/local-helper-runtime.json"
SOURCE_TXN_DIR="$SOURCE_ROOT/ai/.workflow-state-txn"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/runtime-preflight.XXXXXX")
ROOT="$TMP/repository"
PREFLIGHT="$ROOT/scripts/ai/runtime-preflight.sh"
HELPER_TESTS="$ROOT/scripts/ai/run-helper-tests.sh"
STATE="$ROOT/ai/project-state.json"
SUMMARY="$ROOT/ai/project-state.md"
EVIDENCE="$ROOT/ai/evidence/local-helper-runtime.json"
TXN_DIR="$ROOT/ai/.workflow-state-txn"
REAL_PYTHON=
for candidate in python3 python; do
  candidate_path=$(command -v "$candidate" 2>/dev/null || true)
  if [ -n "$candidate_path" ] && "$candidate_path" -c 'import sys; raise SystemExit(0 if sys.version_info.major == 3 else 1)' >/dev/null 2>&1; then
    REAL_PYTHON=$candidate_path
    break
  fi
done

cleanup() {
  status=$?
  set +e
  if [ -n "${writer_pid:-}" ]; then
    : > "${writer_release:-$TMP/release-writer}"
    wait "$writer_pid"
  fi
  source_canonical_after=$(canonical_fingerprint "$SOURCE_STATE" "$SOURCE_SUMMARY" "$SOURCE_EVIDENCE")
  source_txn_after=$(path_fingerprint "$SOURCE_TXN_DIR")
  rm -rf "$TMP"
  if [ "$source_canonical_after" != "$SOURCE_CANONICAL_BEFORE" ]; then
    printf 'FAIL: source canonical files changed during isolated contract test\n' >&2
    status=1
  fi
  if [ "$source_txn_after" != "$SOURCE_TXN_BEFORE" ]; then
    printf 'FAIL: pre-existing source transaction state changed during isolated contract test\n' >&2
    status=1
  fi
  trap - EXIT HUP INT TERM
  exit "$status"
}

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_contains() {
  case "$1" in
    *"$2"*) ;;
    *) fail "expected output to contain $2" ;;
  esac
}

assert_equal() {
  [ "$1" = "$2" ] || fail "${TEST_CASE:-unlabeled}: expected [$2], got [$1]"
}

require_file() {
  [ -f "$1" ] || fail "required file is missing: $1"
}

path_fingerprint() {
  path=$1
  if [ ! -e "$path" ]; then
    printf 'MISSING\n'
    return
  fi
  if [ -f "$path" ]; then
    printf 'FILE '
    sha256sum "$path"
    return
  fi
  printf 'DIRECTORY\n'
  find "$path" -type d -print | LC_ALL=C sort
  find "$path" -type f -print | LC_ALL=C sort | while IFS= read -r file; do
    sha256sum "$file"
  done
}

canonical_fingerprint() {
  for path in "$@"; do
    printf '%s\n' "$path"
    path_fingerprint "$path"
  done
}

make_fake_python() {
  directory=$1
  name=$2
  mkdir -p "$directory"
  cat > "$directory/$name" <<'FAKE'
#!/bin/sh
set -eu
printf '%s\n' "$PWD|$0:$#:$*" >> "$FAKE_CALL_LOG"
if [ "${1:-}" = "-c" ]; then
  printf '%s\n' "$FAKE_PROBE_RESULT"
  exit "${FAKE_PROBE_EXIT:-0}"
fi
if [ "${FAKE_EXEC_ONLY:-0}" = "1" ]; then
  exit "${FAKE_EXEC_EXIT:-0}"
fi
exec "$REAL_PYTHON" "$@"
FAKE
  chmod +x "$directory/$name"
}

run_preflight() {
  output_file=$1
  shift
  set +e
  "$@" > "$output_file" 2>&1
  status=$?
  set -e
  printf '%s' "$status"
}

[ -n "$REAL_PYTHON" ] || fail "no host Python is available to exercise harmless fake candidates"
SOURCE_CANONICAL_BEFORE=$(canonical_fingerprint "$SOURCE_STATE" "$SOURCE_SUMMARY" "$SOURCE_EVIDENCE")
SOURCE_TXN_BEFORE=$(path_fingerprint "$SOURCE_TXN_DIR")
trap cleanup EXIT HUP INT TERM

mkdir -p "$ROOT/scripts/ai/tests" "$ROOT/ai/evidence"
cp "$SOURCE_ROOT/scripts/ai/runtime-preflight.sh" "$PREFLIGHT"
cp "$SOURCE_ROOT/scripts/ai/run-helper-tests.sh" "$HELPER_TESTS"
cp "$SOURCE_ROOT/scripts/ai/workflow_helper.py" "$ROOT/scripts/ai/workflow_helper.py"
cp -R "$SOURCE_ROOT/ai/schemas" "$ROOT/ai/schemas"
cp "$SOURCE_STATE" "$STATE"
cp "$SOURCE_SUMMARY" "$SUMMARY"
if [ -f "$SOURCE_EVIDENCE" ]; then
  cp "$SOURCE_EVIDENCE" "$EVIDENCE"
fi
chmod +x "$PREFLIGHT" "$HELPER_TESTS"

require_file "$PREFLIGHT"
require_file "$HELPER_TESTS"

TEST_CASE=result-publication-fallbacks
set +e
"$REAL_PYTHON" - "$ROOT" <<'PY'
import importlib.util
import json
import os
from pathlib import Path
from types import SimpleNamespace
import sys

root = Path(sys.argv[1])

def load_helper():
    spec = importlib.util.spec_from_file_location("publication_workflow_helper", root / "scripts" / "ai" / "workflow_helper.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def malformed_outcome(module, reason):
    original = module.gateway_result
    def result(result, actual_reason, data=None):
        if actual_reason == reason:
            return {"result": result, "reason": actual_reason}
        return original(result, actual_reason, data)
    module.gateway_result = result

def arguments(record=False):
    return SimpleNamespace(
        repository_root=str(root),
        runtime_command="python3",
        invalid_arguments=False,
        record=record,
    )

def assert_fallback(name, result, status):
    if status != 5 or result.get("result") != "INVALID_STATE" or result.get("reason") != "GATEWAY_RESULT_SCHEMA_INVALID":
        raise SystemExit(f"{name}: expected validated fallback INVALID_STATE/5, got {result!r}/{status}")

module = load_helper()
malformed_outcome(module, "JSONSCHEMA_METADATA_UNAVAILABLE")
module.package_version = lambda _name: (_ for _ in ()).throw(RuntimeError("metadata unavailable"))
assert_fallback("metadata", *module.run_preflight(arguments()))

module = load_helper()
malformed_outcome(module, "INVALID_INTERPRETER")
original_executable = module.sys.executable
module.sys.executable = str(root / "missing-python")
try:
    assert_fallback("interpreter", *module.run_preflight(arguments()))
finally:
    module.sys.executable = original_executable

transaction = root / "ai" / ".workflow-state-txn"
transaction.mkdir()
(transaction / "journal.json").write_text("{}\n", encoding="utf-8")
module = load_helper()
malformed_outcome(module, "INVALID_TRANSACTION_STATE")
assert_fallback("transaction", *module.run_preflight(arguments()))
import shutil
shutil.rmtree(transaction)

module = load_helper()
malformed_outcome(module, "STATE_RECORDING_FAILED")
os.environ["AI_WORKFLOW_TEST_FAIL_AFTER_STAGE"] = "1"
try:
    assert_fallback("recording", *module.run_preflight(arguments(record=True)))
finally:
    os.environ.pop("AI_WORKFLOW_TEST_FAIL_AFTER_STAGE", None)

schema_path = root / "ai" / "schemas" / "gateway-result.schema.json"
original_schema = schema_path.read_text(encoding="utf-8")
schema_path.write_text("{not-json}\n", encoding="utf-8")
try:
    module = load_helper()
    module.package_version = lambda _name: (_ for _ in ()).throw(RuntimeError("metadata unavailable"))
    assert_fallback("malformed-schema", *module.run_preflight(arguments()))
finally:
    schema_path.write_text(original_schema, encoding="utf-8")
PY
publication_status=$?
set -e
assert_equal "$publication_status" "0"

TEST_CASE=transaction-durability-barriers
set +e
"$REAL_PYTHON" - "$ROOT" <<'PY'
import errno
import importlib.util
import json
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("durability_workflow_helper", root / "scripts" / "ai" / "workflow_helper.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

barrier_root = root.parent / "barrier-repository"
shutil.copytree(root / "ai", barrier_root / "ai")
events = []
original_atomic_write = module.atomic_write
original_copy_backup = module.copy_backup
original_fsync_directory = module.fsync_directory
original_remove_transaction = module.remove_transaction
original_mkdir = module.Path.mkdir

def atomic_write(path, content):
    events.append(f"atomic:start:{path.name}")
    original_atomic_write(path, content)
    events.append(f"atomic:end:{path.name}")

def copy_backup(source, destination):
    events.append(f"backup:start:{destination.name}")
    original_copy_backup(source, destination)
    events.append(f"backup:end:{destination.name}")

def fsync_directory(path):
    events.append(f"directory:{path.name}")
    original_fsync_directory(path)

def remove_transaction(path):
    events.append("remove:start")
    original_remove_transaction(path)
    events.append("remove:end")

def mkdir(path, *args, **kwargs):
    original_mkdir(path, *args, **kwargs)
    if path.name == ".workflow-state-txn":
        events.append("transaction:mkdir")

module.atomic_write = atomic_write
module.copy_backup = copy_backup
module.fsync_directory = fsync_directory
module.remove_transaction = remove_transaction
module.Path.mkdir = mkdir
module.record(barrier_root, {
    "environment": "LOCAL",
    "targetRuntime": "Python 3",
    "detectedRuntime": "Python 3",
    "runtimeCommand": "python3",
    "version": "barrier-test",
    "jsonschemaVersion": "barrier-test",
    "validator": "Draft202012Validator",
    "formatChecker": True,
    "interpreterSha256": "1" * 64,
    "observedAt": "2026-01-01T00:00:00Z",
})

transaction_mkdir = events.index("transaction:mkdir")
owner_start = events.index("atomic:start:owner.json")
parent_sync = next(index for index, event in enumerate(events[transaction_mkdir + 1:], transaction_mkdir + 1) if event == "directory:ai")
if not transaction_mkdir < parent_sync < owner_start:
    raise SystemExit(f"transaction creation was not durably ordered: {events!r}")

last_backup = max(index for index, event in enumerate(events) if event.startswith("backup:end:"))
journal_start = events.index("atomic:start:journal.json")
journal_directory = next(index for index, event in enumerate(events[last_backup + 1:], last_backup + 1) if event == "directory:.workflow-state-txn")
if not last_backup < journal_directory < journal_start:
    raise SystemExit(f"backup/journal barrier order is wrong: {events!r}")
if not events.index("atomic:end:journal.json") < events.index("atomic:start:local-helper-runtime.json"):
    raise SystemExit(f"journal publication did not precede target replacement: {events!r}")
remove_start = events.index("remove:start")
remove_directory = next(index for index, event in enumerate(events[remove_start + 1:], remove_start + 1) if event == "directory:ai")
if not events.index("atomic:end:project-state.md") < remove_start < remove_directory < events.index("remove:end"):
    raise SystemExit(f"transaction removal was not durably ordered: {events!r}")

original_open = module.os.open
try:
    module.os.open = lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError(errno.EINVAL, "directory fsync unsupported"))
    module.fsync_directory(barrier_root / "ai")
    module.os.open = lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError(errno.EIO, "unexpected directory failure"))
    try:
        module.fsync_directory(barrier_root / "ai")
    except OSError as error:
        if error.errno != errno.EIO:
            raise
    else:
        raise SystemExit("directory fsync swallowed an unsupported error")
finally:
    module.os.open = original_open
    shutil.rmtree(barrier_root)
PY
durability_status=$?
set -e
assert_equal "$durability_status" "0"

assert_schema_valid() {
  "$REAL_PYTHON" - "$ROOT/ai/schemas/gateway-result.schema.json" "$1" <<'PY'
import json
import sys

from jsonschema import Draft202012Validator, FormatChecker

with open(sys.argv[1], encoding="utf-8") as handle:
    schema = json.load(handle)
with open(sys.argv[2], encoding="utf-8") as handle:
    instance = json.load(handle)
Draft202012Validator.check_schema(schema)
errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))
raise SystemExit(1 if errors else 0)
PY
}

assert_document_valid() {
  schema=$1
  instance=$2
  "$REAL_PYTHON" - "$schema" "$instance" <<'PY'
import json
import sys

from jsonschema import Draft202012Validator, FormatChecker

with open(sys.argv[1], encoding="utf-8") as handle:
    schema = json.load(handle)
with open(sys.argv[2], encoding="utf-8") as handle:
    instance = json.load(handle)
Draft202012Validator.check_schema(schema)
errors = sorted(
    Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance),
    key=lambda error: (list(error.path), list(error.schema_path)),
)
if errors:
    for error in errors:
        print(error.message, file=sys.stderr)
    raise SystemExit(1)
PY
}

assert_gateway_envelope() {
  "$REAL_PYTHON" - "$1" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    instance = json.load(handle)
expected = {"$schema", "$id", "schemaVersion", "operation", "result", "reason", "errors", "data"}
if set(instance) != expected:
    raise SystemExit(f"gateway fields differ: {sorted(instance)}")
if instance["$schema"] != "ai/schemas/gateway-result.schema.json":
    raise SystemExit("gateway $schema is not canonical")
if instance["$id"] != "ai/gateway-result.json":
    raise SystemExit("gateway $id is not canonical")
if instance["schemaVersion"] != 1:
    raise SystemExit("gateway schemaVersion is not 1")
PY
}

write_valid_transaction() {
  age=$1
  rm -rf "$TXN_DIR"
  "$REAL_PYTHON" - "$ROOT" "$age" <<'PY'
import datetime as dt
import hashlib
import json
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
age = sys.argv[2]
transaction = root / "ai" / ".workflow-state-txn"
transaction.mkdir(parents=True)
owner = {
    "pid": 99999999,
    "createdAt": (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        if age == "recent"
        else "2000-01-01T00:00:00Z"
    ),
}
targets = [
    (root / "ai" / "evidence" / "local-helper-runtime.json", "local-helper-runtime.json.backup"),
    (root / "ai" / "project-state.json", "project-state.json.backup"),
    (root / "ai" / "project-state.md", "project-state.md.backup"),
]
files = []
for target, backup_name in targets:
    backup = transaction / backup_name
    existed = target.is_file()
    previous = hashlib.sha256(target.read_bytes()).hexdigest() if existed else None
    if existed:
        shutil.copyfile(target, backup)
    files.append({
        "target": target.relative_to(root).as_posix(),
        "backup": backup_name,
        "existed": existed,
        "previousSha256": previous,
        "intendedSha256": previous or ("0" * 64),
    })
journal = {
    "version": 1,
    "stage": "PREPARED",
    "owner": owner,
    "files": files,
}
(transaction / "owner.json").write_text(json.dumps(owner, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
(transaction / "journal.json").write_text(json.dumps(journal, separators=(",", ":"), sort_keys=True) + "\n", encoding="utf-8")
PY
}

EMPTY_PATH="$TMP/empty"
mkdir -p "$EMPTY_PATH"
out="$TMP/no-runtime.json"
TEST_CASE=no-runtime
status=$(run_preflight "$out" env PATH="$EMPTY_PATH" "$PREFLIGHT")
assert_equal "$status" "3"
bootstrap=$(cat "$out")
assert_equal "$bootstrap" '{"operation":"PREFLIGHT","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'
case "$bootstrap" in
  *"$TMP"*|*"PATH"*|*"python3"*) fail "bootstrap failure leaked caller-controlled text" ;;
esac

out="$TMP/invalid-arguments.json"
TEST_CASE=invalid-arguments
caller_cwd=$PWD
cd "$ROOT"
status=$(run_preflight "$out" scripts/ai/runtime-preflight.sh unexpected)
cd "$caller_cwd"
assert_equal "$status" "5"
assert_contains "$(cat "$out")" '"result":"INVALID_STATE"'
assert_gateway_envelope "$out" || fail "shell INVALID_STATE is not the complete gateway envelope"
assert_schema_valid "$out" || fail "shell INVALID_STATE does not validate against gateway-result.schema.json"

fake_dir="$TMP/fake runtime"
call_log="$TMP/calls.log"
: > "$call_log"
make_fake_python "$fake_dir" python3
make_fake_python "$fake_dir" python

out="$TMP/pass.json"
TEST_CASE=python3-precedence
status=$(run_preflight "$out" env \
  PATH="$fake_dir" \
  REAL_PYTHON="$REAL_PYTHON" \
  FAKE_CALL_LOG="$call_log" \
  FAKE_PROBE_RESULT='3|Draft202012Validator|FormatChecker' \
  "$PREFLIGHT")
if [ "$status" != "0" ]; then
  cat "$out" >&2
  cat "$call_log" >&2
  env PATH="$fake_dir" REAL_PYTHON="$REAL_PYTHON" FAKE_CALL_LOG="$call_log" FAKE_PROBE_RESULT='3|Draft202012Validator|FormatChecker' /bin/bash -x "$PREFLIGHT" >&2 || true
fi
assert_equal "$status" "0"
pass=$(cat "$out")
assert_contains "$pass" '"operation":"PREFLIGHT"'
assert_contains "$pass" '"result":"PASS"'
assert_contains "$pass" '"reason":null'
assert_contains "$pass" '"errors":[]'
assert_contains "$pass" '"data":{'
assert_contains "$pass" '"runtimeCommand":"python3"'
assert_contains "$pass" '"runtimeExecutableHash"'
assert_contains "$pass" '"pythonVersion"'
assert_contains "$pass" '"validator":"Draft202012Validator"'
assert_contains "$pass" '"formatChecker":true'
assert_gateway_envelope "$out" || fail "PREFLIGHT PASS omitted required gateway metadata"
assert_schema_valid "$out" || fail "PREFLIGHT PASS does not validate against gateway-result.schema.json"
assert_contains "$(cat "$call_log")" 'workflow_helper.py preflight --repository-root'
assert_contains "$(cat "$call_log")" 'python3'
case "$(cat "$call_log")" in
  *" python "*) fail "python ran even though python3 had precedence" ;;
esac

out="$TMP/relative-pass.json"
TEST_CASE=relative-invocation
caller_cwd=$PWD
cd "$ROOT"
status=$(run_preflight "$out" env \
  PATH="$fake_dir" \
  REAL_PYTHON="$REAL_PYTHON" \
  FAKE_CALL_LOG="$call_log" \
  FAKE_PROBE_RESULT='3|Draft202012Validator|FormatChecker' \
  scripts/ai/runtime-preflight.sh)
cd "$caller_cwd"
assert_equal "$status" "0"
assert_gateway_envelope "$out" || fail "relative invocation did not resolve the fixture repository"

out="$TMP/python2.json"
TEST_CASE=python2-rejection
status=$(run_preflight "$out" env \
  PATH="$fake_dir" \
  REAL_PYTHON="$REAL_PYTHON" \
  FAKE_CALL_LOG="$call_log" \
  FAKE_PROBE_RESULT='2|Draft202012Validator|FormatChecker' \
  "$PREFLIGHT")
assert_equal "$status" "3"
assert_equal "$(cat "$out")" '{"operation":"PREFLIGHT","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'

out="$TMP/missing-validator.json"
TEST_CASE=missing-validator-rejection
status=$(run_preflight "$out" env \
  PATH="$fake_dir" \
  REAL_PYTHON="$REAL_PYTHON" \
  FAKE_CALL_LOG="$call_log" \
  FAKE_PROBE_RESULT='3|missing|missing' \
  "$PREFLIGHT")
assert_equal "$status" "3"
assert_equal "$(cat "$out")" '{"operation":"PREFLIGHT","result":"NOT_CONFIGURED","reason":"helper runtime unavailable","errors":[],"data":null}'

py_dir="$TMP/py-only"
make_fake_python "$py_dir" python
out="$TMP/python-fallback.json"
TEST_CASE=python-fallback
status=$(run_preflight "$out" env \
  PATH="$py_dir" \
  REAL_PYTHON="$REAL_PYTHON" \
  FAKE_CALL_LOG="$call_log" \
  FAKE_PROBE_RESULT='3|Draft202012Validator|FormatChecker' \
  PYTHON="$TMP/ignored-python" \
  "$PREFLIGHT")
assert_equal "$status" "0"
assert_contains "$(cat "$call_log")" 'workflow_helper.py preflight --repository-root'

before_state=$(sha256sum "$STATE")
before_summary=$(sha256sum "$SUMMARY" 2>/dev/null || true)
before_evidence=$(sha256sum "$EVIDENCE" 2>/dev/null || true)
out="$TMP/record.json"
TEST_CASE=record
status=$(run_preflight "$out" env AI_WORKFLOW_TEST_DIAGNOSTIC=1 "$PREFLIGHT" --record)
if [ "$status" != "0" ]; then
  cat "$out" >&2
fi
assert_equal "$status" "0"
require_file "$EVIDENCE"
assert_contains "$(cat "$EVIDENCE")" '"environment":"LOCAL"'
assert_contains "$(cat "$EVIDENCE")" '"runtimeCommand"'
assert_contains "$(cat "$EVIDENCE")" '"interpreterSha256"'
case "$(cat "$EVIDENCE")" in
  *"$REAL_PYTHON"*) fail "runtime evidence contains interpreter path" ;;
esac
assert_contains "$(cat "$STATE")" '"configurationStatus": "VERIFIED"'
assert_contains "$(cat "$SUMMARY")" 'LOCAL helper runtime'
assert_document_valid "$ROOT/ai/schemas/helper-runtime-evidence.schema.json" "$EVIDENCE" || fail "helper evidence is not independently schema-valid"
assert_document_valid "$ROOT/ai/schemas/project-state.schema.json" "$STATE" || fail "project state is not independently schema-valid"
"$REAL_PYTHON" - "$STATE" "$SUMMARY" <<'PY' || fail "generated project-state summary differs from canonical runtime state"
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    state = json.load(handle)
with open(sys.argv[2], encoding="utf-8") as handle:
    summary = handle.read()
start = "<!-- GENERATED:START source=ai/project-state.json -->"
end = "<!-- GENERATED:END source=ai/project-state.json -->"
actual = summary[summary.index(start) + len(start):summary.index(end)]
required_sections = (
    "### Project Summary",
    "### Important Paths",
    "### Known Ports",
    "### Environment State",
    "### Helper Runtime State",
    "### Command Registry Reference",
    "### Cache Invalidation Inputs",
)
if any(actual.count(section) != 1 for section in required_sections):
    raise SystemExit(1)
if f"Canonical source: `ai/project-state.json`" not in actual:
    raise SystemExit(1)
if f"Schema version: `{state['schemaVersion']}`" not in actual:
    raise SystemExit(1)
if f"Updated at: `{state['updatedAt']}`" not in actual:
    raise SystemExit(1)
if "8080 (INFERRED)" not in actual:
    raise SystemExit(1)
for path in state["importantPaths"]:
    if f"| {path['purpose']} | {path['path']} |" not in actual:
        raise SystemExit(1)
for environment in state["environments"]:
    if f"| {environment['kind']} | {environment['configurationStatus']} |" not in actual:
        raise SystemExit(1)
for runtime in state["helperRuntimes"]:
    detected = runtime["detectedRuntime"] or "N/A"
    version = runtime["version"] or "N/A"
    row = f"| {runtime['environment']} | {runtime['targetRuntime']} | {detected} | {runtime['configurationStatus']} | {version} |"
    if row not in actual:
        raise SystemExit(1)
if f"- `{state['commandRegistryRef']}`" not in actual:
    raise SystemExit(1)
for path in state["cacheInvalidationInputs"]:
    if f"- `{path}`" not in actual:
        raise SystemExit(1)
PY

out="$TMP/metadata-failure.json"
TEST_CASE=metadata-failure
set +e
"$REAL_PYTHON" - "$ROOT" > "$out" 2>&1 <<'PY'
import importlib.util
from pathlib import Path
from types import SimpleNamespace
import sys

root = Path(sys.argv[1])
spec = importlib.util.spec_from_file_location("fixture_workflow_helper", root / "scripts" / "ai" / "workflow_helper.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

def unavailable(_name):
    raise RuntimeError("metadata unavailable")

module.package_version = unavailable
result, status = module.run_preflight(SimpleNamespace(
    repository_root=str(root),
    runtime_command="python",
    record=False,
))
print(module.compact(result))
raise SystemExit(status)
PY
metadata_status=$?
set -e
assert_equal "$metadata_status" "3"
assert_contains "$(cat "$out")" '"result":"NOT_CONFIGURED"'
assert_contains "$(cat "$out")" '"reason":"JSONSCHEMA_METADATA_UNAVAILABLE"'
assert_gateway_envelope "$out" || fail "metadata lookup failure escaped the structured gateway envelope"
assert_schema_valid "$out" || fail "metadata lookup failure result is not schema-valid"

after_state=$(sha256sum "$STATE")
after_summary=$(sha256sum "$SUMMARY")
after_evidence=$(sha256sum "$EVIDENCE")
TEST_CASE=idempotence
status=$(run_preflight "$out" env AI_WORKFLOW_TEST_DIAGNOSTIC=1 "$PREFLIGHT" --record)
if [ "$status" != "0" ]; then
  cat "$out" >&2
fi
assert_equal "$status" "0"
assert_equal "$(sha256sum "$STATE")" "$after_state"
assert_equal "$(sha256sum "$SUMMARY")" "$after_summary"
assert_equal "$(sha256sum "$EVIDENCE")" "$after_evidence"
expected_interpreter_hash=$("$REAL_PYTHON" - "$EVIDENCE" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    print(json.load(handle)["interpreterSha256"])
PY
)

"$REAL_PYTHON" - "$EVIDENCE" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    evidence = json.load(handle)
evidence["interpreterSha256"] = "0" * 64
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(evidence, handle, separators=(",", ":"), sort_keys=True)
    handle.write("\n")
PY
changed_evidence=$(sha256sum "$EVIDENCE")
out="$TMP/hash-refresh.json"
TEST_CASE=interpreter-hash-refresh
status=$(run_preflight "$out" env AI_WORKFLOW_TEST_DIAGNOSTIC=1 "$PREFLIGHT" --record)
if [ "$status" != "0" ]; then
  cat "$out" >&2
fi
assert_equal "$status" "0"
assert_contains "$(cat "$EVIDENCE")" "\"interpreterSha256\":\"$expected_interpreter_hash\""
case "$(sha256sum "$EVIDENCE")" in
  "$changed_evidence") fail "interpreter hash mismatch did not refresh durable evidence" ;;
esac
after_state=$(sha256sum "$STATE")
after_summary=$(sha256sum "$SUMMARY")
after_evidence=$(sha256sum "$EVIDENCE")

"$REAL_PYTHON" - "$STATE" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    state = json.load(handle)
runtime = next(item for item in state["helperRuntimes"] if item["environment"] == "LOCAL")
runtime.update({"detectedRuntime": None, "configurationStatus": "UNKNOWN", "version": None, "evidence": []})
environment = next(item for item in state["environments"] if item["kind"] == "LOCAL")
environment.update({"configurationStatus": "UNKNOWN", "notes": ["stale test state"]})
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(state, handle, indent=2)
    handle.write("\n")
PY
out="$TMP/canonical-repair.json"
TEST_CASE=canonical-mismatch-repair
status=$(run_preflight "$out" "$PREFLIGHT" --record)
assert_equal "$status" "0"
assert_equal "$(sha256sum "$STATE")" "$after_state"
assert_equal "$(sha256sum "$SUMMARY")" "$after_summary"
assert_equal "$(sha256sum "$EVIDENCE")" "$after_evidence"

write_valid_transaction recent
recent_txn=$(path_fingerprint "$TXN_DIR")
out="$TMP/recent-owner.json"
TEST_CASE=recent-dead-owner
status=$(run_preflight "$out" "$PREFLIGHT")
assert_equal "$status" "2"
assert_contains "$(cat "$out")" '"result":"BLOCKED"'
assert_contains "$(cat "$out")" '"reason":"STATE_TRANSACTION_ACTIVE"'
assert_gateway_envelope "$out" || fail "recent transaction BLOCKED result omitted gateway metadata"
assert_schema_valid "$out" || fail "recent transaction BLOCKED result is not schema-valid"
assert_equal "$(path_fingerprint "$TXN_DIR")" "$recent_txn"
rm -rf "$TXN_DIR"

write_valid_transaction stale
printf '%s\n' '{"interrupted":true}' > "$STATE"
out="$TMP/recovery.json"
TEST_CASE=stale-dead-recovery
status=$(run_preflight "$out" "$PREFLIGHT")
assert_equal "$status" "0"
assert_equal "$(sha256sum "$STATE")" "$after_state"
[ ! -e "$TXN_DIR" ] || fail "verified stale recovery journal was not removed"

write_valid_transaction stale
printf '%s\n' '{"version":1,"stage":"PREPARED"}' > "$TXN_DIR/journal.json"
malformed_txn=$(path_fingerprint "$TXN_DIR")
out="$TMP/malformed-journal.json"
TEST_CASE=malformed-journal
status=$(run_preflight "$out" "$PREFLIGHT")
assert_equal "$status" "5"
assert_contains "$(cat "$out")" '"result":"INVALID_STATE"'
assert_equal "$(path_fingerprint "$TXN_DIR")" "$malformed_txn"
rm -rf "$TXN_DIR"

write_valid_transaction stale
printf '%s\n' 'backup digest mismatch' >> "$TXN_DIR/project-state.json.backup"
mismatched_txn=$(path_fingerprint "$TXN_DIR")
out="$TMP/mismatched-journal.json"
TEST_CASE=mismatched-backup
status=$(run_preflight "$out" "$PREFLIGHT")
assert_equal "$status" "5"
assert_contains "$(cat "$out")" '"result":"INVALID_STATE"'
assert_equal "$(path_fingerprint "$TXN_DIR")" "$mismatched_txn"
rm -rf "$TXN_DIR"

"$REAL_PYTHON" - "$STATE" <<'PY'
import json
import sys

path = sys.argv[1]
with open(path, encoding="utf-8") as handle:
    state = json.load(handle)
runtime = next(item for item in state["helperRuntimes"] if item["environment"] == "LOCAL")
runtime.update({"detectedRuntime": None, "configurationStatus": "UNKNOWN", "version": None, "evidence": []})
environment = next(item for item in state["environments"] if item["kind"] == "LOCAL")
environment.update({"configurationStatus": "UNKNOWN", "notes": ["active writer test state"]})
with open(path, "w", encoding="utf-8", newline="\n") as handle:
    json.dump(state, handle, indent=2)
    handle.write("\n")
PY
active_state=$(sha256sum "$STATE")
out="$TMP/active-writer.json"
writer_release="$TMP/release-writer"
env AI_WORKFLOW_TEST_HOLD_AFTER_PREPARED="$writer_release" "$PREFLIGHT" --record > "$TMP/active-writer-owner.json" 2>&1 &
writer_pid=$!
prepared=0
for _attempt in $(seq 1 100); do
  if [ -f "$TXN_DIR/journal.json" ]; then
    prepared=1
    break
  fi
  sleep 0.05
done
[ "$prepared" = "1" ] || fail "active writer did not publish a PREPARED journal"
"$REAL_PYTHON" - "$TXN_DIR/journal.json" <<'PY' || fail "active writer journal is incomplete"
import json
import re
import sys

with open(sys.argv[1], encoding="utf-8") as handle:
    journal = json.load(handle)
expected = {
    "ai/evidence/local-helper-runtime.json",
    "ai/project-state.json",
    "ai/project-state.md",
}
if journal.get("version") != 1 or journal.get("stage") != "PREPARED":
    raise SystemExit(1)
owner = journal.get("owner", {})
if not isinstance(owner.get("pid"), int) or not owner.get("createdAt"):
    raise SystemExit(1)
files = journal.get("files", [])
if {item.get("target") for item in files} != expected or len(files) != len(expected):
    raise SystemExit(1)
for item in files:
    if not re.fullmatch(r"[a-f0-9]{64}", item.get("intendedSha256", "")):
        raise SystemExit(1)
    previous = item.get("previousSha256")
    if item.get("existed") and not re.fullmatch(r"[a-f0-9]{64}", previous or ""):
        raise SystemExit(1)
PY
active_txn=$(path_fingerprint "$TXN_DIR")
TEST_CASE=active-writer
status=$(run_preflight "$out" "$PREFLIGHT")
assert_equal "$status" "2"
assert_contains "$(cat "$out")" '"result":"BLOCKED"'
assert_contains "$(cat "$out")" '"reason":"STATE_TRANSACTION_ACTIVE"'
assert_equal "$(path_fingerprint "$TXN_DIR")" "$active_txn"
assert_equal "$(sha256sum "$STATE")" "$active_state"
: > "$writer_release"
set +e
wait "$writer_pid"
writer_status=$?
set -e
writer_pid=
if [ "$writer_status" != "0" ]; then
  cat "$TMP/active-writer-owner.json" >&2
fi
assert_equal "$writer_status" "0"
assert_equal "$(sha256sum "$STATE")" "$after_state"
assert_equal "$(sha256sum "$SUMMARY")" "$after_summary"
assert_equal "$(sha256sum "$EVIDENCE")" "$after_evidence"
[ ! -e "$TXN_DIR" ] || fail "successful active writer left its transaction lock behind"

out="$TMP/staged-failure.json"
TEST_CASE=staged-failure
status=$(run_preflight "$out" env AI_WORKFLOW_TEST_FAIL_AFTER_STAGE=1 "$PREFLIGHT" --record)
assert_equal "$status" "5"
assert_contains "$(cat "$out")" '"result":"INVALID_STATE"'
assert_contains "$(cat "$out")" '"reason":"STATE_RECORDING_FAILED"'
assert_contains "$(cat "$out")" '"errors":[]'
assert_contains "$(cat "$out")" '"data":null'
assert_schema_valid "$out" || fail "non-PASS gateway result does not validate against gateway-result.schema.json"
assert_equal "$(sha256sum "$STATE")" "$after_state"
assert_equal "$(sha256sum "$SUMMARY")" "$after_summary"
assert_equal "$(sha256sum "$EVIDENCE")" "$after_evidence"

case "$before_state$before_summary$before_evidence" in
  '') fail "state checksum capture failed" ;;
esac
case "$(find "$ROOT" -maxdepth 1 -name .ai-runs -print -quit)" in
  '') ;;
  *) fail ".ai-runs was created" ;;
esac

set +e
TEST_CASE=helper-test-arguments
"$HELPER_TESTS" unexpected > "$TMP/helper-args.out" 2>&1
helper_status=$?
set -e
assert_equal "$helper_status" "5"

helper_call_log="$TMP/helper-calls.log"
: > "$helper_call_log"
helper_caller="$TMP/helper caller"
mkdir -p "$helper_caller"
TEST_CASE=helper-test-caller-cwd
caller_cwd=$PWD
cd "$helper_caller"
status=$(run_preflight "$TMP/helper-launch.out" env \
  PATH="$fake_dir" \
  REAL_PYTHON="$REAL_PYTHON" \
  FAKE_CALL_LOG="$helper_call_log" \
  FAKE_PROBE_RESULT='3|Draft202012Validator|FormatChecker' \
  FAKE_EXEC_ONLY=1 \
  "$HELPER_TESTS")
cd "$caller_cwd"
assert_equal "$status" "0"
assert_contains "$(cat "$helper_call_log")" '-m unittest scripts/ai/tests/test_workflow_helper.py -v'
case "$(tail -n 1 "$helper_call_log")" in
  "$ROOT"'|'*) ;;
  *) fail "helper-test launcher did not anchor its working directory to the repository" ;;
esac
printf 'PASS: runtime preflight contract\n'
