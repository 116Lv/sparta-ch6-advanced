# GitHub Issue Template

Copy this body when the Orchestrator creates a dispatchable issue. Replace every placeholder before dispatch.

```md
# Task

<Short, action-oriented issue title>

## Purpose

<Why this dispatchable unit exists and the expected outcome.>

## Owning Feature

- owning_feature: `specs/{feature}` or `none`
- routing_files_read:
  - `<path>`
- routing_reason: <Why this feature owns the work, or why no feature owns it.>

## Required Reading

- `<path>`

## Scope

### In Scope

- <Included work>

### Out Of Scope

- <Excluded work>

## Acceptance Criteria

- [ ] <Observable completion condition>

## Evidence Required

- <Exact commands, review evidence, API evidence, or document checks required before final status.>

## Suggested Agent

- agent: `<role-name>`
- assignment_owner: `orchestrator`

## Work Log

- local_log_path: `ai/work-logs/issue-{number}/`
- reconciliation_required: `false`

## Open Questions

- <Question, or `None`>
```

For an approved `pending_issue` fallback, use `local_log_path: ai/work-logs/no-issue/{work-key}/`, set `reconciliation_required: true`, and state the GitHub creation failure in **Open Questions**. Do not use that variation unless the Orchestrator has recorded a failed creation attempt.
