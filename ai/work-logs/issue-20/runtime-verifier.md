---
issue: 20
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/20
agent: runtime-verifier
tracking_status: issue_backed
status: done
owning_feature: "none"
current_owner: final-verifier
started_at: 2026-07-16T00:00:00+09:00
ended_at: 2026-07-16T18:16:57+09:00
last_updated: 2026-07-16T19:36:30+09:00
branch: codex/implement-cafe-features
related_files:
  - docs/superpowers/specs/2026-07-16-level-5-runtime-verification-design.md
  - docs/superpowers/plans/2026-07-16-level-5-runtime-verification-implementation.md
changed_files:
  - ai/work-logs/issue-20/runtime-verifier.md
commands_run:
  - verify.build
  - verify.unit
  - verify.integration
  - verify.api-smoke
  - verify.e2e
tests_run: []
blockers: []
skill_ids:
  - superpowers:subagent-driven-development
  - superpowers:systematic-debugging
handoff_state_ref: ai/work-logs/issue-20/README.md
reusable_context_refs: []
not_run_project_commands: []
reconciliation_required: false
github_reconciliation_status: complete
issue_creation_attempted_at: 2026-07-16T00:00:00+09:00
issue_creation_failure_reason: GitHub connector rejected external disclosure because explicit authorization to publish repository planning content was not established.
expected_issue_scope: Apply and independently review the approved Level 5 QueryDSL, real-infrastructure verification, canonical commands, and evidence reconciliation as one cohesive completion unit.
migration_history:
  - moved_at: 2026-07-16T19:36:30+09:00
    from: ai/work-logs/no-issue/level-5-runtime-verification
    to: ai/work-logs/issue-20
    comment_url: https://github.com/116Lv/sparta-ch6-advanced/issues/20#issuecomment-4990893221
---

# Runtime Verifier

## Later Reconciliation

The executable-mode blocker documented by this role was corrected in later local commits. The
final-verifier subsequently ran and finalized all five official commands from a fresh Ubuntu-native
checkout. The failure evidence below remains intentionally preserved as historical diagnosis.

## Status

`DONE_WITH_CONCERNS`: WSL Ubuntu and Docker Desktop are available, but all five official commands
fail closed before a run session can be created because the repository tracks the directly executed
`scripts/ai/workflow-gate.sh` as non-executable (`100644`). No product process was launched.

## Execution Context

- Windows repository: `C:\Users\lbw01\GitHub\sparta-ch6-advanced`
- Windows branch/HEAD supplied and confirmed in the native clone:
  `codex/implement-cafe-features` / `f8ed7a06feb40e1ac2aa1edc9aac94af89e3bcce`
- Explicit distribution: `Ubuntu`
- Linux user: `lbw01`
- Direct mount path: `/mnt/c/Users/lbw01/GitHub/sparta-ch6-advanced`
- WSL-native verification clone: `/home/lbw01/sparta-ch6-advanced-runtime-20260716`
- Docker client/server: `29.5.3` / `29.5.3`, Docker Desktop `4.78.0`
- Docker Compose: `v5.1.4`

The direct `/mnt/c` checkout could not parse the runner because the Windows checkout contains CRLF:

```text
wsl.exe -d Ubuntu --cd /mnt/c/Users/lbw01/GitHub/sparta-ch6-advanced -- bash scripts/ai/command-runner.sh run verify.build --run-id verify-20260716-level5-runtime-build-01
observed Windows invocation exit: 1
scripts/ai/command-runner.sh: line 2: set: -\r: invalid option
```

No repository configuration or tracked content was changed to hide that boundary. A local clone of
the same HEAD was created in the Ubuntu native filesystem. Its runner is LF/POSIX text and Docker is
reachable. The clone initially reported `HELPER_RUNTIME_EVIDENCE_STALE` because canonical evidence
was for Windows Python 3.9.6. The repository preflight was executed with `--record` and passed for
Ubuntu Python 3.14.4/jsonschema 4.19.2. Those preflight changes exist only in the disposable native
clone, not the Windows working repository.

## Root Cause Evidence

`git ls-tree HEAD` and the native checkout agree:

```text
100644 scripts/ai/command-runner.sh
100644 scripts/ai/workflow-gate.sh
100644 scripts/ai/done-claim-check.sh
100755 scripts/e2e/verify-e2e.sh
```

The native checkout reports the first three files as `-rw-r--r--` and the E2E script as
`-rwxr-xr-x`. `command-runner.sh` line 42 uses `exec "$GATE" ...`, so every official RUN_START
terminates with:

```text
scripts/ai/command-runner.sh: line 42: /home/lbw01/sparta-ch6-advanced-runtime-20260716/scripts/ai/workflow-gate.sh: Permission denied
```

An exploratory `chmod` was immediately reverted before the evidence runs. The tracked mode and the
evidence runs remain unmodified.

## Official Command Outcomes

Every row used this exact Windows invocation shape for RUN_START:

```text
wsl.exe -d Ubuntu --cd /home/lbw01/sparta-ch6-advanced-runtime-20260716 -- bash scripts/ai/command-runner.sh start --run-id <run-id> --task-key level-5-runtime-verification
```

Every row then used this exact official command invocation shape:

```text
wsl.exe -d Ubuntu --cd /home/lbw01/sparta-ch6-advanced-runtime-20260716 -- bash scripts/ai/command-runner.sh run <command-id> --run-id <run-id>
```

| Command | Run ID | RUN_START observed exit/result | `run` observed exit/result | Attempt ID | Tests | Failures | Artifact |
|---|---|---|---|---|---:|---:|---|
| `verify.build` | `verify-20260716-level5-runtime-build-05` | 1; shell `Permission denied` | 1; `PRE_COMMAND INVALID_STATE/RUN_ID_INVALID` | none | N/A | N/A | none; run directory unavailable |
| `verify.unit` | `verify-20260716-level5-runtime-unit-01` | 1; shell `Permission denied` | 1; `PRE_COMMAND INVALID_STATE/RUN_ID_INVALID` | none | N/A | N/A | none; run directory unavailable |
| `verify.integration` | `verify-20260716-level5-runtime-integration-01` | 1; shell `Permission denied` | 1; `PRE_COMMAND INVALID_STATE/RUN_ID_INVALID` | none | N/A | N/A | none; run directory unavailable |
| `verify.api-smoke` | `verify-20260716-level5-runtime-api-smoke-01` | 1; shell `Permission denied` | 1; `PRE_COMMAND INVALID_STATE/RUN_ID_INVALID` | none | N/A | N/A | none; run directory unavailable |
| `verify.e2e` | `verify-20260716-level5-runtime-e2e-01` | 1; shell `Permission denied` | 1; `PRE_COMMAND INVALID_STATE/RUN_ID_INVALID` | none | N/A | N/A | none; run directory unavailable |

The exact JSON result for each `run` was:

```json
{"$id":"ai/gateway-result.json","$schema":"ai/schemas/gateway-result.schema.json","data":null,"errors":[{"code":"RUN_ID_INVALID","instancePath":"","message":"run directory is unavailable","schemaPath":""}],"operation":"PRE_COMMAND","reason":"RUN_ID_INVALID","result":"INVALID_STATE","schemaVersion":1}
```

Earlier recovery run IDs retained for completeness:

- `verify-20260716-level5-runtime-build-01`: direct `/mnt/c` CRLF runner parse failure; then native-clone preflight `HELPER_RUNTIME_EVIDENCE_STALE`.
- `verify-20260716-level5-runtime-build-02`: preflight evidence still stale because the first preflight was probe-only, not `--record`.
- `verify-20260716-level5-runtime-build-03`: `RUN_ID_INVALID` because no RUN_START session existed.
- `verify-20260716-level5-runtime-build-04`: RUN_START reached the direct gate exec and failed `Permission denied`.

None of these recovery attempts reserved an attempt, launched Gradle/Docker/Testcontainers/the
application, produced test counts, or created a finalized artifact.

## Failure Classification And Fixer Handoff

- Classification: repository POSIX runner packaging/mode defect, before product execution.
- WSL, the Ubuntu distribution, repository access, Docker CLI/daemon, and Compose are not the blocker.
- Minimal correction candidate: track every shell file that is directly executed by another shell
  entry point with executable Git mode, starting with `scripts/ai/workflow-gate.sh`; verify whether
  `done-claim-check.sh` is also directly executed in the finalization path before choosing its mode.
- Add a regression contract that asserts Git executable mode for directly executed POSIX entry
  points, not only shell syntax or source contents.
- After the fix, repeat Ubuntu `runtime-preflight.sh --record` only when canonical helper evidence is
  stale, then create each RUN_START session and execute all five commands with fresh run IDs.
- Preserve all failures and do not promote registry/QA/completion state from these non-runs.

## Reconciliation Addendum

The executable-mode failures in this role remain preserved as historical evidence. Later
failure-fixer and final-verifier roles corrected them, finalized five replacement PASS runs, and
reconciled the fallback directory to Issue #20. No current runtime or tracking blocker remains in
this role.
