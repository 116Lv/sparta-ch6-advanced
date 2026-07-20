# Review Gate Skill

## 목적

범위, 증거, cache 재사용, handoff 상태, 완료 준비 경계를 확인한다.

## 필수 입력

- Diff 또는 변경 파일 목록
- 검증 증거
- `ai/agent-handoff.json`
- Work-log 요약

## 허용 작업

- 정적 검토를 수행한다.
- 지원되지 않는 완료 주장을 차단한다.
- 보류 중인 GitHub reconciliation 상태를 확인한다.

## 금지 작업

- Phase 2B에서 제품 명령은 NOT RUN으로 유지한다.
- `tracking_status`가 `pending_issue`인 동안 issue-backed closure를 주장하지 않는다.
- reconciliation 완료, verification 완료, registry `VERIFIED` 또는 무조건적인 전체 DONE을 주장하지 않는다.

## 증거 출력

- PASS/FAIL 및 발견 사항을 포함한 검토 로그

## Handoff 및 재사용

handoff에는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, `github_reconciliation_status`를 포함한다.

## Phase 2B 경계

검토는 Phase 2B 구현 범위만 통과시킬 수 있다. GitHub 조정 공백을 닫을 수는 없다.

## Phase 2C 진입점

Phase 2C는 entry point `review`, `done-claim`, 기준 정책 `ai/verification-policy.json`, 요약 `ai/verification-gates.md`와 함께 `scripts/ai/verification-gate.sh`를 사용한다. gate는 `pending_issue`를 유지하면서 검증 완전성과 작업/변경 적용 가능성을 확인한다. 조정이 완료될 때까지 issue 기반 종료, 조정 완료 주장, 제한 없는 전체 DONE은 차단된다. 제품 명령은 NOT RUN으로 유지한다.
