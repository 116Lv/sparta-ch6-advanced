# AI Workflow Agent Handoff

## Human Policy Notes

`ai/agent-handoff.json` is the canonical Phase 2B handoff packet. This Markdown file explains how orchestrators and workers reuse that packet during issue summaries, role logs, and review.

JSON is canonical. Markdown is not parsed as executable state. Product commands remain NOT RUN in Phase 2B.

## Required Handoff State

Every Phase 2B handoff carries:

- `skill_ids`
- `handoff_state_ref`
- `reusable_context_refs`
- `not_run_project_commands`
- `github_reconciliation_status`

The current canonical state is `ai/agent-handoff.json`, and the skill catalog is `ai/skill-catalog.json`.

## Reuse Contract

Workers must reuse `ai/context-map.json`, `ai/workflow-cache.json`, the Phase 2A work log, and the Phase 2B issue summary before rediscovering workflow context. Cache or context exceptions must be recorded in the role log.

## Boundary

Phase 2B does not create repository `.ai-runs`, artifact manifests, finalized `run.json`, registry `VERIFIED` transitions, verification-completeness claims, issue-backed closure claims, reconciliation-complete claims, or unqualified overall DONE claims.

## Phase 2C Verification Gates

Phase 2C handoffs should include `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh` when verification completeness or task/change applicability is in scope. `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` are mapped by change type. Product commands remain NOT RUN for static/helper gates. GitHub Issue #7 now backs the handoff, but Issue tracking does not by itself close the Issue or authorize an unqualified overall DONE claim.
