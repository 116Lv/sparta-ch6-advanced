# AI Workflow Baseline Reconciliation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Reconcile five completed `pending_issue` fallback work logs to GitHub Issues #4-#8, validate the approved Phase 1B-2C baseline without product commands, and publish the work as an Issue-linked draft PR.

**Architecture:** Each fallback directory is migrated atomically to its matching `issue-{number}` directory. Frontmatter, internal repository paths, index rows, handoff/cache references, and contract tests are updated mechanically while historical failure evidence is preserved. Existing Phase outputs are committed in coherent groups and published from a dedicated branch.

**Tech Stack:** Git, GitHub CLI, PowerShell mechanical rewrites, Python `unittest`, POSIX shell contract scripts, Markdown, JSON.

## Global Constraints

- Preserve approved Phase 1A, 1B, 2A, 2B, and 2C decisions.
- Phase 1B-3 remains `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.
- Do not run Gradle/product commands, servers, Docker Compose, HTTP/API smoke calls, migrations, seeds, or product command-runner execution.
- Do not create repository `.ai-runs`, artifact manifests, or finalized `run.json`.
- Do not promote the command registry to `VERIFIED`.
- Do not claim unqualified overall DONE or GitHub Issue closure.

---

### Task 1: Reconcile Issue-Backed Work Logs

**Files:**
- Move: `ai/work-logs/no-issue/phase-1b-command-gateway/` to `ai/work-logs/issue-4/`
- Move: `ai/work-logs/no-issue/phase-2a-context-cache/` to `ai/work-logs/issue-5/`
- Move: `ai/work-logs/no-issue/phase-2b-skills-handoff/` to `ai/work-logs/issue-6/`
- Move: `ai/work-logs/no-issue/phase-2c-verification-gates/` to `ai/work-logs/issue-7/`
- Move: `ai/work-logs/no-issue/subagent-workflow-20260710/` to `ai/work-logs/issue-8/`
- Modify: every Markdown file in the five migrated directories
- Modify: `ai/work-logs/index.md`
- Modify: repository files returned by exact old-path scans, including handoff/cache records and helper contract tests

**Interfaces:**
- Consumes: GitHub Issues #4-#8 and the six-step reconciliation contract in `ai/github-issue-planning.md`.
- Produces: five issue-backed work-log directories with complete migration history and no live references to the former fallback paths.

- [ ] Move each complete directory to its Issue-numbered destination.
- [ ] Replace exact old repository paths with the matching `ai/work-logs/issue-{number}` path.
- [ ] Update frontmatter in every migrated summary and role log: real `issue`, real `issue_url`, `tracking_status: issue_backed`, `reconciliation_required: true`, and a migration timestamp. Keep final reconciliation pending until Task 4 posts the required Issue comment.
- [ ] Preserve `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, workflow `status`, and historical evidence.
- [ ] Append a migration-history record containing the old and new directory paths.
- [ ] Update `ai/work-logs/index.md`, handoff/cache references, and exact-path contract expectations.
- [ ] Verify no live `pending_issue` metadata or old fallback path remains for Issues #4-#8.

### Task 2: Validate The Approved Baseline

**Files:**
- Test: `scripts/ai/tests/test_workflow_helper.py`
- Test: `scripts/ai/tests/run-contract-tests.sh`
- Test: repository static state

**Interfaces:**
- Consumes: reconciled paths and approved Phase 1B-2C helper contracts.
- Produces: current non-product verification evidence suitable for the PR.

- [ ] Run focused reconciliation/static tests and correct only path/state consistency defects.
- [ ] Run `python -m unittest scripts.ai.tests.test_workflow_helper -v`; expect all non-skipped tests to pass.
- [ ] Run `scripts/ai/run-helper-tests.sh`; expect PASS.
- [ ] Run `scripts/ai/tests/run-contract-tests.sh`; expect both contract suites to pass.
- [ ] Run `scripts/ai/runtime-preflight.sh` and read-only `scripts/ai/repo-intake.sh --output -`; expect valid helper results and `createdAiRuns: false`.
- [ ] Run static checks for absent `.ai-runs`, non-fixture manifests/finalized runs, secrets, and registry `VERIFIED` state.
- [ ] Keep every actual project command explicitly NOT RUN.

### Task 3: Commit By Cohesive Issue Scope

**Files:**
- Stage: only files belonging to the approved AI workflow baseline and reconciliation.

**Interfaces:**
- Consumes: validated working tree from Tasks 1-2.
- Produces: reviewable Issue-linked commits on `codex/ai-workflow-reconciliation`.

- [ ] Create or switch to `codex/ai-workflow-reconciliation` without rewriting the existing Phase 1A history.
- [ ] Commit shared Issue #8 workflow infrastructure separately where it can stand alone.
- [ ] Commit Phase 1B, 2A, 2B, and 2C artifacts in coherent groups, referencing Issues #4, #5, #6, and #7 respectively.
- [ ] Commit reconciliation path and metadata updates referencing Issues #4-#8.
- [ ] Confirm the staged/committed diff excludes unrelated user changes and forbidden runtime evidence.

### Task 4: Publish Draft Pull Request

**Files:**
- No repository file changes required.

**Interfaces:**
- Consumes: validated commits and remote Issues #4-#8.
- Produces: pushed branch, draft PR, and Issue comments linking the migrated logs and PR.

- [ ] Push `codex/ai-workflow-reconciliation` to `origin` with upstream tracking.
- [ ] Open one draft PR to `main` summarizing Phase 1B-2C baseline, reconciliation, constraints, and validation.
- [ ] Link Issues #4-#8 without auto-closing them.
- [ ] Comment on each Issue with its migrated work-log path and draft PR URL.
- [ ] After all five comments succeed, set `reconciliation_required: false`, mark index reconciliation complete, refresh dependent cache digests, commit, and push the final state.
- [ ] Report branch, commits, Issue URLs, PR URL, validation results, NOT RUN project commands, and remaining Phase 3 scope.
