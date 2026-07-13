---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: task-5-implementation-agent
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: task-5-implementation-agent
started_at: 2026-07-11T00:00:00Z
ended_at: 2026-07-11T00:00:00Z
last_updated: 2026-07-13T09:32:29+09:00
branch: main
related_files:
  - ai/work-logs/issue-4/task-5-resolution-brief.md
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-10-ai-workflow-phase-1b-1-implementation.md
changed_files:
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - scripts/ai/tests/test-runtime-preflight.sh
  - ai/schemas/gateway-result.schema.json
  - ai/project-state.md
  - ai/fixtures/phase-1b/parameters/README.md
  - ai/fixtures/phase-1b/parameters/duplicate-key.json
  - ai/fixtures/phase-1b/prerequisites/README.md
  - ai/fixtures/phase-1b/prerequisites/ordered.json
  - ai/work-logs/issue-4/task-5-resolution-brief.md
  - ai/work-logs/issue-4/task-5-implementation-agent.md
commands_run:
  - C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
  - C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh
tests_run:
  - "RED: helper contract exit 1; 42 tests ran; resolver cases failed because resolve_command was absent."
  - "RED: helper contract exit 1; 43 tests ran; resolution order and secret-directory regressions failed before their minimal fixes."
  - "RED: helper contract exit 1; 45 tests ran; extra resolve arguments escaped as argparse SystemExit 2."
  - "GREEN: helper contract exit 0; 45 tests ran in 5.253s; OK (skipped=3)."
  - "Runtime-preflight regression: exit 0; PASS: runtime preflight contract."
  - "Critical-review RED: helper contract exit 1; 51 tests ran; FAILED (failures=20, errors=1, skipped=7) for unsafe output writes, missing BLOCKED/null schema support, fake prerequisite data, wrong RegistryBlockedError mapping, and absent publish_resolve_output."
  - "Critical-review GREEN: helper contract exit 0; 51 tests ran in 8.397s; OK (skipped=7)."
  - "Runtime-preflight regression after critical-review GREEN: exit 1; result-publication-fallbacks exposed a monkeypatched gateway_result compatibility regression."
  - "Publication-fallback RED: helper contract exit 1; 52 tests ran; FAILED (errors=1, skipped=7) because fallback construction depended on the monkeypatched result factory."
  - "Final GREEN: helper contract exit 0; 52 tests ran in 8.367s; OK (skipped=7)."
  - "Final runtime-preflight regression: exit 0; PASS: runtime preflight contract."
  - "Final-review RED: helper contract exit 1; 59 tests ran in 8.729s; FAILED (failures=2, errors=9, skipped=7) for the absent current-state preflight, incomplete generated summary, and stale module contract."
  - "Final-review GREEN: helper contract exit 0; 59 tests ran in 9.745s; OK (skipped=7)."
  - "Updated runtime-preflight contract before canonical sync: exit 0; PASS: runtime preflight contract."
  - "Actual repository recorded preflight sandbox attempt: exit 1; PREFLIGHT/INVALID_STATE with STATE_RECORDING_FAILED because the requested repository is outside default writable roots."
  - "Approved actual repository recorded preflight: exit 0; PREFLIGHT/PASS using runtimeCommand python."
  - "Post-record runtime-preflight contract: exit 0; PASS: runtime preflight contract."
  - "Final helper verification after canonical summary sync: exit 0; 59 tests ran in 9.813s; OK (skipped=7)."
blockers: []
historical_blockers:
  - "Seven parameter/output/working-directory/wrapper symlink cases are skipped in this Windows sandbox because symlink creation is unavailable."
reconciliation_required: false
issue_creation_attempted_at: 2026-07-10T12:37:12Z
issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"
expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 1B command gateway without product behavior changes."
migration_history:
  - migrated_at: 2026-07-13T08:54:37+09:00
    from: ai/work-logs/no-issue/phase-1b-command-gateway
    to: ai/work-logs/issue-4
    comment_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4#issuecomment-4953423372
---

## Reconciliation Update

GitHub Issue #4 now backs this historical role record. Statements below about unavailable Issue creation, pending reconciliation, or the earlier 403 describe the state when this role executed; they are not current blockers.

# Task 5 Implementation Log

## Routing

The task is repository-wide AI workflow infrastructure with `owning_feature: none`. It executes the approved Phase 1B-1 Task 5 plan.

## TDD Record

Created the brief and log before code. Added the pure-resolution contract and fixtures, captured RED before `resolve_command` existed, implemented the resolver and preflight-gated CLI, then captured final GREEN and runtime-preflight evidence. Follow-up RED/GREEN cycles fixed canonical-validation ordering and secret-directory rejection.

## Command Boundary

No project argv, Gradle, product test, server, Docker, HTTP/API, database, migration, seed, or infrastructure command is authorized by this task. No `.ai-runs` artifact is created. No files are staged or committed.

## Work Done

- Added pure `resolve_command` behavior for ordered schema/semantic validation, ID lookup, configuration and classification mapping, closed parameter handling, whole-token substitution, prerequisite blocking, final containment, and schema-valid result publication.
- Added the internal `resolve` CLI with mandatory non-recording current preflight, fixed exit mapping, stdout marker support, and contained file output.
- Added strict parameter and prerequisite fixtures plus contract tests for UTF-8 JSON, duplicate keys, size/scalar/control limits, inert argv values, forbidden paths, deterministic prerequisites, no process invocation, no `.ai-runs`, and CLI output behavior.

## Verification Evidence

- `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`: exit `0`; `Ran 45 tests in 5.253s`; `OK (skipped=3)`.
- `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`: exit `0`; `PASS: runtime preflight contract`.
- NOT RUN: Gradle, product tests, application server, Docker, HTTP/API, database, migration, seed, and infrastructure commands.

## Remaining Concern

Seven symlink cases are skipped by the current Windows sandbox. The regular containment checks and all non-symlink output and parameter-path rejections ran; a symlink-capable runtime is still needed for an unqualified realpath-containment claim.

## Critical Review Finding Dispositions

1. **Output safety: fixed.** Resolve output now supports only stdout `-` or a new, non-hidden, root-level lowercase `.json` file. Existing files, destination symlinks, nested paths, hidden paths, non-JSON paths, and every `ai/`, `scripts/`, `gradle/`, `.git/`, or `.ai-runs/` path are rejected. File creation uses exclusive create semantics and cannot replace a raced existing target. CLI regressions prove canonical, executable, and existing bytes remain unchanged; `resolution.json` remains the supported benign file case.
2. **Missing-wrapper result mapping: fixed.** `RegistryBlockedError` now maps to schema-valid `RESOLVE/BLOCKED`, exit `2`, with `data: null` and the stable wrapper error preserved.
3. **BLOCKED result shape: fixed.** The gateway schema retains the exact non-empty prerequisite-data branch and adds a disjoint exact `data: null` branch. UNKNOWN/STALE/UNCERTAIN and RISKY/DESTRUCTIVE results no longer manufacture prerequisite IDs; only actual prerequisite blocking includes ordered `prerequisiteIds`.
4. **Resolved parameter-path policy: fixed.** The helper applies the same `.git`, `.ai-runs`, secret-path, and `.env` checks to repository-relative parts after strict realpath resolution. Symlink-capable regressions cover lexical-safe aliases into each forbidden class; they are explicit but skipped on this Windows host.
5. **Schema-valid BLOCKED coverage: fixed.** Tests validate missing-wrapper, configuration, classification, and actual-prerequisite BLOCKED results against `gateway-result.schema.json` and assert the exact null-versus-prerequisite data shape.

## Critical Review TDD Evidence

- RED: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh` exited `1`; `Ran 51 tests in 7.508s`; `FAILED (failures=20, errors=1, skipped=7)`.
- First GREEN: the same helper command exited `0`; `Ran 51 tests in 8.397s`; `OK (skipped=7)`.
- Runtime regression then exposed the publication-fallback compatibility issue and exited `1` in `result-publication-fallbacks`.
- Focused fallback RED: helper tests exited `1`; `Ran 52 tests in 8.441s`; `FAILED (errors=1, skipped=7)`.
- Final GREEN: helper tests exited `0`; `Ran 52 tests in 8.367s`; `OK (skipped=7)`.
- Final runtime regression: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh` exited `0`; `PASS: runtime preflight contract`.
- NOT RUN: Gradle, product tests, application server, Docker, HTTP/API, database, migration, seed, and infrastructure commands. No repository `.ai-runs`, staging, or commit was created.

## Final Review Finding Dispositions

1. **Public resolve current preflight: fixed.** `run_resolve` no longer constructs a hardcoded `runtimeCommand`. Every public resolve invocation probes the current interpreter, Python version, jsonschema version, validator, FormatChecker, and interpreter hash, then strictly validates durable LOCAL evidence and canonical project state before command resolution. The allowlisted durable `runtimeCommand` is published only as validated identity metadata. Missing evidence or state claims and schema-valid drift return read-only `BLOCKED`; malformed evidence/state returns `INVALID_STATE`; matching state returns `PASS`. No project process is created.
2. **Full generated project-state summary: fixed and synchronized.** `summary_for` now deterministically renders Project Summary (including facts), Important Paths, Known Ports, Environment State, Helper Runtime State, Command Registry Reference, and Cache Invalidation Inputs. It includes canonical source, schema version, update time, evidence paths, the Phase 1A bootstrap/source notice, and `8080 (INFERRED)`. Runtime contract coverage verifies recording retains every section and derives displayed values from canonical state. Human Policy Notes now distinguish the Phase 1A static bootstrap from Phase 1B recorded LOCAL helper evidence while keeping project commands `NOT RUN`.
3. **Module contract: fixed.** The helper docstring now states that it preflights and purely resolves commands but never executes project commands.

## Final Review TDD And Sync Evidence

- RED: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh` exited `1`; `Ran 59 tests in 8.729s`; `FAILED (failures=2, errors=9, skipped=7)`.
- GREEN: the same helper command exited `0`; `Ran 59 tests in 9.745s`; `OK (skipped=7)`.
- Updated runtime contract before canonical sync exited `0`; `PASS: runtime preflight contract`.
- First actual `scripts/ai/runtime-preflight.sh --record` attempt exited `1` with `STATE_RECORDING_FAILED` under the default filesystem sandbox. The approved retry exited `0` with `PREFLIGHT/PASS`, `runtimeCommand: python`, Python `3.9.6`, jsonschema `4.25.1`, validator `Draft202012Validator`, FormatChecker `true`, and interpreter SHA-256 `0fe699e2cb61a2cbe449a34eee56bd6175fbeb6ee7dc1261b0c338574c010d2b`.
- Matching evidence preserved both `ai/project-state.json updatedAt` and `ai/evidence/local-helper-runtime.json observedAt` at `2026-07-10T14:17:27Z`. Canonical JSON/evidence bytes remained logically unchanged; the generated Markdown section was transactionally expanded from canonical state.
- Post-record runtime contract exited `0`; `PASS: runtime preflight contract`.
- Final helper verification exited `0`; `Ran 59 tests in 9.813s`; `OK (skipped=7)`.
- NOT RUN: Gradle, product tests, application server, Docker, HTTP/API, database, migration, seed, and infrastructure commands. No repository `.ai-runs`, staging, or commit was created.
