# API Smoke Verifier Skill

## Purpose

Phase 2B에서 HTTP 요청을 실행하지 않고 API smoke 검증 준비 상태를 분류한다.

## Required Inputs

- `ai/command-registry.json`
- API smoke 명령 상태
- 현재 handoff 상태

## Allowed Operations

- case 또는 사전 조건이 없으면 API smoke를 `NOT_CONFIGURED`로 보고한다.
- 변경에 실제 API 증거가 필요하지만 사전 조건이 없으면 API smoke를 `BLOCKED`로 보고한다.

## Prohibited Operations

- Phase 2B에서 제품 명령은 NOT RUN으로 유지한다.
- 이 skill은 Phase 2B에서 HTTP, curl 또는 API 호출을 실행해서는 안 된다.
- server 또는 Docker Compose를 시작하지 않는다.
- 이후 승인된 phase에서 실제 request 증거 없이 API 검증 완료를 주장하지 않는다.

## Evidence Outputs

- 작업 로그의 NOT RUN 또는 readiness 분류

## Handoff And Reuse

handoff에는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, API smoke 분류를 포함한다.

## Phase 2B Boundary

Phase 2B는 계약만 기록한다. 실제 API smoke 실행은 이후 범위로 남는다.

Machine-contract literal: `Product commands remain NOT RUN in Phase 2B`; this skill `must not run HTTP, curl, or API calls in Phase 2B`.

## Phase 2C 진입점

Phase 2C는 entry point `api-smoke`, 기준 정책 `ai/verification-policy.json`, 요약 `ai/verification-gates.md`와 함께 `scripts/ai/verification-gate.sh`를 사용한다. 누락된 API smoke capability는 API/적용 가능한 변경 유형에서 `BLOCKED`, 관련 없는 변경 유형에서 `NOT_APPLICABLE`로 매핑한다. 제품 명령은 NOT RUN으로 유지한다.
