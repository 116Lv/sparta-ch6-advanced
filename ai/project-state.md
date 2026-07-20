# AI 워크플로 프로젝트 상태

## 사람용 정책 참고 사항

`ai/project-state.json`은 stable project fact, confidence, environment, helper runtime, port의 canonical source of truth다. 이 Markdown file에는 policy explanation과 review 가능한 summary만 포함된다.

- generated summary를 새로 고치기 전에 canonical JSON을 업데이트한다.
- canonical JSON과 독립적으로 generated marker 사이의 content를 수정하지 않는다.
- confidence와 capability value는 Phase 1A schema가 정의한 closed enum을 사용한다.
- `NOT_APPLICABLE`은 `N/A`로 표시하며 executable JSON은 `N/A`를 절대로 저장하지 않는다.
- Phase 1A는 static evidence에서만 project state를 bootstrap했고 Python, Gradle, application, Docker, HTTP request, migration, seed, infrastructure command를 실행하지 않았다.
- Phase 1B는 지원되는 preflight transaction을 통해 scrubbed environment-local Python helper evidence를 기록하고 일치하는 LOCAL helper runtime/environment만 `VERIFIED`로 표시할 수 있다.
- 기록된 helper-runtime evidence는 어떤 project command도 authorize하거나 prove하지 않는다. Gradle, product test, application, Docker, HTTP/API, database, migration, seed, infrastructure command는 이후 지원 execution gateway가 evidence를 기록할 때까지 계속 `NOT RUN`이다.
- application port 8080은 이후 지원 workflow가 runtime evidence를 만들 때까지 inference로 남는다.

<!-- GENERATED:START source=ai/project-state.json -->
## Generated State Summary

Canonical source: `ai/project-state.json`
Schema version: `1`
Updated at: `2026-07-16T09:48:08Z`

This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.

### Project Summary

| Field | Value |
|---|---|
| Name | sparta-ch6-advanced |
| Product Type | Spring Boot backend API assignment |
| Main Language | Java 21 |
| Framework | Spring Boot 4.1.0 |
| Build System | Gradle Wrapper 9.0.0 |

#### Facts

| ID | Value | Confidence | Observed At | Evidence |
|---|---|---|---|---|
| test.framework | JUnit Platform via Spring Boot Test | CONFIRMED | 2026-07-10T08:26:30Z | STATIC_FILE: build.gradle (Spring Boot Test is declared and the test task uses JUnit Platform.) |
| database.primary | MySQL | CONFIRMED | 2026-07-10T08:26:30Z | STATIC_FILE: src/main/resources/application.yml (The primary datasource uses MySQL.) |

### Important Paths

| Purpose | Path |
|---|---|
| Application source | src/main/java |
| Tests | src/test |
| Project documentation | docs |
| Feature specifications | specs |
| Architecture decisions | adr |
| AI workflow policy | ai |

### Known Ports

| Service | Port | Evidence |
|---|---|---|
| application | 8080 (INFERRED) | STATIC_FILE: src/main/resources/application.yml (No explicit server.port is configured; 8080 is the Spring Boot default inference.) |
| mysql | 3306 (CONFIRMED) | STATIC_FILE: docker-compose.yml (MySQL maps port 3306.) |
| redis | 6379 (CONFIRMED) | STATIC_FILE: docker-compose.yml (Redis maps port 6379.) |
| kafka | 9092 (CONFIRMED) | STATIC_FILE: docker-compose.yml (Kafka maps port 9092.) |

### Environment State

| Environment | Configuration Status | Notes |
|---|---|---|
| LOCAL | VERIFIED | Local Python 3 helper runtime passed the recorded Phase 1B preflight. |
| CI | CONFIGURED_UNVERIFIED | phase-3b-repository-contract workflow exists; native enforcement remains NOT_CONFIGURED. |

### Helper Runtime State

| Environment | Target | Detected | Configuration Status | Version | Evidence |
|---|---|---|---|---|---|
| LOCAL | Python 3 | Python 3 | VERIFIED | 3.14.4 (main, Jun 18 2026, 14:25:02) [GCC 15.2.0] | RUNTIME_COMMAND: ai/evidence/local-helper-runtime.json (Local Python 3 helper runtime passed the Phase 1B preflight.) |
| CI | Python 3 | N/A | NOT_CONFIGURED | N/A | N/A |

### Command Registry Reference

- `ai/command-registry.json`

### Cache Invalidation Inputs

- `build.gradle`
- `settings.gradle`
- `gradle/wrapper/gradle-wrapper.properties`
- `docker-compose.yml`
- `src/main/resources/application.yml`
- `src/test/resources/application-test.yml`
- `.github/**`
<!-- GENERATED:END source=ai/project-state.json -->
