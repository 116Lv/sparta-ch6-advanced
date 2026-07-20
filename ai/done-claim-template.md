# 완료 주장 템플릿

`ai/qa-gate.md` 이후 `ai/issue-completion-checklist.md`의 closure section 전에 이 형식을 사용한다. 실제로 기록된 evidence 또는 실제로 실행한 command만 명시한다. `N/A`는 reason과 함께만 사용한다.

## 1. 요약

무엇이 변경되었고 resulting work status는 무엇인가?

## 2. 변경된 파일

- `path/to/file`: 변경 목적

## 3. 충족한 Routing 및 요구 사항

- Owning feature: `specs/{feature}` 또는 `none`
- 읽은 routing file:
- 충족한 requirement 및 acceptance criteria:

## 4. Delegated-Work 추적

- Dispatch한 subagent: `yes` 또는 `no`
- `tracking_status`: `issue_backed` 또는 `pending_issue`
- Workflow `status`: `planned`, `in_progress`, `handoff_needed`, `blocked`, `in_review`, 또는 `done`
- GitHub Issue number: <issue-backed이면 number, pending이면 `N/A - creation failed`>
- GitHub Issue URL: <issue-backed이면 URL, pending이면 `N/A - creation failed`>
- GitHub Issue state: `open`, `closed`, 또는 `not_created`
- Issue work-log path: `ai/work-logs/issue-{number}/README.md` 또는 승인된 `no-issue` fallback path
- 관련 agent log:
  - `ai/work-logs/issue-{number}/{role}.md` 또는 `ai/work-logs/no-issue/{work-key}/{role}.md`
- Current owner 및 recovery state:
- Fallback creation-attempt metadata/evidence: <pending이면 required, 그 외에는 `N/A - issue-backed`>
- Reconciliation status: 정확한 remaining step과 함께 `not_applicable`, `complete`, 또는 `pending`

subagent를 dispatch했으면 이 section의 모든 field가 required다. `tracking_status: issue_backed`에는 실제 Issue number, URL, summary, 관련된 모든 role log가 필수다. `tracking_status: pending_issue`에서는 문서화된 creation failure, exact fallback path, complete metadata, 모든 관련 role log, reconciliation plan이 있을 때만 `N/A` Issue field가 유효하다. missing/invalid data는 completion claim을 차단한다. valid pending fallback은 아래 설명한 issue-backed 및 unqualified overall `DONE` claim만 차단한다.

## 5. 실행한 명령

실제로 실행한 command만 나열한다. 실행하지 않은 required command를 명시적으로 식별한다.

```bash
./gradlew test
./gradlew integrationTest
curl -i http://localhost:8080/api/example
```

## 6. 테스트 결과

| Command 또는 check | 결과 | Evidence 또는 note |
|---|---|---|
| Typecheck/build | PASS/FAIL/NOT RUN | |
| Lint | PASS/FAIL/NOT RUN | |
| Unit test | PASS/FAIL/NOT RUN | |
| Integration test | PASS/FAIL/NOT RUN | |
| End-to-end test | PASS/FAIL/NOT RUN/N/A | |
| 실제 API 검증 | PASS/FAIL/NOT RUN/N/A | |

## 7. API 검증 증거

API가 변경되었으면 이 section을 완료한다.

| Method | Endpoint | 예상 | 실제 | 결과 | Evidence |
|---|---|---:|---:|---|---|
| POST | /api/example | 201 | 201 | PASS | command/log link |

## 8. Server Log 검토

- Unexpected 500 response: absent/present/not checked
- Unhandled exception: absent/present/not checked
- 관련 로그 증거:

## 9. 업데이트한 문서

- 업데이트한 docs, spec, ADR, workflow file:
- 업데이트하지 않은 문서: reason:

## 10. Blocker 및 남은 위험

- Blocker:
- 남은 risk 또는 unverified behavior:
- 필수 next handoff:

## 11. 완료 결정

- `implementation_status`: `PASS`, `FAIL`, `BLOCKED`, 또는 `PARTIAL`
- `tracking_status`: `issue_backed` 또는 `pending_issue`
- `github_issue_closure_status`: `ready_to_close`, `closed`, `not_ready`, 또는 `pending_issue_reconciliation`
- `overall_decision`: `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, 또는 `PARTIAL`

implementation completion, tracking availability, GitHub Issue closure는 별도 결정이다. fallback이 complete하면 `implementation_status: PASS`, `tracking_status: pending_issue`가 유효하지만 `overall_decision`은 `DONE`이어서는 안 된다. tracking reconciliation만 남은 concern이면 `DONE_WITH_CONCERNS`를 사용하고, 그 외에는 remaining blocker 또는 incomplete scope가 뒷받침하는 decision을 사용한다.

unqualified `overall_decision: DONE`에는 workflow `status: done`, `implementation_status: PASS`, `tracking_status: issue_backed`, `ready_to_close` 또는 `closed`인 `github_issue_closure_status`가 필요하다. closure checklist는 이 done claim의 존재를 검증할 수 있고 pre-QA checklist는 검증해서는 안 된다.

## Phase 2C 게이트 입력

verification completeness와 task/change applicability를 보고할 때 `ai/verification-gates.md`, `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`를 참조한다. 선택한 change type과 `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL`의 mapped result를 포함한다. 별도로 지원 evidence path를 통해 실행하지 않는 한 제품 명령은 계속 NOT RUN이다. `tracking_status`가 `pending_issue`인 동안 issue-backed closure, reconciliation-complete status, unqualified overall DONE을 주장하지 않는다.
