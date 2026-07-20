# AI 워크플로 스킬

## 목적

Phase 2B는 재사용 가능한 AI 워크플로 skill 계약을 정의한다. skill 목록의 기준 문서는 `ai/skill-catalog.json`이다. 제품 명령은 Phase 2B에서 NOT RUN으로 유지한다.

## 필수 스킬

- `repo-intake`
- `command-runner`
- `verification-runner`
- `api-smoke-verifier`
- `failure-triage`
- `docs-sync`
- `review-gate`

기준 카탈로그는 각 ID가 한 번씩 나타나는 이 정확한 ID 집합을 포함해야 한다. schema `uniqueItems`는 심층 방어이며, 일곱 카탈로그 객체가 구조적으로 구별되더라도 의미 검증은 중복, 누락, 대체 또는 알 수 없는 ID를 거부한다.

## 공통 경계

이 skill은 입력, 출력, handoff 요구사항, 검토 가능한 증거를 정의한다. 저장소 `.ai-runs`, artifact manifest, finalized `run.json`, 레지스트리 `VERIFIED` 전환, 검증 완전성 주장, issue 기반 종료, 조정 완료 주장 또는 제한 없는 전체 DONE 주장을 만들지 않는다.

## Phase 2C 검증 게이트

Phase 2C는 `verification-runner`, `api-smoke-verifier`, `failure-triage`, `review-gate`를 `ai/verification-gates.md`, `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`에 연결한다. 이 정적/helper gate는 검증 완전성, 작업/변경 적용 가능성, `NOT_CONFIGURED` / `NOT_APPLICABLE` / `BLOCKED` / `FAIL` 매핑을 정의한다. 제품 명령은 NOT RUN으로 유지한다.
