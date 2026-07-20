# Subagent Workflow

## 목적

하나 이상의 하위 에이전트에 작업을 위임할 때마다 이 워크플로를 사용한다. GitHub Issue는 외부 작업 추적을 제공하고, `ai/work-logs/issue-{number}/`는 지속적인 워크플로 진행, 실행 증거, 복구 컨텍스트를 제공한다.

Orchestrator는 issue 생성, 배정, 조정, GitHub Issue 갱신, 최종 issue 상태를 소유한다. Worker는 역할별 작업 로그만 소유한다. Main Dev Agent는 최종 일관성과 완료 결정에 계속 책임을 진다.

## 필수 routing gate

Orchestrator가 issue를 만들거나 하위 에이전트를 배정하기 전에 `ai/document-routing.md`를 따른다.

1. 필수 routing gate를 실행한다.
2. 다음 결과 중 하나를 기록한다.
   - `Owning feature: specs/{feature}`
   - `Owning feature: none`
3. 작업이 feature-owned이면 주제별 planning, implementation, verification, review 또는 규범 문서 작업을 배정하기 전에 `specs/{feature}/spec.md`를 읽는다.
4. 소유 기능 결과, routing 이유 및 이미 읽은 파일을 각 worker에게 전달한다.

Worker는 소유권을 추측하거나 필수 기능 명세를 건너뛰어서는 안 된다. 배정에 라우팅 결과가 없으면 worker는 중단하고 Orchestrator에게 요청해야 한다.

## 필수 배정 흐름

Orchestrator는 다음 순서를 따른다.

1. 작업을 routing하고 소유권을 기록한다.
2. 공유 목적과 수용 기준을 갖는 일관되고 독립적으로 종료 가능한 작업 항목마다 하나의 Issue 경계를 정의한다. 여러 하위 에이전트 또는 역할이 해당 Issue 아래에서 작업할 수 있다. 독립적으로 수용하고 종료할 수 있는 범위만 분할한다.
3. `ai/github-issue-template.md`를 사용하여 각 작업 항목의 GitHub Issue를 생성한다.
4. `ai/work-logs/issue-{number}/README.md`, 배정된 역할 로그 및 `ai/work-logs/index.md`를 초기화한다.
5. 아래 필수 field와 함께 worker를 지정하고 배정한다.
6. 증분 worker 로그를 issue 요약 및 GitHub Issue 댓글에 조정한다.
7. 복구 기록에서 pause, blocker 및 resume을 관리한다.
8. 필수 증거가 준비되면 독립 검토를 배정하고 `status: in_review`를 기록한다.
9. `ai/issue-completion-checklist.md`의 pre-QA 섹션을 완료한다.
10. `ai/qa-gate.md`를 실행하고 `implementation_status`를 기록한다. `PASS`이면 Issue 요약 및 완료된 역할 로그의 워크플로 `status: done`을 설정한다.
11. `ai/done-claim-template.md`에서 done claim을 생성한다.
12. `ai/issue-completion-checklist.md`의 closure 섹션을 완료한 후 모든 closure 조건이 통과할 때만 Issue를 종료한다.

상세 수명 주기, 상태, 엄격한 fallback 규칙은 `ai/github-issue-planning.md`를 사용한다.

## 필수 handoff field

모든 하위 에이전트 handoff에는 다음이 포함되어야 한다.

- `tracking_status`와 `issue` 및 `issue_url`, 또는 완전한 `pending_issue` fallback metadata;
- Phase 2B skill 또는 handoff 재사용이 적용될 때 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands` 및 `github_reconciliation_status`;
- 현재 route ID, 작업 phase, `owning_feature`, context 상태, routing 이유 및 이미 읽은 route-selected 파일;
- 고유한 activated trigger, 전체 정식 load-trigger 매핑과 함께 계속 deferred된 문서, 현재 include/deferred path 및 re-route trigger;
- route-selected 파일 및 이 작업에 필요한 phase-gated 파일의 Markdown 문서 link;
- 사용 가능한 경우 GitHub Issue, issue 요약 및 관련 이전 역할 로그 또는 결정의 context link;
- 배정된 역할, in-scope 작업 및 out-of-scope 경계;
- 이미 내린 결정, 열린 질문, 남은 작업 및 남은 verification/completion 증거;
- work-log path 및 현재 워크플로 `status`; 그리고
- handoff 및 검토에 필요한 수용 기준과 증거.

Issue 기반 위임은 자체 일관된 번호, 정확한 저장소 Issue URL, 요약, 역할 ref로 `activeIssue`를 설정한다. 이후 `activatedTriggers`의 일치하는 기준 trigger와 정확한 typed scope를 사용해 해당 Issue의 `README.md`와 배정 worker에 필요한 역할 로그만 opt-in한다. URL에는 trailing slash, query, fragment, credentials, alternate host, port, scheme가 없어야 한다. Non-Issue handoff는 `activeIssue: null`을 사용하며 work-log scope나 재사용 가능 ref를 갖지 않는다. 활성화 없는 기준 적격성은 scope를 승인하지 않는다. 외부, 미목록, subtree, direct-children, descendant, 제외된 재사용 scope는 `BLOCKED`를 포함한 모든 상태에서 유효하지 않다. 과거 Issue 필드는 활성 identity의 별칭이 아니라 provenance다. 이전 역할 로그 주장은 기준 소유 문서와 대조한다.

작업이 phase 또는 활동을 바꾸면 계속하기 전에 다시 라우팅한다. READY와 PARTIAL handoff는 선택한 닫힌 활동에 필수인 모든 trigger를 활성화하고 base와 activated-trigger 문서를 읽는다. 누락으로 기록할 수 있는 것은 BLOCKED뿐이다. 워크플로 재탐색도 최소 하나의 닫힌 주제를 선택하고 그 주제의 정확한 문서만 materialize한다. 모든 읽기는 범위 안에 있고 어떤 읽기도 deferred로 남지 않으며, 활성화 문서 또는 opt-in 선택은 정확한 materialized 범위를 사용한다. READY와 PARTIAL은 모든 활성 Issue ref를 포함해 materialized opt-in 경로를 모두 읽는다. BLOCKED도 기준 trigger 배열은 보존하지만 범위를 넓히거나 외부 activated scope를 사용할 수 없다. 소유 기능이 없는 기능 필수 경로는 배정해서는 안 된다. 하위 에이전트 완료 보고서는 검증 또는 완료 gate를 대체하지 않는다.

## 단계별 handoff

기능 명세 파일은 필요한 phase에서 사용한다.

- Specification Agent: 요구 사항을 작성하거나 변경하기 전에 `spec.md`를 읽는다.
- Implementation Agent: implementation planning 또는 execution 전에 `spec.md`, 그다음 `plan.md`를 읽는다.
- Test Agent 및 API Verification Agent: execution 또는 verification handoff 전에 `spec.md`, 그다음 `tasks.md`를 읽는다.
- Documentation Agent: feature-owned 규범 문서는 먼저 `spec.md`, 그다음 `ai/document-routing.md`가 선택한 owner 문서를 읽는다.
- Review Agent: routing, 필수 phase-gated 읽기, 수용 기준, 검증 증거 및 필요한 문서 갱신을 확인한다. 지원되지 않는 완료 주장을 차단한다.

## 작업 로그 규칙

Worker는 `ai/work-log-template.md`에서 배정된 `{role}.md`를 초기화 또는 갱신하고, 의미 있는 작업·결정·명령 결과·검증 시도·차단 뒤에는 메타데이터를 최신으로 유지한다. `tracking_status`는 Issue 가용성만, `status`는 워크플로 진행만 기록한다. Worker는 실패 증거를 보존하고 정확한 복구 지점을 보고해야 한다.

Orchestrator는 issue 요약, `ai/work-logs/index.md`, GitHub Issue 댓글을 역할 로그와 일치하게 유지한다. Worker는 배정된 역할에 `handoff_needed`, `blocked`, `done`을 제안할 수 있지만 최종 issue 상태를 설정하거나 issue를 닫는 것은 Orchestrator뿐이다.

재개 시 변경 전에 issue 디렉터리의 `README.md`와 최신 관련 역할 로그를 읽는다. 역할 범위가 변하지 않았으면 기존 역할 로그에 이어 쓴다.

재사용 가능한 컨텍스트가 있으면 저장소 컨텍스트를 다시 탐색하기 전에 `ai/agent-handoff.json`, `ai/skill-catalog.json`, 참조된 `ai/workflow-cache.json` 레코드에서 재개한다.

검증 완전성 또는 작업/변경 적용 가능성이 범위에 있으면 handoff는 `ai/verification-gates.md`, `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`를 참조해야 한다. handoff는 변경 유형별 `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL` 매핑 증거를 보존해야 한다. 제품 명령은 Phase 2C 정적/helper gate에서 NOT RUN으로 유지한다.

## 일시 중지, 차단 및 재개

worker가 일시 중지하거나 차단을 보고하기 전에 역할 로그는 다음을 명시해야 한다.

- 현재 상태 및 도달한 정확한 지점;
- 지금까지의 결정 및 변경 파일;
- 실패를 포함한 명령 및 검증 결과;
- 담당 owner와 blocker; 그리고
- 다음 역할, 필수 읽기 자료의 Markdown link, issue 요약과 관련 역할 로그의 context link, 남은 작업 및 필수 증거.

그다음 Orchestrator는 issue 요약, 색인, GitHub Issue 댓글을 갱신한다. 재개한 worker는 계속하기 전에 이 복구 레코드를 읽는다.

## `pending_issue` 예외

실제 시도 뒤 GitHub Issue 생성이 불가능하면 Orchestrator는 정확히 하나의 의도된 향후 Issue 경계에 `ai/work-logs/no-issue/{work-key}/`를 사용할 수 있다. Issue 요약과 모든 역할 로그는 `issue: pending`, `tracking_status: pending_issue`, 실제 워크플로 `status`, `reconciliation_required: true`를 사용한다. `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `migration_history`, 모든 일반 handoff 증거를 기록해야 한다.

완전한 fallback은 `implementation_status: PASS`로 구현 QA를 통과할 수 있지만, 제한 없는 전체 `DONE`, issue 기반 주장, 조정 완료 또는 Issue 종료를 뒷받침할 수는 없다. 누락되었거나 유효하지 않은 fallback 메타데이터, 역할 로그 또는 검증 증거는 QA 차단 요소로 남는다.

Orchestrator는 이후 하나의 의도된 Issue를 만들고 전체 디렉터리를 `ai/work-logs/issue-{number}/`로 이동하며 이전 경로를 `migration_history`에 보존하고 모든 메타데이터와 색인을 갱신한 뒤 GitHub에 migration 요약을 게시해야 한다. 이전 디렉터리를 링크하거나 일부 파일만 복사하는 것은 충분하지 않다.

## 에이전트 역할

### Main Dev Agent

- 최종 일관성 검토를 수행한다.
- 코드와 문서의 일치를 확인한다.
- 증거에 따라 완료 결정을 승인하거나 거부한다.

### Orchestrator Agent

- 작업을 라우팅하고 응집되며 독립적으로 종료 가능한 Issue 경계를 정의한다.
- GitHub Issue를 생성하고 배정한다.
- issue 요약과 색인을 초기화·조정·갱신한다.
- 일시 중지, 차단, 재개 배정을 관리한다.
- 증거 검토 뒤 최종 issue 상태를 설정하고 issue를 종료한다.

### Specification Agent

- 명세를 초안 작성하거나 갱신한다.
- 수락 기준과 미해결 질문을 명확히 한다.
- 요구사항과 문서의 충돌을 기록한다.

### Implementation Agent

- 배정된 범위만 구현한다.
- 문서화된 아키텍처를 따른다.
- 역할 로그에 결정, 변경 파일, 명령, 증거를 기록한다.

### Test Agent

- 배정에 따라 단위, 통합, 회귀 test를 작성하고 실행한다.
- test 명령, 결과, 실패, 남은 공백을 기록한다.

### API Verification Agent

- API 검증이 필요할 때 server와 실제 HTTP 요청을 실행한다.
- 상태 코드, 응답 본문, 예상하지 못한 500 응답, server 로그를 검증한다.
- 역할 로그에 정확한 증거를 기록한다.

### Bug Hunter Agent

- edge case, 권한, 검증, 회귀, race condition을 조사한다.
- 재현 가능한 발견 사항과 증거를 기록한다.

### Documentation Agent

- 배정된 docs, specs, decisions, ADR을 갱신한다.
- 완료 보고에 필요한 근거와 링크를 기록한다.

### Review Agent

- 라우팅, 범위, 변경 파일, 수락 기준, 증거, QA 요구사항을 독립적으로 확인한다.
- 증거가 누락되었거나 일관되지 않거나 모순되면 최종 상태를 차단한다.

## 증거 규칙

- 모든 의미 있는 명령과 그 결과를 역할 로그에 기록한다.
- 실패한 검증 시도나 해결되지 않은 차단 요소를 숨기지 않는다.
- 관련 명령 또는 요청을 실제로 실행하지 않았다면 test 또는 API 검증 통과를 주장하지 않는다.
- Main Dev Agent와 Orchestrator는 issue 및 저장소 QA 규칙이 요구하는 증거 없이 완료를 거부해야 한다.
- 완료 순서를 정확히 따른다: 검토/증거 준비 -> QA 전 checklist -> QA gate -> done claim -> 종료 checklist 및 Issue 종료.
