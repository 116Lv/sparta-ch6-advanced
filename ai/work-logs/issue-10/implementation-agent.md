---
issue: 10
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/10
agent: implementation-agent
tracking_status: issue_backed
status: done
owning_feature: none
current_owner: implementation-agent
started_at: 2026-07-13T11:03:43+09:00
ended_at: 2026-07-13T22:21:36+09:00
last_updated: 2026-07-13T22:21:36+09:00
branch: codex/phase-3a-native-runtime-adapters
related_files:
  - ai/schemas/native-runtime-adapters.schema.json
  - ai/schemas/native-runtime-snapshot.schema.json
  - ai/schemas/native-bypass-attempt.schema.json
  - ai/schemas/native-adapter-result.schema.json
  - ai/native-runtime-adapters.json
  - ai/native-runtime-adapters.md
  - ai/agent-handoff.json
  - ai/workflow-cache.json
  - scripts/ai/native-adapter-gate.sh
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
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
  - "Historical Task 1 RED: expected schema-allowlist failure before implementation."
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
skill_ids: []
handoff_state_ref: ai/agent-handoff.json
reusable_context_refs:
  - ai/context-map.json
  - ai/workflow-cache.json
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

# Summary

## Final Approval Review Remediation

Implemented the final review fixes with test-first evidence. The snapshot signature now binds task identity and the complete canonical deduplicated bypass event set by count and SHA-256, replay identity includes the task, supported-host PASS compares those signed facts after trust, and resolution IDs remain an additional exact binding. Surface/operation/command-intent combinations are closed, backend Ed25519 unavailability returns structured `BLOCKED`, and handoff cache bytes are checkout-stable through an exact-file `-text` attribute. Focused GREEN passed four tests; the Phase 3A suite passed 88 tests.

The final rereview identified one remaining `COMMAND`/`COMMAND` branch that allowed omitted `commandIntent`. The schema now requires the matching intent and the negative regression is part of the passing 95-test Phase 2C plus Phase 3A set.

Completed the historical Task 1 closed schema contracts and three-name helper allowlist update; the final review wave adds the separately reviewed closed runtime-snapshot schema.

# Work Done

- Resumed from the recorded RED test.
- Preserved the valid inherited schemas, work logs, tests, index entry, and helper allowlist additions.
- Verified the mandated focused GREEN test and the complete Task 1 schema-vector test class.

# Current State

Historical Task 1 is complete. Tasks 2 through 4 subsequently completed; Task 5 records the final qualified evidence and independent review.

# Decisions

- Keep the implementation limited to Task 1 files and the authorized allowlist support.

# Verification Evidence

- Command: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v`
- Result: PASS (1 test).
- Command: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
- Result: PASS (4 tests).

# Blockers

- None.

# Next Handoff

- Next role: reviewer
- Required reading:
  - [Issue summary](README.md)
  - [Implementation plan](../../../docs/superpowers/plans/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-implementation.md)
- Context links:
  - [Plan reviewer log](plan-reviewer.md)
- Remaining work: Phase 3B CI installation, remote-runner guarantees, durable CI evidence, and cross-host parity.
- Evidence required: separately scoped supported-host verification; Task 5 did not create or claim native enforcement evidence.

## Task 5 Final Verification Record (2026-07-13)

- Phase 3A suite: exit 0, 68 tests passed.
- Phase 2C plus Phase 3A suite: exit 0, 75 tests passed.
- Full helper unittest and `run-helper-tests.sh`: exit 1 each; 319 tests, one CRLF fixture failure, and 17 skips. They are not PASS.
- Contract script, runtime preflight without `--record`, repo intake, and `git diff --check`: exit 0.
- Native adapter gate: expected exit 1 with `UNSUPPORTED`/`HOST_UNSUPPORTED` and `phase2CLeafResult: NOT_APPLICABLE`.

The sole full-helper failure is `PosixLaunchTests.test_fake_gradlew_is_exact_posix_builtin_fixture`: it expects LF while `ai/fixtures/phase-1b/execution/fake-gradlew` has CRLF checkout bytes. The clean-filtered working-tree hash (`git hash-object`) matches the index and `origin/main` blob (`59c3111f32a22ddac701cf212b148160df516850`); the raw checkout hash (`git hash-object --no-filters`) is `3d9c04428a49e35002a85aadd1feaa895d0c5dea`. `git ls-files --eol` reports `i/lf w/crlf`; no Phase 3A code change or auto-fix was made.

The repository was clean before and after the commands. `.ai-runs`, non-fixture `artifact-manifest.json`, and non-fixture finalized `run.json` remain absent; the command-registry diff against `origin/main` exits 0. Gradle/build, product tests, application server, Docker Compose, HTTP/curl/API, database, migration, seed, infrastructure, and deployment commands remain NOT RUN. No native enforcement PASS or registry `VERIFIED` promotion is claimed.

## Task 3 Final Hardening Report (2026-07-13)

### Scope

- Hardened native bypass-summary credential detection and lifecycle precedence in the assigned helper and focused tests.
- Preserved existing work and did not run product commands or collect runtime evidence.

### RED

- Command: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_bypass_summary_rejects_bearer_credentials_regardless_of_trailing_non_whitespace scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_bypass_summary_allows_bearer_token_documentation scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_bypass_summary_rejects_basic_credentials_regardless_of_trailing_non_whitespace scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_current_detection_wins_over_resolution_in_the_same_deduplication_group -v`
- Result: expected exit `1`; 4 tests ran with 13 failures. Quotes, apostrophes, braces, slashes, and an over-broad Bearer documentation exception bypassed the delimiter-based rules; a current detection lost to a resolution in the same deduplication group.

### GREEN

- Replaced delimiter enumeration with `Basic`/`Bearer` scheme-plus-non-whitespace-token checks.
- Restricted the Bearer documentation exception to the exact whole-summary phrase `bearer token documentation`.
- Made a current `DETECTED` event return `UNRESOLVED` before evaluating resolutions in the same deduplication group.
- Focused RED command after implementation: exit `0`; 4 tests passed.
- Complete adapter class: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v` exited `0`; 26 tests passed.

### Concerns

- The explicit Bearer documentation allowlist intentionally contains only the case-insensitive exact whole-summary phrase required by the tests. Any surrounding or additional text remains fail-closed.

## Task 3 Final Input-Classification Report (2026-07-13)

### Scope

- Rejected an explicitly empty native-adapter CLI `--repository-root` before path resolution, including a subprocess run from repository CWD.
- Classified bypass reference/path/read failures as `BLOCKED` with `NATIVE_BYPASS_REFERENCE_INVALID`; loaded record schema and semantic failures remain `FAIL` with `NATIVE_BYPASS_CONTRACT_INVALID`.
- Replaced lexical `observedAt` ordering with exact RFC3339 UTC timestamp ordering, including variable-length fractional seconds.
- Preserved the canonical unsupported-host result and did not change the shell wrapper.

### RED

- Focused input-classification command exited `1` as expected before implementation: empty repository root resolved to the repository and returned `UNSUPPORTED`; bypass reference faults returned contract `FAIL`; fractional lifecycle input did not produce the required resolution classification.
- The first fractional vector revealed the Python 3.9 parser rejects a valid two-digit RFC3339 fraction. The final vector uses `.100Z` and `.1Z`, equivalent instants that sorted differently as strings, and drove the shared RFC3339 parser fix.

### GREEN

- Focused input-classification suite: 5 tests passed.
- Complete adapter class: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v` exited `0`; 39 tests passed.
- No Gradle, product, application, network, database, or infrastructure commands were run; no workflow evidence was created.

## Task 3 Trust-Boundary Fixes Report (2026-07-13)

### Scope

- Anchored the native adapter wrapper and helper path to the wrapper file location, independent of caller CWD.
- Applied closed identifier contracts and secret/raw-marker scanning to all bypass-attempt string content, including `runId`, `deduplicationKey`, and every summary value.
- Replaced terminal `$` SemVer anchors with Python-supported `\Z` in every Phase 3A schema.
- Required a current-gate `RESOLVED` event to follow a `DETECTED` event from a different gate invocation.

### TDD Evidence

- RED: the focused four-test command exited `1` with the expected failures: terminal-newline SemVer values were accepted by schemas; non-summary secret markers reached lifecycle handling; a same-invocation resolution was only untrusted; and an external CWD made the wrapper load a nonexistent helper.
- GREEN: the same focused tests passed after the minimal fixes. The wrapper path normalization uses Bash builtins so Git Bash Windows-style paths are anchored correctly.
- A follow-up RED/GREEN regression preserved the pre-existing 128/128/256 character limits for `taskKey`, `runId`, and `deduplicationKey` after they moved to closed identifier schemas.
- Full Phase 3A suite: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v` exited `0`; 51 tests passed.

### Boundary Notes

- No product commands, runtime evidence, or repository `.ai-runs` artifacts were created.
- The lifecycle remains fail-closed: a later unpaired detection is unresolved, while a resolution with no earlier detection from a different invocation is invalid.

## Task 3 Structured Redaction Contract Report (2026-07-13)

### Scope

- Replaced all four free-form bypass summary strings with closed structured schema variants.
- Required SHA-256 digests for non-`NONE` query/tool summaries and all argument summaries; `NONE` query/tool variants have no digest or content slot.
- Limited arguments to closed classifications and a count from zero through 64, repository targets to safe relative paths, and external targets to a closed redacted category plus digest.
- Preserved 512-scalar/UTF-8-byte checks and semantic secret-marker scanning across nested summary string leaves.
- Made every current-gate `DETECTED` event unresolved even when a later current-gate `RESOLVED` event can pair with an older detection.

### TDD Evidence

- Initial RED: the focused three-test command exited `1`; the old schema rejected each structured summary object and the lifecycle vector could not pass the retired string contract.
- Intermediate RED: after the schema change, both schema tests passed while lifecycle loading raised on the helper's string-only `.encode()` assumption.
- Lifecycle RED: after recursive summary inspection, same-gate detection vectors returned `NATIVE_BYPASS_RESOLUTION_INVALID` or `NATIVE_BYPASS_RESOLUTION_UNTRUSTED` instead of `NATIVE_BYPASS_UNRESOLVED`.
- Focused GREEN: six structured-contract, bounds, semantic-secret, and lifecycle tests passed.
- Full Phase 3A suite: `python -B -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v` exited `0`; 53 tests passed.

### Boundary Notes And Concerns

- No Phase 1/2 baseline, product command, workflow evidence, `.ai-runs` artifact, network call, database operation, or infrastructure command was touched or run.
- External target and payload/query classifications are deliberately closed. A future producer needing another category must update the schema and tests explicitly rather than publish an arbitrary label.

## Task 3 Portable Closed-Pattern Fix Report (2026-07-13)

### Scope

- Required the canonical unsupported-host minimum snapshot to contain a nonempty `producerId` and exactly `surfaces: []`; every nonempty or malformed surface value now yields `BLOCKED` with `NATIVE_ADAPTER_SNAPSHOT_INVALID`.
- Replaced terminal `$` and Python-only `\Z` usage in the three Phase3A-native schemas with the portable exact-end assertion `(?![\s\S])`, including identifiers, timestamps, repository paths/refs, SHA-256 digests/fingerprints, and SemVer.
- Added schema contract vectors for valid values and terminal-newline rejection, including `eventId`, fingerprints, result refs, digests, and versions.

### TDD Evidence

- RED: `python -B -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_canonical_empty_supported_hosts_block_malformed_unsigned_snapshot scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_native_adapter_schema_patterns_use_portable_exact_end_and_reject_terminal_newlines -v` exited `1` with 9 expected failures. `[null]` and other nonempty snapshots returned `UNSUPPORTED`; `$`-anchored values accepted terminal newlines.
- GREEN: the same focused command exited `0`; 2 tests passed.
- GREEN: `python -B -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v` exited `0`; 54 tests passed.

### Boundary Notes

- No product commands, runtime evidence, `.ai-runs` artifacts, network calls, database operations, or infrastructure commands were run or created.

## Task 4 Native Result Preservation Report (2026-07-13)

### Scope

- Preserved the mapped native adapter result in the early correlation and entry-point applicability returns.
- Reused one explicit-input native leaf in the regular verification check loop, so runtime snapshot and bypass references are evaluated once per gate invocation.
- Updated the malformed-bypass expectation from top-level `BLOCKED` to its correct `FAIL`/exit `1` contract; retained `BLOCKED`/exit `2` for native `BLOCKED` and `NOT_CONFIGURED`, and retained unsupported-host N/A behavior.

### TDD Evidence

- RED: the focused five-test command exited `1` with the expected three failures: both early malformed-bypass paths returned `BLOCKED` instead of `FAIL`, and explicit snapshot/bypass inputs invoked the evaluator twice.
- GREEN: the same focused command exited `0`; all 5 tests passed.

### Boundary Notes

- No product commands, evidence, `.ai-runs` artifacts, network calls, databases, or infrastructure commands were run or created.

## Phase 3A Minor Review Closeout (2026-07-13)

- Added a failing regression with a malformed ordinary leaf followed by a forged `native-runtime-adapter` leaf; it initially returned `VERIFICATION_LEAF_RESULTS_INVALID`.
- Updated `load_verification_leaf_results()` to pre-scan the confirmed `results` array for dictionary entries with the reserved native check ID before ordinary entry validation.
- The focused regression now returns `INVALID_STATE` with `NATIVE_ADAPTER_LEAF_FORGED` and exit status `5`.
- Current status provenance: `git status --short --branch` exited `0` with `## codex/phase-3a-native-runtime-adapters...origin/main [ahead 30]` before the closeout edits.
- Phase 2C plus Phase 3A focused verification passed 76 tests; the focused issue-backed work-log/static check passed; `git diff --check` exited `0` with no whitespace errors.

## Final Branch Review Fix Wave (2026-07-13)

### Strict TDD

- RED: seven focused supported-host signature, canonicalization, provenance, and fallback vectors exited `1` with 12 expected failures. Additional policy, shell-fallback, documentation, allowlist-count, and handoff-digest regressions each failed before their implementation.
- GREEN: the temporary Ed25519 vector passes only with a complete signed all-`ENFORCED` snapshot. Bad producer, host/version, key, signature, freshness, challenge, replay, callback, and unavailable crypto all block while trusted surfaces remain baseline `NOT_CONFIGURED`.
- GREEN: Phase 3A passed 78 tests; Phase 2C plus Phase 3A passed 85 tests; targeted schema/cache/handoff checks passed 3 tests.

### Scope And Boundaries

- Added a closed runtime snapshot contract, restricted RFC 8785-compatible canonical bytes, real optional `cryptography.hazmat` verification, claimed/trusted surface separation, and `hostVersion: null` plus `versionProvenance: UNPROBED|PROBED` conditionals.
- Canonical `supportedHosts` remains empty and the current host remains `UNSUPPORTED`/`NOT_APPLICABLE`. Repository policy cannot promote runtime surfaces to `ENFORCED`.
- Keys, snapshots, and evidence are not persisted. Replay challenges are consumed only in process; Phase 3B owns durable cross-process enforcement and runner installation.
- No prohibited product, service, network, database, deployment, or durable-evidence command ran.
- The full helper suite was not rerun. Its prior 319-test result with one disclosed CRLF checkout-fixture failure and 17 skips remains historical evidence until the main agent reruns it.

## Final Lifecycle Finding Fix Wave (2026-07-13)

### Strict TDD

- RED: seven focused tests reported 14 expected failures because the snapshot schema rejected `resolutionEventIds`, every valid `RESOLVED_TRANSITION` remained unconditionally blocked, snapshot trust ran before ordinary unresolved blocking, and Issue10 metadata omitted tracked Phase3A files and retained ignored references.
- GREEN: temporary Ed25519 vectors cover exact signed resolution binding `PASS`, missing/mismatched/extra binding `BLOCKED`, stale and bad-signature `BLOCKED`, unsupported/unprobed/no-snapshot resolution claims `BLOCKED`, and ordinary unresolved detection `BLOCKED` before challenge consumption.
- GREEN: Phase3A passed 85 tests; Phase2C plus Phase3A passed 92 tests; targeted snapshot-schema, Issue10 metadata, workflow-cache, and agent-handoff checks passed 4 tests.

### Scope And Boundaries

- The closed snapshot requires at most 64 unique resolution event identifiers of at most 128 characters, and canonical signing excludes only `signature`.
- Lifecycle evaluation retains every current valid later-gate resolution event ID. Exact comparison occurs only after full snapshot trust and all four trusted surfaces are `ENFORCED`.
- Resolution reasons remain schema allowlisted. Missing/mismatched/extra binding uses precise reasons; duplicate/oversized binding remains snapshot-contract invalid.
- Canonical current-host resolution claims remain blocking because the host is `null`/`UNPROBED` and `UNSUPPORTED`. No product command, registry promotion, Issue closure action, or durable evidence generation ran.
