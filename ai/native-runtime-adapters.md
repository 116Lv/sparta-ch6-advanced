# Native Runtime Adapter Policy

`ai/native-runtime-adapters.json` is the canonical repository support policy.
The executable contracts are
`ai/schemas/native-runtime-adapters.schema.json`,
`ai/schemas/native-runtime-snapshot.schema.json`,
`ai/schemas/native-adapter-result.schema.json`, and
`ai/schemas/native-bypass-attempt.schema.json`. Result mapping is owned by
`ai/verification-gates.md`; the approved architecture is recorded in
`docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md`.

## Current Host Discovery

The canonical current host is `codex-desktop` with `hostVersion: null` and
`versionProvenance: UNPROBED`. `supportedHosts: []` remains canonical. A
repository declaration cannot invent a host version, and supported-host
matching requires an authoritative `PROBED` SemVer value.

No native registration manifest or callable interceptor installation API is
available for this host. Repository shell, file-read, search, and tool-call
access therefore does not prove native interception.

| Surface | Status | Reason code |
| --- | --- | --- |
| `COMMAND` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `FILE_READ` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `SEARCH` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `TOOL_CALL` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |

This maps to the Phase 2C `NOT_APPLICABLE` leaf with the explicit
repository-only qualification. It is not native enforcement.

## Responsibility Boundary

`scripts/ai/command-runner.sh` remains the only supported product-command
path. The repository gateway owns command registration, parameter validation,
approval checks, run lifecycle, evidence publication, and integrity
finalization. A native adapter may observe, classify, block, and report host
operations; it never executes a product command and never grants repository
gateway authority.

The host producer owns authoritative host-version probing, pre-operation hook
registration, one-use challenge handling, callback execution, signing, and an
external durable replay ledger. The internal evaluator accepts those facts only
through immutable `HostNativeTrust`; its descriptor, probe, and ledger root
must resolve outside the repository. The public repository CLI cannot inject
host trust, a supported-host policy, a probe, or a ledger and therefore remains
on the canonical unsupported-host path. The repository evaluator owns schema
validation, trust verification, claimed/trusted normalization, bypass lifecycle
checks, and Phase 2C mapping.

## Signed Snapshot Trust

A supported-host snapshot is closed by
`ai/schemas/native-runtime-snapshot.schema.json`. The signed payload binds the
trusted `producerId`, `hostId`, `hostVersion`, adapter version, `observedAt`,
the current `taskKey` and `gateInvocationId`, the bounded bypass event count
and complete event-set SHA-256, the bounded unique `resolutionEventIds` array,
all four surfaces, per-surface callback proof, the raw Ed25519 public key, and
its SHA-256 fingerprint. The detached
`signature` member signs the snapshot with that member removed.

Trust requires all of the following:

- the current policy has a matching supported host and a `PROBED` authoritative
  host version;
- producer, host, host version, adapter range, and `gateInvocationId` match;
- `observedAt` is not in the future and is at most 300 seconds old;
- the supplied public key hashes to both the signed fingerprint and the public
  key fingerprint pinned by policy;
- `cryptography.hazmat` Ed25519 verification accepts the detached signature;
- every `ENFORCED` surface has signed proof that its callback observed the
  operation before execution and returned `BLOCKED` for the same challenge;
- the signed event count and canonical event-set digest exactly match every
  supplied deduplicated bypass record;
- the signed `resolutionEventIds` exactly equal the current valid later-gate
  `RESOLVED` event IDs, including an empty array when no resolution is claimed;
- the signed attestation identity is atomically consumed in the external
  host-owned replay ledger before trusted surfaces can pass; the in-process
  one-use set remains defense in depth only.

The optional crypto dependency is fail-closed: unavailable Ed25519 support is
`BLOCKED`. The evaluator accepts no private key. Safe handle-relative ledger
publication and directory durability are required; an unavailable safe backend
or uncertain write, sync, close, or cleanup fails closed. Tests create temporary
external ledgers, keys, and fixtures only; key material, replay state, and
runtime evidence are not written to durable repository state.

## Claimed And Trusted Status

`claimedSurfaces` records a closed snapshot's declarations.
`trustedSurfaces` records only what survived the complete trust chain. Missing
snapshots use the supported policy's `NOT_CONFIGURED` baseline. Malformed,
rejected, stale, replayed, or unverifiable snapshots may show their closed
claims, but their trusted surfaces remain the non-promoted baseline and never
become `ENFORCED`.

Supported-host policy surfaces are constrained to `NOT_CONFIGURED`; repository
files cannot declare runtime `ENFORCED`. A signed snapshot can promote a
surface to trusted `AUDIT_ONLY` or `ENFORCED`, but `PASS` requires all four
trusted surfaces to be `ENFORCED` with valid signed callback proof and no
unresolved bypass attempt. Signed resolution IDs cannot be reused as proof for
a missing, different, or additional current resolution event.

## Canonical Signature Bytes

The signature encoder uses an RFC 8785-compatible restricted subset. Signed
data may contain only objects with ASCII string keys, arrays, ASCII strings,
booleans, null, and integers in the interoperable range
`[-9007199254740991, 9007199254740991]`. Floats, non-ASCII keys or values, and
other Python types are rejected. ASCII keys make Python `sort_keys` ordering
byte-identical to RFC 8785 key ordering; compact UTF-8 JSON has no insignificant
whitespace.

Known vector before canonicalization:

```json
{"z":["ASCII",true,null,7],"signature":{"algorithm":"Ed25519","encoding":"BASE64","value":"excluded"},"a":{"k":"v"}}
```

Known canonical bytes after removing `signature`:

```json
{"a":{"k":"v"},"z":["ASCII",true,null,7]}
```

## Structured Redaction And Bypass Lifecycle

`ai/schemas/native-bypass-attempt.schema.json` allows only closed summaries.
Repository targets are bounded safe relative paths. External targets, argument
sets, queries, and tool payloads use closed classifications, counts where
applicable, and SHA-256 digests; raw authorization data, cookies, credentials,
environment values, request bodies, argv, query text, payloads, and absolute
external targets are forbidden. Redaction uncertainty is completion-blocking.

`surface`, `operationType`, and `commandIntent` use a closed semantic matrix.
Native `FILE_READ`, `SEARCH`, and `TOOL_CALL` records match their operation and
omit command intent. Shell-mediated logical operations retain `COMMAND` as the
surface and carry a command intent matching the logical operation.

Each observed event starts as `DETECTED`. Its `detectionEventId`,
`detectionGateInvocationId`, and `detectionEventSha256` fields are null.
Repeated delivery of the same `eventId` is idempotent; `deduplicationKey` groups
events but never removes the original. A later `RESOLVED` event must use the
same task, a later observation, a different gate invocation, a closed
allowlisted resolution reason, and non-null original-detection binding fields.
The evaluator locates exactly one prior `DETECTED` event whose immutable event
ID, task, original gate invocation, deduplication identity, and canonical event
digest all match the resolution. An absent, duplicate, later, unrelated, or
digest-mismatched detection cannot be cleared, and any other detection in the
group remains unresolved. A detection from the current gate remains unresolved
even if a current-gate resolution follows it.

A valid later-gate transition can clear only on a supported, authoritatively
probed host with a fresh trusted all-`ENFORCED` snapshot whose signed task,
complete event count and canonical event-set digest match the gate inputs and
whose signed `resolutionEventIds` match every current resolution event. Missing
snapshots and missing, mismatched, duplicate, oversized, or extra signed
bindings block; canonical unsupported-host resolution claims also block. Any
ordinary unresolved attempt blocks before snapshot trust evaluation, and Phase
3A does not persist or publish durable bypass evidence.

## Phase 3B Ownership

Phase 3B owns CI adapter installation, remote-runner guarantees, durable CI
evidence, CI ledger provisioning and retention, required-check wiring,
cross-host parity, and attestation. Phase 3A supplies the local external-ledger
contract and fail-closed evaluator only. Phase 1B-3 remains `INTEGRITY_ONLY`,
and no native result promotes registry commands to `VERIFIED`, closes an Issue,
or authorizes an unqualified overall `DONE` claim.
