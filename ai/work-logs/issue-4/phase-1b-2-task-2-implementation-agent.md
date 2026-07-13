---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-task-2-implementation-agent
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: phase-1b-2-task-2-implementation-agent
started_at: 2026-07-11T13:14:14+09:00
ended_at: 2026-07-11T15:21:37+09:00
last_updated: 2026-07-13T08:54:37+09:00
branch: main
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - ai/work-logs/issue-4/phase-1b-2-task-2-run-lifecycle-brief.md
changed_files:
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/fixtures/phase-1b/execution/
  - ai/work-logs/issue-4/phase-1b-2-task-2-implementation-agent.md
commands_run:
  - "Focused RunLifecycleTests RED/GREEN commands recorded in the preserved body."
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/run-helper-tests.sh"
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/tests/test-runtime-preflight.sh"
tests_run:
  - "Final helper verification: exit 0; Ran 138 tests; OK (skipped=9)."
  - "Final runtime preflight verification: exit 0; PASS: runtime preflight contract."
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

# Phase 1B-2 Task 2 Implementation Agent

## Routing And Scope

- Owning feature: `none` because this is repository-wide AI workflow infrastructure.
- Scope: approved Phase 1B-2 Task 2 only: `RUN_START`, run locking/recovery history, and stale `RESERVED` repair.
- Prior Task 1 schemas and Phase 1B-1 behavior remain unchanged.

## Initial TDD Evidence (Pre-review)

- status: red
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests.test_start_run_publishes_only_an_open_session_after_current_preflight -v`
  - result: exit `1`; expected `AttributeError` because `start_run` did not exist.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests.test_start_run_publishes_only_an_open_session_after_current_preflight -v`
  - result: exit `0`; `Ran 1 test`; `OK`.
- status: red
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`
  - result: exit `1`; expected `RUN_START` preflight mapping failure (`PREFLIGHT` was returned), then expected missing lock APIs.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`
  - result: exit `0`; `Ran 4 tests`; `OK` after run-start mapping and lock/recovery implementation.
- status: red
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`
  - result: exit `1`; expected session-publication cleanup failure and missing `repair_reserved_attempts` API.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`
  - result: exit `0`; `Ran 7 tests`; `OK` after cleanup and monotonic repair implementation.
- status: red
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests.test_start_run_rejects_invalid_existing_symlinked_and_unsafe_run_paths -v`
  - result: exit `1`; permissive run-directory mode incorrectly returned `PASS`.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`
  - result: exit `0`; `Ran 8 tests`; `OK` after the supported permission guard.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`
  - result: exit `0`; `Ran 87 tests`; `OK (skipped=7)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
  - result: exit `0`; `PASS: runtime preflight contract`.
- status: green
  - command: `git diff --check` and repository `.ai-runs` absence check
  - result: exit `0`; no `.ai-runs` exists at the repository root. Existing CRLF warnings are limited to pre-existing tracked files.

## Implemented Behavior

- `start_run` performs current runtime preflight before every mutation and emits the exact `RUN_START` envelope.
- Run directories and lock directories use exclusive creation, closed owner records, contained paths, schema-validated sessions, same-directory temporary publication, fsync, and restrictive modes when the host supports them.
- A live or recent owner blocks recovery. A dead and expired owner is quarantined, replaced, recorded in immutable session history, and released only after history publication and quarantine cleanup.
- Recovery repairs only an exact, schema-valid, `LAUNCHED` stale process attempt to a `BLOCKED` command result and terminal reservation. Malformed, missing, `SPAWN_FAILED`, mismatched, or contradictory evidence stays `RESERVED`; no process launch is reachable.

## Critical And Important Review Remediation

- status: red
  - command: `python -m unittest` with the five focused stranded-result, session-failure, publication-collision, LAUNCHED-only, and lost-update tests.
  - result: exit `1`; `Ran 5 tests`; `FAILED (failures=5)`.
  - observed defects: stranded valid result remained `RESERVED`; injected session failure was unreachable; collision winner was not preserved; `SPAWN_FAILED` became `BLOCKED`; concurrent session state was overwritten.
- status: red
  - command: `python -m unittest` with the four focused internal-owner, concurrent-acquire, stale-owner-mutation, and failed-history tests.
  - result: exit `1`; `Ran 4 tests`; `FAILED (failures=1, errors=3)`.
  - observed defects: acquire/recovery still required caller-provided owners and lifecycle barriers were absent.
- status: green
  - command: focused five-test repair command from the RED cycle.
  - result: exit `0`; `Ran 5 tests`; `OK`.
- status: green
  - command: focused seven-test owner/recovery collision and concurrency command.
  - result: first run exit `1`, `Ran 7 tests`, one concurrent-recovery failure exposed an ABA race; after adding the exclusive recovery claim, the isolated concurrent-recovery test exited `0`, `Ran 1 test`, `OK`.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`
  - result: exit `0`; `Ran 23 tests`; `OK (skipped=2)`; both skips are the new ancestor-directory symlink tests on this Windows host.
- status: green
  - command: focused compare-release mutation and recovery-session-write fault tests.
  - result: exit `0`; `Ran 2 tests`; `OK`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`
  - result: exit `0`; `Ran 104 tests`; `OK (skipped=9)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
  - result: exit `0`; `PASS: runtime preflight contract`.
- status: green
  - command: `git diff --check`, repository `.ai-runs` absence, forbidden subprocess/`run.json` scan, and staged-file inventory.
  - result: exit `0`; repository-root `.ai-runs` absent; no subprocess or `run.json` path; no staged files. Existing CRLF warnings are limited to pre-existing tracked files. The only `artifact-manifest` helper references remain Task 1 schema allowlisting and validation.

### Remediated Behavior

- Every existing repair-path component is checked with `lstat`; symlink/reparse points, escaped realpaths, and non-exact regular files fail closed. Missing command directories are created one component at a time and rechecked before publication.
- A valid stranded repair result is strictly schema/semantically validated and completes the `RESERVED` transition without overwrite. Malformed or contradictory results remain visible and unchanged.
- Immutable result publication is resumable after session failure. Collision winners are validated, never overwritten or deleted, and session publication uses compare-and-swap to preserve concurrent updates.
- Lock acquire and recovery generate internal UUID4 owners. Compare-release uses the closed non-symlink owner reader and preserves a lock when ownership changes.
- Atomic recovery claims prevent concurrent recovery ABA. Deterministic barriers/faults cover lock acquire/recovery, quarantine and replacement collisions, failed history/session writes, repair collisions/resume, PID permission/reuse, and lost updates.
- Added approved fixtures: `lock-owner-dead-recent.json`, `lock-owner-dead-expired.json`, and `reserved-with-process-attempt.json`.

## Second Important-Finding Remediation

- status: red
  - command: focused three-test lock-required session mutation, post-comparison writer barrier, and owner-mutation command.
  - result: exit `1`; `Ran 3 tests`; `FAILED (failures=1, errors=2)` because `replace_run_session` had no held-lock parameter and no post-comparison barrier.
- status: red
  - command: focused nine-test claim cleanup/recovery, quarantine resume, owner-publication failure, and ownerless recovery command.
  - result: exit `1`; `Ran 9 tests`; `FAILED (failures=5, errors=3)`.
  - observed defects: pre-quarantine claims remained orphaned, expired claims always blocked, exact quarantine resume was absent, owner-write failure left an empty lock, and expired/concurrent ownerless recovery had no winner.
- status: red
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests.test_repair_rejects_missing_lock_before_immutable_result_publication -v`
  - result: exit `1`; `Ran 1 test`; `FAILED (failures=1)` because repair published immutable evidence before rejecting its missing lock.
- status: green
  - command: focused three-test session serialization command from the RED cycle.
  - result: exit `0`; `Ran 3 tests`; `OK`.
- status: green
  - command: focused nine-test recovery/ownerless command from the RED cycle.
  - result: exit `0`; `Ran 9 tests`; `OK`.
- status: green
  - command: focused missing-lock-before-repair-publication command from the RED cycle.
  - result: exit `0`; `Ran 1 test`; `OK`.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`
  - result: exit `0`; `Ran 38 tests`; `OK (skipped=2)` before the final missing-lock regression was added.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`
  - result: exit `0`; `Ran 118 tests`; `OK (skipped=9)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`
  - result: exit `0`; `PASS: runtime preflight contract`.

### Second Remediation Behavior

- Every post-start session mutation requires the exact `AcquiredRunLock`. The closed owner is checked before comparison, immediately before temporary publication, and immediately before `os.replace`; another supported writer cannot acquire during the comparison/replacement window.
- Repair validates its held lock before immutable result publication, so a lockless caller cannot strand new evidence.
- Pre-quarantine failures compare-release a still-owned recovery claim. Live or recent fixed claims block; an exact dead-and-expired claim is quarantined, replaced with a new UUID4 claim, revalidated, and removed.
- A prior crash with no lock and exactly one valid `lock-recovery-*` quarantine resumes under a new claim/replacement lock, appends matching history at most once, repairs reservations, and cleans up. Multiple or contradictory quarantines remain unchanged and fail closed.
- Owner publication `OSError` removes only the exact still-empty initialization directory created by that acquisition and fsyncs its parent. Recent ownerless locks block; expired exact empty locks are quarantined and removed under the recovery claim; non-empty or unsafe ownerless locks remain visible and blocked.

## Third Important-Finding Remediation

- status: red
  - command: focused ten-test replacement-lock resume, ownerless-claim initialization, and late-owner race command.
  - result: exit `1`; `Ran 10 tests`; `FAILED (failures=6, errors=3)`; one pre-existing ordinary publication-cleanup behavior passed.
  - observed defects: replacement lock plus quarantine was permanently contradictory, the post-history fault boundary was absent, ownerless fixed claims could not age into conservative recovery, and a late owner could be displaced from the main lock path.
- status: green
  - command: the same focused ten-test command from the RED cycle.
  - result: exit `0`; `Ran 10 tests`; `OK`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`.
  - result: exit `0`; `Ran 128 tests`; `OK (skipped=9)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`.
  - result: exit `0`; `PASS: runtime preflight contract`.

### Third Remediation Behavior

- Under a newly acquired or recovered claim, exactly one valid stale quarantine plus one exact dead-and-expired replacement lock is resumable. Existing history must match the quarantine recovery ID, stale-owner tuple, and replacement owner ID; absent history is appended once, while matching history is reused without duplication.
- Fault coverage proves resume before history publication, during session publication, and after history publication. Live or recent replacement owners, mismatched history, and contradictory evidence remain visible and fail closed.
- A hard crash after recovery-claim `mkdir` leaves a recent exact-empty claim in the initializing state. Only an expired exact-empty non-symlink claim may be quarantined, rechecked, removed, and retried; concurrent recovery has one winner, and ordinary owner-publication failure cleans only its exact empty directory.
- Ownerless main-lock recovery now has a deterministic post-age-check barrier and rechecks the quarantined directory. A late valid owner is atomically restored when the original path is free and blocks further acquisition; if the path is occupied, both contradictory owners remain preserved and recovery fails closed.

## Final Correlation-Race Remediation

- status: red
  - command: focused six-test replacement-proof, normal-acquire marker, and ownerless-claim late-owner command.
  - result: exit `1`; `Ran 6 tests`; `FAILED (failures=4, errors=2)`.
  - observed defects: replacement ownership was not derived from the quarantine UUID, mismatched no-history evidence resumed, normal acquisition ignored recovery markers, and a late recovery-claim owner was displaced instead of restored.
- status: green
  - command: the same focused six-test command from the RED cycle.
  - result: exit `0`; `Ran 6 tests`; `OK`.
- status: red
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`.
  - result: exit `1`; `Ran 54 tests`; `FAILED (errors=1, skipped=2)` because a concurrent ownerless-claim loser leaked `FileNotFoundError` during quarantine removal.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`.
  - result: exit `0`; `Ran 54 tests`; `OK (skipped=2)` after mapping replacement disappearance/collision to a closed blocked race.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`.
  - result: exit `0`; `Ran 133 tests`; `OK (skipped=9)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`.
  - result: exit `0`; `PASS: runtime preflight contract`.

### Final Correlation Behavior

- Recovery generates the UUID before quarantine publication. The quarantine is `lock-recovery-<uuid>`, and the internal replacement-lock publisher uses exactly `<uuid>` as its UUID4 owner ID; callers cannot select normal lock ownership.
- Resume requires the exact replacement owner ID to match the quarantine UUID. Existing history must bind the same recovery ID, replacement owner, and stale-owner tuple; missing history is appended once. Mismatched evidence remains preserved and contradictory.
- Normal lock acquisition checks for the fixed recovery claim and every exact `lock-recovery-*` marker before lock creation and again before owner publication. Only the internal recovery replacement path bypasses this marker block.
- Ownerless recovery-claim quarantine now re-lstats after rename. A late valid owner is restored atomically to the fixed claim path and blocks; if a concurrent winner occupies that path, both directories remain preserved and the state is invalid.

## Scope Confirmation

- Product, Gradle, build, product/unit tests, server, Docker, HTTP/API, database, migration, seed, and infrastructure commands: NOT RUN.
- Shell command runner, subprocess launch, `run.json`, manifest publication, finalization, staging, and commit: NOT ADDED or NOT RUN.
- Repository-root `.ai-runs`: must remain absent; test artifacts live only in `TemporaryDirectory` repositories.

## Environment Notes

- The default `bash` command routes to WSL, which has no installed distribution. Git Bash at `C:\Program Files\Git\bin\bash.exe` ran the approved shell tests successfully.
- Windows does not provide directory symlink creation in this test environment, and its reported mode bits do not distinguish `0700` from `0777`. Nine symlink-only cases are skipped: seven established cases plus the two new repair ancestor tests. Permission enforcement is fail-closed on hosts where permission modes are verifiable and conservative on Windows.

## Final Crash-Resume Remediation

- status: red
  - command: focused four-test replacement-lock publication and ownerless-main cleanup command.
  - result: exit `1`; `Ran 4 tests`; `FAILED (failures=1, errors=3)`.
- status: green
  - command: the same focused four-test command from the RED cycle.
  - result: exit `0`; `Ran 4 tests`; `OK`.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`.
  - result: exit `0`; `Ran 58 tests`; `OK (skipped=2)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`.
  - result: exit `0`; `Ran 137 tests`; `OK (skipped=9)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`.
  - result: exit `0`; `PASS: runtime preflight contract`.

### Final Crash-Resume Behavior

- An empty replacement lock left by a crash after `mkdir` and before owner publication resumes owner publication under the recovered and revalidated claim, using the quarantine UUID.
- Ownerless-main cleanup resumes from both an initialization quarantine and the claim-only state left after main-lock removal.
- Existing recovery correlation, collision preservation, and late-owner protections remain enforced.

### Final Scope Confirmation

- Repository-root `.ai-runs`: absent.
- Product, Gradle, build, product/unit tests, server, Docker, HTTP/API, database, migration, seed, and infrastructure commands: NOT RUN.
- Staging and commit: NOT RUN.

## Initialization-Quarantine Marker Race Remediation

- status: red
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests.test_normal_acquisition_blocks_during_stale_claim_replacement_gap -v`.
  - result: exit `1`; `Ran 1 test`; `FAILED (failures=1)` because normal acquisition succeeded (`normal_error` was `None`) while recovery was paused after stale-claim rename and before replacement-claim publication.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests.test_normal_acquisition_blocks_during_stale_claim_replacement_gap -v`.
  - result: exit `0`; `Ran 1 test`; `OK`.
- status: green
  - command: `python -m unittest scripts.ai.tests.test_workflow_helper.RunLifecycleTests -v`.
  - result: exit `0`; `Ran 59 tests`; `OK (skipped=2)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh`.
  - result: exit `0`; `Ran 138 tests`; `OK (skipped=9)`.
- status: green
  - command: `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh`.
  - result: exit `0`; `PASS: runtime preflight contract`.

### Remediated Behavior

- The deterministic barrier pauses recovery in the exact stale-claim rename/replacement gap while the fixed claim is absent and the exact `lock-initialization-quarantine-<uuid>` is the remaining durable recovery marker.
- Normal acquisition now treats exact supported `lock-initialization-quarantine-<uuid>` names, the fixed recovery claim, and exact `lock-recovery-<uuid>` names as active recovery evidence at both marker checks.
- Pattern matching remains exact; existing malformed, contradictory, symlink/reparse, owner-correlation, and late-owner paths retain their fail-closed lifecycle validation.
- Recovery resumes after the barrier, removes the initialization quarantine, and releases the replacement claim without changing prior lifecycle, correlation, RESERVED-repair, or late-owner behavior.

### Scope Confirmation

- Changed files: `scripts/ai/workflow_helper.py`, `scripts/ai/tests/test_workflow_helper.py`, and this implementation log.
- Repository-root `.ai-runs`: not created; lifecycle artifacts were confined to `TemporaryDirectory` repositories.
- Product, Gradle, build, product/unit tests, server, Docker, HTTP/API, database, migration, seed, and infrastructure commands: NOT RUN.
- Staging and commit: NOT RUN.
