# AI Workflow Command Registry

## 사람용 정책 메모

`ai/command-registry.json`은 명령 capability 상태의 기준 문서다. 이 Markdown 파일은 정책을 설명하고 JSON을 요약하며, 실행 가능한 상태로 파싱하지 않고 JSON을 재정의할 수 없다.

- 생성 요약을 새로 고치기 전에 기준 JSON을 갱신한다.
- 생성 marker 사이 콘텐츠를 기준 JSON과 독립적으로 편집하지 않는다.
- `NOT_APPLICABLE`은 `N/A`로 표시하며 실행 가능한 JSON에는 `N/A`를 저장하지 않는다.
- 명령은 Phase 1B gateway가 존재한 뒤 해당 gateway를 통해서만 실행할 수 있다. Phase 1A는 상태 계약만 정의한다.
- `VERIFIED`에는 정확히 등록된 argv의 성공 실행과 기록된 Phase 1B 런타임 증거가 필요하다. 사람 수동 명령 출력은 이 규칙을 충족하지 않는다.
- 네이티브 `gradlew.bat` 실행은 향후 범위이며 `NOT_CONFIGURED`로 유지한다.
- schemaVersion 1 실행 argv는 `./gradlew`로 시작하도록 allowlist한다. 단 `verify.e2e`는 정확한 무인수 argv `["./scripts/e2e/verify-e2e.sh"]`만 사용할 수 있다. Phase 1B는 다른 모든 실행 argv 또는 E2E 인자를 실행 전에 `INVALID_STATE`로 거부한다.
- token 수준 safeguard는 심층 방어로 유지한다. backslash, shell 제어 연산자, pipeline, redirection, separator, newline, dollar expression, `eval` expression은 유효하지 않다.
- 활성 parameter는 이름 있는 문자열 property와 필수 문자열 pattern을 가진 제한된 닫힌 객체 schema를 사용한다. 임의의 포함 schema는 유효하지 않다.
- 저장소 path는 URI scheme나 `..` segment가 없는 상대 forward-slash 전용 path다. 기준 registry는 `./schemas/command-registry.schema.json`을 사용하며 정적 fixture는 `ai/schemas/command-registry.schema.json`을 사용할 수 있다.
- timestamp는 엄격한 UTC 형태를 사용한다. Phase 1B는 의미 date-time 검증에 Python `jsonschema` `FormatChecker`를 활성화해야 한다.
- `uniqueItems`는 `commands[*].id`가 아닌 전체 command 객체에 적용한다. Phase 1B 의미 검증은 조회 또는 실행 전에 정확히 중복된 ID를 `INVALID_STATE`로 거부해야 한다.
- Draft 2020-12는 동적 required와 properties key 집합을 비교할 수 없다. 실행 전에 Phase 1B 의미 검증은 required name이 properties key와 정확히 일치하도록 요구하고 모든 불일치를 INVALID_STATE로 거부해야 한다.

<!-- GENERATED:START source=ai/command-registry.json -->
## Generated State Summary

This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.

- Canonical source: `ai/command-registry.json`
- Schema: `./schemas/command-registry.schema.json`
- Schema version: `1`
- Updated at: `2026-07-16T19:43:00Z`
- Registered capability records: `10`
- Verified command records: `5`

| ID | Purpose | Configuration Status | Classification | Argv Display | Evidence | Last Verified |
|---|---|---|---|---|---|---|
| `dependencies.install` | Install or resolve project dependencies | `UNKNOWN` | `UNAVAILABLE` | `UNKNOWN` | NONE | NONE |
| `server.dev` | Start the development server | `UNKNOWN` | `UNAVAILABLE` | `UNKNOWN` | NONE | NONE |
| `verify.build` | Compile or build the project | `VERIFIED` | `SAFE` | `["./gradlew", "assemble"]` | finalized artifact; final-verifier log | 2026-07-16T09:59:21Z |
| `verify.unit` | Run the configured Gradle test task | `VERIFIED` | `SAFE` | `["./gradlew", "test"]` | finalized artifact; final-verifier log | 2026-07-16T09:59:23Z |
| `verify.lint` | Run lint checks | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `build.gradle` | NONE |
| `verify.integration` | Run a dedicated integration-test command | `VERIFIED` | `SAFE` | `["./gradlew", "integrationTest"]` | finalized artifact; final-verifier log | 2026-07-16T09:59:25Z |
| `verify.e2e` | Run end-to-end tests | `VERIFIED` | `SAFE` | `["./scripts/e2e/verify-e2e.sh"]` | fresh finalized P2 artifact; historical single-instance artifact | 2026-07-16T19:40:52Z |
| `verify.api-smoke` | Run real HTTP API smoke verification | `VERIFIED` | `SAFE` | `["./gradlew", "apiSmokeTest"]` | finalized artifact; final-verifier log | 2026-07-16T09:59:28Z |
| `db.migration` | Apply database migrations | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `build.gradle` | NONE |
| `db.seed` | Seed development or test data | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `src/main/resources/application.yml`; `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md` | NONE |

### Bootstrap Constraints

- Build, unit, integration, API smoke, and E2E are VERIFIED by finalized Ubuntu-native official-runner artifacts for the exact POSIX argv shown above.
- The fresh P2 E2E artifact records the no-argument sequencer completing the preserved single-instance scenario and the two-instance nginx/k6 scenario. The earlier E2E artifact remains historical single-instance evidence only.
- P2 finalization proves retained artifact integrity with `scope: INTEGRITY_ONLY` and `completenessEvaluated: false`; it does not independently prove verification completeness or the documented non-claims.
- Lint, migration, and seed are not configured; dependency installation and the development server remain unknown and unavailable.
- Each VERIFIED command records both its immutable finalized artifact manifest and the durable final-verifier reconciliation log.
<!-- GENERATED:END source=ai/command-registry.json -->
