# AI Workflow Enforcement Phase 1B-1 Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use `superpowers:subagent-driven-development` to execute this plan task by task, with TDD and an independent review after each implementation task.

**Goal:** Implement a fail-closed Python 3 preflight and pure command-resolution planner that validates canonical workflow JSON, registry semantics, closed parameters, classification, and prerequisites without executing any project command.

**Architecture:** `runtime-preflight.sh` is the only Phase 1B-1 shell entry point. It probes the fixed `python3`, then `python` allowlist and invokes `workflow_helper.py`. The initial probe is restricted to runtime identity and validator capabilities. On success, the helper writes durable scrubbed LOCAL evidence and synchronizes canonical runtime state plus generated summary. The helper then owns strict JSON loading, allowlisted Draft 2020-12 validation, semantic registry validation, path containment, and pure structured resolution. Phase 1B-1 never creates `.ai-runs`, launches a resolved project argv, or updates a project command to `VERIFIED`.

**Tech Stack:** POSIX Bash, Python 3 standard library, Python `jsonschema`, JSON Schema Draft 2020-12, `unittest`.

**Baseline:** `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`

## Global Constraints

1. Owning feature is `none`; no product source or product test is modified.
2. Probe the fixed PATH command-name allowlist `python3`, then `python`; accept either only after proving Python major version 3. Do not use `py`, environment-selected executables, Node.js, Java, or `jq`.
3. Use `Draft202012Validator.check_schema`, `Draft202012Validator`, and `FormatChecker`.
4. Load only allowlisted repository-local schemas and never fetch schemas over the network.
5. Reject duplicate JSON keys and `NaN`/infinite constants.
6. The resolver is pure planning. It must not invoke `./gradlew`, spawn a product process, or create `.ai-runs`. Only successful preflight recording may update LOCAL helper-runtime state; project command verification state never changes.
7. Resolution output contains argv arrays only. Never create a shell command string or use `eval`, `sh -c`, `bash -c`, `shell=True`, `shlex.split`, environment expansion, or glob expansion.
8. Native `gradlew.bat`, non-Gradle executable profiles, destructive operations, migrations, seeds, deployment, production mutation, and secret changes remain unsupported.
9. Tests may run only the helper/preflight contract. Gradle, application server, Docker, HTTP/API, database, migration, seed, and infrastructure commands remain `NOT RUN`.
10. Preserve the current Phase 1A working-tree changes. Do not revert or reformat unrelated files.

## Task 1: Preflight Bootstrap Contract

**Files:**
- Create: `scripts/ai/tests/test-runtime-preflight.sh`
- Create: `scripts/ai/runtime-preflight.sh`
- Create: `scripts/ai/run-helper-tests.sh`
- Create: `scripts/ai/workflow_helper.py`
- Create: `ai/schemas/gateway-result.schema.json`
- Create: `ai/schemas/helper-runtime-evidence.schema.json`
- Create: `ai/evidence/local-helper-runtime.json`
- Modify: `ai/project-state.json`
- Modify: `ai/project-state.md`
- Modify: `.gitignore`
- Create: `ai/fixtures/phase-1b/preflight/`

**Step 1: Write the failing shell contract test**

Cover:

- no allowlisted Python command on controlled PATH returns exit `3` and fixed `NOT_CONFIGURED` JSON;
- controlled fake `python3` and `python` candidates are invoked as quoted argv, not as a shell string;
- `python3` has deterministic precedence over `python`;
- `py` and environment-selected executable values are ignored;
- a candidate reporting Python 2 or missing `jsonschema` returns exit `3`;
- an available Python 3 plus `Draft202012Validator` and FormatChecker produces a schema-valid PREFLIGHT PASS result;
- successful record mode writes schema-valid scrubbed evidence, updates only the LOCAL helper-runtime state, and refreshes the generated summary;
- identical current runtime evidence is idempotent and does not rewrite tracked files;
- a staged write/validation failure restores the prior evidence, canonical JSON, and summary and returns `INVALID_STATE`;
- interrupted `ai/.workflow-state-txn/` journals are recovered or rolled back before canonical reads;
- a changed interpreter SHA-256 invalidates otherwise identical cached evidence and requires a state refresh before helper use;
- unavailable runtime leaves canonical state unchanged;
- caller-controlled values are absent from bootstrap failure JSON.

The test uses temporary fake executables only and never invokes project commands.

**Step 2: Run the test and verify RED**

Run: `bash scripts/ai/tests/test-runtime-preflight.sh`

Expected: FAIL because `scripts/ai/runtime-preflight.sh` does not exist.

**Step 3: Implement the minimal shell entry point and preflight helper**

Requirements:

- `set -eu`;
- resolve repository root from the script location without accepting caller root overrides;
- literal candidate order `python3`, then `python`;
- fixed bootstrap JSON and exit `3` when absent;
- invoke the selected literal candidate with `scripts/ai/workflow_helper.py preflight --repository-root <root>` and every argument quoted;
- helper proves major version 3 and required `jsonschema` capabilities;
- helper validates PREFLIGHT PASS output against the closed gateway-result schema;
- record mode validates the helper-runtime evidence and resulting project state before replacement and uses an explicit recovery journal for interrupted multi-file synchronization;
- `run-helper-tests.sh` accepts no arguments, repeats the fixed candidate/preflight policy, and executes only `-m unittest scripts/ai/tests/test_workflow_helper.py -v` through the selected confirmed runtime;
- no `eval`, command string, environment-selected executable, or dynamic argv append.

**Step 4: Run the test and verify GREEN**

Run: `bash scripts/ai/tests/test-runtime-preflight.sh`

Expected: PASS.

**Step 5: Self-review and independent task review**

Confirm the script cannot select any executable except PATH-resolved `python3` and cannot interpolate caller data into the bootstrap JSON.

## Task 2: Gateway Result Schema And Python Preflight

**Files:**
- Create: `scripts/ai/tests/test_workflow_helper.py`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `ai/schemas/gateway-result.schema.json`
- Create: `ai/fixtures/phase-1b/gateway-result/`

**Step 1: Write failing Python tests**

Cover:

- PREFLIGHT PASS result validates against the new schema;
- non-PASS requires a non-empty reason and contains no executable argv;
- RESOLVE PASS requires command ID, classification, working directory, argv, and prerequisite IDs;
- unknown operation/result/extra fields are rejected;
- helper preflight reports Python major version 3, `jsonschema` version, `Draft202012Validator`, and FormatChecker availability;
- helper output is validated before emission.

**Step 2: Verify runtime preflight before running Python tests**

Run: `bash scripts/ai/runtime-preflight.sh`

Expected: PASS/exit `0`. If it returns `NOT_CONFIGURED`/exit `3`, record the exact blocker and stop implementation; do not install or assume dependencies without approval.

**Step 3: Run the focused tests and verify RED**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: FAIL because the gateway schema/helper behavior is missing.

**Step 4: Extend the schema and preflight helper**

Complete the closed Draft 2020-12 common fields and conditional PREFLIGHT/RESOLVE data. Implement deterministic error JSON and shared exit mapping. Do not add execution code.

**Step 5: Run the focused tests and verify GREEN**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: PASS.

**Step 6: Run the shell preflight contract again**

Run: `bash scripts/ai/tests/test-runtime-preflight.sh`

Expected: PASS.

## Task 3: Strict JSON And Allowlisted Schema Validation

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Modify: `scripts/ai/workflow_helper.py`
- Create: `ai/fixtures/phase-1b/json/duplicate-key.json`
- Create: `ai/fixtures/phase-1b/json/non-finite.json`

**Step 1: Add failing tests**

Cover:

- duplicate object keys are rejected;
- `NaN`, `Infinity`, and `-Infinity` are rejected;
- invalid calendar dates fail through FormatChecker;
- unsupported instance schema path/version fails;
- schema files are selected only from the internal allowlist;
- schema `check_schema` failure is `INVALID_STATE`;
- validation errors are deterministically ordered with stable codes and JSON paths;
- all Phase 1A valid fixtures pass schema validation;
- all Phase 1A schema-invalid fixtures fail as `INVALID_STATE`.

**Step 2: Run and verify RED**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: New tests fail for missing strict loader/validator behavior.

**Step 3: Implement strict loading and validation**

Implement duplicate-key hooks, non-finite rejection, a fixed schema map, schema self-check, FormatChecker validation, and deterministic error normalization. Do not permit instance-controlled filesystem or network resolution.

**Step 4: Run and verify GREEN**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: PASS.

## Task 4: Registry Semantic Validation

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Modify: `scripts/ai/workflow_helper.py`
- Create: `ai/fixtures/phase-1b/registry/`

**Step 1: Add failing tests**

Cover:

- duplicate command IDs;
- required/property mismatch;
- partial, malformed, undeclared, disabled, and unresolved placeholders;
- repeated valid whole-token placeholders;
- unanchored, non-compiling, catastrophic, or unsupported regex constructs;
- unsupported argv zero including `gradlew.bat`;
- unknown prerequisite, self-reference, cycle, and deterministic topological order;
- working-directory escape, symlink escape where supported, missing wrapper, and wrapper escape;
- schema validation and all semantic validation complete before command lookup.

Use existing Phase 1A semantic-invalid fixtures where applicable.

**Step 2: Run and verify RED**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: New semantic tests fail.

**Step 3: Implement semantic validation**

Return `INVALID_STATE` with stable codes and deterministic paths. Treat a missing previously evidenced wrapper as `BLOCKED`, but path/symlink escape as `INVALID_STATE`. Do not execute or inspect Gradle tasks.

**Step 4: Run and verify GREEN**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: PASS.

## Task 5: Pure Resolution, Parameters, Classification, And Prerequisites

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Modify: `scripts/ai/workflow_helper.py`
- Create: `ai/fixtures/phase-1b/parameters/`
- Create: `ai/fixtures/phase-1b/prerequisites/`

**Step 1: Add failing resolution tests**

Cover:

- canonical `verify.unit` resolves to exactly `["./gradlew", "test"]`;
- well-formed unknown ID -> `NOT_CONFIGURED`;
- malformed ID -> `POLICY_VIOLATION`;
- `NOT_CONFIGURED` -> `NOT_CONFIGURED`;
- `UNKNOWN`, `STALE`, `UNCERTAIN` -> `BLOCKED`;
- SAFE continues; RISKY and DESTRUCTIVE are blocked;
- parameters supplied when disabled, including `{}`, -> `POLICY_VIOLATION`;
- missing, extra, wrong-type, and pattern-invalid parameters -> `POLICY_VIOLATION`;
- files over 65536 bytes, values over 1024 scalar values, and control characters -> `POLICY_VIOLATION`;
- a value containing spaces and shell metacharacters remains one inert argv element;
- parameter input path escape and cross-run `.ai-runs` access are rejected;
- any Phase 1B-1 command with non-empty prerequisites -> `BLOCKED` with deterministic ordered prerequisite IDs;
- no resolver path invokes subprocess execution or creates `.ai-runs`.

**Step 2: Run and verify RED**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: New resolution tests fail.

**Step 3: Implement minimal resolution behavior**

Validate in the specification order, substitute only whole tokens, return a schema-valid gateway result, preserve argv only as a list, and block non-empty prerequisites until Phase 1B-2 provides active-run evidence.

**Step 4: Run and verify GREEN**

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: PASS.

**Step 5: Run the complete Phase 1B-1 helper contract**

Run: `bash scripts/ai/tests/test-runtime-preflight.sh`

Expected: PASS.

Run: `bash scripts/ai/run-helper-tests.sh`

Expected: PASS.

## Task 6: Repository Integration And Review

**Files:**
- Modify: `AGENTS.md`
- Modify: `ai/work-logs/issue-4/README.md`
- Modify: `ai/work-logs/issue-4/specification-agent.md`
- Modify: `ai/work-logs/issue-4/spec-reviewer.md`
- Create: `ai/work-logs/issue-4/implementation-agent.md`
- Create: `ai/work-logs/issue-4/task-reviewer.md`
- Modify: `ai/work-logs/index.md`

**Step 1: Update the enforcement boundary**

Document that Phase 1B-1 provides recorded LOCAL runtime preflight and pure resolution only. It still does not authorize direct project commands or provide project-command execution evidence. Successful preflight makes LOCAL helper runtime `VERIFIED` with durable scrubbed environment-local evidence; current preflight mismatch blocks use and makes cached evidence stale for that invocation. CI remains `NOT_CONFIGURED`.

**Step 2: Record exact verification evidence**

Record every helper/preflight command and result. Mark every Gradle, product test, server, Docker, HTTP/API, database, migration, seed, and infrastructure command `NOT RUN`.

**Step 3: Static repository checks**

Run: `git diff --check`

Expected: PASS, allowing only existing line-ending warnings.

Run: `git status --short`

Expected: only the intended Phase 1A and Phase 1B files are modified/untracked.

**Step 4: Independent review**

Dispatch a fresh reviewer with the Phase 1B spec, this task plan, changed-file inventory, test report, and diff. Fix every Critical and Important finding, rerun covering tests, and repeat review until clean.

## Completion Report Requirements

Report:

- created and modified files;
- preflight availability/result;
- schema and semantic-validation coverage;
- exact canonical command outcomes;
- parameter and prerequisite behavior;
- proof that no project argv executed and `.ai-runs` was not created;
- test commands and outputs;
- every project command as `NOT RUN`;
- unresolved Minor findings and residual risks;
- Phase 1B-2 and Phase 1B-3 remaining scope;
- `tracking_status: pending_issue` and required GitHub reconciliation;
- Phase 1B-1 final PASS/FAIL.
