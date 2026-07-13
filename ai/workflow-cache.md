# AI Workflow Cache

## Human Policy Notes

`ai/workflow-cache.json` is the canonical Phase 2A cache record. This Markdown file is a reviewable summary and policy note. JSON is canonical. Markdown is not parsed as executable state.

Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness, does not create durable command evidence, and does not mark registry commands `VERIFIED`.

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Cache records therefore support reuse and review; they are not complete host telemetry.

## Generated State Summary

Canonical source: `ai/workflow-cache.json`

Phase 2A started with an empty cache. Phase 2B adds a reviewable `HANDOFF_CONTEXT` record linking `ai/agent-handoff.json`, the Phase 2A context-cache fallback summary, and the Phase 2B skills/handoff fallback summary. Repo intake validates the cache shape and reports proposal-only stale or uncertain entries. Raw logs and local `.ai-runs` evidence do not belong here.

Phase 2C adds reviewable links to `ai/verification-gates.md`, canonical `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh` for verification completeness and task/change applicability. `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mapping remains change-type specific. Product commands remain NOT RUN for static/helper gates.
