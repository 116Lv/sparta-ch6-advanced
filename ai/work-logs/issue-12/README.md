---
issue: 12
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/12
tracking_status: issue_backed
status: done
owning_feature: none
current_owner: main-agent
started_at: 2026-07-13T23:30:00+09:00
ended_at: 2026-07-14T19:50:14+09:00
last_updated: 2026-07-20T14:05:00+09:00
branch: codex/phase-3b-ci-gates-durable-evidence
related_files:
  - docs/superpowers/specs/2026-07-13-ai-workflow-phase-3b-ci-gates-durable-evidence-design.md
  - docs/superpowers/plans/2026-07-13-ai-workflow-phase-3b-ci-gates-durable-evidence-implementation.md
---

# Issue Summary

> Current status: GitHub Issue #12는 2026-07-14에 종료됐다. 아래의 `pending`, `NOT_CONFIGURED`, 재실행 필요 문구는 종료 전 시점의 검증 이력이며 현재 Issue 진행 상태가 아니다.

Issue #12 tracks Phase 3B CI gates and durable CI evidence after PR #11 merged.
The work preserves approved Phase 1A through Phase 3A decisions. The current
local host remains `UNSUPPORTED`; CI durable evidence is currently
`NOT_CONFIGURED` and completion-blocking until a retained GitHub Actions run
provides durable identity and artifacts.

## Verification Log

- RED: Phase3BCIGatesDurableEvidenceTests failed before implementation because
  schemas, workflow, and `ci_evidence_gate()` did not exist.

## Boundaries

No product command, Gradle, server, Docker, HTTP/API, database, migration, seed,
deploy, or operations command is authorized by this work log. No `.ai-runs`,
manifest, finalized run, registry `VERIFIED`, Issue closure, or unqualified DONE
claim is produced by this phase.
## Verification Evidence

| Command | Exit | Result |
| --- | ---: | --- |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v` before implementation | 1 | RED: missing schema allowlist, workflow, and `ci_evidence_gate()`. |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v` | 0 | GREEN: 3 Phase 3B tests passed. |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v` | 0 | PASS: 98 tests. |
| `C:\Program Files\Git\bin\bash.exe scripts/ai/ci-evidence-gate.sh --task-key issue-12 --gate-invocation-id local-static --output -` | non-pass | Expected fail-closed JSON: `NOT_CONFIGURED`, `CI_EVIDENCE_NOT_AVAILABLE`, Phase 2C leaf `BLOCKED`. |
| `git diff --check` | 0 | PASS after EOF whitespace fix; Git reported only existing LF-to-CRLF working-copy warnings. |
| `git diff --exit-code origin/main -- ai/command-registry.json` | 0 | PASS: no command registry change or `VERIFIED` promotion. |
| artifact checks | 0 | `.ai-runs`: absent; non-fixture `artifact-manifest.json`: 0; non-fixture `run.json`: 0. |

## Current CI/Native Status

- Required CI check: `phase-3b-ci-gates` workflow file exists.
- Durable CI evidence: `NOT_CONFIGURED` until a retained GitHub Actions run supplies run ID, job ID, attempt, commit SHA, task/gate correlation, native adapter digest, bypass event-set digest, and resolution IDs.
- CI native adapter installation: `NOT_CONFIGURED` / `REMOTE_NATIVE_ADAPTER_NOT_INSTALLED`.
- Remote runner evidence: `NOT_CONFIGURED` and completion-blocking for CI evidence claims.
- Local `codex-desktop` native host: still `null` / `UNPROBED`; COMMAND, FILE_READ, SEARCH, TOOL_CALL remain `UNSUPPORTED`.

## Independent Review

- Requested from subagent reviewer `Plato`; result pending at this log update.
## Independent Review Result

Independent reviewer `Plato` reported one Critical and two Important findings.
The Critical finding was valid: repository-authored status flags could
previously make `ci_evidence_gate()` return `PASS` without retained run identity
or artifacts. The fix adds regression coverage and requires `retainedRun`, exact
binding names, matching `taskKey`/`gateInvocationId`, and existing artifact refs
before any `PASS` path can proceed.

Important findings were also addressed:

- The GitHub Actions workflow now writes `phase3b-ci-gate-result.json` and uploads
  it with `ai/ci-capability-status.json` using 90-day artifact retention. The job
  treats the current expected `NOT_CONFIGURED` evidence state as a validated
  fail-closed result rather than an infrastructure crash.
- `ai/schemas/ci-gate-result.schema.json` now constrains CI result data instead
  of accepting arbitrary objects.

Post-review verification:

| Command | Exit | Result |
| --- | ---: | --- |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v` | 0 | PASS: 5 tests. |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v` | 0 | PASS: 100 tests. |
| `C:\Program Files\Git\bin\bash.exe scripts/ai/ci-evidence-gate.sh --task-key issue-12 --gate-invocation-id local-static --output -` | non-pass | Expected fail-closed JSON: `NOT_CONFIGURED`, `CI_EVIDENCE_NOT_AVAILABLE`, Phase 2C leaf `BLOCKED`. |

## GitHub Actions Follow-up (2026-07-14)

PR #13 workflow run `29258536257` failed in `Run contract tests` after the
100-test predecessor suite passed. The contract harness intentionally puts
`/usr/bin` first, so it selected Ubuntu's distribution `jsonschema` instead of
the `actions/setup-python` interpreter that received the workflow's pip
dependencies. The older validator failed while resolving the project-state
schema with `TypeError: unhashable type: 'dict'`.

The workflow now pins `jsonschema==4.25.1` and `cryptography==45.0.5` into both
the setup-python interpreter and the `/usr/bin/python3` interpreter exercised
by the shell contracts. Evidence evaluation uses `!cancelled()` so an earlier
test failure still produces fail-closed diagnostic evidence without delaying a
cancelled run. Wrapper fallback JSON is promoted to the result path, and the
named evidence artifact is uploaded only when both the gate result and
repository capability status exist; missing files are an upload error. This
installs CI helper dependencies only; it does not change the native adapter
status from `NOT_CONFIGURED`.

| Command | Exit | Result |
| --- | ---: | --- |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests.test_ci_workflow_provisions_contract_runtime_and_retains_failure_evidence -v` before workflow fix | 1 | RED: contract runtime provisioning command was absent. |
| same targeted command after workflow fix | 0 | GREEN: runtime provisioning order and failure-evidence retention are enforced. |
| `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v` | 0 | PASS: 101 tests. |
| `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/run-contract-tests.sh` | 0 | PASS: runtime preflight and thin closed command shell contracts. |

Follow-up reviewer `Newton` found no Critical issues and two Important issues:
partial artifact publication and under-specified provisioning assertions. Both
were fixed with fallback result capture, complete-bundle upload conditions,
exact two-interpreter package-pin assertions, and a runtime import/version probe
in the workflow. Minor cancellation and stale timestamp findings were also
addressed. The actual rerun on `ubuntu-latest` remains required before this
follow-up can be considered ready to merge.
