# AI Workflow Phase 2C Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add static/helper-verifiable verification applicability, workflow entry points, and document integration for Phase 2C without executing project commands.

**Architecture:** Phase 2C adds canonical verification policy JSON plus a thin shell entry point that asks `workflow_helper.py` to evaluate task/change applicability and leaf-result mapping. Existing QA, routing, issue, work-log, skill, and done-claim documents link to those executable gates. The implementation validates contracts through helper/static tests and temporary fixtures only.

**Tech Stack:** Markdown policy docs, JSON Schema Draft 2020-12, Python 3 helper with `jsonschema`, Bash thin wrappers, Python `unittest`, temporary fixture data.

## Global Constraints

- Owning feature: none.
- Preserve Phase 1A, Phase 1B-1, Phase 1B-2, Phase 1B-3, Phase 2A, and Phase 2B approved baselines.
- Do not execute Gradle, build, product/unit project tests, server, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands.
- Do not create repository-root `.ai-runs` evidence.
- Do not create real repository artifact manifests or finalized `run.json` files.
- Do not mark any registry command `VERIFIED`.
- GitHub Issue reconciliation remains `pending_issue` with error `authorization failure: GitHub API 403 Resource not accessible by integration`.
- Phase 1B-3 remains integrity-only: `completenessEvaluated: false`, `scope: INTEGRITY_ONLY`; Phase 2C may define applicability/completeness policy but must not claim issue-backed closure, reconciliation completion, or unqualified overall `DONE`.
- Existing command-runner/workflow-gate boundary remains unchanged: standalone workflow gates do not launch product commands.

---

## File Structure

- Create `docs/superpowers/plans/2026-07-13-ai-workflow-phase-2c-implementation.md`: this plan.
- Create `ai/work-logs/issue-7/README.md`: pending-Issue fallback summary and durable recovery record.
- Create `ai/work-logs/issue-7/implementation-agent.md`: implementation evidence log.
- Create `ai/work-logs/issue-7/plan-reviewer.md`: independent plan review record.
- Create `ai/work-logs/issue-7/reviewer.md`: final independent review record.
- Create `ai/verification-policy.json`: canonical change-type, entry-point, check-requiredness, and result-mapping policy.
- Create `ai/schemas/verification-policy.schema.json`: closed schema for the canonical policy.
- Create `ai/schemas/verification-gate-result.schema.json`: closed helper result contract for Phase 2C static gates.
- Create `ai/verification-gates.md`: human-readable entry-point and applicability policy summary.
- Create `scripts/ai/verification-gate.sh`: thin shell entry point for static/helper gate evaluation.
- Modify `scripts/ai/workflow_helper.py`: allowlist schemas, evaluate Phase 2C verification/applicability gates, and expose a `verification-gate` CLI.
- Modify `scripts/ai/tests/test_workflow_helper.py`: add RED/GREEN Phase 2C contract tests.
- Modify `AGENTS.md`, `docs/00-index.md`, `ai/document-routing.md`, `ai/skills/README.md`, `ai/skills/verification-runner.md`, `ai/skills/api-smoke-verifier.md`, `ai/skills/failure-triage.md`, `ai/skills/review-gate.md`, `ai/verification-levels.md`, `ai/qa-gate.md`, `ai/done-claim-template.md`, `ai/issue-completion-checklist.md`, `ai/subagent-workflow.md`, `ai/work-log-template.md`, `ai/work-logs/README.md`, `ai/work-logs/index.md`, `ai/agent-handoff.json`, `ai/agent-handoff.md`, `ai/skill-catalog.json`, `ai/workflow-cache.json`, and `ai/workflow-cache.md`: connect Phase 2C executable gates without changing product-command authority.

## Task 1: Phase 2C Planning And Pending-Issue Work Log

**Files:**
- Create: `docs/superpowers/plans/2026-07-13-ai-workflow-phase-2c-implementation.md`
- Create: `ai/work-logs/issue-7/README.md`
- Create: `ai/work-logs/issue-7/implementation-agent.md`
- Create: `ai/work-logs/issue-7/plan-reviewer.md`
- Modify: `ai/work-logs/index.md`

**Interfaces:**
- Consumes: pending-Issue fallback metadata pattern from Phase 2A and Phase 2B.
- Produces: durable Phase 2C recovery record and plan-review evidence.

- [ ] Initialize the fallback summary with `tracking_status: pending_issue`, `status: in_progress`, `owning_feature: "none"`, the exact 403 reconciliation error, and an expected scope for Phase 2C verification gates.
- [ ] Add an `in_progress` Phase 2C row to `ai/work-logs/index.md`.
- [ ] Dispatch an independent plan reviewer and record the verdict in `plan-reviewer.md`.

## Task 2: Canonical Verification Policy And Schema

**Files:**
- Create: `ai/verification-policy.json`
- Create: `ai/schemas/verification-policy.schema.json`
- Create: `ai/schemas/verification-gate-result.schema.json`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces:
  - `validate_repository_instance(root, "ai/verification-policy.json")`
  - schema allowlist entries for `verification-policy` and `verification-gate-result`
  - closed change types: `documentation-only`, `static-workflow`, `domain-logic`, `db-api`, `auth-permission`, `critical-data`, `user-flow`

- [ ] Write failing tests proving the policy is schema-valid, includes every Phase 2C entry point, and encodes required checks by change type.
- [ ] Run the focused RED test; expect failure before schemas/JSON/allowlist exist.
- [ ] Add the schemas and canonical JSON.
- [ ] Extend `SCHEMA_NAMES` in `workflow_helper.py`.
- [ ] Run the focused GREEN test.

## Task 3: Static Verification Gate Helper And Shell Entry Point

**Files:**
- Create: `scripts/ai/verification-gate.sh`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces helper CLI:

```text
workflow_helper.py verification-gate
  --repository-root <absolute-path>
  --change-type <policy-change-type>
  --entry-point <verification-level|api-smoke|failure-triage|review|done-claim>
  [--leaf-results-file <repository-relative-json-path>]
  --output <path-or-stdout-marker>
```

- [ ] Write failing tests for `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mapping by change type using temp fixture leaf-result files only.
- [ ] Run the focused RED test; expect failure before helper operation exists.
- [ ] Implement policy evaluation:
  - irrelevant leaf checks become `NOT_APPLICABLE`;
  - missing required capability maps to overall `BLOCKED`;
  - executed failing check maps to `FAIL`;
  - all required PASS plus authorized N/A entries maps to `PASS`;
  - no project command is launched and no `.ai-runs` is created.
- [ ] Add `scripts/ai/verification-gate.sh` as a thin fixed-argument entry point.
- [ ] Run focused GREEN tests.

## Task 4: Document And Skill Integration

**Files:**
- Create: `ai/verification-gates.md`
- Modify: `AGENTS.md`, `docs/00-index.md`, `ai/document-routing.md`
- Modify: `ai/skills/README.md`, `ai/skills/verification-runner.md`, `ai/skills/api-smoke-verifier.md`, `ai/skills/failure-triage.md`, `ai/skills/review-gate.md`
- Modify: `ai/verification-levels.md`, `ai/qa-gate.md`, `ai/done-claim-template.md`, `ai/issue-completion-checklist.md`, `ai/subagent-workflow.md`, `ai/work-log-template.md`, `ai/work-logs/README.md`
- Modify: `ai/agent-handoff.json`, `ai/agent-handoff.md`, `ai/skill-catalog.json`, `ai/workflow-cache.json`, `ai/workflow-cache.md`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Consumes: `ai/verification-policy.json` and `scripts/ai/verification-gate.sh`.
- Produces: existing QA/routing/issue/work-log documents and concrete feature-template files under `specs/_template/` linked to executable Phase 2C gates.

- [ ] Write failing integration tests that require links to `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh` from routing, QA, done-claim, skill, handoff, work-log docs, and `specs/_template/*` feature-template documents.
- [ ] Run the focused RED test.
- [ ] Update docs to define verification completeness and task/change applicability inside Phase 2C, while preserving the pending reconciliation and no-product-command boundaries.
- [ ] Update skill catalog and handoff/cache records so Phase 2C entry points are discoverable and no raw evidence references are added.
- [ ] Run focused GREEN tests.

## Task 5: Integration Verification And Review

**Files:**
- Modify: `ai/work-logs/issue-7/README.md`
- Modify: `ai/work-logs/issue-7/implementation-agent.md`
- Create or modify: `ai/work-logs/issue-7/reviewer.md`

**Interfaces:**
- Consumes: all Phase 2C outputs.
- Produces: final Phase 2C PASS/FAIL evidence.

- [ ] Run allowed non-product administrative workflow verification only. These commands are helper/static/contract checks for workflow infrastructure; they must not launch Gradle, build, product/unit project tests, server, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands; must not create repository `.ai-runs`; must not publish artifact manifests or finalized `run.json`; and must not promote registry commands to `VERIFIED`:

```bash
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests -v
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests -v
python -m unittest scripts.ai.tests.test_workflow_helper -v
bash scripts/ai/run-helper-tests.sh
bash scripts/ai/tests/run-contract-tests.sh
bash scripts/ai/runtime-preflight.sh
bash scripts/ai/repo-intake.sh --output -
bash scripts/ai/verification-gate.sh --change-type documentation-only --entry-point verification-level --output -
git diff --check
```

- [ ] Run static no-evidence checks for absent repository `.ai-runs`, absent non-fixture `artifact-manifest.json`, absent non-fixture finalized `run.json`, no registry `VERIFIED` promotion, and preserved pending GitHub reconciliation error.
- [ ] Dispatch an independent final reviewer with the diff and verification evidence.
- [ ] Record created files, modified files, gate contract scope, mapping coverage, NOT RUN project commands, evidence absence, registry state, pending issue status, final review verdict, and Phase 2C PASS/FAIL.

## Self-Review

- Spec coverage: The plan covers verification-level, API-smoke, failure-triage, review, and done-claim entry points; document integration; change-type applicability; and static/helper verification only.
- Placeholder scan: No `TBD`, `TODO`, or open implementation placeholder is used as a required step.
- Type consistency: `verification-policy`, `verification-gate-result`, and `verification-gate` names are consistent across files, tests, shell, and helper CLI.
