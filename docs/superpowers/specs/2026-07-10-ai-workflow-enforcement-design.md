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

### Stable Context

- `ai/context-map.md`: repository surfaces, ownership, canonical documents, important paths, generated/excluded paths, and minimal reading routes.
- `ai/command-registry.json`: canonical command IDs, argv arrays, classification, evidence, prerequisites, input paths, and verification state.
- `ai/command-registry.md`: human-readable command policy and generated registry summary.
- `ai/project-state.json`: canonical stack, package manager, ports, environment files, services, test frameworks, confidence status, and intake fingerprint.
- `ai/project-state.md`: human-readable project-state explanation and summary.

`ai/document-routing.md` becomes a thin routing gate. It selects an owning feature and a route ID, then delegates repository-wide path and reading decisions to `context-map.md`.

### Cache And Tool Control

- `.ai-runs/<run-id>/`: append-only per-run command metadata, scrubbed logs, verification evidence, and done-claim inputs.
- `ai/workflow-cache.md`: recent run summaries, evidence pointers, file discoveries, and reusable handoff notes; it does not store unbounded raw logs.
- `ai/cache-policy.md`: cache keys, freshness rules, invalidation triggers, and conditions that permit rediscovery.
- `ai/tool-call-policy.md`: limits for broad search, tree scans, repeated file reads, repeated command discovery, and duplicate external tool calls.
- `ai/resource-budget.md`: numeric default limits and required reasons for exceptions.
- `ai/agent-handoff.md`: shared context packet for orchestrator and subagent transitions.

The cache key for a command result includes the command ID, argv hash, working directory, hashes of registry-declared relevant input paths, and an allowlisted environment fingerprint. A rerun against the same key requires an allowed reason. File reads are keyed by normalized path and content hash, not modification time alone. Input hashing must remain scoped so cache calculation does not become another full-repository scan.

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

### Evidence Storage

Workflow evidence is stored per run under `.ai-runs/<run-id>/`:

```text
.ai-runs/<run-id>/
  run.json
  commands/
    <command-id>.json
  logs/
    <command-id>.stdout.log
    <command-id>.stderr.log
  done-claim.md
```

The workflow cache stores only summaries and pointers to evidence. `.ai-runs/` is ignored by Git by default because raw evidence can contain local or sensitive data. Durable repository work logs contain scrubbed summaries, while CI may preserve scrubbed raw evidence as an external artifact.

Command output, HTTP responses, and verification logs are filtered before persistence. Authorization headers, cookies, tokens, passwords, secrets, and sensitive environment values are masked. `.env`, `.env.local`, credential stores, and secret-file contents must not be captured. Capture uses an allowlist where possible because post-processing alone cannot guarantee secret removal.

## Execution Flow

1. `PRE_TASK` reads cached state and validates fingerprints.
2. The agent selects a context-map route and relevant skill.
3. `PRE_EDIT` validates ownership before a write.
4. Commands are requested by registry ID through `command-runner.sh`.
5. `PRE_COMMAND` allows, blocks, or requires a recorded reason.
6. `POST_COMMAND` persists success or failure in the workflow cache.
7. Verification runs through `verification-runner` and `verify-level.sh`.
8. Failures must pass `failure-triage` before rerun.
9. `PRE_DONE_CLAIM` and `done-claim-check.sh` validate completion evidence.

## Repository Intake

Initial intake is read-only and non-destructive. It inspects tracked repository paths, Gradle wrapper/configuration, application configuration, tests, and existing workflow documents. It does not execute unregistered build, database, deployment, or production commands.

The current intake evidence supports these facts and confidence states:

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
- `api-smoke.sh`: run declared HTTP cases against a configured base URL; fail as not configured when endpoint cases or prerequisites are absent.
- `done-claim-check.sh`: validate recorded completion evidence.

Bash scripts remain simple human-facing entry points. JSON parsing, hashing, atomic state updates, structured process execution, evidence writing, and log scrubbing may use one small helper runtime only after that runtime is confirmed in the local and CI environments. The workflow must not silently assume Python, Node.js, `jq`, or another undeclared dependency.

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

## Verification Strategy

1. Static checks validate required files, headings, registry IDs, hook links, and executable script permissions.
2. Script contract tests use temporary fixtures to confirm unknown commands, destructive commands, unjustified reruns, hidden failures, and evidence-free done claims are rejected.
3. Repository verification uses only commands first registered with evidence.
4. API smoke remains blocked until a runnable endpoint and its cases exist.
5. The final setup report distinguishes implemented repository gates from host-runtime enforcement gaps.

## Delivery Phases

### Phase 1: Executable Command Boundary

- Add canonical command and project-state JSON schemas and human-readable summaries.
- Add registry-ID command execution without `eval`.
- Add pre/post command gates, per-run evidence, secret-safe capture, and registry validation.
- Register only evidenced commands and represent absent capabilities as `NOT_CONFIGURED`.

### Phase 2: Workflow Reuse And Completion Gates

- Add context map, cache policy, tool-call policy, resource budget, handoff state, and remaining skills.
- Add repository intake, verification-level, API-smoke, failure-triage, review, and done-claim gates.
- Connect existing QA, routing, issue, work-log, and feature-template documents to executable entry points.

### Phase 3: Host Enforcement

- Add native agent-runtime hook adapters where supported.
- Add CI gates and scrubbed evidence artifacts where repository policy requires them.

Each phase must remain usable and testable on its own. Repository-gateway enforcement is not described as complete interception of host tool calls before Phase 3 support exists.

## Success Criteria

- Repository structure and reading routes are stored in `context-map.md`.
- Known commands and unsupported command categories are canonical in `command-registry.json` and summarized in `command-registry.md`.
- Project facts distinguish confirmed, inferred, configured-unverified, verified, not-configured, and unknown states.
- Cache and tool-call invalidation rules prevent unjustified rediscovery.
- Repeated procedures are represented by focused skills.
- Mandatory transitions invoke executable gates.
- Command reruns and failed-command continuation are blocked by evidence rules.
- Subagent handoffs contain reusable context and prior results.
- Completion claims fail without required recorded verification.
- Raw commands, `eval`, unsanitized evidence publication, and unsupported API-smoke claims are blocked.
- Existing workflow and QA documents point to the new execution structure without contradictory duplicate rules.

## Non-Goals

- Implementing product features.
- Running production, deployment, destructive database, migration, or seed operations.
- Claiming that repository scripts can intercept every host tool call without a native runtime adapter.
- Replacing all existing documentation with generated files.
