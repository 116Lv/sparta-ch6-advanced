# Task 3 Brief: Strict JSON And Allowlisted Schema Validation

## Scope

Extend the Phase 1B-1 Python helper with strict UTF-8 JSON loading and Draft 2020-12 instance validation. Schema selection is limited to a fixed repository-relative allowlist and may never follow an instance-controlled path or URI.

## Owned Files

- `scripts/ai/workflow_helper.py`
- `scripts/ai/tests/test_workflow_helper.py`
- `ai/fixtures/phase-1b/json/duplicate-key.json`
- `ai/fixtures/phase-1b/json/non-finite.json`
- `ai/work-logs/issue-4/task-3-strict-json-brief.md`
- `ai/work-logs/issue-4/task-3-implementation-agent.md`

## Acceptance Criteria

- Reject duplicate object keys and `NaN`, `Infinity`, and `-Infinity` as `INVALID_STATE`.
- Validate formats with `FormatChecker`, including rejection of invalid calendar dates.
- Reject unsupported instance `$schema` paths and unsupported `schemaVersion` values.
- Select schemas only from a fixed internal repository-relative allowlist; instance values never trigger arbitrary filesystem or network access.
- Run `Draft202012Validator.check_schema` and map schema self-check failures to `INVALID_STATE`.
- Normalize validation failures into deterministic ordered errors with stable codes, JSON instance paths, and schema paths.
- Validate every Phase 1A valid fixture and reject every Phase 1A schema-invalid fixture.
- Preserve all Task 1 and Task 2 behavior and create no `.ai-runs` evidence.

## TDD And Command Boundary

1. Add fixtures and failing tests first.
2. Run `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh` and record RED.
3. Implement only the strict loader and allowlisted validator needed for GREEN.
4. Run the helper tests again and then `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh` for regression.

NOT RUN: Gradle, product tests, application server, Docker, HTTP/API, database, migration, seed, or infrastructure commands. Do not commit or stage.
