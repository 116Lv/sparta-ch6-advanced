# Issue Completion Checklist

This checklist has three checkpoints in one linear sequence:

1. review/evidence ready -> pre-QA checklist;
2. QA gate -> done claim;
3. closure checklist -> GitHub Issue closure.

Complete **Before Implementation**, **During Implementation**, and **Pre-QA Readiness** before running `ai/qa-gate.md`. Do not require a done claim during pre-QA; create it after QA. Return to the post-claim closure phase only after that done claim exists.

## Before Implementation

- [ ] The Work Route ownership gate in `ai/document-routing.md` was completed.
- [ ] The owning feature outcome is recorded as `specs/{feature}` or `none`.
- [ ] The required owner documents and feature-spec files were read.
- [ ] Acceptance criteria and the verification level are clear.
- [ ] Open questions are resolved or explicitly recorded.
- [ ] Before dispatch, exactly one of these mutually exclusive records exists:
  - A real GitHub Issue-backed dispatch with `tracking_status: issue_backed`, its number, URL, and expected work-log path in the handoff; or
  - After a failed GitHub Issue creation attempt, a documented `no-issue/{work-key}/` fallback with `tracking_status: pending_issue`, actual workflow `status`, complete failure metadata, and a reconciliation plan.
- [ ] The Issue or fallback directory represents exactly one cohesive, independently closable work item with shared purpose and acceptance criteria; multiple participating agents use separate role logs under that same boundary.

## During Implementation

- [ ] The documented layer and architecture rules were followed.
- [ ] New decisions are recorded in `decisions.md` or an ADR when required.
- [ ] Temporary code, unapproved TODOs, and debug logging were not left behind.
- [ ] Error handling was not hidden.
- [ ] Every dispatched agent updated its role-specific log after meaningful work, a failure, verification, a blocker, or a handoff.
- [ ] The Issue summary links all involved role logs and identifies `tracking_status`, workflow `status`, and current owner.

## Pre-QA Readiness

- [ ] Independent review is complete, required evidence is ready, and the Issue summary uses `status: in_review`.
- [ ] `tracking_status` and workflow `status` use only their canonical values and are not conflated.
- [ ] Commands, results, and verification evidence required by the selected verification level are recorded.
- [ ] API changes include real HTTP request evidence against a running server.
- [ ] Unexpected 500 responses were checked and absent, and server logs were reviewed when runtime verification is required.
- [ ] Documentation update needs were reviewed and completed where required.
- [ ] Every dispatched role log records scope, changed files, commands, evidence, blockers, and the next handoff or completion state.
- [ ] When `tracking_status: issue_backed`, a real Issue number/URL, Issue summary, and all role logs are linked.
- [ ] When `tracking_status: pending_issue`, the Issue summary and every role log contain `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `reconciliation_required: true`, and `migration_history`.

After this section passes, run `ai/qa-gate.md` and record `implementation_status`. A complete fallback may produce `implementation_status: PASS`. When QA passes, set the Issue summary and completed role logs to workflow `status: done`, then create the done claim from `ai/done-claim-template.md` before continuing below.

## Post-Claim Closure Phase

Run this phase only after the QA result and done claim exist. While `tracking_status` is `pending_issue`, report `pending_issue_reconciliation`; do not report an issue-backed claim, reconciliation completion, unqualified overall `DONE`, or GitHub Issue closure.

### Phase 2C Verification Gate

- [ ] `ai/verification-gates.md`, canonical `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh` were used or explicitly reported as NOT RUN with a reason.
- [ ] The selected change type records task/change applicability and verification completeness.
- [ ] `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mappings match the selected change type.
- [ ] Product commands remain NOT RUN unless separately executed through the supported evidence path.

### `pending_issue` Reconciliation

Complete these checks when the work used the fallback; otherwise record them as not applicable.

- [ ] A real Issue was created for the one original intended Issue boundary, without merging or splitting unrelated scope during migration.
- [ ] The full `ai/work-logs/no-issue/{work-key}/` directory was moved to `ai/work-logs/issue-{number}/`. Link-only reconciliation or copying selected files was not used.
- [ ] The prior fallback path, final Issue path, and move timestamp are preserved in `migration_history` in the Issue summary and every role log.
- [ ] `issue`, `issue_url`, `tracking_status: issue_backed`, `last_updated`, and `reconciliation_required: false` are updated in every migrated record while workflow `status` and creation-failure history are preserved.
- [ ] `ai/work-logs/index.md` replaces the fallback entry with the final path, and the GitHub Issue contains the migration summary.

### GitHub Issue Closure

- [ ] A done claim created from `ai/done-claim-template.md` exists and records `implementation_status: PASS`.
- [ ] Current tracking records use `tracking_status: issue_backed`, and the Issue summary uses workflow `status: done`.
- [ ] A real GitHub Issue number and URL are linked to the work.
- [ ] The Issue body or comments contain the final summary, changed files, verification evidence, blockers, and local work-log path.
- [ ] `ai/work-logs/issue-{number}/README.md` exists and links every involved role log.
- [ ] Every involved role log records its final workflow status, evidence, blockers, and next handoff or completion state.
- [ ] The Issue acceptance criteria and all required QA evidence are satisfied.
- [ ] The Issue has no unresolved blocker or required follow-up.
- [ ] The Issue was closed only after all prior closure checks passed.
