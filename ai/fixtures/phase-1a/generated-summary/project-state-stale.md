# Stale Project State Summary Fixture

<!-- GENERATED:START source=ai/project-state.json -->
## Generated State Summary

This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.

- Canonical source: `ai/project-state.json`
- Schema: `./schemas/project-state.schema.json`
- Schema version: `1`
- Updated at: `2026-07-10T08:26:30Z`

### Project Summary

| Field | Value |
|---|---|
| Name | `sparta-ch6-advanced` |
| Product type | Spring Boot backend API assignment |
| Main language | Java 21 |
| Framework | Spring Boot 4.1.0 |
| Build system | Gradle Wrapper 9.0.0 |

### Facts

| ID | Value | Confidence | Evidence | Observed At |
|---|---|---|---|---|
| `test.framework` | JUnit Platform via Spring Boot Test | `CONFIRMED` | `build.gradle` | `2026-07-10T08:26:30Z` |
| `database.primary` | MySQL | `CONFIRMED` | `src/main/resources/application.yml` | `2026-07-10T08:26:30Z` |

### Important Paths

| Purpose | Path |
|---|---|
| Application source | `src/main/java` |
| Tests | `src/test` |
| Project documentation | `docs` |
| Feature specifications | `specs` |
| Architecture decisions | `adr` |
| AI workflow policy | `ai` |

### Known Ports

| Service | Port | Confidence | Evidence |
|---|---:|---|---|
| application | 9090 | `CONFIRMED` | `src/main/resources/application.yml` |
| mysql | 3306 | `CONFIRMED` | `docker-compose.yml` |
| redis | 6379 | `CONFIRMED` | `docker-compose.yml` |
| kafka | 9092 | `CONFIRMED` | `docker-compose.yml` |

Application port: `9090 (CONFIRMED)`.

### Environment State

| Environment | Configuration Status | Notes |
|---|---|---|
| `LOCAL` | `UNKNOWN` | Python 3 is the Phase 1B target, but no runtime preflight is executed in Phase 1A. |
| `CI` | `NOT_CONFIGURED` | No CI workflow exists; CI enforcement is Phase 3 scope. |

### Helper Runtime State

| Environment | Target Runtime | Detected Runtime | Version | Configuration Status | Evidence |
|---|---|---|---|---|---|
| `LOCAL` | Python 3 | NONE | NONE | `UNKNOWN` | NONE |
| `CI` | Python 3 | NONE | NONE | `NOT_CONFIGURED` | NONE |

### Command Registry Reference

`ai/command-registry.json`

### Cache Invalidation Inputs

- `build.gradle`
- `settings.gradle`
- `gradle/wrapper/gradle-wrapper.properties`
- `docker-compose.yml`
- `src/main/resources/application.yml`
- `src/test/resources/application-test.yml`
- `.github/**`
<!-- GENERATED:END source=ai/project-state.json -->
