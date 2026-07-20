# AI 워크플로 강제 적용 Phase 1A 문서화 명세

## 상태

- 명세 상태: Phase 1A 구현 계획 수립 승인됨
- Owning feature: none
- Baseline: `docs/superpowers/specs/2026-07-10-ai-workflow-enforcement-design.md`
- Scope: Phase 1A-1, Phase 1A-2, and Phase 1A-3 only
- 이 명세의 검증 레벨: Level 0 문서 검토

## 목표

Phase 1A가 추가할 기계 판독 가능 워크플로 상태의 문서화 계약을 만든다. Phase 1A는 스키마, 정식 JSON 골격, 사람이 읽을 수 있는 요약, 저장소 통합 및 정적 fixture를 확립한다. 프로젝트 명령을 실행하거나 command gateway를 구현하지 않는다.

## 전역 제약 조건

1. 실행 가능한 워크플로 상태의 정식 출처는 JSON이다.
2. Markdown에는 사람을 위한 정책과 정식 JSON의 요약이 포함되며, 독립적인 기준 문서가 아니다.
3. 모든 실행 가능한 JSON은 JSON Schema Draft 2020-12, `schemaVersion: 1`, 저장소 상대 forward-slash 경로 및 이 명세가 확장 데이터를 명시적으로 허용하지 않는 한 `additionalProperties: false`를 사용한다.
4. 타임스탬프는 ISO-8601 UTC 문자열을 사용한다.
5. Phase 1A는 정적 파일 검사만 수행한다. Gradle, 애플리케이션, 데이터베이스, 인프라, API, migration, seed, lint, test 또는 helper-runtime 명령을 실행하지 않는다.
6. 성공적인 실행 증거 없이는 어떤 기능도 `VERIFIED`로 표시하지 않는다.
7. command gateway, command runner, hook 스크립트, 증거 수집, 자동 Markdown 생성 및 자동 schema 검증은 Phase 1B 이후 범위다.
8. Phase 1B는 `jsonschema` 라이브러리와 Draft 2020-12 검증을 사용하는 Python 3를 대상으로 하지만, Phase 1A는 Python을 실행하거나 설치되어 있다고 가정하지 않는다.
9. Phase 1A 및 Phase 1B는 `["./gradlew", "test"]`와 같은 POSIX/Bash Gradle argv만 지원한다. 네이티브 `gradlew.bat` 지원은 미래 범위이며 `NOT_CONFIGURED`이다.
10. Phase 1B gateway가 runtime 증거를 기록하기 전까지 AI 에이전트는 프로젝트 build, test, server, Docker, HTTP, migration, seed 또는 infrastructure 명령을 실행하지 않는다.
11. Phase 1A의 작성 및 검토에 필요한 정적 파일 검사, 문서 편집 및 호스트 승인 버전 관리 작업은 관리 워크플로 작업이며 프로젝트 명령 검증 증거가 아니다.

## 단계 경계

### Phase 1A-1: 스키마 및 정식 상태

닫힌 스키마를 정의하고 초기 기준 명령 레지스트리와 프로젝트 상태를 만든다.

### Phase 1A-2: 사람이 읽을 수 있는 요약

사람이 편집할 수 있는 정책 섹션, 생성 요약 소유 marker, bootstrap 요약 규칙, 표시 매핑을 정의한다.

### Phase 1A-3: 저장소 통합

로컬 실행 증거를 무시하고 `AGENTS.md`를 새 상태 계약에 연결하며 이후 자동 검증을 위한 정적 fixture 문서를 추가한다.

## 생성할 파일

### 명세 아티팩트

| 경로 | 책임 |
|---|---|
| `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md` | 승인된 Phase 1A 상태 및 레지스트리 계약 |

### 스키마

| 경로 | 책임 |
|---|---|
| `ai/schemas/command-registry.schema.json` | 명령 및 사용 불가 capability 레코드 검증 |
| `ai/schemas/project-state.schema.json` | 프로젝트 사실, 경로, 포트, 환경, 런타임 가용성 검증 |
| `ai/schemas/run.schema.json` | 향후 실행별 증거 색인 정의 |
| `ai/schemas/command-result.schema.json` | 향후 명령 실행 결과 정의 |
| `ai/schemas/done-claim.schema.json` | 향후 기계 판독 가능한 완료 주장 정의 |
| `ai/schemas/approval-record.schema.json` | 향후 승인 감사 레코드 정의 |
| `ai/schemas/policy-violation.schema.json` | 향후 정책 위반 이벤트 정의 |

### 정식 상태 및 사람이 읽는 요약

| 경로 | 책임 |
|---|---|
| `ai/command-registry.json` | 기준 명령 capability 레지스트리 |
| `ai/project-state.json` | 기준 프로젝트 상태 및 정적 intake 사실 |
| `ai/command-registry.md` | 사람용 정책 메모 및 명령 레지스트리 요약 |
| `ai/project-state.md` | 사람용 정책 메모 및 프로젝트 상태 요약 |

### 정적 검증 fixture

| 경로 | 예상 용도 |
|---|---|
| `ai/fixtures/phase-1a/valid/command-registry.json` | 유효한 레지스트리 fixture |
| `ai/fixtures/phase-1a/valid/project-state.json` | 유효한 프로젝트 상태 fixture |
| `ai/fixtures/phase-1a/valid/run.json` | 유효한 향후 run-index fixture |
| `ai/fixtures/phase-1a/valid/command-result.json` | 유효한 향후 command-result fixture |
| `ai/fixtures/phase-1a/valid/done-claim.json` | 유효한 향후 done-claim fixture |
| `ai/fixtures/phase-1a/valid/approval-record.json` | 유효한 향후 승인 감사 fixture |
| `ai/fixtures/phase-1a/valid/policy-violation.json` | 유효한 향후 정책 위반 fixture |
| `ai/fixtures/phase-1a/invalid/command-registry-invalid-enum.json` | 알 수 없는 상태 값 거부 |
| `ai/fixtures/phase-1a/invalid/command-registry-raw-command.json` | argv 대신 원시 명령 문자열 거부 |
| `ai/fixtures/phase-1a/invalid/command-registry-unknown-version.json` | 지원하지 않는 스키마 버전 거부 |
| `ai/fixtures/phase-1a/invalid/project-state-missing-required.json` | 필수 상태 누락 거부 |
| `ai/fixtures/phase-1a/invalid/project-state-invalid-confidence.json` | 임의로 만든 confidence 값 거부 |
| `ai/fixtures/phase-1a/invalid/run-invalid-result.json` | 임의로 만든 워크플로 결과 거부 |
| `ai/fixtures/phase-1a/invalid/command-result-missing-process-exit.json` | 불완전한 실행 증거 거부 |
| `ai/fixtures/phase-1a/invalid/approval-record-missing-reference.json` | 감사 참조 필드 없는 승인 주장 거부 |
| `ai/fixtures/phase-1a/invalid/policy-violation-invalid-type.json` | 임의로 만든 정책 위반 유형 거부 |
| `ai/fixtures/phase-1a/generated-summary/command-registry-stale.md` | 향후 validator가 오래된 생성 콘텐츠를 감지해야 함 |
| `ai/fixtures/phase-1a/generated-summary/project-state-stale.md` | 향후 validator가 모순되는 생성 콘텐츠를 감지해야 함 |

fixture는 Phase 1A의 정적 test vector다. Phase 1B까지 validator나 fixture runner를 구현하지 않는다.

## 수정할 파일

| 경로 | 필수 변경 |
|---|---|
| `.gitignore` | 저장소 루트 무시 디렉터리로 `.ai-runs/` 추가 |
| `AGENTS.md` | 기준 상태 읽기 순서, Phase 1A 상태 의미, 강제 적용 경계 문구 추가 |

Phase 1A에서는 product source, test source, Gradle 구성, runtime 구성, 기능 명세, ADR, QA gate 또는 command script를 수정하지 않는다.

## 폐쇄형 enum 정의

### 사실 신뢰도

허용 값:

- `CONFIRMED`: 정적 저장소 증거가 직접 뒷받침함
- `INFERRED`: runtime 증거가 없는 합리적 기본값 또는 추론
- `UNKNOWN`: 검사하지 않았거나 현재 증거로 알 수 없음
- `STALE`: 이전에 알려졌으나 관련 변경으로 무효화됨
- `UNCERTAIN`: 검사한 증거가 충돌하거나 불완전함

### 기능 구성

허용 값:

- `UNKNOWN`: capability가 확정적으로 발견되지 않음
- `CONFIGURED_UNVERIFIED`: 정적 구성은 있지만 성공한 실행 증거가 없음
- `VERIFIED`: 정확히 등록된 argv가 성공적으로 실행되었고 증거가 기록됨
- `NOT_CONFIGURED`: 현재 지원되는 명령 또는 메커니즘이 정의되지 않음
- `STALE`: 이전 구성 증거가 무효화됨
- `UNCERTAIN`: 구성 증거가 불완전하거나 모순됨

### 워크플로 결과

허용 값:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_CONFIGURED`
- `NOT_APPLICABLE`
- `SKIPPED_WITH_REASON`

Markdown은 `NOT_APPLICABLE`을 `N/A`로 표시한다. JSON에는 `N/A`를 저장하지 않는다.

### 스크립트 제어 결과

허용 값:

- `PASS`
- `FAIL`
- `BLOCKED`
- `NOT_CONFIGURED`
- `POLICY_VIOLATION`
- `INVALID_STATE`
- `NOT_APPLICABLE`
- `SKIPPED_WITH_REASON`

### 명령 분류

허용 값:

- `SAFE`
- `RISKY`
- `DESTRUCTIVE`
- `UNAVAILABLE`

### 환경 종류

허용 값:

- `LOCAL`
- `CI`

### 증거 종류

허용 값:

- `STATIC_FILE`
- `RUNTIME_COMMAND`
- `EXTERNAL_APPROVAL`
- `CI_ARTIFACT`

Phase 1A는 `STATIC_FILE` 증거만 사용한다.

### 승인 유형

허용 값:

- `REGISTRY_UPDATE`
- `RISKY_COMMAND`
- `DESTRUCTIVE_COMMAND`
- `PRODUCTION_OPERATION`
- `DEPLOYMENT`
- `SECRET_CHANGE`

### 정책 위반 유형

허용 값:

- `RAW_COMMAND_ATTEMPT`
- `UNREGISTERED_COMMAND`
- `UNSAFE_PARAMETER`
- `MISSING_RERUN_REASON`
- `DESTRUCTIVE_WITHOUT_APPROVAL`
- `UNSCRUBBED_EVIDENCE`
- `COMPLETION_WITHOUT_EVIDENCE`
- `DIRECT_TOOL_BYPASS`

## JSON Schema 계약

모든 스키마에는 `$schema`, `$id`, `schemaVersion`이 필요하다. 모든 객체는 `additionalProperties: false`를 설정한다. null 허용 필드는 `"type": ["string", "null"]`처럼 명시적 union을 사용하며, 누락 데이터는 임의로 만든 문자열로 표현하지 않는다.

스키마 파일은 다음 패턴의 안정적인 URN을 사용한다.

```text
urn:sparta-ch6-advanced:ai-workflow:schema:<schema-name>:v1
```

예를 들어 `command-registry.schema.json`은 `$id: urn:sparta-ch6-advanced:ai-workflow:schema:command-registry:v1`을 사용한다. 기준 instance 파일은 `$schema: ./schemas/command-registry.schema.json`, `$id: ai/command-registry.json`처럼 저장소 상대 `$schema` 경로와 저장소 상대 `$id`를 사용한다. 공개 HTTP 스키마 URL은 사용하지 않는다.

### `command-registry.schema.json`

최상위 필수 필드:

- `$schema`
- `$id`
- `schemaVersion`
- `updatedAt`
- `commands`

각 명령 레코드에 필요:

- `id`: 고유 dotted 식별자
- `purpose`: 사람이 읽을 수 있는 capability 설명
- `configurationStatus`: Capability Configuration 열거형
- `classification`: Command Classification 열거형
- `argv`: 비어 있지 않은 문자열 배열 또는 `null`
- `workingDirectory`: 저장소 상대 경로
- `parameters`: `allowed` 및 null 허용 `schema`를 가진 객체
- `prerequisites`: capability 또는 service 식별자 배열
- `evidence`: 증거 레코드 배열
- `inputPaths`: 저장소 상대 경로 또는 glob 배열
- `lastVerifiedAt`: ISO-8601 UTC 문자열 또는 `null`
- `notes`: 문자열 배열

조건부 규칙:

- `CONFIGURED_UNVERIFIED`, `VERIFIED`에는 비어 있지 않은 argv와 최소 하나의 증거 레코드가 필요하다.
- `VERIFIED`에는 null이 아닌 `lastVerifiedAt`과 `RUNTIME_COMMAND` 증거가 필요하다.
- `NOT_CONFIGURED`에는 `argv: null`, `classification: UNAVAILABLE`, `lastVerifiedAt: null`이 필요하다.
- `UNKNOWN`, `STALE`, `UNCERTAIN`은 실행 가능한 것으로 취급할 수 없다.
- 원시 shell 명령 문자열, shell pipeline, `eval` 표현식은 표현할 수 없다.

### `project-state.schema.json`

최상위 필수 필드:

- `$schema`
- `$id`
- `schemaVersion`
- `updatedAt`
- `project`
- `facts`
- `importantPaths`
- `ports`
- `environments`
- `helperRuntimes`
- `commandRegistryRef`
- `cacheInvalidationInputs`

필수 프로젝트 필드:

- `name`
- `productType`
- `mainLanguage`
- `framework`
- `buildSystem`

각 fact에는 `id`, `value`, `confidence`, `evidence`, `observedAt`이 필요하다. 각 port에는 `service`, `value`, `confidence`, `evidence`가 필요하다. 각 helper-runtime 레코드에는 `environment`, `targetRuntime`, `detectedRuntime`, `configurationStatus`, `version`, `evidence`가 필요하다.

애플리케이션 port는 confidence `INFERRED`와 값 `8080`을 사용한다. helper runtime은 이후 승인된 preflight가 증거를 기록할 때까지 `UNKNOWN`으로 유지한다.

### `run.schema.json`

필수 필드:

- `$schema`, `$id`, `schemaVersion`
- `runId`, `taskKey`, `startedAt`, `endedAt`
- `workingDirectory`, `environment`
- `result`
- `commandResultRefs`, `approvalRefs`, `policyViolationRefs`, `evidenceRefs`
- `redactionApplied`

이 schema는 Phase 1A에서 정의되지만 Phase 1A는 `.ai-runs/<run-id>/run.json` 파일을 만들지 않는다.

### `command-result.schema.json`

필수 필드:

- `$schema`, `$id`, `schemaVersion`
- `runId`, `commandId`
- `startedAt`, `endedAt`
- `result`, `processExitCode`
- `argvHash`, `inputFingerprint`, `environmentFingerprint`
- `stdoutPath`, `stderrPath`
- `redactionApplied`, `reason`

`processExitCode`는 child process code를 보존한다. workflow control code로 재사용하지 않는다.

### `done-claim.schema.json`

필수 필드:

- `$schema`, `$id`, `schemaVersion`
- `runId`, `taskKey`, `generatedAt`
- `implementationStatus`, `overallResult`
- `checks`, `notRunItems`, `evidenceRefs`
- `unexpected500Status`, `unhandledExceptionStatus`
- `blockers`, `remainingRisks`

Phase 1A에서는 done-claim JSON을 만들지 않는다.

### `approval-record.schema.json`

필수 필드:

- `$schema`, `$id`, `schemaVersion`
- `approvalId`, `runId`
- `type`, `approver`, `scope`, `reason`
- `approvedAt`, `externalReference`

스키마는 approval record가 감사 레코드라고 명시한다. 로컬에 작성한 레코드는 독립적으로 작업을 승인할 수 없다.

### `policy-violation.schema.json`

필수 필드:

- `$schema`, `$id`, `schemaVersion`
- `violationId`, `runId`
- `type`, `description`, `detectedAt`
- `blocking`, `context`

Phase 1A에서는 policy-violation 이벤트를 만들지 않는다.

## 초기 `command-registry.json` 구조

초기 레지스트리는 실행 가능한 argv가 없더라도 capability 레코드를 포함한다. 아래 타임스탬프는 형태만 예시하며 구현은 실제 UTC 기록 시각을 사용한다.

Phase 1A/1B command profile은 POSIX/Bash 전용이다. `verify.unit`은 `["./gradlew", "test"]`를 사용한다. Native Windows `gradlew.bat` 실행 profile은 표현하지 않으며 향후 범위로 남는다. Windows의 Git Bash는 POSIX wrapper path가 동작할 때만 사용할 수 있으며 Phase 1A는 해당 조건을 테스트하지 않는다.

```json
{
  "$schema": "./schemas/command-registry.schema.json",
  "$id": "ai/command-registry.json",
  "schemaVersion": 1,
  "updatedAt": "2026-07-10T00:00:00Z",
  "commands": [
    {
      "id": "dependencies.install",
      "purpose": "Install or resolve project dependencies",
      "configurationStatus": "UNKNOWN",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [],
      "inputPaths": ["build.gradle", "settings.gradle", "gradle/**"],
      "lastVerifiedAt": null,
      "notes": ["Gradle resolves dependencies as part of tasks; no standalone install command is selected in Phase 1A."]
    },
    {
      "id": "server.dev",
      "purpose": "Start the development server",
      "configurationStatus": "UNKNOWN",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [],
      "inputPaths": ["build.gradle", "src/main/resources/application.yml"],
      "lastVerifiedAt": null,
      "notes": ["No runtime command is selected or executed in Phase 1A."]
    },
    {
      "id": "verify.build",
      "purpose": "Compile or build the project",
      "configurationStatus": "UNKNOWN",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [],
      "inputPaths": ["build.gradle", "settings.gradle", "gradle/**", "src/main/**", "src/test/**"],
      "lastVerifiedAt": null,
      "notes": ["No exact build argv is selected or executed in Phase 1A."]
    },
    {
      "id": "verify.unit",
      "purpose": "Run the configured Gradle test task",
      "configurationStatus": "CONFIGURED_UNVERIFIED",
      "classification": "SAFE",
      "argv": ["./gradlew", "test"],
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [
        {
          "kind": "STATIC_FILE",
          "path": "build.gradle",
          "claim": "The test task is configured to use JUnit Platform."
        },
        {
          "kind": "STATIC_FILE",
          "path": "gradlew",
          "claim": "The Gradle wrapper entry point exists."
        }
      ],
      "inputPaths": ["build.gradle", "settings.gradle", "gradle/**", "src/main/**", "src/test/**"],
      "lastVerifiedAt": null,
      "notes": ["Static configuration evidence exists; the command has not been executed."]
    },
    {
      "id": "verify.lint",
      "purpose": "Run lint checks",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No lint task or plugin is declared." }],
      "inputPaths": ["build.gradle"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "verify.integration",
      "purpose": "Run a dedicated integration-test command",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No dedicated integration-test task is declared." }],
      "inputPaths": ["build.gradle", "src/test/**"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "verify.e2e",
      "purpose": "Run end-to-end tests",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No E2E task or framework is declared." }],
      "inputPaths": ["build.gradle"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "verify.api-smoke",
      "purpose": "Run real HTTP API smoke verification",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": ["server.dev"],
      "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/java/com/ch6/cafe/CafeApplication.java", "claim": "No API-smoke case registry or runner exists." }],
      "inputPaths": ["src/main/**", "src/test/**", "docs/07-data-and-api-contracts.md"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "db.migration",
      "purpose": "Apply database migrations",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "No migration tool or task is declared." }],
      "inputPaths": ["build.gradle", "src/main/resources/**"],
      "lastVerifiedAt": null,
      "notes": []
    },
    {
      "id": "db.seed",
      "purpose": "Seed development or test data",
      "configurationStatus": "NOT_CONFIGURED",
      "classification": "UNAVAILABLE",
      "argv": null,
      "workingDirectory": ".",
      "parameters": { "allowed": false, "schema": null },
      "prerequisites": [],
      "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/resources/application.yml", "claim": "No seed command or seed configuration is declared." }],
      "inputPaths": ["src/main/resources/**", "src/test/resources/**"],
      "lastVerifiedAt": null,
      "notes": []
    }
  ]
}
```

## 초기 `project-state.json` 구조

```json
{
  "$schema": "./schemas/project-state.schema.json",
  "$id": "ai/project-state.json",
  "schemaVersion": 1,
  "updatedAt": "2026-07-10T00:00:00Z",
  "project": {
    "name": "sparta-ch6-advanced",
    "productType": "Spring Boot backend API assignment",
    "mainLanguage": "Java 21",
    "framework": "Spring Boot 4.1.0",
    "buildSystem": "Gradle Wrapper 9.0.0"
  },
  "facts": [
    {
      "id": "test.framework",
      "value": "JUnit Platform via Spring Boot Test",
      "confidence": "CONFIRMED",
      "evidence": [{ "kind": "STATIC_FILE", "path": "build.gradle", "claim": "Spring Boot Test is declared and the test task uses JUnit Platform." }],
      "observedAt": "2026-07-10T00:00:00Z"
    },
    {
      "id": "database.primary",
      "value": "MySQL",
      "confidence": "CONFIRMED",
      "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/resources/application.yml", "claim": "The primary datasource uses MySQL." }],
      "observedAt": "2026-07-10T00:00:00Z"
    }
  ],
  "importantPaths": [
    { "purpose": "Application source", "path": "src/main/java" },
    { "purpose": "Tests", "path": "src/test" },
    { "purpose": "Project documentation", "path": "docs" },
    { "purpose": "Feature specifications", "path": "specs" },
    { "purpose": "Architecture decisions", "path": "adr" },
    { "purpose": "AI workflow policy", "path": "ai" }
  ],
  "ports": [
    { "service": "application", "value": 8080, "confidence": "INFERRED", "evidence": [{ "kind": "STATIC_FILE", "path": "src/main/resources/application.yml", "claim": "No explicit server.port is configured; 8080 is the Spring Boot default inference." }] },
    { "service": "mysql", "value": 3306, "confidence": "CONFIRMED", "evidence": [{ "kind": "STATIC_FILE", "path": "docker-compose.yml", "claim": "MySQL maps port 3306." }] },
    { "service": "redis", "value": 6379, "confidence": "CONFIRMED", "evidence": [{ "kind": "STATIC_FILE", "path": "docker-compose.yml", "claim": "Redis maps port 6379." }] },
    { "service": "kafka", "value": 9092, "confidence": "CONFIRMED", "evidence": [{ "kind": "STATIC_FILE", "path": "docker-compose.yml", "claim": "Kafka maps port 9092." }] }
  ],
  "environments": [
    { "kind": "LOCAL", "configurationStatus": "UNKNOWN", "notes": ["Python 3 is the Phase 1B target, but no runtime preflight is executed in Phase 1A."] },
    { "kind": "CI", "configurationStatus": "NOT_CONFIGURED", "notes": ["No CI workflow exists; CI enforcement is Phase 3 scope."] }
  ],
  "helperRuntimes": [
    { "environment": "LOCAL", "targetRuntime": "Python 3", "detectedRuntime": null, "configurationStatus": "UNKNOWN", "version": null, "evidence": [] },
    { "environment": "CI", "targetRuntime": "Python 3", "detectedRuntime": null, "configurationStatus": "NOT_CONFIGURED", "version": null, "evidence": [] }
  ],
  "commandRegistryRef": "ai/command-registry.json",
  "cacheInvalidationInputs": [
    "build.gradle",
    "settings.gradle",
    "gradle/wrapper/gradle-wrapper.properties",
    "docker-compose.yml",
    "src/main/resources/application.yml",
    "src/test/resources/application-test.yml",
    ".github/**"
  ]
}
```

이 명세의 예시 타임스탬프는 설명용이다. Phase 1A 구현은 프로젝트 명령을 실행하지 않고 실제 UTC 시각을 기록한다.

## Markdown 요약 규칙

`ai/command-registry.md`와 `ai/project-state.md`는 모두 다음 소유권 구조를 사용한다.

```md
# 문서 제목

## 사람이 작성하는 정책 참고

Human-editable policy and interpretation rules.

<!-- GENERATED:START source=ai/example.json -->
## 생성된 상태 요약

Bootstrap summary derived from the canonical JSON in the same reviewed change.
<!-- GENERATED:END source=ai/example.json -->
```

규칙:

1. Human Policy Notes는 직접 편집할 수 있다.
2. 생성 marker 사이의 콘텐츠는 기준 JSON과 독립적으로 편집해서는 안 된다.
3. Phase 1A에서는 동일 변경의 JSON에서 초기 요약을 수동 bootstrap하고 정확한 일치를 검토한다.
4. 자동 생성 및 검증은 Phase 1B 이후로 미룬다.
5. 요약에는 기준 경로, 스키마 버전, 갱신 시각, 상태, 증거 경로를 표시해야 한다.
6. `NOT_APPLICABLE`은 `N/A`로 표시하고, 나머지 enum 값은 변경 없이 표시한다.
7. 불일치는 먼저 기준 JSON을 갱신한 뒤 요약을 새로 고쳐 해결한다.
8. Markdown 표는 실행 가능한 상태로 절대 파싱하지 않는다.

생성 섹션에는 다음 Phase 1A bootstrap 고지를 포함한다.

```md
This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.
```

### `command-registry.md` Generated Summary Columns

- ID
- Purpose
- Configuration Status
- Classification
- Argv Display
- Evidence
- Last Verified

`argv: null`에는 `configurationStatus`에 따라 `NOT CONFIGURED` 또는 `UNKNOWN`을 표시하며 명령을 임의로 만들지 않는다.

### `project-state.md` Generated Summary Sections

- Project Summary
- Important Paths
- Known Ports
- Environment State
- Helper Runtime State
- Command Registry Reference
- Cache Invalidation Inputs

애플리케이션 port는 `8080 (INFERRED)`로 표시해야 한다.

## `.gitignore` 통합

전용 AI 워크플로 섹션 아래에 다음 저장소 루트 항목을 추가한다.

```gitignore
### AI Workflow Local Evidence ###
.ai-runs/
```

규칙:

- 디렉터리를 재귀적으로 무시한다.
- 원시 로그를 커밋하는 negation 규칙을 추가하지 않는다.
- 검토 가능한 증거는 정제된 작업 로그, 완료 보고서 또는 향후 CI 산출물에 둔다.
- Phase 1A는 `.ai-runs/`를 만들지 않는다.

## `AGENTS.md` 추가 사항

**First Rule** 뒤에 다음 section을 추가한다.

```md
## 필수 워크플로 상태

저장소 구조, 명령, port, 환경 또는 검증 capability를 다시 탐색하기 전에 다음을 읽는다.

1. `ai/project-state.json` - canonical project state
2. `ai/command-registry.json` - canonical command capability registry
3. `ai/project-state.md` and `ai/command-registry.md` - human policy and summaries

JSON이 기준 문서다. Markdown 요약은 JSON을 재정의하거나 모순되어서는 안 된다.

Phase 1A는 상태와 레지스트리 계약만 제공한다. command gateway, 네이티브 도구 interception 또는 CI 강제 적용을 제공하지 않는다. Phase 1A를 완전한 명령 강제 적용으로 설명하지 않는다.

Phase 1A 작업 중에는 프로젝트 명령을 실행하지 않는다. `verify.unit`은 `CONFIGURED_UNVERIFIED`로 유지하고 lint, 전용 integration test, E2E, migration, seed, API smoke는 `NOT_CONFIGURED`로 유지하며 애플리케이션 port 8080은 `INFERRED`로 유지한다.

Phase 1B gateway가 존재할 때까지 AI 에이전트는 Gradle, application server, Docker Compose, HTTP/API, migration, seed 또는 infrastructure 명령을 직접 실행해서는 안 된다. AI 에이전트에는 임시 직접 명령 예외가 없다. 정적 파일 검사, 문서 편집, 호스트 승인 버전 관리 작업은 허용되는 관리 워크플로 작업으로 유지한다.

AI 워크플로 밖에서 사람이 수동으로 실행한 명령은 레지스트리 항목을 `VERIFIED`로 만들지 않고 워크플로 증거로 계산하지 않으며 에이전트가 통과한 검사로 보고해서는 안 된다. Phase 1B command-runner 증거만 항목을 `VERIFIED`로 전환할 수 있다.

`NOT_CONFIGURED`, `UNKNOWN`, `STALE`, `UNCERTAIN` 상태의 명령은 실행할 수 없다. 기록된 런타임 증거 없이는 어떤 명령도 `VERIFIED`로 표시할 수 없다.
```

기존 Document Map에 새 상태 파일 4개와 schema 디렉터리도 추가한다. Phase 1B까지 command-runner 지침을 추가하지 않는다.

## Phase 1A 완료 기준

Phase 1A는 다음을 모두 만족할 때만 완료다.

- [ ] 일곱 스키마가 모두 존재하며 Draft 2020-12, `schemaVersion: 1`, 닫힌 객체, 이 명세의 enum을 사용한다.
- [ ] `ai/command-registry.json`, `ai/project-state.json`이 문서 검토로 각 스키마를 준수한다.
- [ ] `verify.unit`이 argv `./gradlew test` 및 정적 증거와 함께 `CONFIGURED_UNVERIFIED`다.
- [ ] 네이티브 `gradlew.bat` 실행은 Phase 1A에 없으며 향후 범위 / `NOT_CONFIGURED`로 기록된다.
- [ ] lint, 전용 integration test, E2E, migration, seed, API smoke가 `argv: null`과 함께 `NOT_CONFIGURED`다.
- [ ] 어떤 명령이나 capability도 `VERIFIED`로 표시하지 않는다.
- [ ] 애플리케이션 port 8080이 `INFERRED`다.
- [ ] Python 3가 Phase 1B 대상 runtime으로 기록되며, 명령 실행 없이 기존 정적 증거가 달리 증명하지 않는 한 로컬 가용성은 `UNKNOWN`, CI는 `NOT_CONFIGURED`로 유지된다.
- [ ] Markdown 파일에 Human Policy Notes와 생성 marker가 있으며 bootstrap 요약은 기준 JSON과 일치한다.
- [ ] `.ai-runs/`를 무시하고 원시 증거를 커밋하지 않는다.
- [ ] `AGENTS.md`가 기준 읽기 순서와 Phase 1A 강제 적용 경계를 명시한다.
- [ ] 향후 검증을 위한 정적 유효 및 무효 fixture가 존재한다.
- [ ] product, command gateway, hook script, 명령 실행, migration, seed, API smoke 또는 runtime 검증 변경을 포함하지 않는다.
- [ ] 어떤 사람 수동 명령 결과도 `VERIFIED` AI 워크플로 증거로 받아들이지 않는다.
- [ ] Resolved Decisions 아래의 여섯 결정이 schema, 기준 예시, Markdown 규칙, `AGENTS.md` 문구에 일관되게 반영된다.

Phase 1A 검증은 문서 및 정적 일관성 검토만 수행한다. 모든 프로젝트 명령을 `NOT RUN`으로 보고해야 한다.

## Phase 1A 비목표

Phase 1A는 다음을 수행하지 않는다.

- `scripts/ai/command-runner.sh` 구현
- `scripts/ai/workflow-gate.sh` 구현
- `scripts/ai/done-claim-check.sh` 구현
- JSON 자동 파싱, 생성 또는 검증
- Gradle 또는 애플리케이션 명령 실행
- `.ai-runs/` 증거 생성
- 명령 로그 수집 또는 정제
- pre/post command hook 구현
- command ID의 기술적 강제 적용
- cache, fingerprint, repo intake, skill 또는 handoff 자동화 구현
- API smoke case 구현
- 네이티브 runtime adapter 또는 CI gate 추가
- product code, test, runtime 동작, database 상태, migration, seed, deployment 또는 secret 변경

## 해결된 결정

1. **Helper runtime:** Phase 1B는 Python 3를 대상으로 한다. Phase 1A는 로컬 가용성을 `UNKNOWN`으로 기록하고 preflight를 수행하지 않으며 Node.js, Java, `jq`로의 암묵적 fallback을 허용하지 않는다.
2. **Gradle 실행 프로필:** Phase 1A와 Phase 1B는 `["./gradlew", "test"]` 같은 POSIX/Bash argv만 등록한다. 네이티브 Windows `gradlew.bat` 지원은 향후 범위이며 `NOT_CONFIGURED`다.
3. **스키마 식별:** 스키마 파일은 안정적인 프로젝트 URN을 사용한다. 기준 instance는 저장소 상대 `$schema`, `$id` 값을 사용한다.
4. **생성 요약:** Phase 1A는 동일 검토 변경에서 기준 JSON으로 작은 요약을 수동 bootstrap한다. 자동 생성과 stale 검증은 Phase 1B 이후에 시작한다.
5. **스키마 validator:** Phase 1B는 Draft 2020-12 지원 Python `jsonschema`를 대상으로 하고 `scripts/ai/lib/validate_json.py`를 계획한다. Phase 1A는 스키마와 fixture만 만든다.
6. **임시 명령 정책:** Phase 1B gateway가 존재할 때까지 AI 프로젝트 명령 실행을 완전히 중지한다. 사람의 수동 결과는 AI 워크플로 밖에 있으며 `VERIFIED` 상태나 통과 검사 주장을 만들 수 없다.

## 열린 질문

없음. 이전 여섯 질문은 위에서 해결했다. 구현을 시작하기 전에 검토자는 구현 계획이 이 명세의 해결된 결정, 파일 경계, 비목표를 보존하는지만 확인한다.

## 검토 결정

이 명세는 Phase 1A 구현 계획 수립을 승인한다. 승인은 이 문서에 나열한 Phase 1A 파일 생성과 수정만 허용한다. Phase 1B command gateway 구현이나 AI 프로젝트 명령 실행을 허용하지 않는다.
