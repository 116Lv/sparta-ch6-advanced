---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: phase-1b-2-task-4-subprocess-reviewer
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: phase-1b-2-task-4-subprocess-reviewer
started_at: 2026-07-11T17:22:13+09:00
ended_at: 2026-07-11T17:29:23+09:00
last_updated: 2026-07-13T08:54:37+09:00
branch: main
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-11-ai-workflow-phase-1b-2-implementation.md
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/fixtures/phase-1b/execution/fake-gradlew
  - ai/work-logs/issue-4/phase-1b-2-task-4-posix-launch-brief.md
  - ai/work-logs/issue-4/phase-1b-2-task-4-implementation-agent.md
findings:
  critical: 0
  important: 0
  minor: 0
changed_files:
  - ai/work-logs/issue-4/phase-1b-2-task-4-reviewer.md
commands_run:
  - "Static review only; no tests or implementation commands were run."
tests_run:
  - "Accepted implementation evidence recorded in the preserved review body."
blockers: []
reconciliation_required: true
issue_creation_attempted_at: 2026-07-10T12:37:12Z
issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"
expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 1B command gateway without product behavior changes."
migration_history:
  - migrated_at: 2026-07-13T08:54:37+09:00
    from: ai/work-logs/no-issue/phase-1b-command-gateway
    to: ai/work-logs/issue-4
---

## Reconciliation Update

GitHub Issue #4 now backs this historical role record. Statements below about unavailable Issue creation, pending reconciliation, or the earlier 403 describe the state when this role executed; they are not current blockers.

# Phase 1B-2 Task 4 Subprocess/Security Review

## Verdict

**PASS. Status: DONE. Findings: Critical 0, Important 0, Minor 0.**

Owning feature: none. This is repository-wide AI workflow enforcement, not product-feature behavior. The inspected implementation is fully within approved Phase 1B-2 Task 4 scope.

## Independent Trace

1. **Closed subprocess reachability: PASS.** The only production `Popen` call is `subprocess.Popen` in `launch_reserved` (`scripts/ai/workflow_helper.py:1253-1263`), and its only production caller is `execute_command` (`scripts/ai/workflow_helper.py:1320`, `1364`). Standalone `start_run` and `pre_command` contain no launch edge; no standalone POST implementation exists in Task 4. The AST contract independently enforces the same owner/caller set and standalone exclusions (`scripts/ai/tests/test_workflow_helper.py:4338-4355`). The direct test call at lines 4378-4380 is confined to the harmless temporary-repository POSIX fixture.
2. **Platform and capability mapping: PASS.** `host_is_posix` is exact `os.name == "posix"`; `/bin/sh` is an exact absolute path and must stat as a regular file and pass `X_OK` (`scripts/ai/workflow_helper.py:1240-1250`). `execute_command` maps non-POSIX, missing/empty copied PATH, and unavailable `/bin/sh` to PRE_COMMAND `NOT_CONFIGURED`, exit 3, before PRE reservation or launch (`scripts/ai/workflow_helper.py:1326-1339`). Mocked zero-`Popen` mappings and missing/non-file/non-executable shell cases remain active cross-platform (`scripts/ai/tests/test_workflow_helper.py:4190-4230`).
3. **Closed request and exact child environment: PASS.** The execute request requires exactly `runId` and `commandId` with only the three approved optional references; interpreter/environment keys and non-dicts fail as `POLICY_VIOLATION` with no launch (`scripts/ai/workflow_helper.py:1321-1325`; `scripts/ai/tests/test_workflow_helper.py:4248-4259`). The child map starts empty, copies only PATH, JAVA_HOME, GRADLE_USER_HOME, HOME, TMPDIR, LANG, and LC_ALL, and rejects non-string/NUL/newline values (`scripts/ai/workflow_helper.py:36-38`, `1219-1230`). That exact map is supplied to PRE for its sorted environment fingerprint and then unchanged to launch (`scripts/ai/workflow_helper.py:1341-1349`, `1364`, `3503`). No caller-selected interpreter, environment, `which`, or PATH lookup is used.
4. **Contained argv launch contract: PASS.** PRE PASS data is revalidated as a non-empty list of non-empty strings, and cwd is strict-resolved, directory-checked, and required to remain under the strict-resolved repository root (`scripts/ai/workflow_helper.py:1350-1364`, `1300-1317`). `Popen` receives the list argv, contained cwd, exact env, `shell=False`, `DEVNULL` stdin, separate stdout/stderr PIPEs, and `start_new_session=True` (`scripts/ai/workflow_helper.py:1253-1263`). The exact mocked call is asserted at test lines 4232-4246.
5. **Process-group cleanup: PASS.** An already-exited child returns before identity lookup or signaling. A live child must still satisfy `getpgid(process.pid) == process.pid` before SIGTERM and again before SIGKILL; failed/mismatched identity blocks signaling (`scripts/ai/workflow_helper.py:1266-1289`). Cleanup performs one grace-bounded wait after SIGTERM, one grace-bounded reap after SIGKILL, and maps unreaped timeout plus attribute/OS/type/value failures to `ProcessGroupError` (`scripts/ai/workflow_helper.py:1273-1297`). Tests cover ordered TERM/KILL, both bounded waits, unrelated-group rejection with zero signals, unreaped timeout, signal OS error, and already-exited zero-signal behavior (`scripts/ai/tests/test_workflow_helper.py:4284-4336`).
6. **Windows and fixture coverage: PASS.** Only the real POSIX launch test is guarded by `skipUnless(os.name == "posix")`; all mocked launch and cleanup contracts remain active on Windows (`scripts/ai/tests/test_workflow_helper.py:4151-4366`, `4368-4384`). The fake wrapper is exact `#!/bin/sh\n`, uses only `printf` and a shell loop, and preserves spaces/metacharacters as one argv element (`ai/fixtures/phase-1b/execution/fake-gradlew:1-5`; test lines 4357-4384).
7. **Task 5 boundary: PASS.** Task 4 adds no POST orchestration, stream consumption/capture, scrubber/redaction implementation, process-attempt publication, terminal reservation transition, or command-result persistence. `execute_command` returns the PRE result/status and spawned process only (`scripts/ai/workflow_helper.py:1364-1365`). Existing POST schema validation and stale-RESERVED repair support are inherited earlier-phase contracts, not a Task 5 execution path.

## Accepted Evidence

- Inherited RED: `Ran 12`; `FAILED (failures=2, errors=14, skipped=1)`.
- Focused GREEN: `Ran 12`; `OK (skipped=1)`; the sole skip was the real POSIX launch on Windows.
- Full helper regression: `Ran 179`; `OK (skipped=15)`.
- Runtime preflight: `PASS: runtime preflight contract`.
- Repository-root `.ai-runs`: absent. Staging index: empty (`0`).
- No tests, helper commands, project commands, staging, or commits were run by this independent reviewer; evidence above is accepted from the implementation handoff as instructed. Review activity was limited to read-only static inspection and this reviewer-log write.

## Remaining Administrative State

Pending-Issue reconciliation remains required because the recorded GitHub integration attempt returned `403 Resource not accessible by integration`. This does not block Task 4 technical approval or the Task 5 handoff.
