# AI Workflow Project State

## Human Policy Notes

`ai/project-state.json` is the canonical source of truth for stable project facts, confidence, environments, helper runtimes, and ports. This Markdown file contains policy explanation and a reviewable summary only.

- Update canonical JSON before refreshing the generated summary.
- Do not edit content between generated markers independently of canonical JSON.
- Confidence and capability values use the closed enums defined by the Phase 1A schemas.
- `NOT_APPLICABLE` is displayed as `N/A`; executable JSON never stores `N/A`.
- Phase 1A bootstrapped project state from static evidence only and did not run Python, Gradle, the application, Docker, HTTP requests, migrations, seeds, or infrastructure commands.
- Phase 1B may record scrubbed environment-local Python helper evidence through the supported preflight transaction and mark only the matching LOCAL helper runtime and environment `VERIFIED`.
- Recorded helper-runtime evidence does not authorize or prove any project command. Gradle, product tests, the application, Docker, HTTP/API, database, migration, seed, and infrastructure commands remain `NOT RUN` until a later supported execution gateway records their evidence.
- Application port 8080 remains an inference until runtime evidence is produced through a later supported workflow.

<!-- GENERATED:START source=ai/project-state.json -->
## Generated State Summary

Canonical source: `ai/project-state.json`
Schema version: `1`
Updated at: `2026-07-14T00:00:00Z`

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
| LOCAL | Python 3 | Python 3 | VERIFIED | 3.9.6 (tags/v3.9.6:db3ff76, Jun 28 2021, 15:26:21) [MSC v.1929 64 bit (AMD64)] | RUNTIME_COMMAND: ai/evidence/local-helper-runtime.json (Local Python 3 helper runtime passed the Phase 1B preflight.) |
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
