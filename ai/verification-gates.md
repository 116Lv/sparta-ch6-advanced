# AI Workflow Verification Gates

## Human Policy Notes

`ai/verification-policy.json` is the canonical Phase 2C source for verification completeness, task/change applicability, workflow entry points, and result mapping. This Markdown file explains the policy for agents and reviewers. JSON is canonical. Markdown is not parsed as executable state.

Product commands remain NOT RUN for Phase 2C helper/static verification. `scripts/ai/verification-gate.sh` evaluates only static/helper/contract inputs and must not launch Gradle, build, product/unit project tests, server, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands.

## Entry Points

- `verification-level`: maps a change type to required verification checks.
- `api-smoke`: maps real API smoke requiredness for API-visible work.
- `failure-triage`: records failed or blocked leaf status before rerun or continuation.
- `review`: checks independent review and delegated-work readiness.
- `done-claim`: checks whether completion evidence is applicable before a done claim.

## Task/Change Applicability

Phase 2C defines task/change applicability by change type in `ai/verification-policy.json`. The supported change types are `documentation-only`, `static-workflow`, `domain-logic`, `db-api`, `auth-permission`, `critical-data`, and `user-flow`.

Verification completeness means every required check for the selected change type has an allowed mapped result and every inapplicable check is explicitly mapped with a reason. While `tracking_status` remains `pending_issue`, implementation QA may pass with a complete fallback, but issue-backed closure, reconciliation-complete, and unqualified overall DONE remain blocked.

## Result Mapping

- `NOT_CONFIGURED` on a required check maps to `BLOCKED`.
- `NOT_CONFIGURED` on an irrelevant or optional check maps to `NOT_APPLICABLE`.
- A missing non-native leaf is `NOT_CONFIGURED`; canonical policy describes configuration and applicability but never supplies leaf `PASS` evidence.
- Caller-supplied `NOT_APPLICABLE` is allowed only when the selected change type appears in that check's canonical `notApplicableFor` array. Otherwise it maps to `BLOCKED`, including for required checks.
- The internal native adapter's canonical unsupported-host result remains the sole non-caller exception and keeps the explicit repository-only qualification.
- `BLOCKED` on a required check remains `BLOCKED`.
- `FAIL` remains visible as `FAIL` for required and optional checks, and takes precedence over `BLOCKED` in the aggregate result.

`NOT_APPLICABLE` may be displayed as `N/A` in Markdown summaries, but executable JSON stores `NOT_APPLICABLE`.

Every check output carries the same five leaf-identity keys in one of two closed shapes. A verified external or native check requires all five to be non-null. A missing, synthesized, or policy-derived check requires all five to be null and cannot report raw or mapped `PASS` or `FAIL`; it therefore cannot validate as verified evidence. For an external leaf, `leafResultSha256` is derived from the exact bounded bytes that the loader parsed and accepted, without reopening the leaf path, and `evidenceRef` points to the bound evidence artifact when present. The internal native leaf records `ai/native-adapter-result.json`, the SHA-256 of that canonical in-process result, the canonical producer, checked-out commit, and canonical policy digest. One gate evaluation bounded-reads `ai/verification-policy.json` exactly once; strict parsing, schema validation, SHA-256 derivation, native identity, and all external leaf checks use the same recursively immutable snapshot, so a replacement race cannot mix policy semantics and identity.

## Native Runtime Adapter Leaf

`native-runtime-adapter` is an internal-only required check for every change type. `scripts/ai/verification-gate.sh` requires `--task-key` and `--gate-invocation-id` and may forward `--runtime-snapshot` and `--bypass-attempts` directly to the in-process evaluator for diagnosis. Those repository inputs cannot supply immutable external `HostNativeTrust` and cannot promote the public path above the canonical unsupported host. The public `native-adapter-gate` CLI accepts no host descriptor, probe, trust anchor, ledger, policy, snapshot, or bypass fixture capable of producing supported-host PASS. The gate never accepts a precomputed native adapter result. Ordinary `--leaf-results-file` input containing this check ID is forged state and returns `INVALID_STATE` with `NATIVE_ADAPTER_LEAF_FORGED` before leaf lookup.

The verification loop invokes `native_adapter_phase2c_leaf()` with the current correlation. That helper calls `native_adapter_gate()` against canonical `ai/native-runtime-adapters.json`; the check never reaches the static `registryCommandId: null` PASS fallback. Invalid task or gate correlation fails closed.

The current host version is `null`/`UNPROBED` and the host is `UNSUPPORTED`. Adapter result `UNSUPPORTED` maps to raw and mapped `NOT_APPLICABLE` with reason `HOST_UNSUPPORTED`; an overall PASS is qualified as `REPOSITORY_ONLY_HOST_UNSUPPORTED` and proves only the repository gate. Supported-host matching requires an authoritative `PROBED` version. For a supported host, missing authenticated enforcement is `NOT_CONFIGURED` or `BLOCKED`; producer/key/signature/freshness/challenge/replay/callback/crypto, redaction, correlation, or bypass faults remain `BLOCKED` or `FAIL`.

The result keeps `claimedSurfaces` separate from `trustedSurfaces`. Policy surfaces are baseline-only and cannot declare runtime `ENFORCED`. Missing or rejected snapshots retain trusted `NOT_CONFIGURED` surfaces. Only immutable external host trust plus a closed, fresh, Ed25519 snapshot with signed callback proof and atomic consumption in the external durable replay ledger can emit trusted `ENFORCED`; the process-local replay set is defense in depth. All four trusted surfaces plus no unresolved bypass are required for native adapter `PASS`. A later-gate `RESOLVED` event must bind exactly one prior detection by event ID, task, original gate invocation, deduplication key, and canonical detection digest before every current resolution event ID is compared with the bounded unique `resolutionEventIds` array inside the signed snapshot bytes. Missing, unrelated, multiple, later, or digest-mismatched detections and missing, mismatched, duplicate, oversized, or extra signed resolution IDs block, as do resolution claims on the canonical unsupported host or without a trusted snapshot. Canonical `supportedHosts` remains empty, so this supported path is exercised only with temporary external host trust, keys, and ledgers and creates no durable repository evidence.

`scripts/ai/command-runner.sh` remains the only supported product-command path. Native adapters do not execute product commands. Phase 3B owns CI adapter installation, remote-runner guarantees, durable CI evidence, CI ledger provisioning and retention, and cross-host parity.

## Evidence Boundary

Phase 2C and Phase 3A static/helper gates do not create repository `.ai-runs`, artifact manifests, finalized `run.json`, registry `VERIFIED` transitions, issue-backed closure claims, reconciliation-complete claims, or unqualified overall DONE claims. Phase 1B-3 remains `completenessEvaluated: false` with scope `INTEGRITY_ONLY`. Real project verification remains NOT RUN unless the supported command-runner evidence path is explicitly used.
