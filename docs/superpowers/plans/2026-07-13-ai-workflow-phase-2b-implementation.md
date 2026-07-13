# AI Workflow Phase 2B Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Phase 2B skill contracts, agent handoff state, and reusable-context links to issue summaries and work logs without executing product commands or claiming verification completeness.

**Architecture:** Phase 2B remains repository-wide AI workflow infrastructure. Skill behavior is documented in focused Markdown contracts and indexed by schema-valid canonical JSON, while handoff/reuse state is represented by closed JSON plus reviewable Markdown summaries. The existing Python helper validates the new contracts and work-log links through static/helper tests only.

**Tech Stack:** Markdown policy docs, JSON Schema Draft 2020-12, Python 3 helper with `jsonschema`, Python `unittest`, Git Bash thin shell contract tests.

## Global Constraints

- Owning feature: none.
- Preserve Phase 1A, Phase 1B-1, Phase 1B-2, Phase 1B-3, and Phase 2A approved baselines.
- Do not execute Gradle, build, product/unit project tests, server, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands.
- Do not create repository-root `.ai-runs` evidence.
- Do not create real repository artifact manifests or finalized `run.json` files.
- GitHub Issue reconciliation remains `pending_issue` with error `authorization failure: GitHub API 403 Resource not accessible by integration`.
- Phase 1B-3 remains integrity-only: `completenessEvaluated: false`, `scope: INTEGRITY_ONLY`; Phase 2B must not introduce verification completeness, registry `VERIFIED`, issue-backed closure, reconciliation completion, or unqualified overall `DONE`.
- Existing command-runner/workflow-gate boundary remains unchanged: standalone workflow gates do not launch product commands.
- Phase 2B skills define contracts and routing only. Executable product-command behavior remains behind existing Phase 1B supported paths and later Phase 2C applicability policy.

---

## File Structure

- Create `docs/superpowers/plans/2026-07-13-ai-workflow-phase-2b-implementation.md`: this implementation plan.
- Create `ai/work-logs/issue-6/README.md`: pending-Issue fallback summary and durable recovery record.
- Create `ai/work-logs/issue-6/implementation-agent.md`: implementation evidence log.
- Create `ai/work-logs/issue-6/plan-reviewer.md`: independent plan review record.
- Create `ai/work-logs/issue-6/reviewer.md`: final independent review record.
- Create `ai/skills/README.md`: skill directory index and shared Phase 2B rules.
- Create `ai/skills/repo-intake.md`: repo-intake skill contract.
- Create `ai/skills/command-runner.md`: command-runner skill contract.
- Create `ai/skills/verification-runner.md`: verification-runner skill contract.
- Create `ai/skills/api-smoke-verifier.md`: API-smoke verifier skill contract.
- Create `ai/skills/failure-triage.md`: failure-triage skill contract.
- Create `ai/skills/docs-sync.md`: docs-sync skill contract.
- Create `ai/skills/review-gate.md`: review-gate skill contract.
- Create `ai/skill-catalog.json`: canonical skill registry for Phase 2B contracts.
- Create `ai/schemas/skill-catalog.schema.json`: closed schema for skill catalog validation.
- Create `ai/agent-handoff.md`: human-readable handoff state and reuse contract.
- Create `ai/agent-handoff.json`: canonical current handoff packet.
- Create `ai/schemas/agent-handoff.schema.json`: closed schema for agent handoff packets.
- Modify `ai/workflow-cache.json`: add reviewable Phase 2B handoff context records and notes without raw logs.
- Modify `ai/workflow-cache.md`: summarize Phase 2B reusable context links.
- Modify `scripts/ai/workflow_helper.py`: allowlist new schemas and validate Phase 2B skill/handoff contracts.
- Modify `scripts/ai/tests/test_workflow_helper.py`: add RED/GREEN tests for Phase 2B contracts.
- Modify `AGENTS.md`, `docs/00-index.md`, `ai/document-routing.md`, `ai/subagent-workflow.md`, `ai/work-log-template.md`, `ai/work-logs/README.md`, and `ai/work-logs/index.md`: connect Phase 2B skills, handoff state, and reusable context to routing and work-log recovery.

## Task 1: Phase 2B Planning And Pending-Issue Work Log

**Files:**
- Create: `docs/superpowers/plans/2026-07-13-ai-workflow-phase-2b-implementation.md`
- Create: `ai/work-logs/issue-6/README.md`
- Create: `ai/work-logs/issue-6/implementation-agent.md`
- Create: `ai/work-logs/issue-6/plan-reviewer.md`
- Modify: `ai/work-logs/index.md`

**Interfaces:**
- Consumes: pending-Issue fallback metadata pattern from `ai/work-logs/issue-5/README.md`.
- Produces: durable Phase 2B recovery record for planning, implementation, review, and later GitHub reconciliation.

- [ ] **Step 1: Initialize the fallback summary and logs**

Create the Phase 2B fallback with:

```yaml
issue: pending
tracking_status: pending_issue
status: in_progress
owning_feature: "none"
reconciliation_required: true
issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"
expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 2B skills, handoff state, and reusable context links without product command execution."
```

- [ ] **Step 2: Update the work-log index**

Add one row for `phase-2b-skills-handoff` with `Workflow Status` set to `in_progress` and `Reconciliation` set to `required`. Also align only the existing Phase 2A index row's workflow-status cell to `done` because `ai/work-logs/issue-5/README.md` already records `status: done`; this is a narrow index/summary consistency fix and is not an issue-backed closure, reconciliation-complete claim, verification-complete claim, or unqualified overall `DONE`.

- [ ] **Step 3: Independent plan review**

Dispatch a review agent to check this plan against the design, Phase 2A boundaries, Phase 1B integrity-only limits, and the product-command prohibition. Record the reviewer verdict in `plan-reviewer.md` before implementation.

## Task 2: Skill Contract Documents And Catalog

**Files:**
- Create: `ai/skills/README.md`
- Create: `ai/skills/repo-intake.md`
- Create: `ai/skills/command-runner.md`
- Create: `ai/skills/verification-runner.md`
- Create: `ai/skills/api-smoke-verifier.md`
- Create: `ai/skills/failure-triage.md`
- Create: `ai/skills/docs-sync.md`
- Create: `ai/skills/review-gate.md`
- Create: `ai/skill-catalog.json`
- Create: `ai/schemas/skill-catalog.schema.json`
- Modify: `AGENTS.md`, `docs/00-index.md`, `ai/document-routing.md`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces:
  - `validate_repository_instance(root, "ai/skill-catalog.json")`
  - schema allowlist entry for `skill-catalog`
  - complete skill IDs: `repo-intake`, `command-runner`, `verification-runner`, `api-smoke-verifier`, `failure-triage`, `docs-sync`, `review-gate`

- [ ] **Step 1: Write failing skill catalog tests**

Add tests asserting every required skill document exists, every catalog entry points to an existing repository-contained document, and every entry states Phase 2B product commands remain NOT RUN. If a skill mentions supported-path execution, the text must state it is future-phase or later-phase behavior outside Phase 2B's no-product-command verification.

- [ ] **Step 2: Run focused RED**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests.test_phase_2b_skill_catalog_and_documents_are_complete -v`

Expected: FAIL because the Phase 2B skill catalog and documents are absent.

- [ ] **Step 3: Add skill documents**

Each skill document must define:

- purpose;
- required inputs;
- allowed operations;
- prohibited operations;
- evidence outputs;
- handoff/reuse requirements;
- Phase 2B boundary notes.

The `api-smoke-verifier` skill must explicitly report API smoke as `NOT_CONFIGURED` or `BLOCKED` when prerequisites/cases are absent and must not run HTTP/curl/API calls in Phase 2B.

- [ ] **Step 4: Add skill catalog schema and JSON**

`skill-catalog.json` records each skill ID, document path, route ID, allowed entry point, prohibited operations, evidence outputs, and handoff fields. The schema rejects missing required skills, path escapes, duplicate IDs, and extra fields.

- [ ] **Step 5: Allowlist the schema and run focused GREEN**

Extend `SCHEMA_NAMES` with `skill-catalog`, then run the same focused test. Expected: PASS.

## Task 3: Agent Handoff State And Workflow Cache Reuse

**Files:**
- Create: `ai/agent-handoff.md`
- Create: `ai/agent-handoff.json`
- Create: `ai/schemas/agent-handoff.schema.json`
- Modify: `ai/workflow-cache.json`
- Modify: `ai/workflow-cache.md`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces:
  - `validate_repository_instance(root, "ai/agent-handoff.json")`
  - schema allowlist entry for `agent-handoff`
  - reusable context links from `ai/workflow-cache.json` to `ai/agent-handoff.json`, Phase 2A work log, and Phase 2B fallback summary

- [ ] **Step 1: Write failing handoff validation tests**

Add tests asserting `agent-handoff.json` validates, contains route ID `repo-wide-ai-workflow`, preserves `trackingStatus: pending_issue`, preserves the exact reconciliation error `authorization failure: GitHub API 403 Resource not accessible by integration`, links Phase 2A reusable context, includes every Phase 2B skill ID, and records NOT RUN product-command categories.

- [ ] **Step 2: Run focused RED**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests.test_agent_handoff_and_workflow_cache_reuse_validate -v`

Expected: FAIL because the handoff schema/JSON do not exist and workflow-cache has no Phase 2B links.

- [ ] **Step 3: Add handoff schema, JSON, and Markdown**

`agent-handoff.json` must include:

- route and owning-feature result;
- required startup documents;
- reusable context refs;
- skill catalog ref;
- work-log refs;
- GitHub reconciliation status;
- prohibited project commands as explicit NOT RUN categories;
- remaining later-phase boundaries.

- [ ] **Step 4: Update workflow cache**

Add a `HANDOFF_CONTEXT` entry and `handoffNotes` that point to Phase 2A and Phase 2B reviewable docs. Do not add raw logs, `.ai-runs` refs, manifest refs, or finalized `run.json` refs.

- [ ] **Step 5: Allowlist the schema and run focused GREEN**

Extend `SCHEMA_NAMES` with `agent-handoff`, then run the same focused test. Expected: PASS.

## Task 4: Work-Log And Routing Integration

**Files:**
- Modify: `AGENTS.md`
- Modify: `docs/00-index.md`
- Modify: `ai/document-routing.md`
- Modify: `ai/subagent-workflow.md`
- Modify: `ai/work-log-template.md`
- Modify: `ai/work-logs/README.md`
- Modify: `ai/work-logs/index.md`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Consumes: `ai/skill-catalog.json`, `ai/agent-handoff.json`, `ai/workflow-cache.json`.
- Produces: issue summaries and work logs that carry reusable context refs, skill IDs, handoff state, pending reconciliation status, and NOT RUN product-command declarations.

- [ ] **Step 1: Write failing integration tests**

Add tests that verify:

- `AGENTS.md`, `docs/00-index.md`, and `ai/document-routing.md` link to `ai/skills/README.md` and `ai/agent-handoff.md`;
- `ai/subagent-workflow.md`, `ai/work-log-template.md`, and `ai/work-logs/README.md` require reusable context refs in handoffs/work logs;
- `ai/work-logs/index.md` has Phase 2A `done` and Phase 2B `in_progress` pending-Issue rows.
- the Phase 2A index status alignment is documented as index consistency only and not as unqualified overall `DONE`.

Also add a static no-product-command boundary test with command-aware matching. The test must inspect `scripts/ai/runtime-preflight.sh`, `scripts/ai/repo-intake.sh`, and the reachable helper entry points in `scripts/ai/workflow_helper.py` (`preflight`, `repo-intake`, result publication, validation, schema loading, context/cache validation, and path/digest helpers). It fails if those files contain an invocation token or subprocess argv path for `gradlew`, `gradlew.bat`, `docker`, `docker-compose`, `curl`, `wget`, `mysql`, `psql`, `java -jar`, `bootRun`, `migration`, `seed`, or `scripts/ai/command-runner.sh run`. Matching must be command-aware so ordinary unittest method names or prose words such as `test` and `http` are not false positives; Phase 2B does not ban the helper test suite or documentation references, it bans product-command execution paths.

- [ ] **Step 2: Run focused RED**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests.test_work_log_and_routing_docs_link_phase_2b_reuse_contracts -v`

Expected: FAIL before document integration.

- [ ] **Step 3: Update routing and work-log docs**

Link Phase 2B skill and handoff docs without duplicating executable rules. Require future issue summaries and role logs to include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and `github_reconciliation_status`.

- [ ] **Step 4: Run focused GREEN**

Run the same focused test. Expected: PASS.

## Task 5: Integration Verification And Review

**Files:**
- Modify: `ai/work-logs/issue-6/README.md`
- Modify: `ai/work-logs/issue-6/implementation-agent.md`
- Create or modify: `ai/work-logs/issue-6/reviewer.md`

**Interfaces:**
- Consumes: all Phase 2B outputs from Tasks 1-4.
- Produces: final Phase 2B PASS/FAIL evidence.

- [ ] **Step 1: Run allowed verification**

Allowed commands:

```bash
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests -v
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests -v
python -m unittest scripts.ai.tests.test_workflow_helper -v
bash scripts/ai/run-helper-tests.sh
bash scripts/ai/tests/run-contract-tests.sh
bash scripts/ai/runtime-preflight.sh
bash scripts/ai/repo-intake.sh --output -
git diff --check
```

Expected: all exit `0`, except platform capability skips already accepted by Phase 1B.

- [ ] **Step 2: Static no-evidence check**

Run:

```bash
test ! -d .ai-runs
python -c "from pathlib import Path; root=Path('.'); bad=[]; [bad.append(str(p).replace('\\\\','/')) for p in root.rglob('*') if '.git' not in p.parts and not str(p).replace('\\\\','/').startswith('ai/fixtures/') and (str(p).replace('\\\\','/').startswith('.ai-runs/') or p.name in {'artifact-manifest.json','run.json'})]; print('\\n'.join(bad)); raise SystemExit(1 if bad else 0)"
git status --short
```

Expected: `.ai-runs` absent; no artifact manifest or finalized `run.json`; working tree changes limited to Phase 2B files and pre-existing Phase 1A/1B/2A work.

- [ ] **Step 3: Independent final review**

Dispatch a review agent with the diff and verification evidence. It must check Phase 2B scope, no product commands, no repository `.ai-runs`, pending issue status with the exact 403 error preserved, no Phase 2C completeness claims, no registry `VERIFIED` promotion, no issue-backed closure claim, no reconciliation-complete claim, and no unqualified overall `DONE` claim.

- [ ] **Step 4: Update work logs**

Record created files, modified files, implemented contracts, commands, NOT RUN product commands, `.ai-runs` state, manifest/run state, pending-Issue status, final review verdict, and Phase 2B PASS/FAIL in `README.md` and `implementation-agent.md`.
