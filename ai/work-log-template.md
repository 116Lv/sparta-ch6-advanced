# Work Log Template

Use these copy-ready templates for issue-scoped work logs. Keep the YAML field names exactly as shown so the index and future automation can read them consistently.

- Set `tracking_status` to exactly `issue_backed` or `pending_issue`.
- Set workflow `status` to exactly `planned`, `in_progress`, `handoff_needed`, `blocked`, `in_review`, or `done`.
- Set `owning_feature` to either `specs/{feature}` or `none`. In each YAML template, replace the example value with `"none"` when no feature owns the work.

## Issue Summary Template

Create `ai/work-logs/issue-{number}/README.md` once per GitHub Issue.

```md
---
issue: <number>
issue_url: <GitHub issue URL>
tracking_status: issue_backed
status: planned
owning_feature: "specs/{feature}" # Allowed: "specs/{feature}" or "none"; choose one.
current_owner: orchestrator
started_at: <ISO-8601 timestamp>
ended_at:
last_updated: <ISO-8601 timestamp>
branch: <branch name>
related_files: []
changed_files: []
commands_run: []
tests_run: []
blockers: []
skill_ids: []
handoff_state_ref:
reusable_context_refs: []
not_run_project_commands: []
github_reconciliation_status:
reconciliation_required: false
issue_creation_attempted_at:
issue_creation_failure_reason:
expected_issue_scope:
migration_history: []
---

# Issue Summary

## Recovery Summary

<The issue purpose, current status, and exact next recovery step.>

## Routing Outcome

- Owning feature: `specs/{feature}` or `none`
- Routing reason: <reason>
- Routing files read:
  - `<path>`

## Agent Logs

- [<Role>](<role>.md): <status>

## Current State

<What is complete, active, paused, or blocked.>

## Decisions

- <Decision and rationale>

## Verification Evidence

- <Evidence linked to acceptance criteria, or `Not run` with the reason.>

## Blockers

- <Blocker and owner, or `None`>

## Next Handoff

- Next role: <role-name>
- Required reading:
  - [<Document title>](<relative-path>)
- Context links:
  - [<Relevant role log>](<role>.md)
- Remaining work: <work to continue>
- Evidence required: <evidence required before the next handoff or review>
```

## Role Log Template

Create `ai/work-logs/issue-{number}/{role}.md` for each dispatched role. Resume by appending a dated update to the existing role log unless the role scope has changed.

```md
---
issue: <number>
issue_url: <GitHub issue URL>
agent: <role-name>
tracking_status: issue_backed
status: in_progress
owning_feature: "specs/{feature}" # Allowed: "specs/{feature}" or "none"; choose one.
current_owner: <role-name>
started_at: <ISO-8601 timestamp>
ended_at:
last_updated: <ISO-8601 timestamp>
branch: <branch name>
related_files: []
changed_files: []
commands_run: []
tests_run: []
blockers: []
skill_ids: []
handoff_state_ref:
reusable_context_refs: []
not_run_project_commands: []
github_reconciliation_status:
reconciliation_required: false
issue_creation_attempted_at:
issue_creation_failure_reason:
expected_issue_scope:
migration_history: []
---

# Summary

<Assigned scope and current result.>

# Work Done

- <Meaningful action or decision>

# Current State

<Current progress, pause point, or blocker.>

# Decisions

- <Decision and rationale>

# Verification Evidence

- Command: `<command>`
- Result: <PASS, FAIL, NOT RUN, or observed output>

# Blockers

- <Blocker and owner, or `None`>

# Next Handoff

- Next role: <role-name>
- Required reading:
  - [<Document title>](<relative-path>)
- Context links:
  - [Issue summary](README.md)
  - [<Relevant prior role log>](<role>.md)
- Remaining work: <work to continue>
- Evidence required: <evidence required before the next handoff or review>
```

## `pending_issue` Variation

Only the Orchestrator may authorize this variation after a GitHub Issue creation attempt fails. Store it at `ai/work-logs/no-issue/{work-key}/`, with exactly one intended future Issue boundary. Set `issue: pending`, leave `issue_url:` empty, set `tracking_status: pending_issue`, keep `status` at the actual workflow state, and set `reconciliation_required: true`. Keep every normal metadata field and every recovery section unchanged.

Both temporary records must include the following explicit metadata. The `issue_creation_*` fields preserve the creation failure as recovery evidence even after the directory migrates to `issue-{number}`.

### Pending Issue Summary Metadata

```md
---
issue: pending
issue_url:
tracking_status: pending_issue
status: planned
owning_feature: "specs/{feature}" # Allowed: "specs/{feature}" or "none"; choose one.
current_owner: orchestrator
started_at: <ISO-8601 timestamp>
ended_at:
last_updated: <ISO-8601 timestamp>
branch: <branch name>
related_files: []
changed_files: []
commands_run: []
tests_run: []
blockers: []
skill_ids: []
handoff_state_ref:
reusable_context_refs: []
not_run_project_commands: []
github_reconciliation_status:
reconciliation_required: true
issue_creation_attempted_at: <ISO-8601 timestamp>
issue_creation_failure_reason: <authentication, authorization, outage, or network failure>
expected_issue_scope: <the one cohesive, independently closable work item the future GitHub Issue will track>
migration_history: []
---
```

Use the **Issue Summary Template** recovery sections without removing or renaming any section.

### Pending Role Log Metadata

```md
---
issue: pending
issue_url:
agent: <role-name>
tracking_status: pending_issue
status: in_progress
owning_feature: "specs/{feature}" # Allowed: "specs/{feature}" or "none"; choose one.
current_owner: <role-name or orchestrator after handoff>
started_at: <ISO-8601 timestamp>
ended_at:
last_updated: <ISO-8601 timestamp>
branch: <branch name>
related_files: []
changed_files: []
commands_run: []
tests_run: []
blockers: []
skill_ids: []
handoff_state_ref:
reusable_context_refs: []
not_run_project_commands: []
github_reconciliation_status:
reconciliation_required: true
issue_creation_attempted_at: <ISO-8601 timestamp>
issue_creation_failure_reason: <authentication, authorization, outage, or network failure>
expected_issue_scope: <the one cohesive, independently closable work item the future GitHub Issue will track>
migration_history: []
---
```

Use the **Role Log Template** sections without removing or renaming any section.

A fallback that finishes implementation may set workflow `status: done` while retaining `tracking_status: pending_issue`. This combination may support `implementation_status: PASS`, but it is not issue-backed and cannot support an unqualified overall `DONE` or Issue closure.

Phase 2C work logs must include links to `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh` whenever verification completeness or task/change applicability is evaluated. Record the selected change type and the `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mapping. Product commands remain NOT RUN for static/helper gates.

During reconciliation, move the full `no-issue/{work-key}/` directory to `issue-{number}/`. In every migrated record, set `tracking_status: issue_backed`, preserve workflow `status`, and replace `migration_history: []` with a structured entry:

```yaml
migration_history:
  - moved_at: <ISO-8601 timestamp>
    from: ai/work-logs/no-issue/{work-key}/
    to: ai/work-logs/issue-{number}/
```
