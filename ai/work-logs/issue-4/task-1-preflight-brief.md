# Task 1 Brief: Preflight Bootstrap Contract

## Context

This is the first implementation task for AI Workflow Enforcement Phase 1B-1. It establishes only the helper-runtime bootstrap and structured preflight result. It does not resolve or execute project commands.

## Required Reading

- `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`
- `docs/superpowers/plans/2026-07-10-ai-workflow-phase-1b-1-implementation.md`
- `ai/schemas/project-state.schema.json`
- `ai/project-state.json`

## Files Owned

- `scripts/ai/tests/test-runtime-preflight.sh`
- `scripts/ai/runtime-preflight.sh`
- `scripts/ai/run-helper-tests.sh`
- `scripts/ai/workflow_helper.py`
- `ai/schemas/gateway-result.schema.json`
- `ai/schemas/helper-runtime-evidence.schema.json`
- `ai/evidence/local-helper-runtime.json`
- `ai/project-state.json`
- `ai/project-state.md`
- `.gitignore`
- `ai/fixtures/phase-1b/preflight/`
- `ai/work-logs/issue-4/implementation-agent.md`

Do not modify any other file. Other agents and the user may be working in the repository; do not revert or overwrite their changes.

## TDD Sequence

1. Write `test-runtime-preflight.sh` first.
2. Run it and record the expected RED failure caused by missing implementation.
3. Implement the minimum shell entry point, helper preflight, and closed gateway-result schema.
4. Run the same test and record GREEN, or report `NOT_CONFIGURED` with the exact missing runtime/dependency blocker.
5. Self-review for shell injection, unchecked executable selection, schema gaps, and accidental project execution.

## Required Behavior

- Candidate order is the literal PATH allowlist `python3`, then `python`.
- A candidate is accepted only if it proves Python major version 3 and imports `Draft202012Validator` and `FormatChecker`.
- `py`, environment-selected executable paths, Node.js, Java, and `jq` are ignored.
- No candidate returns fixed bootstrap JSON with `result: NOT_CONFIGURED` and exit `3`.
- Bootstrap failure JSON contains no caller-controlled text.
- Successful preflight emits a `gateway-result.schema.json`-valid PREFLIGHT PASS object.
- The argument-free helper-test launcher uses the preflight-selected `python3` or Python-3-compatible `python` and runs only the approved unittest module.
- Successful record mode writes schema-valid scrubbed LOCAL runtime evidence, transitions only the LOCAL helper-runtime state, and refreshes the generated project-state summary with recovery-journal protection.
- Evidence includes the interpreter SHA-256 without its path; an identical current report performs no tracked-file rewrite.
- Transient `ai/.workflow-state-txn/` state is ignored and any interrupted transaction is recovered before canonical reads.
- Unavailable runtime leaves canonical JSON and summary unchanged.
- Shell invocation uses quoted argv. No `eval`, `sh -c`, command string, alias, or unchecked append.
- Phase 1B-1 does not create `.ai-runs`; only preflight record mode may update helper-runtime canonical state.

## Test Boundary

Allowed:

- `bash scripts/ai/tests/test-runtime-preflight.sh`
- harmless temporary fake executables created by the test
- helper-runtime capability checks performed by the preflight

NOT RUN:

- Gradle and product tests
- application server
- Docker Compose
- HTTP/API requests
- database, migration, or seed commands
- infrastructure commands

## Handoff

Update `implementation-agent.md` with:

- status: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`;
- files changed;
- RED command and observed expected failure;
- GREEN command and exact result;
- confirmation that no project command executed and `.ai-runs` was not created;
- self-review findings and remaining concerns.
