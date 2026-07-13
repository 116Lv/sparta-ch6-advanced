# Review Gate Skill

## Purpose

Check scope, evidence, cache reuse, handoff state, and completion-readiness boundaries.

## Required Inputs

- Diff or changed-file list
- Verification evidence
- `ai/agent-handoff.json`
- Work-log summary

## Allowed Operations

- Perform static review.
- Block unsupported completion claims.
- Confirm pending GitHub reconciliation status.

## Prohibited Operations

- Product commands remain NOT RUN in Phase 2B.
- Do not claim issue-backed closure while `tracking_status` is `pending_issue`.
- Do not claim reconciliation complete, verification complete, registry `VERIFIED`, or unqualified overall DONE.

## Evidence Outputs

- Review log with PASS/FAIL and findings.

## Handoff And Reuse

Handoffs include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and `github_reconciliation_status`.

## Phase 2B Boundary

Review can pass Phase 2B implementation scope only. It cannot close the GitHub reconciliation gap.

## Phase 2C Entry Point

Phase 2C uses `scripts/ai/verification-gate.sh` with entry points `review` and `done-claim`, canonical policy `ai/verification-policy.json`, and summary `ai/verification-gates.md`. The gate checks verification completeness and task/change applicability while preserving `pending_issue`; issue-backed closure, reconciliation-complete claims, and unqualified overall DONE remain blocked until reconciliation completes. Product commands remain NOT RUN.
