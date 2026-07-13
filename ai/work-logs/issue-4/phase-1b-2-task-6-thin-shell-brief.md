# Phase 1B-2 Task 6 Thin Closed Shell Brief

## Routing

Owning feature: none. This is repository-wide AI workflow enforcement under the approved Phase 1B specification and Phase 1B-2 Task 6 plan.

## Scope

Add only the closed `command-runner.sh` and `workflow-gate.sh` transports, their isolated Git Bash contract test, and the exact Python CLI dispatch needed to call the approved Tasks 1-5 operations.

## Closed Interfaces

```text
command-runner.sh start --run-id <id> --task-key <key>
command-runner.sh run <command-id> --run-id <id> [--parameters-file <repo-json>] [--rerun-reason-file <repo-text>] [--approval-ref <repo-json>]
workflow-gate.sh RUN_START --run-id <id> --task-key <key>
workflow-gate.sh PRE_COMMAND --run-id <id> --command-id <id> [same optional files]
workflow-gate.sh POST_COMMAND --run-id <id> --attempt-id <id>
```

The order is literal. Missing, duplicate, reordered, raw, or extra arguments are policy violations with operation-specific structured results and exit `4`. Valid invocations relay helper stdout and exit status unchanged.

## Launch Boundary

Only `command-runner.sh run` selects helper operation `execute-command`. Start delegates `RUN_START` through `workflow-gate.sh`; every workflow-gate operation is validation or persistence only. Shell transports use quoted arguments and perform no JSON parsing, command-string evaluation, dynamic sourcing, or project-command launch.

## Explicit Deferrals

Do not accept finalization stages or publish manifests, `run.json`, done claims, registry transitions, or Phase 1B-3 state. Contract tests use temporary repositories and an instrumented helper transport only; they never execute the repository Gradle wrapper or any product command.
