# Verification Runner Skill

## Purpose

Choose verification contracts and record what was or was not run without claiming verification completeness.

## Required Inputs

- `ai/verification-levels.md`
- `ai/command-registry.json`
- Current handoff state

## Allowed Operations

- Select static/helper/contract checks allowed by the current phase.
- Record explicit NOT RUN items.

## Prohibited Operations

- Product commands remain NOT RUN in Phase 2B.
- Do not claim verification completeness.
- Do not convert `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, or `FAIL` into PASS.

## Evidence Outputs

- Verification command names and observed results.
- Explicit NOT RUN list.

## Handoff And Reuse

Handoffs include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and verification evidence refs.

## Phase 2B Boundary

Phase 2B verifies only static/helper/contract artifacts and does not evaluate full task applicability.

## Phase 2C Entry Point

Phase 2C uses `scripts/ai/verification-gate.sh` with canonical `ai/verification-policy.json` and summary `ai/verification-gates.md` to evaluate verification completeness and task/change applicability. `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` are mapped by change type. Product commands remain NOT RUN for this static/helper gate.
