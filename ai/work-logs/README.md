# Work Logs

Repository work logs are the durable execution and recovery record for delegated work. GitHub Issues remain the external task-tracking layer; work logs capture workflow progress, commands, verification evidence, blockers, and next handoff.

Follow [github-issue-planning.md](../github-issue-planning.md) and [work-log-template.md](../work-log-template.md). `ai/document-routing.md` is always the ownership gate before issue creation or dispatch.

## 현재 상태를 확인하는 기준

현재 상태는 먼저 [index.md](index.md)를 보고, 그다음 각 `issue-{number}/README.md`의 frontmatter를 확인한다. 역할별 로그와 본문의 `pending`, `blocked`, `Issue remains open` 같은 문구는 해당 시점의 실행 이력일 수 있으며 현재 상태를 뜻하지 않는다. GitHub Issue가 종료된 뒤에는 인덱스와 Issue 요약을 `issue_backed`, `status: done`, reconciliation 완료 상태로 갱신하되, 실패·검증 이력 자체는 삭제하지 않는다.

When Phase 2B skill or handoff reuse applies, issue summaries and role logs must carry `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and `github_reconciliation_status`. Use `ai/agent-handoff.json`, `ai/skill-catalog.json`, and `ai/workflow-cache.json` before rediscovering reusable workflow context.

When Phase 2C verification gates apply, issue summaries and role logs must link `ai/verification-gates.md`, canonical `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh`. Record verification completeness, task/change applicability, and the `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mapping by change type. Product commands remain NOT RUN for static/helper gates.

## Directory Layout

```text
ai/work-logs/
  index.md
  issue-{number}/
    README.md
    {role}.md
  no-issue/
    {work-key}/
      README.md
      {role}.md
```

Each `issue-{number}` directory represents exactly one cohesive, independently closable GitHub Issue with shared purpose and acceptance criteria. Multiple subagents or roles may contribute separate `{role}.md` logs under that Issue. Split directories only when scopes can be accepted and closed independently, not because multiple agents participate. Its `README.md` is the Issue-level recovery summary. Update the Issue summary and index whenever tracking status, workflow status, or ownership changes.

## Lifecycle

1. The Orchestrator routes work, defines cohesive Issue boundaries, then creates a GitHub Issue for each independently closable item.
2. The Orchestrator initializes `issue-{number}/`, its issue summary, the assigned role log, and the index entry before dispatch.
3. Workers update only their role log after meaningful progress, decisions, command results, verification attempts, or blockers.
4. On pause or block, workers record the recovery point and notify the Orchestrator. The Orchestrator updates the issue summary, index, and GitHub Issue.
5. A Review Agent records independent evidence and the Orchestrator marks the Issue summary `status: in_review` when evidence is ready.
6. Complete the pre-QA sections of `ai/issue-completion-checklist.md`, then run `ai/qa-gate.md`. When implementation QA passes, set completed work to workflow `status: done`.
7. Create the done claim from `ai/done-claim-template.md` after QA.
8. Complete the closure sections of `ai/issue-completion-checklist.md`. The Orchestrator reconciles evidence, updates GitHub, and closes the Issue only when every closure condition passes.

## `pending_issue` Fallback

`no-issue/{work-key}` is a temporary exception, not an alternate tracking system. It is permitted only after a recorded GitHub Issue creation failure, preserves exactly one intended future Issue boundary, and must use `tracking_status: pending_issue` with `reconciliation_required: true`. Workflow `status` continues to record actual progress.

A complete fallback may pass implementation QA with `implementation_status: PASS`. It still blocks an unqualified overall `DONE`, an issue-backed claim, reconciliation completion, and Issue closure. Missing or invalid fallback metadata, role logs, or verification evidence blocks implementation QA.

The Orchestrator must later create the one intended Issue, move the full fallback directory to `issue-{number}/`, update every metadata record and the index, preserve the prior path in `migration_history`, and comment on the new Issue with the migration summary. Linking the old directory or copying selected files is not reconciliation.

## Update Discipline

- Use the exact metadata and section names from [work-log-template.md](../work-log-template.md).
- Preserve command outputs and failed verification attempts; do not replace them with conclusions.
- Do not mark an issue closed from a worker log. Only the Orchestrator owns final issue status and closure.
- Resume from the issue summary and most recent relevant role log before making new changes.
