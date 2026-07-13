# Repo Intake Skill

## Purpose

Reuse Phase 2A repository context and cache records before rediscovery.

## Required Inputs

- `ai/context-map.json`
- `ai/workflow-cache.json`
- `ai/project-state.json`
- `ai/command-registry.json`

## Allowed Operations

- Run read-only repo intake through `scripts/ai/repo-intake.sh --output -`.
- Report proposal-only project-state refresh and command-discovery updates.

## Prohibited Operations

- Product commands remain NOT RUN in Phase 2B.
- Do not create repository `.ai-runs`.
- Do not mark registry commands `VERIFIED`.

## Evidence Outputs

- Scrubbed work-log summaries.
- `REPO_INTAKE` structured result when the helper is explicitly run.

## Handoff And Reuse

Handoffs include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, and `not_run_project_commands`.

## Phase 2B Boundary

This skill is read-only and proposal-only in Phase 2B.
