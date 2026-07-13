#!/usr/bin/env bash
set -eu

PATH=/usr/bin:/bin:$PATH
SOURCE_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../../.." && pwd)
COMMAND_RUNNER_SOURCE="$SOURCE_ROOT/scripts/ai/command-runner.sh"
WORKFLOW_GATE_SOURCE="$SOURCE_ROOT/scripts/ai/workflow-gate.sh"
DONE_CLAIM_SOURCE="$SOURCE_ROOT/scripts/ai/done-claim-check.sh"
HELPER_SOURCE="$SOURCE_ROOT/scripts/ai/workflow_helper.py"
TMP=$(mktemp -d "${TMPDIR:-/tmp}/command-runner.XXXXXX")
ROOT="$TMP/repository with spaces"
FAKE_BIN="$TMP/fake-bin"
CALL_LOG="$TMP/helper-calls.log"
LAUNCH_LOG="$TMP/launches.log"
OUTPUT="$TMP/output"

cleanup() {
  status=$?
  rm -rf "$TMP"
  trap - EXIT HUP INT TERM
  exit "$status"
}

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

assert_equal() {
  [ "$1" = "$2" ] || fail "${TEST_CASE:-unlabeled}: expected [$2], got [$1]"
}

assert_file_line() {
  grep -F -x -- "$2" "$1" >/dev/null || fail "${TEST_CASE:-unlabeled}: missing line [$2]"
}

run_capture() {
  set +e
  "$@" >"$OUTPUT" 2>&1
  status=$?
  set -e
  CAPTURED_OUTPUT=$(cat "$OUTPUT")
  CAPTURED_STATUS=$status
}

run_mocked() {
  MOCK_OUTPUT=$1
  MOCK_STATUS=$2
  export MOCK_OUTPUT MOCK_STATUS
  shift 2
  run_capture "$@"
}

invalid_result() {
  operation=$1
  reason=$2
  printf '%s' "{\"\$schema\":\"ai/schemas/gateway-result.schema.json\",\"\$id\":\"ai/gateway-result.json\",\"schemaVersion\":1,\"operation\":\"$operation\",\"result\":\"POLICY_VIOLATION\",\"reason\":\"$reason\",\"errors\":[],\"data\":null}"
}

trap cleanup EXIT HUP INT TERM

[ -f "$COMMAND_RUNNER_SOURCE" ] || fail "command-runner.sh is absent (expected RED before implementation)"
[ -f "$WORKFLOW_GATE_SOURCE" ] || fail "workflow-gate.sh is absent (expected RED before implementation)"
[ -f "$DONE_CLAIM_SOURCE" ] || fail "done-claim-check.sh is absent"
[ -f "$HELPER_SOURCE" ] || fail "workflow_helper.py is absent"

mkdir -p "$ROOT/scripts/ai" "$FAKE_BIN"
cp "$COMMAND_RUNNER_SOURCE" "$ROOT/scripts/ai/command-runner.sh"
cp "$WORKFLOW_GATE_SOURCE" "$ROOT/scripts/ai/workflow-gate.sh"
cp "$DONE_CLAIM_SOURCE" "$ROOT/scripts/ai/done-claim-check.sh"
cp "$HELPER_SOURCE" "$ROOT/scripts/ai/workflow_helper.py"
chmod +x "$ROOT/scripts/ai/command-runner.sh" "$ROOT/scripts/ai/workflow-gate.sh" "$ROOT/scripts/ai/done-claim-check.sh"

cat >"$FAKE_BIN/python3" <<'FAKE'
#!/bin/sh
set -eu
if [ "${1:-}" = "-c" ]; then
  printf '%s\n' '3|Draft202012Validator|FormatChecker'
  exit 0
fi
{
  printf '%s\n' 'CALL'
  for argument in "$@"; do
    printf 'ARG:%s\n' "$argument"
  done
} >> "$CALL_LOG"
if [ "${2:-}" = "execute-command" ]; then
  printf '%s\n' launch >> "$LAUNCH_LOG"
fi
printf '%s\n' "$MOCK_OUTPUT"
exit "$MOCK_STATUS"
FAKE
chmod +x "$FAKE_BIN/python3"
export PATH="$FAKE_BIN:/usr/bin:/bin" CALL_LOG LAUNCH_LOG
: >"$CALL_LOG"
: >"$LAUNCH_LOG"

RUNNER="$ROOT/scripts/ai/command-runner.sh"
GATE="$ROOT/scripts/ai/workflow-gate.sh"
DONE="$ROOT/scripts/ai/done-claim-check.sh"

TEST_CASE=start-route
relay='{"operation":"RUN_START","result":"PASS","reason":null,"errors":[],"data":{"runId":"run 1","taskKey":"task;literal","sessionRef":".ai-runs/run 1/.state/run-session.json"}}'
run_mocked "$relay" 0 "$RUNNER" start --run-id 'run 1' --task-key 'task;literal'
assert_equal "$CAPTURED_STATUS" 0
assert_equal "$CAPTURED_OUTPUT" "$relay"
assert_file_line "$CALL_LOG" 'ARG:run-start'
assert_file_line "$CALL_LOG" 'ARG:run 1'
assert_file_line "$CALL_LOG" 'ARG:task;literal'

TEST_CASE=run-route-and-quoted-forwarding
relay='{"operation":"POST_COMMAND","result":"FAIL","reason":"CHILD_EXIT_NONZERO","errors":[],"data":{"processExitCode":17}}'
run_mocked "$relay" 1 "$RUNNER" run 'verify.unit' --run-id 'run 1' \
  --parameters-file 'tmp/parameters file.json' \
  --rerun-reason-file 'tmp/reason;literal.txt' \
  --approval-ref 'tmp/approval $literal.json'
assert_equal "$CAPTURED_STATUS" 1
assert_equal "$CAPTURED_OUTPUT" "$relay"
for expected in \
  'ARG:execute-command' 'ARG:verify.unit' 'ARG:run 1' \
  'ARG:tmp/parameters file.json' 'ARG:tmp/reason;literal.txt' 'ARG:tmp/approval $literal.json'; do
  assert_file_line "$CALL_LOG" "$expected"
done
assert_equal "$(wc -l <"$LAUNCH_LOG" | tr -d ' ')" 1

TEST_CASE=workflow-gate-routes-never-launch
run_mocked '{"operation":"PRE_COMMAND","result":"PASS"}' 0 "$GATE" PRE_COMMAND \
  --run-id run-2 --command-id verify.unit --approval-ref tmp/approval.json
assert_equal "$CAPTURED_STATUS" 0
assert_file_line "$CALL_LOG" 'ARG:pre-command'
run_mocked '{"operation":"POST_COMMAND","result":"BLOCKED"}' 2 "$GATE" POST_COMMAND \
  --run-id run-2 --attempt-id attempt-1
assert_equal "$CAPTURED_STATUS" 2
assert_file_line "$CALL_LOG" 'ARG:post-command'
assert_equal "$(wc -l <"$LAUNCH_LOG" | tr -d ' ')" 1

TEST_CASE=done-claim-check-prepare-route
relay='{"operation":"PRE_DONE_CLAIM","result":"PASS","reason":null,"errors":[],"data":{"completenessEvaluated":false,"scope":"INTEGRITY_ONLY"}}'
run_mocked "$relay" 0 "$DONE" prepare 'run 1' --claim '.ai-runs/run 1/claim input.json'
assert_equal "$CAPTURED_STATUS" 0
assert_equal "$CAPTURED_OUTPUT" "$relay"
assert_file_line "$CALL_LOG" 'ARG:done-claim-prepare'
assert_file_line "$CALL_LOG" 'ARG:run 1'
assert_file_line "$CALL_LOG" 'ARG:.ai-runs/run 1/claim input.json'
assert_equal "$(wc -l <"$LAUNCH_LOG" | tr -d ' ')" 1
run_mocked "$relay" 0 "$DONE" verify-finalized 'run 1'
assert_equal "$CAPTURED_STATUS" 0
assert_equal "$CAPTURED_OUTPUT" "$relay"
assert_file_line "$CALL_LOG" 'ARG:verify-finalized'

TEST_CASE=matrix-relay
for row in \
  'RUN_START PASS 0' 'RUN_START BLOCKED 2' 'RUN_START NOT_CONFIGURED 3' \
  'RUN_START POLICY_VIOLATION 4' 'RUN_START INVALID_STATE 5' \
  'PRE_COMMAND PASS 0' 'PRE_COMMAND BLOCKED 2' 'PRE_COMMAND NOT_CONFIGURED 3' \
  'PRE_COMMAND POLICY_VIOLATION 4' 'PRE_COMMAND INVALID_STATE 5' \
  'POST_COMMAND PASS 0' 'POST_COMMAND FAIL 1' 'POST_COMMAND BLOCKED 2' \
  'POST_COMMAND NOT_CONFIGURED 3' 'POST_COMMAND POLICY_VIOLATION 4' 'POST_COMMAND INVALID_STATE 5' \
  'PRE_DONE_CLAIM PASS 0' 'PRE_DONE_CLAIM FAIL 1' 'PRE_DONE_CLAIM BLOCKED 2' \
  'PRE_DONE_CLAIM NOT_CONFIGURED 3' 'PRE_DONE_CLAIM POLICY_VIOLATION 4' 'PRE_DONE_CLAIM INVALID_STATE 5'; do
  set -- $row
  operation=$1
  result=$2
  expected_status=$3
  relay="{\"operation\":\"$operation\",\"result\":\"$result\",\"sentinel\":\"unchanged\"}"
  case "$operation" in
    RUN_START) run_mocked "$relay" "$expected_status" "$GATE" RUN_START --run-id run-3 --task-key task-3 ;;
    PRE_COMMAND) run_mocked "$relay" "$expected_status" "$GATE" PRE_COMMAND --run-id run-3 --command-id verify.unit ;;
    POST_COMMAND) run_mocked "$relay" "$expected_status" "$GATE" POST_COMMAND --run-id run-3 --attempt-id attempt-1 ;;
    PRE_DONE_CLAIM) run_mocked "$relay" "$expected_status" "$DONE" prepare run-3 --claim .ai-runs/run-3/claim.json ;;
  esac
  assert_equal "$CAPTURED_STATUS" "$expected_status"
  assert_equal "$CAPTURED_OUTPUT" "$relay"
done

TEST_CASE=closed-invalid-runner-forms
expected=$(invalid_result RUN_START INVALID_RUN_START_ARGUMENTS)
for encoded in \
  'start|--task-key|task|--run-id|run' \
  'start|--run-id|run|--run-id|again' \
  'start|--run-id|run|--task-key' \
  'start|--run-id|run|--task-key|task|extra'; do
  old_ifs=$IFS; IFS='|'; set -- $encoded; IFS=$old_ifs
  run_capture "$RUNNER" "$@"
  assert_equal "$CAPTURED_STATUS" 4
  assert_equal "$CAPTURED_OUTPUT" "$expected"
done
expected=$(invalid_result PRE_COMMAND INVALID_EXECUTE_COMMAND_ARGUMENTS)
for encoded in \
  'run|verify.unit|--run-id' \
  'run|verify.unit|--run-id|run|raw-string' \
  'run|verify.unit|--parameters-file|p.json|--run-id|run' \
  'run|verify.unit|--run-id|run|--approval-ref|a.json|--parameters-file|p.json' \
  'run|verify.unit|--run-id|run|--approval-ref|a.json|--approval-ref|b.json'; do
  old_ifs=$IFS; IFS='|'; set -- $encoded; IFS=$old_ifs
  run_capture "$RUNNER" "$@"
  assert_equal "$CAPTURED_STATUS" 4
  assert_equal "$CAPTURED_OUTPUT" "$expected"
done
expected=$(invalid_result PRE_DONE_CLAIM INVALID_DONE_CLAIM_ARGUMENTS)
for encoded in \
  'prepare|--claim|claim.json|run' \
  'prepare|run|--claim' \
  'prepare|run|--claim|claim.json|extra' \
  'verify-finalized' \
  'verify-finalized|run|extra' \
  'finalize|run|--claim|claim.json'; do
  old_ifs=$IFS; IFS='|'; set -- $encoded; IFS=$old_ifs
  run_capture "$DONE" "$@"
  assert_equal "$CAPTURED_STATUS" 4
  assert_equal "$CAPTURED_OUTPUT" "$expected"
done

TEST_CASE=closed-invalid-gate-forms
expected=$(invalid_result PRE_COMMAND INVALID_PRE_COMMAND_ARGUMENTS)
run_capture "$GATE" PRE_COMMAND --command-id verify.unit --run-id run
assert_equal "$CAPTURED_STATUS" 4
assert_equal "$CAPTURED_OUTPUT" "$expected"
expected=$(invalid_result POST_COMMAND INVALID_POST_COMMAND_ARGUMENTS)
run_capture "$GATE" POST_COMMAND --run-id run --attempt-id attempt --extra raw
assert_equal "$CAPTURED_STATUS" 4
assert_equal "$CAPTURED_OUTPUT" "$expected"
expected=$(invalid_result RUN_START INVALID_RUN_START_ARGUMENTS)
run_capture "$GATE" FINALIZE --run-id run --task-key task
assert_equal "$CAPTURED_STATUS" 4
assert_equal "$CAPTURED_OUTPUT" "$expected"
assert_equal "$(wc -l <"$LAUNCH_LOG" | tr -d ' ')" 1

TEST_CASE=static-shell-boundary
for shell in "$COMMAND_RUNNER_SOURCE" "$WORKFLOW_GATE_SOURCE" "$DONE_CLAIM_SOURCE"; do
  grep -F 'set -eu' "$shell" >/dev/null || fail "$shell lacks set -eu"
  if grep -E '(^|[^[:alnum:]_])(eval|jq)([^[:alnum:]_]|$)|sh -c|bash -c' "$shell" >/dev/null; then
    fail "$shell contains forbidden evaluation or JSON parsing"
  fi
done
grep -F 'execute-command' "$COMMAND_RUNNER_SOURCE" >/dev/null || fail 'runner does not name execute-command'
if grep -F 'execute-command' "$WORKFLOW_GATE_SOURCE" >/dev/null; then
  fail 'workflow gate reaches execute-command'
fi
if grep -E 'FINALIZ|PRE_DONE|artifact-manifest|run\.json' "$COMMAND_RUNNER_SOURCE" "$WORKFLOW_GATE_SOURCE" >/dev/null; then
  fail 'command/gate shell contains Phase 1B-3 behavior'
fi
grep -F 'PRE_DONE_CLAIM' "$DONE_CLAIM_SOURCE" >/dev/null || fail 'done-claim shell lacks PRE_DONE_CLAIM'
grep -F 'done-claim-prepare' "$DONE_CLAIM_SOURCE" >/dev/null || fail 'done-claim shell does not call helper prepare operation'
grep -F 'verify-finalized' "$DONE_CLAIM_SOURCE" >/dev/null || fail 'done-claim shell does not call helper verify operation'

printf '%s\n' 'PASS: thin closed command shell contracts'
