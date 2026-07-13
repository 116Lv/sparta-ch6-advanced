# Phase 1B-2 Task 4 POSIX Launch Brief

## Scope

Implement only approved Phase 1B-2 Task 4 in `workflow_helper.py`: the closed `execute_command(root, request)` orchestration seam, exact `launch_reserved(argv, cwd, env)` subprocess contract, and bounded `terminate_process_group(process, grace_seconds)` cleanup.

## Required Behavior

- Return PRE_COMMAND `NOT_CONFIGURED` before reservation or launch on non-POSIX hosts, missing/empty allowlisted `PATH`, or unavailable exact `/bin/sh` executable regular file.
- Accept only a closed execute request. Caller input cannot select or look up an interpreter or provide a child environment.
- Launch only PRE_COMMAND PASS argv as a list with `shell=False`, contained cwd, exact allowlisted environment, `DEVNULL` stdin, separate stdout/stderr pipes, and a new process session.
- Terminate only a process group still led by the launched PID: SIGTERM, one bounded wait, SIGKILL if needed, and one bounded reap wait.
- Keep standalone RUN_START and PRE_COMMAND non-launching. Task 5 POST persistence, redaction, capture, terminal reservation transitions, and process publication remain absent.

## Test Boundary

Use mocked cross-platform contracts on every host and a capability-gated real POSIX launch in a `TemporaryDirectory` repository with `ai/fixtures/phase-1b/execution/fake-gradlew`. Never execute repository Gradle, build, product tests, server, Docker, HTTP/API, database, migration, seed, or infrastructure commands. Never create repository-root `.ai-runs`, stage, or commit.
