# AI Workflow Enforcement Phase 1B-2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to implement this plan task by task. Use strict TDD: make each focused test RED, implement only enough for GREEN, run the listed regressions, then obtain the named independent reviewer checkpoint before the next task.

**Goal:** Implement the supported Phase 1B-2 command gateway with structured RUN_START, exclusive OPEN-run locking, fail-closed PRE_COMMAND policy, POSIX argv-only execution, bounded byte-stream redaction, and immutable POST_COMMAND evidence.

**Architecture:** Bash remains closed transport. `workflow_helper.py` owns validation, fingerprints, lock/session recovery, orchestration, `Popen`, redaction, and evidence writes. Only the closed orchestration helper reachable from `command-runner.sh run` may call `Popen`; standalone RUN_START, PRE_COMMAND, and POST_COMMAND helper operations and `workflow-gate.sh` never launch. `.state/run-session.json` is the Phase 1B-2 control record; manifest publication, `run.json`, finalization, done claims, and completeness remain Phase 1B-3.

**Tech Stack:** POSIX Bash, Python 3 standard library, Python `jsonschema` with `Draft202012Validator` and `FormatChecker`, `unittest`, temporary repositories, harmless fake `./gradlew`.

## Global Constraints

1. Owning feature: `none`. Modify only the Phase 1B workflow files named by a task. Do not modify product source, product tests, Gradle/application configuration, canonical state, migrations, seeds, Docker, API, database, infrastructure, or product documentation.
2. Preserve all approved Phase 1A and Phase 1B-1 semantics and valid fixtures. Changes to `command-result.schema.json` are additive optional fields only; Phase 1B-2 semantic checks make them mandatory for newly written results.
3. RUN_START is the single additive Phase 1B-2 gateway operation. Lock recovery is session history, never another operation.
4. Only `command-runner.sh run` reaches launch orchestration. No command string, raw argv append, inline JSON, `eval`, `sh -c`, `bash -c`, `shell=True`, `shlex.split`, glob expansion, or environment-selected executable is allowed.
5. Current helper preflight runs on every public gateway invocation. Missing, malformed, mismatched, or stale helper evidence blocks before launch.
6. Only the POSIX `./gradlew` profile can execute. RISKY, DESTRUCTIVE, migration, seed, deployment, production mutation, secret change, bulk mutation, `gradlew.bat`, and all non-POSIX execution are blocked or NOT_CONFIGURED as specified below.
7. Future tests execute only helper/gateway contracts in temporary repositories with a harmless fake `./gradlew`. Never run repository Gradle, build, product tests, server, Docker, HTTP/API, database, migration, seed, or infrastructure.
8. All new schemas are closed Draft 2020-12 schemas. Continue strict UTF-8 JSON loading, duplicate-key/non-finite rejection, internal schema allowlisting, `FormatChecker`, deterministic errors, path containment, exclusive writes, validation-before-publication, `fsync` where supported, atomic rename, and read-only immutable artifacts where supported.
9. Shared exits remain exact: `0 PASS`, `1 FAIL`, `2 BLOCKED`, `3 NOT_CONFIGURED`, `4 POLICY_VIOLATION`, `5 INVALID_STATE`, `6 NOT_APPLICABLE`, `7 SKIPPED_WITH_REASON`. Child exit codes are stored only in `processExitCode`.
10. Do not stage or commit. Preserve pending-Issue `403`/reconciliation metadata and Phase 1B-1 PASS history.

---

## Closed Phase 1B-2 Contracts

### Exact Paths, IDs, And Reference Equality

For run `R`, command `C`, attempt `A`, and event `E`:

```text
sessionRef       = .ai-runs/R/.state/run-session.json
lockOwner        = .ai-runs/R/.state/lock/owner.json
commandResultRef = .ai-runs/R/commands/C/A.json
processAttemptRef= .ai-runs/R/process-attempts/C/A.json
stdoutPath       = .ai-runs/R/logs/C/A.stdout.log
stderrPath       = .ai-runs/R/logs/C/A.stderr.log
policyEventRef   = .ai-runs/R/policy-violations/E.json
gateResultRef    = .ai-runs/R/gate-results/<stage>-E.json
```

Every schema-versioned immutable, session, or evidence artifact `$id` equals its repository-relative reference exactly. Path segments equal embedded `runId`, `commandId`, and `attemptId`. Session reference arrays are unique individually and across arrays; reservation refs are unique and must occur exactly once in their matching session arrays. A command result and process attempt for one reservation share the exact run/command/attempt tuple. The transient `.state/lock/owner.json` and quarantined copies are closed embedded-schema control JSON, never artifacts or session references, and do not carry or satisfy artifact `$id` equality.

Add optional `attemptId` and `processAttemptRef` properties to `command-result.schema.json`; do not add them to its required array so all Phase 1A v1 fixtures remain unchanged and valid. Phase 1B-2 semantic publication requires both fields and exact equality for every new command result.

### Run Session And External Lock

`run-session.schema.json` requires schema identity, `runId`, `taskKey`, `startedAt`, `workingDirectory`, `environment`, `state`, reference arrays, `reservations`, `lockRecoveries`, and `redactionApplied`. Phase 1B-2 creates and accepts only `state: OPEN`; `FINALIZING` is reserved for Phase 1B-3.

The active lock is external to the session. Acquire `.state/lock/` by atomic `mkdir`; then exclusively publish closed `.state/lock/owner.json` with exactly `ownerId`, `runId`, `pid`, and `acquiredAt`. Reuse the existing conservative 300-second recent-owner interval. Release rereads and compares all four values before removing `owner.json` and the empty lock directory. A live owner or an owner younger than 300 seconds blocks. Recovery requires both a dead PID and an `acquiredAt` age of at least 300 seconds. Recovery rereads the same owner bytes, atomically renames `.state/lock/` to `.state/lock.recovery-<recoveryId>/`, atomically creates a fresh `.state/lock/`, and exclusively writes the replacement owner; any rename/mkdir/write collision blocks without deleting either record. Under the replacement lock, append one closed session `lockRecoveries` item with exactly `recoveryId`, `runId`, `recoveredOwnerId`, `replacementOwnerId`, `previousPid`, `previousAcquiredAt`, `recoveredAt`, and `reason: DEAD_AND_EXPIRED`. Validate the quarantined owner against the recorded fields, remove only that quarantine, then compare-and-release the replacement lock.

On lock acquisition, scan every RESERVED reservation. Derive its one exact `processAttemptRef` from command/attempt IDs. If a schema-valid, tuple-matching launched process attempt exists, create a monotonic BLOCKED repair command result and transition the reservation to BLOCKED under the replacement lock. If the attempt is missing, malformed, contradictory, or safe immutable publication cannot complete, return BLOCKED or INVALID_STATE as appropriate, leave RESERVED visible, and never relaunch automatically.

### Reservations And Reruns

Each reservation requires `attemptId`, `commandId`, all three fingerprints, `reservedAt`, `state`, terminal fields/refs, `rerunReasonHash`, and `rerunOfAttemptId`. First attempts store both rerun fields as null. A duplicate fingerprint whose prior reservation is PASS may reserve only when `--rerun-reason-file` resolves inside the repository, is a regular non-secret file, is UTF-8, contains exactly one non-empty line with no CR/LF after normalization, and is at most 1024 Unicode scalar values and 4096 UTF-8 bytes. Store SHA-256 of normalized reason bytes plus `rerunOfAttemptId`; never store raw text.

Missing/invalid reason for a prior PASS returns POLICY_VIOLATION, appends immutable `MISSING_RERUN_REASON`, and creates no reservation. Any duplicate of FAIL or BLOCKED returns BLOCKED with `FAILURE_TRIAGE_NOT_CONFIGURED`, creates no reservation, and creates no approval/policy surrogate. An existing RESERVED duplicate is handled only by RESERVED recovery. Failed-attempt reruns remain deferred to a future approved failure-triage contract.

### Fingerprint Framing

Use SHA-256 over a byte sequence of explicit UTF-8 frames. Each frame is:

```text
uint64_be(len(labelBytes)) || labelBytes || uint64_be(len(valueBytes)) || valueBytes
```

`argvHash` frames labels `argv[0]`, `argv[1]`, ... in token order and values as exact argv tokens. `inputFingerprint` frames `commandId`, normalized repository-relative POSIX `workingDirectory`, then each registry `inputPaths` item in declaration order.

The Phase 1B-2 `inputPaths` grammar has exactly two forms:

1. A repository-relative literal regular-file path with no `*`, `?`, `[`, `]`, `{`, or `}`.
2. A repository-relative directory prefix ending exactly in `/**`, with a non-empty prefix and no other glob metacharacter.

For both forms, reject traversal, absolute paths, URI/scheme prefixes, backslashes, empty components, and normalization outside the repository as `INVALID_STATE`. A literal path must exist after normalization, remain contained, and be a regular file; missing, directory, symlink, or special-file literals are `INVALID_STATE`. For `dir/**`, resolve the prefix without following symlinks and recursively walk it with `followlinks=False`; reject any symlink encountered even when it would remain contained, ignore directory entries themselves, include only contained regular files, and sort normalized POSIX repository-relative file paths by UTF-8 byte order. A missing directory or a tree containing no regular files emits exactly `frame("NO_MATCH", pattern)`. For each included literal/matched file, frame `path`, decimal `size`, and lowercase `sha256`. Stat/open/read changes or errors return INVALID_STATE before reservation; no partial fingerprint is accepted. `environmentFingerprint` frames the exact child environment sorted by key, one key/value pair at a time.

### Child Environment And POSIX Lifecycle

On `os.name != "posix"`, execution orchestration returns NOT_CONFIGURED/exit 3 before `Popen`; Windows contract tests mock `Popen` for argument assertions or skip only the POSIX launch case. Build the child environment from an empty map, copying only `PATH`, `JAVA_HOME`, `GRADLE_USER_HOME`, `HOME`, `TMPDIR`, `LANG`, and `LC_ALL` when present. Normalize keys/values to strings, reject NUL/newline values, and reject keys matching case-insensitive `TOKEN|SECRET|PASSWORD|PASSWD|API_KEY|PRIVATE_KEY|AUTH|COOKIE|CREDENTIAL`. Require copied `PATH` to be present and non-empty. Require exact absolute `/bin/sh` to exist, be a regular file, and be executable; otherwise return NOT_CONFIGURED before launch. The fake wrapper begins with exact bytes `#!/bin/sh\n`, uses shell builtins only, and accepts no interpreter selection from caller arguments or environment. The fingerprint hashes the exact sorted child environment map.

Launch with list argv, `shell=False`, contained cwd, exact environment, closed stdin, separate pipes, and `start_new_session=True`. Until a future registry timeout field is approved, use a conservative 3600-second process timeout. Timeout/resource cleanup sends SIGTERM to the child process group, waits at most 5 seconds, sends SIGKILL if needed, then waits at most 5 additional seconds for reap. Failure to reap is BLOCKED and remains in process-attempt facts. Never signal an unrelated PID/process group.

### Bounded Byte-Stream Redaction

Read stdout and stderr concurrently in 65536-byte chunks with strict incremental UTF-8 decoders. Invalid or incomplete UTF-8 is redaction uncertainty. Limit stdout and stderr separately to 1048576 bytes and combined input to 2097152 bytes. The maximum configured literal or fixed-pattern match width is 4096 bytes; retain 8192 bytes of carry per stream. Crossing any cap stops publication, terminates the process group, deletes temporary logs, and returns BLOCKED; no truncated log is published.

Apply these literal Python regular expressions to decoded text, replacing the final value group with `[REDACTED]` while retaining the prefix and any quote delimiters:

```text
Authorization header: (?im)^(Authorization:[ \t]*(?:Bearer[ \t]+)?)([^\r\n]+)$
Cookie header:        (?im)^((?:Cookie|Set-Cookie):[ \t]*)([^\r\n]+)$
Bearer token:         (?i)\b(Bearer[ \t]+)([^\s\r\n]+)
Secret assignment:   (?i)\b((?:token|access_token|refresh_token|password|passwd|secret|api_key|private_key|credential)[ \t]*[:=][ \t]*)(?:"([^"\r\n]+)"|'([^'\r\n]+)'|([^\s\r\n]+))
```

Measure each matched value after UTF-8 encoding; an empty or over-4096-byte candidate is UNSCRUBBED uncertainty, not safe text. Once a sensitive header/assignment prefix is seen, retain explicit pending-sensitive state; reaching the 8192-byte carry bound without a terminator blocks instead of discarding the prefix. Public configured literals are exactly empty until an approved non-secret configuration source exists. Tests may inject bounded literals through an internal-only helper argument. No `.env`, credential store, key file, or other secret file is read.

### Gateway Operation Matrix

The schema has only the listed Phase 1B-2 branches; N/A and skip are not emitted by these operations.

| Operation | Result | Data | Exit |
|---|---|---|---:|
| RUN_START | PASS | exactly `runId`, `taskKey`, `sessionRef` | 0 |
| RUN_START | BLOCKED | null | 2 |
| RUN_START | NOT_CONFIGURED | null | 3 |
| RUN_START | POLICY_VIOLATION | null | 4 |
| RUN_START | INVALID_STATE | null | 5 |
| PRE_COMMAND | PASS | exactly `runId`, `commandId`, `attemptId`, `argvHash`, `inputFingerprint`, `environmentFingerprint`, `workingDirectory`, `argv` | 0 |
| PRE_COMMAND | BLOCKED | null | 2 |
| PRE_COMMAND | NOT_CONFIGURED | null | 3 |
| PRE_COMMAND | POLICY_VIOLATION | null | 4 |
| PRE_COMMAND | INVALID_STATE | null | 5 |
| POST_COMMAND | PASS | exactly `runId`, `commandId`, `attemptId`, `processExitCode`, `processAttemptRef`, `commandResultRef` | 0 |
| POST_COMMAND | FAIL | exactly the same POST data shape, with exact non-zero `processExitCode` | 1 |
| POST_COMMAND | BLOCKED | exactly the same POST data shape; `processExitCode` is nullable and preserves a known child exit | 2 |
| POST_COMMAND | NOT_CONFIGURED | null | 3 |
| POST_COMMAND | POLICY_VIOLATION | null | 4 |
| POST_COMMAND | INVALID_STATE | null | 5 |

RUN_START is the only additive start operation and does not change existing PREFLIGHT/RESOLVE semantics, including the RESOLVE/BLOCKED prerequisite data exception. All non-PASS RUN_START and PRE_COMMAND data is null. POST_COMMAND/FAIL and POST_COMMAND/BLOCKED use the exact six-field closed POST data object shown above; POST_COMMAND/NOT_CONFIGURED, POST_COMMAND/POLICY_VIOLATION, and POST_COMMAND/INVALID_STATE have null data. Standalone helper `run-start`, `pre-command`, and `post-command` operations validate/persist only and never call `Popen`. Only `execute-command`, reachable from closed `command-runner.sh run`, orchestrates PRE, launch, and POST in one helper process.

### Exact Execution Outcomes

| Condition | Process attempt | Command result | Reservation | POST/runner |
|---|---|---|---|---|
| Spawn failure | `SPAWN_FAILED`, null exit, reason | BLOCKED with null execution/log fields | BLOCKED | BLOCKED/2 |
| Exit 0 and fully scrubbed | `LAUNCHED`, `EXITED`, exit 0, `SCRUBBED` | PASS with both immutable logs | PASS | PASS/0 |
| Non-zero and fully scrubbed | `LAUNCHED`, `EXITED`, exact non-zero exit, `SCRUBBED` | FAIL with both immutable logs and exact exit | FAIL | FAIL/1 |
| Timeout or resource/output cap | launched facts, `TIMED_OUT` or `RESOURCE_LIMIT` | BLOCKED with null execution/log fields; temps deleted | BLOCKED | BLOCKED/2 |
| Invalid UTF-8, redaction, or write uncertainty | launched facts with `UNSCRUBBED` | BLOCKED with null execution/log fields; temps deleted | BLOCKED | BLOCKED/2 plus immutable `UNSCRUBBED_EVIDENCE` |
| Process attempt published, later terminal publication fails | immutable process attempt remains | none until recovery repair | remains RESERVED | BLOCKED/2; recovery repairs to BLOCKED or leaves visibly RESERVED |

No branch publishes partial/truncated logs or a false PASS. `process-attempt.schema.json` records run/command/attempt IDs, reservation/start/end times, all fingerprints, working directory, launch status, nullable child exit, termination, redaction status, and reason, but no argv, output, environment value, absolute path, or secret.

### Manifest Contract And Deferral

`artifact-manifest.schema.json` has schema identity, `runId`, `generatedAt`, `algorithm: SHA-256`, and unique closed artifact entries with `path`, lowercase 64-hex `sha256`, integer `size` with minimum 0, and closed kind. Add fixtures containing zero-byte stdout and stderr logs. Phase 1B-2 adds and validates the schema/fixtures only. It never publishes `artifact-manifest.json`, closes the directory, writes `run.json`, enters FINALIZING, removes `.state`, validates done claims, aggregates results, or claims completeness; all remain Phase 1B-3.

## Implementation Order

### Task 1: Additive Schemas, RUN_START, And Compatibility Fixtures

**Files:**
- Create: `ai/schemas/run-session.schema.json`
- Create: `ai/schemas/process-attempt.schema.json`
- Create: `ai/schemas/artifact-manifest.schema.json`
- Modify: `ai/schemas/gateway-result.schema.json`
- Modify: `ai/schemas/command-result.schema.json`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Create: `ai/fixtures/phase-1b/gateway/run-session-open.json`
- Create: `ai/fixtures/phase-1b/gateway/run-session-invalid-lock-recovery.json`
- Create: `ai/fixtures/phase-1b/gateway/process-attempt-exited.json`
- Create: `ai/fixtures/phase-1b/gateway/process-attempt-spawn-failed.json`
- Create: `ai/fixtures/phase-1b/gateway/artifact-manifest-empty-logs.json`
- Create: `ai/fixtures/phase-1b/gateway/artifact-manifest-negative-size.json`
- Create: `ai/fixtures/phase-1b/gateway/run-start-pass.json`
- Create: `ai/fixtures/phase-1b/gateway/run-start-blocked.json`
- Create: `ai/fixtures/phase-1b/gateway/pre-command-pass.json`
- Create: `ai/fixtures/phase-1b/gateway/post-command-fail.json`

**Interfaces:** Add exactly `run-session`, `process-attempt`, and `artifact-manifest` to the existing internal schema allowlist. Add optional `attemptId` and `processAttemptRef` to command-result. Extend gateway publication fallback operation selection with RUN_START/PRE_COMMAND/POST_COMMAND while preserving PREFLIGHT/RESOLVE branches.

- [ ] **RED:** Add tests for every matrix row, exact data keys, null non-PASS RUN_START data, unknown fields/results, manifest size 0 acceptance and -1 rejection, exact `$id`/reference equality, tuple/path mismatch, duplicate cross-array refs, and unchanged validation of every existing Phase 1A valid fixture.
- [ ] **RED command:** `bash scripts/ai/run-helper-tests.sh` -> FAIL because the three schemas, RUN_START branches, and additive command-result fields do not exist.
- [ ] **GREEN:** Implement only the closed schemas, allowlist entries, exact matrix branches, semantic equality helpers, and fixtures. Do not add execution or manifest publication.
- [ ] **Regression:** `bash scripts/ai/run-helper-tests.sh` -> PASS; `bash scripts/ai/tests/test-runtime-preflight.sh` -> PASS.
- [ ] **Reviewer checkpoint:** Fresh schema reviewer confirms all operation/result/data pairs are closed, Phase 1A fixtures are unchanged, size 0 is valid, and no Phase 1B-3 behavior appears.

### Task 2: RUN_START, Exclusive Lock, Recovery History, And RESERVED Repair

**Files:**
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Create: `ai/fixtures/phase-1b/execution/lock-owner-live.json`
- Create: `ai/fixtures/phase-1b/execution/lock-owner-dead-recent.json`
- Create: `ai/fixtures/phase-1b/execution/lock-owner-dead-expired.json`
- Create: `ai/fixtures/phase-1b/execution/reserved-with-process-attempt.json`

**Interfaces:** `start_run(root, run_id, task_key)`, `acquire_run_lock(root, run_id, owner_id)`, `release_run_lock(lock, expected_owner)`, `recover_run_lock(root, run_id, replacement_owner)`, and `repair_reserved_attempts(root, session)`.

- [ ] **RED:** Temporary-repository tests assert exclusive run/session creation, RUN_START/PASS exact data, no `run.json`, restrictive mode where supported, atomic lock mkdir, closed owner JSON, compare-and-release, owner mismatch refusal, live block, recent-dead block, dead-and-expired-only recovery, stale-owner reread equality, quarantine rename collision, replacement mkdir/write collision, lockRecovery append before quarantine cleanup/release, and no recovery gateway operation.
- [ ] **RED:** Add crash tests for RESERVED plus valid launched process attempt, missing attempt, malformed attempt, tuple mismatch, immutable repair collision, and repair publication failure. Assert valid repair creates BLOCKED result/reservation and every unsafe case remains visible and never calls launch.
- [ ] **RED command:** `bash scripts/ai/run-helper-tests.sh` -> FAIL because RUN_START and run locking/recovery are absent.
- [ ] **GREEN:** Implement exclusive paths and monotonic recovery under the acquired replacement lock. Reuse existing strict JSON, PID/timestamp, exclusive-write, atomic-write, and fsync primitives without reusing the preflight transaction directory.
- [ ] **Regression:** `bash scripts/ai/run-helper-tests.sh` -> PASS; `bash scripts/ai/tests/test-runtime-preflight.sh` -> PASS.
- [ ] **Reviewer checkpoint:** Fresh concurrency reviewer checks lock stealing, owner equality, dead-and-expired conjunction, session history ordering, crash consistency, Windows unsupported-permission behavior, and no automatic relaunch.

### Task 3: Fingerprints, Same-Run Prerequisites, Rerun Policy, And PRE_COMMAND

**Files:**
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Create: `ai/fixtures/phase-1b/execution/fingerprint-tree/empty.txt`
- Create: `ai/fixtures/phase-1b/execution/fingerprint-pattern-vectors.json`
- Create: `ai/fixtures/phase-1b/execution/rerun-reason.txt`
- Create: `ai/fixtures/phase-1b/gateway/prerequisite-pass-same-run.json`
- Create: `ai/fixtures/phase-1b/gateway/prerequisite-wrong-run.json`

**Interfaces:** `length_prefixed_frame(label, value)`, `argv_hash(argv)`, `input_fingerprint(root, command)`, `child_environment(source)`, `environment_fingerprint(env)`, and `pre_command(...)`.

- [ ] **RED:** Assert exact known SHA-256 vectors for empty/non-ASCII UTF-8 frames, argv token order, declaration-order patterns, UTF-8-sorted file matches, zero-byte file size/hash, explicit NO_MATCH, working-directory normalization, symlink escape, non-regular match, read/stat error, and exact sorted environment map. Include canonical vectors for an existing literal file, missing literal, literal directory, literal symlink, existing non-empty `dir/**`, existing empty `dir/**`, missing `dir/**`, nested files, UTF-8 path ordering, and a symlink at every walked depth.
- [ ] **RED:** Reject vectors for bare `*`, suffix/prefix/interior `*`, `?`, `[x]`, `{x}`, `dir/**/more`, `dir/*`, `/**`, empty prefix, empty component, `..`, absolute POSIX/Windows paths, URI/scheme prefixes, and every backslash form as INVALID_STATE.
- [ ] **RED:** Cover current preflight, active OPEN run, Phase 1B-1 resolution, same-run PASS prerequisite equality, wrong-run/path/ID/result rejection, RISKY/DESTRUCTIVE blocking, unregistered/unsafe immutable events, audit-only approvals, first reservation, prior PASS rerun reason bounds/one-line/containment/hash/link, missing reason event, and prior FAIL/BLOCKED/RESERVED duplicate blocking without triage surrogates.
- [ ] **RED command:** `bash scripts/ai/run-helper-tests.sh` -> FAIL because framed fingerprints and B2 PRE/rerun semantics are absent.
- [ ] **GREEN:** Implement the exact frame format, fail-closed input walk, exact environment map, policy precedence, same-run evidence checks, reason hash/link fields, and immutable RESERVED append. Standalone PRE never launches.
- [ ] **Regression:** `bash scripts/ai/run-helper-tests.sh` -> PASS; `bash scripts/ai/tests/test-runtime-preflight.sh` -> PASS.
- [ ] **Reviewer checkpoint:** Fresh policy reviewer confirms deterministic fingerprints, path/read failure handling, failed reruns fully deferred, no approval/event triage overload, event conditions, and no `Popen` reachability.

### Task 4: POSIX-Only Launch And Process-Group Bounds

**Files:**
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Create: `ai/fixtures/phase-1b/execution/fake-gradlew` with exact first line `#!/bin/sh` and shell builtins only

**Interfaces:** `execute_command(root, request)`, `launch_reserved(argv, cwd, env)`, and `terminate_process_group(process, grace_seconds)`.

- [ ] **RED:** Mock tests assert non-POSIX NOT_CONFIGURED with zero `Popen` calls; missing/empty PATH NOT_CONFIGURED; missing/non-file/non-executable `/bin/sh` NOT_CONFIGURED; exact environment keys/normalization/rejections; no caller interpreter lookup; list argv; `shell=False`; contained cwd; `DEVNULL`; separate pipes; `start_new_session=True`; SIGTERM then bounded SIGKILL/reap; no unrelated process-group signal; and standalone run-start/pre/post operations never launch.
- [ ] **RED:** On POSIX only, first assert exact `/bin/sh` exists, is a regular file, and is executable. Then use a temporary repository harmless fake `./gradlew` whose first bytes are exactly `#!/bin/sh\n` and whose body uses only `printf`, `read`, `case`, loops, parameter expansion, and other POSIX shell builtins; prove spaces/metacharacters stay one argv element. Windows skips only this real POSIX launch case and retains mocked argument contracts.
- [ ] **RED command:** `bash scripts/ai/run-helper-tests.sh` -> FAIL because launch orchestration is absent.
- [ ] **GREEN:** Add the one closed `execute-command` orchestration path called only by command-runner; keep public helper operations non-launching. Implement exact POSIX lifecycle and environment.
- [ ] **Regression:** `bash scripts/ai/run-helper-tests.sh` -> PASS; `bash scripts/ai/tests/test-runtime-preflight.sh` -> PASS.
- [ ] **Reviewer checkpoint:** Fresh subprocess reviewer traces every `Popen` call site and confirms only runner orchestration reaches it, with exact process-session cleanup and platform mapping.

### Task 5: Strict Bounded Redaction And Exact Terminal Outcomes

**Files:**
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Create: `ai/fixtures/phase-1b/execution/redaction-classes.json`
- Create: `ai/fixtures/phase-1b/execution/invalid-utf8.bin`
- Create: `ai/fixtures/phase-1b/execution/empty.stdout.log`
- Create: `ai/fixtures/phase-1b/execution/empty.stderr.log`

**Interfaces:** `BoundedStreamScrubber`, `capture_and_scrub(process, limits, injected_literals=())`, `publish_process_attempt(...)`, `publish_command_result(...)`, and `post_command(...)`.

- [ ] **RED:** Test 65536-byte reads, 8192-byte carry, each 1 MiB stream boundary, 2 MiB combined boundary, exact-at-limit success, one-byte-over failure, no truncated publication, strict split valid UTF-8, invalid and incomplete UTF-8, every literal regex class split at every relevant chunk/carry boundary, pending-sensitive prefix overflow, quoted/unquoted assignments, 4096-byte candidate/literal acceptance, 4097-byte rejection, empty public literals, internal bounded literal injection, and proof no secret-file path is opened.
- [ ] **RED:** Parameterize every exact outcome-table row. Assert process-attempt preservation, exact child exit, temp deletion, immutable UNSCRUBBED_EVIDENCE only for redaction/write uncertainty, null BLOCKED execution/log fields, reservation transition, publication-failure RESERVED state, collision/race/second-terminal rejection, and no false PASS.
- [ ] **RED command:** `bash scripts/ai/run-helper-tests.sh` -> FAIL because bounded scrubber and POST persistence are absent.
- [ ] **GREEN:** Implement concurrent bounded byte capture, strict decoders, fixed patterns, fail-closed caps, process-attempt-first publication, exact result mapping, exclusive temp+fsync+rename+read-only publication, session ref append, and one terminal transition.
- [ ] **Regression:** `bash scripts/ai/run-helper-tests.sh` -> PASS; `bash scripts/ai/tests/test-runtime-preflight.sh` -> PASS.
- [ ] **Reviewer checkpoint:** Fresh security/persistence reviewer checks deadlock resistance, all byte bounds, redaction completeness, no secret reads, event precision, crash ordering, and the exact outcome table.

### Task 6: Thin Closed Shell Interfaces

**Files:**
- Create: `scripts/ai/command-runner.sh`
- Create: `scripts/ai/workflow-gate.sh`
- Create: `scripts/ai/tests/test-command-runner.sh`
- Modify: `scripts/ai/workflow_helper.py`

**Interfaces:**

```text
command-runner.sh start --run-id <id> --task-key <key>
command-runner.sh run <command-id> --run-id <id> [--parameters-file <repo-json>] [--rerun-reason-file <repo-text>] [--approval-ref <repo-json>]
workflow-gate.sh RUN_START --run-id <id> --task-key <key>
workflow-gate.sh PRE_COMMAND --run-id <id> --command-id <id> [same optional files]
workflow-gate.sh POST_COMMAND --run-id <id> --attempt-id <id>
```

- [ ] **RED:** Shell contracts assert literal closed forms, duplicate/reordered/missing/extra/raw/string arguments rejected with exact structured result/exit, quoted argv forwarding, unchanged helper result relay, RUN_START exact data, all matrix mappings, and no shell JSON parsing/eval.
- [ ] **RED:** Instrument the helper so only `command-runner.sh run` reaches `execute-command` and exactly one fake child launch; direct workflow-gate stages and direct helper pre/post calls never launch.
- [ ] **RED command:** `bash scripts/ai/tests/test-command-runner.sh` -> FAIL because both scripts are absent.
- [ ] **GREEN:** Implement `set -eu` literal dispatch. Start delegates RUN_START; run delegates one helper orchestration; workflow-gate delegates validation/persistence operations only. No finalization stage is accepted.
- [ ] **Regression:** `bash scripts/ai/tests/test-command-runner.sh` -> PASS; `bash scripts/ai/run-helper-tests.sh` -> PASS; `bash scripts/ai/tests/test-runtime-preflight.sh` -> PASS.
- [ ] **Reviewer checkpoint:** Fresh shell reviewer confirms exact interface, exit relay, one launch route, and absence of command strings/eval.

### Task 7: Repository Boundary And Independent Final Review

**Files:**
- Modify: `AGENTS.md`
- Modify: `ai/work-logs/issue-4/README.md`
- Create: `ai/work-logs/issue-4/phase-1b-2-implementation-agent.md`
- Create: `ai/work-logs/issue-4/phase-1b-2-reviewer.md`
- Modify: `ai/work-logs/index.md`

- [ ] **RED:** Static contract assertions require AGENTS to identify command-runner as the only supported project-command path, keep direct/RISKY/DESTRUCTIVE/non-POSIX execution prohibited, and state that Phase 1B-3 finalization remains absent. Work-log assertions preserve `pending_issue`, exact 403, reconciliation, and Phase 1B-1 PASS history.
- [ ] **RED command:** `bash scripts/ai/run-helper-tests.sh` -> FAIL until boundary wording and evidence records are updated.
- [ ] **GREEN:** Make only the narrow boundary/log changes. Record every actual contract command and outcome, every product command as NOT RUN, all reviewer verdicts, and remaining portability/redaction risks.
- [ ] **Regression:** `bash scripts/ai/tests/test-command-runner.sh` -> PASS; `bash scripts/ai/run-helper-tests.sh` -> PASS; `bash scripts/ai/tests/test-runtime-preflight.sh` -> PASS; `git diff --check` -> PASS; `git status --short` -> intended workflow files only, accounting explicitly for pre-existing user changes.
- [ ] **Reviewer checkpoint:** Independent final reviewer receives approved specs, this plan, complete diff, test outputs, temporary-repository artifact samples, and inventory. Resolve every Critical/Important finding and repeat review until approved.

## Explicit Phase 1B-3 Deferrals

Do not implement or publish `artifact-manifest.json`, `run.json`, FINALIZING transition, `.state` removal, directory closure, PRE_DONE_CLAIM, done-claim checking, final aggregation, finalized verification, applicability, or completeness. Do not transition registry commands to VERIFIED from ignored local evidence. Failed-attempt reruns also remain blocked until a separately approved failure-triage artifact and authority exist.

## Final Execution Report Requirements

Report changed files, every RED/GREEN command and observed output, reviewer verdicts, operation-matrix coverage, exact fingerprint vectors, POSIX/non-POSIX evidence, redaction/output-limit evidence, lock/recovery tests, temporary fake-wrapper proof, all product commands as NOT RUN, pending-Issue reconciliation, Phase 1B-1 PASS history, and Phase 1B-3 deferrals. Never claim manifest publication, finalized run integrity, registry VERIFIED, verification completeness, or unqualified DONE.
