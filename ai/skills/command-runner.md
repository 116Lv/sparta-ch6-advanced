# Command Runner Skill

## Purpose

Phase 1B 경계를 우회하지 않고 레지스트리 ID로 지원되는 command-runner 워크플로 계약을 선택한다.

## Required Inputs

- `ai/command-registry.json`
- Phase 1B command-runner 정책
- 현재 handoff 상태

## Allowed Operations

- Phase 1B 이후 `scripts/ai/command-runner.sh`가 유일하게 지원되는 project-command 경로임을 설명한다.
- Phase 2B의 제품 명령을 NOT RUN으로 기록한다.

## Prohibited Operations

- Phase 2B에서 제품 명령은 NOT RUN으로 유지한다.
- 직접 shell project command를 실행하지 않는다.
- RISKY, DESTRUCTIVE, non-POSIX, migration, seed, server, Docker, HTTP 또는 infrastructure 명령을 실행하지 않는다.

## Evidence Outputs

- Work-log NOT RUN 항목
- Policy 및 handoff 참조

## Handoff And Reuse

handoff에는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, 명령 레지스트리 ref를 포함한다.

## Phase 2B Boundary

지원 경로 실행은 이 작업의 향후 또는 이후 phase 동작으로 남으며 Phase 2B는 skill 계약만 기록한다.

Machine-contract literal: `Product commands remain NOT RUN in Phase 2B`.
