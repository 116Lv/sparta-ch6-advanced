# AI 워크플로 강제 적용 설계

## 상태

승인된 방향이며 문서화 명세 검토 대기 중이다.

## 문제

저장소에는 상세한 Markdown 지침이 있지만, 반복되는 에이전트 결정과 절차는 영속적 상태나 실행 가능한 게이트로 뒷받침되지 않는다. 에이전트는 저장소 구조, 명령, 검증 흐름 및 문서 경로를 반복해서 다시 발견하고, 변경되지 않은 파일을 다시 읽고, 변경되지 않은 명령을 다시 실행하며, 하위 에이전트 간에 탐색을 중복할 수 있다.

이 설계는 안정된 결정을 registry로, 반복 절차를 skill로, 필수 검사를 hook으로, 재사용 가능한 탐색 결과를 cache 및 handoff 기록으로 옮긴다. 문서화는 여전히 필요하지만, 더 긴 prompt로 누락된 강제 적용을 보완하는 대신 실행 가능한 워크플로 상태를 설명하거나 저장한다.

## 설계 원칙

1. 안정된 사실은 한 번 탐색하고 증거 및 무효화 규칙과 함께 저장한다.
2. 명령은 registry ID로 참조하고 하나의 gateway를 통해 실행한다.
3. 반복 절차는 경계가 있는 입력과 출력을 갖는 skill로 분리한다.
4. 필수 전이는 증거가 없을 때 실행 가능한 hook으로 차단한다.
5. 선언된 입력이 바뀔 때까지 cache 결과를 재사용한다.
6. 하위 에이전트는 컨텍스트를 다시 구성하는 대신 이전 탐색 결과와 명령 증거를 받는다.
7. 시스템은 강제 적용 한계를 정직하게 보고한다. 호스트 에이전트 runtime이 네이티브 hook adapter를 제공하지 않는 한, 저장소 스크립트는 저장소 gateway를 우회하는 도구 호출을 가로챌 수 없다.

## 아키텍처

### 기계 판독 가능 상태

Markdown 문서는 사람이 읽는 정책과 검토에 사용한다. 실행 가능한 스크립트는 자유 형식 Markdown 표를 주된 기준 문서로 파싱해서는 안 된다.

기계 판독 가능 워크플로 상태는 전용 JSON 파일에 저장한다.

- `ai/command-registry.json`
- `ai/project-state.json`
- `.ai-runs/<run-id>/run.json`

대응하는 Markdown 파일은 이 기록을 설명하고 현재 상태를 요약한다. 실행의 정식 출처는 JSON이다. registry 검증 명령은 schema를 검사하고 생성되거나 요약된 Markdown이 이를 모순하지 않는지 확인한다. 에이전트는 서로 독립적인 두 기준 문서를 수동으로 유지해서는 안 된다.

### JSON 스키마

실행 가능한 JSON 상태는 사용 전에 반드시 검증해야 한다.

Required schemas:

- `ai/schemas/command-registry.schema.json`
- `ai/schemas/project-state.schema.json`
- `ai/schemas/run.schema.json`
- `ai/schemas/command-result.schema.json`
- `ai/schemas/done-claim.schema.json`
- `ai/schemas/approval-record.schema.json`
- `ai/schemas/policy-violation.schema.json`

스크립트는 최선 노력 파싱을 시도하는 대신 유효하지 않거나 지원하지 않는 schema 버전을 거부한다. schema 검증은 fail-closed이다. 잘못된 상태, 알 수 없는 필수 필드 및 호환되지 않는 버전은 영향을 받는 워크플로 작업을 차단한다.

### 상태 계약

스키마는 모호한 하나의 범용 상태 대신 서로 다른 개념별 별도 enum을 정의한다.

- 프로젝트 사실 신뢰도: `CONFIRMED`, `INFERRED`, `UNKNOWN`, `STALE`, `UNCERTAIN`
- 기능 구성: `UNKNOWN`, `CONFIGURED_UNVERIFIED`, `VERIFIED`, `NOT_CONFIGURED`, `STALE`, `UNCERTAIN`
- 워크플로 결과: `PASS`, `FAIL`, `BLOCKED`, `NOT_CONFIGURED`, `NOT_APPLICABLE`, `SKIPPED_WITH_REASON`
- 스크립트 제어 결과: `PASS`, `FAIL`, `BLOCKED`, `NOT_CONFIGURED`, `POLICY_VIOLATION`, `INVALID_STATE`, `NOT_APPLICABLE`, `SKIPPED_WITH_REASON`

`OK`, `DONE`, `PASSED`, `probably-pass`, `not-needed` 같은 값은 유효하지 않다. `NOT_CONFIGURED`는 기능 또는 검증 메커니즘이 정의되지 않았음을 뜻한다. `BLOCKED`는 현재 작업에 누락되었거나 사용할 수 없는 해당 기능이 필요함을 뜻한다. `NOT_APPLICABLE`는 해당 기능이 분류된 작업에 적용되지 않음을 뜻한다. `FAIL`은 실행이 발생했고 실패했음을 뜻한다. `SKIPPED_WITH_REASON`은 선택된 검증 정책이 건너뛰기를 명시적으로 허용하고 이유를 기록하는 경우에만 허용된다. 사람이 읽는 요약은 `NOT_APPLICABLE`를 `N/A`로 표시하지만, 실행 가능한 JSON은 정식 값으로 `N/A`를 저장하지 않는다.

### 안정된 컨텍스트

- `ai/context-map.md`: 저장소 surface, 소유권, canonical document, 중요 경로, generated/excluded path 및 최소 읽기 route.
- `ai/command-registry.json`: canonical command ID, argv array, 분류, 증거, 전제 조건, 입력 경로 및 검증 상태.
- `ai/command-registry.md`: 사람이 읽을 수 있는 명령 정책 및 생성된 registry 요약.
- `ai/project-state.json`: canonical stack, package manager, port, 환경 파일, service, test framework, 신뢰 상태 및 intake fingerprint.
- `ai/project-state.md`: 사람이 읽을 수 있는 project-state 설명 및 요약.

정식 JSON과 사람이 작성한 정책 참고는 소유자가 다르다. Markdown 요약은 별도 섹션을 사용한다.

```text
## 사람이 작성하는 정책 참고
사람이 편집하는 설명.

## 생성된 상태 요약
정식 JSON에서 생성됨. 수동 편집은 금지된다.
```

생성 섹션에는 `<!-- GENERATED SUMMARY FROM ai/command-registry.json. DO NOT EDIT MANUALLY. -->` 같은 표시를 포함한다. registry 검증은 오래되었거나 정식 JSON과 일치하지 않는 생성 요약을 거부한다.

`ai/document-routing.md`는 얇은 routing gate가 된다. 소유 기능과 route ID를 선택한 뒤 저장소 전역 경로 및 읽기 결정을 `context-map.md`에 위임한다.

### 캐시 및 도구 제어

- `.ai-runs/<run-id>/`: append-only 실행별 명령 metadata, 정제된 log, 검증 증거 및 done-claim 입력.
- `ai/workflow-cache.md`: 최근 실행 요약, 증거 pointer, 파일 탐색 결과 및 재사용 가능한 handoff note. 제한 없는 raw log는 저장하지 않는다.
- `ai/cache-policy.md`: cache key, freshness rule, invalidation trigger 및 재탐색을 허용하는 조건.
- `ai/tool-call-policy.md`: broad search, tree scan, 반복 file read, 반복 command discovery 및 중복 external tool call 한도.
- `ai/resource-budget.md`: 숫자 기본 한도 및 예외에 필요한 사유.
- `ai/agent-handoff.md`: orchestrator와 subagent 전환을 위한 공유 context packet.

명령 결과의 cache key에는 명령 ID, argv hash, 작업 디렉터리, registry에 선언된 관련 입력 경로의 hash 및 allowlist 환경 fingerprint가 포함된다. 같은 key에 대한 재실행에는 허용된 이유가 필요하다. 파일 읽기는 수정 시각만이 아니라 정규화된 경로와 콘텐츠 hash로 key를 만든다. cache 계산이 또 다른 전체 저장소 스캔이 되지 않도록 입력 hash는 범위가 제한되어야 한다.

선언된 입력과 관련 환경 fingerprint가 변경되지 않은 경우에만 cache 재사용이 허용된다. 변경된 파일을 registry 선언 입력에 확신 있게 매핑할 수 없으면 영향을 받는 cache 항목은 `STALE` 또는 `UNCERTAIN`이 된다. 의존성 매핑이 불완전하거나 모호하면 워크플로는 안전하지 않은 재사용보다 재검증을 우선한다.

실행별 증거 디렉터리는 하위 에이전트 간 공유 쓰기 충돌을 피한다. registry 및 project-state 갱신은 직렬화하고 임시 파일에 쓴 뒤 schema 검증하고 원자적으로 이름을 바꾼다. 모든 lock은 소유자, run ID 및 생성 시각을 기록하여 오래된 lock이 이후 작업을 조용히 막는 대신 탐지되도록 한다.

### 스킬

스킬은 반복되는 다단계 절차를 담당한다.

- `repo-intake`: 초기 설정 또는 유효한 invalidation 후 context map, project state 및 command registry를 채운다.
- `command-runner`: registry ID를 검증하고 command hook을 호출하며 명령을 실행하고 결과를 기록한다.
- `verification-runner`: verification level에 등록된 check를 선택하고 실행한다.
- `api-smoke-verifier`: 선언된 실제 HTTP case를 실행하고 server evidence를 검토한다.
- `failure-triage`: 실패한 명령의 재실행을 허용하기 전에 root cause를 기록한다.
- `docs-sync`: context map이 선택한 canonical document만 업데이트한다.
- `review-gate`: scope, evidence, cache update 및 completion readiness를 검증한다.

스킬 문서는 계약과 리소스 예산을 정의한다. 실행 가능한 동작은 각 스킬 문서 안의 중복된 shell fragment가 아니라 공유 스크립트에 둔다.

### 훅

- `PRE_TASK`: context map, project state, registry, cache policy 및 route 선택을 요구한다. 상태가 누락되었거나 유효하지 않을 때만 repository intake를 허용한다.
- `PRE_EDIT`: 소유권, 이전 read/cache 상태 및 영향받는 document route를 요구한다.
- `PRE_COMMAND`: 등록된 command ID, 안전 분류, 전제 조건 및 중복 시 유효한 재실행 사유를 요구한다.
- `POST_COMMAND`: 정확한 결과와 실패 증거를 기록하고 실패 후 조용한 계속 진행을 차단한다.
- `PRE_VERIFY`: 필수 verification level과 등록된 verification ID를 결정한다.
- `POST_VERIFY`: 결과와 미해결 실패를 영속화한다.
- `PRE_DONE_CLAIM`: 적용 가능한 검증 증거, 명시적 NOT RUN 항목, 필요할 때 API 증거 및 미해결 unexpected 500 또는 unhandled exception이 없음을 요구한다.

hook 계약은 `ai/hooks/` 아래에 둔다. `scripts/ai/workflow-gate.sh`는 hook 단계가 공유하는 검사를 구현한다. `scripts/ai/command-runner.sh`는 명령 실행 경계이며 pre/post 명령 검사를 호출한다.

### 명령 실행 안전성

에이전트는 원시 shell 명령을 직접 실행하지 않는다. 에이전트는 registry ID로 명령 실행을 요청한다.

```bash
scripts/ai/command-runner.sh run <command-id>
```

command runner는 `ai/command-registry.json`에서 명령 ID를 해석하고, 안전성 검사를 적용하며, pre/post 명령 gate를 호출하고, `eval` 없이 선언된 argv를 실행하며, `.ai-runs/<run-id>/` 아래에 증거를 기록한다. registry에 없는 명령은 범위가 있는 탐색 또는 승인된 registry 갱신이 증거와 함께 해당 명령을 기록할 때까지 차단된다.

구성된 명령은 원시 shell 문자열이 아니라 argv 배열을 사용한다. 구조화된 helper는 shell 확장을 비활성화한 상태로 실행한다. 동적 인수는 registry 선언 매개변수 schema를 통해서만 허용하며, 검사되지 않은 shell 텍스트로 추가하지 않는다.

기본적으로 매개변수는 비활성화된다.

```json
{
  "id": "gradle-test",
  "argv": ["./gradlew", "test"],
  "classification": "safe",
  "parameters": { "allowed": false }
}
```

매개변수가 필요한 명령은 placeholder와 폐쇄형 검증 schema를 선언한다. 제공된 각 값은 검증 후 하나의 argv 요소가 되며 shell에 의해 해석되지 않는다.

```json
{
  "id": "gradle-test-class",
  "argv": ["./gradlew", "test", "--tests", "{{testClass}}"],
  "classification": "safe",
  "parameters": {
    "allowed": true,
    "schema": {
      "type": "object",
      "additionalProperties": false,
      "required": ["testClass"],
      "properties": {
        "testClass": {
          "type": "string",
          "pattern": "^[A-Za-z0-9_.$*]+$"
        }
      }
    }
  }
}
```

잘못된 registry schema 및 해석되지 않은 placeholder는 `INVALID_STATE`를 생성한다. 알 수 없는 매개변수, 누락된 필수 매개변수 및 매개변수 검증 실패는 `POLICY_VIOLATION`을 생성한다. 두 결과는 모두 process 실행 전에 발생한다.

### 파일 읽기 및 도구 호출 강제 적용 경계

저장소 스크립트는 에이전트가 `scripts/ai/command-runner.sh`를 사용할 때만 명령 실행을 gate할 수 있다. 네이티브 runtime adapter 없이는 반복 파일 읽기, 광범위 검색, 직접 shell 호출, MCP 호출 또는 다른 호스트 도구 호출을 완전히 가로챌 수 없다.

네이티브 adapter가 존재할 때까지 file-read, search 및 tool-call 규칙은 정책, cache 기록, handoff 기록, 감사 검사 및 done-claim 검토를 통해 강제한다. 탐지된 우회는 정책 위반으로 기록되고 완료를 차단할 수 있지만, Phase 1 및 Phase 2는 완전한 기술적 가로채기를 주장하지 않는다. Phase 3은 호스트가 지원하는 곳에 네이티브 runtime adapter와 CI gate를 추가할 수 있다.

### 증거 저장소

워크플로 증거는 실행별로 `.ai-runs/<run-id>/` 아래에 저장한다.

```text
.ai-runs/<run-id>/
  run.json
  approvals.json
  policy-violations/
    <event-id>.json
  commands/
    <command-id>.json
  logs/
    <command-id>.stdout.log
    <command-id>.stderr.log
  done-claim.json
  done-claim.md
```

워크플로 cache에는 요약과 증거 포인터만 저장한다. 원시 증거에는 로컬 또는 민감한 데이터가 있을 수 있으므로 `.ai-runs/`는 기본적으로 Git이 무시한다. 영속적인 저장소 작업 로그에는 정제된 요약을 담고, CI는 정제된 원시 증거를 외부 아티팩트로 보존할 수 있다.

명령 출력, HTTP 응답 및 검증 로그는 영속화 전에 필터링한다. authorization header, cookie, token, password, secret 및 민감한 환경 값은 마스킹한다. `.env`, `.env.local`, credential store 및 secret file 콘텐츠를 수집해서는 안 된다. 사후 처리만으로는 secret 제거를 보장할 수 없으므로 가능한 경우 수집에 allowlist를 사용한다.

원시 증거는 로컬에 있으며 기본적으로 Git이 무시한다. 검토 가능한 증거는 `ai/workflow-cache.md`, issue 작업 로그, 완료 보고서 및 CI 아티팩트 요약을 통해 정제된 형태로만 게시한다. 검토자에게 정제되지 않은 로컬 로그 검사를 요구해서는 안 되며, 정제된 요약 또는 외부 아티팩트 참조가 없는 로컬 증거 포인터는 여러 머신 간 영속적 증거로 취급하지 않는다.

### 승인 기록

사람의 승인이 필요한 작업은 승인 유형, 승인자, 범위, 이유, 타임스탬프, 관련 run ID 및 존재하는 경우 외부 승인 참조를 포함하는 구조화된 증거를 생성한다. 실행별 승인 기록은 `.ai-runs/<run-id>/approvals.json`에 저장하고 `ai/schemas/approval-record.schema.json`으로 검증한다.

승인 기록은 감사 기록이지 독립적인 권한 증명이 아니다. 에이전트는 `approvedBy: human`을 작성하여 승인을 만들어내서는 안 된다. 파괴적 작업, 운영 작업, secret 작업, deployment 및 그 밖의 승인 의존 작업은 실행 전에 실제 host-runtime 또는 외부 인간 승인 이벤트가 여전히 필요하며, 기록은 그 이벤트와 범위를 포착한다.

정책 위반에는 `ai/schemas/policy-violation.schema.json`으로 검증되는 append-only 이벤트 파일을 사용한다. 각 이벤트에는 유형, 설명, 탐지 시각, 차단 상태, run ID 및 관련 명령 또는 도구 컨텍스트를 기록한다. `run.json`에는 요약과 포인터만 두어 하나의 공유 violations 배열을 동시에 다시 쓰지 않도록 한다.

## 실행 흐름

1. `PRE_TASK`는 cache된 상태를 읽고 fingerprint를 검증한다.
2. 에이전트는 context-map route와 관련 skill을 선택한다.
3. `PRE_EDIT`는 쓰기 전에 소유권을 검증한다.
4. 명령은 `command-runner.sh`를 통해 registry ID로 요청한다.
5. `PRE_COMMAND`는 허용·차단하거나 기록된 이유를 요구한다.
6. `POST_COMMAND`는 상세 성공 또는 실패 증거를 실행 디렉터리 아래에 영속화하고 워크플로 cache의 정제된 요약 포인터만 갱신한다.
7. 검증은 `verification-runner`와 `verify-level.sh`를 통해 실행한다.
8. 실패는 재실행 전에 `failure-triage`를 거쳐야 한다.
9. `PRE_DONE_CLAIM` 및 `done-claim-check.sh`는 완료 증거를 검증한다.

## 저장소 intake

초기 intake는 읽기 전용이며 비파괴적이다. 추적된 저장소 경로, Gradle wrapper/configuration, 애플리케이션 configuration, test 및 기존 워크플로 문서를 검사한다. 등록되지 않은 build, database, deployment 또는 production 명령은 실행하지 않는다.

현재 intake 증거는 다음 사실 신뢰도 및 기능 구성 상태를 뒷받침한다.

- `CONFIRMED`: Gradle Wrapper는 package/build 진입점이다.
- `CONFIRMED`: Java 21 및 Spring Boot가 구성되어 있다.
- `CONFIRMED`: MySQL, Redis 및 Kafka 개발 서비스가 포트 3306, 6379 및 9092에 선언되어 있다.
- `INFERRED`: 애플리케이션에 명시적인 server port가 없으므로 runtime 검증 전까지 8080은 추론이다.
- `CONFIGURED_UNVERIFIED`: Gradle `test` task에는 구성 증거가 있지만 이 설계 작업의 일부로 실행되지는 않았다.
- `NOT_CONFIGURED`: lint, 전용 integration-test, E2E, migration, seed 및 API-smoke 명령은 현재 정의되지 않았다.
- 정확한 registry argv가 성공적으로 실행되고 증거가 기록되기 전까지 어떤 명령도 `VERIFIED`로 표시하지 않는다.

## 스크립트 범위

- `repo-intake.sh`: 유효한 무효화 후 안정된 컨텍스트를 갱신한다.
- `workflow-gate.sh`: hook 검사를 실행한다.
- `command-runner.sh`: registry 명령을 실행하고 증거를 영속화한다.
- `verify-level.sh`: 검증 수준을 등록된 명령 ID에 매핑한다.
- `api-smoke.sh`: 구성된 base URL에 대해 선언된 HTTP case를 실행한다. endpoint case 또는 사전 조건이 없으면 `NOT_CONFIGURED`를 보고하여 검증 gate가 변경 유형별로 해당 결과를 `NOT_APPLICABLE` 또는 `BLOCKED`에 매핑하도록 한다.
- `done-claim-check.sh`: 기록된 완료 증거를 검증한다.

### 스크립트 종료 코드

모든 워크플로 스크립트는 공통 process exit-code 계약을 사용한다.

- `0`: `PASS`
- `1`: `FAIL`
- `2`: `BLOCKED`
- `3`: `NOT_CONFIGURED`
- `4`: `POLICY_VIOLATION`
- `5`: `INVALID_STATE`
- `6`: `NOT_APPLICABLE`
- `7`: `SKIPPED_WITH_REASON`

모든 스크립트는 schema 검증된 구조화 결과 JSON도 기록한다. 호출자는 stdout 텍스트를 파싱하여 상태를 추론해서는 안 된다. child 명령의 네이티브 process exit code는 `processExitCode`로 별도 저장한다. 0이 아닌 child exit는 워크플로 결과 `FAIL` 및 runner exit code `1`에 매핑하므로 child exit code를 워크플로 제어 코드와 혼동할 수 없다.

leaf check 스크립트는 위 상세 exit code를 반환할 수 있다. final gate 스크립트는 정책이 허용한 `NOT_APPLICABLE` 또는 `SKIPPED_WITH_REASON` leaf 결과를 전체 `PASS`로 변환한다. 그 외에는 차단하는 0이 아닌 결과를 보존한다. CI 및 네이티브 hook adapter는 모든 non-PASS leaf 결과가 실패해야 함을 의도적으로 요구하지 않는 한 원시 leaf check 대신 final gate 명령을 호출한다.

Bash 스크립트는 간단한 사람 대상 진입점으로 유지한다. JSON 파싱, hashing, 원자적 state 갱신, 구조화된 process 실행, 증거 작성 및 로그 정제는 해당 환경에 대해 runtime이 확인된 후에만 하나의 작은 helper runtime을 사용할 수 있다. 워크플로는 Python, Node.js, `jq` 또는 다른 선언되지 않은 의존성을 조용히 가정해서는 안 된다.

### helper runtime 사전 점검

JSON 파싱, hashing, schema 검증, 원자적 쓰기, 구조화된 실행 또는 로그 정제를 구현하기 전에 repository intake는 Python, Node.js, Java 또는 `jq` 같은 후보 helper runtime을 탐지한다. 선택한 runtime, 실행 파일 경로 또는 명령, 버전, 증거 및 환경별 상태는 `ai/project-state.json`에 기록한다.

runtime 상태는 지원 환경별로 별도 기록한다. Phase 1은 상태가 `CONFIRMED`인 로컬 승인 runtime을 요구한다. CI는 Phase 3까지 `UNKNOWN` 또는 `NOT_CONFIGURED`로 남을 수 있으며, 이 경우 CI 강제 적용은 로컬 gateway를 차단하지 않고 `BLOCKED`이다. 승인되고 사용 가능한 로컬 helper runtime이 없으면 영향을 받는 로컬 명령은 `NOT_CONFIGURED`로 실패한다. 스크립트는 취약한 Markdown 파싱이나 선언되지 않은 도구로 조용히 강등하거나 대체하지 않는다.

어떤 스크립트도 database reset/drop/truncate, production mutation, deployment, secret 변경 또는 대량 파괴 작업을 수행하지 않는다.

## 기존 문서 통합

기존 워크플로 문서는 전체 대체가 아니라 병합한다.

- `AGENTS.md`는 필수 시작 순서 및 gateway 규칙에 연결한다.
- `ai/document-routing.md`는 context-map route ID를 통해 routing한다.
- `ai/verification-levels.md`, `ai/qa-gate.md` 및 `ai/done-claim-template.md`는 실행 가능한 검증 및 done-claim 진입점을 참조한다.
- `ai/subagent-workflow.md`, issue 템플릿 및 work-log 템플릿은 context-map route, registry ID, cache key, 이전 증거 및 handoff 상태를 담는다.
- `docs/00-index.md`는 새 워크플로 기준 문서를 매핑한다.
- `docs/09-quality-operations-and-rules.md`는 hook 세부 사항을 중복하지 않고 실행 가능한 QA 강제 적용에 연결한다.
- 기능 템플릿은 명령을 만들어내는 대신 검증 ID를 참조한다.

## 실패 처리

- registry 항목 누락: 실행을 차단하고 repo intake 또는 승인된 registry 갱신을 통해 범위가 있는 탐색을 실행한다.
- 변경되지 않은 명령의 반복: 허용된 재실행 이유가 기록되지 않았다면 차단한다.
- 변경되지 않은 파일 읽기의 반복: cache를 재사용하거나 cache가 유효하지 않은 이유를 기록한다.
- 명령 실패: 실패 증거를 저장하고 triage 또는 명시적인 blocked 상태 전까지 계속 진행하지 못하도록 차단한다.
- 오래된 project state: 영향받는 섹션만 무효화한 뒤 범위가 있는 컨텍스트를 갱신한다.
- API 사전 조건 누락: NOT CONFIGURED 또는 BLOCKED를 보고하며 실제 API 검증을 주장하지 않는다.
- 정제되지 않았거나 민감할 수 있는 증거: 게시, done-claim 포함 및 commit을 차단한다.
- runtime 우회: 저장소 강제 적용이 우회되었음을 보고하며, 네이티브 runtime adapter는 별도로 추가할 수 있다.

### API smoke 필요성

`NOT_CONFIGURED`가 항상 관련 없는 작업을 실패시키는 것은 아니다. 비API 변경의 경우 API smoke는 `NOT_APPLICABLE`로 보고하고 이유와 함께 `N/A`로 표시할 수 있다. API, auth, permission, persistence 또는 외부에 보이는 동작 변경의 경우 실행 가능한 API case 또는 사전 조건이 누락되면 `PASS`가 아닌 `BLOCKED`이다. endpoint case, infrastructure 또는 server 사전 조건이 없을 때 에이전트는 실제 API 검증을 주장해서는 안 된다.

### 게이트 결과 매핑

모든 검증 및 완료 gate는 동일한 매핑을 적용한다.

- 적용 가능한 명령이 존재하고 성공: `PASS`
- 적용 가능한 명령이 존재하지만 실행에 실패: `FAIL`
- 필수 기능이 없거나 사용할 수 없음: 명령 결과 `NOT_CONFIGURED`, gate 결과 `BLOCKED`
- 기능이 분류된 작업과 무관함: `NOT_APPLICABLE` (`N/A`로 표시)
- 정책이 건너뛰기를 명시적으로 허용하고 이유를 기록함: `SKIPPED_WITH_REASON`

누락된 registry 항목은 기능 탐색 시 `NOT_CONFIGURED`이다. 현재 작업에 필요하면 검증 또는 완료 gate는 전체 결과를 `BLOCKED`로 변환한다. 에이전트는 `NOT_CONFIGURED`를 조용한 skip으로 바꿀 수 없다.

## 검증 전략

1. 정적 검사는 필수 파일, heading, registry ID, hook link 및 실행 가능한 스크립트 권한을 검증한다.
2. 스크립트 계약 test는 임시 fixture를 사용하여 알 수 없는 명령, 파괴적 명령, 근거 없는 재실행, 숨겨진 실패 및 증거 없는 done claim이 거부되는지 확인한다.
3. 저장소 검증에는 먼저 증거와 함께 등록된 명령만 사용한다.
4. API smoke는 실행 가능한 endpoint 및 해당 case가 생길 때까지 차단된 상태로 유지된다.
5. 최종 설정 보고서는 구현된 저장소 gate와 host-runtime 강제 적용의 공백을 구분한다.

## 제공 단계

### Phase 1A: 상태 및 registry 골격

#### Phase 1A-1: 스키마 및 정식 상태

- registry, state, run, command result, done claim, approval record 및 policy violation을 위한 schema와 폐쇄형 enum 계약을 추가한다.
- 초기 정식 `ai/command-registry.json` 및 `ai/project-state.json` 골격을 추가한다.
- Phase 3 CI 가용성을 요구하지 않고 로컬 및 CI helper-runtime 상태를 기록한다.
- 증거가 있는 명령만 등록한다. `test`는 `CONFIGURED_UNVERIFIED`, 지원하지 않는 기능은 `NOT_CONFIGURED`로 표시한다.
- 애플리케이션 port는 확인됨이 아닌 `INFERRED`로 기록한다.

#### Phase 1A-2: 사람이 읽을 수 있는 요약

- 별도의 사람 정책 및 생성 요약 섹션을 갖는 `ai/command-registry.md`와 `ai/project-state.md`를 추가한다.
- 생성 섹션 소유권 marker를 추가하고 생성 상태의 수동 편집을 금지한다.
- `NOT_APPLICABLE`에서 `N/A`를 포함하는 JSON-to-Markdown 표시 매핑을 정의한다.
- 오래되었거나 모순되는 생성 요약을 탐지하는 fixture를 추가한다.

#### Phase 1A-3: 저장소 통합

- `.ai-runs/`를 `.gitignore`에 추가한다.
- `AGENTS.md`를 정식 JSON 상태, 사람이 읽는 요약 및 supported-path 강제 적용 경계에 연결한다.
- 유효, 잘못된 형식, 알 수 없는 버전 및 유효하지 않은 enum 상태를 위한 schema-validation fixture를 추가한다.
- Phase 1A가 명령 실행 gateway 또는 제품 동작을 추가하지 않음을 검증한다.

### Phase 1B: 명령 gateway

#### Phase 1B-1: registry 해석 및 매개변수 검증

- 승인된 helper-runtime preflight를 구현하고 사용할 수 없으면 fail closed한다.
- schema에 유효한 JSON에서 registry ID를 해석하고 `eval` 또는 shell 확장 없이 argv 배열을 구성한다.
- 폐쇄형 parameter schema, 해석되지 않은 placeholder 검사, classification 및 prerequisite를 강제한다.

#### Phase 1B-2: 명령 실행 및 증거

- `scripts/ai/command-runner.sh` 및 `scripts/ai/workflow-gate.sh`를 추가한다.
- pre/post 명령 gate, 공유 exit code, 구조화된 결과 및 실행별 증거를 추가한다.
- secret-safe 수집, 승인 감사 기록, policy-violation 이벤트 및 정제된 요약을 추가한다.

#### Phase 1B-3: 완료 게이트 및 계약 테스트

- `scripts/ai/done-claim-check.sh` 및 final-gate leaf-result 집계를 추가한다.
- 유효하지 않은 상태, 알 수 없는 명령, 안전하지 않은 매개변수, 근거 없는 재실행, 숨겨진 실패 및 누락된 증거를 위한 fixture 기반 test를 추가한다.
- Phase 1B는 완전한 host-tool 가로채기가 아니라 정책, 감사 및 supported-path 강제 적용으로 계속 기술한다.

### Phase 2: 워크플로 재사용 및 완료 게이트

#### Phase 2A: 컨텍스트 intake 및 캐시 제어

- 저장소 context map, 범위가 지정된 repo intake, project-state 갱신 및 command-discovery 갱신 흐름을 추가한다.
- cache 정책, tool-call 정책, resource budget, fingerprint 및 보수적인 무효화를 추가한다.

#### Phase 2B: 스킬 및 handoff 재사용

- repo-intake, command-runner, verification-runner, API-smoke, failure-triage, docs-sync 및 review-gate skill을 추가한다.
- agent handoff 상태를 추가하고 재사용 가능한 컨텍스트를 issue 요약 및 work log에 연결한다.

#### Phase 2C: 검증 및 문서 통합

- verification-level, API-smoke, failure-triage, review 및 done-claim 워크플로 진입점을 추가한다.
- 기존 QA, routing, issue, work-log 및 feature-template 문서를 실행 가능한 gate에 연결한다.
- 변경 유형별 `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED` 및 `FAIL` 매핑을 검증한다.

### Phase 3: 호스트 강제 적용

#### Phase 3A: 네이티브 runtime adapter

- 지원되는 경우 command, file-read, search 및 tool-call hook용 호스트별 adapter를 추가한다.
- 저장소 전용 강제 적용으로는 이전에 감사할 수 있었지만 가로챌 수 없었던 우회 시도를 기록하고 노출한다.

#### Phase 3B: CI 게이트 및 영속적 증거

- CI final gate, schema 검증 및 generated-summary 일관성 검사를 추가한다.
- 정제된 증거 아티팩트를 게시하고 그 참조를 검토 가능한 완료 보고서에 연결한다.

각 phase는 독자적으로 사용 가능하고 test 가능해야 한다. Phase 3 지원이 존재하기 전에는 repository-gateway 강제 적용을 host tool 호출의 완전한 가로채기라고 기술하지 않는다.

각 subphase는 실행 전에 자체 문서화 명세 또는 범위가 제한된 implementation-plan 섹션을 받는다. 상위 phase를 하나의 실행 작업으로 취급하지 않는다.

## 성공 기준

- 저장소 구조와 읽기 route는 `context-map.md`에 저장된다.
- 알려진 명령과 지원하지 않는 명령 범주는 `command-registry.json`의 정식 정보이며 `command-registry.md`에 요약된다.
- 모든 실행 가능한 JSON 상태는 schema version을 가지며 유효하지 않거나 호환되지 않으면 거부된다.
- 프로젝트 사실, 기능 구성, 워크플로 결과 및 스크립트 결과는 별도 폐쇄형 enum을 사용한다.
- cache 및 tool-call 무효화 규칙은 근거 없는 재탐색을 방지한다.
- 반복 절차는 집중된 skill로 표현한다.
- 필수 전이는 실행 가능한 gate를 호출한다.
- 명령 재실행 및 실패한 명령의 계속 진행은 증거 규칙으로 차단된다.
- 하위 에이전트 handoff에는 재사용 가능한 컨텍스트와 이전 결과가 포함된다.
- 완료 주장은 필요한 기록 검증이 없으면 실패한다.
- 원시 명령, `eval`, 정제되지 않은 증거 게시 및 지원되지 않는 API-smoke 주장은 차단된다.
- 기존 워크플로 및 QA 문서는 모순되는 중복 규칙 없이 새로운 실행 구조를 가리킨다.

## 승인 참고

이 설계는 AI Workflow Enforcement의 기준선으로 승인되었다. 구현은 Phase 1A로 시작하며 제품 기능 작업으로 확장해서는 안 된다.

phase 구현은 다음 제약을 보존한다.

1. 실행 가능한 워크플로 상태의 정식 출처는 JSON이다.
2. Markdown 요약은 독립적인 기준 문서가 아니다.
3. 유효하지 않은 schema 상태는 fail closed한다.
4. 명령은 registry ID와 argv 배열로 표현한다.
5. 원시 shell 명령 실행, 검사되지 않은 동적 인수 및 `eval`은 금지된다.
6. 실행별 원시 증거는 `.ai-runs/<run-id>/` 아래에 저장하며 Git이 무시한다.
7. 검토 가능한 증거는 게시 전에 정제한다.
8. 승인 기록은 감사 기록일 뿐이며 승인을 만들어낼 수 없다.
9. 저장소 gateway 강제 적용은 네이티브 adapter 또는 CI gate가 존재할 때까지 supported-path 강제 적용이다.
10. 제품 기능, production 작업, deployment, 파괴적 database 작업, migration, seed 및 secret 변경은 범위 밖으로 유지된다.

## 비목표

- 제품 기능 구현.
- production, deployment, 파괴적 database, migration 또는 seed 작업 실행.
- 네이티브 runtime adapter 없이 저장소 스크립트가 모든 host tool 호출을 가로챌 수 있다고 주장.
- 기존 문서 전체를 생성 파일로 대체.
