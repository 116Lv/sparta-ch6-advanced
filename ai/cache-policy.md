# AI Workflow Cache Policy

## Human Policy Notes

`ai/workflow-cache.json` is the canonical Phase 2A cache record. This Markdown file explains freshness and invalidation policy. JSON is canonical. Markdown is not parsed as executable state.

Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness and does not promote ignored local evidence into durable cross-machine proof.

## Cache Keys

File-read entries are keyed by normalized repository-relative path and SHA-256 content digest. Command evidence summaries are keyed by command ID, argv hash, working directory, declared input fingerprints, and allowlisted environment fingerprint from the supported command gateway.

Verification-decision entries use a distinct closed key containing task key, gate invocation ID, checked-out commit SHA, change type, entry point, verification-policy SHA-256, the exact producer set selected by canonical change-type and entry-point policy, every consumed evidence path and SHA-256, the relevant environment fingerprint, and expiry. Task and gate identifiers are mandatory lookup identity, but repo intake does not claim an external authority for them. A non-null environment fingerprint is `UNCERTAIN` until an authoritative current environment mapping exists.

## Freshness Rules

A cache entry is `FRESH` only when every declared path still exists as expected and every recorded digest matches. Verification-decision reuse additionally requires the current commit and policy digest, exact canonical producer set, every evidence digest, and unexpired decision to match. A mismatch or expiry makes the entry `STALE`. A missing or unmapped classification, task/gate identity, path, policy/commit source, or environment input makes the entry `UNCERTAIN` unless a specific route can prove it irrelevant.

The canonical cache does not materialize a reusable verification PASS decision whose commit or short-lived expiry would become self-referential or immediately stale. Such decisions may be recorded only when every durable input is available.

## Conservative Invalidation

When dependency mapping is incomplete or ambiguous, the workflow prefers re-verification over unsafe reuse. Phase 2A repo intake may report proposal-only `projectStateRefresh` and `commandDiscoveryUpdates` records, but it does not execute commands, does not create `.ai-runs`, and does not mark a registry command `VERIFIED`.

## Evidence Boundary

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Cache policy therefore combines structured records, work logs, handoff notes, and review gates rather than claiming total technical interception.

## Phase 3A Native Boundary

The current host-native adapter state is `UNSUPPORTED` with `hostVersion: null` and `versionProvenance: UNPROBED`. Native runtime snapshots and bypass-attempt references are per-invocation inputs correlated by task and gate ID; they are not reusable cached PASS results. A cached, repository-authored, digest-mismatched, correlation-mismatched, or otherwise precomputed `native-runtime-adapter` leaf cannot satisfy verification. A supported-host snapshot must be fresh, Ed25519-verified, bound to the task and a one-use gate challenge, authenticate the complete canonical bypass event set with its signed count and SHA-256, and bind current later-gate resolution event IDs exactly in signed `resolutionEventIds`; in-process replay and resolution-binding state are ephemeral, and Phase 3B owns cross-process challenge and event-set durability.

The `FRESH` handoff cache entry uses a raw-byte SHA-256. `.gitattributes` marks `ai/agent-handoff.json` as `-text`, so Git does not rewrite line endings and the recorded digest is reproducible on LF and CRLF-default checkout hosts.

`scripts/ai/command-runner.sh` remains the only supported product-command path. Native adapters do not gain command execution authority through cache reuse. Unsupported-host verification may pass only with an explicit repository-only qualification, while supported-host faults remain completion-blocking. Phase 3B owns durable CI evidence, remote-runner cache parity, and CI adapter availability.
