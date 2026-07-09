# QA Gate

작업은 QA Gate를 통과하기 전까지 완료로 인정하지 않는다.

## Required Checks

- typecheck 통과
- lint 통과
- unit test 통과
- integration test 통과
- 필요한 경우 e2e test 통과
- DB migration 성공
- 서버 실행 성공
- 실제 API request 성공
- 예상하지 못한 500 응답 없음
- 서버 로그에 unhandled exception 없음
- API response body가 문서의 contract와 일치

## API Verification Rules

API가 변경된 작업은 mock 테스트만으로 완료할 수 없다.

반드시 실제 서버를 대상으로 HTTP request를 수행해야 한다.

각 endpoint는 가능한 경우 다음을 확인한다.

| Case | Expected |
|---|---|
| 정상 요청 | 2xx |
| 잘못된 입력 | 400 |
| 인증 없음 | 401 |
| 권한 없음 | 403 |
| 없는 리소스 | 404 |
| 중복/충돌 | 409 |
| 서버 내부 오류 | 예상하지 못한 500이 없어야 함 |

## Failure Conditions

다음 중 하나라도 해당하면 완료가 아니다.

- 테스트를 실행하지 않음
- 테스트 결과 로그가 없음
- 서버를 실행하지 않음
- DB migration을 적용하지 않음
- 실제 API 요청을 수행하지 않음
- 예상하지 못한 500 발생
- 서버 로그에 unhandled exception 존재
- 실패한 테스트를 무시함
- 테스트를 통과시키기 위해 요구사항을 변경함
- 문서와 구현이 충돌함

## Exception Handling

검증을 실행할 수 없는 환경이면 완료가 아니라 `BLOCKED` 또는 `PARTIAL`로 보고한다.

허용되는 표현:

- "NOT RUN: 프로젝트에 Gradle wrapper가 아직 없습니다."
- "BLOCKED: MySQL/Redis/Kafka 테스트 환경이 아직 없습니다."

허용되지 않는 표현:

- "테스트는 못 했지만 완료입니다."
- "로직상 문제 없어 보입니다."
- "mock으로 확인했으니 실제 API도 문제 없습니다."

