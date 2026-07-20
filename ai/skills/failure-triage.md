# Failure Triage Skill

## Purpose

이후 승인된 실패 명령 재실행 전에 root-cause 컨텍스트를 기록한다.

## Required Inputs

- 실패한 명령 증거 또는 helper/static 실패 출력
- 현재 handoff 상태
- 적용 가능한 정책 문서

## Allowed Operations

- 실패 증상을 요약한다.
- owner, 영향을 받는 route 및 다음 안전한 작업을 식별한다.

## Prohibited Operations

- Phase 2B에서 제품 명령은 NOT RUN으로 유지한다.
- 로컬 note를 작성하여 rerun을 승인하지 않는다.
- 실패 증거를 숨기거나 실패를 skipped check로 다시 작성하지 않는다.

## Evidence Outputs

- 작업 로그의 실패 triage 요약
- Blocker 또는 다음 handoff 기록

## Handoff And Reuse

handoff에는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, 실패 증거 ref를 포함한다.

## Phase 2B Boundary

이 skill은 triage 레코드만 정의하며 재실행 권한은 이후 범위로 남는다.

Machine-contract literal: `Product commands remain NOT RUN in Phase 2B`.

## Phase 2C 진입점

Phase 2C는 entry point `failure-triage`, 기준 정책 `ai/verification-policy.json`, 요약 `ai/verification-gates.md`와 함께 `scripts/ai/verification-gate.sh`를 사용한다. 실패한 leaf 결과는 `FAIL`, 차단된 필수 leaf 결과는 `BLOCKED`, 관련 없는 검사는 `NOT_APPLICABLE`로 매핑한다. 제품 명령은 NOT RUN으로 유지한다.
