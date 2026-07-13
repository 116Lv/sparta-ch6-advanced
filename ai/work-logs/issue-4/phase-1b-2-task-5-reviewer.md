---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-task-5-security-persistence-reviewer
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: phase-1b-2-task-5-security-persistence-reviewer
started_at: 2026-07-11T23:48:00+09:00
ended_at: 2026-07-12T01:37:54+09:00
last_updated: 2026-07-13T08:54:37+09:00
branch: main
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/schemas/process-attempt.schema.json
  - ai/schemas/command-result.schema.json
  - ai/schemas/run-session.schema.json
  - ai/work-logs/issue-4/phase-1b-2-task-5-bounded-redaction-brief.md
  - ai/work-logs/issue-4/phase-1b-2-task-5-implementation-agent.md
findings:
  critical: 0
  important: 0
  minor: 0
changed_files:
  - ai/work-logs/issue-4/phase-1b-2-task-5-reviewer.md
commands_run:
  - "Static review only; no tests or implementation commands were run."
tests_run:
  - "Accepted implementation evidence recorded in the preserved review body."
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

# Phase 1B-2 Task 5 Persistence/Outcome Review

## Verdict

**FAIL. Status: IN_REVIEW. Findings: Critical 0, Important 3, Minor 0.**

Owning feature: none. This is repository-wide AI workflow enforcement. Task 5 must not hand off to Task 6 until the findings below are resolved and independently rereviewed.

## Findings

### I1. Collision and second-terminal POST data can report a contradictory child exit

`post_command_data` copies `processExitCode` from the newly supplied process-attempt object before persisted state is inspected (`scripts/ai/workflow_helper.py:3672-3692`). On an existing terminal reservation or process-attempt collision, the BLOCKED result returns that supplied value (`scripts/ai/workflow_helper.py:3783-3795`) rather than the immutable winner's exit or null. The race test deliberately installs a winner with exit 9 and submits exit 0, but checks only BLOCKED/status and winner preservation, not returned POST data (`scripts/ai/tests/test_workflow_helper.py:4655-4677`). This violates the exact POST/BLOCKED requirement to preserve a known child exit and permits the gateway response to contradict durable evidence. Return the authoritative persisted exit when it is safely proven; otherwise return null, and assert collision plus second-terminal data precisely.

### I2. Log/result publication does not provide the approved atomic publication boundary

The approved contract requires exclusive temp, fsync, atomic rename, and read-only publication, with no partial/truncated logs (`docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md:20`, `84-97`, `133-135`, `241-243`). Both JSON and byte publishers use `os.link`, not atomic rename (`scripts/ai/workflow_helper.py:2424-2450`, `3532-3558`). `publish_command_result` then publishes stdout, stderr, and command JSON one at a time (`scripts/ai/workflow_helper.py:3627-3668`) with no cleanup or resumable journal. A failure after stdout publication leaves a final-path log even though no terminal result/session transition exists; a chmod failure can leave that final path writable. The failure-order test mocks the whole command-result publisher before any log write, so it does not cover failures after the first log, after the second log, after result publication, or during read-only conversion (`scripts/ai/tests/test_workflow_helper.py:4621-4632`). Implement the approved durable publication sequence or a newly approved equivalent that proves exclusive atomic visibility, cleans temporary/partial logs, and remains safely resumable across each crash point.

### I3. Process-attempt write uncertainty can omit the required event and strand RESERVED

`publish_process_attempt` creates the final artifact before `make_read_only` (`scripts/ai/workflow_helper.py:3589-3624`). If read-only conversion raises `EvidenceWriteUncertainty`, `post_command` has not yet set `process_published = True`, so its uncertainty handler does not append `UNSCRUBBED_EVIDENCE` (`scripts/ai/workflow_helper.py:3689`, `3704-3705`, `3766-3779`). The final-path process attempt can remain present and writable while the reservation stays RESERVED. Recovery only repairs `launchStatus: LAUNCHED` (`scripts/ai/workflow_helper.py:2860-2889`), so the same failure for a schema-valid SPAWN_FAILED attempt is neither terminalized nor recoverable and every retry collides. This misses the approved write-uncertainty event precision and monotonic recovery contract. Cover write failures at each process-attempt publication step, including SPAWN_FAILED, and prove one recoverable terminal outcome or a safely visible RESERVED state that can actually resume.

## Contract Trace

- Exact six execution rows: mapping logic and parameterized happy/failure rows are present (`scripts/ai/workflow_helper.py:3707-3748`; tests `4587-4619`), but FAIL overall because collision and write-failure rows are incomplete as described above.
- Process-attempt-first ordering: PASS for the normal path (`scripts/ai/workflow_helper.py:3704-3749`); later result failure leaves process evidence and RESERVED (`tests:4621-4640`).
- BLOCKED command-result fields: PASS; execution hashes, child exit, and log paths are null (`scripts/ai/workflow_helper.py:3740-3746`; tests `4607-4614`). POST/BLOCKED separately preserves a known exit on the normal UNSCRUBBED row.
- Reservation transition and held lock/session CAS: PASS for normal paths. Publication occurs under the held external lock; process refs append before terminal work; the terminal session replacement uses expected-session CAS (`scripts/ai/workflow_helper.py:3693-3705`, `3750-3765`; `2793-2828`).
- Publication failure, collision, race, resume, second terminal: FAIL due I1-I3. Normal process-first failure stays RESERVED and launched recovery can repair BLOCKED, but intermediate artifact and spawn-failure windows are not fully safe.
- `UNSCRUBBED_EVIDENCE` precision: PASS for redaction uncertainty and command-result write uncertainty after process publication, and generic collision emits no event (`scripts/ai/workflow_helper.py:3712-3717`, `3766-3775`; tests `4642-4653`). FAIL for pre-return process-attempt write uncertainty per I3.
- No false PASS: PASS in inspected branches; PASS is returned only after result publication and terminal session replacement (`scripts/ai/workflow_helper.py:3720-3723`, `3749-3765`).
- Standalone POST launch isolation: PASS; `post_command` has no launch edge, and the outcome test patches `Popen` and asserts zero calls (`tests:4601-4619`).
- Task 6 / Phase 1B-3 boundary: PASS. `command-runner.sh` and `workflow-gate.sh` are absent; Task 5 does not create `artifact-manifest.json` or `run.json` (`tests:4679-4697`).

## Accepted Historical Evidence

- Focused Task 5: `Ran 12 tests`; `OK`.
- Full helper: `Ran 191 tests`; `OK (skipped=15)`.
- Runtime preflight: `PASS: runtime preflight contract`.
- Repository-root `.ai-runs`: absent. Staged index: `0`.
- No tests, helper commands, or project commands were run by this reviewer. Static read-only inspection plus this reviewer-log write only.

## Required Resolution

Resolve I1-I3 with focused crash/collision assertions, then request a fresh persistence/outcome rereview. Pending-Issue reconciliation remains required independently of this technical FAIL.

## Remediation Evidence Submitted

**Status remains IN_REVIEW.** The implementation owner submitted remediation evidence; the findings above are not independently closed by this append and Task 6 remains blocked pending rereview.

- Closed execution now owns Popen -> bounded scrubber -> process-attempt -> POST. Raw or oversized caller PASS/FAIL evidence is rejected before process publication.
- Lifecycle evidence covers exact 3600 seconds, process-group termination failure, descendant-held pipe closure, bounded future/drain completion, and exact TIMED_OUT/RESOURCE_LIMIT mapping.
- Streaming evidence covers exact readBytes=65536, carryBytes=8192, 1 MiB/2 MiB caps, pending-sensitive overflow, and every fixed assignment class including access_token, passwd, secret, private_key, and credential.
- Persistence evidence covers process faults after temp, chmod, rename, and session for LAUNCHED and SPAWN_FAILED; each uncertainty emits one UNSCRUBBED_EVIDENCE event and retries to a non-RESERVED terminal state.
- Terminal evidence covers faults after stdout, stderr, result, chmod, and before session; no partial finals remain after handled failure, and the deterministic journal resumes then clears after terminal session publication.
- Collision evidence asserts persisted exit 0 over contradictory caller exit 7, valid race winner exit 9, and null for malformed/unprovable persisted evidence.
- Focused Task5: Ran 34 tests; OK (skipped=1).
- Full helper via exact Git Bash: Ran 201 tests; OK (skipped=15).
- Runtime preflight: exact PASS: runtime preflight contract.
- Static graph: only launch_reserved owns Popen; only execute_command calls launch, capture, and POST.
- .ai-runs, Task6 shells, manifest, and run.json are absent; staged index is 0.
- Product/Gradle/server/Docker/API/DB/migration/seed/infrastructure commands were not run.

## Journal Retry Remediation Submitted For Independent Rereview

**Status remains IN_REVIEW.** This is implementation-owner evidence only. It does not independently close I1-I3, change the finding counts, approve Task 5, or authorize Task 6.

- Strict leftover-journal RED: `Ran 1 test`; `FAILED (failures=2)` for both post-session crash variants.
- The submitted fix reconciles an exact committed terminal tuple under the run lock, verifies journal/final digests, rereads and identity-checks the journal before unlink, fsyncs the state directory, and never deletes immutable finals.
- Regression coverage now requires zero Task 5 temp/journal transactions after successful LAUNCHED/SPAWN_FAILED and terminal crash-point retry/resume. A conflicting journal winner is preserved together with final bytes and exact session bytes.
- Journal cleanup/collision focus: `Ran 4 tests`; `OK`, plus dedicated collision-winner regression: `Ran 1 test`; `OK`.
- Full consolidated Task 5 classes: `Ran 36 tests`; `OK (skipped=1)`.
- Exact Git Bash full helper: exit `0`; `Ran 203 tests`; `OK (skipped=15)`.
- Exact Git Bash runtime preflight: exit `0`; exact output `PASS: runtime preflight contract`.
- Focused static orchestration tests: `Ran 2 tests`; `OK`.
- Static graph: `Popen owners=['launch_reserved']`; `launch_reserved callers=['execute_command']`; `capture_and_scrub callers=['execute_command']`; `post_command callers=['execute_command']`.
- Repository-root `.ai-runs`: absent. Task 6 shells: absent. `artifact-manifest.json`: `0`. `.ai-runs/**/run.json`: `0`. Staged index: `0`.
- `git diff --check`: exit `0`; only inherited LF-to-CRLF warnings for `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md`.
- Product/Gradle/server/Docker/API/DB/migration/seed/infrastructure commands were not run.

Fresh independent security/persistence rereview remains required. Reviewer status stays `in_review`.

## Fresh Independent Persistence/Outcome Rereview

### Final Verdict

**PASS. Status: DONE. Findings: Critical 0, Important 0, Minor 0.**

Owning feature: none. Task 5 is technically clean and may hand off to Task 6. Pending-Issue reconciliation remains required independently and does not change this technical verdict.

### Finding Closure

- **C refs: PASS (0 open).** No critical finding was identified in the prior review or this fresh rereview.
- **I1: PASS.** Collision, race, and second-terminal responses derive `processExitCode` from a schema-valid persisted process attempt when provable and otherwise return null (`scripts/ai/workflow_helper.py:4130-4144`, `4177-4182`, `4270-4285`). Tests assert persisted exit 0 over contradictory caller exit 7, race winner exit 9, malformed evidence null, exact session preservation, and no false PASS (`scripts/ai/tests/test_workflow_helper.py:4815-4853`).
- **I2: PASS.** stdout, stderr, and result publication uses same-directory fsynced staging, chmod before visibility, atomic no-replace rename, deterministic digest journal, cleanup of handled partial finals, and terminal session CAS under the held lock (`scripts/ai/workflow_helper.py:3777-3823`, `3887-4110`, `4228-4248`). Pre-session faults after chmod/stdout/stderr/result roll back finals and resume from the journal; post-session faults preserve committed read-only finals, then validate the exact committed session/result/process tuple and exact log/result references, verify final digests against the journal, reread and identity-check the journal, unlink only that journal, and fsync its directory (`scripts/ai/workflow_helper.py:3934-4054`; tests `4903-5023`). Conflicting journal winners and immutable final/session bytes are preserved.
- **I3: PASS.** Process attempts are schema/tuple validated, fsynced and chmodded before atomic publication, appended to the session with held-lock CAS, and cleaned on handled pre-session faults (`scripts/ai/workflow_helper.py:3838-3884`). Fault coverage spans temp, chmod, rename, and session steps for both `LAUNCHED` and `SPAWN_FAILED`; each uncertainty emits one `UNSCRUBBED_EVIDENCE`, retry reaches a non-RESERVED terminal state, and no Task 5 publication transaction remains (`scripts/ai/tests/test_workflow_helper.py:4866-4901`).
- **M refs: PASS (0 open).** No minor finding was identified.

### Contract Trace

- **Exact six outcome rows: PASS.** Spawn failure, scrubbed exit 0, scrubbed nonzero exit, timeout/resource limit, redaction uncertainty, and later terminal-publication failure map exactly to the approved process/result/reservation/POST rows. BLOCKED command results keep execution hashes, exit, and log fields null; POST preserves a known process exit only where the closed POST contract permits it (`scripts/ai/workflow_helper.py:4186-4227`; tests `4745-4779`, `4781-4800`).
- **Process-first ordering, held lock, CAS, and refs: PASS.** POST acquires and validates the external lock, publishes and session-references the exact process tuple first, publishes terminal evidence, then performs one expected-session terminal replacement. PASS is returned only after terminal publication and session commit (`scripts/ai/workflow_helper.py:4173-4184`, `4228-4250`; `2987-3026`).
- **Atomic/resumable publication and cleanup: PASS.** Journal bytes are exclusively written and fsynced; final files are fsynced and read-only before visibility; handled pre-commit faults remove matching partial finals; committed retries require exact tuple/reference/digest agreement before journal deletion and state-directory fsync. Chmod, each final rename, before-session, after-session, cleanup-failure, collision, and retry paths are covered (`scripts/ai/workflow_helper.py:1858-1879`, `3907-4110`; tests `4903-5023`).
- **No false PASS and collision preservation: PASS.** Evidence/write uncertainty and post-launch publication failure do not become PASS before terminal commit. Authoritative collision data cannot contradict durable evidence, and conflicting journals/finals/session bytes are not overwritten or deleted.
- **Task 6 / Phase 1B-3 boundary: PASS.** Repository-root `.ai-runs`, `command-runner.sh`, `workflow-gate.sh`, `test-command-runner.sh`, `artifact-manifest.json`, and `.ai-runs/**/run.json` are absent; staged index count is 0. No Task 6 shell or Phase 1B-3 finalization/manifest behavior is present.

### Accepted Evidence

- Focused Task 5: `Ran 36 tests`; `OK (skipped=1)`.
- Full helper: `Ran 203 tests`; `OK (skipped=15)`.
- Runtime preflight: `PASS: runtime preflight contract`.
- Repository-root `.ai-runs`: absent. Staged index: `0`.
- This reviewer ran no tests, helper commands, project commands, product commands, staging, or commits. Review activity was read-only static inspection plus this reviewer-log update.

## Final Redaction Rereview Remediation Submitted

**Status: IN_REVIEW. Findings pending fresh adjudication: Critical 0, Important 2, Minor 0.** The prior PASS above is historical. This remediation evidence does not close either current finding, approve Task 5, or authorize Task 6.

### Current Finding 1: Lifecycle Bound

- Confirmed RED: `Ran 5 tests`; `FAILED (failures=1, errors=3, skipped=1)`. Both child-alive final-wait cases leaked raw `subprocess.TimeoutExpired`; the bounded scrubbed sink was absent; exact raw-at-cap input returned expanded scrubbed evidence above the cap. The real POSIX descriptor regression skipped on Windows.
- `execute_command` now creates one absolute monotonic deadline after launch and passes it into capture. Final child wait consumes only the remaining time. A wait timeout invokes the existing identity-checked, bounded TERM/KILL/reap path; timeout or reap failure still creates a `TIMED_OUT/NOT_APPLIED` process attempt and calls POST with no captured logs.
- Real POSIX pipe capture uses `selectors.DefaultSelector`, nonblocking descriptors, and `os.read(..., 65536)`. It does not depend on closing a stream from another thread. The mocked stream path remains available for cross-platform contract tests only.
- Mocked lifecycle/retention GREEN: `Ran 7 tests`; `OK (skipped=1)`. The skip is the capability-gated real POSIX descendant-held pipe regression.

### Current Finding 2: Approved Retention Interpretation

- Adjudicated contract interpretation: spec line 281 forbids **unbounded** in-memory capture; spec line 299 and plan lines 84-97 explicitly approve 1048576 bytes per stream, 2097152 bytes combined, and 8192 bytes of carry per stream. The contract does not forbid retaining bounded scrubbed bytes needed for later atomic publication. No incompatible no-retention or streaming-publication refactor is warranted.
- The former list of scrubbed fragments was replaced because byte caps did not directly bound per-fragment object overhead. Each stream now retains scrubbed-only bytes in one bounded `bytearray`; a shared locked budget rejects before append when either the 1 MiB stream limit or 2 MiB combined limit would be crossed. Carry remains owned by `BoundedStreamScrubber` and remains at most 8192 bytes.
- Tests prove exact retained stream/combined limits, unchanged retained counts after one-byte-over rejection, bytearray rather than fragment-list retention, and fail-closed redaction expansion where exact-at-cap raw input would produce over-cap scrubbed output. No oversized evidence is returned for publication.

### Submitted Verification

- Consolidated Task 5 launch/redaction/persistence: `Ran 41 tests`; `OK (skipped=2)`. Skips: real POSIX launch and real POSIX descendant-held pipe descriptors, both unavailable on Windows.
- Exact Git Bash full helper: exit `0`; `Ran 208 tests`; `OK (skipped=16)`. The prior 15 host-capability skips remain, plus the new real POSIX pipe regression.
- Exact Git Bash runtime preflight: exit `0`; exact output `PASS: runtime preflight contract`.
- Static graph: `Popen owners=['launch_reserved']`; `launch_reserved callers=['execute_command']`; `capture_and_scrub callers=['execute_command']`; `post_command callers=['execute_command']`.
- `git diff --check`: exit `0`; only inherited LF-to-CRLF warnings for `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md`.
- Final hygiene: repository-root `.ai-runs` absent; staged count `0`; Task 6 shells `0`; `artifact-manifest.json` count `0`; `.ai-runs/**/run.json` count `0`. The Task 5 tree is inherited and untracked, so ordinary `git diff --stat` reports only the pre-existing tracked `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md` changes and cannot render a scoped Task 5 patch. No Task 6, Phase 1B-3, product, staging, or commit command was run.

## Final Comprehensive Read-Only Approval Review

### Verdict

**FAIL. Status: IN_REVIEW. Findings: Critical 0, Important 1, Minor 0.**

Owning feature: none. Task 5 must remain blocked from Task 6 until I1 is resolved and independently rereviewed.

### Findings

#### I1. Exact deadline exhaustion and non-timeout final reap failures can bypass POST and strand RESERVED

`execute_command` correctly creates one deadline and passes it into capture, but when capture returns at or after that deadline it raises a raw `subprocess.TimeoutExpired` before entering the inner handler (`scripts/ai/workflow_helper.py:1851-1859`). The outer handlers accept `ExecutionLifecycleTimeout`, `CaptureResourceLimit`, and `RedactionUncertainty`, not raw `subprocess.TimeoutExpired` (`scripts/ai/workflow_helper.py:1875-1901`). In addition, the final `process.wait(timeout=remaining)` catches only `TimeoutExpired`; an `OSError`/reap failure escapes the same POST boundary. Either path exits after reservation and launch without `post_command`, so the reservation can remain `RESERVED`, violating the required absolute lifecycle outcome.

The current lifecycle tests cover a positive remaining timeout from `process.wait` and a mocked termination/reap failure, but not capture consuming the deadline before the wait or a direct final-wait reap error (`scripts/ai/tests/test_workflow_helper.py:4309-4368`). Convert every deadline-exhausted/final-wait failure into the bounded termination path and `ExecutionLifecycleTimeout`, then assert exactly one POST/BLOCKED call with `TIMED_OUT/NOT_APPLIED` facts and no captured logs.

### Contract Trace

- **C refs: PASS (0 open).** No critical finding was identified.
- **I refs: FAIL (1 open).** I1 prevents lifecycle approval and leaves a reachable RESERVED-stranding path.
- **M refs: PASS (0 open).** No minor finding was identified.
- **Bounded POSIX capture: PASS.** Real POSIX pipes use `selectors.DefaultSelector`, nonblocking descriptors, and 65536-byte `os.read`; descendant-held descriptors are bounded by the lifecycle deadline (`scripts/ai/workflow_helper.py:525-581`; tests `4768-4805`). The mocked fallback bounds future waits, closes streams, and limits drain time (`scripts/ai/workflow_helper.py:583-620`; tests `4603-4621`).
- **Streaming/caps/redaction: PASS.** The scrubber retains 8192 bytes of carry, uses scrubbed-only bounded bytearrays, and enforces 1048576 bytes per stream and 2097152 combined before append, including redaction expansion (`scripts/ai/workflow_helper.py:206-236`, `290-412`, `444-492`; tests `4589-4766`). No public secret source is read.
- **Closed orchestration/forgery boundary: PASS.** `launch_reserved` is the only `Popen` owner; `execute_command` is its only caller and owns capture plus POST. POST accepts PASS/FAIL logs only as sealed scrubber evidence; raw or oversized caller evidence is rejected before process publication (`scripts/ai/workflow_helper.py:1687-1697`, `1781-1901`, `4282-4307`; tests `4460-4477`, `4983-4992`).
- **Atomic/resumable terminal evidence: PASS.** Process facts and terminal artifacts use fsynced staging, read-only-before-visibility publication, deterministic journals, rollback/resume, authoritative collision exits, and one locked terminal session transition (`scripts/ai/workflow_helper.py:3913-4020`, `4043-4247`, `4266-4434`; tests `4874-5166`). LAUNCHED and SPAWN_FAILED uncertainty paths are covered and do not falsely PASS.
- **Task 6 / Phase 1B-3 boundaries: PASS.** Task 6 shell entry points, manifest publication, and `run.json` remain absent. Repository-root `.ai-runs` is absent and staged index count is 0.

### Accepted Evidence

- RED5 failed as expected.
- GREEN7: `OK (skipped=1)`.
- Task 5: `Ran 41 tests`; `OK (skipped=2)`.
- Full helper: `Ran 208 tests`; `OK (skipped=16)`.
- Runtime preflight: `PASS: runtime preflight contract`.
- Repository-root `.ai-runs`: absent. Staged index: `0`.
- This reviewer ran no tests, helper commands, project commands, product commands, staging, or commits. Review activity was read-only static inspection plus this reviewer verdict/status update.

## Final Wait Lifecycle Remediation Evidence

### Status

**Status: IN_REVIEW. Findings pending fresh independent adjudication: Critical 0, Important 1, Minor 0.** The implementation evidence below does not self-close I1, approve Task 5, or authorize Task 6.

### Submitted Remediation

- Strict focused RED: exit `1`; `Ran 3 tests`; `FAILED (errors=3)`. Exact capture-deadline exhaustion leaked raw `subprocess.TimeoutExpired`, direct final wait leaked `OSError`, and another final-wait exception leaked `RuntimeError`, all before POST.
- The focused tests now wrap the real POST persistence path. Each requires execute to return `POST_COMMAND/BLOCKED` without leaking, POST exactly once, one terminal BLOCKED reservation, durable `TIMED_OUT/NOT_APPLIED` process facts, no published logs, null BLOCKED command-result execution/log fields, and no false PASS. The non-timeout exception case also requires authoritative exit `9` to remain in the process attempt.
- Final wait handling is centralized behind `wait_for_process_exit`. Deadline exhaustion, timeout, direct wait/reap exceptions, and unavailable status close as `ExecutionLifecycleTimeout`. The helper first preserves a safely proven integer exit; while the child remains unproven it uses the existing bounded identity-checked process-group termination path.
- Timeout/resource and redaction orchestration use the same safe authoritative-exit probe, preventing a secondary `poll()` error from reopening the lifecycle boundary.

### Submitted Verification

- Focused GREEN: exit `0`; `Ran 3 tests`; `OK`.
- Launch/lifecycle and redaction focus: exit `0`; `Ran 31 tests`; `OK (skipped=2)`.
- Consolidated Task 5 launch/redaction/persistence classes: exit `0`; `Ran 44 tests`; `OK (skipped=2)`.
- Exact Git Bash full helper: exit `0`; `Ran 211 tests`; `OK (skipped=16)`.
- Exact Git Bash runtime preflight: exit `0`; exact output `PASS: runtime preflight contract`.
- In-memory syntax compile: `PASS`. Static call graph: `Popen owners=['launch_reserved']`; `launch_reserved callers=['execute_command']`; `capture_and_scrub callers=['execute_command']`; `post_command callers=['execute_command']`.
- Hygiene: repository-root `.ai-runs` absent; staged count `0`; Task 6 shells `0`; `artifact-manifest.json` count `0`; `.ai-runs/**/run.json` count `0`.
- `git diff --check`: exit `0`; inherited LF-to-CRLF warnings only for `.gitignore`, `AGENTS.md`, and `ai/work-logs/index.md`. The Task 5 tree remains inherited and untracked, so ordinary `git diff --stat` still reports only those three pre-existing tracked files.

Fresh independent lifecycle/security/persistence rereview remains required. Reviewer status remains `in_review`.

## Final Decisive Read-Only Rereview

### Verdict

**PASS. Status: DONE. Findings: Critical 0, Important 0, Minor 0.**

Owning feature: none. Task 5 is technically clean and may hand off to Task 6. Pending-Issue reconciliation remains required independently and does not change this technical verdict.

### Finding Closure

- **C refs: PASS (0 open).** No Critical finding is present in the final Task 5 implementation.
- **I1: PASS.** One absolute deadline covers capture and final child wait. `wait_for_process_exit` converts exact deadline exhaustion, `TimeoutExpired`, every direct final `wait()` exception, and unavailable exit status into `ExecutionLifecycleTimeout`; it preserves only a safely proven integer exit and invokes bounded identity-checked process-group termination while exit remains unknown (`scripts/ai/workflow_helper.py:1734-1771`, `1891-1908`). The real-POST regressions prove deadline-boundary, `OSError`, and other final-wait exceptions return POST_COMMAND/BLOCKED, call POST exactly once, create exactly one terminal BLOCKED reservation, persist `TIMED_OUT/NOT_APPLIED` process facts, publish no logs, keep BLOCKED command-result execution/log fields null, preserve authoritative exit 9 only in process-attempt facts, and never falsely PASS (`scripts/ai/tests/test_workflow_helper.py:4877-4959`). No reachable final-wait path strands the reservation in RESERVED.
- **M refs: PASS (0 open).** No Minor finding is present.

### Regression Trace

- **Selectors and fallback: PASS.** Real POSIX pipes use `DefaultSelector`, nonblocking descriptors, and bounded 65536-byte `os.read`; the cross-platform fallback uses two bounded futures, closes streams on timeout, and bounds drain completion (`scripts/ai/workflow_helper.py:525-621`; `scripts/ai/tests/test_workflow_helper.py:4770-4807`).
- **Carry and retained caps: PASS.** The scrubber retains exactly bounded 8192-byte carry; scrubbed output is retained in bytearrays under exact 1048576-byte per-stream and 2097152-byte combined pre-append caps, including redaction expansion (`scripts/ai/workflow_helper.py:206-236`, `270-412`, `444-492`; `scripts/ai/tests/test_workflow_helper.py:4591-4649`).
- **Closed execution/capture/POST graph: PASS.** `launch_reserved` is the only `Popen` owner; `execute_command` is its only caller and the only caller of capture plus POST. Standalone POST does not launch (`scripts/ai/workflow_helper.py:1687-1697`, `1821-1924`, `4305-4457`).
- **Persistence and lifecycle: PASS.** Process-attempt-first publication, fsynced read-only-before-visibility terminal staging, atomic no-replace publication, deterministic journal resume/cleanup, collision preservation, authoritative POST data, one held-lock terminal transition, and no false PASS remain intact (`scripts/ai/workflow_helper.py:3997-4270`, `4289-4457`; `scripts/ai/tests/test_workflow_helper.py:4961-5228`). Later publication uncertainty remains visibly RESERVED only where explicit recovery owns terminalization; final-wait failures now reach normal BLOCKED terminal publication.
- **Task 6 / Phase 1B-3 boundary: PASS.** `command-runner.sh`, `workflow-gate.sh`, `test-command-runner.sh`, repository `artifact-manifest.json`, and `.ai-runs/**/run.json` are absent. No finalization, manifest publication, registry transition, or done-claim behavior was introduced.

### Accepted Evidence

- RED3: exit `1`; `Ran 3 tests`; expected `errors=3` for the three formerly escaping final-wait paths.
- GREEN3: exit `0`; `Ran 3 tests`; `OK`.
- Lifecycle/redaction focus: exit `0`; `Ran 31 tests`; `OK (skipped=2)`.
- Consolidated Task 5: exit `0`; `Ran 44 tests`; `OK (skipped=2)`.
- Full helper: exit `0`; `Ran 211 tests`; `OK (skipped=16)`.
- Runtime preflight: exit `0`; exact `PASS: runtime preflight contract`.
- Static hygiene reconfirmed read-only: repository-root `.ai-runs` absent; staged index count `0`; Task 6 shells, published manifest, and run JSON count `0`.
- This reviewer ran no tests, helper commands, project commands, product commands, staging, or commits. Review activity was read-only static inspection plus this reviewer-log verdict/status update.
