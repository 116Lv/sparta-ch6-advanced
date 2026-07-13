# AI Workflow Phase 1B-3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the Phase 1B-3 integrity-only done-claim gate, final evidence manifest/run finalization, stale-summary checks, and contract tests without running project commands.

**Architecture:** Keep Bash as thin entry points and put all JSON validation, evidence graph checks, digest closure, final aggregation, and stale-summary logic in `scripts/ai/workflow_helper.py`. `done-claim-check.sh prepare` transitions an OPEN run session to FINALIZING, validates the proposed claim and evidence graph, writes a PRE_DONE_CLAIM gate result, publishes `artifact-manifest.json`, publishes final `run.json` last, and removes `.state/` only after immutable finalization succeeds.

**Tech Stack:** Python 3.9+, `jsonschema` Draft 2020-12, POSIX shell contract tests, Python `unittest`, temporary fixture repositories only.

## Global Constraints

- Owning feature: none; this is repo-wide AI workflow enforcement.
- Do not modify product source, product tests, Gradle configuration, app configuration, migration, seed, Docker, API, or database files.
- Do not run Gradle, product unit tests, build, server, Docker Compose, curl/API, migration, seed, or real project command-runner execution in the real repository.
- Verification may use helper tests, runtime/direct preflight, shell contract tests, static scans, and temp fixture/fake command execution only.
- Keep GitHub Issue reconciliation pending with exact failure reason: `"authorization failure: GitHub API 403 Resource not accessible by integration"`.
- Phase 1B-3 is integrity-only. It must report `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`; it must not claim verification completeness or unqualified overall DONE.
- Until Phase 2C exists, any `NOT_APPLICABLE` or `SKIPPED_WITH_REASON` done-claim check blocks integrity PASS.
- Do not create `.ai-runs` evidence in the real repository during implementation or verification.

---

### Task 1: PRE_DONE_CLAIM Schema And Shell Contract

**Files:**
- Modify: `ai/schemas/gateway-result.schema.json`
- Create: `scripts/ai/done-claim-check.sh`
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Create: `scripts/ai/tests/run-contract-tests.sh`
- Modify: `scripts/ai/tests/test-command-runner.sh`

**Interfaces:**
- Produces: gateway operation `PRE_DONE_CLAIM`.
- Produces: shell command `scripts/ai/done-claim-check.sh prepare <run-id> --claim <repo-relative-json>`.
- Consumes: existing helper CLI style from `workflow-gate.sh` and `command-runner.sh`.

- [ ] **Step 1: Write failing schema tests**

Add tests that assert `PRE_DONE_CLAIM/PASS` requires data keys `runId`, `taskKey`, `doneClaimRef`, `manifestRef`, `runRef`, `gateResultRef`, `completenessEvaluated`, and `scope`, with `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`. Add non-PASS tests for `FAIL`, `BLOCKED`, `NOT_CONFIGURED`, `POLICY_VIOLATION`, and `INVALID_STATE` with `data: null`.

- [ ] **Step 2: Run the targeted test and verify RED**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.GatewayResultSchemaTests -v`

Expected before implementation: FAIL because `PRE_DONE_CLAIM` is not an allowed operation.

- [ ] **Step 3: Implement schema branch and thin shell**

Update `gateway-result.schema.json` and `workflow_helper.py` operation allowlist for `PRE_DONE_CLAIM`. Add `done-claim-check.sh` with closed argument parsing and helper runtime probing copied in style from existing shell entry points. Add `run-contract-tests.sh` to run helper tests plus shell contracts, and extend shell contract tests so command/gate shells do not contain finalization logic while `done-claim-check.sh` is the only shell that names `prepare`/`PRE_DONE_CLAIM`.

- [ ] **Step 4: Run targeted schema/shell tests**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.GatewayResultSchemaTests -v`

Run: `bash scripts/ai/tests/test-command-runner.sh`

Expected: targeted schema tests pass; shell contract test still launches only mocked helper paths and no project command.

### Task 2: Integrity Aggregation And Final Evidence Closure

**Files:**
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Modify: `ai/schemas/run.schema.json`
- Modify: `ai/schemas/artifact-manifest.schema.json`

**Interfaces:**
- Produces helper function `prepare_done_claim(root, run_id, claim_ref) -> (gateway_result, exit_code)`.
- Produces helper CLI subcommand `done-claim-prepare --repository-root <abs> --run-id <id> --claim <repo-relative-json>`.
- Publishes immutable artifacts in this order: gate result, done claim, artifact manifest, run.json.

- [ ] **Step 1: Write failing finalization tests**

Create temp fixture tests for:
- evidence-free PASS claim returns `BLOCKED`;
- hidden failed command result returns `FAIL`;
- blocking policy violation returns `POLICY_VIOLATION`;
- digest mismatch returns `INVALID_STATE`;
- valid all-PASS integrity claim writes `artifact-manifest.json`, then `run.json`, removes `.state/`, and reports `completenessEvaluated: false`.

- [ ] **Step 2: Run targeted RED tests**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`

Expected before implementation: FAIL because `prepare_done_claim` and the CLI do not exist.

- [ ] **Step 3: Implement finalizer**

Implement strict claim path resolution, current preflight, FINALIZING transition under run lock, reservation/reference validation, artifact discovery, SHA-256 manifest generation, stale generated-summary comparison, done-claim semantic aggregation, gate-result publication, manifest publication, final `run.json` publication, and `.state/` removal after `run.json` exists. Persist `run.json.result` as `BLOCKED` when detailed gate outcome is `INVALID_STATE` or `POLICY_VIOLATION`.

- [ ] **Step 4: Run targeted GREEN tests**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v`

Expected: PASS.

### Task 3: Repository Boundary Documentation And Work Logs

**Files:**
- Modify: `AGENTS.md`
- Modify: `ai/work-logs/index.md`
- Modify: `ai/work-logs/issue-4/README.md`
- Create: `ai/work-logs/issue-4/phase-1b-3-implementation-agent.md`
- Create: `ai/work-logs/issue-4/phase-1b-3-reviewer.md`

**Interfaces:**
- Preserves `tracking_status: pending_issue`.
- Preserves `reconciliation_required: true`.
- Updates Phase 1B-3 status only; no issue-backed or reconciliation-complete claim.

- [ ] **Step 1: Write failing repository-boundary tests**

Update existing boundary tests to require `AGENTS.md` to say Phase 1B-3 provides integrity-only finalization/done-claim checks and still does not prove verification completeness. Require work logs to preserve pending issue metadata and add Phase 1B-3 role-log metadata.

- [ ] **Step 2: Run targeted RED tests**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B2Task7RepositoryBoundaryTests -v`

Expected before docs/log update: FAIL on old Phase 1B-3 future-work wording and missing Phase 1B-3 role logs.

- [ ] **Step 3: Update docs/logs narrowly**

Update only the Phase 1B boundary wording and the existing pending work-log directory. Do not alter the GitHub 403 reconciliation status.

- [ ] **Step 4: Run targeted GREEN tests**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B2Task7RepositoryBoundaryTests -v`

Expected: PASS.

### Task 4: Full Allowed Verification And Independent Review

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py`
- Modify: any file required by failed helper or shell contract tests from Tasks 1-3.

**Interfaces:**
- Produces final evidence summary for this Phase 1B-3 request.

- [ ] **Step 1: Run helper test suite**

Run: `scripts/ai/run-helper-tests.sh`

Expected: all helper tests pass; no real project command executes.

- [ ] **Step 2: Run shell/runtime contracts**

Run: `scripts/ai/tests/run-contract-tests.sh`

Run: `scripts/ai/runtime-preflight.sh`

Run: `python scripts/ai/workflow_helper.py preflight --repository-root . --runtime-command python --record`

Expected: PASS or documented local runtime result; no real project command executes.

- [ ] **Step 3: Run static artifact absence checks**

Run: `Test-Path .ai-runs`; `Get-ChildItem -Recurse -Filter artifact-manifest.json`; and guarded `Get-ChildItem .ai-runs -Recurse -Filter run.json` only if `.ai-runs` exists.

Expected: real repository `.ai-runs` absent, manifest count 0, finalized run.json count 0.

- [ ] **Step 4: Request independent review**

Dispatch a review agent with the Phase 1B-3 spec excerpt, changed file list, and verification output. Fix Critical/Important findings, rerun the relevant tests, and report final PASS/FAIL.
