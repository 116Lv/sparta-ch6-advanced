# AI Workflow Phase 2A Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 2A context intake and cache-control enforcement without executing product commands or claiming verification completeness.

**Architecture:** Phase 2A remains repository-wide AI workflow infrastructure. Canonical reusable context is published as reviewable Markdown and static JSON policy records, while `workflow_helper.py` adds read-only validation and conservative invalidation checks over temporary fixtures and repository files. Bash entry points stay thin and never launch project commands.

**Tech Stack:** Markdown policy docs, JSON Schema Draft 2020-12, Python 3 helper with `jsonschema`, Bash thin wrappers, Python `unittest`, temporary fixture repositories.

## Global Constraints

- Owning feature: none.
- Preserve Phase 1A, Phase 1B-1, Phase 1B-2, and Phase 1B-3 approved baselines.
- Do not execute Gradle, build, product/unit project tests, server, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands.
- Do not create repository-root `.ai-runs` evidence.
- Do not create real repository manifest or finalized `run.json`; only temporary fixture runs may create disposable `.ai-runs`.
- GitHub Issue reconciliation remains `pending_issue` with error `authorization failure: GitHub API 403 Resource not accessible by integration`.
- Phase 1B-3 remains integrity-only: `completenessEvaluated: false`, `scope: INTEGRITY_ONLY`; Phase 2A must not introduce verification completeness, registry `VERIFIED`, issue-backed closure, or unqualified overall `DONE`.
- Existing command-runner/workflow-gate boundary remains unchanged: standalone workflow gates do not launch product commands.

---

## File Structure

- Create `docs/superpowers/plans/2026-07-12-ai-workflow-phase-2a-implementation.md`: this implementation plan.
- Create `ai/work-logs/issue-5/README.md`: pending-Issue fallback summary and durable recovery record.
- Create `ai/work-logs/issue-5/implementation-agent.md`: implementation evidence log.
- Create `ai/work-logs/issue-5/plan-reviewer.md`: independent plan review record.
- Create `ai/work-logs/issue-5/reviewer.md`: final independent review record.
- Create `ai/context-map.md`: route IDs, repository surfaces, generated/excluded paths, owner docs, and minimal reading routes.
- Create `ai/cache-policy.md`: cache key, freshness, reuse, invalidation, and stale/uncertain mapping rules.
- Create `ai/tool-call-policy.md`: repository-only policy limits for repeated reads, searches, rediscovery, and unsupported host-tool interception.
- Create `ai/resource-budget.md`: numeric default budgets and exception-recording rules.
- Create `ai/workflow-cache.md`: scrubbed reusable context and evidence pointer format; no raw logs.
- Create `ai/schemas/context-map.schema.json`: closed machine-readable context-map contract.
- Create `ai/schemas/workflow-cache.schema.json`: closed workflow-cache record contract.
- Create `ai/schemas/repo-intake-result.schema.json`: closed structured result contract for Phase 2A read-only intake.
- Create `ai/context-map.json`: canonical Phase 2A context routes and surfaces.
- Create `ai/workflow-cache.json`: canonical empty/initial workflow cache.
- Create `scripts/ai/repo-intake.sh`: thin read-only Phase 2A entry point.
- Modify `scripts/ai/workflow_helper.py`: allowlist new schemas, add read-only context/cache validation, conservative invalidation, and repo-intake helper operation.
- Modify `scripts/ai/tests/test_workflow_helper.py`: add RED/GREEN tests for Phase 2A contracts.
- Modify `AGENTS.md`, `docs/00-index.md`, `ai/document-routing.md`, `ai/work-logs/index.md`: link Phase 2A artifacts without changing product rules.

## Task 1: Phase 2A Planning And Work Log

**Files:**
- Create: `docs/superpowers/plans/2026-07-12-ai-workflow-phase-2a-implementation.md`
- Create: `ai/work-logs/issue-5/README.md`
- Create: `ai/work-logs/issue-5/implementation-agent.md`
- Create: `ai/work-logs/issue-5/plan-reviewer.md`
- Modify: `ai/work-logs/index.md`

**Interfaces:**
- Consumes: existing `pending_issue` fallback metadata pattern from `ai/work-logs/issue-4/README.md`.
- Produces: durable Phase 2A recovery record for later implementation and review logs.

- [ ] **Step 1: Write the plan and fallback logs**

Create this plan, initialize the Phase 2A pending-Issue fallback with:

```yaml
issue: pending
tracking_status: pending_issue
status: in_progress
owning_feature: "none"
reconciliation_required: true
issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"
expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 2A context intake and cache control without product command execution."
```

- [ ] **Step 2: Update the work-log index**

Add one row for `phase-2a-context-cache` with `Workflow Status` set to `in_progress` and `Reconciliation` set to `required`.

- [ ] **Step 3: Independent plan review**

Dispatch a review agent to check this plan against the design, Phase 1B limits, and the product-command prohibition. Record the reviewer verdict in `plan-reviewer.md` before helper implementation.

## Task 2: Static Context And Cache Documents

**Files:**
- Create: `ai/context-map.md`
- Create: `ai/cache-policy.md`
- Create: `ai/tool-call-policy.md`
- Create: `ai/resource-budget.md`
- Create: `ai/workflow-cache.md`
- Modify: `AGENTS.md`
- Modify: `docs/00-index.md`
- Modify: `ai/document-routing.md`

**Interfaces:**
- Consumes: Phase 2A design sections for context map, cache/tool-call policy, resource budgets, and repository-only enforcement limits.
- Produces: human-readable policy documents used by Task 3 schemas and Task 4 helper validation.

- [ ] **Step 1: Write failing doc presence tests**

Add tests that fail while the five new docs are missing or unlinked:

```python
def test_phase_2a_policy_documents_exist_and_are_linked(self):
    required = [
        "ai/context-map.md",
        "ai/cache-policy.md",
        "ai/tool-call-policy.md",
        "ai/resource-budget.md",
        "ai/workflow-cache.md",
    ]
    for relative in required:
        self.assertTrue((REPOSITORY_ROOT / relative).is_file(), relative)
```

- [ ] **Step 2: Run focused RED**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests.test_phase_2a_policy_documents_exist_and_are_linked -v`

Expected: FAIL because the Phase 2A documents are absent.

- [ ] **Step 3: Create the docs**

Each document must state:

- JSON remains canonical when JSON exists.
- Markdown is reviewable policy and summary, not an executable parser source.
- Repository scripts cannot intercept all host reads/search/tool calls before Phase 3.
- Unsupported host-wide interception is audit/review only in Phase 2A.
- Product commands remain NOT RUN.

- [ ] **Step 4: Link the docs**

Update `AGENTS.md`, `docs/00-index.md`, and `ai/document-routing.md` so routing points to `ai/context-map.md` route IDs and the new Phase 2A policy docs.

- [ ] **Step 5: Run focused GREEN**

Run the same focused unittest. Expected: PASS.

## Task 3: Canonical Context And Cache Schemas

**Files:**
- Create: `ai/schemas/context-map.schema.json`
- Create: `ai/schemas/workflow-cache.schema.json`
- Create: `ai/schemas/repo-intake-result.schema.json`
- Create: `ai/context-map.json`
- Create: `ai/workflow-cache.json`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces:
  - `validate_repository_instance(root, "ai/context-map.json")`
  - `validate_repository_instance(root, "ai/workflow-cache.json")`
  - `validate(root, result, "ai/schemas/repo-intake-result.schema.json")`
  - schema allowlist entries for `context-map` and `workflow-cache`

- [ ] **Step 1: Write failing schema validation tests**

Add tests proving `ai/context-map.json` and `ai/workflow-cache.json` are schema-valid through the existing allowlisted validator, and invalid fixtures reject unknown route/cache statuses.

- [ ] **Step 2: Run focused RED**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests.test_context_map_and_workflow_cache_validate_through_allowlist -v`

Expected: FAIL because schemas and JSON files are absent or not allowlisted.

- [ ] **Step 3: Add schemas and canonical JSON**

`context-map.json` includes route IDs, owner documents, generated/excluded paths, important repository surfaces, and minimal reading routes. `workflow-cache.json` starts with empty arrays for file discoveries, command evidence summaries, handoff notes, and invalidation events.

`repo-intake-result.schema.json` defines the only structured output shape for Phase 2A repo intake. Required fields are `$schema`, `$id`, `schemaVersion`, `operation`, `result`, `reason`, `errors`, and `data`; `operation` is exactly `REPO_INTAKE`; `result` uses the script control outcome enum; and PASS data contains `contextMapRef`, `workflowCacheRef`, `projectStateRefresh`, `commandDiscoveryUpdates`, `cacheInvalidation`, and `createdAiRuns` exactly.

- [ ] **Step 4: Allowlist schemas**

Extend `SCHEMA_NAMES` in `workflow_helper.py` with `context-map`, `workflow-cache`, and `repo-intake-result`.

- [ ] **Step 5: Run focused GREEN**

Run the same focused unittest. Expected: PASS.

## Task 4: Repo Intake And Conservative Invalidation

**Files:**
- Create: `scripts/ai/repo-intake.sh`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces helper CLI:

```text
workflow_helper.py repo-intake
  --repository-root <absolute-path>
  --output <path-or-stdout-marker>
```

`repo-intake` validates Phase 2A canonical files and emits a schema-backed `REPO_INTAKE` `PASS` or fail-closed result validated by `ai/schemas/repo-intake-result.schema.json`. It does not execute project commands, start runs, or create `.ai-runs`.

- [ ] **Step 1: Write failing repo-intake tests**

Tests assert that `repo-intake`:

- returns `PASS` when Phase 2A JSON/docs are valid;
- returns `INVALID_STATE` when a context route points outside the repository;
- reports affected `projectStateRefresh` proposals for known Phase 1A project-state invalidation inputs without marking any command `VERIFIED`;
- reports `commandDiscoveryUpdates` as proposal-only records when static discovery sees unsupported command-surface changes, preserving existing `CONFIGURED_UNVERIFIED`, `NOT_CONFIGURED`, `UNKNOWN`, `STALE`, or `UNCERTAIN` semantics;
- reports stale/uncertain cache entries when their keyed file digest changes or the changed file is unmapped;
- creates no `.ai-runs` in the repository root.

- [ ] **Step 2: Run focused RED**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests -v`

Expected: FAIL because `repo-intake` does not exist.

- [ ] **Step 3: Implement minimal read-only helper**

Add `repo_intake(root)` and CLI parser support. Reuse existing path containment, strict JSON, schema validation, `digest`, and `publish_result`. The helper must validate every emitted result against `ai/schemas/repo-intake-result.schema.json` before returning it.

`projectStateRefresh` is proposal-only in Phase 2A: it identifies affected `ai/project-state.json` sections and confidence transitions such as `STALE` or `UNCERTAIN`, but it does not automatically rewrite canonical project state unless a later approved phase authorizes atomic refresh writes. `commandDiscoveryUpdates` is also proposal-only: it identifies registry records affected by static command-surface changes and recommended non-executable status changes, but it never executes commands, never records runtime evidence, and never marks registry records `VERIFIED`.

- [ ] **Step 4: Add thin shell entry point**

`scripts/ai/repo-intake.sh` accepts only `--output <path-or-stdout-marker>` and invokes the selected helper runtime. It must not accept command IDs or dynamic argv.

- [ ] **Step 5: Run focused GREEN**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests -v`

Expected: PASS.

## Task 5: Integration Verification And Review

**Files:**
- Modify: `ai/work-logs/issue-5/implementation-agent.md`
- Create: `ai/work-logs/issue-5/reviewer.md`
- Modify: `ai/work-logs/issue-5/README.md`

**Interfaces:**
- Consumes: all Phase 2A outputs from Tasks 1-4.
- Produces: final Phase 2A PASS/FAIL evidence.

- [ ] **Step 1: Run allowed verification**

Allowed commands:

```bash
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests -v
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests -v
bash scripts/ai/run-helper-tests.sh
bash scripts/ai/tests/run-contract-tests.sh
bash scripts/ai/runtime-preflight.sh
git diff --check
```

Expected: all exit `0`, except platform capability skips already accepted by Phase 1B.

- [ ] **Step 2: Static no-evidence check**

Run:

```bash
test ! -d .ai-runs
git status --short
```

Expected: `.ai-runs` absent; staged files `0`.

- [ ] **Step 3: Independent final review**

Dispatch a review agent with the diff and verification evidence. It must check Phase 2A scope, no product commands, no repository `.ai-runs`, pending issue status, and no Phase 2C completeness claims.

- [ ] **Step 4: Update work logs**

Record changed files, commands, NOT RUN product commands, pending-Issue status, and final PASS/FAIL in `README.md` and `implementation-agent.md`.
