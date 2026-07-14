---
issue: 14
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/14
agent: implementation-agent
tracking_status: issue_backed
status: in_progress
owning_feature: "none"
current_owner: implementation-agent
started_at: 2026-07-14T02:48:51+09:00
ended_at:
last_updated: 2026-07-14T12:59:25+09:00
branch: codex/ai-workflow-trust-hardening
related_files:
  - docs/superpowers/specs/2026-07-14-ai-workflow-trust-boundary-hardening-design.md
  - docs/superpowers/plans/2026-07-14-phase-1b3-evidence-integrity-hardening.md
  - docs/superpowers/plans/2026-07-14-phase-3b-ci-provenance-hardening.md
changed_files:
  - ai/ci-capability-status.json
  - ai/ci-gates.md
  - ai/schemas/ci-capability-status.schema.json
  - ai/schemas/ci-gate-result.schema.json
  - ai/schemas/github-ci-provenance.schema.json
  - scripts/ai/tests/test_workflow_helper.py
  - scripts/ai/workflow_helper.py
  - ai/work-logs/issue-14/implementation-agent.md
commands_run:
  - "Task 1 RED (expected exit 1): $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_check_evidence_must_be_top_level_and_bound_to_session scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_pass_check_cannot_also_be_declared_not_run -v [2 tests; 2 expected failures; both actual results were ('PASS', 0)]"
  - "Task 1 focused GREEN (exit 0): $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_check_evidence_must_be_top_level_and_bound_to_session scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_pass_check_cannot_also_be_declared_not_run -v [2 tests passed]"
  - "Task 1 surrounding GREEN (exit 0): $env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v [10 tests passed]"
  - "Task 1 self-review (exit 0): git diff --check [no whitespace errors; line-ending conversion warnings only]"
  - "Task 1 commit (exit 0): git commit -m 'fix(ai): bind phase 1b3 claim evidence' [2e25b00; 2 files changed, 77 insertions, 3 deletions]"
tests_run:
  - "Task 1 RED: 2 focused done-claim trust-boundary regressions failed for the expected missing-validation reason."
  - "Task 1 focused GREEN: 2 tests passed."
  - "Task 1 surrounding GREEN: Phase1B3DoneClaimGateTests passed 10 tests."
blockers: []
skill_ids:
  - verification-runner
  - failure-triage
  - docs-sync
handoff_state_ref: ai/agent-handoff.json
reusable_context_refs:
  - ai/workflow-cache.json
  - ai/verification-policy.json
  - ai/native-runtime-adapters.json
not_run_project_commands:
  - Gradle
  - build
  - product/unit project tests
  - application server
  - Docker Compose
  - HTTP/curl/API
  - database
  - migration
  - seed
  - infrastructure commands
github_reconciliation_status: issue_backed
reconciliation_required: false
issue_creation_attempted_at: 2026-07-14T02:48:51+09:00
issue_creation_failure_reason:
expected_issue_scope: AI workflow trust-boundary hardening across Phases 1B-3 through 3B
migration_history: []
---

# Summary

Implement the approved hardening plans one reviewed task at a time without executing prohibited product commands or creating real `.ai-runs` evidence.

# Work Done

- Design, plans, exact-main baseline, and worktree isolation were prepared by the orchestrator.

# Current State

Ready to begin global Task 1 (Phase 1B-3 local Task 1).

# Decisions

- Follow TDD for every task and commit each task before review.

# Verification Evidence

- Command: targeted Python unittest baseline from the Issue summary
- Result: PASS (120 tests); no product command was run

# Blockers

- None

# Next Handoff

- Next role: implementation-agent
- Required reading:
  - [Trust-boundary design](../../docs/superpowers/specs/2026-07-14-ai-workflow-trust-boundary-hardening-design.md)
  - [Phase 1B-3 execution plan](../../docs/superpowers/plans/2026-07-14-phase-1b3-evidence-integrity-hardening.md)
- Context links:
  - [Issue summary](README.md)
- Remaining work: Implement and report the assigned task only.
- Evidence required: TDD RED/GREEN command output, changed files, self-review, and commit.

## Task 1 Update (2026-07-14)

### Changed Files

- `scripts/ai/tests/test_workflow_helper.py`: added the two brief-specified regressions for unbound check evidence and contradictory not-run declarations.
- `scripts/ai/workflow_helper.py`: added closed evidence-graph resolution and not-run consistency validation, then reused resolved command artifacts during semantic aggregation.
- `ai/work-logs/issue-14/implementation-agent.md`: recorded Task 1 TDD evidence and recovery state.

### Decisions

- Validated claim/session binding immediately after done-claim run/task identity, before any PASS/BLOCKED/FAIL aggregation.
- Allowed both active-session command results and gateway results as check evidence, while requiring top-level evidence to equal all check evidence and include every command result.
- Kept finalized-run projection verification and locked rollback untouched because they belong to later Phase 1B-3 tasks.
- Preserved the repository-only integrity boundary: no verification-completeness, registry `VERIFIED`, phase-completion, Issue closure, or unqualified overall `DONE` claim is made.

### Exact Verification Evidence

- RED command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_check_evidence_must_be_top_level_and_bound_to_session scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_pass_check_cannot_also_be_declared_not_run -v`
- RED result: expected exit `1`; 2 tests ran and both failed because the baseline returned `('PASS', 0)` instead of `('INVALID_STATE', 5)`.
- Focused GREEN command: same focused command after implementation.
- Focused GREEN result: exit `0`; 2 tests passed.
- Surrounding GREEN command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`
- Surrounding GREEN result: exit `0`; 10 tests passed.
- Self-review command: `git diff --check`
- Self-review result: exit `0`; no whitespace errors, only Git line-ending conversion warnings.

### Recovery State

- Task 1 implementation and focused evidence were committed as `2e25b00` and are ready for independent review.
- The Task 1 helper/test changes are in `2e25b00`; before the recovery-log commit, this assigned role-log update is the only tracked working-tree change. The required ignored report is at `.superpowers/sdd/task-1-phase1b3-report.md`.
- Next safe action after Task 1 review is the separately scoped finalized-run projection task; rollback hardening remains later scope.
- Gradle, build/product tests, server, Docker, HTTP/API, database, migration, seed, deploy, and infrastructure commands remain NOT RUN. No real repository `.ai-runs` directory was created.

## Task 2 Update (2026-07-14)

### Changed Files

- `scripts/ai/tests/test_workflow_helper.py`: added the two brief-specified finalized-run tampering and stale-result regressions.
- `scripts/ai/workflow_helper.py`: added deterministic finalized-run projection validation against the schema-validated claim, gate, and manifest-kind references.
- `ai/work-logs/issue-14/implementation-agent.md`: recorded Task 2 TDD evidence and recovery state.

### Decisions

- Loaded the final done claim and pre-done gate through their schemas after validating manifest digest and directory closure, then rejected any projection mismatch before returning PASS.
- Compared `commandResultRefs`, `approvalRefs`, and `policyViolationRefs` by manifest kind while preserving the exact ordered final evidence references.
- Preserved `completenessEvaluated: false`, `scope: INTEGRITY_ONLY`, Task 1 evidence binding, and child-failure/policy precedence.
- Kept locked FINALIZING rollback untouched because it belongs to Task 3.

### Exact Verification Evidence

- RED command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_verify_finalized_rejects_tampered_run_json scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_verify_finalized_rejects_stale_run_result -v`
- RED result: expected exit `1`; 2 tests ran and both failed because the baseline returned `('PASS', 0)` instead of `('INVALID_STATE', 5)` after `run.json` tampering.
- Focused GREEN command: same focused command after implementation.
- Focused GREEN result: exit `0`; 2 tests passed in `2.999s`.
- Surrounding GREEN command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`
- Surrounding GREEN result: exit `0`; 12 tests passed in `15.472s`.
- Self-review command: `git diff --check`
- Self-review result: exit `0`; no whitespace errors, only Git line-ending conversion warnings.
- Repository evidence check: `Test-Path -LiteralPath '.ai-runs'`
- Repository evidence result: `.ai-runs` was absent from the isolated checkout; tests used copied temporary repositories only.

### Recovery State

- Task 2 helper/test changes were committed as `3ce67ae` with message `fix(ai): verify finalized run projection` and are ready for independent review.
- The required ignored report is at `.superpowers/sdd/task-2-phase1b3-report.md`; the assigned role-log update is committed separately.
- Gradle, build/product tests, server, Docker, HTTP/API, database, migration, seed, deploy, and infrastructure commands remain NOT RUN. No verification-completeness, registry `VERIFIED`, phase-completion, Issue closure, native/CI enforcement, or unqualified overall `DONE` claim is made.

## Task 3 Update (2026-07-14)

### Changed Files

- `scripts/ai/tests/test_workflow_helper.py`: added validation and I/O failure-injection recovery/retry regressions plus an exact-FINALIZING-session conflict regression.
- `scripts/ai/workflow_helper.py`: added same-owner, exact-session, pre-publication rollback and explicit recovery-required handling.
- `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`: documented evidence closure, not-run contradiction handling, final projection verification, and the bounded rollback boundary.
- `ai/work-logs/issue-14/implementation-agent.md`: recorded Task 3 TDD evidence and recovery state.

### Decisions

- Captured the exact validated OPEN session after immutable-publication resumption and derived the sole acceptable FINALIZING projection from it.
- Required the same held run-lock owner before cleanup and before each deletion, then reused `replace_run_session(..., expected_session=expected_finalizing)` for the final exact compare-and-swap.
- Limited cleanup to the exact done claim, PRE_DONE_CLAIM gate result, and manifest references through the secure run-artifact resolver; any `run.json` entry prevents rollback.
- Mapped any rollback or precondition failure to `BLOCKED` with `FINALIZATION_RECOVERY_REQUIRED`, preserving FINALIZING for explicit recovery and avoiding false finalization.
- Preserved Task 1 evidence binding, Task 2 final projection verification, validation/result precedence, `completenessEvaluated: false`, and `scope: INTEGRITY_ONLY`.

### Exact Verification Evidence

- Baseline command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`
- Baseline result: exit `0`; 12 tests passed in `15.487s`; repository `.ai-runs` was absent.
- RED command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_validation_failure_before_run_publication_rolls_back_and_retries scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_io_failure_before_run_publication_rolls_back_and_retries scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_mutated_finalizing_session_requires_explicit_recovery -v`
- RED result: expected exit `1`; 3 tests failed for the intended missing-recovery reasons. Validation and I/O left `FINALIZING`; the mutated-session case returned the original `INVALID_STATE` instead of explicit recovery-required `BLOCKED`.
- Focused GREEN command: same three-test command after implementation.
- Focused GREEN result: exit `0`; 3 tests passed in `4.885s`.
- Surrounding GREEN command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`
- Surrounding GREEN result after the secure-path refactor: exit `0`; 15 tests passed in `20.814s`; repository `.ai-runs` was absent.
- Self-review command: `git diff --check`
- Self-review result: exit `0`; no whitespace errors, only Git line-ending conversion warnings.

### Recovery State

- Task 3 helper/test/spec changes are committed as `7da8f15` with message `fix(ai): recover failed phase 1b3 finalization` and await independent review.
- The required ignored report is at `.superpowers/sdd/task-3-phase1b3-report.md`; this assigned role-log update is committed separately.
- No Task 4 or later-phase implementation was started. Gradle, build/product tests, server, Docker, HTTP/API, database, migration, seed, deploy, and infrastructure commands remain NOT RUN.
- No verification-completeness, registry `VERIFIED`, phase-completion, Issue closure, native/CI enforcement, or unqualified overall `DONE` claim is made.

## Task 3 Critical Review Fix (2026-07-14)

### Finding And Root Cause

- Critical review found that OPEN-to-FINALIZING and FINALIZING-to-OPEN replacement callers assumed an exception meant the exact compare-and-swap had not taken effect.
- `replace_run_session` can durably apply `os.replace` before a later directory fsync or chmod raises, so the durable session must be reconciled under the retained lock before deciding whether rollback started or succeeded.

### Changed Files

- `scripts/ai/tests/test_workflow_helper.py`: added post-apply exception injection after each session replacement and deep-equality assertions against the full captured OPEN snapshot.
- `scripts/ai/workflow_helper.py`: added exact expected-FINALIZING derivation and schema-valid session rereads bracketed by same-owner lock validation; reconciled both transition and restoration exceptions.
- `.superpowers/sdd/task-3-phase1b3-report.md`: appended the ignored detailed review-fix evidence.
- `ai/work-logs/issue-14/implementation-agent.md`: appended this review-fix recovery record.

### Exact TDD Evidence

- RED command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_transition_exception_after_finalizing_replace_rolls_back_exact_open_session scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_restore_exception_after_open_replace_preserves_original_failure_and_snapshot -v`
- RED result: expected exit `1`; 2 tests failed in `2.481s`. The transition case retained FINALIZING instead of the complete OPEN snapshot; the restore case returned `BLOCKED / FINALIZATION_RECOVERY_REQUIRED / 2` instead of the original `INVALID_STATE / INJECTED_FINALIZATION_FAILURE / 5` although exact OPEN was durable.
- Focused GREEN command: same two-test command after reconciliation implementation.
- Focused GREEN result: exit `0`; 2 tests passed in `2.616s`.
- Surrounding GREEN command: `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`
- Surrounding GREEN result: exit `0`; 17 tests passed in `23.840s`; repository `.ai-runs` was absent.
- Self-review command: `git diff --check`
- Self-review result: exit `0`; no whitespace errors, only Git line-ending conversion warnings.

### Recovery And Lock Decisions

- After a transition exception, exact expected FINALIZING is treated as started and enters bounded rollback; exact captured OPEN preserves the original result; conflict, unreadability, or owner change returns `FINALIZATION_RECOVERY_REQUIRED` without cleanup.
- After a restore exception, exact captured OPEN is accepted as successful rollback and preserves the original pre-publication result; exact FINALIZING, conflict, unreadability, or owner change remains recovery-required.
- Both reconciliation reads validate the same held lock owner before and after full schema-valid session loading. No state-only match or unlocked bypass was introduced; publication and cleanup guards remain unchanged.

### Recovery State

- Reconciliation helper/test changes are committed as `e2f85d7` with message `fix(ai): reconcile phase 1b3 session replacements` and await independent rereview.
- Gradle, build/product tests, server, Docker, HTTP/API, database, migration, seed, deploy, and infrastructure commands remain NOT RUN. No real repository `.ai-runs` was created.
- No verification-completeness, registry `VERIFIED`, phase-completion, Issue closure, native/CI enforcement, or unqualified overall `DONE` claim is made.

## Task 4 Update — Phase 2 Task 1 (2026-07-14)

### Changed Files

- `ai/schemas/verification-leaf-result.schema.json`: added the closed, strict
  verification leaf artifact contract.
- `ai/schemas/verification-policy.schema.json`: bound every check to a closed
  producer, evidence schema, and change-type applicability array.
- `ai/verification-policy.json`: recorded canonical producer, evidence-schema,
  and `notApplicableFor` values for all nine checks.
- `scripts/ai/workflow_helper.py`: replaced free-form leaf summaries with
  reference loading, strict repository HEAD probing, and leaf/evidence binding
  validation.
- `scripts/ai/tests/test_workflow_helper.py`: added legacy evidence-free,
  correlation/policy/producer/freshness/schema/digest, strict-path/commit, and
  native-forgery regressions; migrated only positive surrounding fixtures.
- `ai/work-logs/issue-14/implementation-agent.md`: appended this Task 4
  implementation evidence.

### Decisions And Schema Compatibility

- Confirmed before implementation that `review-gate`, `done-claim-gate`,
  `failure-triage`, and `verify.static` use
  `ai/schemas/gateway-result.schema.json`; registry-backed unit, integration,
  API-smoke, and E2E checks use `ai/schemas/command-result.schema.json`; the
  internal native check uses `ai/schemas/native-adapter-result.schema.json` in
  canonical policy only.
- `done-claim-gate` binds the gateway evaluation artifact, not the done-claim
  input document. `verify.api-smoke` binds registry-command evidence.
- External native IDs are rejected before referenced evidence lookup, including
  the new bound-ref form. Existing legacy forged-native precedence tests remain
  unchanged and passing.
- Production obtains the checked-out commit only through strict
  `git -C <root> rev-parse HEAD`; there is no caller commit argument or fallback.
  Missing or malformed Git state maps to BLOCKED with
  `VERIFICATION_REPOSITORY_COMMIT_NOT_CONFIGURED`.
- Preserved current aggregation/default behavior because fail-closed defaults,
  optional FAIL visibility, and required NOT_APPLICABLE authority belong to
  Phase 2 Task 2. Cache and skill/handoff exact-set behavior remains Phase 2
  Task 3.

### Exact TDD Evidence

- Required RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests -v`
- Required RED result: expected exit `1`; 11 tests ran in `9.599s` and all 11
  failed for the intended missing-contract reasons. The evidence-free legacy
  PASS reached aggregation; bound refs were not understood; mismatch-specific
  and forged-native reason codes were absent.
- Required focused GREEN command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_evidence_free_legacy_leaf_result_is_rejected scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_bound_leaf_mismatches_are_rejected_before_aggregation scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_valid_bound_leaf_reaches_aggregation scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_external_native_bound_leaf_is_rejected_before_evidence_lookup -v`
- Required focused GREEN result: exit `0`; 4 tests passed in `3.312s`.
- Self-review Git-probe RED: the strict-probe test errored on non-string stdout
  because `re.fullmatch` received `None`; after the minimal type guard the same
  test passed in `0.666s`.
- Self-review schema RED: one focused test produced five expected subtest
  failures because JSON Schema `$` accepted terminal-newline suffixes; after
  portable exact-end guards, the newline and strict-probe tests passed together
  (2 tests in `1.344s`).

### Final Verification Evidence

- Schema allowlist focus:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B2Task1SchemaTests.test_phase_1b2_and_phase_2_schema_names_are_allowlisted -v`
- Schema allowlist result: exit `0`; 1 test passed in `0.155s`.
- Final surrounding command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
- Final surrounding result: exit `0`; 101 tests passed in `37.180s` (13 Phase
  2C and 88 Phase 3A).
- First Phase 3A surrounding run: 87 passed and one positive legacy fixture
  failed. It was migrated to bound refs; no production contract was weakened.
- `git diff --check`: exit `0`; no whitespace errors, only Git line-ending
  warnings.
- Repository evidence checks: `.ai-runs` absent; `__pycache__` absent.

### Commits And Recovery State

- Implementation/schema/test commit: `0be7062` (`fix(ai): verify phase 2 leaf evidence`).
- Detailed ignored report:
  `.superpowers/sdd/task-4-phase2-report.md`.
- This role-log append is committed separately so the worktree returns clean.
- No Gradle, build/product tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, or infrastructure command was run. No real `.ai-runs` was
  created. No push, PR, merge, Issue modification/closure, registry `VERIFIED`,
  phase-complete, native/CI enforcement, or unqualified overall `DONE` claim is
  made.

### Review Fix — Single-Read Evidence Binding (2026-07-14)

- Independent review identified that evidence schema validation and digest
  comparison reopened the same path, allowing different bytes to satisfy each
  check. `verified_leaf_result` now resolves as before, checks the canonical
  evidence schema before loading, opens once, reads at most 65,537 bytes, and
  derives SHA-256, strict JSON parsing, and schema validation from the same
  immutable bytes. The established schema-validation-before-digest reason
  precedence is unchanged.
- Focused RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_leaf_evidence_is_opened_once_and_verified_from_the_same_bytes scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_malformed_leaf_evidence_preserves_strict_json_reason scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_oversized_leaf_evidence_is_rejected_before_schema_validation -v`
- Focused RED result: expected exit `1`; 3 tests ran in `2.230s`. The current
  code reopened evidence and raised `VERIFICATION_LEAF_DIGEST_MISMATCH` when
  the second open returned replacement bytes; oversized evidence incorrectly
  reached normal BLOCKED aggregation. Malformed JSON already preserved
  `MALFORMED_JSON`.
- Focused GREEN command: the same three-test command after the minimal fix.
- Focused GREEN result: exit `0`; 3 tests passed in `2.089s`.
- Phase 2C command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests -v`
- Phase 2C result: exit `0`; 17 tests passed in `14.824s`.
- Phase 2C plus Phase 3A command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
- Compatibility result: exit `0`; 105 tests passed in `39.820s` (17 Phase 2C,
  88 Phase 3A); no compatibility adjustment was needed.
- `git diff --check` and staged `git diff --cached --check` exited `0`;
  recursive `__pycache__` search returned no paths; `.ai-runs` was absent.
- Implementation/tests commit: `ae40d09` (`fix(ai): bind leaf evidence to one
  read`). This evidence append is committed separately.
- No Gradle, build/product tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, infrastructure, push, PR, merge, Issue modification/closure,
  registry `VERIFIED`, phase-complete, native/CI enforcement, or unqualified
  overall `DONE` action or claim was made.

## Task 5 Update - Phase 2 Task 2 (2026-07-14)

### Routing And Handoff

- `tracking_status: issue_backed`; Issue #14:
  `https://github.com/116Lv/sparta-ch6-advanced/issues/14`.
- `owning_feature: none`; this is repo-wide Phase 2C/3A verification-gate
  infrastructure routed through `AGENTS.md`, `ai/document-routing.md`,
  `ai/subagent-workflow.md`, `ai/github-issue-planning.md`,
  `ai/verification-gates.md`, `ai/verification-policy.json`, and the exact Task
  5 brief.
- `skill_ids`: `verification-runner`, `failure-triage`, `docs-sync`;
  `handoff_state_ref`: `ai/agent-handoff.json`; reusable context:
  `ai/workflow-cache.json`, `ai/verification-policy.json`, and
  `ai/native-runtime-adapters.json`; `github_reconciliation_status` is
  `issue_backed`.

### Changed Files And Decisions

- `scripts/ai/workflow_helper.py`: removed policy-only PASS defaults, added the
  three-input leaf mapper, preserved FAIL-over-BLOCKED aggregation, applied
  canonical `notApplicableFor` authority to caller leaves, preserved the
  internal `HOST_UNSUPPORTED` repository-only exception, and emitted verified
  external/native leaf identities.
- `scripts/ai/tests/test_workflow_helper.py`: added isolated required-N/A,
  optional-FAIL, absent-static-leaf, and external/native identity regressions.
- `ai/schemas/verification-gate-result.schema.json`: closed each check output
  over nullable leaf reference/digest/producer/commit/policy identity fields.
- `ai/verification-gates.md`: documented fail-closed defaults, applicability
  authority, optional FAIL visibility, precedence, and identity semantics.
- Verified external checks expose their bound evidence reference and leaf
  identity. Missing/policy-derived checks use null identity fields rather than
  implying verified evidence. The native leaf uses
  `ai/native-adapter-result.json`, a SHA-256 of its canonical in-process result,
  the canonical producer, checked-out commit, and canonical policy digest.
- Task 4's evidence schema/digest validation and external native-forgery
  precedence were not weakened. Cache identity and exact skill/handoff sets
  remain Task 6 scope.

### Exact TDD And Verification Evidence

- Preliminary isolation command: the two brief-specified tests with
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest ... -v` exited `1`, but
  required N/A was masked by another missing required leaf. The test helper was
  corrected to provide bound PASS companions before accepting RED evidence.
- Exact RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_required_caller_not_applicable_is_blocked scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_optional_fail_remains_visible -v`
- Exact RED result: expected exit `1`; both tests failed for the intended
  mapping reasons. Required caller N/A returned `PASS / 0` instead of
  `BLOCKED / 2`; optional FAIL returned `PASS / 0` instead of `FAIL / 1`.
- First focused GREEN result: the same two-test command exited `0`; 2 tests
  passed in `1.742s`.
- Second RED command targeted missing static evidence and verified identity;
  it exited `1`. The missing required static leaf returned `PASS / 0`, and the
  identity test raised `KeyError: 'leafResultRef'`.
- Final focused command covered all four Task 5 regressions; exit `0`; 4 tests
  passed in `3.437s`.
- Final surrounding command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
- Final surrounding result: exit `0`; 109 tests passed in `44.009s` (21 Phase
  2C and 88 Phase 3A). No fixture migration or compatibility weakening was
  needed.
- Phase 1B-3 integrity command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -q`
- Phase 1B-3 result: exit `0`; 17 tests passed in `24.550s`.
- `git diff --check` and staged `git diff --cached --check` exited `0`; only
  line-ending conversion warnings were emitted. Recursive `__pycache__` search
  returned no paths and repository `.ai-runs` was absent.

### Commit And Recovery State

- Implementation/schema/tests/docs commit: `b704018`
  (`fix(ai): fail closed phase 2 aggregation`).
- Detailed ignored report: `.superpowers/sdd/task-5-phase2-report.md`.
- This dated role-log append is committed separately. It records implementation
  evidence only; independent review and orchestration remain with the parent.
- Gradle, build/product tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, infrastructure, real `.ai-runs`, push, PR, merge, and GitHub
  Issue state commands were NOT RUN. No registry `VERIFIED`, phase completion,
  Issue closure, native/CI enforcement, or unqualified overall `DONE` claim is
  made.

### Task 5 Independent Review Fix - Verified Identity Binding (2026-07-14)

- Review found that verified external/native records could validate with null
  identity values, and that `leafResultSha256` reopened the leaf after accepted
  verification bytes had been read.
- `ai/schemas/verification-gate-result.schema.json` now has exclusive closed
  shapes: verified records require all five non-null identities; synthesized
  records require all five null identities and cannot carry raw PASS or FAIL.
  No new discriminator or broad contract field was added.
- `scripts/ai/workflow_helper.py` now reads each referenced leaf once into a
  normalized reference/exact-byte/parsed-value input, passes that input through
  verified loading, and hashes those exact accepted bytes. Aggregation never
  reopens the leaf. Bound evidence keeps its existing one-read validation and
  schema-before-digest precedence.
- `scripts/ai/tests/test_workflow_helper.py` now rejects missing/null verified
  identity, accepts the explicit synthesized shape, forbids synthesized PASS,
  and simulates a PASS first read followed by a valid FAIL replacement while
  asserting one leaf-path open and accepted-byte identity output.
- `ai/verification-gates.md` documents the two exclusive shapes and exact-byte
  digest binding.

Exact schema RED:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_gate_result_schema_distinguishes_verified_and_synthesized_checks -v`
exited `1` in `1.222s` with 11 expected failures: ten external/native null
identity mutations and one synthesized PASS-with-null record validated.
The same command then exited `0`; 1 test passed in `1.313s`.

Exact accepted-byte RED:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_gate_uses_single_read_leaf_identity_after_replacement -v`
exited `1` in `0.888s`; the gate returned replacement `FAIL / 1` rather than
accepted first-read `PASS / 0`.

Focused GREEN:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_gate_uses_single_read_leaf_identity_after_replacement scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_leaf_evidence_is_opened_once_and_verified_from_the_same_bytes -v`
exited `0`; 2 tests passed in `1.578s`. The broader eight-test schema, identity,
evidence, and forged-native focus also exited `0`; 8 passed in `6.559s`.

Final surrounding command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
exited `0`; 111 tests passed in `46.782s` (23 Phase 2C, 88 Phase 3A).
Phase 1B-3 command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -q`
exited `0`; 17 tests passed in `24.959s`.

- `git diff --check` and staged `git diff --cached --check` exited `0`; only
  line-ending warnings were emitted. `.ai-runs` and recursive `__pycache__`
  remained absent.
- Review-fix implementation/tests/schema/docs commit: `138d39a`
  (`fix(ai): bind phase 2 verified identities`). This evidence append is
  committed separately.
- Summary, index, reviewer log, Task 6 cache, exact skill/handoff sets, product,
  infrastructure, and GitHub Issue state were not changed. Gradle,
  build/product tests, server, Docker, HTTP/API, database, migration, seed,
  deploy, infrastructure, real `.ai-runs`, push, PR, merge, and GitHub Issue
  commands were NOT RUN. No registry state promotion, phase-state claim, Issue
  closure, native/CI enforcement, or unqualified overall completion claim is
  made.

### Task 5 Re-Review Fix - Synthesized Mapped Result (2026-07-14)

- Re-review found that the all-null synthesized check branch constrained
  `rawResult` but still allowed mapped-only PASS or FAIL.
- Added mapped-only mutations that preserve raw `NOT_CONFIGURED` and require
  schema rejection for both PASS and FAIL.
- Added the matching synthesized `mappedResult` enum for `BLOCKED`,
  `NOT_CONFIGURED`, `NOT_APPLICABLE`, and `SKIPPED_WITH_REASON`. Verified
  external/native record behavior and exact accepted-byte identity remain
  unchanged.
- Updated `ai/verification-gates.md` to state that synthesized records cannot
  claim raw or mapped PASS/FAIL.

Exact RED command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests.test_gate_result_schema_distinguishes_verified_and_synthesized_checks -v`
exited `1`; 1 test ran in `1.351s` with exactly two expected mapped-only
subtest failures. Focused GREEN used the same command and exited `0`; 1 test
passed in `1.497s`.

Final covering command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
exited `0`; 111 tests passed in `45.295s` (23 Phase 2C, 88 Phase 3A).
`git diff --check` and staged `git diff --cached --check` exited `0`; only
line-ending warnings were emitted.

- Implementation/schema/tests/docs commit: `c35aa24`
  (`fix(ai): reject synthesized pass mappings`). This evidence append is
  committed separately.
- Implementation-agent metadata remains accurate and unchanged: skill IDs are
  `verification-runner`, `failure-triage`, and `docs-sync`; reusable context
  includes `ai/native-runtime-adapters.json`. `review-gate` belongs to the
  reviewer handoff rather than this role.
- Summary, index, reviewer log, Task 6 cache, skill/reusable-context metadata,
  product, infrastructure, and GitHub Issue state were not edited. Prohibited
  commands and real `.ai-runs` remained NOT RUN; no phase-state or closure
  claim is made.

## Task 6 Update - Phase 2 Task 3 (2026-07-14)

### Routing And Handoff

- `tracking_status: issue_backed`; Issue #14:
  `https://github.com/116Lv/sparta-ch6-advanced/issues/14`.
- `owning_feature: none`; this is repo-wide Phase 2 cache and skill/handoff
  integrity work routed through `AGENTS.md`, `ai/document-routing.md`, the
  Phase 2A cache policies, Phase 2B catalog/handoff contracts, and the exact
  Task 6 brief.
- Implementation `skill_ids`: `verification-runner`, `failure-triage`, and
  `docs-sync`; `handoff_state_ref`: `ai/agent-handoff.json`; reusable context:
  `ai/workflow-cache.json`, `ai/verification-policy.json`, and
  `ai/native-runtime-adapters.json`; `github_reconciliation_status` is
  `issue_backed`.

### Changed Files And Decisions

- `scripts/ai/workflow_helper.py`: added complete cache-entry identity,
  fail-closed verification-decision invalidation, exact catalog semantics, and
  exact handoff-to-catalog validation during repo intake.
- `scripts/ai/tests/test_workflow_helper.py`: added schema, cache-staleness,
  duplicate-skill, and missing-distinct-handoff-skill regressions.
- `ai/schemas/workflow-cache.schema.json`: added the distinct closed
  `VERIFICATION_DECISION` key branch while retaining path keys for legacy and
  handoff cache entries.
- `ai/schemas/skill-catalog.schema.json` and
  `ai/schemas/agent-handoff.schema.json`: added `uniqueItems` defense in depth.
- `ai/workflow-cache.json`: documented the complete identity contract without
  materializing a self-referential or short-lived cached PASS decision.
- `ai/cache-policy.md`, `ai/skills/README.md`, and `ai/agent-handoff.md`:
  documented stale/uncertain mapping and exact-set semantics.
- Verification-decision identity covers task key, gate invocation ID, commit,
  change type, entry point, verification-policy digest, sorted exact producer
  IDs, sorted evidence path/digest pairs, environment fingerprint, and expiry.
  Current commit and policy are derived internally. Producers are the exact
  required/optional policy checks whose canonical entry point matches the
  selected change type and entry point; `documentation-only` plus `review`
  therefore yields only `review-gate`.
- Missing or unmapped task/gate/classification/policy/commit/environment state
  is `UNCERTAIN`; commit, policy, producer, evidence mismatch or expiry is
  `STALE`. Task/gate values remain required cache identity but repo intake does
  not falsely claim external authority for them. A non-null environment
  fingerprint remains `UNCERTAIN` until an authoritative current mapping exists.

### Exact TDD And Verification Evidence

- Exact RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests -v`
- Exact RED result: expected exit `1`; 17 tests ran in `5.538s`, with 12
  assertion failures and 5 missing-interface/schema errors. The baseline
  reported every policy/commit/task/gate/producer/change/entry/environment/
  expiry/evidence mutation as `FRESH`, accepted both malformed skill sets, and
  lacked all three required interfaces.
- Focused GREEN command: the same Phase 2A/2B command after the minimum
  implementation.
- Focused GREEN result: exit `0`; 17 tests passed in `6.007s`.
- Required surrounding command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
- Surrounding result: exit `0`; 128 tests passed in `52.476s`. No leaf,
  aggregation, forged-native precedence, or Phase 3A compatibility adjustment
  was needed.
- Phase 1B-3 integrity command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`
- Phase 1B-3 result: exit `0`; 17 tests passed in `23.777s`.
- `git diff --check` and staged `git diff --cached --check` exited `0`; only
  line-ending conversion warnings were emitted. Repository `.ai-runs` and
  recursive `__pycache__` remained absent.

### Commit And Recovery State

- Implementation/schema/tests/docs commit: `6a3a9dc`
  (`fix(ai): bind phase 2 cache and handoff state`).
- The current intentional boundary is that repo intake cannot authenticate an
  external task/gate assertion or non-null environment fingerprint; those
  inputs remain identity-only or `UNCERTAIN`, never reusable authority.
- This dated evidence append is committed separately. Independent review and
  orchestration remain with the parent; no summary, index, reviewer log, or
  GitHub Issue state was changed.
- Gradle, build/product tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, infrastructure, real `.ai-runs`, push, PR, merge, and GitHub
  Issue mutation/closure were NOT RUN. No registry `VERIFIED`, phase-state,
  native/CI enforcement, closure, or unqualified overall completion claim is
  made.

### Task 6 Review Fix - Policy Single-Read And Stale Precedence (2026-07-14)

- Independent review found two Important defects and one directly related Minor
  schema defect: verification policy validation and hashing used separate file
  opens; early `UNCERTAIN` returns masked later deterministic `STALE` findings;
  and the workflow-cache SHA-256 pattern accepted a terminal newline.
- `scripts/ai/workflow_helper.py` now reads canonical verification policy once
  into bounded immutable bytes, strict-parses and schema-validates that object,
  hashes the same bytes, and derives producer mappings from the same object.
  Cache findings accumulate across every safely checkable input. Any proven
  commit/policy/producer/evidence mismatch or expiry yields `STALE`; otherwise
  missing/unmapped task, classification, environment, path, or current input is
  `UNCERTAIN`. Unsafe or unavailable evidence paths are recorded without a
  digest open, while independent safe evidence and expiry checks continue.
- `ai/schemas/workflow-cache.schema.json` now uses the portable exact-end guard
  for SHA-256. `scripts/ai/tests/test_workflow_helper.py` covers the policy
  replacement race, compound precedence, the purely unmapped control, and the
  terminal-newline mutation. Exact skill and handoff sets and the no-canonical-
  fake-decision boundary are unchanged.

Exact review-fix RED command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests.test_verification_decision_cache_schema_requires_complete_identity scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests.test_verification_cache_stale_findings_precede_compound_uncertainty scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests.test_verification_cache_policy_is_parsed_hashed_and_mapped_from_one_read -v`
exited `1`; 3 tests ran in `1.522s` with 5 intended failures: policy was
opened twice, all three compound cases returned `UNCERTAIN`, and the newline
digest validated.

Focused GREEN used the same command and exited `0`; 3 tests passed in `1.520s`.
Phase 2A/2B focus exited `0`; 19 tests passed in `7.380s`. The required Phase
2A/2B/2C/3A command exited `0`; 130 tests passed in `52.915s`. The separate
`Phase1B3DoneClaimGateTests -v` command exited `0`; 17 tests passed in
`23.422s`. `git diff --check` and staged `git diff --cached --check` exited `0`
with only line-ending warnings; `.ai-runs` and recursive `__pycache__` remained
absent.

- Review-fix implementation/schema/tests commit: `cf77ce1`
  (`fix(ai): close phase 2 cache review gaps`). This evidence append is
  committed separately.
- Summary, index, reviewer log, canonical fake decision state, product,
  infrastructure, and GitHub Issue state were not edited. Prohibited commands
  and claims remain NOT RUN/not made as recorded above; independent rereview
  remains with the parent.

### Task 6 Final Review Fix - Evidence Read-Time Faults (2026-07-14)

- Final review found that evidence resolve and regular-file checks were guarded,
  but `digest(path)` ran after the guard. Disappearance, permission, or read
  failure after `is_file()` could therefore escape instead of producing
  conservative cache classification.
- The accepted evidence content is now opened/read/hashed once inside the
  guarded block. Unsafe paths remain lexically rejected before open. Any
  open/read `OSError` records unavailable evidence, skips that digest, and
  continues through remaining evidence and expiry. With no safe stale fact the
  result is `UNCERTAIN`; a safely proven later digest mismatch or expiry yields
  `STALE` while retaining both stale and unavailable diagnostics.
- The focused regression simulates `FileNotFoundError` at open and `OSError`
  during read after a successful `is_file()`, asserts the second evidence is
  still opened in all four subcases, and covers both standalone `UNCERTAIN` and
  compound `STALE` outcomes.

Exact RED command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests.test_verification_cache_evidence_read_faults_continue_to_safe_stale_checks -v`
exited `1`; 1 test ran in `0.771s` with 4 intended errors because both open-
time disappearance and read-time `OSError` escaped in plain and compound cases.
After guarding the digest, the same command exposed 2 intended diagnostic-
retention failures: statuses were correct but compound `STALE` reasons omitted
the unavailable evidence finding. The final focused GREEN exited `0`; 1 test
with 4 subcases passed in `0.782s`.

Phase 2A/2B focus exited `0`; 20 tests passed in `8.122s`. The required Phase
2A/2B/2C/3A command exited `0`; 131 tests passed in `50.038s`. `git diff
--check` and staged `git diff --cached --check` exited `0` with only line-ending
warnings; `.ai-runs` and recursive `__pycache__` remained absent.

- Implementation/tests commit: `5b2994c` (`fix(ai): guard cache evidence reads`).
  This evidence append is committed separately.
- Exact-set semantics, policy single-read binding, no-canonical-fake-decision
  state, summary, index, reviewer log, product/infrastructure scope, and GitHub
  state remain unchanged. Independent rereview remains with the parent.

## Task 7 Update - Phase 3A Task 1 (2026-07-14)

### Routing And Handoff

- `tracking_status: issue_backed`; GitHub Issue #14.
- `owning_feature: none`; this is repository-wide Phase 3A trust-authority
  separation routed through `AGENTS.md`, `ai/document-routing.md`, the exact
  Task 7 brief, and the existing Phase 2C/3A contracts.
- Implementation `skill_ids`: `verification-runner`, `failure-triage`, and
  `docs-sync`; `handoff_state_ref`: `ai/agent-handoff.json`; reusable context:
  `ai/workflow-cache.json`, `ai/verification-policy.json`, and
  `ai/native-runtime-adapters.json`; `github_reconciliation_status` remains
  `issue_backed`.

### Authority Split And Files

- Added `ai/schemas/host-native-trust.schema.json` and the frozen
  `HostNativeTrust` value plus `load_host_native_trust(...)`.
- Host descriptor, authoritative probe, and ledger paths must resolve outside
  the repository and cannot be symlinks. Closed compiled checks repeat host and
  producer identifiers, strict SemVer/range, lowercase SHA-256 fingerprint,
  exact four-surface set, authoritative `PROBED` provenance/timestamp, and
  descriptor/probe identity matching even when a copied schema is weakened.
- `ai/schemas/native-runtime-adapters.schema.json` now constrains
  `supportedHosts` to empty. Python semantic validation independently rejects
  non-empty repository policy and preserves exactly four current-host
  `UNSUPPORTED` surfaces.
- `native_adapter_gate(...)` accepts explicit internal host trust. Public
  `native-adapter-gate` no longer accepts descriptor, probe, ledger, policy,
  runtime-snapshot, or bypass-attempt fixture inputs and always evaluates with
  `host_trust=None`.
- Signed producer/key/signature, freshness, challenge/callback/host mismatch,
  replay, bypass event-set, and resolution-binding negative tests remain
  active; supported lower-level tests now use external host context.

### Exact TDD And Verification Evidence

- Exact RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_repository_supported_host_and_temporary_key_cannot_promote_public_cli scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_repository_probed_host_fixture_remains_host_unsupported scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_external_host_context_can_verify_signed_snapshot_in_lower_level_evaluator -v`
- RED result: exit `1`; 3 tests ran in `0.817s`. The public CLI returned a real
  signed `PASS / 0` from repository-controlled supported-host/key material;
  the external loader was absent; the repository-only `PROBED` control already
  returned `UNSUPPORTED / HOST_UNSUPPORTED / 6`.
- Initial GREEN: the same three tests exited `0`; 3 passed in `0.776s`.
- Compiled contract/path/public-boundary focus exited `0`; 4 tests passed in
  `2.556s`.
- Final surrounding command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
- Final surrounding result: exit `0`; 118 tests passed in `48.903s` (23 Phase
  2C and 95 Phase 3A).
- Direct canonical gate exited `6` with `UNSUPPORTED`, `HOST_UNSUPPORTED`,
  null/`UNPROBED` host version, four `UNSUPPORTED` surfaces, and repository-only
  qualification. `git diff --check` exited `0` with line-ending warnings only;
  recursive `__pycache__` and repository `.ai-runs` were absent.

### Commit And Remaining Boundaries

- Implementation/schema/tests commit: `841987e`
  (`fix(ai): move native trust outside repository`). This role-log append is
  committed separately; the detailed ignored report is
  `.superpowers/sdd/task-7-phase3a-report.md`.
- `ledger_root` is validated and carried but durable replay remains Task 8;
  later resolution binding remains Task 9. Existing in-memory replay and
  resolution tests were not weakened.
- Gradle, build/product tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, infrastructure, real `.ai-runs`, push, PR, merge, and GitHub
  Issue mutation were NOT RUN. No registry `VERIFIED`, phase-state, Issue
  closure, native/CI enforcement, or unqualified overall completion claim is
  made. Independent review remains with the parent.

### Task 7 Review Fix - Deep Host Trust Immutability (2026-07-14)

- Independent review found that `frozen=True` prevented dataclass field
  rebinding but retained caller-owned mutable descriptor/probe dictionaries and
  the nested surface list. The evaluator read those same aliases after
  validation.
- `HostNativeTrust.__post_init__` now recursively copies mappings into fresh
  read-only `MappingProxyType` values and lists/tuples into tuples. Direct
  construction and loader construction therefore expose no caller-mutable
  evaluator facts. Mapping access and surface iteration remain compatible with
  the existing evaluator; no mutable view is reconstructed.
- The regression attempts top-level descriptor fingerprint/producer/host,
  probe producer/host/version, and nested surface mutation; each raises. It
  then mutates every original constructor input alias and proves the immutable
  trust still retains the original facts and verifies the original signed
  snapshot.

Exact RED command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_host_native_trust_deep_freezes_values_and_detaches_input_aliases -v`
exited `1`; 1 test ran in `0.136s` with seven intended mutation failures.

Focused GREEN used the same command and exited `0`; 1 test passed in `0.231s`.
The final immutability/external-evaluator/public-boundary focus exited `0`; 3
tests passed in `2.180s`.

Final surrounding command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
exited `0`; 119 tests passed in `48.692s` (23 Phase 2C and 96 Phase 3A).
`git diff --check` exited `0` with line-ending warnings only; recursive
`__pycache__` and repository `.ai-runs` remained absent.

- Review-fix implementation/tests commit: `ed654a7`
  (`fix(ai): deep freeze host native trust`). This evidence append is committed
  separately.
- Public CLI arguments, external path validation, canonical unsupported state,
  summary, index, reviewer log, Task 8 replay scope, product/infrastructure
  state, and GitHub state were not changed. Prohibited commands and claims
  remain NOT RUN/not made. Independent rereview remains with the parent.

## Task 8 Update - Phase 3A Task 2 (2026-07-14)

### Routing And Handoff

- `tracking_status: issue_backed`; GitHub Issue #14.
- `owning_feature: none`; this is repo-wide Phase 3A native trust replay
  hardening routed through `AGENTS.md`, `ai/document-routing.md`, the approved
  trust-boundary design and Phase 3A plan, and the exact Task 8 brief.
- Implementation `skill_ids`: `verification-runner`, `failure-triage`, and
  `docs-sync`; `handoff_state_ref`: `ai/agent-handoff.json`; reusable context:
  `ai/workflow-cache.json`, `ai/verification-policy.json`, and
  `ai/native-runtime-adapters.json`; GitHub reconciliation remains
  `issue_backed`.

### Changed Files And Decisions

- `scripts/ai/workflow_helper.py`: added strict external ledger destination
  validation, canonical attestation identity, atomic `O_CREAT | O_EXCL` 0600
  consumption, file durability, partial-record cleanup, replay mapping, and
  the durable-before-memory call from the signed snapshot trust chain.
- `scripts/ai/tests/test_workflow_helper.py`: added two-fresh-process replay,
  create/fsync failure, stale/future no-consumption, record identity/mode, and
  post-load ledger symlink-swap coverage.
- The durable record binds SHA-256 repository-path identity, producer, task,
  gate/challenge, the signed snapshot `$id`, the gate challenge as nonce, and
  the signed bypass event-set SHA-256. Its filename is the SHA-256 of the
  compact sorted canonical record.
- The external ledger is re-resolved against the repository immediately before
  consumption. Symlinked roots/components, repository-contained roots,
  non-directories, unsafe record names, non-regular records, and POSIX roots or
  records with broader-than-owner permissions fail closed.
- Signature, task/gate, host/version, freshness, key, callback, event-set, and
  resolution checks retain their existing order and mapping. Durable
  consumption occurs only after callback verification; the process-local set
  is updated only after durable consumption and remains defense in depth.
- Public CLI arguments and host trust injection remain unchanged and
  unsupported; no repository ledger or `.ai-runs` state is written.

### Exact TDD And Verification Evidence

- RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_signed_attestation_replay_is_blocked_across_processes scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_ledger_creation_and_durability_faults_fail_closed_without_records scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_stale_and_future_attestations_never_touch_durable_ledger scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_ledger_root_symlink_swap_is_blocked_without_repository_write -v`
- RED result: expected exit `1`; 4 tests ran in `1.612s`, with 3 intended
  failures and 1 Windows directory-symlink capability skip. A second fresh
  interpreter returned `PASS`, and injected ledger create and fsync faults both
  returned `PASS`. The stale/future control was already blocked without ledger
  writes.
- Focused GREEN command: the same four-test command after implementation.
- Focused GREEN result: exit `0`; 4 tests ran in `1.625s`, with the same single
  Windows directory-symlink capability skip. Cross-process reuse was
  `BLOCKED / NATIVE_ADAPTER_CHALLENGE_REPLAYED`; create and fsync faults were
  fail-closed `BLOCKED / NATIVE_ADAPTER_EVALUATION_INVALID`; stale/future
  attestations left no record.
- Phase 3A command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
- Phase 3A result: exit `0`; 100 tests passed in `29.424s`, with 1 Windows
  directory-symlink capability skip.
- Required surrounding command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
- Surrounding result: exit `0`; 123 tests passed in `50.170s`, with the same
  single capability skip.
- A compatibility spot-check initially named a nonexistent test method and
  produced one loader `AttributeError`; failure triage identified the selector
  typo, corrected it to
  `test_signed_snapshot_binds_task_and_complete_bypass_event_set`, and the
  corrected three-test check passed in `1.004s`.
- `git diff --check` exited `0`; only line-ending conversion warnings were
  emitted. Repository `.ai-runs` and recursive `__pycache__` remained absent.

### Atomicity, Faults, Commit, And Recovery State

- The record itself is the lock: exactly one contender can create the
  deterministic path with `O_EXCL`; later contenders map `FileExistsError` to
  replay without opening or rewriting the accepted record.
- The winner verifies a regular owner-only record, writes canonical bytes,
  flushes, and `fsync`s before trusted surfaces can return. Any open, write,
  flush, metadata, or fsync fault propagates to the gate's fail-closed mapping.
  A partial record is removed after the descriptor is closed; cleanup failure
  also remains blocking and leaves no PASS path.
- Implementation/tests commit: `5d1e1f7`
  (`fix(ai): persist native attestation replay state`). This role-log append is
  committed separately; the detailed ignored report is
  `.superpowers/sdd/task-8-phase3a-report.md`.
- The directory-symlink swap regression could not execute on this Windows host
  because symlink creation was unavailable. The runtime path revalidation is
  implemented and the test remains executable on a capable host. Real host
  ledger ownership/ACL configuration was not exercised; only temporary
  external test ledgers were used.
- Task 9 retains original detection-resolution binding. Summary, index,
  reviewer log, product/infrastructure files, and GitHub Issue state were not
  changed. Gradle, build/product tests, server, Docker, HTTP/API, database,
  migration, seed, deploy, infrastructure, real `.ai-runs`, push, PR, merge,
  and GitHub Issue mutation were NOT RUN. No registry `VERIFIED`, phase-state,
  Issue closure, native/CI enforcement, or unqualified completion claim is
  made. Independent review remains with the parent.

### Task 8 Review Fix - Pinned Directory Durability (2026-07-14)

- Independent review found two Important defects in `5d1e1f7`: file fsync did
  not durably publish the parent directory entry, and validation returned a
  pathname that was traversed again during record creation. `O_NOFOLLOW` on the
  final record did not protect swappable ancestor components.
- Platform inspection showed CPython 3.9.6 on this Windows host has an empty
  `os.supports_dir_fd`; `os.open` and `os.unlink` have no `dir_fd`, while
  `O_DIRECTORY` and `O_NOFOLLOW` are absent. Production therefore has no
  pathname fallback: a supported-host attestation is fail-closed
  `BLOCKED / NATIVE_ADAPTER_EVALUATION_INVALID` when safe handle-relative
  ledger primitives are unavailable. Canonical public unsupported-host behavior
  is unchanged and never reaches ledger consumption.
- On a supported POSIX backend, consumption now validates the owner-only 0700
  root, opens it with `O_DIRECTORY | O_NOFOLLOW`, and compares the pinned
  handle's directory type, device, inode, owner, and mode with the pre-open
  metadata. The digest filename is created only relative to that handle with
  `O_CREAT | O_EXCL | O_NOFOLLOW`; its handle must be a regular owner-only 0600
  file owned by the evaluator user.
- Publication now writes with progress checking, fsyncs and closes the record,
  fsyncs the pinned directory entry, and closes the directory before returning
  success. Partial cleanup closes the record, unlinks only relative to the
  pinned directory, and fsyncs the directory after removal. Any write, file
  fsync, file close, publication directory fsync, directory close, relative
  unlink, or cleanup directory fsync uncertainty remains blocking and never
  returns PASS.
- The process-local challenge set is still checked and updated only after the
  durable consumer returns. It remains defense in depth, not authority.
- Existing supported-host contract tests on this backend use a unittest-only
  consumption stub registered and restored through per-test `setUp` cleanup.
  Ledger-security tests explicitly stop the stub and invoke production through
  focused mocks for only the missing handle-relative OS primitives. The stub
  is not present in production, HostNativeTrust, the public CLI, or any
  repository policy input.

Exact review-fix RED command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_safe_ledger_backend_is_required_for_supported_host_pass scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_safe_ledger_pins_directory_and_fsyncs_published_entry scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_simultaneous_safe_ledger_contenders_yield_one_pass_and_one_replay scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_safe_ledger_publication_and_cleanup_faults_never_return_success scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_safe_ledger_rejects_validation_to_open_directory_swap -v`
exited `1`; 5 tests ran in `0.498s` with 11 intended failures including fault
subtests. The safe-backend guard was absent, record creation used a pathname,
simultaneous safe contenders could not yield one PASS/one replay, durability
and cleanup paths violated the handle-relative contract, and the directory
identity swap was not detected.

Focused GREEN used the same command and exited `0`; 5 tests passed in `0.624s`.
After adding the capable-host real swap branch, the final focused run exited
`0`; 5 tests passed in `0.628s`. The simultaneous gate test produced exactly
one PASS and one `NATIVE_ADAPTER_CHALLENGE_REPLAYED` BLOCKED result. The fault
matrix covered write, record fsync, record close, publication directory fsync,
directory close, relative cleanup unlink, and cleanup directory fsync.

- Phase 3A command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -q`
- Phase 3A result: exit `0`; 104 tests passed in `28.663s`, with 2 explicit
  Windows platform skips (real handle-relative cross-process execution and
  directory symlink creation).
- Pre-commit Phase 2C + Phase 3A result: exit `0`; 127 tests passed in
  `49.676s`, with the same 2 skips.
- Post-commit Phase 2C + Phase 3A result: exit `0`; 127 tests passed in
  `49.690s`, with the same 2 skips.
- `git diff --check` exited `0` with line-ending warnings only; repository
  `.ai-runs` and recursive `__pycache__` remained absent.
- Review-fix implementation/tests commit: `9089b17`
  (`fix(ai): pin native replay ledger directory`). This evidence append is
  committed separately and the ignored Task 8 report carries the same review
  evidence.
- No summary, index, reviewer log, Task 9, product/infrastructure, public CLI,
  canonical host state, or GitHub state was changed. Prohibited commands and
  claims remain NOT RUN/not made. Independent rereview remains with the parent.

## Task 9 Update - Phase 3A Task 3 (2026-07-14)

### Routing And Handoff

- `tracking_status: issue_backed`; GitHub Issue #14.
- `owning_feature: none`; this is repo-wide Phase 3A bypass-resolution trust
  hardening routed through `AGENTS.md`, `ai/document-routing.md`, the approved
  trust-boundary design and Phase 3A plan, and the exact Task 9 brief.
- Implementation `skill_ids`: `verification-runner`, `failure-triage`, and
  `docs-sync`; `handoff_state_ref`: `ai/agent-handoff.json`; reusable context:
  `ai/workflow-cache.json`, `ai/verification-policy.json`, and
  `ai/native-runtime-adapters.json`; GitHub reconciliation remains
  `issue_backed`.

### Changed Files And Decisions

- `ai/schemas/native-bypass-attempt.schema.json`: requires null detection
  binding fields on `DETECTED` and non-null identifier/digest fields on
  `RESOLVED`.
- `scripts/ai/workflow_helper.py`: adds `native_detection_digest()` and exact
  prior-detection event/task/original-gate/deduplication/digest/time matching.
  Unmatched detections remain unresolved; mismatched resolutions are invalid
  before signed current-resolution ID comparison.
- `scripts/ai/tests/test_workflow_helper.py`: adds schema closure and direct plus
  gate-level unrelated event/task/original-gate/digest regressions, updates
  valid resolution fixtures with exact original-detection bindings, and
  preserves event-set mismatch ordering.
- `ai/native-runtime-adapters.md`, `ai/verification-gates.md`, and the Phase 3A
  design now state external immutable `HostNativeTrust`, the public unsupported
  boundary, safe external durable replay consumption, and original detection
  binding without claiming current enforcement.
- Current-gate detections still win as unresolved. A valid resolution cannot
  clear any other detection that merely shares its deduplication key.
- External host trust, pinned durable ledger behavior, signature/callback/event
  set trust, exact signed `resolutionEventIds`, reusable handoff/context refs,
  canonical unsupported state, and Phase 3B boundaries remain unchanged.

### Exact TDD And Verification Evidence

- RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_resolution_must_bind_the_exact_original_detection scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_unrelated_resolution_event_cannot_clear_detection_at_gate -v`
- RED result: expected exit `1`; the four wrong event/task/original-gate/digest
  subcases each returned `RESOLVED_TRANSITION`, and the gate case returned
  `FAIL / NATIVE_BYPASS_CONTRACT_INVALID / 1` instead of the precise blocked
  resolution-invalid result.
- Initial focused GREEN: the same pre-rename two-test command exited `0`; 2
  tests passed in `0.275s`.
- First surrounding Phase 3A run exposed three fixture migrations. Failure
  triage preserved validation ordering: a schema-only resolution received
  non-null bindings, the later-unresolved resolution received its true digest,
  and the event-set tamper recomputed its resolution digest so it could continue
  testing the later signed event-set mismatch. The targeted three-test rerun
  passed in `0.869s`.
- Final focused command (schema plus direct and gate-level all-four mismatch
  cases): exit `0`; 3 tests passed in `1.209s`.
- Final Phase 3A command: exit `0`; 107 tests passed in `30.844s`, with 2
  explicit Windows capability skips.
- Final Phase 2C + Phase 3A command: exit `0`; 130 tests passed in `52.600s`,
  with the same 2 skips.
- The brief's `scripts/ai/tests/native-adapter-gate.sh` path is absent. Syntax
  verification of the tracked `scripts/ai/native-adapter-gate.sh` exited `0`.
- The public gate returned captured exit `6` with
  `UNSUPPORTED / HOST_UNSUPPORTED`, null/`UNPROBED` host version, four
  unsupported surfaces, and repository-only qualification.
- `git diff --check` and staged diff check exited `0` with only line-ending
  warnings. Repository `.ai-runs` and recursive `__pycache__` remained absent.

### Commit, Concerns, And Recovery State

- Implementation/schema/tests/docs commit: `920fe21`
  (`fix(ai): bind native bypass resolutions`). This Task 9 evidence append is
  committed separately; the detailed ignored report is
  `.superpowers/sdd/task-9-phase3a-report.md`.
- The shell-path mismatch in the brief was not repaired by creating a duplicate;
  the tracked wrapper remains unchanged and syntax-valid.
- Two pre-existing platform skips remain: real handle-relative cross-process
  ledger execution and directory-symlink creation are unavailable here. No real
  supported host, authoritative external trust, or production ledger was used.
- No Phase 3B, product/infrastructure, GitHub, handoff, reusable-context,
  canonical policy, or shell-wrapper file changed. Gradle, build/product tests,
  server, Docker, HTTP/API, database, migration, seed, deploy, infrastructure,
  real `.ai-runs`, push, PR, merge, and GitHub Issue mutation were NOT RUN. No
  registry `VERIFIED`, phase-state, Issue closure, native/CI enforcement, or
  unqualified completion claim is made. Independent review remains with the
  parent.

### Task 9 Review Fix - Deterministic Resolution Precedence (2026-07-14)

- Independent review found insertion-order dependence across deduplication
  groups: an invalid resolution in the first group returned
  `NATIVE_BYPASS_RESOLUTION_INVALID` before a later current-gate detection could
  establish the required `NATIVE_BYPASS_UNRESOLVED` precedence. Reordering the
  same event set changed the result.
- `native_bypass_lifecycle_state(...)` now pre-scans the complete validated,
  event-ID-deduplicated attempt collection for any current-gate `DETECTED`
  event. That fact returns `UNRESOLVED` before per-group resolution validation,
  independent of group or delivery order.
- When no current-gate detection exists, an unrelated resolution still returns
  `NATIVE_BYPASS_RESOLUTION_INVALID`. Exact event/task/original-gate/dedupe/
  digest/time binding, unmatched later-detection blocking, signed current
  `resolutionEventIds` comparison, and event delivery conflict/idempotency
  checks remain unchanged.

Exact review-fix RED command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_current_gate_detection_precedes_cross_group_invalid_resolution_in_all_orders -v`
exited `1`; the `invalid-first` permutation returned resolution-invalid while
the same events in `current-first` order returned unresolved. The invalid-only
control remained resolution-invalid.

The same focused command exited `0`; 1 test passed in `0.538s`. The final
precedence/binding focus exited `0`; 4 tests passed in `1.649s`.

- Phase 3A: exit `0`; 108 tests passed in `31.400s`, with 2 existing Windows
  capability skips.
- Phase 2C + Phase 3A: exit `0`; 131 tests passed in `53.341s`, with the same
  skips.
- Tracked shell syntax, unstaged/staged diff checks: exit `0`; only line-ending
  warnings. Repository `.ai-runs` and recursive `__pycache__` remained absent.
- Review-fix implementation/tests commit: `de7b89f`
  (`fix(ai): stabilize bypass resolution precedence`). This evidence append is
  committed separately and the ignored Task 9 report carries the same evidence.
- No summary, index, reviewer, Phase 3B, product/infrastructure, GitHub, public
  wrapper, canonical policy, handoff, or reusable-context file changed. No
  prohibited command, enforcement claim, Issue closure, or unqualified
  completion claim was made. Independent rereview remains with the parent.

## Task 10 Update - Phase 3B Task 1 (2026-07-14)

### Routing And Handoff

- `tracking_status: issue_backed`; GitHub Issue #14.
- `owning_feature: none`; this is repo-wide Phase 3B repository-contract and
  native-enforcement status separation routed through `AGENTS.md`,
  `ai/document-routing.md`, the approved trust-boundary design, the Phase 3B
  provenance-hardening plan, and the exact Task 10 brief.
- Implementation `skill_ids`: `verification-runner`, `failure-triage`, and
  `docs-sync`; `handoff_state_ref`: `ai/agent-handoff.json`; reusable context:
  `ai/workflow-cache.json`, `ai/verification-policy.json`, and
  `ai/native-runtime-adapters.json`; GitHub reconciliation remains
  `issue_backed`.

### Changed Files And Decisions

- `.github/workflows/phase-3b-ci-gates.yml`: the workflow, job ID, and job name
  are now `phase-3b-repository-contract`. It runs only helper/static contract
  checks, captures two diagnostic text files with pipeline failure propagation,
  and uploads only those diagnostics. The CI evidence gate and its accepted
  exit-3 path were removed; no `phase-3b-native-enforcement` job is emitted.
- `ai/schemas/ci-capability-status.schema.json` and
  `ai/ci-capability-status.json`: replaced ambiguous `requiredCheck`,
  `workflowRefs`, and `nativeAdapterInstallation` canonical fields with closed
  `repositoryContract` and `nativeEnforcement` objects. Canonical native
  enforcement is `NOT_CONFIGURED`, `requiredCheckConfigured: false`, and
  `GITHUB_REQUIRED_CHECK_AND_NATIVE_ADAPTER_NOT_CONFIGURED`; durable evidence
  and remote runner remain completion-blocking.
- `ai/project-state.json` and `ai/project-state.md`: the CI environment is
  `CONFIGURED_UNVERIFIED` because the repository contract workflow exists,
  while the same canonical note says native enforcement remains
  `NOT_CONFIGURED`. LOCAL environment and helper-runtime claims are unchanged.
- `scripts/ai/tests/test_workflow_helper.py`: added/updated workflow, canonical
  status, project-state, diagnostic artifact, and required-check identity
  regressions.
- `scripts/ai/workflow_helper.py` and
  `ai/schemas/ci-gate-result.schema.json`: minimal compatibility updates derive
  the legacy gate-result projection from `nativeEnforcement`, name the required
  check `phase-3b-native-enforcement`, and keep canonical missing evidence as
  `NOT_CONFIGURED` / Phase 2C `BLOCKED` / exit `3`. These two files are necessary
  because removing `currentCi.requiredCheck` without updating the reader would
  raise `KeyError` and the old result schema would continue to name the green
  repository job as enforcement. No Task 11 GitHub provenance path was added.

### Exact TDD And Verification Evidence

- First RED attempt (sandboxed):
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v`
  exited `1`; 7 tests ran with 5 intended semantic failures and 2
  `PermissionError` errors because the externally located isolated worktree was
  read-only to that sandbox profile when tests created temporary status JSON.
- RED rerun with the worktree write permission available used the same command
  and exited `1`; 7 tests ran with 6 failures, 0 errors, and 1 pass. Failures
  precisely showed the old `phase-3b-ci-gates` required check, missing split
  objects, evidence-gate/exit-3 workflow path, missing diagnostics, and project
  state claiming no workflow exists.
- Initial GREEN used the same Phase 3B command and exited `0`; 7 tests passed in
  `0.554s`.
- Expanded preservation command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v`
  exited `0`; 138 tests passed in `54.873s`, with 2 pre-existing explicit
  Windows capability skips (directory symlink creation and the real
  handle-relative cross-process ledger backend).
- Final Phase 3B rerun after the explicit no-enforcement-job assertion exited
  `0`; 7 tests passed in `0.484s`.
- A static Python validation command loaded canonical CI status and project
  state through approved schemas, proved the Markdown summary equals
  `summary_for(...)`, validated the emitted CI gate result against
  `ci-gate-result.schema.json`, and asserted
  `NOT_CONFIGURED / BLOCKED / exit 3 / phase-3b-native-enforcement`; exit `0`
  with `schemas/summary/gate: PASS`.
- `git diff --check` and staged diff check exited `0`; only expected Git
  LF-to-CRLF warnings appeared before staging. Repository `.ai-runs` and
  recursive `__pycache__` remained absent.

### Commit, Concerns, And Recovery State

- Implementation/schema/tests/state commit: `a89e07e`
  (`fix(ai): separate ci contract and enforcement`). This Task 10 evidence
  append is committed separately; the detailed ignored report is
  `.superpowers/sdd/task-10-phase3b-report.md`.
- A green repository contract workflow is not enforcement success. The actual
  GitHub required check and native adapter remain externally unconfigured, and
  the repository contract remains `CONFIGURED_UNVERIFIED` because no Action was
  executed in this task.
- Task 11 still owns authenticated GitHub run/job/workflow/artifact provenance;
  Task 12 still owns the complete helper-suite contract entry point. No part of
  either later task was implemented here.
- Phase 3A remains `hostVersion: null` / `UNPROBED` / `UNSUPPORTED` with the
  repository-qualified Phase 2C `NOT_APPLICABLE` leaf. Phase 1B-3 remains
  `INTEGRITY_ONLY`; Phase 2 result mapping and handoff/skill references are
  unchanged.
- Gradle, build/product tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, infrastructure, real `.ai-runs`, GitHub Actions, push, PR,
  merge, branch-protection, and Issue mutation were NOT RUN. No registry
  `VERIFIED`, native/CI enforcement, Issue closure, or unqualified completion
  claim is made. Independent review remains with the parent.

### Task 10 Review Fix - Explicit Result Identity Split (2026-07-14)

- Independent review found two Important issues. First, the CI result called
  `phase-3b-native-enforcement` the `requiredCheck` while putting the green
  repository-contract workflow path in `workflowRefs`, and both shell fallback
  envelopes retained the old `phase-3b-ci-gates` identity. Second,
  `ai/ci-gates.md` still claimed that old required check was configured.
- `ai/schemas/ci-gate-result.schema.json` and `scripts/ai/workflow_helper.py`
  now expose closed `repositoryContract` and `nativeEnforcement` objects
  directly. The legacy `requiredCheck`, `workflowRefs`, and
  `nativeAdapterInstallation` result fields were removed, so no consumer can
  associate the green contract workflow path with native enforcement.
- `scripts/ai/ci-evidence-gate.sh` now emits the same schema-valid split in both
  invalid-argument and helper-runtime-unavailable fallbacks. Required durable
  evidence bindings and cache retention are complete in both envelopes.
- `ai/ci-gates.md` now states exactly that `phase-3b-repository-contract` is
  `CONFIGURED_UNVERIFIED` and `phase-3b-native-enforcement` is
  `NOT_CONFIGURED` with `requiredCheckConfigured: false`; it no longer claims
  any configured GitHub required enforcement check.
- `scripts/ai/tests/test_workflow_helper.py` adds exact result, shell fallback,
  document, schema, and invalid-correlation regressions.

Exact review RED command:
`$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests.test_ci_gate_is_fail_closed_without_durable_github_actions_evidence scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests.test_ci_gate_shell_fallbacks_preserve_split_identity scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests.test_ci_policy_document_reports_exact_split_status -v`
exited `1`; 3 tests produced 4 intended assertion failures: one helper result,
two shell fallback subtests, and one policy-document assertion. The same command
then exited `0`; 3 tests passed in `0.251s`.

- A subsequent explicit schema-validation probe correctly exposed that the
  helper's invalid-argument fallback still copied a space-containing raw
  `taskKey`, causing the result schema identifier pattern to fail. This was not
  hidden as a verification artifact.
- Additional RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests.test_ci_gate_invalid_arguments_emit_schema_valid_split_fallback -v`
  exited `1`; 1 test failed because `taskKey` was `bad argument` instead of the
  schema-safe `invalid` placeholder.
- The helper now validates task/gate correlation independently before building
  fallback data and substitutes `invalid` only for the malformed member. Final
  focused review command ran the four review regressions and exited `0`; 4 tests
  passed in `0.281s`.
- Intermediate expanded Phase 2C + Phase 3A + Phase 3B verification exited `0`;
  140 tests passed in `56.669s` with 2 existing Windows capability skips.
- Final expanded verification after the correlation fix exited `0`; 141 tests
  passed in `56.723s` with the same 2 skips.
- `C:\Program Files\Git\bin\bash.exe -n scripts/ai/ci-evidence-gate.sh`
  exited `0`. Canonical and invalid helper results both validated against the
  result schema, exact legacy mixed-key search reported absent, `git diff
  --check` and staged diff check exited `0`, and repository `.ai-runs` plus
  recursive `__pycache__` remained absent.
- Review-fix implementation commit: `beb427a`
  (`fix(ai): separate ci gate result identities`). This evidence append is
  committed separately and the ignored Task 10 report is synchronized.
- Task 11 GitHub provenance and Task 12 complete contract-test entrypoint were
  not changed. Phase 3A remains `UNPROBED`/`UNSUPPORTED`, Phase 2 mapping and
  handoff/skill references remain unchanged, and no product/infrastructure or
  GitHub-state operation was run. Independent rereview remains with the parent.

### Task 10 Second Review Fix - Correlation Length Boundary (2026-07-14)

- Independent rereview found that `taskKey` and `gateInvocationId` used the
  identifier regex but did not enforce the CI gate result schema's exact
  `minLength: 1` / `maxLength: 128` contract. A 129-character identifier could
  therefore reach result construction even though the emitted document could
  not validate against `ai/schemas/ci-gate-result.schema.json`.
- `scripts/ai/workflow_helper.py` now applies one closed correlation predicate
  to both fields: string type, length 1 through 128 inclusive, and the existing
  identifier regex. Invalid values independently normalize to `invalid`, return
  `BLOCKED / INVALID_CI_GATE_ARGUMENTS / exit 2`, and never leak the oversized
  raw value into the result envelope.
- `scripts/ai/tests/test_workflow_helper.py` adds 128-valid and 129-invalid
  boundary coverage for both fields, validates every result against the schema,
  proves the raw oversized value is absent, and preserves the shell wrapper's
  exact separate argument forwarding.
- RED command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests.test_ci_gate_correlation_length_matches_result_schema_boundary -v`
  exited `1`; 1 test produced 2 intended failures because 129-character
  `taskKey` and `gateInvocationId` values both returned the baseline
  `NOT_CONFIGURED / CI_EVIDENCE_NOT_AVAILABLE / exit 3` result.
- Focused GREEN command covering the new boundary, invalid fallback, and shell
  forwarding exited `0`; 3 tests passed in `0.334s`. The full Phase 3B class
  then exited `0`; 11 tests passed in `0.920s`.
- Final Phase 2C + Phase 3A + Phase 3B expansion exited `0`; 142 tests passed in
  `55.398s` with the same 2 pre-existing Windows capability skips (directory
  symlink creation and the real handle-relative cross-process ledger backend).
- An independent schema boundary probe validated both 128-character results
  and both schema-safe 129-character rejection results. Shell syntax
  (`bash -n`), `git diff --check`, staged diff check, and the absence of
  repository `.ai-runs` and recursive `__pycache__` all passed.
- Review-fix implementation commit: `b646c22`
  (`fix(ai): enforce ci correlation length bounds`). This role-log evidence is
  committed separately and the ignored Task 10 report is synchronized.
- Task 11 provenance and Task 12 full contract entry point remain untouched.
  Phase 3A and Phase 2 mappings are unchanged, and no product, infrastructure,
  GitHub-state, or real run-state operation was performed.

### Task 11 - Authenticated GitHub Provenance (2026-07-14)

- Added the closed Draft 2020-12
  `ai/schemas/github-ci-provenance.schema.json` contract and allowlisted it in
  the helper. The envelope binds repository, workflow ref/SHA, head SHA, event,
  run ID/attempt, job ID, artifact ID/digest and member digests, task/gate,
  native evidence digest, bypass event-set digest, resolution IDs, signer, and
  verified attestation subject.
- Expanded the repository `retainedRun` schema to the same 16 binding claims.
  This object remains untrusted and is compared exactly with externally
  verified provenance; it cannot create authority on its own.
- Added frozen canonical-byte `GitHubCiProvenance`. The internal PASS path
  rejects raw dictionaries, while the public `ci-evidence-gate.sh`/CLI exposes
  no provenance option and therefore always calls with `None`, returning
  `NOT_CONFIGURED / CI_GITHUB_PROVENANCE_NOT_AVAILABLE / exit 3`.
- Artifact members use handle-relative `O_NOFOLLOW` reads on supporting POSIX
  hosts and a regular-file identity-revalidating fallback elsewhere. Traversal,
  symlink substitution, open identity races, missing files, digest tampering,
  wrong run identity, and unrelated-run evidence are rejected.
- `ai/schemas/ci-gate-result.schema.json` exposes verified GitHub identity and
  requires a non-null closed identity for every schema-valid PASS. Contract and
  native-enforcement identities remain separate.

RED evidence:

- Closed-schema test exited `1` because `github-ci-provenance` was absent.
- Repository-only retained state produced the prior generic BLOCKED result,
  and a fully matching raw dictionary produced PASS; both contradicted the new
  trust boundary.
- A PASS result with `githubProvenance: null` validated under the old result
  schema. Each regression failed for the intended missing-boundary reason
  before production changes.

GREEN and expanded evidence:

- Focused provenance matrix exited `0`; 5 tests passed in `1.740s`.
- Frozen-value/raw-dictionary boundary exited `0`; 2 tests passed in `0.327s`.
- Full Phase 3B class exited `0`; 18 tests passed in `2.803s` with one Windows
  symlink-capability skip before the frozen-value test was added.
- Final Phase 2C + Phase 3A + Phase 3B expansion exited `0`; 150 tests passed in
  `56.814s` with 3 platform-capability skips: existing directory-symlink and
  real handle-relative ledger skips plus the new file-symlink permission skip.
- Draft 2020-12 self-check for all three affected provenance/result/status
  schemas, `bash -n scripts/ai/ci-evidence-gate.sh`, and `git diff --check`
  exited `0`. `.ai-runs`, recursive `__pycache__`, and temporary
  `.phase3b-provenance-*` artifacts were absent.

Implementation commit: `7ea9308` (`fix(ai): bind ci evidence to github
provenance`). The ignored detailed report is
`.superpowers/sdd/task-11-phase3b-report.md`. Gradle, product/build tests,
server, Docker, HTTP/API, database, migration, seed, deploy, infrastructure,
GitHub Actions/state mutation, push, PR, merge, Issue closure, and real
`.ai-runs` were NOT RUN. External GitHub/Sigstore verification and required
native-enforcement check installation remain `NOT_CONFIGURED`; independent
review is the next role.

### Task 11 Review Fix - External Authority And Safe Member Reads (2026-07-14)

- Independent review found one Critical and two Important trust defects in the
  initial implementation. The exported `GitHubCiProvenance` constructor could
  be called by repository Python and therefore did not prove external origin;
  expected run identity was derived from untrusted `retainedRun`; and the
  non-POSIX pathname fallback did not provide a pinned production-safe member
  read.
- The constructible authority type and production PASS path were removed.
  `ci_evidence_gate` now returns
  `NOT_CONFIGURED / CI_GITHUB_PROVENANCE_NOT_AVAILABLE / exit 3` after valid
  status loading regardless of any injected Python value. No repository object,
  schema-valid boolean, or frozen wrapper can activate production PASS.
- The lower-level pure `verify_github_ci_provenance` seam does not publish a
  production result. It requires a separate immutable
  `GitHubTrustedRunContext` from a future external verifier. Provenance and
  `retainedRun` independently match repository, workflow ref/SHA, head/event,
  run/attempt/job, artifact/member, task/gate, native/bypass/resolution, and
  signer fields against that context. Changing both claims to the same older
  genuine run is rejected as `CI_GITHUB_PROVENANCE_MISMATCH`.
- Production artifact reads now require POSIX `dir_fd` plus `O_NOFOLLOW` and
  open every component relative to its pinned parent descriptor. The pathname
  fallback was deleted. Hosts without this backend fail closed with
  `CI_ARTIFACT_MEMBER_BACKEND_UNAVAILABLE`; Windows lower-level correlation
  tests use an explicit unit-test-only bytes consumer with no production-gate
  authority.
- `ai/ci-gates.md` now states that constructible/frozen repository values do
  not prove origin, the production gate is unconditionally NOT_CONFIGURED until
  real GitHub/Sigstore integration exists, both claims require independent
  current-context matching, and non-POSIX production member reads fail closed.

Review-fix RED and GREEN evidence:

- Focused RED exited `1`: a forged production object entered the old injection
  path and returned `BLOCKED / CI_GITHUB_PROVENANCE_INVALID` instead of the
  required unconditional NOT_CONFIGURED state; `GitHubTrustedRunContext`, the
  lower verifier, and safe-backend predicate were absent.
- Focused GREEN exited `0`; 6 authority/context/backend tests passed in
  `1.172s`.
- Full Phase 3B exited `0`; 22 tests passed in `3.272s` with one explicit safe
  POSIX member-backend platform skip.
- Final Phase 2C + Phase 3A + Phase 3B expansion exited `0`; 153 tests passed in
  `57.102s` with 3 platform skips (the two existing Phase 3A Windows safe-ledger
  skips plus the Phase 3B safe-POSIX member-backend skip).
- Draft 2020-12 self-check for the provenance/status/result schemas, shell
  syntax check for `scripts/ai/ci-evidence-gate.sh`, forbidden old authority/fallback symbol
  search, `git diff --check`, and staged diff check exited `0`. `.ai-runs`,
  recursive `__pycache__`, and `.phase3b-provenance-*` artifacts were absent.

Review-fix implementation commit: `d8834f9` (`fix(ai): close ci provenance
authority gap`). The ignored Task 11 report is synchronized. Task 12's contract
entry point remains untouched. No product, infrastructure, GitHub-state, push,
PR, merge, Issue closure, or real run-state operation was performed;
independent re-review remains with the parent.

## Task 12 - Complete Contract-Test Entry Point (2026-07-14)

### Routing And Scope

- `tracking_status: issue_backed`; GitHub Issue #14 remains open and workflow
  `status` remains `in_progress` pending independent review.
- `owning_feature: none`; this is repo-wide Phase 3B contract-test and workflow
  infrastructure routed through `AGENTS.md`, `ai/document-routing.md`, the
  approved Phase 3B hardening plan/design, and
  `.superpowers/sdd/task-12-phase3b-brief.md`.
- Implementation `skill_ids`: `verification-runner`, `failure-triage`, and
  `docs-sync`; `handoff_state_ref`: `ai/agent-handoff.json`; reusable context:
  `ai/workflow-cache.json`, `ai/verification-policy.json`, and
  `ai/native-runtime-adapters.json`.

### Implementation And Trust Boundary

- `scripts/ai/tests/run-contract-tests.sh` now resolves and enters the
  repository root, runs the full
  `python -m unittest scripts.ai.tests.test_workflow_helper -v` command exactly
  once, and then runs the runtime-preflight and command-runner shell contracts.
  `set -eu`, deterministic PATH, and command ordering preserve nonzero failure
  propagation.
- `.github/workflows/phase-3b-ci-gates.yml` provisions both pinned helper
  runtimes and calls only the complete contract entry point for regressions.
  The selective Phase 2C/3A/3B unittest command and duplicate helper diagnostic
  artifact were removed; `set -o pipefail` preserves failures through `tee`.
- The Phase 3B design now states that repository contract green does not imply
  native enforcement PASS, the external GitHub/Sigstore verifier and required
  native check remain `NOT_CONFIGURED`, and repository diagnostics cannot
  establish enforcement authority.
- Full-suite intake exposed three stale/cross-platform test assumptions. The
  exact schema allowlist now includes all 28 canonical schemas, stale-summary
  mutation derives the current canonical `updatedAt`, and the POSIX shell
  fixture strictly normalizes only checkout CRLF to LF while rejecting any
  other carriage return. These changes preserve closed-set and byte-exact
  assertions rather than weakening them.

### TDD And Failure Evidence

- Focused RED exited `1`: the new entry-point regression failed because
  `REPOSITORY_ROOT` and the full helper-module invocation were absent.
- Focused GREEN exited `0`; 1 test passed in `0.056s`.
- The first full-module attempt exited `1`: 416 tests ran in `191.293s`, with 4
  failures, 44 errors, and 20 skips. A second diagnostic reproduction ran the
  same 416 tests in `190.436s` with the same result. The four failures were the
  exact schema count, stale hard-coded project-state timestamp, case-sensitive
  design phrase, and Windows CRLF POSIX fixture. All 44 errors shared one root
  cause: default sandbox denial when Phase 3B fixtures created temporary
  provenance/artifact state in this externally located worktree.
- The four canonical/platform regressions then exited `0`; 4 tests passed in
  `1.542s`. An approved representative Phase 3B provenance fixture exited `0`,
  confirming the sandbox diagnosis.
- Long foreground approved full-module attempts exceeded the tool host's
  approximately 100-second lifetime, so no exit code was claimed from those
  interrupted attempts. Final exhaustive evidence was partitioned without
  omitting tests: the approved Phase 3B class exited `0` with 23 tests passed in
  `2.983s` and 1 platform skip; every other test class exited `0` with 393 tests
  passed in `187.353s` and 19 platform skips. Combined coverage is all 416
  helper tests with 20 explicit platform-capability skips.

### Static Verification, Commit, And Recovery

- `bash -n` passed for `run-contract-tests.sh`,
  `test-runtime-preflight.sh`, and `test-command-runner.sh`.
- Draft 2020-12 schema self-checks for CI capability, result, and GitHub
  provenance passed; canonical CI state remains repository contract
  `CONFIGURED_UNVERIFIED` and native enforcement `NOT_CONFIGURED` with
  `requiredCheckConfigured: false`.
- `git diff --check`, staged diff check, unsupported success-claim search, and
  absence checks for `.ai-runs`, recursive `__pycache__`, Phase 3B temporary
  provenance paths, and the underbound status fixture passed.
- Implementation commit: `5a57125` (`test(ai): run complete workflow
  contracts`). The ignored detailed report is
  `.superpowers/sdd/task-12-phase3b-report.md`.
- Gradle, product/build tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, infrastructure, GitHub Actions/state mutation, push, PR, merge,
  Issue closure, and real `.ai-runs` were NOT RUN. External verifier and native
  required-check installation remain `NOT_CONFIGURED`; independent review is
  the next role.

### Task 12 Review Fix - Semantic Execution Structure (2026-07-14)

- Independent review found that substring counts and index ordering could be
  satisfied by commented commands, dead branches, duplicates, or selective
  helper invocations. The test-only contract validators now remove blank and
  full-comment lines before evaluating executable structure.
- The shell validator requires one exact normalized top-level sequence:
  shebang, `set -eu`, deterministic PATH, script/root resolution, repository
  `cd`, the complete helper module once, and the two exact shell suites in
  order. Any additional statement or compound/dead branch is rejected.
- The workflow validator parses indentation into one exact repository-contract
  job, closed job metadata, and a six-step action model. Every install,
  dependency-probe, contract run, `pipefail`, diagnostic pipeline, upload
  condition, artifact path, missing-file policy, and retention field is bound;
  any other unittest or selective helper runner is rejected.
- Mutation coverage rejects commented, `if false` dead-branch, duplicate, and
  selective-runner forms independently for both the entry script and workflow
  (eight negative variants). Comments and blank lines remain allowed and are
  excluded from the executable model.
- Focused RED exited `1`; the mutation test failed because the semantic
  validator did not exist. Focused GREEN after implementation/refactor exited
  `0`; 3 tests passed in `0.146s`.
- `bash -n` for all three contract scripts, `git diff --check`, staged diff
  check, and `.ai-runs` / recursive `__pycache__` absence checks passed.
- Review-fix implementation commit: `9f064cb` (`test(ai): validate contract
  execution structure`). The ignored Task 12 report is synchronized. The prior
  exhaustive partition remains 416 helper tests covered with 20 explicit
  platform skips. An exact post-fix full-module execution is pending with the
  parent and is not claimed here.
- No workflow, production helper, schema, canonical state, product,
  infrastructure, GitHub state, push, PR, merge, Issue closure, or real
  `.ai-runs` operation changed or ran. Native enforcement and the external
  verifier remain `NOT_CONFIGURED`; independent re-review remains next.

### Task 12 Exact Post-Fix Contract Suite Evidence (2026-07-14)

- The parent copied the repository into a writable temporary verification
  directory and ran the exact entrypoint-owned helper command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper -v`.
- The first exact execution exited `1` after `193.501s`: 417 tests ran with 1
  failure and 20 platform skips. The temporary copy had excluded the linked
  worktree `.git` pointer, so repository commit identity failed closed with
  `VERIFICATION_REPOSITORY_COMMIT_NOT_CONFIGURED`. This was an environment
  construction failure; it is preserved as failed evidence and does not
  support a PASS claim.
- After restoring the same linked-worktree `.git` pointer in the writable copy,
  the identical exact command exited `0` after `191.541s`: all 417 tests passed
  with the same 20 explicit platform-capability skips.
- This exact successful rerun, together with the semantic GREEN and eight
  mutation regressions, closes the reviewer finding that commented, dead,
  duplicate, or selective helper paths could satisfy the prior test and closes
  the pending exact post-fix full-module evidence gap. The earlier exhaustive
  416-test partition remains historical pre-fix evidence and is not substituted
  for this 417-test exact rerun.
- The verification executed helper tests only. It did not run Gradle, product
  commands, servers, Docker, HTTP/API, databases, migrations, seeds, deploys,
  GitHub Actions/state mutation, push, PR, merge, Issue closure, or real
  `.ai-runs`. Native enforcement and the external verifier remain
  `NOT_CONFIGURED`; independent re-review remains next.

### Task 12 Second Review Fix - Closed Workflow Top Level (2026-07-14)

- Independent re-review found that the semantic validator closed the job and
  step model but ignored workflow top-level authority outside `jobs`. An added
  `env` / `BASH_ENV`, arbitrary top-level key, disabled or changed trigger, or
  broadened permissions could therefore retain the approved job model while
  changing execution authority.
- The normalized workflow must now have the exact approved top-level sequence:
  repository-contract `name`, `pull_request` plus `push` to `main`,
  `permissions` with only `contents: read`, and then the single `jobs` mapping.
  A second guard rejects any trailing top-level key after the jobs block.
- Seven negative mutations cover `env.BASH_ENV`, an extra `concurrency` key,
  complete trigger removal, trigger branch change, disabled triggers,
  `contents: write`, and complete permissions removal. Existing comment/blank,
  shell execution, job, step, runner, and diagnostic-upload mutations remain
  unchanged.
- Focused RED exited `1`; 1 test produced 7 expected subtest failures because
  every top-level mutation was accepted by the prior validator (`0.058s`).
  Focused GREEN exited `0`; all 4 semantic contract tests passed in `0.189s`.
- `bash -n` for all three contract scripts, `git diff --check`, staged diff
  check, and `.ai-runs` / recursive `__pycache__` absence checks passed.
- Review-fix implementation commit: `fa9e415` (`test(ai): close workflow
  top-level model`). The ignored Task 12 report is synchronized. The prior
  exact 417-test run is retained as pre-fix history; an exact post-`fa9e415`
  full-module rerun is pending with the parent and is not claimed here.
- No workflow source, production helper, schema, canonical state, product,
  infrastructure, GitHub state, push, PR, merge, Issue closure, or real
  `.ai-runs` operation changed or ran. Native enforcement and the external
  verifier remain `NOT_CONFIGURED`; independent re-review remains next.

### Task 12 Final Exact Contract Suite Evidence (2026-07-14)

- After `fa9e415` and its evidence commit `7c464dc`, the parent created a fresh
  writable temporary repository copy that included the linked-worktree `.git`
  pointer from the outset. No source changed after this copy was created.
- The parent ran the exact full helper command:
  `$env:PYTHONDONTWRITEBYTECODE='1'; python -m unittest scripts.ai.tests.test_workflow_helper -v`.
  It exited `0`: 418 tests ran in `192.707s`, all passed, and 20 explicit
  platform-capability tests were skipped (`OK (skipped=20)`).
- This is the final Task 12 exact-suite validation for the closed workflow
  top-level model. It supersedes the successful 417-test evidence that
  predated `fa9e415`; the earlier 416-test partition and 417-test runs remain
  preserved only as historical evidence.
- The exact validation executed helper tests only. It did not run Gradle,
  product commands, servers, Docker, HTTP/API, databases, migrations, seeds,
  deploys, GitHub Actions/state mutation, push, PR, merge, Issue closure, or
  real `.ai-runs`. Native enforcement and the external verifier remain
  `NOT_CONFIGURED`; independent re-review remains next.

### Task 13 Integration Fix - Complete Finalized Projection (2026-07-14)

#### Root Cause And TDD Evidence

- `run.json` is intentionally excluded from the artifact manifest, while the
  prior `validate_final_run_projection()` compared only run/task/result,
  selected reference lists, and the PASS manifest reference. Schema-valid
  mutations of `$id`, `startedAt`, `endedAt`, `workingDirectory`,
  `environment`, `redactionApplied`, and `reason` therefore returned PASS.
  Non-PASS finalizations also left manifest ID/run ID, complete claim content,
  gate reason, and non-command artifact path/kind identities unbound.
- Focused RED exited `1`: 4 test methods produced 10 expected failures. Every
  mutation returned `PASS`, exit `0`, instead of `FINAL_RUN_PROJECTION_MISMATCH`.
  The matrix covered the seven unbound run fields plus schema-valid FAIL-run
  manifest, claim, and gate mutations; claim/gate bytes were changed and the
  manifest digest/size was repaired to prove the manifest was not authority.
- The first embedded-manifest receipt prototype made the focused tests green,
  but review of the trust model showed that the receipt could be repaired with
  the manifest. That prototype was not committed. Authority was moved to the
  exact-CAS retained run session before proceeding.

#### Authoritative Receipt And Recovery Boundary

- Run sessions now have closed OPEN, FINALIZING, and FINALIZED states.
  `finalizationReceipt` is null in OPEN/FINALIZING and required in FINALIZED.
  The receipt contains the complete closed run projection, canonical digest
  and explicit outcome identity for the done claim, canonical digest and
  result/reason identity for the PRE_DONE_CLAIM gate, exact manifest `$id` and
  run ID, and the complete ordered artifact path/kind set.
- Finalization uses exact expected-session CAS twice: OPEN to FINALIZING, then
  FINALIZING to receipt-bearing FINALIZED before final artifacts are written.
  `run.json` is published only from the retained receipt projection and remains
  the final publication. The retained session is then made read-only and is
  excluded from manifest/directory evidence closure as control authority.
- Rollback receives the orchestrator's exact current FINALIZING or FINALIZED
  snapshot. Before `run.json` publication it removes only the attributed final
  artifacts and compare-and-swaps back to the captured OPEN session. A changed
  sealed session fails closed with `FINALIZATION_RECOVERY_REQUIRED`; an
  existing `run.json` remains non-rollbackable.
- `verify-finalized` loads the retained FINALIZED session independently of the
  manifest, validates every schema-defined run field by exact object equality,
  recomputes claim/gate canonical identities, requires the requested manifest
  identity, and compares every manifest artifact path/kind exactly.

#### GREEN And Expanded Verification

- Focused retained-authority GREEN exited `0`: the valid finalization plus the
  run-field and non-PASS manifest/claim/gate mutation methods all passed.
- Phase 1B-2 schema plus Phase 1B-3 finalization exited `0`: 38 tests passed in
  `40.305s`. After adding the second seal-CAS fault, schema-coverage, read-only
  receipt, and process-attempt kind-identity regressions, the fresh final Phase
  1B-3 class exited `0`: 24 tests passed in `43.018s`.
- Both CAS fault boundaries are covered: an exception after the first
  FINALIZING replace and an exception after the receipt-bearing FINALIZED seal
  each restore the exact OPEN snapshot. Validation/OSError partial publication
  rollback, retry, restore-error, mutated-seal recovery, and published-run
  non-rollback invariants also pass.
- The first exact full helper run completed 424 tests in `220.670s` with 44
  errors and 20 platform skips. All 44 errors were sandbox `WinError 5` failures
  from Phase 3B temporary provenance directory creation; no product or helper
  assertion failure was reported. Two approved long full-process reruns ended
  after the tool host closed stdout, so no PASS or exit code is claimed from
  them.
- The same affected and downstream coverage was rerun in bounded partitions:
  Phase 2C plus Phase 3A exited `0` with 131 tests passed and 2 platform skips
  in `52.848s`; approved Phase 3B exited `0` with 25 tests passed and 1 platform
  skip in `3.236s`. Together with the initial full-module evidence, this
  distinguishes the filesystem sandbox fault from functional regressions.
- Python AST parsing and Draft 2020-12 self-checks for all 28 schemas passed.
  Git Bash syntax checks for every `scripts/ai/**/*.sh`, `git diff --check`,
  staged diff check, and absence checks for repository `.ai-runs`, Phase 3B
  temporary directories, and recursive `__pycache__` all exited `0`.

#### Commit And Boundary

- Implementation commit: `9692fba` (`fix(ai): bind complete final run
  projection`). Changed files are the run-session schema/fixtures, helper,
  focused regressions, Phase 1B specification, and trust-boundary design.
- Gradle, product/build tests, server, Docker, HTTP/API, database, migration,
  seed, deploy, infrastructure, GitHub Actions/state mutation, push, PR, merge,
  Issue closure, and real repository `.ai-runs` were NOT RUN. This remains
  Phase 1B integrity-only evidence; independent review is the next role.

### Task 13 Integration Fix 1 - Recovery And Session Anchor (2026-07-14)

#### Review Findings And RED

- Integration review found two Important gaps in `9692fba`: no public operation
  could reconcile a process-crash-left FINALIZING or receipt-bearing FINALIZED
  session, and the receipt did not bind the complete pre-receipt session.
- Focused RED exited `1`. The run-session schema had no complete
  `preReceiptSession` or anchor digest, the helper had no
  `recover_finalization` operation, and schema-valid additions/removals in
  `processAttemptRefs`, `gateResultRefs`, `reservations`, and `lockRecoveries`
  could verify as PASS because authority was re-derived from the retained
  mutable session.

#### Implementation

- Commit `4035894` (`fix(ai): recover interrupted finalization safely`) adds the
  closed `FINALIZATION_RECOVERY` gateway operation and the documented shell
  command `done-claim-check.sh recover-finalization <run-id>`.
- Recovery acquires the exact run lock, reclaims only dead-and-expired stale
  ownership without changing a sealed session, and reconciles deterministically:
  FINALIZING is cleaned and compare-and-swapped to OPEN; a complete valid
  receipt-bearing FINALIZED state resumes missing claim/gate/manifest/run
  publications; inconsistent partial finals are cleaned and restored to OPEN.
  Existing `run.json` is verified, never rolled back, and the retained session
  read-only bit is repaired. Repeated recovery reports `ALREADY_OPEN` or
  `ALREADY_FINALIZED`.
- The receipt now stores the complete closed canonical FINALIZING session,
  including `$id`, command/process/approval/policy/gate refs, reservations,
  lock-recovery history, state and null receipt, plus its canonical SHA-256.
  Verification derives the run projection only from this anchored snapshot,
  requires the retained FINALIZED transform to match exactly, and cross-checks
  process, command, approval, policy, gate, reservation and artifact identities
  against manifest closure.

#### GREEN And Boundary

- The complete recovery matrix covers crashes after each durable session CAS,
  valid partial publication resume, inconsistent partial cleanup, dead/expired
  stale-lock recovery, retry idempotence, published-run non-rollback/read-only
  repair, Python CLI dispatch, and the shell alias.
- Fresh bounded verification exited `0`: GatewayResultSchema,
  Phase1B2Task1Schema, StrictJsonAndSchemaValidation, complete
  Phase1B3DoneClaimGate, and Phase1B2Task7RepositoryBoundary ran 75 tests in
  `66.332s`, all passed. Git Bash syntax checks for the touched shell entry
  points and `git diff --check` also exited `0`.
- Only helper unit/schema/static checks against temporary repositories ran.
  Gradle, product/build tests, server, Docker, HTTP/API, databases, migrations,
  seeds, deploys, infrastructure, GitHub mutation, push, PR, merge, Issue
  closure, and real repository `.ai-runs` were NOT RUN. Independent review is
  still required; this implementation record does not self-approve Task 13.

### Task 13 Integration Fix 2 - Independent Finalization Journal (2026-07-14)

#### Findings And RED Evidence

- Follow-up review found five Important gaps: recovery still derived OPEN from
  a potentially invalid receipt/current session, the original custom claim
  input reference was not sealed, a crash after manifest publication was
  treated as unexpected closure, sealed stale-lock recovery erased its history,
  and `EvidenceWriteUncertainty`/`RuntimeError` could escape recovery.
- The initial focused RED command exited `1`: seven assertions failed for the
  missing journal identity/order, unsafe normalization, manifest rollback,
  omitted recovery suffix, and escaping runtime uncertainty. The custom claim
  setup additionally raised `UNKNOWN_FINAL_ARTIFACT`, directly reproducing the
  hard-coded claim-input exclusion defect. The setup was converted to the
  desired public recovery assertion before implementation.

#### Journal Authority And Recovery Semantics

- Commit `9a225e8` (`fix(ai): anchor finalization recovery journal`) adds the
  closed `.state/finalization-journal.json` schema and writes that fixed,
  read-only journal through an exclusive durable publication before the
  OPEN-to-FINALIZING compare-and-swap.
- The journal binds a UUID identity, exact pre-transition OPEN session, exact
  derived FINALIZING session, requested `claimInputRef`, and expected
  lock-recovery history. The sealed receipt binds the independent journal path,
  ID, and canonical SHA-256. Verification and recovery load the journal
  independently and require exact receipt/journal/session relationships.
- Missing, malformed, or mismatched journal/receipt authority now returns the
  schema-valid `BLOCKED / FINALIZATION_RECOVERY_REQUIRED / 2` result without
  normalizing to OPEN. A valid inconsistent pre-run publication rolls back only
  through the journal OPEN source, exact final refs, exact current session CAS,
  and exact journal cleanup. Successful finalization retains the journal
  read-only; existing `run.json` remains non-rollbackable.
- Recovery reads the sealed custom claim reference, recognizes and validates an
  existing manifest before closure reconciliation, and resumes a crash after
  manifest publication. Dead-and-expired stale-lock recovery always appends its
  immutable history record; the sealed snapshot remains an exact prefix, new
  suffix entries are shape/identity validated, and rollback preserves the
  suffix without erase or reorder.
- `EvidenceWriteUncertainty` and `RuntimeError` are caught at the recovery
  boundary and return the same fail-closed schema-valid BLOCKED result. The
  public operation documentation now names the retained journal authority and
  distinguishes invalid authority from valid pre-publication cleanup.

#### Fresh Verification And Boundary

- Fresh combined verification exited `0`: GatewayResultSchema,
  Phase1B2Task1Schema, StrictJsonAndSchemaValidation, the complete expanded
  Phase1B3DoneClaimGate class, and Phase1B2Task7RepositoryBoundary ran 86 tests
  in `97.501s`, all passed.
- The matrix includes journal-before-CAS ordering, journal/session/history
  mutations, missing/mutated/schema-invalid authority, custom claim recovery,
  crash after manifest, retained read-only journal, stale suffix resume and
  rollback preservation, runtime uncertainty, prior idempotence, and every
  prior final projection/session mutation regression. Git Bash syntax checks
  for the touched shell entry points and `git diff --check` exited `0`.
- Only helper/schema/static checks against temporary repositories ran. Gradle,
  product/build tests, servers, Docker, HTTP/API, databases, migrations, seeds,
  deploys, infrastructure, GitHub mutation, push, PR, merge, Issue closure, and
  real repository `.ai-runs` were NOT RUN. Independent review remains required;
  this implementation evidence does not self-approve Task 13.
