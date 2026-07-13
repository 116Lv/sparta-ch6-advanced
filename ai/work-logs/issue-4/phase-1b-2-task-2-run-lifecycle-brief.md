# Phase 1B-2 Task 2 Run Lifecycle Brief

## Scope

Implement only approved Phase 1B-2 Task 2: `start_run(root, run_id, task_key)`, exclusive active-run locking, dead-and-expired lock recovery history, and safe monotonic repair of stale `RESERVED` attempts.

## Routing

- Owning feature: `none`
- Reason: the command gateway is repository-wide AI workflow infrastructure.
- Approved inputs:
  - `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`
  - `docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md`

## Boundaries

- Preserve Task 1 and all prior work.
- Call current LOCAL runtime preflight before every run-start mutation.
- Create only `.ai-runs/<run-id>/.state/run-session.json` in temporary test repositories; do not create `run.json`.
- Validate and publish the exact `RUN_START` envelope, and fail closed on IDs, paths, lock ownership, permissions, malformed control JSON, collisions, or escaped/symlinked paths.
- Lock recovery requires both a dead owner and an expired acquisition time. Recovery appends its immutable history under the replacement lock before cleanup and release.
- Recovery can repair only a safe, existing, identity-matching `RESERVED` process attempt to `BLOCKED`; it never launches a process.
- Do not add a shell interface, subprocess support, command execution, manifest/finalization behavior, product commands, staging, or commits.

## TDD Record

The next change is a test-only RED cycle for run start, lock/recovery behavior, and the current-preflight regression. Production helper code follows only after the failing behavior is observed.
