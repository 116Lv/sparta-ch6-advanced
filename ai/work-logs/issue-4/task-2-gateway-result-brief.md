# Task 2 Brief: Gateway Result Schema And Python Preflight

## Context

Task 1 established the safe runtime bootstrap, durable LOCAL runtime evidence, canonical state synchronization, and isolated shell contract. Task 2 adds Python unittest coverage for the closed gateway result and preflight helper API. It still does not resolve or execute project commands.

## Required Reading

- `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`
- `docs/superpowers/plans/2026-07-10-ai-workflow-phase-1b-1-implementation.md`
- `ai/work-logs/issue-4/task-1-rereviewer.md`

## Files Owned

- `scripts/ai/tests/test_workflow_helper.py`
- `scripts/ai/workflow_helper.py`
- `ai/schemas/gateway-result.schema.json`
- `ai/fixtures/phase-1b/gateway-result/`
- `ai/work-logs/issue-4/task-2-implementation-agent.md`

Do not modify any other file. Preserve all Task 1 behavior and unrelated changes.

## TDD Sequence

1. Create `test_workflow_helper.py` first.
2. Run `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh` and observe RED.
3. Extend only the gateway schema/helper behavior required by the tests.
4. Run the same Python contract GREEN.
5. Run `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh` to prove Task 1 remains GREEN.

## Required Behavior

- PREFLIGHT PASS validates with `$schema`, `$id`, `schemaVersion`, operation, result, reason, errors, and closed data.
- PREFLIGHT non-PASS requires non-empty reason and no executable argv.
- RESOLVE PASS schema branch requires command ID, classification, working directory, argv array, and deterministic prerequisite IDs.
- RESOLVE/BLOCKED prerequisite branch contains only prerequisite IDs in data and no argv/working directory.
- Unknown operation, result, and extra fields are rejected.
- Helper preflight reports Python major 3, package version, Draft 2020-12 validator, FormatChecker, and interpreter SHA-256 without path disclosure.
- Every non-bootstrap result is validated before publication; malformed result schema maps to INVALID_STATE/5.
- No project subprocess, `.ai-runs`, registry mutation, or command VERIFIED transition.

## Verification Boundary

Allowed:

- `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`
- `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
- temporary JSON fixtures

NOT RUN: Gradle, product tests, server, Docker, HTTP/API, database, migration, seed, or infrastructure commands.

## Handoff

Update the role log with RED/GREEN outputs, changed files, self-review, `.ai-runs` absence, and DONE/DONE_WITH_CONCERNS/BLOCKED.
