# AI Workflow Phase 3A Native Runtime Adapters Design

## Status And Scope

Phase 3A adds a host-native enforcement contract around the approved repository workflow. It does not redesign Phase 1A through Phase 2C. Phase 1B-3 remains integrity-only with `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.

This phase covers adapter discovery, command/file-read/search/tool-call capability reporting, bypass-attempt detection and redacted records, completion blocking, and Phase 2C gate integration. Phase 3B CI gates, durable CI evidence, remote runner parity, and required CI adapter availability remain out of scope.

No Gradle, build, product test, server, Docker Compose, HTTP/curl/API, database, migration, seed, deployment, or infrastructure command may run. Verification uses static checks, helper tests, contracts, and temporary fixtures only.

## Host Investigation And Support Floor

The current host identifies as Codex desktop and exposes repository shell, file read, search, and tool-call operations to the active agent. Repository inspection found no `.codex` hook configuration, no host adapter registration manifest, and no callable API for installing pre-command, pre-file-read, pre-search, or pre-tool-call interceptors. Repository scripts therefore cannot prove host-wide interception.

Phase 3A defines `codex-desktop` as the first adapter identity with minimum host version `2026.07`. This floor means the repository understands the host identity and contract format; it does not claim that every runtime at that version exposes native hooks. Discovery must report the actual host version and surface evidence before any surface can become `AUDIT_ONLY` or `ENFORCED`.

Unknown host identities are `UNSUPPORTED`. Known host identities without a configured adapter declaration are `NOT_CONFIGURED`.

## Considered Approaches

### Recommended: Repository Contract With Host Declarations

Keep one canonical repository contract and accept a host-provided capability declaration. The repository validates declarations, normalizes events, records redacted bypass attempts, and feeds a native-adapter leaf result into Phase 2C. This preserves host differences without granting adapters product-command authority.

### Host-Specific Implementations In The Repository

Ship executable integrations for every host. This can provide stronger interception where APIs exist, but couples repository policy to host release details and cannot be honestly implemented for the current host without a registration surface.

### Single Generic Wrapper

Route all actions through one wrapper. This is simple for commands but cannot reliably intercept editor reads, searches, or external tool calls, and would misrepresent partial coverage as host-native enforcement.

The repository contract with host declarations is selected.

## Responsibility Boundary

`scripts/ai/command-runner.sh` remains the only supported product-command path. Native adapters never execute Gradle, server, Docker, HTTP, database, migration, seed, deployment, or infrastructure commands. They may observe a host operation, classify it, block it, and emit a normalized event.

The repository gateway owns command registration, parameters, approval, run lifecycle, cache reuse, evidence publication, and integrity finalization. Native adapters own host-surface discovery, pre-operation observation where available, bypass detection, immediate blocking where available, and structured event delivery.

A command that attempts file reading or search through a shell is recorded as a `COMMAND` surface event with an intent classification such as `FILE_READ` or `SEARCH`; it is not proof of a native file-read or search hook.

## Discovery Contract

The canonical `ai/native-runtime-adapters.json` document contains:

- `schemaVersion`, `updatedAt`, and a closed list of adapter declarations.
- Adapter identity: `hostId`, `hostVersion`, `minimumHostVersion`, `adapterVersion`, and `discoveryMethod`.
- Discovery evidence: source, observed timestamp, freshness deadline, and non-secret evidence references.
- Four required surface declarations: `COMMAND`, `FILE_READ`, `SEARCH`, and `TOOL_CALL`.
- Per-surface `status`, `observationMode`, `blockingMode`, and reason code.
- Completion policy and Phase 2C check mapping.

Allowed status transitions are `NOT_CONFIGURED -> AUDIT_ONLY -> ENFORCED`. `UNSUPPORTED` may become `NOT_CONFIGURED` only after the host identity and minimum version enter the supported-host registry. An adapter cannot jump to `ENFORCED` without fresh discovery evidence and a verified blocking callback for that surface.

## Capability Status Semantics

- `ENFORCED`: fresh discovery evidence proves the operation is observed before execution and a fail-closed callback can block it. A detected bypass is blocked.
- `AUDIT_ONLY`: the operation can be observed or reconstructed, but cannot be guaranteed blocked before execution. Detection is evidence, not enforcement.
- `NOT_CONFIGURED`: the host is recognized, but no valid and fresh adapter declaration/configuration exists for the surface.
- `UNSUPPORTED`: the host or surface has no supported adapter contract at the declared host version.

For the current Codex desktop environment, all four native surfaces are initially `NOT_CONFIGURED`. The repository gateway remains enforced for project commands, but that repository-only fact does not change a native surface to `ENFORCED`.

## Bypass Attempt Contract

Each normalized attempt records:

- `attemptId`, `observedAt`, `hostId`, `hostVersion`, and `adapterVersion`.
- `surface`: `COMMAND`, `FILE_READ`, `SEARCH`, or `TOOL_CALL`.
- `operationType` and optional command intent classification.
- `statusAtObservation`.
- `decision`: `BLOCKED`, `ALLOWED_AUDIT_ONLY`, or `NOT_OBSERVED`.
- `reasonCode`, `repositoryGatewayExpected`, and a Phase 2C correlation identifier.
- Redacted target, argv, query, or tool payload summary.

The contract forbids raw environment values, authorization data, cookies, credentials, request bodies, arbitrary tool payloads, and unbounded output. Paths are repository-relative when inside the repository; absolute paths outside it are reduced to a stable redacted category. Arguments preserve only allowlisted literals and structural placeholders. Search queries and tool payloads store a bounded digest plus a redacted classification, never raw content. Redaction uncertainty blocks publication and maps the adapter leaf result to `BLOCKED`.

## Fail-Closed And Completion Policy

Immediate fail-closed behavior applies only to an `ENFORCED` surface. `AUDIT_ONLY` records the attempt and blocks a Phase 3A host-native enforcement completion claim. `NOT_CONFIGURED`, `UNSUPPORTED`, stale discovery, adapter faults, malformed declarations, redaction uncertainty, or missing required surface results also block that claim.

Repository-only workflows may continue to report their existing qualified Phase 2C result when no host adapter is configured, but they must report native enforcement as `NOT_CONFIGURED` or `UNSUPPORTED`. They may not claim Phase 3A host-native enforcement PASS.

## Phase 2C Integration

Phase 3A adds a required static-workflow leaf check named `native-runtime-adapter`. The Phase 2C result mapping remains authoritative:

- Valid required surfaces at `ENFORCED` with no unresolved bypass attempts: `PASS`.
- Missing or stale required capability: `NOT_CONFIGURED`, mapped to overall `BLOCKED` when required.
- Adapter or redaction failure: `BLOCKED`.
- A bypass allowed despite an `ENFORCED` declaration, or an invalid contract: `FAIL`.
- Host-native enforcement explicitly outside an optional gate: `NOT_APPLICABLE`.

Phase 1B-3 integrity results do not satisfy this leaf and cannot establish verification completeness.

## Verification Strategy

Tests validate schemas, status transitions, discovery freshness, minimum versions, hook-specific semantics, bypass normalization, redaction, completion blocking, Phase 2C mapping, repository gateway authority, and current-host `NOT_CONFIGURED` behavior. All mutable artifacts are written under temporary directories.

Static checks confirm that no repository `.ai-runs`, non-fixture `artifact-manifest.json`, finalized non-fixture `run.json`, or registry `VERIFIED` promotion is created.

## Phase 3B Handoff

Phase 3B owns CI adapter installation, CI fail-closed guarantees, remote-runner discovery, durable CI evidence, required-check wiring, cross-host parity, and CI retention/attestation. Phase 3A provides only the local host contract and helper/static enforcement boundary needed by that later work.
