# AI Workflow Command Registry

## Human Policy Notes

`ai/command-registry.json` is the canonical source of truth for command capability state. This Markdown file explains the policy and summarizes that JSON; it is never parsed as executable state and cannot override the JSON.

- Update canonical JSON before refreshing the generated summary.
- Do not edit content between generated markers independently of canonical JSON.
- `NOT_APPLICABLE` is displayed as `N/A`; executable JSON never stores `N/A`.
- A command is executable only through the Phase 1B gateway after that gateway exists. Phase 1A defines state contracts only.
- `VERIFIED` requires successful execution of the exact registered argv plus recorded Phase 1B runtime evidence. Human manual command output does not satisfy this rule.
- Native `gradlew.bat` execution is future scope and remains `NOT_CONFIGURED`.
- schemaVersion 1 executable argv is allowlisted to begin with `./gradlew`, except that `verify.e2e` may use only the exact no-argument argv `["./scripts/e2e/verify-e2e.sh"]`. Phase 1B rejects every other executable or E2E argument as `INVALID_STATE` before execution.
- Token-level safeguards remain defense in depth: backslashes, shell control operators, pipelines, redirection, separators, newlines, dollar expressions, and `eval` expressions are invalid.
- Enabled parameters use a bounded, closed object schema with named string properties and required string patterns; arbitrary embedded schemas are invalid.
- Repository paths are relative, forward-slash-only paths without URI schemes or `..` segments. The canonical registry uses `./schemas/command-registry.schema.json`; static fixtures may use `ai/schemas/command-registry.schema.json`.
- Timestamps use a strict UTC shape. Phase 1B must enable Python `jsonschema` `FormatChecker` for semantic date-time validation.
- `uniqueItems` applies to whole command objects, not `commands[*].id`. Phase 1B semantic validation must reject exact duplicate IDs as `INVALID_STATE` before lookup or execution.
- Draft 2020-12 cannot compare dynamic required and properties key sets. Before execution, Phase 1B semantic validation must require required names to exactly match properties keys and reject any mismatch as INVALID_STATE.

<!-- GENERATED:START source=ai/command-registry.json -->
## Generated State Summary

This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.

- Canonical source: `ai/command-registry.json`
- Schema: `./schemas/command-registry.schema.json`
- Schema version: `1`
- Updated at: `2026-07-16T11:06:24Z`
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
| `verify.e2e` | Run end-to-end tests | `VERIFIED` | `SAFE` | `["./scripts/e2e/verify-e2e.sh"]` | finalized artifact; final-verifier log | 2026-07-16T09:59:30Z |
| `verify.api-smoke` | Run real HTTP API smoke verification | `VERIFIED` | `SAFE` | `["./gradlew", "apiSmokeTest"]` | finalized artifact; final-verifier log | 2026-07-16T09:59:28Z |
| `db.migration` | Apply database migrations | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `build.gradle` | NONE |
| `db.seed` | Seed development or test data | `NOT_CONFIGURED` | `UNAVAILABLE` | `NOT CONFIGURED` | `src/main/resources/application.yml`; `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md` | NONE |

### Bootstrap Constraints

- Build, unit, integration, API smoke, and E2E are VERIFIED by finalized Ubuntu-native official-runner artifacts for the exact POSIX argv shown above.
- The E2E artifact records the isolated Compose topology and completed black-box scenario.
- Lint, migration, and seed are not configured; dependency installation and the development server remain unknown and unavailable.
- Each VERIFIED command records both its immutable finalized artifact manifest and the durable final-verifier reconciliation log.
<!-- GENERATED:END source=ai/command-registry.json -->
