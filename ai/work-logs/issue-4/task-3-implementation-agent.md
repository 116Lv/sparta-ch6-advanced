---
issue: 4
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4
agent: task-3-implementation-agent
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: task-3-implementation-agent
started_at: 2026-07-10T17:58:32Z
ended_at: 2026-07-10T18:08:36Z
last_updated: 2026-07-13T09:32:29+09:00
branch: main
related_files:
  - ai/work-logs/issue-4/task-3-strict-json-brief.md
  - docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
  - docs/superpowers/plans/2026-07-10-ai-workflow-phase-1b-1-implementation.md
changed_files:
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
  - ai/fixtures/phase-1b/json/duplicate-key.json
  - ai/fixtures/phase-1b/json/non-finite.json
  - ai/work-logs/issue-4/task-3-strict-json-brief.md
  - ai/work-logs/issue-4/task-3-implementation-agent.md
commands_run:
  - C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
  - C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh
tests_run:
  - "RED: helper contract exit 1; 17 tests ran; FAILED (errors=40) because InvalidStateError and validate_repository_instance were absent."
  - "Fixture correction check: helper contract exit 1; 17 tests ran; FAILED (failures=2); both failures were test setup mismatches and were corrected without production changes."
  - "GREEN: helper contract exit 0; 17 tests ran; OK."
  - "Scrub regression RED: helper contract exit 1; 17 tests ran; FAILED (failures=1) because a duplicate key name appeared in the structured message."
  - "Scrub regression GREEN: helper contract exit 0; 17 tests ran; OK."
  - "Final helper verification: exit 0; 17 tests ran in 0.991s; OK."
  - "Final Task 1 runtime-preflight regression: exit 0; PASS: runtime preflight contract."
blockers: []
reconciliation_required: false
issue_creation_attempted_at: 2026-07-10T12:37:12Z
issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"
expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 1B command gateway without product behavior changes."
migration_history:
  - migrated_at: 2026-07-13T08:54:37+09:00
    from: ai/work-logs/no-issue/phase-1b-command-gateway
    to: ai/work-logs/issue-4
    comment_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4#issuecomment-4953423372
---

## Reconciliation Update

GitHub Issue #4 now backs this historical role record. Statements below about unavailable Issue creation, pending reconciliation, or the earlier 403 describe the state when this role executed; they are not current blockers.

# Task 3 Implementation Handoff

## Scope Completed

- Added strict UTF-8 JSON loading with duplicate-key detection and rejection of `NaN`, `Infinity`, and `-Infinity`.
- Added a fixed repository-relative schema allowlist for the seven Phase 1A schemas plus the existing Phase 1B gateway and runtime-evidence schemas.
- Added Draft 2020-12 identity checks, schema self-checking, local-fragment-only schema references, and `FormatChecker` instance validation.
- Added deterministic scrubbed validation errors with stable codes, JSON Pointer instance paths, and schema paths.
- Added fixture coverage proving all nine Phase 1A valid fixture documents validate and all twenty-four Phase 1A invalid fixture documents fail as `INVALID_STATE`.
- Preserved Task 1 and Task 2 behavior. No resolver process execution or Phase 1B-2 behavior was added.

## TDD Evidence

### Primary RED

Command:

```text
C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
```

Exit: `1`

Summary:

```text
Ran 17 tests in 0.203s
FAILED (errors=40)
```

Expected cause: the new tests required `InvalidStateError` and `validate_repository_instance`, which did not exist.

### Scrub Regression RED

The duplicate-key fixture exposed the caller-controlled key name in the structured error message.

```text
Ran 17 tests in 1.057s
FAILED (failures=1)
```

The message was changed to fixed scrubbed text.

### Final GREEN

Command:

```text
C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
```

Exit: `0`

Exact summary:

```text
Ran 17 tests in 0.991s
OK
```

## Task 1 Regression

Command:

```text
C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh
```

Exit: `0`

Exact output:

```text
PASS: runtime preflight contract
```

## Static Review

- Schema selection maps exact instance `$schema` values to fixed repository paths; instance data is never joined into a schema path or URI.
- Existing files are resolved inside the repository root, including real-path containment checks that reject symlink escape.
- Schema files must use the approved Draft 2020-12 URI, stable project URN, and `schemaVersion: 1` before validation.
- External `$ref` and `$dynamicRef` values are rejected; only local fragments are accepted.
- Structured validation messages do not include instance values or duplicate key names.
- `.ai-runs/` is absent.
- No Gradle, product tests, server, Docker, HTTP/API, database, migration, seed, or infrastructure command ran.
- No file was committed or staged.

## Remaining Concerns

None within Task 3 scope. Registry semantic validation and command resolution remain later Phase 1B-1 tasks.

## Status

done

## Independent Review Fix Evidence

Review result received: Critical `0`, Important `2`, Minor `1`.

### Findings Addressed

- Replaced the bypassing `validate(instance, schema_path)` entry point with `validate(root, instance, schema_path)`, which always loads schemas through the fixed `APPROVED_SCHEMA_PATHS` map before any filesystem access.
- Routed gateway-result publication, runtime-evidence validation, project-state validation, and repository-instance validation through the same approved-schema loader.
- The centralized loader enforces repository real-path containment, exact Draft 2020-12 URI, stable project URN, `schemaVersion: 1`, local-fragment-only `$ref` and `$dynamicRef`, and `Draft202012Validator.check_schema`.
- Added regression coverage for Draft URI, stable URN, schema version, arbitrary internal schema path, gateway publication with a tampered schema identity, and file/network forms of `$ref` and `$dynamicRef`.
- External-reference errors now preserve the complete nested schema JSON Pointer, including `/properties/value/$ref` and `/properties/value/$dynamicRef`.

### Review-Fix RED

Preliminary command:

```text
C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
```

Exit: `1`

```text
Ran 20 tests in 1.227s
FAILED (failures=4, errors=1)
```

Observed failures: the old two-argument `validate` API rejected the desired centralized call, and all four external-reference cases returned only `/$ref` or `/$dynamicRef` instead of their nested schema paths.

Final RED command after adding the publication-path regression:

```text
C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
```

Exit: `1`

```text
Ran 21 tests in 1.235s
FAILED (failures=5, errors=1)
```

The additional expected failure proved that a tampered gateway schema URN still returned publication status `0` before the fix.

### Review-Fix GREEN

Command:

```text
C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh
```

Exit: `0`

```text
Ran 21 tests in 1.295s
OK
```

Runtime-preflight regression command:

```text
C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh
```

Exit: `0`

```text
PASS: runtime preflight contract
```

### Review-Fix Files Changed

- `scripts/ai/workflow_helper.py`
- `scripts/ai/tests/test_workflow_helper.py`
- `ai/work-logs/issue-4/task-3-implementation-agent.md`

### Review-Fix Boundary

- `.ai-runs/` remained absent.
- No Gradle, product test, server, Docker, HTTP/API, database, migration, seed, or infrastructure command ran.
- No file was committed or staged.
- Review-fix status: `done`.
