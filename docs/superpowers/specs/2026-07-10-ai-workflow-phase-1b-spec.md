# AI Workflow Enforcement Phase 1B Written Specification

## Status

- Specification status: Approved implementation baseline; independent re-review PASS on 2026-07-10
- Owning feature: none
- Baseline: `docs/superpowers/specs/2026-07-10-ai-workflow-enforcement-design.md`
- State contract: `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md`
- Scope: Phase 1B-1, Phase 1B-2, and Phase 1B-3 only
- First implementation slice: Phase 1B-1

## Goal

Implement the supported command path that resolves only schema-valid registry IDs, constructs argv without shell interpretation, records structured evidence, and blocks unsupported completion claims. Phase 1B is repository gateway enforcement. It does not claim to intercept direct host shell, MCP, file-read, or other external tool calls.

## Fixed Decisions

1. Canonical JSON remains the source of truth. Markdown remains human policy plus generated summary.
2. The helper runtime target is Python 3. The validator is Python `jsonschema` using `Draft202012Validator` and `FormatChecker`.
3. The only schemaVersion 1 executable profile begins with `./gradlew`. Native `gradlew.bat` and other executable profiles remain unsupported.
4. Commands execute as argv arrays with `shell=False`. No `eval`, command string, shell interpolation, shell expansion, or unchecked token append is permitted.
5. Bash files are thin human-facing entry points. Python owns JSON parsing, schema and semantic validation, hashing, atomic writes, structured process execution, redaction, and evidence creation.
6. Runtime preflight is required on every supported gateway invocation. A cached project-state claim never overrides a failed current preflight.
7. Approval JSON is an audit record only. A locally created record cannot create authority.
8. Phase 1B never executes destructive, production, deployment, secret-changing, migration, seed, or bulk mutation commands.
9. Per-run raw evidence is local under `.ai-runs/<run-id>/` and ignored by Git. Durable summaries must be scrubbed.
10. Product commands remain unavailable to AI agents except through the completed `command-runner.sh` supported path.
11. Phase 1B blocks every `RISKY` and `DESTRUCTIVE` command because it has no trusted host approval adapter. Approval files never unlock execution.
12. The initial runtime capability probe is a narrow bootstrap exception: before canonical runtime confirmation, it may report only runtime identity and validator capability and may not read the command registry or plan/execute project commands.

## Phase Boundaries

### Phase 1B-1: Registry Resolution And Parameter Validation

Implement helper-runtime preflight, schema validation, registry semantic validation, ID lookup, closed parameter validation, whole-token placeholder substitution, classification checks, and prerequisite checks. This slice must not execute a resolved project argv.

### Phase 1B-2: Command Execution And Evidence

Add the command runner and workflow gate, execute an already approved resolution with `shell=False`, capture scrubbed logs, persist schema-valid per-run evidence, and record policy and approval audit events.

### Phase 1B-3: Completion Gate And Contract Tests

Add the done-claim gate, leaf-result aggregation, stale-summary checks, and contract tests for all fail-closed behavior.

## File Contract

### Phase 1B-1 Files

| Path | Responsibility |
|---|---|
| `scripts/ai/runtime-preflight.sh` | Thin POSIX entry point that locates an approved Python 3 candidate and invokes helper preflight without shell evaluation |
| `scripts/ai/run-helper-tests.sh` | Argument-free test launcher that uses the same fixed runtime candidate policy and runs only the approved helper unittest module |
| `scripts/ai/workflow_helper.py` | Python helper for preflight, Draft 2020-12 validation, semantic registry validation, and command resolution |
| `scripts/ai/tests/test_workflow_helper.py` | Python standard-library tests for Phase 1B-1 behavior |
| `ai/fixtures/phase-1b/` | Runtime, registry, parameter, classification, and prerequisite contract fixtures |
| `ai/schemas/gateway-result.schema.json` | Structured preflight, resolution, and later leaf-gate control results |
| `ai/schemas/helper-runtime-evidence.schema.json` | Durable scrubbed LOCAL helper-runtime capability evidence |
| `ai/evidence/local-helper-runtime.json` | Current environment-local scrubbed preflight evidence; no executable path, hostname, or secret data |
| `ai/project-state.json` and `ai/project-state.md` | Atomic LOCAL runtime state and generated-summary transition after successful preflight recording |
| `.gitignore` | Ignore transient `ai/.workflow-state-txn/` recovery state |

### Phase 1B-2 Files

| Path | Responsibility |
|---|---|
| `scripts/ai/command-runner.sh` | Supported command entry point: `run <command-id>` and structured options |
| `scripts/ai/workflow-gate.sh` | PRE_COMMAND and POST_COMMAND leaf gates |
| `scripts/ai/workflow_helper.py` | Structured execution, hashing, redaction, atomic evidence writes, and run-index updates |
| `ai/schemas/run-session.schema.json` | Exact-CAS run control state and retained finalized projection receipt |
| `ai/schemas/process-attempt.schema.json` | Secret-free child-attempt facts, including redaction-failure execution outcomes |
| `ai/schemas/artifact-manifest.schema.json` | Exact immutable artifact closure with SHA-256 digests and sizes |

### Phase 1B-3 Files

| Path | Responsibility |
|---|---|
| `scripts/ai/done-claim-check.sh` | PRE_DONE_CLAIM final gate |
| `scripts/ai/tests/run-contract-tests.sh` | Thin test entry point for helper and shell contract tests |
| `scripts/ai/tests/test_workflow_helper.py` | Fixture and final aggregation tests |

No product source, product test, Gradle configuration, application configuration, migration, seed, Docker, API, or database file is modified by Phase 1B.

## Shared Exit Contract

| Exit | Structured result | Meaning |
|---:|---|---|
| 0 | `PASS` | Requested supported-path operation completed |
| 1 | `FAIL` | A child process executed and returned non-zero, or an executed gate failed |
| 2 | `BLOCKED` | Policy requires evidence or authority that is not currently satisfied |
| 3 | `NOT_CONFIGURED` | Required runtime or capability is unavailable |
| 4 | `POLICY_VIOLATION` | Caller request violates a valid closed policy |
| 5 | `INVALID_STATE` | Canonical JSON, schema, semantic contract, or evidence graph is malformed |
| 6 | `NOT_APPLICABLE` | Leaf check is irrelevant to the classified task |
| 7 | `SKIPPED_WITH_REASON` | Policy explicitly permits a documented skip |

The child process exit code is stored only as `processExitCode`. A non-zero child exit maps to workflow `FAIL` and script exit `1`.

## Helper Runtime Preflight

### Candidate Selection

`runtime-preflight.sh` probes the fixed command-name allowlist `python3`, then `python`, from `PATH`. A `python` candidate is accepted only after the helper proves major version 3. It does not use `py`, Node.js, Java, `jq`, or an environment-selected executable. A different executable path requires a future approved configuration field.

The script uses `command -v` with literal allowlisted names and quoted argv invocation. It does not use `eval`, `sh -c`, command strings, aliases, environment-selected executables, or dynamic argument concatenation. A candidate is accepted only when the helper confirms Python major version 3 and imports `Draft202012Validator` and `FormatChecker` successfully.

### Preflight Result

Successful preflight emits one gateway-result envelope containing `operation: PREFLIGHT`, `result: PASS`, `reason: null`, an empty `errors` array, and `data` with:

- `runtimeCommand`: the selected allowlisted command name, `python3` or `python`;
- `runtimeExecutableHash`: SHA-256 of the selected interpreter file, without recording its path;
- `pythonVersion`: full Python version;
- `jsonschemaVersion`: installed library version;
- `validator`: exactly `Draft202012Validator`;
- `formatChecker`: exactly `true`.

Missing Python 3, missing `jsonschema`, unsupported major version, or failed import returns `NOT_CONFIGURED` and exit `3`. It does not fall back to ad hoc parsing.

When Python or `jsonschema` is unavailable, schema validation is impossible. This is the one bootstrap-output exception to the rule that every script result is schema-validated: the shell entry point emits a fixed minimal JSON object with `operation: PREFLIGHT`, `result: NOT_CONFIGURED`, `reason: helper runtime unavailable`, empty `errors`, and `data: null`, then exits `3`. It contains no caller-controlled text. When preflight succeeds, the helper validates its full result against `gateway-result.schema.json`.

### Gateway Result Schema

`gateway-result.schema.json` is a closed Draft 2020-12 schema with exact `oneOf` branches for every allowed operation/result pair and these common fields:

- `$schema`, `$id`, and `schemaVersion: 1`;
- `operation`: `PREFLIGHT`, `RESOLVE`, `RUN_START`, `PRE_COMMAND`, `POST_COMMAND`, or `PRE_DONE_CLAIM`;
- `result`: Script Control Outcome enum;
- `reason`: null only for PASS, otherwise a non-empty string;
- `errors`: deterministic closed objects containing stable `code`, JSON `instancePath`, `schemaPath`, and scrubbed `message`;
- `data`: an operation-specific closed object for PASS; the unchanged closed prerequisite-only object for RESOLVE/BLOCKED; the exact closed POST object for POST_COMMAND/FAIL and POST_COMMAND/BLOCKED; or `null` for RUN_START and PRE_COMMAND non-PASS branches and POST_COMMAND/NOT_CONFIGURED, POST_COMMAND/POLICY_VIOLATION, and POST_COMMAND/INVALID_STATE.

PREFLIGHT PASS data uses the exact nested shape listed above. RESOLVE PASS data contains command ID, classification, repository-relative working directory, final argv array, and deterministic prerequisite IDs. RESOLVE/BLOCKED caused by non-empty prerequisites has `data: { "prerequisiteIds": [...] }` and contains no argv or working directory; this exception is unchanged. RUN_START, PRE_COMMAND, POST_COMMAND, and PRE_DONE_CLAIM branches are added only with their implementation phases and define closed operation-specific data. RUN_START is the single additive Phase 1B-2 operation needed to publish a structured start result: RUN_START/PASS data contains exactly `runId`, `taskKey`, and `sessionRef`; every non-PASS RUN_START branch has `data: null` and uses the shared exit contract. PRE_COMMAND non-PASS data is null. POST_COMMAND/FAIL and POST_COMMAND/BLOCKED use the exact closed POST data object defined by the Phase 1B-2 outcome matrix; POST_COMMAND/NOT_CONFIGURED, POST_COMMAND/POLICY_VIOLATION, and POST_COMMAND/INVALID_STATE use `data: null`. This addition closes the previously omitted structured start result without changing any existing operation semantics. Lock recovery is not a gateway operation. No non-PASS result contains executable argv. The helper validates the result before publication and never emits a reconstructed shell string.

### Canonical Runtime State

The bootstrap probe may inspect only its own runtime/version/import capabilities. After a successful probe, Phase 1B-1 writes `ai/evidence/local-helper-runtime.json` with scrubbed environment-local capability facts, validates it against `helper-runtime-evidence.schema.json`, and then atomically updates the LOCAL helper-runtime entry and matching LOCAL environment notes in `ai/project-state.json`. The parent design's phrase "state CONFIRMED" maps to schema configuration state `VERIFIED` with non-null runtime/version and `RUNTIME_COMMAND` evidence pointing to the durable scrubbed evidence file. CI remains `NOT_CONFIGURED`.

The evidence file records the allowlisted command name and interpreter SHA-256 but not an absolute executable path, hostname, username, environment values, or secrets. It is explicitly environment-local. Every gateway invocation reruns preflight; missing evidence, a mismatched executable hash/runtime/version/capability report, or a failed current probe makes the cached runtime state `STALE` for that invocation and blocks child execution. Cross-machine consumers never treat this file alone as current availability. An identical current report is read-only and does not rewrite timestamps, evidence, canonical JSON, or Markdown.

Evidence, canonical JSON, and generated-summary updates use same-directory temporary files, fsync where supported, and validation before replacement. Because three files cannot be atomically renamed as one operation, the helper uses a locked `ai/.workflow-state-txn/` journal containing prior digests, backup paths, intended new digests, and transaction stage. Every preflight first recovers or rolls back an interrupted transaction before reading canonical state. Success deletes the journal and backups. A failed write or validation restores all prior files and reports `INVALID_STATE`; it never claims synchronization. Missing Python or `jsonschema` leaves canonical LOCAL state unchanged and returns `NOT_CONFIGURED`.

## Schema Validation

1. Load schema and instance as UTF-8 JSON with duplicate-key detection. Duplicate object keys are `INVALID_STATE` even though ordinary JSON parsers would keep the last value.
2. Reject non-JSON numeric constants such as `NaN`, `Infinity`, and `-Infinity`.
3. Require schema `$schema` to be Draft 2020-12 and schema `$id` to match the approved project URN stored in the file.
4. Select schemas from an internal repository-relative allowlist. Instance-controlled paths or URIs never cause arbitrary schema reads or network resolution.
5. Run `Draft202012Validator.check_schema` before validating an instance.
6. Validate with `Draft202012Validator` and `FormatChecker`.
7. Sort validation errors deterministically by JSON path and schema path. Human stderr may summarize them; the structured JSON result remains authoritative.
8. Reject unsupported `schemaVersion` and unknown instance `$schema` values as `INVALID_STATE`.
9. Resolve every repository-relative path against the repository root and reject escape after normalization, including symlink escape for files that must already exist.

No network schema fetch is permitted.

## Registry Semantic Validation

Schema-valid registry JSON is still `INVALID_STATE` when a structural semantic rule fails. The explicit missing-wrapper stale-configuration rule below is the sole `BLOCKED` exception:

1. Command IDs are globally unique.
2. Every non-null argv begins exactly with `./gradlew`.
3. An executable command uses `CONFIGURED_UNVERIFIED` or `VERIFIED`, is not `UNAVAILABLE`, and has static or runtime evidence as required by the schema.
4. A non-executable status has `argv: null`, classification `UNAVAILABLE`, and cannot be resolved for execution.
5. Parameter schema `required` names exactly equal `properties` keys.
6. Parameter patterns are anchored with `^` and `$`, compile successfully, and use the schemaVersion 1 safe-regex subset: character classes, escaped literals, plain literals, `.`, and the linear quantifiers `?`, `*`, and `+`. Parentheses, alternation, counted quantifiers, backreferences, lookarounds, inline flags, conditionals, and nested quantification are rejected.
7. Any argv token containing `{` or `}` is a whole-token placeholder matching exactly `{{parameterName}}`.
8. When parameters are disabled, placeholders are forbidden.
9. When parameters are enabled, the unique placeholder names exactly equal the parameter-schema property names. Repeating the same declared whole-token placeholder is allowed.
10. Every prerequisite ID exists, differs from the owning command ID, and the directed prerequisite graph is acyclic.
11. Prerequisites have a deterministic topological order.
12. Every configured executable working directory exists, resolves inside the repository root, and is a directory.
13. The configured `./gradlew` path exists, resolves inside the repository, and is not a directory. A missing path after prior static evidence is `BLOCKED` as stale configuration; a symlink escape is `INVALID_STATE`.
14. The executable profile is checked again semantically after parsing. Schema validation alone is not treated as the executable allowlist.

## Resolution Interface

The internal helper interface is:

```text
workflow_helper.py resolve
  --repository-root <absolute-path>
  --registry ai/command-registry.json
  --command-id <registry-id>
  [--parameters-file <repository-relative-json-path>]
  --output <path-or-stdout-marker>
```

The future public shell entry point is:

```text
scripts/ai/command-runner.sh run <command-id>
  [--parameters-file <repository-relative-json-path>]
  [--run-id <identifier>]
  [--rerun-reason-file <repository-relative-text-path>]
  [--approval-ref <repository-relative-json-path>]
```

Inline JSON, `key=value` appends, extra trailing argv, and raw command strings are rejected.

`resolve` is a discovery/planning operation: a well-formed absent ID returns `NOT_CONFIGURED` and creates no event. Phase 1B-2 adds a distinct `pre-command` helper operation for execution intent: an absent ID returns `POLICY_VIOLATION`; with an active run it appends `UNREGISTERED_COMMAND`, and without an active run it returns the same structured violation without pretending an event was persisted.

### Resolution Order

Resolution performs these checks in order and stops at the first outcome:

1. current helper preflight;
2. canonical project-state and command-registry schema validation;
3. registry semantic validation;
4. exact command-ID lookup;
5. command configuration status and classification;
6. closed parameter-file parsing and validation;
7. whole-token placeholder substitution;
8. prerequisite graph validation and ordering;
9. if prerequisites are non-empty, return `BLOCKED` because Phase 1B-1 does not yet accept active-run evidence;
10. final argv and working-directory containment checks;
11. structured resolution output.

No child project process is created by the Phase 1B-1 resolver.

## Result Mapping Before Execution

| Condition | Result |
|---|---|
| Python 3 or `jsonschema` unavailable | `NOT_CONFIGURED` |
| Canonical JSON parse, schema, format, duplicate-key, or semantic error | `INVALID_STATE` |
| Well-formed command ID absent during discovery/resolution | `NOT_CONFIGURED` |
| Absent command ID submitted to the Phase 1B-2 execution entry point | `POLICY_VIOLATION` plus `UNREGISTERED_COMMAND` event |
| Command status `NOT_CONFIGURED` | `NOT_CONFIGURED` |
| Command status `UNKNOWN`, `STALE`, or `UNCERTAIN` | `BLOCKED` |
| Classification `UNAVAILABLE` | `NOT_CONFIGURED` |
| Classification `SAFE` | continue |
| Classification `RISKY`, with or without a caller-authored approval record | `BLOCKED` |
| Classification `DESTRUCTIVE` | `BLOCKED` in Phase 1B and a `DESTRUCTIVE_WITHOUT_APPROVAL` event for execution attempts |
| Parameters supplied when disabled | `POLICY_VIOLATION` |
| Missing, unknown, wrong-type, or pattern-invalid parameter | `POLICY_VIOLATION` plus `UNSAFE_PARAMETER` event when a run exists |
| Placeholder or parameter-schema inconsistency | `INVALID_STATE` |
| Unknown, cyclic, or malformed prerequisite graph | `INVALID_STATE` |
| Any prerequisite on the Phase 1B-1 pure resolver | `BLOCKED` with ordered prerequisite IDs |
| Phase 1B-2 active-run prerequisite PASS evidence absent | `BLOCKED` |
| Phase 1B-2 evidence reference malformed, outside run, wrong command, or not PASS | `INVALID_STATE` |

## Parameter Resolution

1. A parameter file is a UTF-8 JSON object with duplicate-key detection and a maximum encoded size of 65536 bytes.
2. Its normalized real path must remain inside the repository root and must not be a secret file or reside in `.git/`. A path under `.ai-runs/` is allowed only inside the current run directory.
3. Every parameter value has at most 1024 Unicode scalar values and contains no C0 control character, DEL, line separator, or paragraph separator.
4. The parameter object is validated against the command's closed schema with Draft 2020-12 validation. Pattern checks use `re.fullmatch` on the safe-regex body rather than relying on `$` end-position behavior.
5. Each placeholder occupies one complete argv token. Its validated string replaces that token as one argv element.
6. Parameter values are never reparsed, split on whitespace, expanded as globs or variables, or interpreted as shell syntax.
7. After substitution, any remaining placeholder marker is `INVALID_STATE`.
8. The resolved argv is held in memory for Phase 1B-2 and is never serialized as an executable shell command.

## Classification And Approval

- `SAFE` commands may proceed after all other checks.
- `RISKY` commands are blocked throughout Phase 1B because no trusted approval adapter exists. A later native adapter may change this only through a new approved specification.
- `DESTRUCTIVE` commands are blocked in Phase 1B. This includes database reset/drop/truncate, migrations, seeds, deployment, production mutation, secret changes, and bulk destructive operations.
- `UNAVAILABLE` commands never execute.
- Approval records must validate, match the current run and scope, and contain a non-empty external reference. These checks establish audit consistency only.

## Prerequisite Enforcement

Prerequisites are not auto-executed. Phase 1B-1 validates and orders the graph, then returns `BLOCKED` for any command with prerequisites because active-run evidence does not yet exist. Phase 1B-2 may continue resolution only when a schema-valid command-result reference in the active run has the matching `commandId` and result `PASS`. Historical registry `VERIFIED` state does not prove that a service or transient prerequisite is currently available.

The Phase 1B-2 PRE_COMMAND operation validates that referenced command-result files:

- are listed by the current schema-valid active `run-session.json`;
- resolve within the current `.ai-runs/<run-id>/` directory;
- match the same `runId`;
- validate against `command-result.schema.json`; and
- report `PASS` for the required command ID.

Missing evidence is `BLOCKED`. Contradictory or malformed evidence is `INVALID_STATE`.

## Phase 1B-2 Execution Contract

1. `command-runner.sh start --run-id <id> --task-key <key>` creates a locked schema-valid OPEN run session before command execution. `run` requires that explicit active run ID.
2. PRE_COMMAND uses the execution-intent operation, current preflight, Phase 1B-1 validation, active-run prerequisite evidence, rerun checks, and the unconditional RISKY/DESTRUCTIVE block.
3. Before child launch, the session atomically adds an immutable attempt reservation. Reservations are append-only and move monotonically from `RESERVED` to exactly one terminal state; they are never removed or rewritten to hide a failure.
4. The helper launches the resolved argv with `subprocess` list arguments, `shell=False`, a repository-contained working directory, an allowlisted environment, closed stdin, and no inherited secret-file content.
5. stdout and stderr are captured separately through a bounded streaming scrubber before disk publication. Unbounded in-memory capture is forbidden.
6. The scrubber masks authorization headers, cookies, token/password/secret assignments, sensitive environment values supplied by the runner, and configured literal secrets. Secret files are never read for capture.
7. Every launched process creates a schema-valid secret-free `process-attempt` artifact containing run/command/attempt IDs, timestamps, hashes, native process exit code when available, and redaction status. It never contains process output or environment values.
8. On redaction failure, temporary logs are deleted and no PASS/FAIL command-result is created. A schema-valid BLOCKED command-result with null execution/log fields records the reason, the process-attempt preserves the child facts, and a blocking `UNSCRUBBED_EVIDENCE` event is appended.
9. On successful redaction, command result and logs are written to same-directory temporary paths with exclusive creation and restrictive permissions, validated, flushed, atomically renamed, and made read-only where supported.
10. Approval and policy-violation records are one immutable schema-valid file per ID. Shared session work is serialized with the exclusive `.state/lock/` directory and its closed `owner.json` containing owner ID, run ID, PID, and acquisition time. Acquisition uses atomic directory creation; release compares the complete owner record before removal. A live or recent owner blocks. Recovery is allowed only when the owner is both dead and expired. After rereading the unchanged stale owner, recovery atomically renames the stale lock directory to a recovery-ID quarantine path, atomically creates the replacement `.state/lock/`, and exclusively writes the replacement owner; any collision blocks. The replacement owner appends an immutable closed `lockRecovery` entry to run-session history, validates the quarantined owner again, removes the quarantine, and only then compare-and-releases its replacement lock. Lock recovery is not a gateway operation.
11. A successful exact argv creates PASS command evidence. Registry `VERIFIED` transition additionally requires a durable scrubbed repository work-log summary or external CI artifact; ignored local evidence alone leaves the registry `CONFIGURED_UNVERIFIED`.
12. A non-zero child exit creates FAIL with its exact `processExitCode`; it never becomes a workflow control exit.

## Rerun Contract

The same command ID, argv hash, input fingerprint, and environment fingerprint may not execute twice in one run without an allowed rerun reason. In Phase 1B-2, only a duplicate of a prior PASS attempt may rerun, and only with a bounded one-line UTF-8 reason file whose normalized real path is repository-contained. The reservation stores `rerunReasonHash` and `rerunOfAttemptId`, never the raw reason. Missing reason returns `POLICY_VIOLATION` and appends `MISSING_RERUN_REASON`. Any duplicate of a prior FAIL or BLOCKED attempt is `BLOCKED` because no approved failure-triage artifact or authority exists in Phase 1B-2; approval records and policy events are not overloaded as triage authority. Automated retry and failed-attempt reruns remain deferred.

### Phase 1B-2 Conservative Execution Clarifications

- The command-result and process-attempt references are exactly `.ai-runs/<run-id>/commands/<command-id>/<attempt-id>.json` and `.ai-runs/<run-id>/process-attempts/<command-id>/<attempt-id>.json`. Each artifact `$id` equals its reference, embedded run/command/attempt IDs match the path, and references are unique across session arrays and reservations. Phase 1A version-1 command-result fixtures remain valid: `attemptId` and `processAttemptRef` are additive optional schema fields, with Phase 1B-2 semantic validation requiring them for newly persisted command results.
- Fingerprints are SHA-256 over explicit UTF-8 length-prefixed frames. Argv frames preserve token order. For Phase 1B-2, each `inputPaths` item is either a repository-relative literal regular-file path containing no glob metacharacter, or a repository-relative directory prefix ending exactly in `/**`. Reject every other `*`, `?`, `[`, `]`, `{`, or `}`, plus empty prefix, traversal, absolute path, URI, and backslash, as `INVALID_STATE`. A literal must exist and be a regular file. A directory prefix is walked recursively without following symlinks; any encountered symlink is `INVALID_STATE`, directory entries are ignored, and only contained regular files are included in UTF-8 byte-order by normalized POSIX repository-relative path. A missing or file-empty `dir/**` contributes deterministic `NO_MATCH`; read/stat errors block or return `INVALID_STATE` before reservation. The input fingerprint covers command ID, normalized working directory, patterns in declaration order, and each resulting path, byte size, and SHA-256. The environment fingerprint covers the exact child environment map sorted by key.
- Execution is POSIX-only in schemaVersion 1. The child environment may copy only `PATH`, `JAVA_HOME`, `GRADLE_USER_HOME`, `HOME`, `TMPDIR`, `LANG`, and `LC_ALL` when present, string-valued, and non-secret; secret-named keys are forbidden. Production execution requires a non-empty allowlisted `PATH` value and the exact absolute `/bin/sh` path to exist as an executable regular file. Otherwise execution returns `NOT_CONFIGURED` before launch. The harmless fake wrapper uses exact shebang `#!/bin/sh` and shell builtins only. No interpreter path or lookup is accepted from caller input. A non-POSIX host returns `NOT_CONFIGURED` before launch. POSIX launch creates a new process session, then timeout/resource cleanup sends SIGTERM followed by bounded SIGKILL to the process group.
- Redaction is a bounded byte-stream operation using strict incremental UTF-8. Invalid or incomplete UTF-8 is `UNSCRUBBED_EVIDENCE`. Reads use 64 KiB chunks, each stream is limited to 1 MiB, combined output is limited to 2 MiB, configured literal/pattern width is limited to 4096 bytes, and the scrubber retains 8192 bytes of carry. Reaching any output cap blocks and publishes no truncated log. Required patterns cover authorization headers, cookie/set-cookie headers, bearer tokens, and token/password/secret assignments. The public configured-literal set is empty until an approved non-secret configuration source exists; contract tests may inject bounded literals internally. Secret files are never read.
- Spawn failure, timeout/resource limit, redaction uncertainty, evidence-write uncertainty, and post-launch publication failure never become PASS. A valid existing process-attempt for a stale RESERVED reservation is repaired monotonically to a BLOCKED command result/reservation under the acquired replacement lock when safe; otherwise the reservation remains blocked and is never relaunched automatically.

## Evidence Layout

```text
.ai-runs/<run-id>/
  .state/
    run-session.json
  run.json
  approvals/
    <approval-id>.json
  policy-violations/
    <event-id>.json
  commands/
    <command-id>/
      <attempt-id>.json
  process-attempts/
    <command-id>/
      <attempt-id>.json
  logs/
    <command-id>/
      <attempt-id>.stdout.log
      <attempt-id>.stderr.log
  gate-results/
    <stage>-<event-id>.json
  artifact-manifest.json
  done-claim.json
  done-claim.md
```

`.state/run-session.json` persists through OPEN, FINALIZING, and FINALIZED. Its FINALIZED form is retained read-only as the authoritative finalization receipt and is excluded from the artifact manifest; `run.json` exists only after finalization publication. Repeated command attempts use collision-free result and log names containing an attempt identifier while preserving `commandId` inside JSON. Every schema-versioned immutable, session, or evidence artifact `$id` equals its repository-relative forward-slash reference. The transient `.state/lock/owner.json` is closed embedded-schema control JSON, is never an artifact or reference, and has no artifact `$id` equality requirement.

This per-ID/per-attempt layout explicitly supersedes the parent design's illustrative flat command paths and `approvals.json`. The refinement is required because the approved approval schema represents one record and append-only rerun evidence cannot safely overwrite flat files.

### Run Finalization Lifecycle

1. `start` creates OPEN `.state/run-session.json`; no `run.json` exists.
2. Every reservation and terminal artifact reference is appended monotonically under the run lock.
3. `done-claim-check.sh prepare <run-id> --claim <path>` changes OPEN to FINALIZING atomically. No new command or approval is accepted afterward.
4. PRE_DONE_CLAIM validates the FINALIZING session, all reservations, every discovered artifact, policy events, and the proposed done claim, then derives the complete gate result and candidate `run.json` in memory.
5. Before publishing final artifacts, the finalizer compare-and-swaps the exact FINALIZING session to FINALIZED with a closed `finalizationReceipt`. The receipt retains every schema-defined `run.json` field, canonical done-claim and gate digests plus outcomes, the exact manifest ID/run ID, and the complete expected artifact path/kind identity set.
6. The finalizer publishes the done claim and gate, requires exact evidence closure, and writes `artifact-manifest.json` with repository-relative path, SHA-256 digest, and byte size for every immutable artifact except the retained `.state`, manifest, and final `run.json` themselves.
7. The finalizer schema-validates and publishes the receipt's exact `runProjection` as `run.json` last, then makes the retained FINALIZED session read-only. A read-only `verify-finalized` operation recomputes directory closure and digests, loads the retained receipt as authority, and emits its result outside the run; it never appends evidence to a finalized run.

An in-process validation or publication exception before step 7 invokes bounded rollback while the same validated run-lock owner is still held. Rollback first proves that `run.json` is absent and that `.state/run-session.json` still equals the orchestrator's exact expected FINALIZING or receipt-bearing FINALIZED snapshot, removes only the attributed `done-claim.json`, PRE_DONE_CLAIM gate result, and artifact manifest, then restores the captured OPEN session with the existing compare-and-swap mutation. A changed lock owner, changed sealed session, unsafe cleanup target, cleanup failure, or any appearance of `run.json` prevents rollback and returns `BLOCKED` with `FINALIZATION_RECOVERY_REQUIRED`, retaining the exact recovery state. A crash before step 7 likewise requires explicit stale-lock/session recovery; after `run.json` publication, verification is anchored in the retained FINALIZED receipt plus manifest digests, and a published `run.json` is never rolled back. No PRE_DONE_CLAIM operation reads a finalized `run.json` to construct its authority, so finalization has no circular trust dependency.

## Phase 1B-3 Completion Contract

Phase 1B-3 is an integrity gate, not a task-applicability or verification-completeness authority. Phase 2C owns machine-readable change classification, required-check selection, allowed N/A/skip policy, and unqualified completion gating. Phase 1B-3 therefore must not introduce a caller-authored requirements manifest or claim that omitted checks were permissible. Until Phase 2C exists, any `NOT_APPLICABLE` or `SKIPPED_WITH_REASON` check makes the Phase 1B-3 integrity gate `BLOCKED`; a recorded reason is necessary but not sufficient authorization.

During finalization, `done-claim-check.sh prepare` validates the FINALIZING run session, every reservation and discovered artifact, command result, process attempt, approval, policy violation, gate result, evidence reference, artifact digest, and proposed done claim. Its gateway result includes `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.

Every check-level `evidenceRefs` entry must resolve to evidence owned by the active session and must also appear in the claim's top-level evidence closure. The claim cannot declare a PASS check, executed command, or completed capability as not run. After publication, `verify-finalized` schema-validates the retained FINALIZED session, done claim, manifest, and PRE_DONE_CLAIM result; reconstructs manifest-kind references; recomputes canonical claim/gate identities; and rejects any stale or altered `run.json` field, manifest identity, outcome, or artifact identity.

An overall `PASS` requires:

- `implementationStatus: PASS`;
- at least one applicable check with durable scrubbed evidence;
- every check result exactly `PASS`; Phase 1B-3 rejects N/A and skips because it cannot authorize them;
- every command/evidence artifact actually present represented consistently in checks or explicit `notRunItems`;
- no blocking policy violation;
- no unresolved unexpected 500 or unhandled exception requirement;
- no blockers;
- no stale generated summary when canonical state changed.

Within the claim's stated checks, `NOT_CONFIGURED` cannot be converted silently to PASS. Child `FAIL`, invalid evidence, hidden or unmanifested failure, completion without evidence, or an unresolved blocking policy violation cannot pass the integrity gate.

Detailed control precedence is: invalid artifact or graph -> `INVALID_STATE`; blocking policy violation -> `POLICY_VIOLATION`; executed child failure -> `FAIL`; blocked, not-configured, N/A, or skipped leaf -> `BLOCKED`; otherwise internally consistent all-PASS claimed evidence -> integrity `PASS`. Because `run.json` and done-claim workflow results do not include `INVALID_STATE` or `POLICY_VIOLATION`, their persisted overall result is `BLOCKED` while the gate-result artifact preserves the detailed control outcome.

An integrity PASS cannot support an unqualified overall DONE, prove that all applicable verification ran, or prove that N/A/skips were authorized. Reports must state `Phase 1B integrity PASS; verification completeness NOT EVALUATED` until Phase 2C supplies authoritative applicability policy.

## Contract Test Matrix

Phase 1B tests must cover at least:

- runtime absent, Python 2, missing `jsonschema`, bootstrap-output fixed shape, and successful durable runtime-state recording/rollback;
- duplicate JSON keys and invalid calendar dates;
- unknown schema URI/version and schema path escape;
- duplicate command IDs and required/property mismatch;
- unsupported executable, shell token, raw command, and unresolved placeholder;
- oversized parameter files/values, control characters, unknown/missing/extra/wrong-type values, unsafe regex constructs, catastrophic-pattern attempts, and full-string mismatch;
- parameter values containing spaces and shell metacharacters remaining one inert argv element;
- unknown command and unavailable/stale command;
- every risky and destructive command blocked even with a caller-authored approval file;
- unknown prerequisite, cycle, Phase 1B-1 non-empty prerequisite blocking, Phase 1B-2 missing PASS evidence, wrong-run evidence, and valid same-run PASS;
- attempted repeated execution without reason;
- child non-zero exit preserved separately from workflow exit;
- redaction of each required secret class, process-attempt preservation, temporary-log deletion, and blocking on scrub failure;
- malformed, missing, or contradictory command evidence;
- monotonic reservation transitions, stale-lock recovery, exact directory closure, artifact digest mismatch, evidence-free PASS done claim, and hidden failed leaf result;
- finalization crash points, no post-final append, and read-only finalized verification;
- integrity PASS explicitly reporting `completenessEvaluated: false`;
- stale generated command-registry and project-state summaries;
- supported-path boundary wording and direct-tool bypass event behavior.

Tests use temporary directories and harmless fixture executables only. They do not invoke Gradle, product servers, Docker, databases, migrations, seeds, or HTTP APIs.

## Enforcement Boundary

Phase 1B enforces only calls routed through repository scripts. It can detect and record a known bypass, and done-claim review can block completion after a detected bypass. It cannot prevent or observe every direct host shell, MCP, editor, file-read, search, or external tool invocation. Native runtime adapters and CI enforcement remain later scope.

## Acceptance Criteria

### Phase 1B-1

- Current runtime preflight fails closed and never assumes Python or `jsonschema`.
- The successful bootstrap writes validated scrubbed LOCAL runtime evidence and transactionally synchronizes canonical JSON plus generated summary with recovery-journal tests; failed bootstrap leaves canonical state unchanged.
- All seven Phase 1A schemas validate through an allowlisted Draft 2020-12 validator with FormatChecker.
- Registry semantic invalid cases are rejected before lookup.
- Parameter input is closed, whole-token only, and cannot append raw argv.
- SAFE classification and Phase 1B-1 prerequisite blocking produce the specified outcomes; RISKY and DESTRUCTIVE always block.
- Resolver tests demonstrate that no project process is created.

### Phase 1B-2

- Only `command-runner.sh` executes resolved project argv.
- Execution uses list argv and `shell=False`.
- Schema-valid sessions, reservations, process attempts, results, scrubbed logs, hashes, approvals, and violations are persisted with monotonic and append-only rules. The artifact-manifest schema and fixtures are added in Phase 1B-2, while manifest publication and directory closure remain Phase 1B-3.
- Failure, rerun, approval, and redaction behavior is fail closed.

### Phase 1B-3

- Done claims cannot hide failed, blocked, unmanifested, stale, digest-mismatched, or unsanitized evidence.
- Final aggregation follows the shared result mapping.
- Contract fixtures cover valid and invalid gateway behavior.
- Documentation explicitly reports supported-path enforcement limits.
- The gate reports integrity only and never claims verification completeness before Phase 2C.

## Phase 1B-1 Verification Boundary

The Phase 1B-1 implementation may run only helper-runtime preflight, its durable scrubbed state-record operation, and helper contract tests needed to verify the gateway itself. Gradle, product tests, application server, Docker Compose, HTTP/API, database, migration, seed, and infrastructure commands remain `NOT RUN` until Phase 1B-2 command execution and evidence recording are complete.

## Remaining Later Scope

- Phase 1B-2 command execution and evidence persistence after Phase 1B-1 passes review.
- Phase 1B-3 done-claim gate and full contract suite after Phase 1B-2 passes review.
- Phase 2 reusable skills, authoritative task/change classification, verification applicability/completeness policy, verification-level orchestration, context cache, API smoke runner, and document integration.
- Phase 3 CI gates, native host adapters, and broader interception where supported.
- Native Windows `gradlew.bat` executable profiles.
