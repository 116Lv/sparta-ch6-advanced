# Stale Command Registry Summary Fixture

<!-- GENERATED:START source=ai/command-registry.json -->
## Generated State Summary

This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.

- Canonical source: `ai/command-registry.json`
- Schema: `./schemas/command-registry.schema.json`
- Schema version: `1`
- Updated at: `2026-07-09T00:00:00Z`
- Registered capability records: `10`
- Verified command records: `0`

| ID | Purpose | Configuration Status | Classification | Argv Display | Evidence | Last Verified |
|---|---|---|---|---|---|---|
| `dependencies.install` | Install or resolve project dependencies | `UNKNOWN` | `UNAVAILABLE` | `UNKNOWN` | NONE | NONE |
| `server.dev` | Start the development server | `UNKNOWN` | `UNAVAILABLE` | `UNKNOWN` | NONE | NONE |
| `verify.build` | Compile or build the project | `UNKNOWN` | `UNAVAILABLE` | `UNKNOWN` | NONE | NONE |
| `verify.unit` | Run the configured Gradle test task | `CONFIGURED_UNVERIFIED` | `SAFE` | `["./gradlew", "test"]` | `build.gradle`; `gradlew` | NONE |
| `verify.lint` | Run lint checks | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `build.gradle` | NONE |
| `verify.integration` | Run a dedicated integration-test command | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `build.gradle` | NONE |
| `verify.e2e` | Run end-to-end tests | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `build.gradle` | NONE |
| `verify.api-smoke` | Run real HTTP API smoke verification | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `src/main/java/com/ch6/cafe/CafeApplication.java`; `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md` | NONE |
| `db.migration` | Apply database migrations | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `build.gradle` | NONE |
| `db.seed` | Seed development or test data | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `src/main/resources/application.yml`; `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md` | NONE |

### Bootstrap Constraints

- `verify.unit` is configured but unverified and uses only the POSIX argv `["./gradlew", "test"]`.
- Lint, dedicated integration test, E2E, API smoke, migration, and seed are not configured.
- Dependency installation, development server, and build argv remain unknown and unavailable.
- Every recorded evidence item is `STATIC_FILE`; no runtime evidence exists.
- Every `lastVerifiedAt` value is `null`.
<!-- GENERATED:END source=ai/command-registry.json -->
