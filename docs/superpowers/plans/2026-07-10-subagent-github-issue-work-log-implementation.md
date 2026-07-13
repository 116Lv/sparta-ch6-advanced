# Subagent GitHub Issue And Work Log Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use Markdown task syntax for tracking.

**Goal:** Make GitHub Issues and issue-scoped repository work logs the enforceable workflow for delegated agent work.

**Architecture:** GitHub Issues are the external task-tracking layer; `ai/work-logs/issue-{number}/` is the durable execution and recovery layer. Work logs keep Issue availability in `tracking_status` and workflow progress in `status`. Existing document routing remains the ownership gate, while dispatch, QA, reporting, and closure documents enforce the linked evidence flow.

**Tech Stack:** Markdown, YAML frontmatter, GitHub Issues, repository-local AI workflow documents.

## Global Constraints

- Preserve `ai/document-routing.md` as the first routing and ownership gate.
- Group durable logs by GitHub Issue number, not by date.
- Use `tracking_status: issue_backed | pending_issue` only for tracking availability. Use `status: planned | in_progress | handoff_needed | blocked | in_review | done` only for workflow progress.
- Define one Issue as one cohesive, independently closable work item with shared purpose and acceptance criteria. Multiple roles may keep separate logs under that Issue; split only independently acceptable and closable scopes.
- Permit `tracking_status: pending_issue` only after a failed GitHub Issue creation attempt, and require later reconciliation by moving the full fallback directory to `issue-{number}/` and preserving its prior path in `migration_history`.
- Allow a complete fallback to produce `implementation_status: PASS`, but block an unqualified overall `DONE`, an issue-backed claim, reconciliation completion, and GitHub Issue closure while tracking remains pending.
- Enforce the linear completion sequence: review/evidence ready, pre-QA checklist, QA gate, done claim, then closure checklist and Issue closure.
- Do not claim implementation completion or close an Issue without the verification evidence applicable to that decision.
- Use UTF-8 and remove corrupted Korean text from every touched workflow document.

---

### Task 1: Issue Planning, Work Logs, And Dispatch

**Files:**
- Create: `ai/github-issue-planning.md`
- Create: `ai/github-issue-template.md`
- Create: `ai/work-log-template.md`
- Create: `ai/work-logs/README.md`
- Create: `ai/work-logs/index.md`
- Modify: `ai/subagent-workflow.md`

**Interfaces:**
- Consumes: routing outcome from `ai/document-routing.md` and the approved design spec.
- Produces: issue creation rules, reusable templates, issue-scoped log lifecycle, and mandatory dispatch fields.

- [x] Define Issue boundaries by shared purpose and acceptance criteria, with separate role logs for multiple agents under one Issue.
- [x] Define `tracking_status` independently from workflow `status` in every copy-ready YAML record and status table.
- [x] Define when Issues are created, split, resumed, blocked, completed, and reconciled after `tracking_status: pending_issue`.
- [x] Define a copy-ready GitHub Issue body with purpose, ownership, scope, acceptance criteria, evidence, agent, log path, and open questions.
- [x] Define Issue summary and role-specific agent log formats with YAML metadata, `owning_feature: specs/{feature}` or `none`, recovery sections, and migration history.
- [x] Rewrite `ai/subagent-workflow.md` as valid UTF-8 and require issue-backed dispatch, incremental logs, handoff, reviewer evidence, and orchestrator ownership.
- [x] Verify all paths and field names match the design spec.

### Task 2: QA, Completion, And Discovery Integration

**Files:**
- Modify: `ai/qa-gate.md`
- Modify: `ai/done-claim-template.md`
- Modify: `ai/issue-completion-checklist.md`
- Modify: `AGENTS.md`
- Modify: `docs/00-index.md`

**Interfaces:**
- Consumes: Task 1 terms and paths (`issue-{number}`, `tracking_status`, workflow `status`, work-log index, verification evidence).
- Produces: enforceable implementation-QA blockers, completion report fields, Issue closure criteria, linear sequence rules, and repository entry-point links.

- [x] Rewrite touched corrupted documents as valid UTF-8 without weakening existing verification rules.
- [x] Make missing or invalid issue-backed/fallback metadata, logs, or evidence a QA blocker whenever subagents were dispatched.
- [x] Permit a complete fallback to pass implementation QA while keeping overall `DONE`, issue-backed claims, reconciliation completion, and Issue closure blocked.
- [x] Add tracking status, Issue number/URL when available, work-log path, agent logs, implementation status, and reconciliation state to completion reporting.
- [x] Make the checklist enforce review/evidence readiness, pre-QA checks, QA, done claim, then closure checks without requiring a future done claim during pre-QA.
- [x] Add the new workflow documents to `AGENTS.md` and `docs/00-index.md` reading and discovery flows.
- [x] Verify terminology and links match Task 1.

### Task 3: Independent Review And Verification

**Files:**
- Review: all files from Tasks 1 and 2
- Update: `ai/work-logs/index.md`
- Update: current execution logs under `ai/work-logs/issue-8/`

**Interfaces:**
- Consumes: complete documentation diff and approved design.
- Produces: independent spec-compliance verdict, consistency verdict, and fresh verification evidence.

- [x] Have fresh reviewer agents check design coverage, document routing, Issue granularity, tracking/progress separation, completion order, Issue/log lifecycle, encoding, and contradictions.
- [x] Resolve every Critical or Important finding, including the final semantic review findings, through the owning worker and re-review.
- [x] Run link/path, required-section, mojibake, whitespace, and Git diff checks.
- [x] Record the final evidence and the unresolved GitHub authentication blocker in the current execution log.

## Current Plan State

As of 2026-07-10T12:32:53+09:00, implementation, independent review, and durable execution-recording are complete. The final review recorded no Critical, Important, or Minor findings; documentation implementation is Approved, the recovery record is Reliable, and implementation QA is PASS. Separately, GitHub reconciliation is Blocked by GitHub authentication: a real Issue has not been created and the fallback directory has not been migrated to `issue-{number}/`. That external reconciliation blocker does not undo implementation completion, but `tracking_status` remains `pending_issue` and still blocks an issue-backed claim, unqualified overall `DONE`, reconciliation completion, and Issue closure.
