# AI Workflow Enforcement Phase 1A Written Specification

## Status

- Specification status: Approved for Phase 1A implementation planning
- Owning feature: none
- Baseline: `docs/superpowers/specs/2026-07-10-ai-workflow-enforcement-design.md`
- Scope: Phase 1A-1, Phase 1A-2, and Phase 1A-3 only
- Verification level for this specification: Level 0 document review

## Goal

Create the written contract for the machine-readable workflow state that Phase 1A will add. Phase 1A establishes schemas, canonical JSON skeletons, human-readable summaries, repository integration, and static fixtures. It does not execute project commands or implement a command gateway.

## Global Constraints

1. JSON is canonical for executable workflow state.
2. Markdown contains human policy and a summary of canonical JSON; it is not an independent source of truth.
3. All executable JSON uses JSON Schema Draft 2020-12, `schemaVersion: 1`, repository-relative forward-slash paths, and `additionalProperties: false` unless this specification explicitly allows extension data.
4. Timestamps use ISO-8601 UTC strings.
5. Phase 1A performs static file inspection only. It does not execute Gradle, application, database, infrastructure, API, migration, seed, lint, test, or helper-runtime commands.
6. No capability is marked `VERIFIED` without successful execution evidence.
7. The command gateway, command runner, hook scripts, evidence capture, automatic Markdown generation, and automatic schema validation are Phase 1B or later.
8. Phase 1B targets Python 3 with the `jsonschema` library and Draft 2020-12 validation, but Phase 1A does not execute Python or assume that it is installed.
9. Phase 1A and Phase 1B support only POSIX/Bash Gradle argv such as `["./gradlew", "test"]`; native `gradlew.bat` support is future scope and `NOT_CONFIGURED`.
10. AI agents do not execute project build, test, server, Docker, HTTP, migration, seed, or infrastructure commands until the Phase 1B gateway records runtime evidence.
11. Static file inspection, document editing, and host-approved version-control operations needed to author and review Phase 1A are administrative workflow operations, not project-command verification evidence.

## Phase Boundaries

### Phase 1A-1: Schemas And Canonical State

Define closed schemas and create the initial canonical command registry and project state.

### Phase 1A-2: Human-Readable Summaries

Define human-editable policy sections, generated-summary ownership markers, bootstrap summary rules, and display mappings.

### Phase 1A-3: Repository Integration

Ignore local run evidence, connect `AGENTS.md` to the new state contract, and add static fixture documents for later automated validation.

## Files To Create

### Specification Artifact

| Path | Responsibility |
|---|---|
| `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md` | Approved Phase 1A state and registry contract |

### Schemas

| Path | Responsibility |
|---|---|
| `ai/schemas/command-registry.schema.json` | Validate command and unavailable-capability records |
| `ai/schemas/project-state.schema.json` | Validate project facts, paths, ports, environments, and runtime availability |
| `ai/schemas/run.schema.json` | Define the future per-run evidence index |
| `ai/schemas/command-result.schema.json` | Define future command execution results |
| `ai/schemas/done-claim.schema.json` | Define future machine-readable completion claims |
| `ai/schemas/approval-record.schema.json` | Define future approval audit records |
| `ai/schemas/policy-violation.schema.json` | Define future policy-violation events |

### Canonical State And Human Summaries

| Path | Responsibility |
|---|---|
| `ai/command-registry.json` | Canonical command capability registry |
| `ai/project-state.json` | Canonical project state and static intake facts |
| `ai/command-registry.md` | Human policy notes and command-registry summary |
| `ai/project-state.md` | Human policy notes and project-state summary |

### Static Validation Fixtures

| Path | Expected Use |
|---|---|
| `ai/fixtures/phase-1a/valid/command-registry.json` | Valid registry fixture |
| `ai/fixtures/phase-1a/valid/project-state.json` | Valid project-state fixture |
| `ai/fixtures/phase-1a/valid/run.json` | Valid future run-index fixture |
| `ai/fixtures/phase-1a/valid/command-result.json` | Valid future command-result fixture |
| `ai/fixtures/phase-1a/valid/done-claim.json` | Valid future done-claim fixture |
| `ai/fixtures/phase-1a/valid/approval-record.json` | Valid future approval audit fixture |
| `ai/fixtures/phase-1a/valid/policy-violation.json` | Valid future policy-violation fixture |
| `ai/fixtures/phase-1a/invalid/command-registry-invalid-enum.json` | Reject unknown status values |
| `ai/fixtures/phase-1a/invalid/command-registry-raw-command.json` | Reject a raw command string in place of argv |
| `ai/fixtures/phase-1a/invalid/command-registry-unknown-version.json` | Reject unsupported schema versions |
| `ai/fixtures/phase-1a/invalid/project-state-missing-required.json` | Reject missing required state |
| `ai/fixtures/phase-1a/invalid/project-state-invalid-confidence.json` | Reject invented confidence values |
| `ai/fixtures/phase-1a/invalid/run-invalid-result.json` | Reject invented workflow results |
| `ai/fixtures/phase-1a/invalid/command-result-missing-process-exit.json` | Reject incomplete execution evidence |
| `ai/fixtures/phase-1a/invalid/approval-record-missing-reference.json` | Reject an approval claim without its audit reference field |
| `ai/fixtures/phase-1a/invalid/policy-violation-invalid-type.json` | Reject invented policy-violation types |
| `ai/fixtures/phase-1a/generated-summary/command-registry-stale.md` | Future validator must detect stale generated content |
| `ai/fixtures/phase-1a/generated-summary/project-state-stale.md` | Future validator must detect contradictory generated content |

Fixtures are static test vectors in Phase 1A. No validator or fixture runner is implemented until Phase 1B.

## Files To Modify

| Path | Required Change |
|---|---|
| `.gitignore` | Add `.ai-runs/` as a repository-root ignored directory |
| `AGENTS.md` | Add canonical-state reading order, Phase 1A status semantics, and enforcement-boundary wording |

No product source, test source, Gradle configuration, runtime configuration, feature spec, ADR, QA gate, or command script is modified in Phase 1A.

## Closed Enum Definitions

### Fact Confidence

Allowed values:

- `CONFIRMED`: directly supported by static repository evidence
- `INFERRED`: reasonable default or implication that lacks runtime evidence
- `UNKNOWN`: not inspected or not knowable from current evidence
- `STALE`: previously known but invalidated by a relevant change
- `UNCERTAIN`: inspected evidence is conflicting or incomplete

### Capability Configuration

Allowed values:

- `UNKNOWN`: capability has not been conclusively discovered
- `CONFIGURED_UNVERIFIED`: static configuration exists, but no successful execution evidence exists
- `VERIFIED`: exact registered argv executed successfully and evidence was recorded
- `NOT_CONFIGURED`: no supported command or mechanism is currently defined
- `STALE`: prior configuration evidence was invalidated
- `UNCERTAIN`: configuration evidence is incomplete or contradictory

### Workflow Result

Allowed values:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_CONFIGURED`
- `NOT_APPLICABLE`
- `SKIPPED_WITH_REASON`

Markdown displays `NOT_APPLICABLE` as `N/A`. JSON never stores `N/A`.

### Script Control Outcome

Allowed values:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_CONFIGURED`
- `POLICY_VIOLATION`
- `INVALID_STATE`
- `NOT_APPLICABLE`
- `SKIPPED_WITH_REASON`

### Command Classification

Allowed values:

- `SAFE`
- `RISKY`
- `DESTRUCTIVE`
- `UNAVAILABLE`

### Environment Kind

Allowed values:

- `LOCAL`
- `CI`

### Evidence Kind

Allowed values:

- `STATIC_FILE`
- `RUNTIME_COMMAND`
- `EXTERNAL_APPROVAL`
- `CI_ARTIFACT`

Phase 1A uses only `STATIC_FILE` evidence.

### Approval Type

Allowed values:

- `REGISTRY_UPDATE`
- `RISKY_COMMAND`
- `DESTRUCTIVE_COMMAND`
- `PRODUCTION_OPERATION`
- `DEPLOYMENT`
- `SECRET_CHANGE`

### Policy Violation Type

Allowed values:

- `RAW_COMMAND_ATTEMPT`
- `UNREGISTERED_COMMAND`
- `UNSAFE_PARAMETER`
- `MISSING_RERUN_REASON`
- `DESTRUCTIVE_WITHOUT_APPROVAL`
- `UNSCRUBBED_EVIDENCE`
- `COMPLETION_WITHOUT_EVIDENCE`
- `DIRECT_TOOL_BYPASS`

## JSON Schema Contracts

Every schema requires `$schema`, `$id`, and `schemaVersion`. Every object sets `additionalProperties: false`. Nullable fields use an explicit union such as `"type": ["string", "null"]`; missing data is not represented by invented strings.

Schema files use stable URNs with this pattern:

```text
urn:sparta-ch6-advanced:ai-workflow:schema:<schema-name>:v1
```

For example, `command-registry.schema.json` uses `$id: urn:sparta-ch6-advanced:ai-workflow:schema:command-registry:v1`. Canonical instance files use a repository-relative `$schema` path and repository-relative `$id`, such as `$schema: ./schemas/command-registry.schema.json` and `$id: ai/command-registry.json`. Public HTTP schema URLs are not used.

### `command-registry.schema.json`

Top-level required fields:

- `$schema`
- `$id`
- `schemaVersion`
- `updatedAt`
- `commands`

Each command record requires:

- `id`: unique dotted identifier
- `purpose`: human-readable capability description
- `configurationStatus`: Capability Configuration enum
- `classification`: Command Classification enum
- `argv`: array of non-empty strings or `null`
- `workingDirectory`: repository-relative path
- `parameters`: object with `allowed` and nullable `schema`
- `prerequisites`: array of capability or service identifiers
- `evidence`: array of evidence records
- `inputPaths`: array of repository-relative paths or globs
- `lastVerifiedAt`: ISO-8601 UTC string or `null`
- `notes`: array of strings

Conditional rules:

- `CONFIGURED_UNVERIFIED` and `VERIFIED` require non-empty argv and at least one evidence record.
- `VERIFIED` requires non-null `lastVerifiedAt` and `RUNTIME_COMMAND` evidence.
- `NOT_CONFIGURED` requires `argv: null`, `classification: UNAVAILABLE`, and `lastVerifiedAt: null`.
- `UNKNOWN`, `STALE`, and `UNCERTAIN` cannot be treated as executable.
- Raw shell command strings, shell pipelines, and `eval` expressions are not representable.

### `project-state.schema.json`

Top-level required fields:

- `$schema`
- `$id`
- `schemaVersion`
- `updatedAt`
- `project`
- `facts`
- `importantPaths`
- `ports`
- `environments`
- `helperRuntimes`
- `commandRegistryRef`
- `cacheInvalidationInputs`

Required project fields:

- `name`
- `productType`
- `mainLanguage`
- `framework`
- `buildSystem`

Each fact requires `id`, `value`, `confidence`, `evidence`, and `observedAt`. Each port requires `service`, `value`, `confidence`, and `evidence`. Each helper-runtime record requires `environment`, `targetRuntime`, `detectedRuntime`, `configurationStatus`, `version`, and `evidence`.

The application port uses value `8080` with confidence `INFERRED`. Helper runtimes remain `UNKNOWN` until a later approved preflight records evidence.

### `run.schema.json`

Required fields:

- `$schema`, `$id`, `schemaVersion`
- `runId`, `taskKey`, `startedAt`, `endedAt`
- `workingDirectory`, `environment`
- `result`
- `commandResultRefs`, `approvalRefs`, `policyViolationRefs`, `evidenceRefs`
- `redactionApplied`

This schema is defined in Phase 1A, but no `.ai-runs/<run-id>/run.json` file is created by Phase 1A.

### `command-result.schema.json`

Required fields:

- `$schema`, `$id`, `schemaVersion`
- `runId`, `commandId`
- `startedAt`, `endedAt`
- `result`, `processExitCode`
- `argvHash`, `inputFingerprint`, `environmentFingerprint`
- `stdoutPath`, `stderrPath`
- `redactionApplied`, `reason`

`processExitCode` preserves the child process code. It is not reused as a workflow control code.

### `done-claim.schema.json`

Required fields:

- `$schema`, `$id`, `schemaVersion`
- `runId`, `taskKey`, `generatedAt`
- `implementationStatus`, `overallResult`
- `checks`, `notRunItems`, `evidenceRefs`
- `unexpected500Status`, `unhandledExceptionStatus`
- `blockers`, `remainingRisks`

No done-claim JSON is created in Phase 1A.

### `approval-record.schema.json`

Required fields:

- `$schema`, `$id`, `schemaVersion`
- `approvalId`, `runId`
- `type`, `approver`, `scope`, `reason`
- `approvedAt`, `externalReference`

The schema states that approval records are audit records. A locally written record cannot independently authorize an action.

### `policy-violation.schema.json`

Required fields:

- `$schema`, `$id`, `schemaVersion`
- `violationId`, `runId`
- `type`, `description`, `detectedAt`
- `blocking`, `context`

No policy-violation event is created in Phase 1A.

## Initial `command-registry.json` Structure

The initial registry contains capability records even when no executable argv is available. The timestamp below illustrates shape only; implementation uses its actual UTC write time.

The Phase 1A/1B command profile is POSIX/Bash only. `verify.unit` uses `["./gradlew", "test"]`. Native Windows `gradlew.bat` execution profiles are not represented and remain future scope. Git Bash on Windows is usable only when the POSIX wrapper path works; Phase 1A does not test that condition.

```json
{
  "$schema": "./schemas/command-registry.schema.json",
  "$id": "ai/command-registry.json",
  "schemaVersion": 1,
  "updatedAt": "2026-07-10T00:00:00Z",
  "commands": [
    {
      "id": "dependencies.install",
      "purpose": "Install or resolve project dependencies",
      "configurationStatus": "UNKNOWN",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [],
      "inputPaths": ["build.gradle", "settings.gradle", "gradle/**"],
      "lastVerifiedAt": null,
      "notes": ["Gradle resolves dependencies as part of tasks; no standalone install command is selected in Phase 1A."]
    },
    {
      "id": "server.dev",
      "purpose": "Start the development server",
      "configurationStatus": "UNKNOWN",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [],
      "inputPaths": ["build.gradle", "src/main/resources/application.yml"],
      "lastVerifiedAt": null,
      "notes": ["No runtime command is selected or executed in Phase 1A."]
    },
    {
      "id": "verify.build",
      "purpose": "Compile or build the project",
      "configurationStatus": "UNKNOWN",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [],
      "inputPaths": ["build.gradle", "settings.gradle", "gradle/**", "src/main/**", "src/test/**"],
      "lastVerifiedAt": null,
      "notes": ["No exact build argv is selected or executed in Phase 1A."]
    },
    {
      "id": "verify.unit",
      "purpose": "Run the configured Gradle test task",
      "configurationStatus": "CONFIGURED_UNVERIFIED",
      "classification": "SAFE",
      "argv": ["./gradlew", "test"],
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [
        {
          "kind": "STATIC_FILE",
          "path": "build.gradle",
          "claim": "The test task is configured to use JUnit Platform."
        },
        {
          "kind": "STATIC_FILE",
          "path": "gradlew",
          "claim": "The Gradle wrapper entry point exists."
        }
      ],
      "inputPaths": ["build.gradle", "settings.gradle", "gradle/**", "src/main/**", "src/test/**"],
      "lastVerifiedAt": null,
      "notes": ["Static configuration evidence exists; the command has not been executed."]
    },
    {
      "id": "verify.lint",
      "purpose": "Run lint checks",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No lint task or plugin is declared." }],
      "inputPaths": ["build.gradle"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "verify.integration",
      "purpose": "Run a dedicated integration-test command",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No dedicated integration-test task is declared." }],
      "inputPaths": ["build.gradle", "src/test/**"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "verify.e2e",
      "purpose": "Run end-to-end tests",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No E2E task or framework is declared." }],
      "inputPaths": ["build.gradle"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "verify.api-smoke",
      "purpose": "Run real HTTP API smoke verification",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": ["server.dev"],
      "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/java/com/ch6/cafe/CafeApplication.java", "claim": "No API-smoke case registry or runner exists." }],
      "inputPaths": ["src/main/**", "src/test/**", "docs/07-data-and-api-contracts.md"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "db.migration",
      "purpose": "Apply database migrations",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No migration tool or task is declared." }],
      "inputPaths": ["build.gradle", "src/main/resources/**"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "db.seed",
      "purpose": "Seed development or test data",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/resources/application.yml", "claim": "No seed command or seed configuration is declared." }],
      "inputPaths": ["src/main/resources/**", "src/test/resources/**"],
      "lastVerifiedAt": null,
      "notes": []
    }
  ]
}
```

## Initial `project-state.json` Structure

```json
{
  "$schema": "./schemas/project-state.schema.json",
  "$id": "ai/project-state.json",
  "schemaVersion": 1,
  "updatedAt": "2026-07-10T00:00:00Z",
  "project": {
    "name": "sparta-ch6-advanced",
    "productType": "Spring Boot backend API assignment",
    "mainLanguage": "Java 21",
    "framework": "Spring Boot 4.1.0",
    "buildSystem": "Gradle Wrapper 9.0.0"
  },
  "facts": [
    {
      "id": "test.framework",
      "value": "JUnit Platform via Spring Boot Test",
      "confidence": "CONFIRMED",
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "Spring Boot Test is declared and the test task uses JUnit Platform." }],
      "observedAt": "2026-07-10T00:00:00Z"
    },
    {
      "id": "database.primary",
      "value": "MySQL",
      "confidence": "CONFIRMED",
      "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/resources/application.yml", "claim": "The primary datasource uses MySQL." }],
      "observedAt": "2026-07-10T00:00:00Z"
    }
  ],
  "importantPaths": [
    { "purpose": "Application source", "path": "src/main/java" },
    { "purpose": "Tests", "path": "src/test" },
    { "purpose": "Project documentation", "path": "docs" },
    { "purpose": "Feature specifications", "path": "specs" },
    { "purpose": "Architecture decisions", "path": "adr" },
    { "purpose": "AI workflow policy", "path": "ai" }
  ],
  "ports": [
    { "service": "application", "value": 8080, "confidence": "INFERRED", "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/resources/application.yml", "claim": "No explicit server.port is configured; 8080 is the Spring Boot default inference." }] },
    { "service": "mysql", "value": 3306, "confidence": "CONFIRMED", "evidence": [{ "kind": "STATIC_FILE", "path": "docker-compose.yml", "claim": "MySQL maps port 3306." }] },
    { "service": "redis", "value": 6379, "confidence": "CONFIRMED", "evidence": [{ "kind": "STATIC_FILE", "path": "docker-compose.yml", "claim": "Redis maps port 6379." }] },
    { "service": "kafka", "value": 9092, "confidence": "CONFIRMED", "evidence": [{ "kind": "STATIC_FILE", "path": "docker-compose.yml", "claim": "Kafka maps port 9092." }] }
  ],
  "environments": [
    { "kind": "LOCAL", "configurationStatus": "UNKNOWN", "notes": ["Python 3 is the Phase 1B target, but no runtime preflight is executed in Phase 1A."] },
    { "kind": "CI", "configurationStatus": "NOT_CONFIGURED", "notes": ["No CI workflow exists; CI enforcement is Phase 3 scope."] }
  ],
  "helperRuntimes": [
    { "environment": "LOCAL", "targetRuntime": "Python 3", "detectedRuntime": null, "configurationStatus": "UNKNOWN", "version": null, "evidence": [] },
    { "environment": "CI", "targetRuntime": "Python 3", "detectedRuntime": null, "configurationStatus": "NOT_CONFIGURED", "version": null, "evidence": [] }
  ],
  "commandRegistryRef": "ai/command-registry.json",
  "cacheInvalidationInputs": [
    "build.gradle",
    "settings.gradle",
    "gradle/wrapper/gradle-wrapper.properties",
    "docker-compose.yml",
    "src/main/resources/application.yml",
    "src/test/resources/application-test.yml",
    ".github/**"
  ]
}
```

Example timestamps in this specification are illustrative. Phase 1A implementation writes the actual UTC time without executing project commands.

## Markdown Summary Rules

Both `ai/command-registry.md` and `ai/project-state.md` use this ownership structure:

```md
# Document Title

## Human Policy Notes

Human-editable policy and interpretation rules.

<!-- GENERATED:START source=ai/example.json -->
## Generated State Summary

Bootstrap summary derived from the canonical JSON in the same reviewed change.
<!-- GENERATED:END source=ai/example.json -->
```

Rules:

1. Human Policy Notes may be edited directly.
2. Content between generated markers may not be edited independently of canonical JSON.
3. During Phase 1A, the initial summary is bootstrapped manually from JSON in the same change and reviewed for exact agreement.
4. Automatic generation and validation are deferred to Phase 1B or later.
5. A summary must show the canonical path, schema version, update time, status, and evidence path.
6. `NOT_APPLICABLE` is displayed as `N/A`; all other enum values are displayed unchanged.
7. A mismatch is resolved by updating canonical JSON first, then refreshing the summary.
8. Markdown tables are never parsed as executable state.

The generated section includes this Phase 1A bootstrap notice:

```md
This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.
```

### `command-registry.md` Generated Summary Columns

- ID
- Purpose
- Configuration Status
- Classification
- Argv Display
- Evidence
- Last Verified

For `argv: null`, display `NOT CONFIGURED` or `UNKNOWN` according to `configurationStatus`; do not invent a command.

### `project-state.md` Generated Summary Sections

- Project Summary
- Important Paths
- Known Ports
- Environment State
- Helper Runtime State
- Command Registry Reference
- Cache Invalidation Inputs

The application port must display `8080 (INFERRED)`.

## `.gitignore` Integration

Add this repository-root entry under a dedicated AI workflow section:

```gitignore
### AI Workflow Local Evidence ###
.ai-runs/
```

Rules:

- Ignore the directory recursively.
- Do not add a negation rule that commits raw logs.
- Reviewable evidence belongs in scrubbed work logs, completion reports, or future CI artifacts.
- Phase 1A does not create `.ai-runs/`.

## `AGENTS.md` Addition

Add the following section after **First Rule**:

```md
## Mandatory Workflow State

Before rediscovering repository structure, commands, ports, environments, or verification capabilities, read:

1. `ai/project-state.json` - canonical project state
2. `ai/command-registry.json` - canonical command capability registry
3. `ai/project-state.md` and `ai/command-registry.md` - human policy and summaries

JSON is canonical. Markdown summaries must not override or contradict JSON.

Phase 1A provides state and registry contracts only. It does not provide a command gateway, native tool interception, or CI enforcement. Do not describe Phase 1A as complete command enforcement.

During Phase 1A work, do not execute project commands. Keep `verify.unit` as `CONFIGURED_UNVERIFIED`; keep lint, dedicated integration test, E2E, migration, seed, and API smoke as `NOT_CONFIGURED`; and keep application port 8080 as `INFERRED`.

Until the Phase 1B gateway exists, AI agents must not directly run Gradle, application server, Docker Compose, HTTP/API, migration, seed, or infrastructure commands. There is no temporary direct-command exception for AI agents. Static file inspection, documentation edits, and host-approved version-control operations remain allowed administrative workflow operations.

A command run manually by a human outside the AI workflow does not make a registry entry `VERIFIED`, does not count as workflow evidence, and must not be reported by an agent as a passed check. Only Phase 1B command-runner evidence may transition an entry to `VERIFIED`.

Commands with `NOT_CONFIGURED`, `UNKNOWN`, `STALE`, or `UNCERTAIN` status are not executable. No command may be marked `VERIFIED` without recorded runtime evidence.
```

Also add the four new state files and schema directory to the existing Document Map. Do not add command-runner instructions until Phase 1B.

## Phase 1A Completion Criteria

Phase 1A is complete only when all of the following are true:

- [ ] All seven schemas exist and use Draft 2020-12, `schemaVersion: 1`, closed objects, and the enums in this specification.
- [ ] `ai/command-registry.json` and `ai/project-state.json` conform by document review to their schemas.
- [ ] `verify.unit` is `CONFIGURED_UNVERIFIED` with argv `./gradlew test` and static evidence.
- [ ] Native `gradlew.bat` execution is absent from Phase 1A and recorded as future scope / `NOT_CONFIGURED`.
- [ ] Lint, dedicated integration test, E2E, migration, seed, and API smoke are `NOT_CONFIGURED` with `argv: null`.
- [ ] No command or capability is marked `VERIFIED`.
- [ ] Application port 8080 is `INFERRED`.
- [ ] Python 3 is recorded as the Phase 1B target runtime; local availability remains `UNKNOWN` and CI remains `NOT_CONFIGURED` unless pre-existing static evidence proves otherwise without command execution.
- [ ] Markdown files contain Human Policy Notes and generated markers, and their bootstrap summaries match canonical JSON.
- [ ] `.ai-runs/` is ignored and no raw evidence is committed.
- [ ] `AGENTS.md` states the canonical reading order and Phase 1A enforcement boundary.
- [ ] Static valid and invalid fixtures exist for future validation.
- [ ] No product, command gateway, hook script, command execution, migration, seed, API smoke, or runtime verification change is included.
- [ ] No human manual command result is accepted as `VERIFIED` AI workflow evidence.
- [ ] The six decisions under Resolved Decisions are reflected consistently across schemas, canonical examples, Markdown rules, and `AGENTS.md` wording.

Verification for Phase 1A is document and static consistency review only. It must report all project commands as `NOT RUN`.

## Phase 1A Non-Goals

Phase 1A does not:

- implement `scripts/ai/command-runner.sh`
- implement `scripts/ai/workflow-gate.sh`
- implement `scripts/ai/done-claim-check.sh`
- parse, generate, or validate JSON automatically
- execute Gradle or application commands
- create `.ai-runs/` evidence
- capture or scrub command logs
- implement pre/post command hooks
- enforce command IDs technically
- implement cache, fingerprints, repo intake, skills, or handoff automation
- implement API smoke cases
- add native runtime adapters or CI gates
- change product code, tests, runtime behavior, database state, migrations, seeds, deployment, or secrets

## Resolved Decisions

1. **Helper runtime:** Phase 1B targets Python 3. Phase 1A records local availability as `UNKNOWN`, performs no preflight, and allows no implicit fallback to Node.js, Java, or `jq`.
2. **Gradle execution profile:** Phase 1A and Phase 1B register only POSIX/Bash argv such as `["./gradlew", "test"]`. Native Windows `gradlew.bat` support is future scope and `NOT_CONFIGURED`.
3. **Schema identity:** Schema files use stable project URNs. Canonical instances use repository-relative `$schema` and `$id` values.
4. **Generated summaries:** Phase 1A manually bootstraps a small summary from canonical JSON in the same reviewed change. Automatic generation and stale validation begin in Phase 1B or later.
5. **Schema validator:** Phase 1B targets Python `jsonschema` with Draft 2020-12 support and plans `scripts/ai/lib/validate_json.py`. Phase 1A creates schemas and fixtures only.
6. **Interim command policy:** AI project-command execution is fully paused until the Phase 1B gateway exists. Human manual results are outside the AI workflow and cannot produce `VERIFIED` state or passed-check claims.

## Open Questions

None. The six prior questions are resolved above. Before implementation begins, the reviewer checks only that the implementation plan preserves the resolved decisions, file boundaries, and non-goals in this specification.

## Review Decision

This specification is approved for Phase 1A implementation planning. Approval authorizes only the Phase 1A file creation and modification listed here. It does not authorize Phase 1B command gateway implementation or any AI project-command execution.
