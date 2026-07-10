# GitHub Issue Planning

## Purpose

Use GitHub Issues as the external task-tracking record for dispatched agent work. Use repository work logs as the durable execution and recovery record. This document defines the Orchestrator's required flow before, during, and after dispatch.

`ai/document-routing.md` remains the first gate. An issue never replaces feature specifications, owner documents, ADRs, verification evidence, or the QA gate.

## Ownership

The Orchestrator owns all GitHub Issue state:

- routing the work and recording the owning feature outcome;
- splitting work into dispatchable issues;
- creating, assigning, commenting on, reconciling, and closing issues; and
- setting the final issue and work-log status after reviewing required evidence.

Workers own their role-specific log only. A worker may report progress, blockers, decisions, and evidence, but must not create, assign, reconcile, close, or set the final status of an issue.

## Executable Flow

1. **Route**: Run `ai/document-routing.md` and record `Owning feature: specs/{feature}` or `Owning feature: none`. For feature-owned work, read `specs/{feature}/spec.md` before subject-specific dispatch.
2. **Define Issue Boundaries**: Divide the work into cohesive, independently closable items with a shared purpose and shared acceptance criteria. Keep multiple subagents or roles under one Issue when their scopes contribute to that same closure decision. Split scopes only when each can be accepted and closed independently, not merely because multiple agents participate.
3. **Create GitHub Issue**: The Orchestrator creates one Issue per cohesive work item using [github-issue-template.md](github-issue-template.md). The Issue body must include the routing outcome, required reading, acceptance criteria, evidence required, suggested roles, and expected work-log path.
4. **Initialize Issue Directory**: Create `ai/work-logs/issue-{number}/README.md`, add an entry to `ai/work-logs/index.md`, and initialize each assigned role log from [work-log-template.md](work-log-template.md). Set `issue`, `issue_url`, `tracking_status: issue_backed`, workflow `status`, `owning_feature`, `current_owner`, and `last_updated` before dispatch.
5. **Dispatch**: Give the worker the issue number, issue URL, work-log path, routing outcome, links to files already read and phase-gated files to read, scope, open questions, and evidence required. Include context links to the issue summary and relevant prior role logs. The Orchestrator records the assignment in the issue and issue summary.
6. **Update Incrementally**: Workers update only their role log after meaningful work, decisions, command results, verification attempts, or blockers. The Orchestrator keeps the issue summary, index, and GitHub Issue comments aligned with the worker logs.
7. **Pause, Block, Or Resume**: Before pausing, set the role-log status to `handoff_needed` or `blocked`, record the exact recovery point and next handoff, and notify the Orchestrator. The Orchestrator updates the issue summary, comments on the GitHub Issue, and assigns or resumes the next role. On resume, read the issue summary and latest role log before making changes.
8. **Review And Evidence Ready**: A Review Agent checks routing, scope, changed files, required evidence, unresolved blockers, and consistency with the Issue acceptance criteria. Record the review evidence in a role log and set the Issue summary to `status: in_review` when it is ready for the completion sequence.
9. **Pre-QA Checklist**: Complete the pre-QA sections of `ai/issue-completion-checklist.md`. This stage verifies evidence readiness and must not require a done claim.
10. **QA Gate**: Run `ai/qa-gate.md` and record `implementation_status` from actual verification evidence. When it is `PASS`, set the Issue summary and completed role logs to workflow `status: done` before creating the done claim.
11. **Done Claim**: After QA, create the completion report from `ai/done-claim-template.md`.
12. **Closure Checklist And Issue Closure**: After the done claim exists, complete the closure sections of `ai/issue-completion-checklist.md`. The Orchestrator reconciles all role logs and review evidence, comments on the Issue with the evidence summary, and closes the Issue only when every closure condition passes.

## Issue Planning Rules

- Create Issues before dispatch whenever work is split into trackable units.
- One Issue is one cohesive, independently closable work item with a shared purpose and acceptance criteria.
- Multiple subagents and roles may work under the same Issue and must keep separate role logs.
- Split into separate Issues when scopes can be accepted and closed independently, not merely because multiple agents participate.
- Use one Issue number per Issue directory. Do not group unrelated work under one directory.
- Keep `ai/work-logs/index.md` current whenever an issue starts, pauses, blocks, resumes, or reaches a final status.
- A status of `done` means the role completed its assigned work; it does not authorize issue closure. Only the Orchestrator may set final issue status and close the issue.
- Do not set `done` or close an issue without the evidence required by its issue body and applicable repository verification rules.

## Tracking And Workflow Status Values

Tracking availability and workflow progress are orthogonal. Use both fields in every Issue summary and role log.

| `tracking_status` | Meaning | Owner |
|---|---|---|
| `issue_backed` | A real GitHub Issue number and URL back the work. | Orchestrator |
| `pending_issue` | A documented temporary fallback exists after Issue creation failed. | Orchestrator |

| `status` | Meaning | Owner |
|---|---|---|
| `planned` | Work is defined but is not assigned or dispatched. | Orchestrator |
| `in_progress` | Assigned work is actively being performed. | Assigned role for its log; Orchestrator for issue summary |
| `handoff_needed` | Work paused with a defined next role or recovery point. | Assigned role proposes; Orchestrator confirms |
| `blocked` | Progress cannot continue until a recorded blocker is resolved. | Assigned role proposes; Orchestrator confirms |
| `in_review` | Work is under independent review or has review evidence ready for QA. | Orchestrator |
| `done` | Assigned work or the issue has satisfied its defined criteria. | Orchestrator sets final issue status |

## Strict `pending_issue` Fallback

Use `tracking_status: pending_issue` only when GitHub Issue creation was attempted and is unavailable because of an external failure, such as authentication, authorization, GitHub outage, or network failure. The Orchestrator must set `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `migration_history`, and `reconciliation_required: true` in the temporary Issue summary and every role log.

The temporary directory must be exactly `ai/work-logs/no-issue/{work-key}/`; `{work-key}` must be stable and descriptive. The directory preserves exactly one intended future Issue boundary. Its Issue summary and role logs use `issue: pending`, an empty `issue_url`, `tracking_status: pending_issue`, and the actual workflow `status`. Do not create a date-only Issue directory, invent an Issue number, overload `status`, or use the fallback for convenience.

A complete fallback with valid metadata, all required role logs, and all applicable verification evidence may pass implementation QA with `implementation_status: PASS`. While `tracking_status` remains `pending_issue`, it still blocks an unqualified overall `DONE`, any claim that the work is issue-backed, reconciliation completion, and GitHub Issue closure. Missing or invalid fallback metadata, role logs, or evidence is an implementation-QA blocker.

When GitHub access is restored, the Orchestrator must:

1. Create the GitHub Issue from the original scope and current evidence.
2. Move the entire temporary directory to `ai/work-logs/issue-{number}/` without discarding history. Linking the old directory or copying selected files is not reconciliation.
3. Append the move timestamp, prior `no-issue` path, and final `issue-{number}` path to `migration_history` in the Issue summary and every role log.
4. Update `issue`, `issue_url`, `tracking_status: issue_backed`, `last_updated`, and `reconciliation_required: false` in the Issue summary and every role log. Preserve workflow `status` and the Issue-creation attempt fields.
5. Replace the `no-issue` index entry with the `issue-{number}` entry and preserve the temporary path in the migration record.
6. Add a GitHub Issue comment linking the migrated log directory and summarizing work completed before Issue creation.

The fallback is not fully reconciled until all six steps are complete. Until then, the work must not be reported as issue-backed or closed.

## Required Dispatch Fields

Every dispatch must contain:

- `tracking_status` plus `issue` and `issue_url`, or the complete `pending_issue` fallback metadata;
- `owning_feature` and the routing files read;
- Markdown document links to required and phase-gated reading;
- context links to the issue summary and relevant prior role logs;
- role, scope, acceptance criteria, and out-of-scope boundaries;
- decisions already made and open questions;
- work-log path and current workflow `status`; and
- evidence required for handoff and review.
