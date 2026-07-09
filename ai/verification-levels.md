# Verification Levels

## Level 0: Document Review

문서만 검토한다. 코드 변경 없음.

Required evidence:

- Reviewed files
- Open questions
- No test claim unless tests were run

## Level 1: Static Verification

- typecheck
- lint
- formatting check

Required evidence:

- Exact commands
- PASS/FAIL/NOT RUN result

## Level 2: Unit Verification

- unit test
- domain rule test
- validation test

Required evidence:

- Test command
- Test result summary
- Failed test details if any

## Level 3: Integration Verification

- DB integration test
- API route/controller test
- repository/use case test
- external adapter test with controlled test environment

Required evidence:

- Test DB or container setup
- Test command
- Result summary

## Level 4: Real API Verification

- actual server run
- actual DB or test DB connection
- migration applied
- seed data prepared
- actual HTTP request executed
- 2xx/4xx response verified
- unexpected 500 absence verified

Required evidence:

- Server command
- Request command or tool
- Expected status
- Actual status
- Response body summary
- Server log review

## Level 5: E2E / Operational Verification

- browser-based E2E if frontend exists
- core user flow verification
- log review
- performance/load test when required
- operational failure scenario when required

Required evidence:

- E2E command or scenario
- Logs reviewed
- Result summary

## Required Levels by Change Type

| Change Type | Required Level |
|---|---:|
| 문서만 변경 | Level 0 |
| 타입/리팩토링 | Level 1 |
| 도메인 로직 변경 | Level 2 |
| DB/API 변경 | Level 4 |
| 인증/인가 변경 | Level 4 |
| 결제/권한/중요 데이터 변경 | Level 5 |
| 사용자 핵심 플로우 변경 | Level 5 |

## Escalation Rule

If the required level cannot be completed because the project is not scaffolded, dependencies are missing, or infrastructure is unavailable, report `BLOCKED` or `NOT RUN` with the exact reason. Do not downgrade the required level silently.

