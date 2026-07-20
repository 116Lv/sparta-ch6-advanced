# Repo Intake Skill

## Purpose

재탐색 전에 Phase 2A 저장소 컨텍스트와 cache 레코드를 재사용한다.

## Required Inputs

- `ai/context-map.json`
- `ai/workflow-cache.json`
- `ai/project-state.json`
- `ai/command-registry.json`

## Allowed Operations

- `scripts/ai/repo-intake.sh --output -`를 통해 read-only repo intake를 실행한다.
- proposal-only project-state 갱신 및 command-discovery update를 보고한다.

## Prohibited Operations

- Phase 2B에서 제품 명령은 NOT RUN으로 유지한다.
- 저장소 `.ai-runs`를 생성하지 않는다.
- registry command를 `VERIFIED`로 표시하지 않는다.

## Evidence Outputs

- 정제된 work-log 요약
- helper를 명시적으로 실행한 경우 `REPO_INTAKE` 구조화 결과

## Handoff And Reuse

handoff에는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`를 포함한다.

## Phase 2B Boundary

이 skill은 Phase 2B에서 읽기 전용이며 제안만 수행한다.

Machine-contract literal: `Product commands remain NOT RUN in Phase 2B`.
