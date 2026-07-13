---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-task-1-reviewer
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: phase-1b-2-task-1-reviewer
started_at: 2026-07-11T12:31:55+09:00
ended_at: 2026-07-11T13:15:58+09:00
last_updated: 2026-07-13T08:54:37+09:00
branch: main
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - ai/schemas/run-session.schema.json
  - ai/schemas/process-attempt.schema.json
  - ai/schemas/artifact-manifest.schema.json
  - ai/schemas/gateway-result.schema.json
  - ai/schemas/command-result.schema.json
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
changed_files:
  - ai/work-logs/issue-4/phase-1b-2-task-1-reviewer.md
commands_run:
  - "Static review only; no tests were rerun and no product commands were run."
  - "Static re-review only; inspected the three finding fixes in current schemas, helper, and tests without rerunning tests or product commands."
  - "Final static Task 1 re-review only; inspected B2 tuple semantics, the 144-combination process matrix, and Phase 1A compatibility without rerunning tests or product commands."
tests_run:
  - "Accepted fresh evidence, not rerun: bash scripts/ai/run-helper-tests.sh exited 0; Ran 66 tests; OK (skipped=7 existing Windows symlink-only cases)."
  - "Accepted fresh evidence, not rerun: bash scripts/ai/tests/test-runtime-preflight.sh exited 0; PASS: runtime preflight contract."
  - "Accepted recorded review-fix evidence, not rerun: bash scripts/ai/run-helper-tests.sh exited 0; Ran 76 tests; OK (skipped=7 existing Windows symlink-only cases)."
  - "Accepted recorded review-fix evidence, not rerun: bash scripts/ai/tests/test-runtime-preflight.sh exited 0; PASS: runtime preflight contract."
  - "Accepted recorded final Task 1 evidence, not rerun: bash scripts/ai/run-helper-tests.sh exited 0; Ran 79 tests; OK (skipped=7 existing Windows symlink-only cases)."
  - "Accepted recorded final Task 1 evidence, not rerun: bash scripts/ai/tests/test-runtime-preflight.sh exited 0; PASS: runtime preflight contract."
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

**Final Task 1 verdict: PASS / APPROVED.** All original and re-review findings are closed. Current findings are Critical none, Important none, Minor none. No test or product command was rerun; `.ai-runs` remains absent.

# Original Findings

## Critical

- None.

## Important

1. **Gateway publication fallback mislabels every new operation as PREFLIGHT.** [scripts/ai/workflow_helper.py](../../../scripts/ai/workflow_helper.py) lines 1064-1066 retain only `PREFLIGHT` and `RESOLVE`, although Task 1 requires fallback selection for `RUN_START`, `PRE_COMMAND`, and `POST_COMMAND`. A malformed result for any new operation therefore publishes `PREFLIGHT/INVALID_STATE`, violating the exact operation/result contract. Fix: preserve all five approved Phase 1B-2 operation names in the fallback allowlist and add focused fallback tests for each new operation.

2. **Run-session validation leaves required terminal and history relationships open.** [ai/schemas/run-session.schema.json](../../../ai/schemas/run-session.schema.json) lines 93-99 allow a terminal `BLOCKED` reservation with `processAttemptRef: null`, despite the Phase 1B-2 outcome table requiring a process-attempt artifact for each terminal post-reservation outcome; its safe publication-failure exception remains `RESERVED`. Lines 68-69 also permit only one of the rerun correlation fields to be null. [scripts/ai/workflow_helper.py](../../../scripts/ai/workflow_helper.py) lines 411-464 do not require each `lockRecoveries[*].runId` to match the enclosing session or reject duplicate reservation `(commandId, attemptId)` tuples. Fix: require a tuple-matching process-attempt reference for every terminal state, require `rerunReasonHash` and `rerunOfAttemptId` to be jointly null or jointly present, bind every lock-recovery run ID to the session and make recovery IDs unique, and reject duplicate reservation tuples. Cover these invalid graphs directly.

3. **Fixtures and tests do not exercise the required forbidden process/gateway combinations.** [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 365-389 cover only one `LAUNCHED/EXITED/SCRUBBED` and one spawn-failure fixture; they omit valid timeout/resource and UNSCRUBBED/NOT_APPLIED combinations and the crossed invalid combinations that must be rejected. Lines 274-314 likewise omit negative RUN_START/PRE_COMMAND cases that place `argv` or any data in a non-PASS branch, and do not test null/empty reason constraints per new branch. Fix: parameterize every valid process-attempt combination and reject every forbidden launch/termination/exit/redaction/reason combination; add one negative test per RUN_START/PRE_COMMAND/POST_COMMAND branch boundary, including non-PASS argv exclusion.

## Minor

- None.

# Verified Scope

- The three new schemas use Draft 2020-12, stable internal URNs, closed objects, and local-fragment references only.
- `OPEN` and `FINALIZING` are schema-compatible; empty reference arrays and zero-byte manifest entries are accepted. Manifest path uniqueness is enforced by the thin in-memory validator.
- `command-result` additions are optional. Existing Phase 1A valid fixtures remain valid, and the established Phase 1A invalid-fixture regression continues to target all invalid fixtures.
- Exactly the three requested schemas were added to the internal allowlist. The new semantic checks operate on supplied instances and do not read caller-selected paths.
- No Phase 1B-3 manifest publication, finalization, `run.json`, or PRE_DONE_CLAIM behavior was added.

# Verification Evidence

- Accepted recorded helper evidence: exit `0`; `Ran 79 tests`; `OK (skipped=7)`, with skips limited to existing Windows symlink-only cases.
- Accepted recorded runtime-preflight evidence: exit `0`; `PASS: runtime preflight contract`.
- This review was static only. Product commands: NOT RUN.

# Re-review Dispositions

## 1. Five-operation fallback preservation

**CLOSED.** [scripts/ai/workflow_helper.py](../../../scripts/ai/workflow_helper.py) lines 48 and 1098-1123 preserve `PREFLIGHT`, `RESOLVE`, `RUN_START`, `PRE_COMMAND`, and `POST_COMMAND` when malformed output is replaced with `INVALID_STATE`. [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 633-656 exercise all three newly added operations and validate the fallback envelope.

## 2. Terminal refs, rerun pairing, recovery/reservation uniqueness, and tuple paths

**PARTIALLY CLOSED; NEW IMPORTANT FINDING.** Terminal reservations now require both refs, RESERVED requires neither, rerun fields are paired, lock-recovery run IDs and IDs are checked, reservation tuples and attempt IDs are unique, and run-session terminal refs use exact tuple-derived paths. Those original sub-findings are closed.

The broader exact-path contract is still incomplete. [scripts/ai/workflow_helper.py](../../../scripts/ai/workflow_helper.py) lines 334-354 validate a B2 command result's `processAttemptRef` but never require its own `$id` to equal `.ai-runs/<runId>/commands/<commandId>/<attemptId>.json`. Lines 357-400 also have no gateway-result semantic branch, so RUN_START `sessionRef` and POST_COMMAND `processAttemptRef`/`commandResultRef` remain generic repository paths rather than tuple-correlated paths. The compatibility test at [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 616-625 currently demonstrates the command-result hole by adding B2 fields to the Phase 1A fixture while retaining its fixture-path `$id` and accepting it.

Exact fix: keep Phase 1A instances unchanged, but when either additive B2 command-result field is present require both fields, the tuple-derived command-result `$id`, and the tuple-derived process-attempt ref. Add in-memory gateway semantic checks for exact RUN_START and POST_COMMAND refs, plus negative tests that alter each run/command/attempt path segment independently.

## 3. Exhaustive process/gateway negative matrix

**OPEN.** Gateway branch negatives are now adequately covered. Process coverage is improved but is not exhaustive as requested. [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 525-589 omit schema-valid `RESOURCE_LIMIT/SCRUBBED`, non-zero `EXITED/SCRUBBED`, non-zero `EXITED/UNSCRUBBED`, and timeout/resource attempts with a known integer native exit, all of which the current schema accepts. The crossed-negative table is representative rather than exhaustive across launch, termination, exit, redaction, and reason dimensions.

Exact fix: derive a parameterized table from every accepted schema combination, including nullable versus known timeout/resource exit codes, then generate or enumerate every forbidden cross-product with an asserted rejection reason. Keep the existing gateway negatives.

# Final Task 1 Re-review

## B2 Command-result Correlation

**CLOSED.** [scripts/ai/workflow_helper.py](../../../scripts/ai/workflow_helper.py) lines 334-366 require both additive B2 fields, the exact tuple-derived command-result `$id`, and the exact tuple-derived `processAttemptRef`. The B2 checks remain opt-in at lines 412-415, so Phase 1A command results with neither additive field retain their original behavior. [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 665-712 cover unchanged Phase 1A form, both partial-field forms, a valid B2 form, and independent run/command/attempt mutations for both paths.

## Gateway Tuple Correlation

**CLOSED.** [scripts/ai/workflow_helper.py](../../../scripts/ai/workflow_helper.py) lines 369-404 bind RUN_START/PASS `sessionRef` to its run ID and POST_COMMAND PASS/FAIL/BLOCKED command/process refs to their run/command/attempt tuple. [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 714-744 cover RUN_START mismatch and every POST terminal branch with independent run, command, and attempt path mutations.

## Exhaustive Process Matrix

**CLOSED.** [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 596-647 enumerate the complete `2 x 4 x 3 x 3 x 2 = 144` launch/termination/exit/redaction/reason space and require the schema-accepted set to equal exactly the explicit 17-combination approved table. Every rejected combination must expose a conditional `const`, `enum`, `type`, or `minLength` reason.

## Phase 1A Compatibility

**CLOSED.** The B2 semantic gate is conditional on additive fields. Existing regressions at [scripts/ai/tests/test_workflow_helper.py](../../../scripts/ai/tests/test_workflow_helper.py) lines 1040-1055 continue to cover all 9 valid and all 24 invalid Phase 1A fixtures, with semantic-invalid registry coverage retained at lines 1096-1106.

## Final Findings

### Critical

- None.

### Important

- None.

### Minor

- None.

# Current Findings

## Critical

- None.

## Important

- None.

## Minor

- None.

# Historical Next Handoff
- Next role: Orchestrator
- Required reading:
  - [Phase 1B specification](../../../docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md)
  - [Phase 1B-2 implementation plan](../../../docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md)
  - [This review](phase-1b-2-task-1-reviewer.md)
- Remaining work: None in Task 1 review scope.
- Evidence required: Preserve the accepted `Ran 79`, `OK (skipped=7)`, and runtime-preflight PASS evidence in the next handoff.
