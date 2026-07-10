# Subagent GitHub Issue And Work Log Design

## Context

This repository already uses Markdown documents as the source of truth for agent work, feature specs, ADRs, verification rules, and completion claims. The existing subagent workflow defines handoff contents, but it does not yet define a durable tracking system for work that may be interrupted, resumed, delegated, or audited later.

The chosen design uses GitHub Issues as the external task board and repository work logs as the durable execution record. GitHub Issues answer "what work exists and what state is it in?" Work logs answer "what actually happened, what changed, what evidence exists, and where should the next agent resume?"

## Goals

- Create GitHub Issues before dispatching subagents whenever work can be split into trackable units.
- Keep each GitHub Issue linked to repository-local work logs.
- Store work logs by issue number, not by date, so interrupted work is easy to resume.
- Make logs structured enough for later automation and readable enough for humans.
- Preserve the existing document-routing and feature-ownership rules.

## Non-Goals

- Do not replace `specs/{feature}` documents with GitHub Issues.
- Do not use GitHub Issues as the only source of execution evidence.
- Do not require a separate external tracker besides GitHub Issues.
- Do not create logs for purely conversational planning that does not dispatch or execute subagent work.

## Architecture

The workflow has two linked layers:

1. GitHub Issue layer
   - One issue represents one cohesive, independently closable work item with a shared purpose and shared acceptance criteria.
   - The issue body captures purpose, owning feature, required reading, scope, acceptance criteria, evidence required, suggested agent, and expected work-log path.
   - Issue comments receive summaries when work starts, pauses, blocks, resumes, or completes.

2. Repository work-log layer
   - Work logs live under `ai/work-logs/issue-{number}/`.
   - Each issue directory contains an issue summary file and one or more role logs. Multiple subagents or roles may contribute separate logs under the same Issue.
   - Logs use YAML frontmatter for structured metadata and Markdown sections for human-readable progress.

Recommended structure:

```text
ai/
  github-issue-planning.md
  github-issue-template.md
  work-log-template.md
  subagent-workflow.md
  work-logs/
    README.md
    index.md
    issue-12/
      README.md
      implementation-agent.md
      test-agent.md
      review-agent.md
```

## Issue Creation Rules

Before dispatching subagents, the Main Dev Agent or Orchestrator Agent must:

1. Follow `ai/document-routing.md`.
2. Record `Owning feature: specs/{feature}` or `Owning feature: none`.
3. Split the work into cohesive, independently closable GitHub Issues.
4. Create each GitHub Issue using the repository issue template.
5. Pass the issue number, owning feature outcome, required reading, open questions, and evidence requirements to the assigned subagent.

Issue granularity follows acceptance and closure boundaries, not commit boundaries or agent count. Keep scopes in one Issue when they share one purpose and one set of acceptance criteria, even when implementation, testing, API verification, documentation, and review use different subagents or role logs. Split scopes into separate Issues only when each scope can be accepted and closed independently.

If GitHub access is unavailable after an actual creation attempt, the Orchestrator may create a temporary `no-issue/{work-key}/` directory so progress can continue. The directory preserves exactly one intended future Issue boundary and must record the creation failure, expected Issue scope, and reconciliation requirement. When access returns, move the full directory to `issue-{number}/`; linking it in place is insufficient, and the prior path must remain in `migration_history`.

## GitHub Issue Template

Each generated issue should include these sections:

```md
# Task

## Purpose

## Owning Feature

- Owning feature:
- Routing files read:

## Required Reading

## Scope

## Acceptance Criteria

## Evidence Required

## Suggested Agent

## Work Log

- Local log path:

## Open Questions
```

## Work Log Rules

Work logs are grouped by issue:

```text
ai/work-logs/issue-{number}/README.md
ai/work-logs/issue-{number}/{role}.md
```

`README.md` is the issue-level recovery summary. It shows the GitHub Issue URL when available, tracking status, workflow status, owning feature, current owner, last updated time, and links to all role logs.

Each role log captures the execution history for one agent role on that Issue. If the same role resumes work later, it should append to the existing log unless the scope changed enough to need a new role-specific log.

Each agent log should include structured metadata:

- `tracking_status` records Issue availability and is exactly `issue_backed` or `pending_issue`.
- `status` records workflow progress and is exactly `planned`, `in_progress`, `handoff_needed`, `blocked`, `in_review`, or `done`.
- `owning_feature` is either `specs/{feature}` or `none`.

```md
---
issue: 12
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/12
agent: implementation-agent
tracking_status: issue_backed
status: in_progress
owning_feature: specs/003-order-payment
started_at: 2026-07-09T22:00:00+09:00
ended_at:
last_updated: 2026-07-09T22:30:00+09:00
branch:
related_files: []
changed_files: []
commands_run: []
tests_run: []
blockers: []
reconciliation_required: false
issue_creation_attempted_at:
issue_creation_failure_reason:
expected_issue_scope:
migration_history: []
---
```

Each agent log should include these human-readable sections:

```md
# Summary

# Work Done

# Current State

# Decisions

# Verification Evidence

# Blockers

# Next Handoff
```

## Update Lifecycle

1. Issue created
   - GitHub Issue exists.
   - Issue body contains `Work Log: pending` or the expected path.

2. Subagent starts
   - Create `ai/work-logs/issue-{number}/README.md` if it does not exist.
   - Create or update `ai/work-logs/issue-{number}/{role}.md`.
   - Add the issue to `ai/work-logs/index.md`.
   - Comment on the GitHub Issue with the local log path.

3. Subagent works
   - Update the log after meaningful changes, decisions, failures, verification attempts, or blockers.
   - Keep `last_updated`, `status`, `changed_files`, `commands_run`, `tests_run`, and `blockers` current.

4. Work pauses or blocks
   - Set status to `blocked` or `handoff_needed`.
   - Fill `Current State`, `Blockers`, and `Next Handoff`.
   - Add a GitHub Issue comment summarizing the pause point and linking the local log.

5. Review and evidence become ready
   - Set the issue-summary status to `in_review` and record independent review evidence.
   - Fill `Verification Evidence`, unresolved blockers, and `Next Handoff` in every involved role log.

6. Pre-QA checklist
   - Complete the pre-QA sections of `ai/issue-completion-checklist.md`.
   - Do not require a done claim at this stage; the done claim is created after QA.

7. QA gate
   - Run `ai/qa-gate.md` and record `implementation_status` from actual evidence.
   - A complete, documented fallback may produce `implementation_status: PASS` while `tracking_status` remains `pending_issue`.
   - When implementation QA passes, set the Issue summary and completed role logs to workflow `status: done` before creating the done claim.

8. Done claim
   - Create the report from `ai/done-claim-template.md` after QA.
   - `tracking_status: pending_issue` blocks an unqualified overall `DONE`, an issue-backed claim, reconciliation completion, and GitHub Issue closure even when implementation passes.

9. Closure checklist and Issue closure
   - Run the closure sections of `ai/issue-completion-checklist.md` after the done claim exists.
   - Add a GitHub Issue comment with the summary, changed files, verification evidence, and log path.
   - Close the Issue only when it is issue-backed, reconciliation is complete, and all acceptance criteria and required evidence are satisfied.

## Integration Points

- `ai/subagent-workflow.md` should require issue-backed dispatch and work-log updates.
- `ai/document-routing.md` remains the ownership gate before issue creation.
- `ai/issue-completion-checklist.md` should provide pre-QA checks first and closure checks only after the done claim.
- `ai/qa-gate.md` should treat missing or invalid tracking metadata, work logs, or verification evidence as blockers while allowing a complete fallback to pass implementation QA.
- `ai/done-claim-template.md` should include tracking status, issue data when available, work-log paths, implementation status, and closure status.

## Error Handling

- Missing issue number: stop and ask the Main Dev Agent for the issue number unless explicitly running in `no-issue` fallback mode.
- Missing owning feature outcome: stop and ask for routing output before subject-specific work.
- Missing verification evidence: do not close the issue or claim completion.
- GitHub unavailable: after a failed creation attempt, set `tracking_status: pending_issue`, keep `status` at the actual workflow state, and require complete fallback metadata and evidence.
- Reconciliation: create the one intended Issue, move the full fallback directory to `issue-{number}/`, and preserve the old path in `migration_history`; a link-only reconciliation is invalid.
- Interrupted work: resume from `ai/work-logs/issue-{number}/README.md`, then the latest relevant agent log.

## Testing And Review

This design is documentation and workflow only. Verification should check:

- Required workflow documents exist.
- Templates contain all required sections.
- `ai/subagent-workflow.md` references issue-backed dispatch and issue-scoped work logs.
- Example paths use issue numbers rather than dates.
- Tracking availability and workflow progress use separate, consistent fields and values.
- Completion follows review/evidence readiness, pre-QA checklist, QA gate, done claim, then closure checklist and Issue closure.
- Completion and QA documents preserve routing-first, runtime, real-HTTP, server-log, and work-log evidence requirements.
