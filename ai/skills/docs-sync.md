# Docs Sync Skill

## 목적

route가 선택한 기준 문서만 업데이트하고 요약을 JSON 기준 문서와 일관되게 유지한다.

## 필수 입력

- Routing 결과
- Route에서 선택한 문서
- 있는 경우 기준 JSON 참조

## 허용 작업

- 범위가 좁은 owner 문서를 갱신한다.
- 실행 가능한 규칙을 중복하는 대신 정식 JSON에 연결한다.

## 금지 작업

- Phase 2B에서 제품 명령은 NOT RUN으로 유지한다.
- 정식 JSON과 독립적으로 생성된 요약을 수동으로 재정의하지 않는다.
- workflow 전용 문서를 통해 제품 요구 사항을 변경하지 않는다.

## 증거 출력

- 변경 문서 목록
- Work-log 근거 및 route 기록

## Handoff 및 재사용

handoff에는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, 변경된 문서를 포함한다.

## Phase 2B 경계

문서 동기화는 AI 워크플로 skill, handoff, 재사용 가능한 컨텍스트 통합으로 제한한다.
