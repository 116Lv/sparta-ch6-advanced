# Done Claim Template

AI는 작업 완료를 주장할 때 반드시 아래 형식으로 보고한다.

## 1. Summary

무엇을 변경했는가?

## 2. Files Changed

- ...

## 3. Requirements Covered

어떤 spec requirement와 acceptance criteria를 만족했는가?

## 4. Commands Executed

실제로 실행한 명령어를 적는다.

```bash
./gradlew test
./gradlew integrationTest
curl -i http://localhost:8080/api/example
```

실행하지 않은 명령어는 실행하지 않았다고 명시한다.

## 5. Test Results

| Command | Result | Notes |
|---|---|---|
| typecheck/build | PASS/FAIL/NOT RUN | ... |
| lint | PASS/FAIL/NOT RUN | ... |
| unit test | PASS/FAIL/NOT RUN | ... |
| integration test | PASS/FAIL/NOT RUN | ... |
| real API verification | PASS/FAIL/NOT RUN | ... |

## 6. API Verification Evidence

API 변경이 있는 경우 작성한다.

| Method | Endpoint | Expected | Actual | Result |
|---|---|---:|---:|---|
| POST | /api/example | 201 | 201 | PASS |
| GET | /api/example/invalid | 404 | 404 | PASS |

## 7. Server Log Review

- unexpected 500: 없음/있음
- unhandled exception: 없음/있음
- 관련 로그 요약:

## 8. Documentation Updated

- 업데이트한 docs/specs/adr:
- 업데이트가 필요 없었던 이유:

## 9. Remaining Risks

남은 리스크나 확인하지 못한 부분을 적는다.

## 10. Completion Decision

- PASS: 완료 가능
- FAIL: 완료 불가
- BLOCKED: 질문/환경 문제로 중단

