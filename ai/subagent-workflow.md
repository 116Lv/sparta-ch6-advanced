# Subagent Workflow

## Mandatory Routing Gate For Subagents

Before the Main Dev Agent dispatches any subagent, follow `ai/document-routing.md`.

The Main Dev Agent must:

1. Run the Mandatory Routing Gate.
2. Record one of these outcomes:
   - `Owning feature: specs/{feature}`
   - `Owning feature: none`
3. If the work is feature-owned, load `specs/{feature}/spec.md` before dispatching subject-specific planning, implementation, verification, review, or normative documentation work.
4. Pass the owning feature outcome and files already read to the subagent.

Subagents must not guess ownership or skip the feature spec. If the prompt does not identify the owning feature outcome, the subagent should ask for it before doing the task.

## Phase-Gated Subagent Handoffs

Use feature-spec files at the phase where they are needed:

- Specification Agent: read `spec.md` before drafting or changing requirements.
- Implementation Agent: read `spec.md` first, then `plan.md` before implementation planning or execution.
- Test Agent and API Verification Agent: read `spec.md`, then `tasks.md` before execution or verification handoff.
- Documentation Agent: read `spec.md` first for feature-owned normative docs, then owner docs selected by `ai/document-routing.md`.
- Review Agent: confirm the routing gate was followed, confirm the right phase-gated files were read, and block unsupported completion claims.

Every subagent handoff should include:

- owning feature outcome
- route-selected files already read
- phase-gated file required for this task
- decisions already made
- open questions
- evidence still required

## Principle

Main Dev Agent는 큰 작업에서 직접 구현자 역할만 하지 않는다. Main Dev Agent는 최종 검토자와 조율자 역할을 수행한다.

구현, 테스트, 검증, 문서 갱신은 가능한 경우 역할별 subagent에게 분리해 맡긴다.

## Agents

### Main Dev Agent

- 최종 리뷰
- 문서와 코드 일치 여부 확인
- 완료 증거 검토
- 승인 또는 반려

### Orchestrator Agent

- 작업 분해
- phase 구성
- 각 subagent에게 작업 할당
- 실패 시 재작업 지시

### Specification Agent

- spec 작성
- acceptance criteria 정리
- open questions 정리
- 요구사항과 문서 충돌 확인

### Implementation Agent

- 코드 구현
- 문서에 정의된 아키텍처 준수
- 구현 중 발생한 결정 사항 기록

### Test Agent

- unit test 작성
- integration test 작성
- regression test 작성
- 실패 케이스 작성

### API Verification Agent

- 실제 서버 실행
- 실제 HTTP request 수행
- status code와 response body 검증
- 예상하지 못한 500 에러 확인
- 서버 로그 확인

### Bug Hunter Agent

- edge case 탐색
- 권한/인증/validation 실패 케이스 확인
- regression 가능성 확인
- race condition 가능성 확인

### Documentation Agent

- docs/specs/decisions/adr 업데이트
- 완료 보고에 필요한 문서 링크 정리

### Review Agent

- 최종 코드 품질 리뷰
- QA Gate 통과 여부 확인
- Done Claim 증거 검토

## Handoff Rules

- 각 agent는 수행한 명령과 결과를 기록한다.
- 실패한 검증은 숨기지 않는다.
- 다음 agent가 필요한 context를 문서 링크와 함께 전달한다.
- Main Dev Agent는 증거 없는 완료 주장을 승인하지 않는다.
