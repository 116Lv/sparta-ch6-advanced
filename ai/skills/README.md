# AI Workflow Skills

## Purpose

Phase 2B defines reusable AI workflow skill contracts. `ai/skill-catalog.json` is canonical for the skill list. Product commands remain NOT RUN in Phase 2B.

## Required Skills

- `repo-intake`
- `command-runner`
- `verification-runner`
- `api-smoke-verifier`
- `failure-triage`
- `docs-sync`
- `review-gate`

The canonical catalog must contain this exact ID set with each ID appearing once. Schema `uniqueItems` is defense in depth; semantic validation rejects duplicate, missing, substituted, or unknown IDs even when the seven catalog objects remain structurally distinct.

## Shared Boundary

These skills define inputs, outputs, handoff requirements, and reviewable evidence. They do not create repository `.ai-runs`, artifact manifests, finalized `run.json`, registry `VERIFIED` transitions, verification-completeness claims, issue-backed closure, reconciliation-complete claims, or unqualified overall DONE claims.

## Phase 2C Verification Gates

Phase 2C connects `verification-runner`, `api-smoke-verifier`, `failure-triage`, and `review-gate` to `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh`. These static/helper gates define verification completeness, task/change applicability, and `NOT_CONFIGURED` / `NOT_APPLICABLE` / `BLOCKED` / `FAIL` mapping. Product commands remain NOT RUN.
