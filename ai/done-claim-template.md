# Done Claim Template

Use this format after `ai/qa-gate.md` and before the closure sections of `ai/issue-completion-checklist.md`. State only evidence actually recorded or commands actually run. Use `N/A` only with a reason.

## 1. Summary

What changed, and what is the resulting work status?

## 2. Files Changed

- `path/to/file`: purpose of the change

## 3. Routing And Requirements Covered

- Owning feature: `specs/{feature}` or `none`
- Routing files read:
- Requirements and acceptance criteria covered:

## 4. Delegated-Work Tracking

- Subagents dispatched: `yes` or `no`
- `tracking_status`: `issue_backed` or `pending_issue`
- Workflow `status`: `planned`, `in_progress`, `handoff_needed`, `blocked`, `in_review`, or `done`
- GitHub Issue number: <number when issue-backed; `N/A - creation failed` when pending>
- GitHub Issue URL: <URL when issue-backed; `N/A - creation failed` when pending>
- GitHub Issue state: `open`, `closed`, or `not_created`
- Issue work-log path: `ai/work-logs/issue-{number}/README.md` or approved `no-issue` fallback path
- Involved agent logs:
  - `ai/work-logs/issue-{number}/{role}.md` or `ai/work-logs/no-issue/{work-key}/{role}.md`
- Current owner and recovery state:
- Fallback creation-attempt metadata and evidence: <required when pending; otherwise `N/A - issue-backed`>
- Reconciliation status: `not_applicable`, `complete`, or `pending` with exact remaining steps

When subagents were dispatched, every field in this section is required. For `tracking_status: issue_backed`, a real Issue number, URL, summary, and every involved role log are mandatory. For `tracking_status: pending_issue`, `N/A` Issue fields are valid only with the documented creation failure, exact fallback path, complete metadata, every involved role log, and a reconciliation plan. Missing or invalid data blocks the completion claim; a valid pending fallback blocks only the issue-backed and unqualified overall `DONE` claims described below.

## 5. Commands Executed

List only commands that actually ran. Explicitly identify required commands that were not run.

```bash
./gradlew test
./gradlew integrationTest
curl -i http://localhost:8080/api/example
```

## 6. Test Results

| Command or check | Result | Evidence or notes |
|---|---|---|
| Typecheck/build | PASS/FAIL/NOT RUN | |
| Lint | PASS/FAIL/NOT RUN | |
| Unit test | PASS/FAIL/NOT RUN | |
| Integration test | PASS/FAIL/NOT RUN | |
| End-to-end test | PASS/FAIL/NOT RUN/N/A | |
| Real API verification | PASS/FAIL/NOT RUN/N/A | |

## 7. API Verification Evidence

Complete this section when an API changed.

| Method | Endpoint | Expected | Actual | Result | Evidence |
|---|---|---:|---:|---|---|
| POST | /api/example | 201 | 201 | PASS | command/log link |

## 8. Server Log Review

- Unexpected 500 response: absent/present/not checked
- Unhandled exception: absent/present/not checked
- Relevant log evidence:

## 9. Documentation Updated

- Updated docs, specs, ADRs, and workflow files:
- Documentation not updated: reason:

## 10. Blockers And Remaining Risks

- Blockers:
- Remaining risks or unverified behavior:
- Required next handoff:

## 11. Completion Decision

- `implementation_status`: `PASS`, `FAIL`, `BLOCKED`, or `PARTIAL`
- `tracking_status`: `issue_backed` or `pending_issue`
- `github_issue_closure_status`: `ready_to_close`, `closed`, `not_ready`, or `pending_issue_reconciliation`
- `overall_decision`: `DONE`, `DONE_WITH_CONCERNS`, `BLOCKED`, or `PARTIAL`

Implementation completion, tracking availability, and GitHub Issue closure are separate decisions. `implementation_status: PASS` with `tracking_status: pending_issue` is valid when the fallback is complete, but `overall_decision` must not be `DONE`. Use `DONE_WITH_CONCERNS` when tracking reconciliation is the only remaining concern; otherwise use the decision supported by the remaining blockers or incomplete scope.

An unqualified `overall_decision: DONE` requires workflow `status: done`, `implementation_status: PASS`, `tracking_status: issue_backed`, and `github_issue_closure_status` of `ready_to_close` or `closed`. The closure checklist may verify this done claim exists; the pre-QA checklist must not.
