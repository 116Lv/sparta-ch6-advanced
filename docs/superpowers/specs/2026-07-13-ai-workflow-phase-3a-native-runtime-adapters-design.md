# AI Workflow Phase 3A Native Runtime Adapters Design

## Status And Scope

Phase 3A adds a host-native enforcement contract around the approved repository workflow. It does not redesign Phase 1A through Phase 2C. Phase 1B-3 remains integrity-only with `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.

This phase covers adapter discovery, command/file-read/search/tool-call capability reporting, bypass-attempt detection and redacted records, completion blocking, and Phase 2C gate integration. Phase 3B CI gates, durable CI evidence, remote runner parity, and required CI adapter availability remain out of scope.

No Gradle, build, product test, server, Docker Compose, HTTP/curl/API, database, migration, seed, deployment, or infrastructure command may run. Verification uses static checks, helper tests, contracts, and temporary fixtures only.

## Host Investigation And Support Floor

The current host identifies as Codex desktop and exposes repository shell, file read, search, and tool-call operations to the active agent. Repository inspection found no `.codex` hook configuration, no host adapter registration manifest, and no callable API for installing pre-command, pre-file-read, pre-search, or pre-tool-call interceptors. Repository scripts therefore cannot prove host-wide interception.

Phase 3A has no supported host-native adapter at implementation time, so the supported-host registry is empty and no minimum supported host version exists. `codex-desktop` is a recognized provisional identity, not a supported adapter. Its canonical `hostVersion` is `null` with `versionProvenance: UNPROBED`; repository policy must not invent a version. A future host may enter the supported-host registry only with an authoritative host version probe, official hook-surface reference, trusted runtime producer identity, and minimum version backed by those sources. Supported-host matching requires `versionProvenance: PROBED` and an authoritative SemVer value.

Unknown, provisional, or version-ineligible host identities are `UNSUPPORTED`. A host becomes `NOT_CONFIGURED` only after it is in the supported-host registry but lacks a valid runtime adapter configuration.

The current investigation is reproducible with repository static probes: inspect `.codex`, `.github`, `ai`, and `scripts/ai`; search for `native`, `adapter`, `hook`, and the four surface names; and inspect the active host tool inventory for a hook registration operation. These probes found repository helper lifecycle hooks but no native registration manifest or callable interceptor installation API. The resulting machine-readable current-host declaration is repository policy evidence only and cannot promote a capability above `UNSUPPORTED`.

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

The canonical `ai/native-runtime-adapters.json` document contains repository-authored support policy only:

- `schemaVersion`, `updatedAt`, and a closed list of adapter declarations.
- Adapter identity: `hostId`, `minimumHostVersion`, supported adapter version range, and allowed trusted producer identifiers.
- Current-host classification, nullable host version, `UNPROBED|PROBED` provenance, and non-secret repository probe references.
- Four required surface declarations: `COMMAND`, `FILE_READ`, `SEARCH`, and `TOOL_CALL`.
- Per-surface repository baseline status and reason code. Supported-host policy is baseline-only and cannot declare runtime `ENFORCED`.
- Completion policy and Phase 2C check mapping.

Runtime discovery is a separate ephemeral snapshot supplied through an explicit `--runtime-snapshot` input and closed by `ai/schemas/native-runtime-snapshot.schema.json`. Repository files cannot create or modify that snapshot and can never self-promote `ENFORCED`. Each future supported-host entry must pin an Ed25519 public-key fingerprint and producer identifier. The snapshot supplies the raw public key; the evaluator hashes it against both the signed fingerprint and the policy pin. Its required `resolutionEventIds` member is a unique array of at most 64 identifiers, each at most 128 characters, and is empty when no current resolution is claimed. The host producer signs the RFC 8785-compatible restricted canonical JSON bytes of the snapshot without its `signature` member, so `resolutionEventIds` is inside the signed payload; the gate verifies the detached signature with optional `cryptography.hazmat`. The restricted subset permits only ASCII keys and string values, arrays, objects, booleans, null, and interoperable-range integers; floats and non-ASCII data are rejected. The private key remains host-owned and is never accepted from the repository, environment variables, command arguments, or the snapshot itself.

A signed snapshot is trusted only when its signature and producer identifier match the supported-host entry, its host/version match the authoritative current probe, its adapter version is allowed, its observation time is no more than 300 seconds old and not in the future, its one-use `gateInvocationId` matches the current challenge, and every claimed blocking callback passes the signed host-producer pre-execution challenge result. Signature failure, unknown key, replay, callback failure, or unavailable signature verification is `BLOCKED` for a supported host. When a valid later-gate `RESOLVED` transition exists, every current resolution `eventId` must match the signed `resolutionEventIds` set exactly; missing, mismatched, duplicate, oversized, or extra bindings block with a resolution-binding or snapshot-contract reason. Canonical `supportedHosts` remains empty, so the current host cannot pass and any resolution claim remains blocking. Temporary policies and temporary Ed25519 keys exercise the complete supported-host path and prove a valid signed all-`ENFORCED`, exactly bound resolution snapshot can produce `PASS`; no key, replay state, resolution-binding state, or evidence becomes durable repository state.

Results separate `claimedSurfaces` from `trustedSurfaces`. Closed snapshot claims may be reported for diagnosis, but missing, malformed, stale, replayed, repository-authored, unallowlisted, or unverifiable snapshots retain the supported policy's trusted `NOT_CONFIGURED` baseline and never emit trusted `ENFORCED`. Allowed trusted transitions are `NOT_CONFIGURED -> AUDIT_ONLY -> ENFORCED`. `UNSUPPORTED` may become `NOT_CONFIGURED` only after the host identity and authoritative minimum version enter the supported-host registry. An adapter cannot emit trusted `ENFORCED` without a fresh verified signature and a verified signed blocking callback for that surface.

## Capability Status Semantics

- `ENFORCED`: fresh discovery evidence proves the operation is observed before execution and a fail-closed callback can block it. A detected bypass is blocked.
- `AUDIT_ONLY`: the operation can be observed or reconstructed, but cannot be guaranteed blocked before execution. Detection is evidence, not enforcement.
- `NOT_CONFIGURED`: the host is recognized, but no valid and fresh adapter declaration/configuration exists for the surface.
- `UNSUPPORTED`: the host or surface has no supported adapter contract at the declared host version.

For the current Codex desktop environment, all four native surfaces are `UNSUPPORTED` because no authoritative native registration surface or minimum supported version is evidenced. The repository gateway remains enforced for project commands, but that repository-only fact does not change a native surface to `ENFORCED`.

## Bypass Attempt Contract

Each normalized attempt records:

- `attemptId`, immutable `eventId`, `observedAt`, `hostId`, `hostVersion`, and `adapterVersion`.
- `surface`: `COMMAND`, `FILE_READ`, `SEARCH`, or `TOOL_CALL`.
- `operationType` and optional command intent classification.
- `statusAtObservation`.
- `decision`: `BLOCKED` or `ALLOWED_AUDIT_ONLY`.
- `reasonCode`, `repositoryGatewayExpected`, `taskKey`, `gateInvocationId`, and nullable repository `runId`.
- `deduplicationKey`, lifecycle state `DETECTED` or `RESOLVED`, nullable `resolvedAt`, and a closed resolution reason.
- Redacted target, argv, query, or tool payload summary.

The contract forbids raw environment values, authorization data, cookies, credentials, request bodies, arbitrary tool payloads, and unbounded output. The `summary` object has no free-form string slot:

- `target` is exactly one of `NONE`, `REPOSITORY_PATH` with a safe repository-relative `repositoryPath`, or `EXTERNAL_TARGET` with a closed `redactedCategory` and SHA-256 digest. Absolute or otherwise external raw targets are never stored.
- `argumentSummary` contains only classification `NONE`, `ALLOWLISTED_LITERALS`, or `STRUCTURAL_PLACEHOLDERS`, a count from zero through 64 constrained by classification, and a SHA-256 digest. It has no argv, argument, or raw-string member.
- `querySummary` is `NONE` with no digest, or `TEXT_QUERY|STRUCTURED_QUERY` with a SHA-256 digest. `toolPayloadSummary` is `NONE` with no digest, or `STRUCTURED_PAYLOAD|OPAQUE_PAYLOAD` with a SHA-256 digest. Their closed conditionals reject content, email, JSON, and other raw payload members.

Every allowed summary string remains bounded to 512 Unicode scalars and 512 UTF-8 bytes and is subject to semantic secret-marker checks. Redaction uncertainty blocks publication and maps the adapter leaf result to `BLOCKED`.

The adapter producer creates a record only for an observed attempt; `NOT_OBSERVED` is an adapter evaluation state, not a fabricated attempt. `eventId` is unique and repeated delivery of the same `eventId` is idempotent. `deduplicationKey` groups semantically repeated attempts but never removes the original event. An attempt is unresolved while its lifecycle is `DETECTED`. Resolution is permitted only by a later gate invocation with the same `taskKey`, a schema-allowlisted resolution reason, a supported authoritatively probed host, a fresh fully trusted all-`ENFORCED` adapter snapshot, and exact signed `resolutionEventIds` binding for every current valid resolution. Any `DETECTED` event emitted by the current gate remains unresolved and cannot be consumed by a current-gate `RESOLVED` event, even when an older detection exists in the same deduplication group. Any ordinary unresolved attempt for the current `taskKey` blocks before snapshot trust evaluation. Unsupported hosts, absent or untrusted snapshots, and missing, mismatched, or extra bindings keep resolution claims blocking.

## Fail-Closed And Completion Policy

Immediate fail-closed behavior applies only to an `ENFORCED` surface. `AUDIT_ONLY` records the attempt and blocks a Phase 3A host-native enforcement completion claim. `NOT_CONFIGURED`, `UNSUPPORTED`, stale discovery, adapter faults, malformed declarations, redaction uncertainty, missing required surface results, or unresolved attempts also block that claim.

Repository-only workflows may continue to report their existing qualified Phase 2C result when no host adapter is configured, but they must report native enforcement as `NOT_CONFIGURED` or `UNSUPPORTED`. They may not claim Phase 3A host-native enforcement PASS.

## Phase 2C Integration

Phase 3A adds `native-runtime-adapter` as a required leaf check to every Phase 2C change type without changing the approved minimum verification levels. The Phase 3A evaluator normalizes an `UNSUPPORTED` host to a Phase 2C `NOT_APPLICABLE` leaf with the host and four trusted surface statuses retained in its reason and evidence contract. For a host present in the supported-host registry, `NOT_CONFIGURED`, stale discovery, signature failure, adapter fault, redaction uncertainty, an unresolved attempt, or an unsafe resolution binding becomes `BLOCKED`; only a fully verified all-`ENFORCED` snapshot with no unresolved bypass and exact signed resolution binding reaches `PASS`. This makes supported-host faults completion-blocking while allowing unsupported hosts to continue only with an explicit repository-only qualification when no resolution is claimed.

- Valid required surfaces at `ENFORCED` with no unresolved bypass attempts and exact signed binding for every current resolution event: `PASS`.
- Missing or stale required capability: `NOT_CONFIGURED`, mapped to overall `BLOCKED` when required.
- Adapter or redaction failure: `BLOCKED`.
- A bypass allowed despite an `ENFORCED` declaration, or an invalid contract: `FAIL`.
- Unsupported host-native enforcement: adapter result `UNSUPPORTED`, normalized to Phase 2C leaf `NOT_APPLICABLE` with an explicit repository-only qualification.

Phase 1B-3 integrity results do not satisfy this leaf and cannot establish verification completeness.

## Verification Strategy

Tests validate schemas, current-version provenance, restricted canonical bytes, real temporary Ed25519 verification, missing-crypto blocking, status transitions, discovery freshness, minimum versions, producer/key/signature/challenge/callback/replay rejection, claimed/trusted separation, hook-specific semantics, bypass normalization, redaction, completion blocking, Phase 2C mapping, repository gateway authority, and current-host `UNSUPPORTED` behavior. All mutable artifacts are written under temporary directories.

Static checks confirm that no repository `.ai-runs`, non-fixture `artifact-manifest.json`, finalized non-fixture `run.json`, or registry `VERIFIED` promotion is created.

## Phase 3B Handoff

Phase 3B owns CI adapter installation, CI fail-closed guarantees, remote-runner discovery, durable CI evidence, required-check wiring, cross-host parity, and CI retention/attestation. Phase 3A provides only the local host contract and helper/static enforcement boundary needed by that later work.
