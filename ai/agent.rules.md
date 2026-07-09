# Agent Rules

## Document Routing

- Start with `ai/document-routing.md`.
- Identify the owning feature/spec before planning.
- Read `specs/{feature}/spec.md` before subject-specific planning, implementation, verification, review, or normative documentation work.
- Read `specs/{feature}/plan.md` before implementation planning or execution.
- Read `specs/{feature}/tasks.md` before execution or verification handoff.
- Read `specs/{feature}/decisions.md` when prior feature decisions exist or when new decisions are made.
- Read `specs/{feature}/checklist.md` before completion claims.
- If auth, permission, role, user identity, principal, account ownership, or `userId` semantics are touched, read and update `docs/02-users-and-permissions.md`.
- The documentation-only route applies only to non-normative wording, index, status, or report edits. Otherwise route by the thing being changed.
- Main Dev Agent coordinates and does final consistency checks. Role agents may draft, implement, test, verify, document, or review within their lane.

## Core Rule

AI는 문서에 없는 요구사항을 임의로 추가하지 않는다.

AI는 테스트를 실행하지 않았다면 실행했다고 말하지 않는다.

AI는 실제 검증 증거 없이 완료를 주장하지 않는다.

## Required Behavior

- 작업 전 관련 문서를 읽는다.
- 모호한 부분은 질문으로 남긴다.
- 임의 가정을 했다면 명시한다.
- 코드와 문서가 충돌하면 보고한다.
- 기능 변경 시 spec/docs/adr 업데이트 필요 여부를 확인한다.
- 완료 전 `ai/qa-gate.md`를 통과해야 한다.
- 완료 주장은 `ai/done-claim-template.md` 형식을 따른다.

## Forbidden Behavior

- 테스트하지 않고 "테스트 완료"라고 말하기
- mock 테스트만 하고 실제 API 검증했다고 말하기
- 500 에러를 무시하고 완료 처리하기
- TODO, 임시 코드, debug log를 이유 없이 남기기
- 에러를 catch하고 삼켜버리기
- 타입 에러를 `any`로 덮기
- 요구사항을 만족하지 못했는데 완료 주장하기
- 문서와 다른 구현을 조용히 추가하기
- 실패한 테스트를 요구사항 변경으로 우회하기

## Evidence Rule

검증 결과는 반드시 실행 명령, 결과, 실패 여부, 실행하지 못한 이유를 포함해야 한다.

`PASS`는 실제로 실행하고 성공했을 때만 사용한다.
