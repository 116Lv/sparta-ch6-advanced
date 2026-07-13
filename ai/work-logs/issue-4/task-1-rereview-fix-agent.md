---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: task-1-rereview-fix-agent
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: task-1-rereview-fix-agent
started_at: 2026-07-10T17:23:49Z
ended_at: 2026-07-11T00:00:00Z
last_updated: 2026-07-13T08:54:37+09:00
branch: main
related_files:
  - ai/work-logs/issue-4/task-1-preflight-brief.md
  - ai/work-logs/issue-4/task-1-rereviewer.md
changed_files:
  - scripts/ai/runtime-preflight.sh
  - scripts/ai/run-helper-tests.sh
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test-runtime-preflight.sh
  - ai/work-logs/issue-4/task-1-rereview-fix-agent.md
commands_run:
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/tests/test-runtime-preflight.sh"
tests_run:
  - "RED shell probe: FAIL: python3-precedence: expected [0], got [3] after the isolated fake candidate stopped reporting jsonschema.__version__."
  - "RED publication gate: metadata: expected validated fallback INVALID_STATE/5, got {'result': 'NOT_CONFIGURED', 'reason': 'JSONSCHEMA_METADATA_UNAVAILABLE'}/3."
  - "GREEN: exit 0, PASS: runtime preflight contract (24.9 seconds)."
  - "RED transaction creation durability: transaction creation was not durably ordered: ['transaction:mkdir', 'atomic:start:owner.json', ...]."
  - "GREEN transaction creation durability: exit 0, PASS: runtime preflight contract (24.9 seconds)."
blockers: []
reconciliation_required: true
issue_creation_attempted_at: 2026-07-10T12:37:12Z
issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"
expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 1B command gateway without product behavior changes."
migration_history:
  - migrated_at: 2026-07-13T08:54:37+09:00
    from: ai/work-logs/no-issue/phase-1b-command-gateway
    to: ai/work-logs/issue-4
---

## Reconciliation Update

GitHub Issue #4 now backs this historical role record. Statements below about unavailable Issue creation, pending reconciliation, or the earlier 403 describe the state when this role executed; they are not current blockers.

# Summary

DONE_WITH_CONCERNS. Fixed the complete Task 1 second re-review set with isolated RED/GREEN coverage. The only remaining concern is the pre-existing `pending_issue` reconciliation requirement; no Issue can be created from this role because the recorded GitHub API authorization failure remains unresolved.

# Work Done

- Added isolated regressions which corrupt intended branch results for metadata, interpreter, transaction/recovery, and record failure paths. Each must return the schema-valid `GATEWAY_RESULT_SCHEMA_INVALID` INVALID_STATE fallback at exit 5.
- Centralized all non-bootstrap result publication through `publish_result`. It validates the intended gateway result before output and never preserves NOT_CONFIGURED or BLOCKED when validation fails. A malformed gateway schema produces the fixed INVALID_STATE/5 control-plane fallback because no result can validate against malformed schema.
- Added file and directory durability barriers: file fsync before each rename, directory fsync after rename, fsynced backup copies followed by a transaction-directory barrier before PREPARED publication, and parent-directory fsync after transaction removal.
- Added a narrow directory-fsync unsupported-platform fallback for EINVAL, ENOTSUP/EOPNOTSUPP, plus Windows directory-descriptor access limitations. Other errors propagate.
- Reworked both shell probes to require only Python major version 3 and imports/names of Draft202012Validator and FormatChecker. jsonschema version discovery remains in the helper via structured package metadata handling.

# Historical State At Execution
- Isolated contract is GREEN: `PASS: runtime preflight contract`, exit 0.
- Source canonical fingerprints and any pre-existing source transaction state were confirmed unchanged by the harness exit trap.
- Product commands were not run and `.ai-runs` was not created.

# Finding Dispositions

1. **Non-bootstrap result publication - FIXED.** Metadata, interpreter, transaction/recovery, state recording, invalid argument, and BLOCKED branches now use one validation gate. When the intended result cannot validate, the helper returns `INVALID_STATE`, `GATEWAY_RESULT_SCHEMA_INVALID`, exit 5; fixed shell runtime-unavailable JSON remains the bootstrap-only exception.
2. **Power-loss durability - FIXED.** `atomic_write` fsyncs the parent directory after rename. Backup content fsyncs precede a transaction-directory fsync before the PREPARED journal. Journal and canonical target replacements use the same rename-plus-directory barrier; transaction removal fsyncs its parent. The regression wraps these primitives in an isolated copied repository and proves the ordering deterministically.
3. **Shell jsonschema version dependence - FIXED.** `runtime-preflight.sh` and `run-helper-tests.sh` no longer read `jsonschema.__version__`; their candidate probes accept only `3|Draft202012Validator|FormatChecker`.

# Verification Evidence

- RED command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
- RED output: `FAIL: python3-precedence: expected [0], got [3]` after the probe regression changed to remove jsonschema version output.
- RED output: `metadata: expected validated fallback INVALID_STATE/5, got {'result': 'NOT_CONFIGURED', 'reason': 'JSONSCHEMA_METADATA_UNAVAILABLE'}/3`.
- GREEN command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
- GREEN output: exit `0`, `PASS: runtime preflight contract` (24.9 seconds).
- Product commands: NOT RUN. No install, server, Docker, HTTP/API, database, migration, seed, infrastructure, `.ai-runs`, or commit action was performed.

# Concerns

- `tracking_status: pending_issue` and `reconciliation_required: true` remain because the already-recorded Issue creation attempt received GitHub API 403. This role did not attempt a prohibited GitHub/commit action.

# Historical Next Handoff
- Next role: Task Re-reviewer.
- Required reading: [Task 1 re-review](task-1-rereviewer.md), this fix log, and the current Task 1 scripts/test harness.
- Required evidence: inspect the publication gate and fsync ordering, then rerun only the approved isolated contract.

# Second Re-review Follow-up

## Finding Disposition

4. **Transaction directory-entry durability - FIXED.** `acquire_transaction` now fsyncs the parent `ai/` directory immediately after it successfully creates `ai/.workflow-state-txn` and before it publishes `owner.json`, a PREPARED journal, or any canonical target replacement.

## RED/GREEN Evidence

- RED command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
- RED output: `transaction creation was not durably ordered: ['transaction:mkdir', 'atomic:start:owner.json', ...]`.
- GREEN command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
- GREEN output: exit `0`, `PASS: runtime preflight contract` (24.9 seconds).
- The isolated durability observer now records the transaction-directory creation and requires the first parent `ai/` directory fsync to occur before `owner.json` publication. The harness continued to confirm source canonical state and pre-existing source transaction state were unchanged.
