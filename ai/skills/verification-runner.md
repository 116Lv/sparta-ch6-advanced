# 검증 실행기 스킬

## Purpose

검증 완전성을 주장하지 않으면서 검증 계약을 선택하고 무엇을 실행했거나 실행하지 않았는지 기록한다.

## Required Inputs

- `ai/verification-levels.md`
- `ai/command-registry.json`
- 현재 인계 상태

## Allowed Operations

- current phase가 허용하는 static/helper/contract check를 선택한다.
- 명시적 NOT RUN item을 기록한다.

## Prohibited Operations

- 제품 명령은 Phase 2B에서 계속 NOT RUN이다.
- verification completeness를 주장하지 않는다.
- `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL`을 PASS로 변환하지 않는다.

## Evidence Outputs

- verification command name과 observed result
- 명시적 NOT RUN 목록

## Handoff And Reuse

handoff에는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, verification evidence ref를 포함한다.

## Phase 2B Boundary

Phase 2B는 static/helper/contract artifact만 검증하며 full task applicability를 평가하지 않는다.

Machine-contract literal: `Product commands remain NOT RUN in Phase 2B`.

## Phase 2C 진입점

Phase 2C는 verification completeness와 task/change applicability를 평가하기 위해 canonical `ai/verification-policy.json`, summary `ai/verification-gates.md`와 함께 `scripts/ai/verification-gate.sh`를 사용한다. `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL`은 change type별로 매핑된다. 제품 명령은 이 static/helper gate에서 계속 NOT RUN이다.
