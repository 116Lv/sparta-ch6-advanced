# Subagent Workflow

## Purpose

Use this workflow whenever work is delegated to one or more subagents. GitHub Issues provide external task tracking; `ai/work-logs/issue-{number}/` provides durable workflow progress, execution evidence, and recovery context.

The Orchestrator owns issue creation, assignment, reconciliation, GitHub Issue updates, and final issue status. Workers own only their role-specific work log. The Main Dev Agent remains accountable for final consistency and completion decisions.

## Mandatory Routing Gate

Before the Orchestrator creates an issue or dispatches a subagent, follow `ai/document-routing.md`.

1. Run the Mandatory Routing Gate.
2. Record one of these outcomes:
   - `Owning feature: specs/{feature}`
   - `Owning feature: none`
3. If work is feature-owned, read `specs/{feature}/spec.md` before dispatching subject-specific planning, implementation, verification, review, or normative documentation work.
4. Pass the owning feature outcome, routing reason, and files already read to each worker.

Workers must not guess ownership or skip the required feature specification. If the dispatch lacks a routing outcome, the worker must pause and ask the Orchestrator for it.

## Required Dispatch Flow

The Orchestrator follows this sequence:

1. Route the work and record ownership.
2. Define one Issue boundary per cohesive, independently closable work item with shared purpose and acceptance criteria. Multiple subagents or roles may work under that Issue; split only scopes that can be accepted and closed independently.
3. Create a GitHub Issue for each work item using `ai/github-issue-template.md`.
4. Initialize `ai/work-logs/issue-{number}/README.md`, the assigned role log, and `ai/work-logs/index.md`.
5. Assign and dispatch the worker with the required fields below.
6. Reconcile incremental worker logs into the issue summary and GitHub Issue comments.
7. Manage pauses, blockers, and resumption from the recovery record.
8. Dispatch independent review when required evidence is ready and record `status: in_review`.
9. Complete the pre-QA sections of `ai/issue-completion-checklist.md`.
10. Run `ai/qa-gate.md` and record `implementation_status`. When it is `PASS`, set the Issue summary and completed role logs to workflow `status: done`.
11. Create the done claim from `ai/done-claim-template.md`.
12. Complete the closure sections of `ai/issue-completion-checklist.md`, then close the Issue only if every closure condition passes.

For the detailed lifecycle, statuses, and strict fallback rules, use `ai/github-issue-planning.md`.

## Required Handoff Fields

Every subagent handoff must include:

- `tracking_status` plus `issue` and `issue_url`, or the complete `pending_issue` fallback metadata;
- `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and `github_reconciliation_status` when Phase 2B skill or handoff reuse applies;
- current route ID, task phase, `owning_feature`, context status, routing reason, and route-selected files already read;
- unique activated triggers, documents still deferred with the full canonical load-trigger mapping, current include/deferred paths, and re-route triggers;
- Markdown document links to route-selected files and phase-gated files required for this task;
- context links to the GitHub Issue when available, the issue summary, and relevant prior role logs or decisions;
- assigned role, in-scope work, and out-of-scope boundaries;
- decisions already made, open questions, remaining work, and remaining verification/completion evidence;
- work-log path and current workflow `status`; and
- acceptance criteria and evidence required for handoff and review.

Issue-backed delegation sets `activeIssue` with a self-consistent number, exact repository Issue URL, summary, and role refs, then opts in only to that Issue's `README.md` and role logs needed by the assigned worker using exact typed scopes and the matching canonical trigger in `activatedTriggers`. The URL has no trailing slash, query, fragment, credentials, alternate host, port, or scheme. Non-Issue handoffs use `activeIssue: null` and carry no work-log scope or reusable ref. Canonical eligibility without activation does not authorize the scope. Foreign, unlisted, subtree, direct-children, descendant, and excluded reusable scopes remain invalid for every status, including `BLOCKED`. Historical Issue fields are provenance rather than aliases for the active identity. Confirm prior role-log claims against canonical owner documents.

If the work changes phase or activity, re-route before continuing. READY and PARTIAL handoffs activate every trigger mandatory for the selected closed activity and read base plus activated-trigger documents; only BLOCKED may record those as missing. Workflow rediscovery also selects at least one closed subject and materializes only that subject's exact documents. Every read is in scope, no read remains deferred, and activated document or opt-in selections use exact materialized scopes. READY and PARTIAL read all materialized opt-in paths, including every active Issue ref. BLOCKED still preserves canonical trigger arrays and cannot widen or use a foreign activated scope. A feature-required route with no owning feature must not dispatch. A subagent completion report never replaces verification or completion gates.

## Phase-Gated Handoffs

Use feature-spec files in the phase where they are needed:

- Specification Agent: read `spec.md` before drafting or changing requirements.
- Implementation Agent: read `spec.md`, then `plan.md`, before implementation planning or execution.
- Test Agent and API Verification Agent: read `spec.md`, then `tasks.md`, before execution or verification handoff.
- Documentation Agent: for feature-owned normative documentation, read `spec.md` first, then owner documents selected by `ai/document-routing.md`.
- Review Agent: confirm routing, required phase-gated reading, acceptance criteria, verification evidence, and any required documentation updates. Block unsupported completion claims.

## Work Log Rules

Workers initialize or update the assigned `{role}.md` from `ai/work-log-template.md` and keep its metadata current after meaningful work, decisions, command results, verification attempts, or blockers. `tracking_status` records only Issue availability; `status` records only workflow progress. Workers must preserve failed evidence and report the exact recovery point.

The Orchestrator keeps the issue summary, `ai/work-logs/index.md`, and GitHub Issue comments aligned with the role logs. Workers may propose `handoff_needed`, `blocked`, or `done` for their assigned role, but only the Orchestrator sets the final issue status or closes an issue.

On resume, read `README.md` in the issue directory and the latest relevant role log before making changes. Append to an existing role log when the role scope is unchanged.

When reusable context exists, resume from `ai/agent-handoff.json`, `ai/skill-catalog.json`, and the referenced `ai/workflow-cache.json` records before rediscovering repository context.

When verification completeness or task/change applicability is in scope, handoffs must reference `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh`. The handoff must preserve `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mapping evidence by change type. Product commands remain NOT RUN for Phase 2C static/helper gates.

## Pause, Block, And Resume

Before a worker pauses or reports a blocker, the role log must state:

- the current status and exact point reached;
- decisions and files changed so far;
- commands and verification results, including failures;
- blockers with the responsible owner; and
- the next role, Markdown links to required reading, context links to the issue summary and relevant role logs, remaining work, and evidence required.

The Orchestrator then updates the issue summary, index, and GitHub Issue comment. A resumed worker reads these recovery records before continuing.

## `pending_issue` Exception

When GitHub Issue creation is unavailable after an actual attempt, the Orchestrator may use `ai/work-logs/no-issue/{work-key}/` for exactly one intended future Issue boundary. The Issue summary and every role log use `issue: pending`, `tracking_status: pending_issue`, actual workflow `status`, and `reconciliation_required: true`. They must record `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `migration_history`, and all normal handoff evidence.

A complete fallback may pass implementation QA with `implementation_status: PASS`, but it cannot support an unqualified overall `DONE`, an issue-backed claim, reconciliation completion, or Issue closure. Missing or invalid fallback metadata, role logs, or verification evidence remains a QA blocker.

The Orchestrator must later create the one intended Issue, move the full directory to `ai/work-logs/issue-{number}/`, preserve its prior path in `migration_history`, update all metadata and the index, and post a migration summary to GitHub. Linking the old directory or copying selected files is insufficient.

## Agent Roles

### Main Dev Agent

- performs final consistency review;
- confirms code and documentation agree; and
- approves or rejects a completion decision based on evidence.

### Orchestrator Agent

- routes work and defines cohesive, independently closable Issue boundaries;
- creates and assigns GitHub Issues;
- initializes, reconciles, and updates issue summaries and the index;
- manages pauses, blockers, and resume assignments; and
- sets final issue status and performs issue closure after evidence review.

### Specification Agent

- drafts or updates specifications;
- clarifies acceptance criteria and open questions; and
- records requirement and documentation conflicts.

### Implementation Agent

- implements only assigned scope;
- follows documented architecture; and
- records decisions, changed files, commands, and evidence in its role log.

### Test Agent

- writes and runs unit, integration, and regression tests as assigned; and
- records test commands, results, failures, and remaining gaps.

### API Verification Agent

- runs the server and real HTTP requests when API verification is required;
- verifies status codes, response bodies, unexpected 500 responses, and server logs; and
- records exact evidence in its role log.

### Bug Hunter Agent

- investigates edge cases, authorization, validation, regressions, and race conditions; and
- records reproducible findings and evidence.

### Documentation Agent

- updates assigned docs, specs, decisions, and ADRs; and
- records the rationale and links required for completion reporting.

### Review Agent

- independently checks routing, scope, changed files, acceptance criteria, evidence, and QA requirements; and
- blocks final status when evidence is missing, inconsistent, or contradicted.

## Evidence Rules

- Record every meaningful command and its result in the role log.
- Do not hide failed verification attempts or unresolved blockers.
- Do not claim tests or API verification passed unless the relevant commands or requests were actually run.
- The Main Dev Agent and Orchestrator must reject completion without the evidence required by the issue and repository QA rules.
- Follow the completion order exactly: review/evidence ready -> pre-QA checklist -> QA gate -> done claim -> closure checklist and Issue closure.
