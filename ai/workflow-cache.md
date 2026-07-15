# AI Workflow Cache

## Human Policy Notes

`ai/workflow-cache.json` is the canonical Phase 2A cache record. This Markdown file is a reviewable summary and policy note. JSON is canonical. Markdown is not parsed as executable state.

Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness, does not create durable command evidence, and does not mark registry commands `VERIFIED`.

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Cache records therefore support reuse and review; they are not complete host telemetry.

## Generated State Summary

Canonical source: `ai/workflow-cache.json`

Phase 2A started with an empty cache. Phase 2B adds a reviewable `HANDOFF_CONTEXT` record linking `ai/agent-handoff.json`, the Phase 2A context-cache fallback summary, and the Phase 2B skills/handoff fallback summary. Repo intake validates the cache shape and reports proposal-only stale or uncertain entries. A `HANDOFF_CONTEXT` entry's `evidenceRefs` preserve historical provenance; they do not authorize current handoff include or reusable scope. Current reuse scope comes only from the validated handoff, while cache freshness consumes the entry's digest-bound `key.paths`. Raw logs and local `.ai-runs` evidence do not belong here.

The current handoff cache digest binds schemaVersion 2 route-phase context, including unique activated triggers, effective required documents, the still-deferred document set, and closed typed path scopes. Cache reuse never widens `includePaths`, treats canonical opt-in eligibility as activation, promotes a deferred scope into default search scope, or makes an activated document optional. Route, phase, ownership, activation, required-context, active-Issue, or typed-scope changes require a new handoff and digest.

For a `READY` or `PARTIAL` handoff, repo intake converts a canonical handoff cache `STALE` or `UNCERTAIN` report into top-level `BLOCKED` status 2 while preserving the report details. This prevents a structural `PASS` from being mistaken for authorization to reuse stale route, phase, owner, trigger, Issue, or typed-scope context. An already `BLOCKED` handoff and non-handoff cache entries retain advisory invalidation reporting because they do not authorize handoff dispatch.

Repo intake recognizes only the single canonical ID `phase-2b-handoff-context`. It requires that entry to be `HANDOFF_CONTEXT` with exactly one `ai/agent-handoff.json` key binding and rejects missing or duplicate canonical identities and competing handoff bindings before computing invalidation. The blocker status is selected only from that canonical entry's report.

Semantic validation also requires globally unique cache entry IDs and unique path identities within each path-based key. Sharing a general input path across distinct entries remains allowed; only a competing `HANDOFF_CONTEXT` binding to the canonical handoff path is cross-entry invalid state.

Phase 2C adds reviewable links to `ai/verification-gates.md`, canonical `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh` for verification completeness and task/change applicability. `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mapping remains change-type specific. Product commands remain NOT RUN for static/helper gates.

Phase 3A adds `ai/native-runtime-adapters.json`, `ai/native-runtime-adapters.md`, and the closed native runtime snapshot schema to reusable handoff context. Runtime snapshots, signatures, public keys, callback proofs, signed task/event-set facts, signed `resolutionEventIds`, challenge-consumption state, and bypass attempts remain per-invocation inputs and are never reusable cache PASS evidence. Canonical current-host state remains `UNSUPPORTED` with an unprobed version. The raw-byte handoff digest is portable because `.gitattributes` marks `ai/agent-handoff.json` as `-text`, preventing checkout EOL conversion.

Verification-decision cache entries, when durable inputs exist, bind the exact ordered required-plus-optional check sequence actually aggregated for the selected change type. Every item is check/producer-indexed and binds a verified leaf-result reference and digest to an evidence path, digest, and canonical schema. The current entry point never narrows this set. The canonical cache intentionally contains no reusable verification decision while those complete durable inputs are unavailable.

For the native check, only the exact logical result reference `ai/native-adapter-result.json` and the exact canonical evidence `ai/native-runtime-adapters.json` with its native-runtime-adapters schema are accepted. Matching bytes at a copied path are stale. Even the exact current binding remains uncertain because the native result has no durable task/gate/commit/policy/freshness envelope; it cannot make a cache decision fresh.
