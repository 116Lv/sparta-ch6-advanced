# Issue 완료 체크리스트

이 체크리스트는 하나의 선형 sequence에 세 checkpoint를 둔다.

1. review/evidence ready -> pre-QA checklist
2. QA gate -> done claim
3. 종료 체크리스트 -> GitHub Issue 종료

`ai/qa-gate.md` 실행 전 **구현 전**, **구현 중**, **Pre-QA 준비**를 완료한다. pre-QA에서 done claim을 요구하지 않는다. QA 후 생성한다. done claim이 존재한 후에만 post-claim closure phase로 돌아간다.

## 구현 전

- [ ] `ai/document-routing.md`의 Work Route ownership gate를 완료했다.
- [ ] owning feature outcome을 `specs/{feature}` 또는 `none`으로 기록했다.
- [ ] 필요한 owner document와 feature-spec file을 읽었다.
- [ ] acceptance criteria와 verification level이 명확하다.
- [ ] open question을 해결했거나 명시적으로 기록했다.
- [ ] dispatch 전 상호 배타적인 다음 record 중 정확히 하나가 존재한다.
  - real GitHub Issue-backed dispatch와 handoff의 `tracking_status: issue_backed`, number, URL, expected work-log path
  - GitHub Issue 생성 시도 실패 후 `tracking_status: pending_issue`, actual workflow `status`, complete failure metadata, reconciliation plan을 갖는 문서화된 `no-issue/{work-key}/` fallback
- [ ] Issue 또는 fallback directory는 shared purpose/acceptance criteria를 가진 정확히 하나의 cohesive, independently closable work item을 나타낸다. 여러 참여 agent는 그 같은 boundary 아래 별도 role log를 사용한다.

## 구현 중

- [ ] 문서화된 layer/architecture rule을 따랐다.
- [ ] 필요할 때 new decision을 `decisions.md` 또는 ADR에 기록했다.
- [ ] temporary code, unapproved TODO, debug logging을 남기지 않았다.
- [ ] error handling을 숨기지 않았다.
- [ ] dispatch된 모든 agent가 meaningful work, failure, verification, blocker, handoff 후 role-specific log를 업데이트했다.
- [ ] Issue summary가 모든 관련 role log를 link하고 `tracking_status`, workflow `status`, current owner를 식별한다.

## QA 전 준비

- [ ] independent review가 완료되고 required evidence가 준비되었으며 Issue summary가 `status: in_review`를 사용한다.
- [ ] `tracking_status`와 workflow `status`는 canonical value만 사용하고 conflated되지 않는다.
- [ ] 선택한 verification level이 요구한 command, result, verification evidence를 기록했다.
- [ ] API change에는 running server에 대한 real HTTP request evidence가 포함된다.
- [ ] runtime verification이 필요할 때 unexpected 500 response를 검사해 absent였고 server log를 검토했다.
- [ ] documentation update need를 검토하고 필요한 곳에서 완료했다.
- [ ] dispatch된 모든 role log가 scope, changed file, command, evidence, blocker, next handoff 또는 completion state를 기록한다.
- [ ] `tracking_status: issue_backed`이면 real Issue number/URL, Issue summary, 모든 role log를 link한다.
- [ ] `tracking_status: pending_issue`이면 Issue summary와 모든 role log에 `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `reconciliation_required: true`, `migration_history`가 있다.

이 section이 통과한 후 `ai/qa-gate.md`를 실행하고 `implementation_status`를 기록한다. complete fallback은 `implementation_status: PASS`를 만들 수 있다. QA가 통과하면 아래로 계속하기 전에 Issue summary와 completed role log를 workflow `status: done`으로 설정하고 `ai/done-claim-template.md`에서 done claim을 만든다.

## 주장 후 종료 단계

이 phase는 QA result와 done claim이 존재한 후에만 실행한다. `tracking_status`가 `pending_issue`인 동안 `pending_issue_reconciliation`을 보고한다. issue-backed claim, reconciliation completion, unqualified overall `DONE`, GitHub Issue closure를 보고하지 않는다.

### Phase 2C 검증 게이트

- [ ] `ai/verification-gates.md`, canonical `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`를 사용했거나 reason과 함께 NOT RUN으로 명시적으로 보고했다.
- [ ] selected change type이 task/change applicability와 verification completeness를 기록한다.
- [ ] `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL` mapping이 selected change type에 일치한다.
- [ ] 별도로 supported evidence path를 통해 실행하지 않는 한 제품 명령은 계속 NOT RUN이다.

### `pending_issue` Reconciliation

work가 fallback을 사용한 경우 이 check를 완료하고, 그 외에는 not applicable로 기록한다.

- [ ] migration 중 관련 없는 scope를 merge/split하지 않고 original intended Issue boundary 하나에 real Issue를 만들었다.
- [ ] 전체 `ai/work-logs/no-issue/{work-key}/` directory를 `ai/work-logs/issue-{number}/`로 옮겼다. link-only reconciliation 또는 selected file 복사를 사용하지 않았다.
- [ ] Issue summary와 모든 role log의 `migration_history`에 prior fallback path, final Issue path, move timestamp를 보존했다.
- [ ] workflow `status`와 creation-failure history를 보존하면서 모든 migrated record의 `issue`, `issue_url`, `tracking_status: issue_backed`, `last_updated`, `reconciliation_required: false`를 업데이트했다.
- [ ] `ai/work-logs/index.md`가 fallback entry를 final path로 교체했고 GitHub Issue가 migration summary를 포함한다.

### GitHub Issue 종료

- [ ] `ai/done-claim-template.md`에서 만든 done claim이 존재하며 `implementation_status: PASS`를 기록한다.
- [ ] current tracking record가 `tracking_status: issue_backed`를 사용하고 Issue summary가 workflow `status: done`을 사용한다.
- [ ] real GitHub Issue number와 URL이 작업에 link되어 있다.
- [ ] Issue body/comment가 final summary, changed file, verification evidence, blocker, local work-log path를 포함한다.
- [ ] `ai/work-logs/issue-{number}/README.md`가 존재하고 모든 관련 role log를 link한다.
- [ ] 모든 관련 role log가 final workflow status, evidence, blocker, next handoff 또는 completion state를 기록한다.
- [ ] Issue acceptance criteria와 모든 required QA evidence를 충족했다.
- [ ] Issue에 unresolved blocker 또는 required follow-up이 없다.
- [ ] 모든 prior closure check가 통과한 후에만 Issue를 닫았다.
