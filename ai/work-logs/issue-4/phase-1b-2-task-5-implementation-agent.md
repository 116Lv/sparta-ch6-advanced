---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-task-5-implementation-agent
tracking_status: issue_backed
status: in_review
owning_feature: "none"
current_owner: phase-1b-2-task-5-security-persistence-reviewer
started_at: 2026-07-11T00:00:00Z
ended_at: 2026-07-11T14:54:37Z
last_updated: 2026-07-13T09:32:29+09:00
branch: main
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - ai/work-logs/issue-4/phase-1b-2-task-5-bounded-redaction-brief.md
changed_files:
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/fixtures/phase-1b/execution/redaction-classes.json
  - ai/fixtures/phase-1b/execution/invalid-utf8.bin
  - ai/fixtures/phase-1b/execution/empty.stdout.log
  - ai/fixtures/phase-1b/execution/empty.stderr.log
  - ai/work-logs/issue-4/phase-1b-2-task-5-implementation-agent.md
commands_run:
  - "Inherited full RED: 190 tests; 48 expected missing-interface errors; 15 skips."
  - "Inherited focused POST persistence: 5 tests; all passed."
  - "Inherited latest combined focused run: 12 tests; 10 passed; 2 failed only for password=\"\" and api_key=''."
  - "python -m unittest scripts.ai.tests.test_workflow_helper.BoundedRedactionTests.test_assignment_quotes_are_retained_and_sensitive_value_bounds_are_exact -v (RED exit 1; GREEN exit 0)"
  - "python -m unittest scripts.ai.tests.test_workflow_helper.BoundedRedactionTests scripts.ai.tests.test_workflow_helper.PostCommandPersistenceTests -v (exit 0)"
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/run-helper-tests.sh (exit 0)"
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/tests/test-runtime-preflight.sh (exit 0)"
  - "python -m unittest scripts.ai.tests.test_workflow_helper.PosixLaunchTests.test_popen_reachability_is_closed_to_execute_command -v (exit 0)"
  - "git diff --check (exit 0; inherited LF-to-CRLF warnings only)"
  - "Repository .ai-runs, Task 6 entry-point, deferred-artifact, staged-index, and git status inspections."
tests_run:
  - "Inherited Task 5 full RED: 190 tests; 48 expected missing-interface errors; 15 skips."
  - "Inherited POST persistence focused: 5/5 passed."
  - "Inherited combined focused: 12 tests; 10 passed; 2 failures only for empty quoted assignments."
  - "Empty quoted assignment RED reproduction: Ran 1 test; FAILED with 2 subtest failures because RedactionUncertainty was not raised."
  - "Empty quoted assignment focused GREEN: Ran 1 test; OK."
  - "Full Task 5 focused suite: Ran 12 tests; OK."
  - "Full helper through exact Git Bash: Ran 191 tests; OK (skipped=15)."
  - "Runtime preflight through exact Git Bash: PASS: runtime preflight contract."
  - "Static Popen reachability: Ran 1 test; OK."
blockers: []
historical_blockers:
  - "GitHub Issue creation remains blocked by the recorded integration 403; fallback reconciliation is still required."
  - "The approved plan requires a fresh security/persistence reviewer checkpoint before Task 6."
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

# Phase 1B-2 Task 5 Implementation Log

## Routing And Boundary

Owning feature is `none`. Work is limited to approved Phase 1B-2 Task 5 owned files. Prior reviewer logs, product code, Task 6 shells, and Phase 1B-3 finalization remain untouched.

## TDD Record

The inherited full RED ran 190 tests with 48 expected missing-interface errors and 15 environment skips. The inherited POST persistence focus was 5/5 PASS. The latest inherited combined Task 5 run exercised 12 tests and had only two failures: `password=""` and `api_key=''` did not raise `RedactionUncertainty`.

The focused reproduction failed with exactly those two subtest failures. Root cause: the quoted assignment branches required one or more characters, so empty quotes fell through to the unquoted branch; the quote delimiters were then treated as a non-empty value. The bounded production fix allows the quoted branches to capture an empty candidate, after which the existing shared `_bounded_value` guard rejects it. No test exception or redaction weakening was added.

The focused empty-assignment test then passed, followed by all 12 Task 5 focused tests.

## Work Done

- Implemented bounded concurrent capture, strict incremental UTF-8 handling, fixed-class and injected-literal redaction, exact byte limits, and fail-closed uncertainty behavior.
- Implemented process-attempt-first immutable POST persistence, exact PASS/FAIL/BLOCKED outcome mapping, scrubbed log publication, terminal reservation transitions, collision handling, and precise `UNSCRUBBED_EVIDENCE` events.
- Corrected empty quoted assignment handling through the common candidate-bound check.
- Added the four approved Task 5 execution fixtures and no Task 6 or Phase 1B-3 artifacts.

## Verification

- Focused empty quoted assignments: exit `0`; `Ran 1 test`; `OK`, including both formerly failing subtests.
- Full Task 5 focus: exit `0`; `Ran 12 tests`; `OK`. This covers every redaction boundary and all six exact POST outcome rows.
- Full helper through exact `C:\Program Files\Git\bin\bash.exe`: exit `0`; `Ran 191 tests`; `OK (skipped=15)`.
- The 15 skips are the suite's declared host-capability cases: one real POSIX launch, symlink availability cases, and safe POSIX FIFO coverage. All mocked cross-platform contracts ran.
- Runtime preflight through exact Git Bash: exit `0`; exact output `PASS: runtime preflight contract`.
- Static `Popen` reachability test: exit `0`; `Ran 1 test`; `OK`; launch remains reachable only through `execute_command` and its sole `launch_reserved` owner.
- No-secret-read proof passed with `builtins.open` forced to fail during public scrubber capture; public literals remain empty and internal literals remain bounded.
- No-truncated-publication proof passed through exact/over-cap capture plus the outcome table: over-cap capture raises uncertainty, and RESOURCE_LIMIT/BLOCKED results publish null execution/log fields.
- Task 6 entry points `command-runner.sh`, `workflow-gate.sh`, and `test-command-runner.sh` are absent. No manifest, `run.json`, finalization, or done-claim publication was added.
- Repository-root `.ai-runs` is absent. Staged files: `0`.
- `git diff --check`: exit `0`, with inherited LF-to-CRLF warnings only for `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md`.

## Historical State At Execution

Task 5 implementation and local contract verification are GREEN. Status remains `in_review` for the plan-required fresh security/persistence reviewer. Pending-Issue reconciliation remains required.

## Product Commands

NOT RUN: Gradle, build, product/unit project tests, application server, Docker Compose, HTTP/API, database, migration, seed, and infrastructure commands.

## Historical Next Handoff

- Next role: Phase 1B-2 Task 5 security/persistence reviewer.
- Review the bounded redaction completeness, carry/candidate limits, no-secret-read boundary, no-truncated-publication behavior, immutable publication ordering, event precision, exact outcome table, and Task 6/Phase 1B-3 deferrals.
- Preserve all prior approved work and reviewer logs; do not begin Task 6 until this checkpoint approves Task 5.

## Security And Persistence Remediation

Status remains in_review. Owning feature remains none; this is repository-wide AI workflow enforcement. No Task 6, Phase 1B-3, product, schema, Task1-4 reviewer-log, staging, or commit work was performed.

### Exact RED

- Closed orchestration/exact limits/streaming carry/assignment classes: Ran 5 tests; first RED FAILED (failures=9). After correcting the test-only secret= key assertion, the valid RED was Ran 5 tests; FAILED (failures=8).
- Lifecycle timeout: Ran 1 test; FAILED (errors=1) because EXECUTION_TIMEOUT_SECONDS was absent.
- Persistence/collision/fault focus: Ran 5 tests; FAILED (failures=18).
- Timeout/resource outcome mapping plus exact 65536/8192 boundary: Ran 2 tests; FAILED (errors=1) because ExecutionLifecycleTimeout was absent; the already-implemented exact boundary assertion passed.

### Exact GREEN

- Closed orchestration, exact limits, real 8192-byte carry, all assignment classes, and bounded lifecycle: Ran 7 tests; OK.
- Persistence/collision/fault focus: Ran 5 tests; OK.
- Exact timeout/resource outcome mapping and 65536/8192 boundary: Ran 2 tests; OK.
- Full Task5-owned launch/redaction/persistence classes: Ran 34 tests; OK (skipped=1). The skip is the declared real-POSIX-launch host case.
- Full helper through exact C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh: exit 0; Ran 201 tests; OK (skipped=15).
- Runtime preflight through exact Git Bash: exit 0; exact output PASS: runtime preflight contract.
- Static Popen/capture graph: Popen owners=['launch_reserved']; launch_reserved callers=['execute_command']; capture_and_scrub callers=['execute_command']; post_command callers=['execute_command'].

### Remediation Result

- execute_command now owns launch, bounded capture/drain, exact timeout/resource mapping, process-attempt creation, and POST publication. Standalone POST accepts no raw PASS/FAIL bytes.
- The scrubber emits during streaming, retains at most the exact 8192-byte carry, requests exact 65536-byte reads, and fails at pending-sensitive overflow.
- Process artifacts stage and fsync before read-only atomic no-replace rename, resume exact matching artifacts, and emit one UNSCRUBBED_EVIDENCE event for injected uncertainty in both LAUNCHED and SPAWN_FAILED paths.
- Terminal logs/result use a deterministic resumable journal, read-only staging before visibility, handled-fault cleanup with no partial finals, and journal removal only after the terminal session transition.
- Collision/second-terminal POST data returns the validated persisted process exit when provable and null for malformed/unprovable evidence.
- Repository .ai-runs: absent. Task6 shells: absent. artifact-manifest.json: 0. .ai-runs/**/run.json: 0. Staged index: 0.
- git diff --check: exit 0; only inherited LF-to-CRLF warnings for .gitignore, AGENTS.md, and ai/work-logs/index.md.
- Product commands NOT RUN: Gradle, build, product/unit project tests, application server, Docker Compose, HTTP/API, database, migration, seed, and infrastructure.

## Journal Retry Cleanup Remediation

Status remains `in_review`. Owning feature remains `none`. This follow-up changed only the Task 5 helper, helper tests, and the two Task 5 role logs. The redaction fixture was inspected and preserved unchanged. No Task 6, Phase 1B-3, manifest, `run.json`, product, schema, staging, or commit work was performed.

### Strict RED And Root Cause

- The partially applied post-session regression was completed and run directly: `Ran 1 test`; `FAILED (failures=2)`. Both `after_session` and `journal_cleanup` variants proved that a committed PASS session and immutable finals could retain `*.terminal-publication.json` after retry.
- Root cause: `post_command` rejected the already-terminal reservation before reconciling the committed terminal journal, so retry returned authoritative BLOCKED data but never reached durable journal cleanup.

### Minimal Fix And Regression Coverage

- Retry now reconciles only an exact terminal session/result/process tuple while holding the existing run lock. It requires exact committed result and log references, verifies the journal against the immutable final digests, rereads and identity-checks the exact regular journal before unlink, and fsyncs the journal directory after removal.
- Cleanup removes only the validated journal. It never chmods or deletes immutable finals. A conflicting journal winner returns `TERMINAL_PUBLICATION_COLLISION` and preserves the winner, final stdout/stderr/result bytes, and exact session bytes.
- Successful LAUNCHED/SPAWN_FAILED process retry and every terminal crash-point resume assert that no Task 5 temp file, terminal journal, or immutable-publication journal remains.

### Exact Final Evidence

- Journal cleanup/collision focus: `Ran 4 tests`; `OK`, followed by the dedicated journal collision winner regression: `Ran 1 test`; `OK`.
- Full consolidated Task 5 launch/redaction/persistence classes: exit `0`; `Ran 36 tests`; `OK (skipped=1)`. The one skip is the declared real-POSIX-launch host case.
- Exact Git Bash full helper command `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`: exit `0`; `Ran 203 tests`; `OK (skipped=15)`.
- Exact Git Bash runtime preflight command `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`: exit `0`; exact output `PASS: runtime preflight contract`.
- Focused static orchestration tests: `Ran 2 tests`; `OK`.
- Static call graph: `Popen owners=['launch_reserved']`; `launch_reserved callers=['execute_command']`; `capture_and_scrub callers=['execute_command']`; `post_command callers=['execute_command']`.
- Repository-root `.ai-runs`: absent. Task 6 shells: absent. `artifact-manifest.json`: `0`. `.ai-runs/**/run.json`: `0`. Staged index: `0`.
- `git diff --check`: exit `0`; only inherited LF-to-CRLF warnings for `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md`.
- Final hygiene: repository-root `.ai-runs` absent; staged count `0`; Task 6 shells `0`; `artifact-manifest.json` count `0`; `.ai-runs/**/run.json` count `0`. Task 5 files remain in the inherited untracked tree, so ordinary `git diff --stat` shows only the three pre-existing tracked documentation changes.
- Product commands NOT RUN: Gradle, build, product/unit project tests, application server, Docker Compose, HTTP/API, database, migration, seed, and infrastructure.

### Handoff

Task 5 remains `in_review` pending a fresh independent security/persistence rereview. This implementation evidence does not close the reviewer findings or authorize Task 6.

## Final Redaction Rereview Remediation

Status remains `in_review`. Scope remained limited to the Task 5 helper, helper tests, and the two Task 5 logs. No Task 6, Phase 1B-3, product, staging, or commit work was performed.

### Root Cause And RED

- The 3600-second deadline ended at the capture futures. After capture returned because the child had closed its own pipes, `execute_command` used a separate fixed five-second wait whose `TimeoutExpired` was not handled. That exception bypassed POST and could strand RESERVED.
- POSIX capture used blocking stream reads in worker threads. Closing those stream objects from another thread was not a proof that a kernel-level read blocked by descendant-held write descriptors would complete.
- The retained scrubbed output used a list of fragments. Raw input bytes were capped, but fragment-object overhead and redaction expansion were not directly bounded by the publication limits.
- Focused RED: `Ran 5 tests`; `FAILED (failures=1, errors=3, skipped=1)`. The two lifecycle tests errored with raw `subprocess.TimeoutExpired`, the bounded sink class was absent, and expanded scrubbed output did not raise `CaptureResourceLimit`. The POSIX real-pipe regression was skipped on Windows.

### Minimal Contract-Faithful Fix

- One absolute monotonic deadline now covers capture and final child wait. The child wait uses only remaining time; timeout and bounded termination/reap failure are converted to `ExecutionLifecycleTimeout`, then to guaranteed POST `BLOCKED` with `TIMED_OUT/NOT_APPLIED` process facts and no logs.
- POSIX real pipe descriptors use selectors, nonblocking mode, and bounded `os.read` calls. Mock stream objects retain the existing concurrent fallback so the cross-platform contract remains testable.
- Scrubbed retention now uses one bounded bytearray per stream and one shared synchronized combined budget. Append checks happen before retention. The sink contains scrubbed-only output, while the scrubber alone retains at most 8192 bytes of carry.
- Approved interpretation: spec line 281 prohibits unbounded in-memory capture, while spec line 299 and plan lines 84-97 approve explicit 1 MiB-per-stream, 2 MiB-combined, and 8192-byte-carry bounds. Retaining those bounded scrubbed bytes for later atomic publication is permitted and required by the existing publication boundary; no whole-stream prohibition is present.

### GREEN And Regression

- Focused lifecycle/retention GREEN: `Ran 7 tests`; `OK (skipped=1)` for the unavailable real POSIX pipe capability.
- Consolidated Task 5: `Ran 41 tests`; `OK (skipped=2)` for real POSIX launch and real POSIX descendant-held pipe descriptors.
- Exact Git Bash full helper: exit `0`; `Ran 208 tests`; `OK (skipped=16)`.
- Exact Git Bash runtime preflight: exit `0`; exact output `PASS: runtime preflight contract`.
- Static call graph remained closed exactly: `Popen owners=['launch_reserved']`; `launch_reserved callers=['execute_command']`; `capture_and_scrub callers=['execute_command']`; `post_command callers=['execute_command']`.
- `git diff --check`: exit `0`; only inherited LF-to-CRLF warnings for `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md`.

Fresh independent redaction rereview remains required. This remediation does not self-close either current finding or authorize Task 6.

## Final Wait Lifecycle Remediation

Status remains `in_review`. Scope remained limited to the Task 5 helper, helper tests, and the two Task 5 role logs. No Task 6, Phase 1B-3, product, staging, or commit work was performed.

### Strict RED And Root Cause

- Focused RED ran the three new final-wait cases and exited `1`: `Ran 3 tests`; `FAILED (errors=3)`. Capture-at-deadline leaked raw `subprocess.TimeoutExpired`, direct final wait leaked `OSError`, and a non-timeout final wait leaked `RuntimeError`; each escaped before POST.
- Root cause was the split exception boundary in `execute_command`: exact deadline exhaustion raised before the inner timeout handler, while the handler caught only `TimeoutExpired`. The outer lifecycle handlers therefore never received the approved closed `ExecutionLifecycleTimeout` abstraction.
- The tests wrap the real immutable `post_command` path and require one POST call, exactly one terminal BLOCKED reservation, durable `TIMED_OUT/NOT_APPLIED` process facts, null command-result exit/log fields, no log directory, no false PASS, and preservation of an authoritative exit when available.

### Minimal Closed Fix

- `wait_for_process_exit` now owns every final deadline/wait outcome. Exact deadline exhaustion, `TimeoutExpired`, `OSError`, other wait exceptions, and unavailable exit status all close as `ExecutionLifecycleTimeout` consumed by orchestration.
- `authoritative_process_exit` safely checks `poll()` and falls back to an integer `returncode`. A proven exit is preserved; an unproven live child uses the existing identity-checked bounded TERM/KILL/reap path before the lifecycle timeout is published.
- The outer timeout/resource and redaction handlers use the same safe authoritative-exit probe, so secondary poll errors cannot reopen the POST boundary. Legacy success mocks now return the documented integer from `Popen.wait`; production no longer manufactures exit `0` from an invalid wait result.

### GREEN And Requested Evidence

- Focused GREEN: exit `0`; `Ran 3 tests`; `OK`.
- Launch/lifecycle plus redaction focus: exit `0`; `Ran 31 tests`; `OK (skipped=2)` for the declared real-POSIX launch and pipe capabilities.
- Consolidated Task 5 launch/redaction/persistence classes: exit `0`; `Ran 44 tests`; `OK (skipped=2)`.
- Exact Git Bash full helper `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`: exit `0`; `Ran 211 tests`; `OK (skipped=16)`.
- Exact Git Bash runtime preflight `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`: exit `0`; exact output `PASS: runtime preflight contract`.
- In-memory syntax compile: `PASS`. Static call graph remained closed exactly: `Popen owners=['launch_reserved']`; `launch_reserved callers=['execute_command']`; `capture_and_scrub callers=['execute_command']`; `post_command callers=['execute_command']`.
- Final hygiene: repository-root `.ai-runs` absent; staged count `0`; Task 6 shells `0`; `artifact-manifest.json` count `0`; `.ai-runs/**/run.json` count `0`.
- `git diff --check`: exit `0`; only inherited LF-to-CRLF warnings for `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md`. Ordinary `git diff --stat` still shows only those three pre-existing tracked documentation changes because the Task 5 tree remains inherited and untracked.

Task 5 remains `in_review` pending fresh independent lifecycle/security/persistence rereview. This remediation evidence does not self-close the Important finding or authorize Task 6.
