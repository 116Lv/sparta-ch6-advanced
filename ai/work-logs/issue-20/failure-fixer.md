---
issue: 20
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/20
agent: failure-fixer
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: repository-owner
started_at: 2026-07-16T17:33:16+09:00
ended_at: 2026-07-16T20:10:58+09:00
last_updated: 2026-07-16T20:28:27+09:00
branch: codex/implement-cafe-features
related_files:
  - docs/superpowers/specs/2026-07-16-level-5-runtime-verification-design.md
  - docs/superpowers/plans/2026-07-16-level-5-runtime-verification-implementation.md
changed_files:
  - scripts/e2e/verify-e2e.sh
  - scripts/ai/tests/test_workflow_helper.py
  - ai/work-logs/issue-20/failure-fixer.md
commands_run:
  - verify.e2e
  - verify.build
  - verify.unit
  - verify.integration
  - verify.api-smoke
tests_run:
  - PosixEntryPointPackagingTests
blockers: []
skill_ids:
  - superpowers:systematic-debugging
  - superpowers:test-driven-development
handoff_state_ref: ai/work-logs/issue-20/README.md
reusable_context_refs:
  - ai/work-logs/issue-20/runtime-verifier.md
not_run_project_commands: []
github_reconciliation_status: complete
reconciliation_required: false
issue_creation_attempted_at: 2026-07-16T00:00:00+09:00
issue_creation_failure_reason: GitHub connector rejected external disclosure because explicit authorization to publish repository planning content was not established.
expected_issue_scope: Apply and independently review the approved Level 5 QueryDSL, real-infrastructure verification, canonical commands, and evidence reconciliation as one cohesive completion unit.
migration_history:
  - moved_at: 2026-07-16T19:36:30+09:00
    from: ai/work-logs/no-issue/level-5-runtime-verification
    to: ai/work-logs/issue-20
    comment_url: https://github.com/116Lv/sparta-ch6-advanced/issues/20#issuecomment-4990893221
---

# Failure Fixer

## Result

The E2E failure was reproduced, traced to lost pipeline input at the POSIX async-command boundary,
fixed with a RED/GREEN regression, and verified by two successful official E2E runs. A second
watchdog lifecycle defect that made every successful bounded command retain its full timeout was
also reproduced behaviorally and fixed before the final five-command verification set.

Local commits:

- `a44d91c fix(e2e): preserve duplicate event stdin`
- `79ae95f fix(e2e): reap watchdog timers promptly`

No push or pull request was performed.

## Systematic Debugging Evidence

The retained failure `verify-20260716-level5-fixed-e2e-03`, attempt
`0bc56311-6cdc-49b7-bd9b-e42f3981ec6a`, exited 1 with
`analytics consumer offset did not become exactly 2`. Apache Kafka 3.8 documentation confirmed
that the console producer writes one event per stdin line and that the consumer-group describe
output exposes the committed current offset used by the script.

A focused POSIX reproduction of the script's async boundary exited 0 but emitted no payload:

```text
printf "payload\n" | { cat <&0 & p=$!; wait "$p"; }
```

This demonstrated that `run_with_watchdog` launched the console producer as an asynchronous list
whose stdin became `/dev/null`. The producer therefore reported success without publishing the
duplicate event. The fix materializes the duplicate JSON into a bounded temporary input file and
redirects that file into the watched child.

The first new regression failed against the old source and the focused packaging suite then passed
5/5 on both Windows and WSL after the fix. Official run
`verify-20260716-level5-fixed-e2e-05`, attempt
`eb5af206-7e5f-4424-a553-0f5f6c35a396`, exited 0 and completed the black-box scenario in 128.8
seconds.

During the preceding preserved run, process-tree inspection showed the watchdog subshell leaving
its `sleep` child alive after successful targets. The behavioral regression ran the real extracted
watchdog function with a five-second timeout: RED retained the timer for 5.53 seconds. A trap-based
attempt remained RED at 5.28 seconds and was replaced rather than layered. The final one-second
condition-polling implementation passed in 1.31 seconds; the full focused class passed 6/6 on
Windows and 6/6 on WSL. `git diff --check` and Git Bash `bash -n scripts/e2e/verify-e2e.sh` also
exited 0.

Interrupted diagnostic run `verify-20260716-level5-fixed-e2e-04`, attempt
`affea551-8d27-44b7-8b1d-b1a9ee0abf34`, was intentionally terminated after the timer leak was
proved. It finalized as exit 130, `FAIL/CHILD_EXIT_NONZERO`, from 08:49:23Z to 09:02:44Z. Its
cleanup logs show Kafka disconnecting, and no E2E or Docker Compose process remained afterward.
This run is retained as failure evidence and is not presented as verification PASS.

## Final Official Runtime Evidence At `79ae95f`

| Command | Run ID | Attempt ID | Exit | Tests | Failures | Artifact |
|---|---|---|---:|---:|---:|---|
| `verify.build` | `verify-20260716-level5-final-build-01` | `9fefbc62-c12c-49e7-bacc-5e4f80d4a7ed` | 0 | N/A | N/A | `.ai-runs/verify-20260716-level5-final-build-01/commands/verify.build/9fefbc62-c12c-49e7-bacc-5e4f80d4a7ed.json` |
| `verify.unit` | `verify-20260716-level5-final-unit-01` | `9ccc610a-fcfd-4c53-a990-dbba2d76ab7e` | 0 | 39 | 0 | `.ai-runs/verify-20260716-level5-final-unit-01/commands/verify.unit/9ccc610a-fcfd-4c53-a990-dbba2d76ab7e.json` |
| `verify.integration` | `verify-20260716-level5-final-integration-01` | `2dacd652-16da-4510-b4d9-e18489235583` | 0 | 35 | 0 | `.ai-runs/verify-20260716-level5-final-integration-01/commands/verify.integration/2dacd652-16da-4510-b4d9-e18489235583.json` |
| `verify.api-smoke` | `verify-20260716-level5-final-api-smoke-01` | `f8109652-c7df-4318-b608-fabcad80711b` | 0 | 2 | 0 | `.ai-runs/verify-20260716-level5-final-api-smoke-01/commands/verify.api-smoke/f8109652-c7df-4318-b608-fabcad80711b.json` |
| `verify.e2e` | `verify-20260716-level5-final-e2e-01` | `fcae2816-dcbc-4732-a624-37ea7923a422` | 0 | 1 scenario | 0 | `.ai-runs/verify-20260716-level5-final-e2e-01/commands/verify.e2e/fcae2816-dcbc-4732-a624-37ea7923a422.json` |

Every command result is `PASS`. The final unit task executed and wrote fresh XML results. The final
integration and API-smoke Gradle tasks were `UP-TO-DATE`; their retained XML reports contain the
listed zero-failure counts. The final E2E run rebuilt the unique Compose project from cached image
layers, exercised the HTTP/MySQL/Redis/Kafka scenario, printed
`Docker Compose black-box E2E scenario completed.`, and cleaned up successfully.

## Handoff

The failure-fixer scope is complete. Registry, QA/completion reconciliation, independent whole-diff
review, and the final verification-before-completion decision remain with the later assigned roles.

## CI Regression Follow-up

PR #19 reported six repository-helper test failures after the five canonical verification commands
were promoted from `CONFIGURED_UNVERIFIED` to `VERIFIED`. This role is resumed to identify the root
cause, reproduce the failure through the supported runner, add a regression-first correction, and
hand the focused diff to independent review. The existing finalized runtime evidence must not be
discarded or downgraded to satisfy stale historical assertions.

### Independent CI Diagnosis

GitHub Actions run `29492190039`, job `87600721409`
(`phase-3b-repository-contract`) ran 551 helper tests and reported exactly six failures. They are
one canonical Level 5 assertion, one Phase 2C current-repository assertion, and four subtests of one
PureResolution status-mapping test. No production, runtime-evidence, registry, schema, or helper
change is indicated by the failure evidence.

The four PureResolution failures are:

- `test_command_id_and_configuration_status_mapping[NOT_CONFIGURED]`
- `test_command_id_and_configuration_status_mapping[UNKNOWN]`
- `test_command_id_and_configuration_status_mapping[STALE]`
- `test_command_id_and_configuration_status_mapping[UNCERTAIN]`

`PureResolutionTests.setUp` copies the current canonical `verify.unit` command, which is now a valid
`VERIFIED` command with a timestamped `lastVerifiedAt`. The loop at
`scripts/ai/tests/test_workflow_helper.py:2205-2209` changes the status, classification, and argv,
but leaves that timestamp in place. The command-registry schema requires `lastVerifiedAt: null` for
all four target statuses (`ai/schemas/command-registry.schema.json:236-250`). Repository-instance
validation runs before command lookup and status mapping
(`scripts/ai/workflow_helper.py:2146-2163`), so the malformed fixture correctly becomes
`INVALID_STATE/5` before the intended `NOT_CONFIGURED/3` or `BLOCKED/2` branch can execute.

Minimal TDD correction: add `command["lastVerifiedAt"] = None` beside the three existing coherent
fixture mutations at `scripts/ai/tests/test_workflow_helper.py:2206-2208`. Keep the four expected
resolver outcomes unchanged. This fixes the fixture, not the registry or resolver, and directly
proves that each schema-valid non-VERIFIED state reaches its existing mapping.

The remaining historical assertions are stale:

1. `Phase2CVerificationGateTests.test_phase_2c_repository_artifacts_and_registry_verified_remain_absent`
   at `scripts/ai/tests/test_workflow_helper.py:11589-11602` still treats the current repository as
   permanently frozen at the Phase 2C pre-runtime state. Keep the checks that no `.ai-runs`,
   `artifact-manifest.json`, or `run.json` files are committed, but rename the test accordingly and
   remove the line 11602 assertion that no command may be `VERIFIED`. If Phase 2C's historical
   no-promotion rule still needs direct coverage, express it against a Phase 2C fixture/output, not
   against the later reconciled canonical registry.
2. `Level5CanonicalVerificationCommandTests.test_canonical_verification_commands_and_gradle_test_boundaries`
   at `scripts/ai/tests/test_workflow_helper.py:15210-15226` was authored before runtime
   reconciliation. Its three assertions per command require `CONFIGURED_UNVERIFIED`, null
   `lastVerifiedAt`, and static-only evidence, producing fifteen violation strings inside one test.
   Replace those expectations with `VERIFIED`, a non-null schema-valid verification timestamp, and
   at least one `RUNTIME_COMMAND` evidence entry for each of the five canonical commands. Preserve
   the exact argv, SAFE classification, disabled parameters, Gradle wrapper evidence, Gradle test
   boundaries, and semantic-validation assertions.

The registry promotion in `d5ed386` satisfies the existing VERIFIED schema contract: executable
argv, SAFE classification, runtime evidence, and a timestamp are all present. Downgrading commands,
removing runtime evidence, or weakening schema/helper validation would conceal the stale tests and
is not a valid fix.

### TDD Correction And Verification

The attached GitHub Actions output and a fresh Ubuntu-native checkout reproduced the exact six
failures across three helper test methods. The resolver fixture now clears `lastVerifiedAt` when it
constructs a non-VERIFIED command. The Phase 2C historical test continues to reject committed run
artifacts but no longer prohibits a later, evidence-backed registry promotion. The Level 5 canonical
test now requires all five commands to be `VERIFIED`, timestamped, and backed by
`RUNTIME_COMMAND` evidence while retaining the exact argv, SAFE classification, disabled parameters,
wrapper evidence, Gradle boundaries, and registry semantic validation.

The new canonical evidence-path assertion then failed RED for all five commands because the registry
still referenced the migrated-away `no-issue` final-verifier log. The registry and generated summary
now point to `ai/work-logs/issue-20/final-verifier.md` and retain the finalized artifact references.

- Official product-unit check before helper correction: run
  `verify-20260716-ci-regression-unit-red-03`, attempt
  `448b328a-a70e-4810-89ca-3b4a146901d6`, exit `0`, 39 tests, 0 failures.
- Focused helper RED: 3 methods, 6 failures matching the attached CI output.
- Initial focused GREEN: 3 methods, `OK`.
- Evidence-path RED: 1 method, five missing Issue #20 evidence violations.
- Final focused GREEN: 3 methods, `OK`.
- Full Ubuntu-native helper suite: 551 tests in 189.384 seconds, `OK`.
- Official product-unit GREEN after registry correction: run
  `verify-20260716-ci-regression-unit-green-01`, attempt
  `2f5d5e62-f89b-461a-b8c8-f54382cd62ea`, exit `0`, 39 tests, 0 failures,
  0 errors, 0 skips.

No production code, command runner, schema, Gradle task, API behavior, or runtime evidence was
downgraded. The focused diff is ready for independent review.

Refreshed GitHub Actions run `29494202619`, job `87607202842`, passed the
`phase-3b-repository-contract` check in 5m6s after commit `8e94339` was pushed. Independent review
and final verification both reported Critical 0, Important 0, Minor 0. This resumed failure-fixer
scope is complete.
