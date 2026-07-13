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
registration, one-use challenge handling, callback execution, and signing.
The repository evaluator owns schema validation, trust verification,
claimed/trusted normalization, bypass lifecycle checks, and Phase 2C mapping.

## Signed Snapshot Trust

A supported-host snapshot is closed by
`ai/schemas/native-runtime-snapshot.schema.json`. The signed payload binds the
trusted `producerId`, `hostId`, `hostVersion`, adapter version, `observedAt`,
the current `gateInvocationId`, all four surfaces, per-surface callback proof,
the raw Ed25519 public key, and its SHA-256 fingerprint. The detached
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
- the in-process one-use challenge has not already been consumed.

The optional crypto dependency is fail-closed: unavailable Ed25519 support is
`BLOCKED`. The evaluator accepts no private key. Tests create temporary keys and
fixtures only; key material, replay state, and runtime evidence are not written
to durable repository state.

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
unresolved bypass attempt.

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

Each observed event starts as `DETECTED`. Repeated delivery of the same
`eventId` is idempotent; `deduplicationKey` groups events but never removes the
original. A later `RESOLVED` event must use the same task, a later observation,
a different gate invocation, and a closed resolution reason. A detection from
the current gate remains unresolved even if a current-gate resolution follows
it. Any unresolved attempt blocks completion, and Phase 3A does not persist or
publish durable bypass evidence.

## Phase 3B Ownership

Phase 3B owns CI adapter installation, remote-runner guarantees, durable CI
evidence, challenge durability across processes, required-check wiring,
cross-host parity, retention, and attestation. Phase 3A supplies the local
contract and fail-closed evaluator only. Phase 1B-3 remains `INTEGRITY_ONLY`,
and no native result promotes registry commands to `VERIFIED`, closes an Issue,
or authorizes an unqualified overall `DONE` claim.
