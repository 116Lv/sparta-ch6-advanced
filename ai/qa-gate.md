# QA Gate

Run this gate after review/evidence readiness and the pre-QA checklist, and before creating the done claim. This gate determines `implementation_status`; it does not by itself authorize an overall `DONE` claim or GitHub Issue closure. A failed, missing, or unrecorded required check blocks implementation completion; it is not an implied pass.

## Required Verification Checks

- Typecheck passes.
- Lint passes.
- Unit tests pass.
- Integration tests pass.
- End-to-end tests pass when required.
- Database migration succeeds when the change includes one.
- The server starts when runtime behavior changed.
- A real API request succeeds when API behavior changed.
- No unexpected HTTP 500 response occurs.
- Server logs contain no unhandled exception.
- API response bodies match the documented contract.

## API Verification Rules

Work that changes an API cannot be completed with mock tests alone. Run real HTTP requests against a running server.

Verify each changed endpoint where applicable:

| Case | Expected result |
|---|---|
| Valid request | 2xx |
| Invalid input | 400 |
| Unauthenticated request | 401 |
| Unauthorized request | 403 |
| Missing resource | 404 |
| Duplicate or conflict | 409 |
| Internal failure | No unexpected 500 response |

## Delegated-Work Evidence Gate

This section applies whenever one or more subagents were dispatched. All of the following are mandatory before implementation QA can pass:

- `tracking_status` is exactly `issue_backed` or `pending_issue`, and workflow `status` uses only the canonical progress values.
- Exactly one tracking record exists: a real GitHub Issue-backed record or the complete fallback defined below.
- An Issue summary exists at `ai/work-logs/issue-{number}/README.md` or the approved `ai/work-logs/no-issue/{work-key}/README.md` path.
- A role-specific work log exists beside that summary for every dispatched role.
- The Issue summary links every involved role log and identifies the current owner, tracking status, workflow status, and recovery state.
- Agent logs record their scope, changed files, commands, verification evidence, blockers, and next handoff.
- The tracking record and work logs contain enough evidence to verify the acceptance criteria and required verification level.

For `tracking_status: issue_backed`, a real GitHub Issue number and URL must link to `ai/work-logs/issue-{number}/`. Missing or invalid tracking metadata, an Issue summary, any involved role log, or required verification evidence is a QA blocker. A reviewer must not infer evidence from an oral handoff, an unlinked terminal result, or an unrecorded claim.

### `pending_issue` Exception

GitHub unavailability permits work to continue only through the documented fallback. The temporary directory must preserve exactly one intended future Issue boundary. Its Issue summary and every role log must use `tracking_status: pending_issue`, retain actual progress in workflow `status`, and record `issue_creation_attempted_at`, `issue_creation_failure_reason`, `expected_issue_scope`, `reconciliation_required: true`, and `migration_history`.

When that fallback metadata, all role logs, and all applicable verification evidence are complete and valid, QA may produce `implementation_status: PASS` while `tracking_status` remains `pending_issue`. Pending tracking still blocks an unqualified overall `DONE`, an issue-backed claim, reconciliation completion, and GitHub Issue closure.

Reconciliation later requires creating the one intended Issue, moving the full fallback directory to `ai/work-logs/issue-{number}/`, preserving the old path in `migration_history`, updating all metadata and the index, and posting the migration summary to the Issue. Linking the old directory or copying selected files is not reconciliation.

## Implementation-QA Failure Conditions

Implementation QA fails when any of the following applies:

- Required verification was not run.
- Results or evidence for required verification are missing.
- The server was not started when runtime verification is required.
- A required database migration was not applied.
- A real API request was not performed after an API change.
- An unexpected 500 response occurred.
- Server logs contain an unhandled exception.
- A failed test was ignored.
- Requirements were changed only to make tests pass.
- Documentation and implementation conflict.
- Delegated-work tracking metadata, role logs, fallback metadata, or required evidence is missing or invalid.

Incomplete reconciliation by itself does not fail implementation QA when the documented fallback is otherwise complete. It remains a blocker for issue-backed tracking, unqualified overall `DONE`, reconciliation completion, and Issue closure.

## QA Output

Record exactly one implementation result for the done claim:

- `implementation_status: PASS` when every applicable implementation and delegated-evidence check passes, including a complete fallback when used.
- `implementation_status: FAIL` when a required check fails.
- `implementation_status: BLOCKED` when a required check cannot run or required evidence cannot be obtained.
- `implementation_status: PARTIAL` when explicitly allowed verification passed but the required implementation scope is incomplete.

When `implementation_status` is `PASS`, set the Issue summary and completed role logs to workflow `status: done` before creating the done claim. Do not change `tracking_status` during this transition.

## Reporting Unavailable Verification

When verification cannot run because of the environment, report `BLOCKED` or `PARTIAL`; do not report completion.

Allowed examples:

- `NOT RUN: The project does not yet have a Gradle wrapper.`
- `BLOCKED: A MySQL, Redis, or Kafka test environment is unavailable.`

Disallowed examples:

- `The tests were not run, but the work is complete.`
- `The logic appears correct.`
- `Mock verification proves the real API works.`
