# 검증 레벨

## Level 0: 문서 검토

문서만 검토한다. 코드 변경 없음.

필수 증거:

- 검토한 파일
- 미해결 질문
- 테스트를 실행하지 않았다면 테스트 주장을 하지 않음

## Level 1: 정적 검증

- typecheck
- lint
- formatting 검사

필수 증거:

- 정확한 명령
- PASS/FAIL/NOT RUN 결과

## Level 2: 단위 검증

- 단위 test
- 도메인 규칙 test
- validation test

필수 증거:

- Test 명령
- Test 결과 요약
- 해당되는 경우 실패한 test 세부 정보

## Level 3: 통합 검증

- DB 통합 test
- API route/controller test
- repository/use case 테스트
- 제어된 test 환경의 외부 adapter test

필수 증거:

- Test DB 또는 container 설정
- Test 명령
- 결과 요약

## Level 4: 실제 API 검증

- 실제 server 실행
- 실제 DB 또는 test DB 연결
- migration 적용
- seed data 준비
- 실제 HTTP request 실행
- 2xx/4xx response 검증
- 예기치 않은 500 부재 검증

필수 증거:

- Server 명령
- Request 명령 또는 tool
- 예상 status
- 실제 status
- Response body 요약
- Server log 검토

## Level 5: E2E / 운영 검증

- frontend가 있으면 browser 기반 E2E
- 핵심 사용자 flow 검증
- log 검토
- 필요한 경우 performance/load test
- 필요한 경우 운영 실패 scenario

필수 증거:

- E2E 명령 또는 scenario
- 검토한 log
- 결과 요약

## 변경 유형별 필수 레벨

| 변경 유형 | 필수 레벨 |
|---|---:|
| 문서만 변경 | Level 0 |
| 타입/리팩토링 | Level 1 |
| 도메인 로직 변경 | Level 2 |
| DB/API 변경 | Level 4 |
| 인증/인가 변경 | Level 4 |
| 결제/권한/중요 데이터 변경 | Level 5 |
| 사용자 핵심 플로우 변경 | Level 5 |

## 상향 규칙

프로젝트가 scaffold되지 않았거나 의존성이 없거나 infrastructure를 사용할 수 없어 필수 수준을 완료할 수 없으면 정확한 이유와 함께 `BLOCKED` 또는 `NOT RUN`을 보고한다. 필수 수준을 조용히 낮추지 않는다.

## Phase 2C 실행 가능 게이트

QA 또는 done-claim 보고 전에 `ai/verification-gates.md`, 기준 `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`를 사용해 검증 완전성과 작업/변경 적용 가능성을 평가한다. Phase 2C gate는 변경 유형별로 `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL`을 매핑한다. 제품 명령은 정적/helper gate 평가에서 NOT RUN으로 유지한다.

