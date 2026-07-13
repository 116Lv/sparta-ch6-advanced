# Failure Triage Skill

## Purpose

Record root-cause context before any later approved failed-command rerun.

## Required Inputs

- Failed command evidence or helper/static failure output
- Current handoff state
- Applicable policy documents

## Allowed Operations

- Summarize failure symptoms.
- Identify owner, affected route, and next safe action.

## Prohibited Operations

- Product commands remain NOT RUN in Phase 2B.
- Do not authorize reruns by writing a local note.
- Do not hide failed evidence or rewrite failures as skipped checks.

## Evidence Outputs

- Failure triage summary in work logs.
- Blocker or next-handoff record.

## Handoff And Reuse

Handoffs include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and failure evidence refs.

## Phase 2B Boundary

This skill defines triage records only; rerun authority remains later scope.

## Phase 2C Entry Point

Phase 2C uses `scripts/ai/verification-gate.sh` with entry point `failure-triage`, canonical policy `ai/verification-policy.json`, and summary `ai/verification-gates.md`. Failed leaf results map to `FAIL`; blocked required leaf results map to `BLOCKED`; irrelevant checks map to `NOT_APPLICABLE`. Product commands remain NOT RUN.
