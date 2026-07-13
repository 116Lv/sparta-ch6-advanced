---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-task-2-reviewer
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: phase-1b-2-task-2-reviewer
started_at: 2026-07-11T00:00:00+09:00
ended_at: 2026-07-11T15:21:37+09:00
last_updated: 2026-07-13T08:54:37+09:00
branch: main
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - ai/schemas/run-session.schema.json
  - ai/schemas/process-attempt.schema.json
  - ai/schemas/command-result.schema.json
  - ai/schemas/gateway-result.schema.json
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/fixtures/phase-1b/execution/
changed_files:
  - ai/work-logs/issue-4/phase-1b-2-task-2-reviewer.md
commands_run:
  - "Static review only; no tests, product commands, or implementation commands were run."
tests_run:
  - "Accepted evidence, not rerun: helper exited 0; Ran 87 tests; OK (skipped=7 existing Windows symlink-only cases)."
  - "Accepted evidence, not rerun: runtime preflight exited 0; PASS: runtime preflight contract."
  - "Accepted re-review evidence, not rerun: helper exited 0; Ran 104 tests; OK (skipped=9)."
  - "Accepted re-review evidence, not rerun: runtime preflight exited 0; PASS: runtime preflight contract."
  - "Accepted final re-review evidence, not rerun: helper exited 0; Ran 118 tests; OK (skipped=9)."
  - "Accepted final re-review evidence, not rerun: runtime preflight exited 0; PASS: runtime preflight contract."
  - "Accepted fourth re-review evidence, not rerun: helper exited 0; Ran 128 tests; OK (skipped=9)."
  - "Accepted fourth re-review evidence, not rerun: runtime preflight exited 0; PASS: runtime preflight contract."
  - "Accepted fifth re-review evidence, not rerun: helper exited 0; Ran 133 tests; OK (skipped=9)."
  - "Accepted fifth re-review evidence, not rerun: runtime preflight exited 0; PASS: runtime preflight contract."
  - "Accepted final crash-resume RED evidence, not rerun: Ran 4 tests; FAILED (failures=1, errors=3)."
  - "Accepted final crash-resume focused GREEN evidence, not rerun: Ran 4 tests; OK."
  - "Accepted final crash-resume lifecycle evidence, not rerun: Ran 58 tests; OK (skipped=2)."
  - "Accepted final crash-resume helper evidence, not rerun: Ran 137 tests; OK (skipped=9)."
  - "Accepted final crash-resume runtime-preflight evidence, not rerun: PASS: runtime preflight contract."
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

# Summary

**Independent final Task 2 review verdict: FAIL / NOT APPROVED; status remains `in_review`.** The two requested crash-resume fixes are present and directly covered: replacement-lock owner publication resumes under the claim/quarantine UUID, and ownerless-main cleanup resumes from both the initialization quarantine and the post-removal claim-only state. Prior UUID/history correlation, collision preservation, late-owner restoration, held-lock checks, session CAS serialization, stale-claim recovery, and conservative owner validation remain present. One Important marker race remains because initialization quarantines do not block normal acquisition during stale-claim replacement. Critical none and Minor none. This static review accepts the supplied RED/GREEN, lifecycle, full-helper, preflight, and repository-root `.ai-runs` absence evidence without rerunning commands.

# Findings

## Critical

1. **`repair_reserved_attempts` does not enforce realpath containment for artifact ancestors.** At `scripts/ai/workflow_helper.py:2045-2061`, the helper rejects only a final-file symlink and the final command-ID directory symlink. A symlinked `.ai-runs/<run>/process-attempts/` ancestor is followed by `read_json`, and a symlinked `.ai-runs/<run>/commands/` ancestor is followed by `mkdir` and `exclusive_publish_json`. Both permit external read/write despite the required run-local realpath/symlink containment. Fix: resolve and verify every existing artifact ancestor beneath the exact run directory before reading or creating it; reject any symlink in the artifact path, including `commands` and `process-attempts`. Add ancestor-symlink tests for both read and write paths, with platform skips stated explicitly.

## Important

1. **Repair publication can leave an immutable terminal result without its terminal session transition.** `scripts/ai/workflow_helper.py:2083` publishes the BLOCKED command result before `scripts/ai/workflow_helper.py:2096-2098` writes the revised session. A crash or `replace_run_session` failure leaves the reservation `RESERVED` but leaves an immutable command result on disk; the next repair then skips it at `scripts/ai/workflow_helper.py:2050` because the command path exists. That violates monotonic repair and session refs/artifact consistency. Fix: add a durable recovery protocol that detects and validates this exact pre-existing repair artifact, then atomically completes the matching session transition, or otherwise journal the two-record transition so recovery never strands evidence.

2. **A non-launched attempt is treated as eligible stale-process evidence.** `scripts/ai/workflow_helper.py:2052-2058` validates tuple fields but never requires `process["launchStatus"] == "LAUNCHED"`. The schema-valid `SPAWN_FAILED` fixture can therefore be converted to `STALE_RESERVED_REPAIRED`, although Task 2 permits this repair only for a launched process attempt. Fix: require the launched form before publishing a repair and retain every other valid, malformed, missing, contradictory, or ambiguous process artifact as `RESERVED`/blocked without relaunch.

3. **The lock owner is not uniformly unpredictable or closed on release.** `scripts/ai/workflow_helper.py:1988-1989` accepts any schema-valid caller-provided `ownerId`, and `scripts/ai/workflow_helper.py:2102-2103` accepts the replacement owner the same way; only the start path creates a UUID at `scripts/ai/workflow_helper.py:1895-1900`. `scripts/ai/workflow_helper.py:2012` rereads the release owner with raw `read_json` rather than the closed, non-symlink `read_run_lock_owner` routine at `scripts/ai/workflow_helper.py:1970-1977`. Fix: generate/validate high-entropy owner IDs for every acquire/recovery path and use the closed owner reader for compare-release.

4. **The focused suite does not prove the required race, collision, and recovery-failure behavior.** `scripts/ai/tests/test_workflow_helper.py:2052-2077` exercises sequential lock acquisition and one owner mismatch; `:2079-2112` exercises only live, recent-dead, and successful stale recovery; `:2132-2197` covers one launched repair and one malformed artifact. It omits concurrent recovery/replace-release races, stale-owner reread mutation, quarantine rename collision, replacement mkdir/write collision, failed recovery evidence preservation, repair publication collision, session-write-after-artifact crash, missing and tuple-mismatched attempts, PID-reuse/permission behavior, and lost-update protection for concurrent session writers. The plan-required `lock-owner-dead-recent.json`, `lock-owner-dead-expired.json`, and `reserved-with-process-attempt.json` fixtures are also absent from `ai/fixtures/phase-1b/execution/`. Add deterministic fault-injection and multiprocess/thread barriers; sequential happy-path coverage is insufficient for this lifecycle gate.

## Minor

- None.

# Verified Scope

- Current preflight precedes `RUN_START` mutation (`scripts/ai/workflow_helper.py:1869-1892`), and preflight failure leaves `.ai-runs` absent in the focused test (`scripts/ai/tests/test_workflow_helper.py:2040-2050`).
- Run/task validation, exclusive run-directory creation, exact OPEN session data, no `run.json`, schema validation before session publication, fsync-backed publication, and supported permission handling are present (`scripts/ai/workflow_helper.py:1796-1922`).
- Lock creation uses `mkdir`, acquisition validates a closed owner, recovery blocks live or recent owners and requires dead plus expired, appends history under the replacement lock, rereads quarantine owner, and releases last (`scripts/ai/workflow_helper.py:1988-2004`, `2102-2148`). PID reuse and permission errors block conservatively through `owner_is_alive`; they are not test-proven here.
- Gateway result tuple/fallback validation is present from Task 1; Task 2 adds no recovery gateway operation. No shell runner, product process, `Popen`, `run.json`, manifest, or finalization behavior was added.
- Windows limitations are honestly stated in the implementation log: directory symlink creation is unavailable and mode bits are not authoritative. The accepted seven symlink-only skips do not cover the missing ancestor-symlink, collision, or crash-order cases.

# Verification Evidence

- Static review only. Product commands: NOT RUN.
- Accepted helper evidence: exit `0`; `Ran 87 tests`; `OK (skipped=7)`.
- Accepted preflight evidence: exit `0`; `PASS: runtime preflight contract`.
- Repository-root `.ai-runs`: absent on static inspection.

# Required Fixes

1. Close artifact-path containment for every repair read/write ancestor.
2. Make the terminal result/session update recoverable and reference-consistent across every crash point.
3. Restrict repair eligibility to exact launched attempts and harden owner generation/release validation.
4. Add collision, concurrency, PID/permission, and fault-injection tests plus the approved execution fixtures; preserve the documented Windows skips.

# Re-review Dispositions

## Original Critical: ancestor containment

**CLOSED.** `scripts/ai/workflow_helper.py:1824-1888` lstat-checks each existing component, rejects symlink/reparse points and non-directories, checks resolved containment beneath the exact run, creates missing parents one component at a time, and requires exact regular files. `scripts/ai/tests/test_workflow_helper.py:2406-2436` covers process-read and command-write ancestor symlinks. These two tests are among the nine accepted Windows symlink-only skips, and the implementation log states that limitation accurately.

## Original Important 1: stranded terminal result

**CLOSED.** `scripts/ai/workflow_helper.py:2203-2282` accepts only a schema-valid and semantically exact existing repair result, preserves collision winners, resumes the session transition without overwriting immutable evidence, and supplies the prior session to replacement. `scripts/ai/tests/test_workflow_helper.py:2438-2502` covers valid resume, contradictory evidence, post-publication session failure, and publication collision.

## Original Important 2: LAUNCHED-only repair

**CLOSED.** `scripts/ai/workflow_helper.py:2187-2199` requires `launchStatus: LAUNCHED` plus the exact run/command/attempt and fingerprint tuple. `scripts/ai/tests/test_workflow_helper.py:2504-2527` keeps missing, SPAWN_FAILED, and tuple-mismatched evidence RESERVED without creating a command result.

## Original Important 3 and 4: owner handling and proof matrix

**CLOSED.** The embedded owner schema requires UUID4 form at `scripts/ai/workflow_helper.py:51-66`; `new_run_lock_owner` generates owners internally at `:2070-2080`; compare-release uses the closed lstat reader and a second complete-owner comparison at `:2100-2117`. Tests at `scripts/ai/tests/test_workflow_helper.py:2102-2319` now cover UUID4 uniqueness, compare-release mutation, concurrent acquire/recovery, stale-owner mutation, PID permission/reuse, quarantine/replacement collisions, and history/session faults. The three approved fixtures now exist under `ai/fixtures/phase-1b/execution/`.

# Current Findings

## Critical

- None.

## Important

1. **`replace_run_session` is check-then-replace, not an atomic CAS, so a concurrent writer can still be lost.** At `scripts/ai/workflow_helper.py:2136-2144`, the helper reads and compares the current session, then later calls unconditional `atomic_write`; another writer can replace the session after line 2143 and before line 2144, and this writer will overwrite that update. The test at `scripts/ai/tests/test_workflow_helper.py:2529-2547` injects its update from `session.before_replace`, before the helper's read at line 2137, so it does not exercise the remaining check/replace race window. Fix: serialize every session writer under a verified held run lock, or use a genuinely atomic generation/digest protocol whose commit fails when the compared generation changed; add a barrier after the comparison and before replacement to prove no lost update.

2. **The fixed recovery claim is orphaned by pre-quarantine failures and has no dead-and-expired recovery path.** `scripts/ai/workflow_helper.py:2294-2306` creates `.state/lock-recovery-claim`, but the stale-owner reread and quarantine rename at `:2308-2319` occur before the only guarded block and there is no compare-release cleanup on those failures. A stale-owner mutation, quarantine collision, rename error, or process crash can therefore leave the fixed claim indefinitely; later recovery always returns `RUN_LOCK_RECOVERY_ACTIVE` at `:2297-2301`, regardless of claim PID or age. The stale-owner and collision tests at `scripts/ai/tests/test_workflow_helper.py:2201-2213` and `:2231-2255` do not assert claim cleanup or recoverability. Fix: compare-release the claim when failure occurs before quarantine mutation, and define conservative dead-and-expired recovery for crashed claims while preserving all partial evidence.

3. **A crash or ordinary write error between lock `mkdir` and owner publication leaves an unrecoverable ownerless lock.** `scripts/ai/workflow_helper.py:2082-2097` creates the lock directory before `owner.json`; only `FileExistsError` from owner publication is handled, and there is no cleanup/recovery for process death or another `OSError`. Future acquisition sees the directory without an owner and permanently returns `RUN_LOCK_INITIALIZING` at `:2084-2088`; `recover_run_lock` cannot parse such a lock. The replacement-write test injects a competing valid owner, not an owner-publication crash or generic write failure. Fix: add a conservative ownerless-initialization recovery protocol and fault tests for failure/crash immediately after mkdir and during owner publication.

## Minor

- None.

# Re-review Evidence

- Static re-review only; no tests, product commands, or implementation commands were run.
- Accepted helper evidence: exit `0`; `Ran 104 tests`; `OK (skipped=9)`.
- Accepted runtime-preflight evidence: exit `0`; `PASS: runtime preflight contract`.
- Nine skips are the seven established Windows symlink-only cases plus the two new repair-ancestor symlink cases.
- Current status: `in_review`; verdict: FAIL / NOT APPROVED.

# Final Task 2 Re-review

## Latest Finding Dispositions

1. **Verified-held-lock session serialization: CLOSED.** `scripts/ai/workflow_helper.py:2173-2229` requires the exact held `AcquiredRunLock`, checks its closed owner before comparison, after the post-compare barrier and before temporary publication, and immediately before `os.replace`. `repair_reserved_attempts` validates the lock before any immutable repair publication at `:2252-2258`. Tests at `scripts/ai/tests/test_workflow_helper.py:2187-2275` cover missing/mismatched locks, lockless repair, a post-compare second writer, sequential updates, and owner mutation immediately before replacement.

2. **Pre-quarantine claim cleanup and dead-expired claim replacement: CLOSED for the implemented states.** `scripts/ai/workflow_helper.py:2391-2415` blocks live/recent claims and replaces an exact dead-and-expired claim; `:2505-2556` compare-releases a still-owned claim on every failure before quarantine mutation. Tests at `scripts/ai/tests/test_workflow_helper.py:2299-2466` cover stale-owner mutation cleanup, injected pre-quarantine failures, claim-owner mutation, live/recent/dead-expired claims, and resume from one exact quarantine after a crash before replacement-lock acquisition.

3. **Ownerless main-lock cleanup and stale recovery: CLOSED for the tested states.** `scripts/ai/workflow_helper.py:2106-2141` cleans an exact empty initialization directory after an ordinary owner-publication error, while `:2527-2547` blocks recent empty locks and quarantines/removes only expired exact empty locks. Tests at `scripts/ai/tests/test_workflow_helper.py:2498-2583` cover publication `OSError`, hard crash after mkdir, recent/expired/non-empty states, retry, and concurrent cleanup winner selection.

## Current Findings

### Critical

- None.

### Important

1. **A failed recovery after replacement-lock acquisition cannot be resumed.** `complete_recovery` creates the replacement lock at `scripts/ai/workflow_helper.py:2433-2436`; history or session failure then leaves both that lock and the original quarantine. On a later attempt, once the replacement owner and claim are dead and expired, `recover_run_lock` observes both and unconditionally returns `RUN_LOCK_RECOVERY_CONTRADICTION` at `:2511-2513`. The fault tests at `scripts/ai/tests/test_workflow_helper.py:2585-2623` assert preservation after history/session failure but never age the owners and resume. This leaves the exact crash states those tests create permanently unrecoverable. Fix: recognize one exact quarantine plus its exact replacement lock/claim as a resumable partial recovery, correlate any existing history, and add resume tests for failures before history, during session publication, and after history publication.

2. **A hard crash between recovery-claim `mkdir` and owner publication leaves an unrecoverable ownerless fixed claim.** `create_recovery_claim` performs `mkdir` at `scripts/ai/workflow_helper.py:2366-2369` and writes `owner.json` afterward. Ordinary `OSError` is cleaned, but process death in that interval leaves an empty `.state/lock-recovery-claim`; the existing-claim path at `:2395-2400` requires a valid owner and reports INVALID_STATE forever, with no recent/expired ownerless-claim branch. Tests cover ownerless main locks and valid claim owners, not this claim-creation crash. Fix: apply the same conservative recent/expired exact-empty protocol to ownerless recovery claims and fault-test the mkdir/publication crash boundary.

3. **Stale ownerless-main-lock recovery can displace a late valid owner.** After checking an ownerless lock is empty and expired at `scripts/ai/workflow_helper.py:2530-2533`, recovery renames it at `:2537` without an atomic initialization identity. If the original delayed acquirer publishes `owner.json` between those steps, recovery moves a now-owned lock away; `:2539-2540` preserves the quarantine but does not restore the active lock, and a new normal acquisition can take `.state/lock`. No barrier test injects owner publication in this window. Fix: after quarantine, detect a late owner and atomically restore the directory when the lock path is still free, or introduce a claimable initialization identity that can be compared before removal; add a deterministic late-owner race test.

### Minor

- None.

## Final Evidence

- Static inspection only; no tests, product commands, or implementation files were run or edited.
- Accepted helper evidence: exit `0`; `Ran 118 tests`; `OK (skipped=9)`.
- Accepted runtime-preflight evidence: exit `0`; `PASS: runtime preflight contract`.
- Status remains `in_review`; verdict: FAIL / NOT APPROVED.

# Fifth Task 2 Re-review

## Latest Finding Dispositions

1. **Replacement-owner UUID/quarantine correlation and normal marker blocking: CLOSED.** `scripts/ai/workflow_helper.py:2117-2195` blocks normal/start acquisition before and after lock-directory creation whenever the fixed claim or an exact recovery quarantine exists, limits public purposes, derives the recovery replacement owner UUID from the quarantine UUID, and keeps replacement publication internal. `:2543-2569` and `:2631-2657` require replacement owner, quarantine, and existing history to share that exact recovery identity. Tests at `scripts/ai/tests/test_workflow_helper.py:2904-3014` cover exact UUID correlation, mismatched pre-history owner rejection, claim/quarantine acquisition blocking, all history fault boundaries, live owners, and history mismatch preservation.

2. **Late ownerless-claim restore/contradiction handling: CLOSED for the tested states.** `scripts/ai/workflow_helper.py:2446-2502` rechecks the ownerless-claim quarantine, validates an appearing owner, restores it to the fixed path when free, and preserves both directories if a competing fixed claim exists. Tests at `scripts/ai/tests/test_workflow_helper.py:3089-3135` cover restored-owner blocking and occupied-path contradiction preservation.

## Current Findings

### Critical

- None.

### Important

1. **A hard crash during replacement-lock initialization is still not resumable.** `acquire_replacement_run_lock` delegates to `_publish_run_lock` at `scripts/ai/workflow_helper.py:2181-2195`; a process death after the replacement `.state/lock` `mkdir` at `:2135-2147` but before `owner.json` publication leaves an exact empty main lock beside the claim and recovery quarantine. On retry, `recover_run_lock` classifies the main lock as ownerless and unconditionally rejects the coexisting recovery quarantine at `:2673-2674`, even though the quarantine UUID provides the intended replacement identity. Existing replacement-resume tests inject faults only after the replacement owner is published. Fix: under the exact claim/quarantine, conservatively block a recent empty replacement initialization and recover an expired exact-empty one by recreating the UUID-correlated replacement; cover process death at `acquire.after_mkdir` with `purpose: recovery`, including concurrent and late-owner cases.

2. **Ownerless-main cleanup has no crash-resume protocol for its initialization quarantine or post-delete claim state.** `scripts/ai/workflow_helper.py:2678-2720` renames the stale empty lock to `lock-initialization-quarantine-*`, removes it, and then releases the claim. A process death after rename leaves a marker that `recovery_quarantines` and `run_recovery_marker_exists` do not recognize; a death after quarantine removal but before claim release leaves no lock and no exact recovery quarantine, so a later `recover_run_lock` reaches `RUN_LOCK_QUARANTINE_MISSING` at `:2721-2724`. Tests cover success and late-owner races but inject no crash after ownerless quarantine rename, after quarantine removal, or before claim release. Fix: make initialization-quarantine cleanup resumable and marker-blocking, and make an exact owned claim plus completed absence an idempotent cleanup state; fault-test every boundary.

### Minor

- None.

## Fifth Re-review Evidence

- Static inspection only; no tests, product commands, or implementation files were run or edited.
- Accepted helper evidence: exit `0`; `Ran 133 tests`; `OK (skipped=9)`.
- Accepted runtime-preflight evidence: exit `0`; `PASS: runtime preflight contract`.
- Status remains `in_review`; verdict: FAIL / NOT APPROVED.

# Fourth Task 2 Re-review

## Latest Finding Dispositions

1. **Stale replacement-lock plus quarantine resume/history correlation: CLOSED for correlated and tested states.** `scripts/ai/workflow_helper.py:2463-2516` reuses the exact replacement lock, binds existing history to recovery ID, quarantined owner tuple, and replacement owner ID, appends absent history once, and rejects duplicate or mismatched history. `:2546-2569` requires both owners to be dead and expired, rereads exact owner bytes, and preserves unexpected entries. Tests at `scripts/ai/tests/test_workflow_helper.py:2904-2968` cover pre-history, session-publication, and post-history resume, no duplicate history, live replacement blocking, and history mismatch preservation.

2. **Ownerless recovery-claim cleanup/concurrent winner: CLOSED for the tested states.** `scripts/ai/workflow_helper.py:2366-2445` handles ordinary publication failure, recent exact-empty initialization blocking, expired exact-empty quarantine/recheck/removal, UUID4 replacement, and dead-expired owned claims. Tests at `scripts/ai/tests/test_workflow_helper.py:2970-3041` cover crash after mkdir, expiry, ordinary publication failure, and one concurrent winner.

3. **Late owner restore/contradiction preservation for the main lock: CLOSED for the tested states.** `scripts/ai/workflow_helper.py:2583-2631` rechecks the quarantined directory, validates a late owner, restores it when `.state/lock` remains free, and preserves both records when another owner occupies the path. Tests at `scripts/ai/tests/test_workflow_helper.py:3043-3086` cover restoration, subsequent acquisition blocking, and occupied-path contradiction preservation.

## Current Findings

### Critical

- None.

### Important

1. **A pre-history main lock cannot be proven to be the quarantined recovery's replacement lock.** When one quarantine and one stale main lock coexist without history, `scripts/ai/workflow_helper.py:2546-2569` treats the main owner as the replacement solely because both records are valid, same-run, dead, and expired; the owner schema has no recovery ID or purpose correlation. Normal `acquire_run_lock` at `:2117-2141` also ignores the recovery claim and quarantine, so after a crash immediately following quarantine rename, an unrelated normal writer can acquire `.state/lock`, mutate the session, and later be misclassified as the replacement if it becomes stale. The pre-history resume tests at `scripts/ai/tests/test_workflow_helper.py:2904-2930` use a genuine replacement created by the failed recovery and do not cover an unrelated normal owner. Fix: prevent normal acquisition while a claim/quarantine exists, or durably correlate the replacement owner with the recovery ID before it can be accepted; add an unrelated-main-lock contradiction test.

2. **Ownerless recovery-claim quarantine lacks the late-owner restoration used for the main lock.** `scripts/ai/workflow_helper.py:2398-2422` checks an expired claim is empty, then renames it and raises INVALID_STATE if `owner.json` appeared by line 2416. It neither restores the now-valid claim nor prevents a later caller from creating a new fixed claim, while the delayed creator can still return an `AcquiredRunLock` for the moved path. The concurrent-winner test at `scripts/ai/tests/test_workflow_helper.py:3017-3041` races two recovery consumers before rename, but does not inject the original delayed claim owner's publication between the emptiness check and quarantine rename. Fix: apply the main-lock late-owner restore/occupied-path contradiction protocol to ownerless claims and verify the delayed creator cannot coexist with a second claim owner.

### Minor

- None.

## Fourth Re-review Evidence

- Static inspection only; no tests, product commands, or implementation files were run or edited.
- Accepted helper evidence: exit `0`; `Ran 128 tests`; `OK (skipped=9)`.
- Accepted runtime-preflight evidence: exit `0`; `PASS: runtime preflight contract`.
- Status remains `in_review`; verdict: FAIL / NOT APPROVED.

# Independent Final Task 2 Review

## Latest Fix Dispositions

1. **Replacement-lock `mkdir` crash before owner publication: PASS.** `scripts/ai/workflow_helper.py:2218-2246` resumes an exact empty replacement lock only through the held recovery claim, derives the replacement owner ID from the quarantine UUID, revalidates the claim immediately before exclusive owner publication, and preserves mismatched or racing owners. `scripts/ai/workflow_helper.py:2794-2809` admits this state only with one exact recovery quarantine and then reuses the normal correlated history/cleanup path. Tests at `scripts/ai/tests/test_workflow_helper.py:2108-2131` and `:3006-3034` inject the crash at recovery `acquire.after_mkdir`, prove UUID-correlated completion, and reject a changed held claim.

2. **Ownerless-main cleanup crash after quarantine creation and after removal: PASS.** `scripts/ai/workflow_helper.py:2594-2654` validates one exact initialization quarantine, restores a late owner or preserves an occupied-path contradiction, revalidates the held claim before removal, and releases the claim only after durable cleanup. `scripts/ai/workflow_helper.py:2826-2843` resumes either the surviving initialization quarantine or the claim-only completed-absence state. Tests at `scripts/ai/tests/test_workflow_helper.py:2602-2660` cover both crash boundaries and successful retry.

3. **Prior protections: PASS for the reviewed paths.** UUID/history correlation and mismatch rejection remain at `scripts/ai/workflow_helper.py:2657-2714` and `:2748-2780`; normal acquisition still blocks the fixed claim and exact recovery quarantines before and after `mkdir` at `:2120-2155`; held-lock and CAS checks remain at `:2278-2334`; stale-claim replacement and late-owner preservation remain at `:2497-2576`; ownerless-main late-owner restoration remains at `:2614-2638`. Regression tests at `scripts/ai/tests/test_workflow_helper.py:2969-3295` retain correlation, collision, live/recent owner, history mismatch, claim concurrency, late-owner, held-lock, and CAS coverage.

## Findings

### Critical

- None. **PASS**

### Important

1. **Initialization quarantines are resumable but not marker-blocking. FAIL.** `run_recovery_marker_exists` at `scripts/ai/workflow_helper.py:2120-2125` recognizes the fixed claim and `lock-recovery-*` quarantines only; it omits `lock-initialization-quarantine-*`. When a crashed ownerless-main cleanup is resumed with an expired owned claim, `acquire_recovery_claim` renames the stale fixed claim at `:2566-2573` before creating its replacement. A normal `acquire_run_lock` can pass both marker checks at `:2132-2155` inside that claim-path gap, publish a valid main lock, and potentially mutate the session while the initialization quarantine still records incomplete cleanup. Recovery later preserves the resulting owned-lock/quarantine contradiction at `:2748-2752`, but prevention is required: the supported normal writer must not be admitted while recovery evidence remains. Existing marker tests at `scripts/ai/tests/test_workflow_helper.py:3054-3078` cover the fixed claim and `lock-recovery-*` quarantine, not an initialization quarantine or the stale-claim replacement gap. Fix: include exact initialization quarantines in the pre/post normal-acquisition marker check and add a deterministic barrier test across stale-claim rename/replacement proving normal acquisition blocks.

### Minor

- None. **PASS**

## Accepted Evidence

- Static review only; no repository commands or tests were run.
- RED: `Ran 4 tests`; `FAILED (failures=1, errors=3)`.
- Focused GREEN: `Ran 4 tests`; `OK`.
- Lifecycle: `Ran 58 tests`; `OK (skipped=2)`.
- Full helper: `Ran 137 tests`; `OK (skipped=9)`.
- Runtime preflight: `PASS`.
- Repository-root `.ai-runs`: absent.
- Final verdict: **FAIL / NOT APPROVED**; status remains `in_review`.

# Final Independent Re-review

## Verdict

**PASS / APPROVED.** Status is `done`. The last Important finding is closed. Critical: none. Important: none. Minor: none.

## Finding Disposition

1. **Exact initialization-quarantine marker blocking: CLOSED.** `scripts/ai/workflow_helper.py:33-38` defines the exact lowercase UUID4 grammar for `lock-initialization-quarantine-<uuid>`. `run_recovery_marker_exists` at `scripts/ai/workflow_helper.py:2120-2133` now recognizes that exact pattern alongside the fixed recovery claim and exact `lock-recovery-<uuid>` markers. Normal/start acquisition invokes the marker check before lock creation and again after `mkdir` but before owner publication at `scripts/ai/workflow_helper.py:2136-2159`, so the stale-claim rename/replacement gap cannot admit a supported normal owner.

2. **Deterministic race proof: PASS.** `scripts/ai/tests/test_workflow_helper.py:2632-2688` first leaves an exact initialization quarantine, ages the fixed claim, and pauses replacement claim creation only after the stale claim has been renamed and the fixed path is absent. While the initialization quarantine is the remaining durable marker, normal acquisition is required to return `RegistryBlockedError`; recovery then resumes, removes the quarantine, releases the replacement claim, and completes successfully.

3. **Exact grammar and fail-closed handling: PASS.** Pattern matching uses anchored `fullmatch`, so near-miss names are not promoted to supported recovery identity. An exact-name entry blocks normal acquisition by name regardless of contents or file type. Recovery subsequently validates exact directories with `lstat`-based control checks, rejects symlink/reparse or non-directory entries, rejects unexpected contents and multiple initialization quarantines, and preserves contradictory evidence at `scripts/ai/workflow_helper.py:2598-2654` and `:2722-2843`.

4. **Prior protections: PASS.** The narrow marker-predicate addition leaves the existing UUID-derived replacement ownership and history correlation checks at `scripts/ai/workflow_helper.py:2657-2718` and `:2748-2809`, held-lock/session serialization at `:2278-2334`, stale-claim late-owner preservation at `:2497-2580`, initialization-quarantine late-owner restoration at `:2618-2654`, and RESERVED repair protections unchanged. Existing focused coverage at `scripts/ai/tests/test_workflow_helper.py:3047-3348` continues to exercise replacement correlation, history fault boundaries, claim races, mismatches, and late-owner restoration/contradiction preservation.

## Accepted Evidence

- Focused RED: exit `1`; `Ran 1 test`; `FAILED (failures=1)` as expected.
- Focused GREEN: exit `0`; `Ran 1 test`; `OK`.
- Lifecycle: exit `0`; `Ran 59 tests`; `OK (skipped=2)`.
- Full helper: exit `0`; `Ran 138 tests`; `OK (skipped=9)`.
- Runtime preflight: `PASS`.
- Repository-root `.ai-runs`: absent.
- Static final re-review only; no commands or tests were run, and no implementation or test file was edited.
