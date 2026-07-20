# 작업 로그 템플릿

Issue 범위 작업 로그에는 이 즉시 복사 가능한 템플릿을 사용한다. 색인과 향후 자동화가 일관되게 읽을 수 있도록 YAML 필드 이름은 표시된 그대로 유지한다.

- `tracking_status`를 정확히 `issue_backed` 또는 `pending_issue`로 설정한다.
- 워크플로 `status`를 정확히 `planned`, `in_progress`, `handoff_needed`, `blocked`, `in_review`, 또는 `done`으로 설정한다.
- `owning_feature`를 `specs/{feature}` 또는 `none`으로 설정한다. 작업을 소유하는 기능이 없으면 각 YAML 템플릿의 예시 값을 `"none"`으로 바꾼다.

## Issue 요약 템플릿

GitHub Issue마다 `ai/work-logs/issue-{number}/README.md`를 한 번 생성한다.

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

## 역할 로그 템플릿

배정된 각 역할에 `ai/work-logs/issue-{number}/{role}.md`를 만든다. 역할 범위가 바뀌지 않았다면 기존 역할 로그에 날짜가 있는 갱신을 추가하여 재개한다.

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

GitHub Issue 생성 시도가 실패한 뒤에는 Orchestrator만 이 변형을 승인할 수 있다. 정확히 하나의 의도된 향후 Issue 경계와 함께 `ai/work-logs/no-issue/{work-key}/`에 저장한다. `issue: pending`을 설정하고 `issue_url:`은 비워 두며 `tracking_status: pending_issue`를 설정하고 `status`는 실제 워크플로 상태로 유지하며 `reconciliation_required: true`를 설정한다. 모든 일반 메타데이터 필드와 모든 복구 섹션을 변경하지 않는다.

두 임시 레코드에는 다음 명시적 메타데이터가 모두 필요하다. `issue_creation_*` 필드는 디렉터리가 `issue-{number}`로 이동한 뒤에도 생성 실패를 복구 증거로 보존한다.

### 대기 중인 Issue 요약 메타데이터

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

어떤 섹션도 제거하거나 이름을 바꾸지 않고 **Issue Summary Template** 복구 섹션을 사용한다.

### 대기 중인 역할 로그 메타데이터

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

어떤 섹션도 제거하거나 이름을 바꾸지 않고 **Role Log Template** 섹션을 사용한다.

구현을 마친 fallback은 `tracking_status: pending_issue`를 유지한 채 워크플로 `status: done`을 설정할 수 있다. 이 조합은 `implementation_status: PASS`를 지원할 수 있지만 issue 기반이 아니며 제한 없는 전체 `DONE` 또는 Issue 종료를 지원할 수 없다.

Phase 2C 작업 로그에는 검증 완전성 또는 작업/변경 적용 가능성을 평가할 때마다 `ai/verification-gates.md`, `ai/verification-policy.json`, `scripts/ai/verification-gate.sh` 링크를 포함해야 한다. 선택한 변경 유형과 `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL` 매핑을 기록한다. 제품 명령은 정적/helper gate에서 NOT RUN으로 유지한다.

조정 중에는 전체 `no-issue/{work-key}/` 디렉터리를 `issue-{number}/`로 이동한다. 이동된 모든 레코드에서 `tracking_status: issue_backed`를 설정하고 워크플로 `status`를 보존하며 `migration_history: []`를 구조화된 항목으로 대체한다.

```yaml
migration_history:
  - moved_at: <ISO-8601 timestamp>
    from: ai/work-logs/no-issue/{work-key}/
    to: ai/work-logs/issue-{number}/
```
