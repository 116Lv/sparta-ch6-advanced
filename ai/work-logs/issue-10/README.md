---
issue: 10
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/10
tracking_status: issue_backed
status: done
owning_feature: none
current_owner: reviewer
started_at: 2026-07-13T11:03:43+09:00
ended_at: 2026-07-13T22:21:36+09:00
last_updated: 2026-07-13T22:21:36+09:00
branch: codex/phase-3a-native-runtime-adapters
related_files:
  - docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md
  - docs/superpowers/plans/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-implementation.md
changed_files:
  - .gitattributes
  - AGENTS.md
  - docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md
  - docs/superpowers/plans/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-implementation.md
  - ai/schemas/native-runtime-adapters.schema.json
  - ai/schemas/native-runtime-snapshot.schema.json
  - ai/schemas/native-bypass-attempt.schema.json
  - ai/schemas/native-adapter-result.schema.json
  - ai/schemas/agent-handoff.schema.json
  - ai/native-runtime-adapters.json
  - ai/native-runtime-adapters.md
  - ai/agent-handoff.json
  - ai/agent-handoff.md
  - ai/cache-policy.md
  - ai/document-routing.md
  - ai/verification-gates.md
  - ai/verification-policy.json
  - ai/schemas/verification-policy.schema.json
  - ai/skill-catalog.json
  - ai/tool-call-policy.md
  - ai/workflow-cache.json
  - ai/workflow-cache.md
  - ai/work-logs/index.md
  - ai/work-logs/issue-10/README.md
  - ai/work-logs/issue-10/plan-reviewer.md
  - ai/work-logs/issue-10/implementation-agent.md
  - ai/work-logs/issue-10/reviewer.md
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - scripts/ai/native-adapter-gate.sh
  - scripts/ai/verification-gate.sh
commands_run:
  - "Historical Task 1 (exit 0): python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v"
  - "Historical Task 1 (exit 0): python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v"
  - "Task 5 (exit 0): git status --short [before; clean]"
  - "Task 5 (exit 0): python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v"
  - "Task 5 (exit 0): python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v"
  - "Task 5 (exit 1; NOT PASS): python -m unittest scripts.ai.tests.test_workflow_helper -v"
  - "Task 5 (exit 1; NOT PASS): bash scripts/ai/run-helper-tests.sh"
  - "Task 5 (exit 0): bash scripts/ai/tests/run-contract-tests.sh"
  - "Task 5 (exit 0): bash scripts/ai/runtime-preflight.sh"
  - "Task 5 (exit 0): bash scripts/ai/repo-intake.sh --output -"
  - "Task 5 (exit 1; expected non-PASS): bash scripts/ai/native-adapter-gate.sh --task-key issue-10 --gate-invocation-id final-static --output -"
  - "Task 5 (exit 0): Test-Path .ai-runs; Get-ChildItem -Recurse -File -Filter artifact-manifest.json | Where-Object { $_.FullName -notmatch '\\ai\\fixtures\\' }; Get-ChildItem -Recurse -File -Filter run.json | Where-Object { $_.FullName -notmatch '\\ai\\fixtures\\' } [absent; 0; 0]"
  - "Task 5 (exit 0): git diff --exit-code origin/main -- ai/command-registry.json"
  - "Task 5 (exit 0): git ls-files --eol -- ai/fixtures/phase-1b/execution/fake-gradlew; git check-attr --all -- ai/fixtures/phase-1b/execution/fake-gradlew [i/lf w/crlf; text/eol unspecified]"
  - "Task 5 (exit 0): git rev-parse origin/main:ai/fixtures/phase-1b/execution/fake-gradlew; git rev-parse :ai/fixtures/phase-1b/execution/fake-gradlew; git hash-object ai/fixtures/phase-1b/execution/fake-gradlew; git hash-object --no-filters ai/fixtures/phase-1b/execution/fake-gradlew [clean-filtered/index/origin 59c3111f32a22ddac701cf212b148160df516850; raw checkout 3d9c04428a49e35002a85aadd1feaa895d0c5dea]"
  - "Task 5 (exit 0): git diff --check"
  - "Task 5 (exit 0): git status --short [after; clean]"
  - "Phase 3A minor closeout (exit 0): git status --short --branch [output: ## codex/phase-3a-native-runtime-adapters...origin/main [ahead 30]]"
  - "Phase 3A minor closeout (exit 0): python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v"
  - "Phase 3A minor closeout (exit 0): python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v"
  - "Phase 3A minor closeout (exit 0): git diff --check"
  - "Final branch review RED (exit 1 as expected): 7 focused signed-snapshot/provenance tests exposed 12 missing trust-path failures."
  - "Final branch review (exit 0): python -B -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v [78 tests]"
  - "Final branch review (exit 0): python -B -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v [85 tests]"
  - "Final branch review (exit 0): 3 targeted schema, workflow-cache, and agent-handoff validation tests."
  - "Final branch review (exit 0): bash -n native-adapter-gate.sh; artifact absence; command-registry diff; git diff --check."
  - "Final lifecycle finding RED (exit 1 as expected): 7 focused schema, signed-resolution, unresolved, and Issue10 metadata tests reported 14 expected failures."
  - "Final lifecycle finding focused GREEN (exit 0): 6 signed-resolution and unresolved-detection tests."
  - "Final lifecycle finding (exit 0): python -B -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v [85 tests]"
  - "Final lifecycle finding (exit 0): python -B -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v [92 tests]"
  - "Final lifecycle finding (exit 0): 4 targeted snapshot-schema, Issue10 metadata, workflow-cache, and agent-handoff tests."
  - "Final lifecycle finding (exit 0): git diff --check; artifact absence; command-registry diff."
tests_run:
  - "Historical Task 1 RED: expected allowlist assertion failure before implementation."
  - "Historical Task 1 GREEN (exit 0): focused allowlist and issue-backed work-log test passed (1 test)."
  - "Historical Task 1 GREEN (exit 0): Phase3ANativeRuntimeAdapterTests passed (4 tests)."
  - "Task 5 (exit 0): Phase3ANativeRuntimeAdapterTests passed (68 tests)."
  - "Task 5 (exit 0): Phase2CVerificationGateTests plus Phase3ANativeRuntimeAdapterTests passed (75 tests)."
  - "Task 5 (exit 1; NOT PASS): full helper unittest and run-helper-tests.sh each reported 319 tests, 1 CRLF fixture failure, and 17 skips."
  - "Task 5 (exit 0): contract tests, runtime preflight without --record, and repo intake passed."
  - "Task 5 (exit 1; expected non-PASS): native adapter gate returned UNSUPPORTED/HOST_UNSUPPORTED with phase2CLeafResult NOT_APPLICABLE."
  - "Phase 3A minor closeout (exit 0): Phase2CVerificationGateTests plus Phase3ANativeRuntimeAdapterTests passed (76 tests)."
  - "Phase 3A minor closeout (exit 0): focused issue-backed work-log/static test passed (1 test)."
  - "Final branch review GREEN (exit 0): Phase3ANativeRuntimeAdapterTests passed 78 tests."
  - "Final branch review GREEN (exit 0): Phase2CVerificationGateTests plus Phase3ANativeRuntimeAdapterTests passed 85 tests."
  - "Final branch review GREEN (exit 0): targeted schema/cache/handoff set passed 3 tests."
  - "Full helper suite was not rerun in this fix wave; the prior disclosed 319-test result with one CRLF fixture failure and 17 skips remains historical evidence until the main agent reruns it."
  - "Final lifecycle finding RED: expected failures showed resolutionEventIds absent from the snapshot contract, unconditional RESOLVED_TRANSITION blocking, snapshot trust preceding ordinary unresolved blocking, and drifted Issue10 metadata."
  - "Final lifecycle finding GREEN (exit 0): Phase3A passed 85 tests; Phase2C plus Phase3A passed 92 tests; targeted schema/handoff/cache and Issue10 metadata passed 4 tests."
  - "Final lifecycle repository checks (exit 0): git diff --check; .ai-runs absent; non-fixture artifact-manifest.json count 0; non-fixture run.json count 0; command-registry diff empty."
blockers: []
skill_ids:
  - review-gate
handoff_state_ref: ai/agent-handoff.json
reusable_context_refs:
  - ai/context-map.json
  - ai/workflow-cache.json
  - ai/verification-policy.json
not_run_project_commands:
  - Gradle/build and product/unit project tests
  - application server
  - Docker Compose
  - HTTP/curl/API
  - database operations
  - migration and seed
  - deployment and infrastructure/operations
  - durable evidence generation (.ai-runs, non-fixture artifact-manifest.json, finalized non-fixture run.json)
github_reconciliation_status: issue_backed
reconciliation_required: false
issue_creation_attempted_at: 2026-07-13T10:00:00+09:00
issue_creation_failure_reason:
expected_issue_scope: Phase 3A native runtime adapter contracts, current-host evaluation, and Phase 2C integration without product-command execution.
migration_history: []
---

# Issue Summary

## Final Approval Review Remediation (2026-07-13)

The final independent approval review found one Critical and three Important trust-contract gaps: the signed snapshot authenticated only resolution IDs rather than the complete bypass event set, omitted `taskKey` from signed challenge identity, allowed inconsistent surface/operation combinations, and did not classify backend-level Ed25519 unavailability. A separate reviewer also found that the raw-byte handoff cache digest depended on checkout EOL conversion.

The remediation adds signed `taskKey`, bounded `bypassEventCount`, and `bypassEventSetSha256`, recomputes the canonical deduplicated event-set digest before PASS, includes task identity in replay state, closes surface/operation/command-intent combinations, and maps `UnsupportedAlgorithm` to completion-blocking `NATIVE_ADAPTER_CRYPTO_UNAVAILABLE`. The Phase 2C Issue #7 reconciliation record remains intact while `phase3AIssue` identifies Issue #10. `.gitattributes` fixes `ai/agent-handoff.json` as `-text`, and the `FRESH` raw-byte SHA-256 was recomputed from deterministic LF bytes.

Focused RED produced four expected failures before implementation. Focused GREEN passed four tests, and the complete Phase 3A suite passed 88 tests. A subsequent rereview found the remaining omitted `commandIntent` branch; its negative regression now closes the matrix and the Phase 2C plus Phase 3A suite passes 95 tests. The independently observed full helper result remains NOT PASS: 336 tests, one unchanged CRLF fixture failure, and 17 skips. No product command or durable evidence command was run.

## Recovery Summary

Issue #10 tracks the cohesive Phase 3A native runtime adapter work. Task 1 resumed from a verified RED test and completed only the closed schema contracts, work logs, and helper schema allowlist entries.

## Routing Outcome

- Owning feature: `none`
- Routing reason: Phase 3A is repository-wide AI workflow infrastructure, not a product feature.
- Routing files read:
  - [Document Routing](../../document-routing.md)
  - [Phase 3A design](../../../docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md)
  - [Phase 3A implementation plan](../../../docs/superpowers/plans/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-implementation.md)

## Agent Logs

- [Plan reviewer](plan-reviewer.md): done
- [Implementation agent](implementation-agent.md): done
- [Reviewer](reviewer.md): done

## Current State

Task 1 is historical and complete; Tasks 2 through 4 are also complete. Task 5 records qualified Phase 3A static/helper evidence and independent final review. The `done` status records only this work-log lifecycle; it does not establish native enforcement PASS, product-command verification, a registry `VERIFIED` transition, issue closure, reconciliation completion, or an unqualified overall DONE claim.

## Decisions

- Historical Task 1 authorized three Phase 3A schema names; this final review wave adds the separately reviewed closed runtime-snapshot schema required by the supported-host trust path.
- The Issue remains open; Task 1 does not close Issue #10 or make an unqualified overall DONE claim.

## Verification Evidence

- RED command: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v`
- Result: expected failure because the three schema names were absent from the helper allowlist.
- GREEN command: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v`
- Result: PASS (1 test).
- Scoped contract command: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
- Result: PASS (4 tests).

## Blockers

- None.

## Next Handoff

- Next role: implementation-agent
- Required reading:
  - [Issue summary](README.md)
  - [Implementation plan](../../../docs/superpowers/plans/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-implementation.md)
- Context links:
  - [Plan reviewer log](plan-reviewer.md)
- Remaining work: Phase 3B CI installation, remote-runner guarantees, durable CI evidence, and cross-host parity.
- Evidence required: separately scoped supported-host verification and review.

## Task 5 Final Verification (2026-07-13)

| Command | Exit | Concise result |
| --- | ---: | --- |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v` | 0 | PASS: 68 tests. |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v` | 0 | PASS: 75 tests. |
| `python -m unittest scripts.ai.tests.test_workflow_helper -v` | 1 | NOT PASS: 319 tests, 1 failure, 17 skipped; `PosixLaunchTests.test_fake_gradlew_is_exact_posix_builtin_fixture` expected LF but the worktree fixture starts with CRLF. |
| `bash scripts/ai/run-helper-tests.sh` | 1 | NOT PASS: same 319-test CRLF-only failure and 17 skips. |
| `bash scripts/ai/tests/run-contract-tests.sh` | 0 | PASS: runtime preflight and thin closed command shell contracts. |
| `bash scripts/ai/runtime-preflight.sh` | 0 | PASS: closed `PREFLIGHT` result; run without `--record`. |
| `bash scripts/ai/repo-intake.sh --output -` | 0 | PASS: `createdAiRuns: false`; command discovery remains proposal-only. |
| `bash scripts/ai/native-adapter-gate.sh --task-key issue-10 --gate-invocation-id final-static --output -` | 1 | Expected non-PASS status: `UNSUPPORTED`, `HOST_UNSUPPORTED`, repository-only qualification, and Phase 2C leaf `NOT_APPLICABLE`. |
| `git diff --check` | 0 | PASS: no whitespace errors. |

The status was clean before the commands and remained clean afterward (`codex/phase-3a-native-runtime-adapters...origin/main [ahead 28]`). The full-suite failure is environmental: `git ls-files --eol` reports `i/lf w/crlf` for `ai/fixtures/phase-1b/execution/fake-gradlew`. Its clean-filtered working-tree hash (`git hash-object`) equals the index and `origin/main` blob hash (`59c3111f32a22ddac701cf212b148160df516850`); the distinct raw checkout hash (`git hash-object --no-filters`) is `3d9c04428a49e35002a85aadd1feaa895d0c5dea`. It is not attributed to the Phase 3A branch.

## Artifact And Promotion Checks

- Repository `.ai-runs`: absent.
- Non-fixture `artifact-manifest.json`: absent.
- Non-fixture finalized `run.json`: absent.
- `git diff --exit-code origin/main -- ai/command-registry.json`: exit 0.
- No product command was run: Gradle/build, product tests, application server, Docker Compose, HTTP/curl/API, database, migration, seed, infrastructure, or deployment.
- No native enforcement PASS, registry `VERIFIED` promotion, or product verification claim was made.

## Independent Review

Task 3 review found its closed schemas, redaction, bypass lifecycle, current-host `UNSUPPORTED` mapping, and no-artifact boundary covered by the final 68-test suite. Task 4 review found the required in-process `native-runtime-adapter` leaf, forged-leaf rejection, correlation handling, Phase 2C mapping, repository-only qualification, command-runner boundary, and Phase 3B deferral covered by the final 75-test suite and document inspection. No Critical or Important finding remains.

The queued Minor diagnostic is resolved: after confirming the top-level `results` array shape, `load_verification_leaf_results()` pre-scans dictionary entries for the reserved `native-runtime-adapter` check ID before ordinary entry validation. The regression places a malformed ordinary leaf before a forged native leaf and now returns `NATIVE_ADAPTER_LEAF_FORGED`.

## Phase 3A Minor Closeout Verification (2026-07-13)

- `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`: exit `0`, 76 tests passed.
- `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v`: exit `0`, 1 test passed.
- `git diff --check`: exit `0`; no whitespace errors. Git reported only the existing LF-to-CRLF conversion warnings for modified tracked files.

## Final Branch Review Fix Wave (2026-07-13)

Implemented the primary supported-host trust path with a closed runtime snapshot schema, restricted RFC 8785-compatible canonical bytes, real optional `cryptography.hazmat` Ed25519 verification, pinned public-key fingerprint, 300-second freshness, one-use gate challenge, and signed callback proof on all four surfaces. A temporary supported policy and temporary key now prove an all-`ENFORCED` snapshot can pass; bad producer, host/version, key, signature, freshness, challenge, replay, callback, or missing crypto blocks. No key, replay state, or runtime evidence is durable.

Results now separate `claimedSurfaces` from `trustedSurfaces`; policy declarations are baseline-only and cannot emit runtime `ENFORCED`. Canonical `supportedHosts` remains empty, current host version is `null`/`UNPROBED`, all four current surfaces remain `UNSUPPORTED`, and the Phase 2C leaf remains repository-qualified `NOT_APPLICABLE` with `HOST_UNSUPPORTED`.

Fresh evidence: Phase3A passed 78 tests; Phase2C plus Phase3A passed 85 tests; targeted schema/cache/handoff validation passed 3 tests; shell syntax, artifact absence, command-registry non-promotion, and `git diff --check` exited 0. The full helper suite was deliberately not rerun. Its earlier disclosed 319-test run with one CRLF checkout-fixture failure and 17 skips remains prior evidence until the main agent reruns it. No Gradle/product/server/Docker/HTTP/API/database/migration/seed/deploy command or durable evidence generation ran.

## Final Lifecycle Finding Fix Wave (2026-07-13)

This fix wave adds required bounded unique `resolutionEventIds` to the closed runtime snapshot and therefore to the canonical signed bytes. A valid later-gate `RESOLVED` transition proceeds through supported/probed host selection, freshness, Ed25519 signature, one-use challenge, signed callback proof, and all-`ENFORCED` trust before its current resolution event IDs are compared exactly with the signed array. Exact binding permits the otherwise valid temporary signed adapter vector to return `PASS`; missing, mismatched, or extra binding has a distinct `BLOCKED` reason, while duplicate or oversized binding is snapshot-contract invalid. Stale and bad-signature vectors remain blocked on the snapshot trust path, and ordinary unresolved detections block before trust evaluation.

The four Issue #10 `changed_files` lists now match the 31 tracked files changed across the contiguous Phase3A commit range. Ignored SDD references were replaced by the tracked design, implementation plan, and Issue work-log links; this summary and the work-log index share the same update timestamp.

Observed helper/static evidence before this record update: Phase3A passed 85 tests, Phase2C plus Phase3A passed 92 tests, and the targeted snapshot-schema, Issue10 metadata, workflow-cache, and agent-handoff set passed 4 tests. `git diff --check`, artifact absence, and command-registry diff checks exited 0. This evidence does not establish product verification, a registry `VERIFIED` transition, Issue closure, reconciliation completion, or an unqualified overall `DONE` claim. Canonical host state remains `null`/`UNPROBED` and `UNSUPPORTED`; no product command or durable evidence generation ran.
