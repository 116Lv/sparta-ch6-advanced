# Task 4 Brief: Registry Semantic Validation

## Scope

Add Phase 1B-1 registry semantic validation before command lookup. This slice validates registry-wide invariants and static repository paths only. It neither resolves a user command into a gateway result nor executes, inspects, or otherwise invokes Gradle.

## Owned Files

- `scripts/ai/workflow_helper.py`
- `scripts/ai/tests/test_workflow_helper.py`
- `ai/fixtures/phase-1b/registry/`
- `ai/work-logs/issue-4/task-4-registry-semantics-brief.md`
- `ai/work-logs/issue-4/task-4-implementation-agent.md`

## Acceptance Criteria

- Reject duplicate IDs and parameter `required`/`properties` key mismatches with deterministic codes and JSON paths.
- Require every brace-bearing argv token to be an exact declared whole-token placeholder; allow repeated declared placeholders; reject disabled, partial, malformed, undeclared, and unresolved placeholders.
- Require anchored, compiling parameter patterns from the Phase 1B-1 safe-regex subset. Reject grouping, alternation, counted quantifiers, backreferences, lookarounds, flags, conditionals, nested quantifiers, and catastrophic constructions.
- Defend the semantic argv allowlist independently of schema validation, including rejection of `gradlew.bat`.
- Reject unknown, self-referencing, and cyclic prerequisites; calculate prerequisite order deterministically without auto-execution.
- Require each configured executable working directory and `./gradlew` wrapper to be contained by real path inside the repository and have the required directory/file type. Missing statically evidenced wrappers are `BLOCKED`; escape is `INVALID_STATE`.
- Complete schema and semantic validation before any ID lookup.

## TDD And Command Boundary

1. Add fixtures and failing tests first.
2. Run only `C:\Program Files\Git\bin\bash.exe scripts/ai/run-helper-tests.sh` for RED and GREEN evidence.
3. Implement pure semantic validation and static path checks; do not add a resolver CLI, subprocess handling, Gradle inspection, or `.ai-runs` behavior.
4. Run only `C:\Program Files\Git\bin\bash.exe scripts/ai/tests/test-runtime-preflight.sh` for the required regression.

NOT RUN: Gradle, product tests, application server, Docker, HTTP/API, database, migration, seed, and infrastructure commands. Do not stage or commit.
