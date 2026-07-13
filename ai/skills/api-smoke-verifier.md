# API Smoke Verifier Skill

## Purpose

Classify API smoke verification readiness without running HTTP requests in Phase 2B.

## Required Inputs

- `ai/command-registry.json`
- API smoke command status
- Current handoff state

## Allowed Operations

- Report API smoke as `NOT_CONFIGURED` when cases or prerequisites are absent.
- Report API smoke as `BLOCKED` when the change requires real API evidence but prerequisites are absent.

## Prohibited Operations

- Product commands remain NOT RUN in Phase 2B.
- This skill must not run HTTP, curl, or API calls in Phase 2B.
- Do not start servers or Docker Compose.
- Do not claim API verification complete without real request evidence in a later approved phase.

## Evidence Outputs

- NOT RUN or readiness classification in work logs.

## Handoff And Reuse

Handoffs include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and API smoke classification.

## Phase 2B Boundary

Phase 2B records the contract only. Real API smoke execution remains later scope.

## Phase 2C Entry Point

Phase 2C uses `scripts/ai/verification-gate.sh` with entry point `api-smoke`, canonical policy `ai/verification-policy.json`, and summary `ai/verification-gates.md`. Missing API smoke capability maps to `BLOCKED` for API/applicable change types and to `NOT_APPLICABLE` for unrelated change types. Product commands remain NOT RUN.
