# AI Workflow Cache Policy

## Human Policy Notes

`ai/workflow-cache.json` is the canonical Phase 2A cache record. This Markdown file explains freshness and invalidation policy. JSON is canonical. Markdown is not parsed as executable state.

Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness and does not promote ignored local evidence into durable cross-machine proof.

## Cache Keys

File-read entries are keyed by normalized repository-relative path and SHA-256 content digest. Command evidence summaries are keyed by command ID, argv hash, working directory, declared input fingerprints, and allowlisted environment fingerprint from the supported command gateway.

Every cache entry ID is globally unique. Within one path-based cache entry, each repository-relative path identity may appear only once even when competing records carry different digests. Different cache entries may legitimately bind the same general input path because their kinds and reuse purposes can differ; the stricter canonical handoff anti-spoof rule below remains the only cross-entry path exclusion.

Verification-decision entries use a distinct closed key containing task key, gate invocation ID, checked-out commit SHA, change type, entry point, verification-policy SHA-256, and the exact ordered check set that `verification_gate` consumes from the selected change type's required checks followed by optional checks. The entry point remains correlation identity and applicability input; it does not filter that consumed set. Each producer/check-indexed binding contains the verified leaf-result reference and SHA-256 plus its evidence path, SHA-256, and canonical schema. The key also binds the relevant environment fingerprint and expiry. Task and gate identifiers are mandatory lookup identity, but repo intake does not claim an external authority for them. A non-null environment fingerprint is `UNCERTAIN` until an authoritative current environment mapping exists.

## Freshness Rules

A cache entry is `FRESH` only when every declared path still exists as expected and every recorded digest matches. Verification-decision reuse additionally requires the current commit and policy digest, exact ordered canonical check/producer set, every leaf-result and evidence digest, every canonical evidence schema, leaf correlation and freshness, and unexpired decision to match. Missing, extra, duplicate, reordered, wrong-producer, wrong-schema, or digest-mismatched known bindings are `STALE`; an unavailable path or unmapped classification, task/gate identity, policy/commit source, or environment input is `UNCERTAIN` unless another proven mismatch or expiry makes the entry `STALE`.

The native cache binding has additional fixed identities: `leafResultRef` must be exactly `ai/native-adapter-result.json`, while evidence must be exactly `ai/native-runtime-adapters.json` validated with `ai/schemas/native-runtime-adapters.schema.json`. A copied or arbitrary native result/evidence path is `STALE` even when its bytes and digest match. The current native result schema does not carry a durable task, gate, commit, policy, and freshness envelope, so an otherwise exact native binding remains `UNCERTAIN` and prevents a `FRESH` verification decision until that correlated durable envelope exists.

The canonical cache does not materialize a reusable verification PASS decision whose commit or short-lived expiry would become self-referential or immediately stale. Such decisions may be recorded only when every durable input is available.

## Conservative Invalidation

When dependency mapping is incomplete or ambiguous, the workflow prefers re-verification over unsafe reuse. Phase 2A repo intake may report proposal-only `projectStateRefresh` and `commandDiscoveryUpdates` records, but it does not execute commands, does not create `.ai-runs`, and does not mark a registry command `VERIFIED`.

Route and handoff reuse is phase-sensitive. A cached read from one phase does not make a later phase's required document optional, and a task-phase, owning-feature, activated-trigger, effective-required, or still-deferred-set change invalidates reuse until the handoff is re-routed. Deferred documents remain unread until activation, then become required context and leave the still-deferred set.

Repo intake fails closed when a `READY` or `PARTIAL` handoff's canonical `HANDOFF_CONTEXT` entry binds `ai/agent-handoff.json` but reports `STALE` or `UNCERTAIN`: the top-level result is `BLOCKED`, status 2, with `HANDOFF_CONTEXT_CACHE_STALE` or `HANDOFF_CONTEXT_CACHE_UNCERTAIN`, and the full cache invalidation report remains in `data`. A handoff already marked `BLOCKED` is not dispatch-ready, so its cache result remains advisory and repo intake may still pass structural validation. `STALE` or `UNCERTAIN` entries of other cache kinds remain advisory.

The canonical handoff cache identity is closed: exactly one entry must have ID `phase-2b-handoff-context`, that entry must be `HANDOFF_CONTEXT`, and its key must bind `ai/agent-handoff.json` exactly once. A missing, duplicate, wrong-kind, or wrong-path canonical entry is invalid state. Any other `HANDOFF_CONTEXT` entry that binds the canonical handoff path is ambiguous invalid state and is rejected before freshness evaluation, so a spoof entry cannot force `BLOCKED` or authorize reuse.

## Evidence Boundary

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Cache policy therefore combines structured records, work logs, handoff notes, and review gates rather than claiming total technical interception.

## Phase 3A Native Boundary

The current host-native adapter state is `UNSUPPORTED` with `hostVersion: null` and `versionProvenance: UNPROBED`. Native runtime snapshots and bypass-attempt references are per-invocation inputs correlated by task and gate ID; they are not reusable cached PASS results. A cached, repository-authored, digest-mismatched, correlation-mismatched, or otherwise precomputed `native-runtime-adapter` leaf cannot satisfy verification. A supported-host snapshot must be fresh, Ed25519-verified, bound to the task and a one-use gate challenge, authenticate the complete canonical bypass event set with its signed count and SHA-256, and bind current later-gate resolution event IDs exactly in signed `resolutionEventIds`; in-process replay and resolution-binding state are ephemeral, and Phase 3B owns cross-process challenge and event-set durability.

The `FRESH` handoff cache entry uses a raw-byte SHA-256. `.gitattributes` marks `ai/agent-handoff.json` as `-text`, so Git does not rewrite line endings and the recorded digest is reproducible on LF and CRLF-default checkout hosts.

`scripts/ai/command-runner.sh` remains the only supported product-command path. Native adapters do not gain command execution authority through cache reuse. Unsupported-host verification may pass only with an explicit repository-only qualification, while supported-host faults remain completion-blocking. Phase 3B owns durable CI evidence, remote-runner cache parity, and CI adapter availability.
