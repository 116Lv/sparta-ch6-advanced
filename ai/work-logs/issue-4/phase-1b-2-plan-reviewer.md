---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-plan-reviewer
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: phase-1b-2-plan-reviewer
started_at: 2026-07-11T12:05:07+09:00
ended_at: 2026-07-11T12:26:24+09:00
last_updated: 2026-07-13T09:32:29+09:00
branch: main
related_files:
  - AGENTS.md
  - docs/superpowers/specs/2026-07-10-ai-workflow-enforcement-design.md
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - ai/schemas/run.schema.json
  - ai/schemas/command-result.schema.json
  - ai/schemas/approval-record.schema.json
  - ai/schemas/policy-violation.schema.json
  - ai/schemas/gateway-result.schema.json
  - scripts/ai/workflow_helper.py
changed_files:
  - ai/work-logs/issue-4/phase-1b-2-plan-reviewer.md
commands_run:
  - "Static file inspection only: repository instructions, approved design/specification, Phase 1A schemas, gateway schema/helper, plan, and work-log policy."
  - "Static re-review only: revised Phase 1B specification and Phase 1B-2 plan lines, canonical registry input patterns, and ASCII scan."
  - "Final static re-review only: POST data, inputPaths grammar, transient owner exemption, POSIX wrapper preconditions, all prior dispositions, and ASCII cleanliness."
tests_run: []
blockers: []
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

# Summary

Initial verdict: **REJECTED**. Intermediate re-review verdict: **FAIL**. Final static re-review verdict: **PASS / APPROVED** with Critical none, Important none, and Minor none.

# Final Static Re-review

## Critical

None.

## Important

None.

## Minor

None.

## Final Dispositions

1. **POST_COMMAND data rule: RESOLVED.** Phase 1B spec lines 130 and 132 now explicitly permit the exact closed POST data object for POST_COMMAND/FAIL and POST_COMMAND/BLOCKED, while retaining null data for POST NOT_CONFIGURED/POLICY_VIOLATION/INVALID_STATE and all non-PASS RUN_START/PRE_COMMAND branches. Plan lines 115-122 match exactly.
2. **Closed `inputPaths` semantics: RESOLVED.** Spec line 297 and plan lines 69-76 define only literal regular-file paths or non-empty directory prefixes ending exactly in `/**`; reject all other glob syntax; define containment, missing/empty behavior, recursive non-following walk, symlink rejection, regular-file selection, UTF-8 ordering, and deterministic NO_MATCH framing. Plan lines 204-205 require canonical positive and rejection vectors.
3. **Transient owner `$id` exemption: RESOLVED.** Spec line 330 and plan line 43 limit artifact `$id` equality to schema-versioned/session/evidence artifacts and explicitly exempt transient lock-owner/quarantine control JSON from artifact/reference semantics.
4. **Absolute `/bin/sh` wrapper/runtime preconditions: RESOLVED.** Spec line 298 and plan line 80 require POSIX, non-empty allowlisted PATH, and executable regular-file `/bin/sh` before launch; the fake wrapper has exact `#!/bin/sh` bytes, uses builtins only, and accepts no caller-selected interpreter. Plan lines 217 and 221-222 require the fixture and precondition tests.
5. **All earlier findings remain resolved.** RUN_START remains the single additive operation (spec lines 126 and 132; plan lines 15 and 105-109); lock recovery remains immutable session history with exclusive acquire/release and RESERVED repair (spec line 286; plan lines 49-53 and 184-185); failed-attempt reruns remain deferred without invented approval authority (spec line 292; plan lines 57-59 and 289); manifest size accepts zero and publication remains B3 (plan line 139); frame bytes, IDs, references, and Phase 1A compatibility remain exact (spec lines 296-297; plan lines 28-76 and 164-166); outcomes remain exhaustive (plan lines 103-133); redaction remains bounded strict UTF-8 (spec line 299; plan lines 84-97 and 240-241); POSIX process-group termination remains bounded (spec line 298; plan lines 80-82); crash repair remains monotonic and never relaunches automatically (spec line 300; plan lines 51-53 and 133); and only closed command-runner orchestration can reach `Popen` (plan lines 7, 122, and 257-268).
6. **ASCII cleanliness: RESOLVED.** A final static non-ASCII scan of both revised documents returned no lines.

The revised Phase 1B specification and Phase 1B-2 plan are internally consistent and implementable without reopening the approved decisions reviewed here.

# Prior Re-review Dispositions

## Critical

None remaining.

1. **RUN_START additive contract and lock-recovery operation gap: RESOLVED.** Revised Phase 1B spec lines 126 and 132 add only `RUN_START`, define exact PASS/non-PASS data, preserve existing operation semantics, and state that lock recovery is session history rather than a gateway operation. Plan lines 15 and 98-102 match it.
2. **Failed-rerun triage authority: RESOLVED.** Spec line 292 and plan lines 57-59 and 280 allow only reasoned reruns of prior PASS attempts and block prior FAIL/BLOCKED duplicates without inventing approval or policy-event authority.
3. **Zero-byte manifest entries: RESOLVED.** Plan line 132 defines integer `size` with minimum 0, preserves B3 publication deferral, and Task 1 lines 150-151 and 159 require zero-byte acceptance and negative-size rejection.

## Important

1. **POST_COMMAND data remains normatively contradictory: OPEN.** Phase 1B spec line 130 says `data` is null for every non-PASS branch other than RESOLVE/BLOCKED. Plan lines 108-110 instead require the full POST data object for POST_COMMAND/FAIL and POST_COMMAND/BLOCKED. Both cannot be implemented by one exact `oneOf` schema. Fix: revise spec line 130 to explicitly allow the closed POST FAIL/BLOCKED data shape, while retaining null data for POST NOT_CONFIGURED/POLICY_VIOLATION/INVALID_STATE and all PRE/RUN_START non-PASS branches.
2. **Fingerprint framing is exact, but input glob expansion is not: OPEN.** Spec line 297 and plan lines 63-69 define deterministic frame bytes, ordering, NO_MATCH, containment, size, and hashes. They do not define the supported glob grammar or matching engine for Phase 1A `inputPaths`, including canonical `gradle/**`, `src/main/**`, and `src/test/**` entries. Different Python APIs disagree about whether `**` itself yields descendants and directories, while plan line 69 also says non-regular matches are rejected. Fix: define the allowed metacharacters and exact repository-relative match algorithm; state that `dir/**` recursively selects contained regular files, how intermediate directories and symlinks are treated, and add vectors for every canonical pattern form.

Prior Important dispositions:

- **Lock representation/acquire/release/stale recovery and reservation repair: RESOLVED.** Spec line 286 and plan lines 49-53 define atomic lock-directory acquisition, closed owner evidence, compare-and-release, dead-and-expired recovery, quarantine, immutable history, and RESERVED repair.
- **Attempt IDs, references, and Phase 1A compatibility: RESOLVED with one Minor wording issue below.** Spec line 296 and plan lines 28-45 define exact paths, tuple equality, cross-array uniqueness, and additive optional command-result fields with B2 semantic requiredness; Task 1 line 159 preserves all Phase 1A valid fixtures.
- **Spawn/exit/timeout/resource/redaction/publication mapping: RESOLVED except for the POST schema conflict above.** Plan lines 96-126 provide the exhaustive result/reservation/control matrix and preserve Phase 1A-null BLOCKED command-result fields.
- **Bounded byte redaction: RESOLVED.** Spec line 299 and plan lines 77-90 define strict incremental UTF-8, invalid/binary handling, chunk/carry/pattern/output bounds, exact patterns, cap behavior, and no secret-file reads; Task 5 line 231 covers boundaries.
- **POSIX environment and process-tree termination: RESOLVED with one Minor fixture issue below.** Spec line 298 and plan lines 71-75 define POSIX-only execution, exact environment keys, a new process session, and bounded SIGTERM/SIGKILL process-group cleanup.
- **Crash repair: RESOLVED.** Spec line 300 and plan lines 51-53 and 121-126 define process-attempt-first truth, monotonic BLOCKED repair, visible unrepaired RESERVED state, and no automatic relaunch.
- **Closed launch boundary: RESOLVED.** Plan lines 7, 115, 248-259 permit `Popen` only through the closed `command-runner.sh run` orchestration and require literal ordered shell forms.

## Minor

1. **Transient lock owner conflicts with the universal `$id` wording.** Plan line 43 says every JSON artifact has `$id` equal to its reference, while line 51 defines `owner.json` with exactly four fields and no `$id`. Fix: narrow line 43 to schema-versioned run/evidence artifacts, or explicitly exempt transient lock-owner control JSON.
2. **Fake-wrapper interpreter availability is still implicit.** Plan line 73 copies `PATH` only when present, while lines 208 and 213 do not define the fake `./gradlew` shebang/interpreter. Fix: require an absolute POSIX fixture shebang whose interpreter existence is checked, or require a non-empty allowlisted `PATH` and a resolvable fixed `sh` before the real POSIX launch test.
3. **ASCII cleanliness: RESOLVED.** A static non-ASCII scan of the revised Phase 1B spec and Phase 1B-2 plan returned no lines; the prior corrupted plan text is gone.

# Findings

## Critical

1. **`start` and stale-lock recovery have no approved schema-valid result.** Plan lines 102-106 require `start_run` to return a `gateway_result` and to emit a recovery gate result, but do not assign an operation or a valid result branch. The approved operation enum is only `PREFLIGHT`, `RESOLVE`, `PRE_COMMAND`, `POST_COMMAND`, and `PRE_DONE_CLAIM` (Phase 1B spec lines 121-132), while the current v1 schema permits only `PREFLIGHT` and `RESOLVE` (gateway schema lines 12-13). Adding `START_RUN` or `LOCK_RECOVERY` reopens the approved enum; reusing `PRE_COMMAND` misstates an operation and lacks a command/attempt. Fix: obtain an approved operation/result contract for start and recovery before implementation, then specify the exact schema branches, data, artifact path, and exit mapping.

2. **Failed-attempt triage invents authority unavailable in Phase 1A.** Plan line 122 requires a recorded failure-triage approval or event, but the approval enum has no triage type and is audit-only (approval schema lines 23-32; Phase 1B spec lines 253-260). The policy-violation enum has no triage event and cannot grant authority (policy schema lines 22-31). The parent design requires the separate `failure-triage` procedure before rerun (design lines 103-110 and 220-224). Fix: approve a closed immutable failure-triage artifact and its rerun-authority rule, or explicitly defer failed-command reruns. Do not overload approval or policy-violation records.

3. **The proposed manifest rejects valid empty logs.** Plan line 60 requires every artifact `size` to be positive, but a successful command may produce an empty stdout or stderr log and Phase 1B finalization must manifest every immutable artifact (Phase 1B spec lines 326-334). Fix: define size as an integer byte count with minimum `0`, and add empty-stdout and empty-stderr fixtures. Keep manifest publication deferred as already required by plan line 42.

## Important

1. **Fingerprint inputs and canonical bytes are unspecified.** Plan lines 52-54 and 124 name `argvHash`, `inputFingerprint`, and `environmentFingerprint` but never define their bytes, path/glob expansion order, missing-file/symlink behavior, working-directory inclusion, or environment key/value encoding. This controls duplicate execution and rerun enforcement, while the parent design requires command ID, argv, working directory, declared inputs, and allowlisted environment in the cache key (design lines 95-97). Fix: lock an ASCII/UTF-8, length-delimited canonical encoding; sorted normalized declared paths with content digests; explicit missing/escape behavior; and the exact allowlisted environment map in the plan and tests.

2. **Run locking is metadata, not an acquire/release protocol with reservation proof.** Plan lines 52-54 describe a mutable embedded `lock`, and lines 102-106 name `with_run_lock`, but specify no exclusive lock object, owner-ID generation, compare-and-release rule, release state, stale proof artifact, or recovery ordering. Concurrent writers can otherwise validate and overwrite the same session. The spec requires serialized shared work and explicit stale-lock evidence (Phase 1B spec lines 279, 285-286). Fix: define the exclusive lock-file/creation protocol, immutable owner token, validated liveness/age evidence, recovery artifact permitted by the approved result contract, and recovery of a `RESERVED` attempt before accepting a new writer.

3. **Attempt identity and result correlation are incomplete and risk a Phase 1A v1 break.** Plan line 54 puts `attemptId` only in the reservation; line 58 puts it only in `process-attempt`; `command-result` v1 has no attempt ID (command-result schema lines 15-39). The plan neither defines `$id == published reference` nor the required uniqueness of command-result/process-attempt refs across session arrays and reservations. It also calls for compatible extensions at plan line 14 without listing an additive v1 strategy or fixture preservation. Fix: define immutable IDs, exact repository-relative paths, reference equality/uniqueness rules, and either an additive optional `attemptId` plus B2 semantic requirement or an approved new result schema. Add regression validation for every existing Phase 1A valid fixture unchanged.

4. **Spawn, timeout/resource, redaction, and result mappings are ambiguous.** Plan lines 54, 58, 64, 139, and 155 leave no exact mapping from `SPAWN_FAILED`, `TIMED_OUT`, and `RESOURCE_LIMIT` to reservation state, command-result result, gateway result, and control exit. A Phase 1A BLOCKED command result must have null process exit, hashes, and log paths (command-result schema lines 75-96), while the plan says POST BLOCKED may preserve a child exit (line 64). Fix: state an exhaustive table. In particular, distinguish a spawn failure from a launched child, make redaction failure BLOCKED with the Phase 1A-null command-result fields and preserved process-attempt facts (Phase 1B spec lines 283-284), and specify timeout/resource termination and exit behavior.

5. **The streaming/redaction security contract is not executable as written.** Plan lines 139-141 require chunk handling and deterministic caps but omit exact cap values, byte-vs-text decoding, invalid UTF-8/binary policy, secret-pattern maximum length, carry length, truncation marker bytes, and write-failure boundary. A sufficient carry cannot be tested without a bound. Fix: define byte-level input handling, a finite maximum secret literal/pattern width and carry length, UTF-8 replacement or binary blocking policy, per-stream/total caps, and tests for split multibyte and invalid-byte data.

6. **The environment and child-lifecycle boundary are underspecified.** Plan lines 137-141 never enumerate the child environment or its executable availability. A minimal environment must still support the approved fake/POSIX `./gradlew` wrapper, and the exact map must feed the environment fingerprint. Killing a process also does not define process-group/tree termination on POSIX and Windows. Fix: name the allowed keys, source/normalization rules, `PATH`/interpreter policy for the fixture wrapper, and platform-specific new-session/process-group creation plus bounded escalation and cleanup.

7. **Crash recovery after a published process attempt is only tested, not designed.** Plan line 155 requires the crash case, but line 157 does not define reconciliation when `process-attempt` exists before the session reference/result transition. Phase 1B finalization later rejects unreferenced artifacts (spec lines 331-336), so a restart cannot simply ignore it. Fix: specify recovery scanning, identity validation, monotonic repair or permanent BLOCKED transition, and the point at which the process-attempt reference is durably appended.

8. **Gateway branches and launch boundary need a closed matrix.** Plan line 64 defines only selected POST branches and conflicts internally by requiring POST BLOCKED data while calling all POST non-PASS exceptional; it omits exact `INVALID_STATE`, `POLICY_VIOLATION`, and `NOT_CONFIGURED` branches. Lines 7, 15, 141, and 180 also alternately call the shell runner and helper the launching authority. Fix: list every operation/result/data/exit combination, including `start` after the approved decision, and state that only the runner-reachable closed helper orchestration may call `Popen`; standalone helper operations must not expose launch capability.

## Minor

1. **Corrupted text:** plan line 23 contains `child?` followed by non-ASCII bytes. Replace it with ASCII text such as `child process native`.

# Verification Evidence

- Command: static inspection only.
- Result: plan/spec/schema/helper consistency review completed; no helper, Gradle, product, test, server, Docker, HTTP/API, database, migration, seed, or infrastructure command was run.
- Re-review: inspected revised Phase 1B spec lines 126, 130, 132, 286, 292, and 296-300; revised Phase 1B-2 plan lines 28-132 and 136-284; canonical registry `inputPaths`; and an ASCII scan of both revised documents.
- Re-review result: Critical none; Important 2; Minor 2 open and 1 resolved; overall FAIL.
- Final static re-review: inspected revised Phase 1B spec lines 126, 130, 132, 286, 292, 296-300, and 330; revised Phase 1B-2 plan lines 28-139, 164-166, 184-185, 204-205, 217, 221-222, 240-241, and 257-289; all prior dispositions; and final ASCII cleanliness.
- Final static re-review result: Critical none; Important none; Minor none; PASS / APPROVED.

# Historical State At Execution
The revised Phase 1B specification and Phase 1B-2 plan are approved with `status: done`. All prior findings are resolved. This was static review only; no specification, plan, schema, helper, test, or implementation file was edited by this reviewer.

# Historical Next Handoff
- Next role: phase-1b-2-implementation-agent
- Required reading:
  - [Phase 1B specification](../../../docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md)
  - [Phase 1B-2 implementation plan](../../../docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md)
  - [This review](phase-1b-2-plan-reviewer.md)
- Remaining work: implement the approved Phase 1B-2 plan task by task with its required RED/GREEN evidence and independent reviewer checkpoints.
- Evidence required: implementation diff, contract-test outputs, temporary fake-wrapper evidence, and the plan-required task/final reviews; product commands remain NOT RUN.
