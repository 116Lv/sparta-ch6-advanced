# Command Runner Skill

## Purpose

Select the supported command-runner workflow contract by registry ID without bypassing the Phase 1B boundary.

## Required Inputs

- `ai/command-registry.json`
- Phase 1B command-runner policy
- Current handoff state

## Allowed Operations

- Explain that `scripts/ai/command-runner.sh` is the only supported project-command path after Phase 1B.
- Record NOT RUN product commands for Phase 2B.

## Prohibited Operations

- Product commands remain NOT RUN in Phase 2B.
- Do not execute direct shell project commands.
- Do not execute RISKY, DESTRUCTIVE, non-POSIX, migration, seed, server, Docker, HTTP, or infrastructure commands.

## Evidence Outputs

- Work-log NOT RUN entries.
- Policy and handoff references.

## Handoff And Reuse

Handoffs include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and command registry refs.

## Phase 2B Boundary

Supported-path execution remains future or later-phase behavior for this task; Phase 2B only records the skill contract.
