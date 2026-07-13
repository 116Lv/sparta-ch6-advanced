---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-task-4-implementation-agent
tracking_status: issue_backed
status: in_review
owning_feature: "none"
current_owner: phase-1b-2-task-4-subprocess-reviewer
started_at: 2026-07-11T16:50:00+09:00
ended_at: 2026-07-11T17:22:13+09:00
last_updated: 2026-07-13T09:32:29+09:00
branch: main
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - ai/work-logs/issue-4/phase-1b-2-task-4-posix-launch-brief.md
  - ai/fixtures/phase-1b/execution/fake-gradlew
changed_files:
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/work-logs/issue-4/phase-1b-2-task-4-implementation-agent.md
commands_run:
  - "C:\\Program Files\\Git\\bin\\bash.exe -lc 'python3 -m unittest scripts/ai/tests/test_workflow_helper.py -v -k PosixLaunchTests' (launcher attempt: exit 1 before tests; WindowsApps python3 permission denied)"
  - "C:\\Program Files\\Git\\bin\\bash.exe -lc '/c/dev/Python/Python39/python.exe -m unittest scripts/ai/tests/test_workflow_helper.py -v -k PosixLaunchTests' (inherited RED: exit 1)"
  - "C:\\Program Files\\Git\\bin\\bash.exe -lc '/c/dev/Python/Python39/python.exe -m unittest scripts/ai/tests/test_workflow_helper.py -v -k PosixLaunchTests' (first GREEN attempt: exit 1)"
  - "C:\\Program Files\\Git\\bin\\bash.exe -lc '/c/dev/Python/Python39/python.exe -m unittest scripts/ai/tests/test_workflow_helper.py -v -k PosixLaunchTests' (focused GREEN: exit 0)"
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/run-helper-tests.sh (first full regression: exit 1)"
  - "C:\\Program Files\\Git\\bin\\bash.exe -lc '/c/dev/Python/Python39/python.exe -m unittest <two focused compatibility tests> -v' (exit 0)"
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/run-helper-tests.sh (final full regression: exit 0)"
  - "C:\\Program Files\\Git\\bin\\bash.exe scripts/ai/tests/test-runtime-preflight.sh (exit 0)"
  - "Python AST Popen/reachability scan; repository .ai-runs check; git staged-file inventory; git status --short"
  - "git diff --check (exit 0; pre-existing CRLF warnings only)"
tests_run:
  - "Inherited Task 4 RED: Ran 12 tests; FAILED (failures=2, errors=14, skipped=1) because the Task 4 production interfaces were absent."
  - "First focused GREEN attempt: Ran 12 tests; FAILED (failures=1, errors=2, skipped=1) on two Windows-only harness assumptions."
  - "Focused Task 4 GREEN: Ran 12 tests; OK (skipped=1)."
  - "First full helper regression: Ran 179 tests; FAILED (failures=2, skipped=15) on the exact approved module docstring and a Phase 1B-1 whole-module subprocess scan."
  - "Focused compatibility correction: Ran 2 tests; OK."
  - "Final full helper through exact Git Bash: Ran 179 tests; OK (skipped=15)."
  - "Runtime preflight through exact Git Bash: PASS: runtime preflight contract."
blockers: []
historical_blockers:
  - "GitHub Issue creation remains blocked by the recorded integration 403; fallback reconciliation is still required."
  - "The approved plan requires a fresh subprocess reviewer checkpoint before Task 5."
reconciliation_required: false
issue_creation_attempted_at: 2026-07-10T12:37:12Z
issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"
expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 1B command gateway without product behavior changes."
migration_history:
  - migrated_at: 2026-07-13T08:54:37+09:00
    from: ai/work-logs/no-issue/phase-1b-command-gateway
    to: ai/work-logs/issue-4
    comment_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4#issuecomment-4953423372
---

## Reconciliation Update

GitHub Issue #4 now backs this historical role record. Statements below about unavailable Issue creation, pending reconciliation, or the earlier 403 describe the state when this role executed; they are not current blockers.

# Summary

Task 4 implements the closed POSIX-only launch seam and bounded process-group termination without adding Task 5 redaction, capture, or POST persistence.

# Work Done

- Added `execute_command(root, request)` with a closed request map and capability checks before PRE_COMMAND reservation.
- Added exact non-POSIX, missing/empty PATH, invalid environment, and unavailable `/bin/sh` result mappings.
- Added `launch_reserved(argv, cwd, env)` as the only `subprocess.Popen` owner, using list argv, contained cwd, exact allowlisted environment, `shell=False`, `DEVNULL`, separate pipes, and `start_new_session=True`.
- Added `terminate_process_group(process, grace_seconds)` with leader identity checks before each signal, bounded SIGTERM and SIGKILL waits, bounded reap, and wrapped process-group errors.
- Preserved standalone RUN_START and PRE_COMMAND as non-launching stages.
- Corrected inherited Windows test mechanics: non-string environment rejection now patches the environment object instead of assigning an invalid value to real `os.environ`, and mocked SIGKILL uses POSIX signal number 9 only when Windows Python lacks the symbol.
- Narrowed the inherited Phase 1B-1 resolver isolation assertion from a whole-module subprocess ban to resolver-function reachability, preserving the original resolver guarantee after Task 4 legitimately adds the launch module.
- Inspected `fake-gradlew` and the Task 4 brief; both were contract-correct and remain unchanged.

# Historical State At Execution
Implementation and local contract verification are GREEN. The repository-root `.ai-runs` path is absent and the staging index is empty. Task 4 is awaiting the plan-required fresh subprocess review.

# Decisions

- Capability checks run before PRE_COMMAND so an unsupported host, missing child PATH, invalid allowlisted environment, or unavailable exact `/bin/sh` cannot create a reservation.
- PRE_COMMAND receives the exact child environment that is later passed to `Popen`, keeping the environment fingerprint and launch environment identical.
- The process group is signalled only when `getpgid(process.pid) == process.pid`; identity is checked again before escalation to SIGKILL.
- Task 5 spawn-result persistence, timeout orchestration, stream capture, redaction, terminal reservation transition, and POST_COMMAND evidence remain deferred.

# Verification Evidence

- Inherited RED: exit `1`; `Ran 12`; `FAILED (failures=2, errors=14, skipped=1)`. Missing APIs included `execute_command`, `host_is_posix`, `posix_shell_available`, `launch_reserved`, `terminate_process_group`, `ProcessGroupError`, and the sole `Popen` owner.
- Focused GREEN: exit `0`; `Ran 12`; `OK (skipped=1)`. The only skip was `real launch requires a POSIX host` on Windows; mocked cross-platform launch contracts all ran.
- Full helper: exit `0`; `Ran 179`; `OK (skipped=15)`. The fifteen skips are environment capability cases already declared by the suite, including the one real POSIX Task 4 launch.
- Runtime preflight: exit `0`; exact output `PASS: runtime preflight contract`.
- Static reachability: `Popen owners: ['launch_reserved']`; `launch_reserved callers: ['execute_command']`; RUN_START and PRE_COMMAND launch-symbol sets are empty.
- Hygiene: repository-root `.ai-runs` absent; staged files `0`; `git diff --check` exit `0` with warnings only for pre-existing tracked CRLF conversions.
- NOT RUN: repository Gradle, build, product/unit project tests, application server, Docker Compose, HTTP/curl/API, database, migration, seed, and infrastructure commands.

# Historical Blockers At Execution
- Pending-Issue reconciliation remains blocked by the recorded GitHub integration `403 Resource not accessible by integration`.
- Fresh subprocess review is required before the Task 5 handoff.

# Historical Next Handoff
- Next role: Phase 1B-2 Task 4 subprocess reviewer
- Required reading:
  - [Phase 1B Specification](../../../docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md)
  - [Phase 1B-2 Plan](../../../docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md)
  - [Task 4 Brief](phase-1b-2-task-4-posix-launch-brief.md)
- Context links:
  - [Issue summary](README.md)
  - [Task 3 reviewer](phase-1b-2-task-3-reviewer.md)
- Remaining work: independently trace every `Popen` and `launch_reserved` edge, validate POSIX capability mapping and exact launch arguments, and review bounded process-group cleanup.
- Evidence required: Critical/Important/Minor findings and an explicit Task 4 approval verdict while preserving pending-Issue reconciliation metadata.
