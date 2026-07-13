# AI Workflow Cache Policy

## Human Policy Notes

`ai/workflow-cache.json` is the canonical Phase 2A cache record. This Markdown file explains freshness and invalidation policy. JSON is canonical. Markdown is not parsed as executable state.

Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness and does not promote ignored local evidence into durable cross-machine proof.

## Cache Keys

File-read entries are keyed by normalized repository-relative path and SHA-256 content digest. Command evidence summaries are keyed by command ID, argv hash, working directory, declared input fingerprints, and allowlisted environment fingerprint from the supported command gateway.

## Freshness Rules

A cache entry is `FRESH` only when every declared path still exists as expected and every recorded digest matches. A changed mapped file makes the entry `STALE`. A missing or unmapped input makes the entry `UNCERTAIN` unless a specific route can prove it irrelevant.

## Conservative Invalidation

When dependency mapping is incomplete or ambiguous, the workflow prefers re-verification over unsafe reuse. Phase 2A repo intake may report proposal-only `projectStateRefresh` and `commandDiscoveryUpdates` records, but it does not execute commands, does not create `.ai-runs`, and does not mark a registry command `VERIFIED`.

## Evidence Boundary

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Cache policy therefore combines structured records, work logs, handoff notes, and review gates rather than claiming total technical interception.
