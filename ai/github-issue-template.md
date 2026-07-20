# GitHub Issue Template

Orchestrator가 배정 가능한 issue를 만들 때 이 본문을 복사한다. 배정 전에 모든 placeholder를 대체한다.

```md
# Task

<Short, action-oriented issue title>

## 목적

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

승인된 `pending_issue` fallback에는 `local_log_path: ai/work-logs/no-issue/{work-key}/`를 사용하고 `reconciliation_required: true`를 설정하며 GitHub 생성 실패를 **Open Questions**에 명시한다. Orchestrator가 실패한 생성 시도를 기록하지 않았다면 이 변형을 사용하지 않는다.
