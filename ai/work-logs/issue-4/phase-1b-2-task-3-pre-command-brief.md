# Phase 1B-2 Task 3 PRE_COMMAND Brief

## Scope

Implement only approved Phase 1B-2 Task 3 in `workflow_helper.py`: exact framed fingerprints, closed input-path handling, allowlisted child-environment hashing, active-run PRE_COMMAND policy, same-run PASS prerequisites, immutable approval/policy audit artifacts, first RESERVED reservation, and PASS-only bounded reruns.

## Routing

- Owning feature: `none`
- Reason: PRE_COMMAND is repository-wide AI workflow infrastructure.
- Approved inputs:
  - `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`
  - `docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md`

## Boundaries

- Preserve approved Task 2 lock, session, recovery, and RESERVED-repair behavior.
- Run current LOCAL helper preflight before every PRE_COMMAND invocation.
- Require a schema-valid OPEN run and serialize every mutation under its exact held lock.
- Record unregistered/unsafe events only after a valid run exists.
- Treat approvals as audit-only; RISKY and DESTRUCTIVE remain blocked.
- Accept prerequisite evidence only when listed by the current session, contained in the run, schema/semantic valid, exact-tuple, same-run, and PASS.
- Create no reservation for rejected preconditions. Permit duplicate reruns only after PASS with a bounded one-line contained reason; FAIL/BLOCKED/RESERVED duplicates remain blocked.
- Do not add subprocess launch, process attempts, POST, shell runners, `run.json`, manifests, finalization, product commands, staging, or commits.

## TDD Record

Tests and approved fixtures were added first. Focused RED failed because `length_prefixed_frame`, `argv_hash`, `input_fingerprint`, `child_environment`, `environment_fingerprint`, and `pre_command` did not exist. Helper implementation followed only after that observed failure.
