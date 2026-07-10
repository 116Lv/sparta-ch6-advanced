# AI Workflow Enforcement Design

## Status

Approved direction, pending written-spec review.

## Problem

The repository has detailed Markdown guidance, but repeated agent decisions and procedures are not backed by durable state or executable gates. Agents can repeatedly rediscover the repository structure, commands, verification flow, and document routes; reread unchanged files; rerun unchanged commands; and duplicate discovery across subagents.

This design moves stable decisions into registries, repeated procedures into skills, mandatory checks into hooks, and reusable discoveries into cache and handoff records. Documentation remains necessary, but it describes or stores executable workflow state instead of compensating for missing enforcement with longer prompts.

## Design Principles

1. Stable facts are discovered once and stored with evidence and invalidation rules.
2. Commands are referenced by registry ID and executed through one gateway.
3. Repeated procedures are isolated as skills with bounded inputs and outputs.
4. Mandatory transitions are blocked by executable hooks when their evidence is absent.
5. Cached results are reused until their declared inputs change.
6. Subagents receive prior discoveries and command evidence instead of rebuilding context.
7. The system reports enforcement limits honestly. Repository scripts cannot intercept a tool call that bypasses the repository gateway unless the host agent runtime provides a native hook adapter.

## Architecture

### Machine-Readable State

Markdown documents are used for human-readable policy and review. Executable scripts must not parse free-form Markdown tables as their primary source of truth.

Machine-readable workflow state is stored in dedicated JSON files:

- `ai/command-registry.json`
- `ai/project-state.json`
- `.ai-runs/<run-id>/run.json`

The corresponding Markdown files explain these records and summarize their current status. JSON is canonical for execution. A registry validation command checks its schema and verifies that generated or summarized Markdown does not contradict it; agents must not maintain two independent sources of truth manually.

### JSON Schemas

Executable JSON state must be validated before use.

Required schemas:

- `ai/schemas/command-registry.schema.json`
- `ai/schemas/project-state.schema.json`
- `ai/schemas/run.schema.json`
- `ai/schemas/command-result.schema.json`
- `ai/schemas/done-claim.schema.json`
- `ai/schemas/approval-record.schema.json`
- `ai/schemas/policy-violation.schema.json`

Scripts reject invalid or unsupported schema versions instead of attempting best-effort parsing. Schema validation is fail-closed: malformed state, unknown required fields, and incompatible versions block the affected workflow action.

### Status Contracts

Schemas define separate enums for different concepts instead of one ambiguous universal status.

- Project fact confidence: `CONFIRMED`, `INFERRED`, `UNKNOWN`, `STALE`, `UNCERTAIN`
- Capability configuration: `UNKNOWN`, `CONFIGURED_UNVERIFIED`, `VERIFIED`, `NOT_CONFIGURED`, `STALE`, `UNCERTAIN`
- Workflow result: `PASS`, `FAIL`, `BLOCKED`, `NOT_CONFIGURED`, `NOT_APPLICABLE`, `SKIPPED_WITH_REASON`
- Script control outcome: `PASS`, `FAIL`, `BLOCKED`, `NOT_CONFIGURED`, `POLICY_VIOLATION`, `INVALID_STATE`, `NOT_APPLICABLE`, `SKIPPED_WITH_REASON`

Values such as `OK`, `DONE`, `PASSED`, `probably-pass`, or `not-needed` are invalid. `NOT_CONFIGURED` means a capability or verification mechanism is not defined. `BLOCKED` means the current task requires that missing or unavailable capability. `NOT_APPLICABLE` means the capability does not apply to the classified task. `FAIL` means execution occurred and failed. `SKIPPED_WITH_REASON` is permitted only when the selected verification policy explicitly allows a skip and records the reason. Human-readable summaries display `NOT_APPLICABLE` as `N/A`; executable JSON never stores `N/A` as the canonical value.

### Stable Context

- `ai/context-map.md`: repository surfaces, ownership, canonical documents, important paths, generated/excluded paths, and minimal reading routes.
- `ai/command-registry.json`: canonical command IDs, argv arrays, classification, evidence, prerequisites, input paths, and verification state.
- `ai/command-registry.md`: human-readable command policy and generated registry summary.
- `ai/project-state.json`: canonical stack, package manager, ports, environment files, services, test frameworks, confidence status, and intake fingerprint.
- `ai/project-state.md`: human-readable project-state explanation and summary.

Canonical JSON and human-authored policy notes have distinct ownership. Markdown summaries use separate sections:

```text
## Human Policy Notes
Human-editable explanation.

## Generated State Summary
Generated from canonical JSON; manual edits are forbidden.
```

Generated sections include a marker such as `<!-- GENERATED SUMMARY FROM ai/command-registry.json. DO NOT EDIT MANUALLY. -->`. Registry validation rejects a generated summary that is stale or inconsistent with canonical JSON.

`ai/document-routing.md` becomes a thin routing gate. It selects an owning feature and a route ID, then delegates repository-wide path and reading decisions to `context-map.md`.

### Cache And Tool Control

- `.ai-runs/<run-id>/`: append-only per-run command metadata, scrubbed logs, verification evidence, and done-claim inputs.
- `ai/workflow-cache.md`: recent run summaries, evidence pointers, file discoveries, and reusable handoff notes; it does not store unbounded raw logs.
- `ai/cache-policy.md`: cache keys, freshness rules, invalidation triggers, and conditions that permit rediscovery.
- `ai/tool-call-policy.md`: limits for broad search, tree scans, repeated file reads, repeated command discovery, and duplicate external tool calls.
- `ai/resource-budget.md`: numeric default limits and required reasons for exceptions.
- `ai/agent-handoff.md`: shared context packet for orchestrator and subagent transitions.

The cache key for a command result includes the command ID, argv hash, working directory, hashes of registry-declared relevant input paths, and an allowlisted environment fingerprint. A rerun against the same key requires an allowed reason. File reads are keyed by normalized path and content hash, not modification time alone. Input hashing must remain scoped so cache calculation does not become another full-repository scan.

Cache reuse is allowed only when declared inputs and relevant environment fingerprints are unchanged. If a changed file cannot be mapped confidently to registry-declared inputs, affected cache entries become `STALE` or `UNCERTAIN`. When dependency mapping is incomplete or ambiguous, the workflow prefers re-verification over unsafe reuse.

Per-run evidence directories avoid shared-write conflicts between subagents. Registry and project-state updates are serialized, written to a temporary file, schema-validated, and atomically renamed. Any lock records its owner, run ID, and creation time so stale locks can be detected rather than silently blocking future work.

### Skills

Skills own repeated multi-step procedures:

- `repo-intake`: populate context map, project state, and command registry after initial setup or valid invalidation.
- `command-runner`: validate a registry ID, invoke command hooks, execute the command, and record the result.
- `verification-runner`: choose and run registered checks for a verification level.
- `api-smoke-verifier`: run declared real HTTP cases and review server evidence.
- `failure-triage`: record root cause before permitting a failed command rerun.
- `docs-sync`: update only canonical documents selected by the context map.
- `review-gate`: verify scope, evidence, cache updates, and completion readiness.

Skill documents define contracts and resource budgets. Executable behavior lives in shared scripts rather than duplicated shell fragments inside each skill document.

### Hooks

- `PRE_TASK`: require context map, project state, registry, cache policy, and route selection. Permit repository intake only when state is missing or invalid.
- `PRE_EDIT`: require ownership, prior-read/cache status, and affected-document route.
- `PRE_COMMAND`: require a registered command ID, safety classification, prerequisites, and a valid rerun reason when duplicated.
- `POST_COMMAND`: record exact result and failure evidence; block silent continuation after failure.
- `PRE_VERIFY`: determine the required verification level and registered verification IDs.
- `POST_VERIFY`: persist results and unresolved failures.
- `PRE_DONE_CLAIM`: require applicable verification evidence, explicit NOT RUN items, API evidence when required, and no unresolved unexpected 500 or unhandled exception.

Hook contracts live under `ai/hooks/`. `scripts/ai/workflow-gate.sh` implements checks shared by the hook stages. `scripts/ai/command-runner.sh` is the command execution boundary and invokes pre/post command checks.

### Command Execution Safety

Agents do not execute raw shell commands directly. Agents request command execution by registry ID:

```bash
scripts/ai/command-runner.sh run <command-id>
```

The command runner resolves the command ID from `ai/command-registry.json`, applies safety checks, invokes pre/post command gates, executes the declared argv without `eval`, and records evidence under `.ai-runs/<run-id>/`. Commands not present in the registry are blocked until scoped discovery or an approved registry update records the command with evidence.

Configured commands use argv arrays rather than raw shell strings. A structured helper executes with shell expansion disabled. Dynamic arguments are accepted only through a registry-declared parameter schema and are never appended as unchecked shell text.

By default, parameters are disabled:

```json
{
  "id": "gradle-test",
  "argv": ["./gradlew", "test"],
  "classification": "safe",
  "parameters": { "allowed": false }
}
```

Commands that require parameters declare placeholders and a closed validation schema. Each supplied value becomes one argv element after validation; it is never interpreted by a shell:

```json
{
  "id": "gradle-test-class",
  "argv": ["./gradlew", "test", "--tests", "{{testClass}}"],
  "classification": "safe",
  "parameters": {
    "allowed": true,
    "schema": {
      "type": "object",
      "additionalProperties": false,
      "required": ["testClass"],
      "properties": {
        "testClass": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_.$*]+$"
        }
      }
    }
  }
}
```

Malformed registry schemas and unresolved placeholders produce `INVALID_STATE`. Unknown parameters, missing required parameters, and parameter validation failures produce `POLICY_VIOLATION`. Both outcomes occur before process execution.

### File Read And Tool-Call Enforcement Boundary

Repository scripts can gate command execution only when agents use `scripts/ai/command-runner.sh`. They cannot completely intercept repeated file reads, broad searches, direct shell invocations, MCP calls, or other host tool calls without a native runtime adapter.

Until native adapters exist, file-read, search, and tool-call rules are enforced through policy, cache records, handoff records, audit checks, and done-claim review. A detected bypass is recorded as a policy violation and can block completion, but Phase 1 and Phase 2 do not claim complete technical interception. Phase 3 may add native runtime adapters and CI gates where the host supports them.

### Evidence Storage

Workflow evidence is stored per run under `.ai-runs/<run-id>/`:

```text
.ai-runs/<run-id>/
  run.json
  approvals.json
  policy-violations/
    <event-id>.json
  commands/
    <command-id>.json
  logs/
    <command-id>.stdout.log
    <command-id>.stderr.log
  done-claim.json
  done-claim.md
```

The workflow cache stores only summaries and pointers to evidence. `.ai-runs/` is ignored by Git by default because raw evidence can contain local or sensitive data. Durable repository work logs contain scrubbed summaries, while CI may preserve scrubbed raw evidence as an external artifact.

Command output, HTTP responses, and verification logs are filtered before persistence. Authorization headers, cookies, tokens, passwords, secrets, and sensitive environment values are masked. `.env`, `.env.local`, credential stores, and secret-file contents must not be captured. Capture uses an allowlist where possible because post-processing alone cannot guarantee secret removal.

Raw evidence is local and ignored by Git by default. Reviewable evidence is published only in scrubbed form through `ai/workflow-cache.md`, issue work logs, completion reports, and CI artifact summaries. Reviewers must not be required to inspect unsanitized local logs, and a local evidence pointer is not treated as durable cross-machine evidence unless a scrubbed summary or external artifact reference exists.

### Approval Records

Actions requiring human approval create structured evidence containing approval type, approver, scope, reason, timestamp, related run ID, and an external approval reference when one exists. Per-run approval records are stored at `.ai-runs/<run-id>/approvals.json` and validated against `ai/schemas/approval-record.schema.json`.

An approval record is an audit record, not independent proof of authority. An agent must not manufacture approval by writing `approvedBy: human`. Destructive, production, secret, deployment, and other approval-bound actions still require an actual host-runtime or external human approval event before execution; the record captures that event and its scope.

Policy violations use append-only event files validated against `ai/schemas/policy-violation.schema.json`. Each event records type, description, detection time, blocking status, run ID, and related command or tool context. `run.json` contains only a summary and pointers, avoiding concurrent rewrites of one shared violations array.

## Execution Flow

1. `PRE_TASK` reads cached state and validates fingerprints.
2. The agent selects a context-map route and relevant skill.
3. `PRE_EDIT` validates ownership before a write.
4. Commands are requested by registry ID through `command-runner.sh`.
5. `PRE_COMMAND` allows, blocks, or requires a recorded reason.
6. `POST_COMMAND` persists detailed success or failure evidence under the run directory and updates only a scrubbed summary pointer in the workflow cache.
7. Verification runs through `verification-runner` and `verify-level.sh`.
8. Failures must pass `failure-triage` before rerun.
9. `PRE_DONE_CLAIM` and `done-claim-check.sh` validate completion evidence.

## Repository Intake

Initial intake is read-only and non-destructive. It inspects tracked repository paths, Gradle wrapper/configuration, application configuration, tests, and existing workflow documents. It does not execute unregistered build, database, deployment, or production commands.

The current intake evidence supports these fact-confidence and capability-configuration states:

- `CONFIRMED`: Gradle Wrapper is the package/build entry point.
- `CONFIRMED`: Java 21 and Spring Boot are configured.
- `CONFIRMED`: MySQL, Redis, and Kafka development services are declared on ports 3306, 6379, and 9092.
- `INFERRED`: The application has no explicit server port, so 8080 is an inference until runtime verification.
- `CONFIGURED_UNVERIFIED`: the Gradle `test` task has configuration evidence but has not been executed as part of this design work.
- `NOT_CONFIGURED`: lint, dedicated integration-test, E2E, migration, seed, and API-smoke commands are not currently defined.
- No command is marked `VERIFIED` until its exact registry argv has executed successfully and evidence has been recorded.

## Script Scope

- `repo-intake.sh`: refresh stable context after valid invalidation.
- `workflow-gate.sh`: execute hook checks.
- `command-runner.sh`: run registry commands and persist evidence.
- `verify-level.sh`: map verification levels to registered command IDs.
- `api-smoke.sh`: run declared HTTP cases against a configured base URL; report `NOT_CONFIGURED` when endpoint cases or prerequisites are absent so the verification gate can map that result to `NOT_APPLICABLE` or `BLOCKED` by change type.
- `done-claim-check.sh`: validate recorded completion evidence.

### Script Exit Codes

All workflow scripts use a shared process exit-code contract:

- `0`: `PASS`
- `1`: `FAIL`
- `2`: `BLOCKED`
- `3`: `NOT_CONFIGURED`
- `4`: `POLICY_VIOLATION`
- `5`: `INVALID_STATE`
- `6`: `NOT_APPLICABLE`
- `7`: `SKIPPED_WITH_REASON`

Every script also writes schema-validated structured result JSON; callers must not infer state by parsing stdout text. A child command's native process exit code is stored separately as `processExitCode`. Any non-zero child exit is mapped to workflow result `FAIL` and runner exit code `1`, so child exit codes cannot be confused with workflow control codes.

Leaf check scripts may return the detailed exit codes above. Final gate scripts translate policy-allowed `NOT_APPLICABLE` or `SKIPPED_WITH_REASON` leaf outcomes into overall `PASS`; otherwise they preserve a blocking non-zero result. CI and native hook adapters call final gate commands rather than raw leaf checks unless they intentionally require every non-PASS leaf result to fail.

Bash scripts remain simple human-facing entry points. JSON parsing, hashing, atomic state updates, structured process execution, evidence writing, and log scrubbing may use one small helper runtime only after that runtime is confirmed for the environment being used. The workflow must not silently assume Python, Node.js, `jq`, or another undeclared dependency.

### Helper Runtime Preflight

Before implementing JSON parsing, hashing, schema validation, atomic writes, structured execution, or log scrubbing, repository intake detects candidate helper runtimes such as Python, Node.js, Java, or `jq`. The selected runtime, executable path or command, version, evidence, and environment-specific state are recorded in `ai/project-state.json`.

Runtime state is recorded separately for supported environments. Phase 1 requires a locally approved runtime with state `CONFIRMED`. CI may remain `UNKNOWN` or `NOT_CONFIGURED` until Phase 3, in which case CI enforcement is `BLOCKED` without blocking the local gateway. If no local helper runtime is approved and available, affected local commands fail as `NOT_CONFIGURED`; scripts do not silently degrade to fragile Markdown parsing or undeclared tooling.

No script performs database reset/drop/truncate, production mutation, deployment, secret changes, or bulk destructive operations.

## Existing Document Integration

Existing workflow documents are merged, not replaced wholesale:

- `AGENTS.md` links the mandatory startup order and gateway rules.
- `ai/document-routing.md` routes through context-map route IDs.
- `ai/verification-levels.md`, `ai/qa-gate.md`, and `ai/done-claim-template.md` reference executable verification and done-claim entry points.
- `ai/subagent-workflow.md`, issue templates, and work-log templates carry context-map routes, registry IDs, cache keys, prior evidence, and handoff state.
- `docs/00-index.md` maps the new workflow sources of truth.
- `docs/09-quality-operations-and-rules.md` links to executable QA enforcement without duplicating hook details.
- Feature templates reference verification IDs instead of inventing commands.

## Failure Handling

- Missing registry entry: block execution and run scoped discovery through repo intake or an approved registry update.
- Repeated unchanged command: block unless an allowed rerun reason is recorded.
- Repeated unchanged file read: reuse cache or record why the cache is invalid.
- Command failure: store failure evidence and block continuation until triage or explicit blocked status.
- Stale project state: invalidate only affected sections, then refresh scoped context.
- Missing API prerequisites: report NOT CONFIGURED or BLOCKED; do not claim real API verification.
- Unscrubbed or potentially sensitive evidence: block publication, done-claim inclusion, and commit.
- Runtime bypass: report that repository enforcement was bypassed; native runtime adapters may be added separately.

### API Smoke Requiredness

`NOT_CONFIGURED` does not always fail unrelated work. For non-API changes, API smoke may be reported as `NOT_APPLICABLE` and displayed as `N/A` with a reason. For API, auth, permission, persistence, or externally visible behavior changes, missing runnable API cases or prerequisites is `BLOCKED`, not `PASS`. Agents must not claim real API verification when endpoint cases, infrastructure, or server prerequisites are absent.

### Gate Result Mapping

All verification and completion gates apply the same mapping:

- Applicable command exists and succeeds: `PASS`
- Applicable command exists and executes unsuccessfully: `FAIL`
- Required capability is absent or unavailable: command result `NOT_CONFIGURED`, gate result `BLOCKED`
- Capability is irrelevant to the classified task: `NOT_APPLICABLE` (displayed as `N/A`)
- Policy explicitly permits a skip and records why: `SKIPPED_WITH_REASON`

A missing registry entry is `NOT_CONFIGURED` at capability discovery. If the current task requires it, the verification or completion gate converts the overall result to `BLOCKED`. Agents cannot turn `NOT_CONFIGURED` into a silent skip.

## Verification Strategy

1. Static checks validate required files, headings, registry IDs, hook links, and executable script permissions.
2. Script contract tests use temporary fixtures to confirm unknown commands, destructive commands, unjustified reruns, hidden failures, and evidence-free done claims are rejected.
3. Repository verification uses only commands first registered with evidence.
4. API smoke remains blocked until a runnable endpoint and its cases exist.
5. The final setup report distinguishes implemented repository gates from host-runtime enforcement gaps.

## Delivery Phases

### Phase 1A: State And Registry Skeleton

- Add schemas and enum contracts for registry, state, runs, command results, done claims, approval records, and policy violations.
- Add canonical `ai/command-registry.json` and `ai/project-state.json` with human-readable Markdown policy and generated summary sections.
- Detect and record local and CI helper-runtime states without requiring Phase 3 CI availability.
- Register only evidenced commands and represent absent capabilities as `NOT_CONFIGURED`.
- Add `.ai-runs/` to `.gitignore` and connect `AGENTS.md` to the supported workflow path and enforcement boundary.
- Add schema and generated-summary validation fixtures.

### Phase 1B: Command Gateway

- Add registry-ID command execution without `eval` and enforce parameter schemas.
- Add `scripts/ai/command-runner.sh`, `scripts/ai/workflow-gate.sh`, and `scripts/ai/done-claim-check.sh`.
- Add shared exit codes, structured script results, pre/post command gates, and per-run evidence.
- Add secret-safe capture, policy-violation events, approval audit records, and scrubbed review summaries.
- Add fixture-based command-runner and gate contract tests before registering repository verification as passed.
- Keep Phase 1B described as policy, audit, and supported-path enforcement rather than complete host-tool interception.

### Phase 2: Workflow Reuse And Completion Gates

- Add context map, cache policy, tool-call policy, resource budget, handoff state, and remaining skills.
- Add repository intake, verification-level, API-smoke, failure-triage, review, and done-claim gates.
- Connect existing QA, routing, issue, work-log, and feature-template documents to executable entry points.

### Phase 3: Host Enforcement

- Add native agent-runtime hook adapters where supported.
- Add CI gates and scrubbed evidence artifacts where repository policy requires them.

Each phase must remain usable and testable on its own. Repository-gateway enforcement is not described as complete interception of host tool calls before Phase 3 support exists.

Every delivery phase is decomposed again in its own written specification and implementation plan. Phase 1A begins with schema/JSON skeletons, then Markdown summaries, then repository integration and fixtures. Phase 1B, Phase 2, and Phase 3 must receive similarly bounded task groups before implementation; the design phase names are not single execution tasks.

## Success Criteria

- Repository structure and reading routes are stored in `context-map.md`.
- Known commands and unsupported command categories are canonical in `command-registry.json` and summarized in `command-registry.md`.
- All executable JSON state is schema-versioned and rejected when invalid or incompatible.
- Project facts, capability configuration, workflow results, and script outcomes use separate closed enums.
- Cache and tool-call invalidation rules prevent unjustified rediscovery.
- Repeated procedures are represented by focused skills.
- Mandatory transitions invoke executable gates.
- Command reruns and failed-command continuation are blocked by evidence rules.
- Subagent handoffs contain reusable context and prior results.
- Completion claims fail without required recorded verification.
- Raw commands, `eval`, unsanitized evidence publication, and unsupported API-smoke claims are blocked.
- Existing workflow and QA documents point to the new execution structure without contradictory duplicate rules.

## Approval Note

This design is approved as the baseline for AI Workflow Enforcement. Implementation starts with Phase 1A and must not expand into product feature work.

Phase implementation preserves these constraints:

1. JSON is canonical for executable workflow state.
2. Markdown summaries are not independent sources of truth.
3. Invalid schema state fails closed.
4. Commands are represented by registry IDs and argv arrays.
5. Raw shell command execution, unchecked dynamic arguments, and `eval` are forbidden.
6. Per-run raw evidence is stored under `.ai-runs/<run-id>/` and ignored by Git.
7. Reviewable evidence is scrubbed before publication.
8. Approval records are audit records only and cannot manufacture approval.
9. Repository gateway enforcement is supported-path enforcement until native adapters or CI gates exist.
10. Product features, production operations, deployment, destructive database operations, migrations, seeds, and secret changes remain out of scope.

## Non-Goals

- Implementing product features.
- Running production, deployment, destructive database, migration, or seed operations.
- Claiming that repository scripts can intercept every host tool call without a native runtime adapter.
- Replacing all existing documentation with generated files.
