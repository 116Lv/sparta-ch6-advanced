---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: task-5-resolution-brief
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: task-5-implementation-agent
started_at: 2026-07-11T00:00:00Z
ended_at: 2026-07-11T00:00:00Z
last_updated: 2026-07-13T09:32:29+09:00
related_files:
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-10-ai-workflow-phase-1b-1-implementation.md
  - ai/work-logs/issue-4/task-4-registry-semantics-brief.md
changed_files:
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/fixtures/phase-1b/parameters/README.md
  - ai/fixtures/phase-1b/parameters/duplicate-key.json
  - ai/fixtures/phase-1b/prerequisites/README.md
  - ai/fixtures/phase-1b/prerequisites/ordered.json
  - ai/work-logs/issue-4/task-5-resolution-brief.md
  - ai/work-logs/issue-4/task-5-implementation-agent.md
commands_run:
  - C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
  - C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh
tests_run:
  - "RED: helper contract exit 1; 42 tests ran; resolver cases failed because resolve_command was absent."
  - "RED: helper contract exit 1; 43 tests ran; canonical validation was incorrectly bypassed by malformed command-id policy handling."
  - "RED: helper contract exit 1; 43 tests ran; a neutral filename inside secrets/ was accepted."
  - "RED: helper contract exit 1; 45 tests ran; extra resolve arguments escaped as argparse SystemExit 2."
  - "GREEN: helper contract exit 0; 45 tests ran in 5.253s; OK (skipped=3)."
  - "Runtime-preflight regression: exit 0; PASS: runtime preflight contract."
blockers: []
historical_blockers:
  - "Symlink-capable runtime verification remains required: the parameter-path symlink test and the existing working-directory/wrapper symlink tests are skipped in this Windows sandbox."
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

# Task 5 Resolution Brief

## Scope

Implement only Phase 1B-1 pure command resolution: schema and semantic validation, exact command lookup, configuration and classification mapping, closed parameter-file handling, whole-token substitution, deterministic prerequisite blocking, and schema-valid `RESOLVE` output. The resolver must not execute a project command, import or invoke `subprocess`, create `.ai-runs`, record run evidence, or add the future public `command-runner.sh`.

## Resolution Order

The implementation follows the Phase 1B specification order and stops at the first outcome: current helper preflight for supported gateway invocation; canonical state and registry validation; semantic validation; command ID lookup; status and classification; parameters; substitution; prerequisites; final containment; structured output. Tests may use the pure internal seam without state recording; this does not weaken public preflight.

## TDD Boundary

The owned helper tests and fixtures are added before resolver production code. Allowed verification is limited to the helper contract launcher and runtime-preflight regression. Gradle, product tests, application/server, Docker, HTTP/API, database, migration, seed, and infrastructure commands remain not run.

## Result

The pure seam validates canonical state and registry before command-ID policy, returns schema-valid `RESOLVE` envelopes with fixed exit mapping, preserves argv as a list, and blocks rather than executes. The supported CLI reruns non-recording current preflight before calling the seam and writes only the requested structured output.
