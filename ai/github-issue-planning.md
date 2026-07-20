# GitHub Issue 계획

## 목적

dispatch된 agent 작업의 외부 task-tracking record로 GitHub Issue를 사용한다. 내구성 있는 execution 및 recovery record로 저장소 work log를 사용한다. 이 문서는 dispatch 전, 중, 후 Orchestrator의 필수 흐름을 정의한다.

`ai/document-routing.md`는 계속 첫 gate다. issue는 feature specification, owner document, ADR, verification evidence, QA gate를 대체하지 않는다.

## 소유권

Orchestrator는 모든 GitHub Issue state를 소유한다.

- 작업을 routing하고 owning feature outcome 기록
- 작업을 dispatch 가능한 issue로 분할
- issue 생성, 할당, comment, reconciliation, close, required evidence 검토 후 final issue/work-log status 설정

worker는 자신의 role-specific log만 소유한다. worker는 progress, blocker, decision, evidence를 보고할 수 있지만 issue를 생성, 할당, reconcile, close하거나 final status를 설정해서는 안 된다.

## 실행 흐름

1. **Route**: `ai/document-routing.md`를 실행하고 `Owning feature: specs/{feature}` 또는 `Owning feature: none`을 기록한다. feature-owned 작업은 subject-specific dispatch 전에 `specs/{feature}/spec.md`를 읽는다.
2. **Issue 경계 정의**: shared purpose와 shared acceptance criteria를 가진 cohesive하고 independently closable한 item으로 작업을 나눈다. 여러 subagent/role의 scope가 같은 closure decision에 기여하면 하나의 Issue 아래에 유지한다. 여러 agent가 참여한다는 이유만으로 분할하지 말고 각 scope를 독립적으로 accept하고 close할 수 있을 때만 분할한다.
3. **GitHub Issue 생성**: Orchestrator는 [github-issue-template.md](github-issue-template.md)를 사용해 cohesive work item마다 Issue 하나를 만든다. Issue body에는 routing outcome, required reading, acceptance criteria, required evidence, suggested role, expected work-log path가 포함되어야 한다.
4. **Issue Directory 초기화**: `ai/work-logs/issue-{number}/README.md`를 만들고 `ai/work-logs/index.md`에 entry를 추가하며 각 assigned role log를 [work-log-template.md](work-log-template.md)에서 초기화한다. dispatch 전 `issue`, `issue_url`, `tracking_status: issue_backed`, workflow `status`, `owning_feature`, `current_owner`, `last_updated`를 설정한다.
5. **Dispatch**: worker에게 issue number, issue URL, work-log path, routing outcome, 이미 읽은 file과 읽을 phase-gated file 링크, scope, open question, required evidence를 준다. issue summary와 relevant prior role log의 context link를 포함한다. Orchestrator는 assignment를 issue와 issue summary에 기록한다.
6. **점진적 업데이트**: worker는 meaningful work, decision, command result, verification attempt, blocker 후 자신의 role log만 업데이트한다. Orchestrator는 issue summary, index, GitHub Issue comment를 worker log와 정렬한다.
7. **Pause, Block 또는 Resume**: pause 전 role-log status를 `handoff_needed` 또는 `blocked`로 설정하고 exact recovery point와 next handoff를 기록하여 Orchestrator에 알린다. Orchestrator는 issue summary를 업데이트하고 GitHub Issue에 comment하며 다음 role을 assign/resume한다. resume 시 변경 전 issue summary와 latest role log를 읽는다.
8. **Review 및 Evidence 준비**: Review Agent는 routing, scope, changed file, required evidence, unresolved blocker, Issue acceptance criteria와의 일관성을 검사한다. review evidence를 role log에 기록하고 completion sequence 준비가 되면 Issue summary를 `status: in_review`로 설정한다.
9. **Pre-QA Checklist**: `ai/issue-completion-checklist.md`의 pre-QA section을 완료한다. 이 단계는 evidence readiness를 검증하며 done claim을 요구해서는 안 된다.
10. **QA Gate**: `ai/qa-gate.md`를 실행하고 actual verification evidence의 `implementation_status`를 기록한다. `PASS`일 때 done claim을 만들기 전에 Issue summary와 완료 role log를 workflow `status: done`으로 설정한다.
11. **Done Claim**: QA 후 `ai/done-claim-template.md`에서 completion report를 만든다.
12. **Closure Checklist 및 Issue Closure**: done claim이 존재한 후 `ai/issue-completion-checklist.md`의 closure section을 완료한다. Orchestrator는 모든 role log와 review evidence를 reconcile하고 evidence summary를 Issue에 comment하며 모든 closure condition이 통과할 때만 Issue를 닫는다.

## Issue 계획 규칙

- 작업이 추적 가능한 unit으로 분할될 때는 dispatch 전에 Issue를 만든다.
- 하나의 Issue는 shared purpose와 acceptance criteria를 가진 하나의 cohesive하고 independently closable한 work item이다.
- 여러 subagent와 role은 같은 Issue에서 작업할 수 있으며 별도의 role log를 유지해야 한다.
- 여러 agent가 참여한다는 이유만으로 분할하지 않고 scope를 독립적으로 accept/close할 수 있을 때 별도 Issue로 나눈다.
- Issue directory마다 Issue number 하나를 사용한다. 관련 없는 작업을 한 directory 아래에 묶지 않는다.
- issue 시작, pause, block, resume, final status 도달 시마다 `ai/work-logs/index.md`를 최신으로 유지한다.
- `done` status는 role이 assigned work를 완료했음을 뜻한다. issue closure를 허가하지 않는다. Orchestrator만 final issue status를 설정하고 issue를 닫을 수 있다.
- issue body와 applicable repository verification rule이 요구한 evidence 없이 `done`을 설정하거나 issue를 닫지 않는다.

## Tracking 및 Workflow Status 값

tracking availability와 workflow progress는 직교한다. 모든 Issue summary와 role log에서 두 field를 사용한다.

| `tracking_status` | 의미 | Owner |
|---|---|---|
| `issue_backed` | 실제 GitHub Issue number와 URL이 작업을 뒷받침한다. | Orchestrator |
| `pending_issue` | Issue 생성 실패 후 문서화된 temporary fallback이 있다. | Orchestrator |

| `status` | 의미 | Owner |
|---|---|---|
| `planned` | 작업은 정의되었지만 assigned/dispatched되지 않았다. | Orchestrator |
| `in_progress` | assigned 작업이 능동적으로 수행 중이다. | 자신의 log에는 assigned role, issue summary에는 Orchestrator |
| `handoff_needed` | 정의된 next role 또는 recovery point와 함께 작업이 pause되었다. | assigned role이 제안, Orchestrator가 확인 |
| `blocked` | 기록된 blocker가 해소될 때까지 progress를 계속할 수 없다. | assigned role이 제안, Orchestrator가 확인 |
| `in_review` | 작업이 독립 review 중이거나 QA 준비 review evidence가 있다. | Orchestrator |
| `done` | assigned work 또는 issue가 정의된 criteria를 충족했다. | Orchestrator가 final issue status 설정 |

## 엄격한 `pending_issue` Fallback

`tracking_status: pending_issue`는 GitHub Issue 생성이 시도되었으나 authentication, authorization, GitHub outage, network failure 같은 external failure로 사용할 수 없을 때만 사용한다. Orchestrator는 temporary Issue summary와 모든 role log에 `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `migration_history`, `reconciliation_required: true`를 설정해야 한다.

temporary directory는 정확히 `ai/work-logs/no-issue/{work-key}/`여야 한다. `{work-key}`는 stable하고 descriptive해야 한다. directory는 의도된 future Issue boundary 하나만 보존한다. Issue summary와 role log는 `issue: pending`, 빈 `issue_url`, `tracking_status: pending_issue`, 실제 workflow `status`를 사용한다. date-only Issue directory를 만들거나 Issue number를 발명하거나 `status`를 overload하거나 convenience를 위해 fallback을 사용하지 않는다.

유효한 metadata, 모든 required role log, 모든 applicable verification evidence를 갖춘 complete fallback은 `implementation_status: PASS`로 implementation QA를 통과할 수 있다. `tracking_status`가 `pending_issue`인 동안 unqualified overall `DONE`, issue-backed 작업 주장, reconciliation completion, GitHub Issue closure는 계속 차단된다. 누락되었거나 invalid한 fallback metadata, role log, evidence는 implementation-QA blocker다.

GitHub access가 복구되면 Orchestrator는 다음을 수행해야 한다.

1. original scope와 current evidence에서 GitHub Issue를 만든다.
2. history를 버리지 않고 temporary directory 전체를 `ai/work-logs/issue-{number}/`로 옮긴다. old directory 연결이나 selected file 복사는 reconciliation이 아니다.
3. Issue summary와 모든 role log의 `migration_history`에 move timestamp, 이전 `no-issue` path, final `issue-{number}` path를 추가한다.
4. Issue summary와 모든 role log의 `issue`, `issue_url`, `tracking_status: issue_backed`, `last_updated`, `reconciliation_required: false`를 업데이트한다. workflow `status`와 Issue-creation attempt field는 보존한다.
5. `no-issue` index entry를 `issue-{number}` entry로 교체하고 temporary path를 migration record에 보존한다.
6. migrated log directory를 연결하고 Issue 생성 전 완료된 작업을 요약하는 GitHub Issue comment를 추가한다.

여섯 단계가 모두 완료될 때까지 fallback은 완전히 reconciled되지 않는다. 그때까지 작업은 issue-backed 또는 closed로 보고해서는 안 된다.

## 필수 Dispatch Field

모든 dispatch에는 다음이 포함되어야 한다.

- `tracking_status`와 `issue`, `issue_url`, 또는 complete `pending_issue` fallback metadata
- `owning_feature`와 읽은 routing file
- required 및 phase-gated reading의 Markdown document link
- issue summary와 relevant prior role log의 context link
- role, scope, acceptance criteria, out-of-scope boundary
- 이미 내린 decision과 open question
- work-log path 및 current workflow `status`
- handoff 및 review에 필요한 evidence
