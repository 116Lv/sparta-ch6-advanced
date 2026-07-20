# 하위 에이전트 GitHub Issue 및 작업 로그 설계

## 배경

이 저장소는 이미 에이전트 작업, 기능 명세, ADR, 검증 규칙 및 완료 주장의 기준 문서로 Markdown 문서를 사용한다. 기존 하위 에이전트 워크플로는 handoff 내용을 정의하지만, 중단·재개·위임 또는 사후 감사될 수 있는 작업을 위한 영속적 추적 시스템은 아직 정의하지 않는다.

선택된 설계는 GitHub Issues를 외부 작업 보드로, 저장소 작업 로그를 영속적인 실행 기록으로 사용한다. GitHub Issues는 "어떤 작업이 존재하고 어떤 상태인가?"에 답한다. 작업 로그는 "실제로 무슨 일이 있었고, 무엇이 바뀌었으며, 어떤 증거가 있고, 다음 에이전트는 어디서 재개해야 하는가?"에 답한다.

## 목표

- 작업을 추적 가능한 단위로 분할할 수 있을 때마다 하위 에이전트를 배정하기 전에 GitHub Issues를 생성한다.
- 각 GitHub Issue를 저장소 로컬 작업 로그에 연결한다.
- 중단된 작업을 쉽게 재개할 수 있도록 날짜가 아닌 issue 번호별로 작업 로그를 저장한다.
- 나중의 자동화에 충분히 구조화되어 있고 사람이 읽기에도 충분히 읽기 쉬운 로그를 만든다.
- 기존 document-routing 및 feature-ownership 규칙을 보존한다.

## 비목표

- `specs/{feature}` 문서를 GitHub Issues로 대체하지 않는다.
- GitHub Issues를 실행 증거의 유일한 출처로 사용하지 않는다.
- GitHub Issues 외에 별도 외부 추적기를 요구하지 않는다.
- 하위 에이전트 작업을 배정하거나 실행하지 않는 순수 대화형 계획에는 로그를 생성하지 않는다.

## 아키텍처

워크플로에는 연결된 두 계층이 있다.

1. GitHub Issue 계층
   - 하나의 issue는 공유 목적과 공유 수용 기준을 갖는, 독립적으로 종료할 수 있는 하나의 일관된 작업 항목을 나타낸다.
   - issue 본문은 목적, 소유 기능, 필수 읽기 자료, 범위, 수용 기준, 필수 증거, 제안 에이전트 및 예상 작업 로그 경로를 기록한다.
   - 작업이 시작·일시 중지·차단·재개 또는 완료될 때 issue 댓글에 요약을 남긴다.

2. 저장소 작업 로그 계층
   - 작업 로그는 `ai/work-logs/issue-{number}/` 아래에 둔다.
   - 각 issue 디렉터리에는 issue 요약 파일과 하나 이상의 역할 로그가 있다. 여러 하위 에이전트 또는 역할이 같은 Issue 아래에 별도 로그를 남길 수 있다.
   - 로그는 구조화된 메타데이터에 YAML frontmatter를, 사람이 읽는 진행 상황에 Markdown 섹션을 사용한다.

권장 구조:

```text
ai/
  github-issue-planning.md
  github-issue-template.md
  work-log-template.md
  subagent-workflow.md
  work-logs/
    README.md
    index.md
    issue-12/
      README.md
      implementation-agent.md
      test-agent.md
      review-agent.md
```

## Issue 생성 규칙

하위 에이전트를 배정하기 전에 Main Dev Agent 또는 Orchestrator Agent는 다음을 수행해야 한다.

1. `ai/document-routing.md`를 따른다.
2. `Owning feature: specs/{feature}` 또는 `Owning feature: none`을 기록한다.
3. 작업을 일관되고 독립적으로 종료할 수 있는 GitHub Issues로 분할한다.
4. 저장소 issue 템플릿을 사용하여 각 GitHub Issue를 생성한다.
5. 배정된 하위 에이전트에게 issue 번호, 소유 기능 결과, 필수 읽기 자료, 열린 질문 및 증거 요구 사항을 전달한다.

Issue 세분성은 커밋 경계나 에이전트 수가 아니라 수용 및 종료 경계를 따른다. 구현, 테스트, API 검증, 문서화 및 검토에 서로 다른 하위 에이전트나 역할 로그를 사용하더라도 하나의 목적과 하나의 수용 기준 세트를 공유하면 범위를 하나의 Issue에 유지한다. 각 범위를 독립적으로 수용하고 종료할 수 있을 때만 별도 Issue로 분리한다.

실제 생성 시도 후 GitHub 접근을 사용할 수 없으면 Orchestrator는 작업 진행을 위해 임시 `no-issue/{work-key}/` 디렉터리를 만들 수 있다. 이 디렉터리는 정확히 하나의 의도된 미래 Issue 경계를 보존해야 하며, 생성 실패, 예상 Issue 범위 및 조정 요구 사항을 기록해야 한다. 접근이 복구되면 전체 디렉터리를 `issue-{number}/`로 이동한다. 제자리 링크만으로는 충분하지 않으며 이전 경로는 `migration_history`에 남아야 한다.

## GitHub Issue 템플릿

생성된 각 issue에는 다음 섹션을 포함해야 한다.

```md
# 작업

## 목적

## 소유 기능

- 소유 기능:
- 읽은 routing 파일:

## 필수 읽기 자료

## 범위

## 수용 기준

## 필수 증거

## 제안 에이전트

## 작업 로그

- 로컬 로그 경로:

## 열린 질문
```

## 작업 로그 규칙

작업 로그는 issue별로 그룹화한다.

```text
ai/work-logs/issue-{number}/README.md
ai/work-logs/issue-{number}/{role}.md
```

`README.md`는 issue 수준의 복구 요약이다. 사용 가능한 경우 GitHub Issue URL, 추적 상태, 워크플로 상태, 소유 기능, 현재 담당자, 마지막 갱신 시각 및 모든 역할 로그 링크를 보여 준다.

각 역할 로그는 해당 Issue에서 한 에이전트 역할의 실행 이력을 기록한다. 같은 역할이 나중에 작업을 재개하면, 범위가 새 역할 전용 로그가 필요할 정도로 바뀌지 않는 한 기존 로그에 추가해야 한다.

각 에이전트 로그에는 다음 구조화된 메타데이터를 포함해야 한다.

- `tracking_status`는 Issue 가용성을 기록하며 정확히 `issue_backed` 또는 `pending_issue`이다.
- `status`는 워크플로 진행 상황을 기록하며 정확히 `planned`, `in_progress`, `handoff_needed`, `blocked`, `in_review` 또는 `done`이다.
- `owning_feature`는 `specs/{feature}` 또는 `none` 중 하나이다.

```md
---
issue: 12
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/12
agent: implementation-agent
tracking_status: issue_backed
status: in_progress
owning_feature: specs/003-order-payment
started_at: 2026-07-09T22:00:00+09:00
ended_at:
last_updated: 2026-07-09T22:30:00+09:00
branch:
related_files: []
changed_files: []
commands_run: []
tests_run: []
blockers: []
reconciliation_required: false
issue_creation_attempted_at:
issue_creation_failure_reason:
expected_issue_scope:
migration_history: []
---
```

각 에이전트 로그에는 다음 사람이 읽을 수 있는 섹션을 포함해야 한다.

```md
# 요약

# 수행한 작업

# 현재 상태

# 결정

# 검증 증거

# 차단 요소

# 다음 handoff
```

## 갱신 수명 주기

1. Issue 생성
   - GitHub Issue가 존재한다.
   - Issue 본문에는 `Work Log: pending` 또는 예상 경로가 포함된다.

2. 하위 에이전트 시작
   - 존재하지 않으면 `ai/work-logs/issue-{number}/README.md`를 생성한다.
   - `ai/work-logs/issue-{number}/{role}.md`를 생성하거나 갱신한다.
   - issue를 `ai/work-logs/index.md`에 추가한다.
   - 로컬 로그 경로와 함께 GitHub Issue에 댓글을 남긴다.

3. 하위 에이전트 작업
   - 의미 있는 변경, 결정, 실패, 검증 시도 또는 차단 요소가 있을 때 로그를 갱신한다.
   - `last_updated`, `status`, `changed_files`, `commands_run`, `tests_run` 및 `blockers`를 최신 상태로 유지한다.

4. 작업 일시 중지 또는 차단
   - 상태를 `blocked` 또는 `handoff_needed`로 설정한다.
   - `Current State`, `Blockers` 및 `Next Handoff`를 채운다.
   - 중지 지점과 로컬 로그 링크를 요약한 GitHub Issue 댓글을 추가한다.

5. 검토 및 증거 준비 완료
   - issue 요약 상태를 `in_review`로 설정하고 독립적인 검토 증거를 기록한다.
   - 관련된 모든 역할 로그의 `Verification Evidence`, 해결되지 않은 차단 요소 및 `Next Handoff`를 채운다.

6. Pre-QA 체크리스트
   - `ai/issue-completion-checklist.md`의 pre-QA 섹션을 완료한다.
   - 이 단계에서 done claim을 요구하지 않는다. done claim은 QA 후에 만든다.

7. QA 게이트
   - `ai/qa-gate.md`를 실행하고 실제 증거의 `implementation_status`를 기록한다.
   - 완전하고 문서화된 fallback은 `tracking_status`가 `pending_issue`로 유지되더라도 `implementation_status: PASS`를 낼 수 있다.
   - 구현 QA가 통과하면 done claim을 만들기 전에 issue 요약과 완료된 역할 로그를 워크플로 `status: done`으로 설정한다.

8. Done claim
   - QA 후 `ai/done-claim-template.md`에서 보고서를 만든다.
   - `tracking_status: pending_issue`는 구현이 통과했더라도 제한 없는 전체 `DONE`, issue 기반 주장, 조정 완료 및 GitHub Issue 종료를 차단한다.

9. 종료 체크리스트 및 Issue 종료
   - done claim이 존재한 후 `ai/issue-completion-checklist.md`의 종료 섹션을 실행한다.
   - 요약, 변경 파일, 검증 증거 및 로그 경로를 담은 GitHub Issue 댓글을 추가한다.
   - issue 기반이고 조정이 완료되었으며 모든 수용 기준과 필수 증거가 충족될 때만 Issue를 종료한다.

## 통합 지점

- `ai/subagent-workflow.md`는 issue 기반 배정 및 issue 범위 작업 로그 갱신을 요구해야 한다.
- `ai/document-routing.md`는 issue 생성 전 소유권 게이트로 유지된다.
- `ai/issue-completion-checklist.md`는 pre-QA 검사를 먼저 제공하고 종료 검사는 done claim 후에만 제공해야 한다.
- `ai/qa-gate.md`는 누락되었거나 유효하지 않은 추적 메타데이터, 작업 로그 또는 검증 증거를 차단 요소로 처리하면서, 완전한 fallback이 구현 QA를 통과하도록 허용해야 한다.
- `ai/done-claim-template.md`는 추적 상태, 사용 가능한 경우 issue 데이터, 작업 로그 경로, 구현 상태 및 종료 상태를 포함해야 한다.

## 오류 처리

- issue 번호 누락: `no-issue` fallback 모드로 실행 중임이 명시되지 않았다면 중지하고 Main Dev Agent에게 issue 번호를 요청한다.
- 소유 기능 결과 누락: 주제별 작업 전에 routing 출력을 요청하고 중지한다.
- 검증 증거 누락: issue를 종료하거나 완료를 주장하지 않는다.
- GitHub 사용 불가: 생성 시도가 실패한 후 `tracking_status: pending_issue`를 설정하고, `status`를 실제 워크플로 상태로 유지하며, 완전한 fallback 메타데이터와 증거를 요구한다.
- 조정: 하나의 의도된 Issue를 만들고 전체 fallback 디렉터리를 `issue-{number}/`로 이동하며, 이전 경로를 `migration_history`에 보존한다. 링크만 사용하는 조정은 무효다.
- 중단된 작업: `ai/work-logs/issue-{number}/README.md`에서 재개한 뒤 최신 관련 에이전트 로그를 읽는다.

## 테스트 및 검토

이 설계는 문서화 및 워크플로 전용이다. 검증은 다음을 확인해야 한다.

- 필수 워크플로 문서가 존재한다.
- 템플릿에 필수 섹션이 모두 있다.
- `ai/subagent-workflow.md`가 issue 기반 배정 및 issue 범위 작업 로그를 참조한다.
- 예시 경로가 날짜가 아니라 issue 번호를 사용한다.
- 추적 가용성과 워크플로 진행이 분리되고 일관된 필드와 값을 사용한다.
- 완료가 검토/증거 준비, pre-QA 체크리스트, QA 게이트, done claim, 종료 체크리스트 및 Issue 종료 순서를 따른다.
- 완료 및 QA 문서가 routing-first, runtime, 실제 HTTP, server-log 및 work-log 증거 요구 사항을 보존한다.
