# QA Gate

검토/증거 준비와 QA 전 checklist 뒤, done claim 생성 전에 이 gate를 실행한다. 이 gate는 `implementation_status`를 결정하며 그 자체로 전체 `DONE` 주장이나 GitHub Issue 종료를 승인하지 않는다. 실패했거나 누락되었거나 기록되지 않은 필수 검사는 구현 완료를 차단하며 암묵적 통과가 아니다.

## 필수 검증 검사

- Typecheck가 통과한다.
- Lint가 통과한다.
- 단위 test가 통과한다.
- 통합 test가 통과한다.
- 필요할 때 end-to-end test가 통과한다.
- 변경에 database migration이 포함되면 성공한다.
- runtime 동작이 변경되면 server가 시작한다.
- API 동작이 변경되면 실제 API 요청이 성공한다.
- 예상하지 못한 HTTP 500 응답이 발생하지 않는다.
- server log에 처리되지 않은 exception이 없다.
- API 응답 본문이 문서화된 계약과 일치한다.

## API 검증 규칙

API를 변경하는 작업은 mock test만으로 완료할 수 없다. 실행 중인 server에 실제 HTTP 요청을 실행한다.

적용되는 경우 변경된 각 endpoint를 검증한다.

| 사례 | 예상 결과 |
|---|---|
| 유효한 요청 | 2xx |
| 잘못된 입력 | 400 |
| 인증되지 않은 요청 | 401 |
| 인가되지 않은 요청 | 403 |
| 누락된 리소스 | 404 |
| 중복 또는 충돌 | 409 |
| 내부 실패 | 예상하지 못한 500 응답 없음 |

## 위임 작업 증거 게이트

이 섹션은 하나 이상의 하위 에이전트를 배정할 때마다 적용된다. 구현 QA가 통과하기 전 다음 모두가 필수다.

- `tracking_status`는 정확히 `issue_backed` 또는 `pending_issue`이고, 워크플로 `status`는 정식 진행 값만 사용한다.
- 실제 GitHub Issue 기반 기록 또는 아래에 정의된 완전한 fallback 중 정확히 하나의 추적 기록이 존재한다.
- Issue 요약은 `ai/work-logs/issue-{number}/README.md` 또는 승인된 `ai/work-logs/no-issue/{work-key}/README.md` 경로에 존재한다.
- 배정된 모든 역할에 대해 해당 요약 옆에 역할별 작업 로그가 존재한다.
- Issue 요약은 관련된 모든 역할 로그를 연결하고 현재 owner, 추적 상태, 워크플로 상태 및 복구 상태를 식별한다.
- 에이전트 로그는 범위, 변경 파일, 명령, 검증 증거, blocker 및 다음 handoff를 기록한다.
- 추적 기록과 작업 로그에는 수용 기준 및 필수 검증 수준을 검증하기에 충분한 증거가 포함된다.

`tracking_status: issue_backed`에는 실제 GitHub Issue 번호와 URL이 `ai/work-logs/issue-{number}/`에 연결되어야 한다. 누락되었거나 유효하지 않은 추적 메타데이터, Issue 요약, 관련 역할 로그 또는 필수 검증 증거는 QA 차단 요소다. 검토자는 구두 handoff, 연결되지 않은 terminal 결과 또는 기록되지 않은 주장으로 증거를 추론해서는 안 된다.

### `pending_issue` Exception

GitHub 사용 불가는 문서화된 fallback을 통해서만 작업 계속을 허용한다. 임시 디렉터리는 정확히 하나의 의도된 향후 Issue 경계를 보존해야 한다. 해당 Issue 요약과 모든 역할 로그는 `tracking_status: pending_issue`를 사용하고 실제 진행을 워크플로 `status`에 유지하며 `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `reconciliation_required: true`, `migration_history`를 기록해야 한다.

fallback 메타데이터, 모든 역할 로그, 모든 적용 가능한 검증 증거가 완전하고 유효하면 `tracking_status`가 `pending_issue`로 유지되어도 QA는 `implementation_status: PASS`를 생성할 수 있다. 대기 중인 추적은 여전히 제한 없는 전체 `DONE`, issue 기반 주장, 조정 완료, GitHub Issue 종료를 차단한다.

이후 조정에는 하나의 의도된 Issue 생성, 전체 fallback 디렉터리의 `ai/work-logs/issue-{number}/` 이동, `migration_history`의 이전 경로 보존, 모든 메타데이터와 색인 갱신, Issue에 migration 요약 게시가 필요하다. 이전 디렉터리 링크나 선택 파일 복사는 조정이 아니다.

## 구현 QA 실패 조건

다음 중 하나라도 적용되면 구현 QA는 실패한다.

- 필수 검증을 실행하지 않았다.
- 필수 검증의 결과 또는 증거가 누락되었다.
- runtime 검증이 필요한데 server를 시작하지 않았다.
- 필수 database migration을 적용하지 않았다.
- API 변경 뒤 실제 API 요청을 수행하지 않았다.
- 예상하지 못한 500 응답이 발생했다.
- server log에 처리되지 않은 exception이 있다.
- 실패한 test를 무시했다.
- test를 통과시키기 위해서만 요구사항을 변경했다.
- 문서와 구현이 충돌한다.
- 위임 작업 추적 메타데이터, 역할 로그, fallback 메타데이터 또는 필수 증거가 누락되었거나 유효하지 않다.

문서화된 fallback이 그 외에 완전하다면 불완전한 조정 자체는 구현 QA를 실패시키지 않는다. 이는 issue 기반 추적, 제한 없는 전체 `DONE`, 조정 완료, Issue 종료의 차단 요소로 남는다.

## QA 출력

done claim에 정확히 하나의 구현 결과를 기록한다.

- 완전한 fallback 사용 시를 포함해 적용 가능한 모든 구현 및 위임 증거 검사가 통과하면 `implementation_status: PASS`.
- 필수 검사가 실패하면 `implementation_status: FAIL`.
- 필수 검사를 실행할 수 없거나 필수 증거를 얻을 수 없으면 `implementation_status: BLOCKED`.
- 명시적으로 허용된 검증은 통과했지만 필수 구현 범위가 불완전하면 `implementation_status: PARTIAL`.

`implementation_status`가 `PASS`이면 done claim 생성 전에 Issue 요약과 완료된 역할 로그의 워크플로 `status: done`을 설정한다. 이 전환 중 `tracking_status`를 변경하지 않는다.

## 사용할 수 없는 검증 보고

환경 때문에 검증을 실행할 수 없으면 `BLOCKED` 또는 `PARTIAL`을 보고하며 완료를 보고하지 않는다.

허용 예시:

- `NOT RUN: 프로젝트에 아직 Gradle wrapper가 없습니다.`
- `BLOCKED: MySQL, Redis 또는 Kafka test 환경을 사용할 수 없습니다.`

허용되지 않는 예시:

- `test를 실행하지 않았지만 작업은 완료되었습니다.`
- `logic이 올바른 것으로 보입니다.`
- `Mock 검증은 실제 API가 작동함을 증명합니다.`

## Phase 2C 실행 가능 게이트

구현 QA를 기록하기 전에 `ai/verification-gates.md`, 기준 `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`를 사용해 변경 유형을 분류하고 작업/변경 적용 가능성을 평가하며 `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL`을 매핑한다. 제품 명령은 이 정적/helper gate에서 NOT RUN으로 유지한다. 완전한 `pending_issue` fallback은 구현 QA를 지원할 수 있지만 issue 기반 종료, 조정 완료 주장, 제한 없는 전체 DONE은 계속 차단된다.
