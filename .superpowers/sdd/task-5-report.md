# Task 5 Report: Docker Compose Black-Box E2E

## Status

Implementation authored and statically inspected. Runtime verification, pre-QA, and QA are
`BLOCKED` because the current Windows host has no supported POSIX/WSL runtime. No command is
reported as PASS and the registry remains `CONFIGURED_UNVERIFIED`.

## Implementation

- Added a multi-stage Java 21 application image with an image-local HTTP readiness dependency.
- Removed fixed container names from the development topology and added dependency health checks.
- Added a standalone E2E topology with `app`, `mysql`, `redis`, and `kafka`, internal service DNS,
  dynamic loopback-only app port, Flyway startup, health dependencies, and an ephemeral named volume.
- Added a strict no-argument POSIX scenario with a unique Compose project name, bounded readiness
  and durable polling, concise failure logs, and unconditional `down -v --remove-orphans` cleanup.
- The scenario seeds only durable user/menu fixtures, charges and pays over real HTTP, verifies the
  MySQL order/payment/history/daily-sales/Outbox graph, waits for `PUBLISHED`, verifies the consumer
  marker and analytics effect, checks Redis and popular-menu HTTP, injects the same `ORDER_PAID`
  envelope through Kafka, and proves marker and analytics counts remain one. The duplicate proof
  fails on consumer-group describe errors, missing topic rows, or invalid offsets; establishes a
  positive committed offset stable across consecutive bounded observations; injects exactly one
  duplicate; and requires the same group to commit exactly `baseline + 1` before checking counts.
- Charge, order, order ID, and popular-menu response assertions use Python stdlib structural JSON
  parsing with exact field/type/value checks; no regex/sed JSON extraction remains.
- Reconciled canonical registry static evidence without promotion and corrected its E2E input glob.
- Resolved the quality-document command/Testcontainers questions and retained load balancer,
  multi-instance deployment, and Redis Sentinel as explicit future work.

## Static Evidence

- Registry JSON parsed successfully with Python stdlib.
- Focused source contracts: PASS (static only), covering scoped cleanup, bounded waits, real Kafka
  producer/group observation, durable analytics, Redis ranking, service DNS, and absence of fixed
  E2E `container_name`.
- `git diff --check`: exit 0.
- Compose YAML parser: NOT RUN because PyYAML is unavailable.
- `bash -n`: NOT RUN because only the unsupported Windows WSL launcher is available.
- No static observation is treated as application build, Compose startup, migration, API, or E2E PASS.

### Task 5 Review RED/GREEN

- Focused RED against commit `825ec53`: 8/8 expected findings reproduced; consumer observation
  errors could be hidden/coerced to zero, advancement was only `> baseline`, response JSON used
  regex/sed, the registry summary timestamp drifted, and the implementation log retained stale state.
- Focused GREEN after correction: 8/8 contracts passed for fatal describe/missing/invalid offset
  handling, stable positive baseline, exact `baseline + 1`, structural response JSON, registry
  timestamp alignment, and current Task 5 blocker/handoff text.
- Registry JSON parse: PASS. `git diff --check`: exit 0. These remain static-only results.

### Final Python Portability RED/GREEN

- Focused source RED: 4/4 expected findings reproduced—the script hard-coded `python`, had no
  `python3`-first absolute resolver, all three parsers bypassed a shared command, and the report
  wording required normalization.
- Focused source GREEN: 7/7 contracts passed. The script resolves one absolute executable path once,
  tries `python3` before `python`, verifies executability and stdlib `json` usability, fails clearly
  when neither candidate works, and uses `"$PYTHON"` for all three structural parsers.
- A further official E2E request was not repeated because the immediately preceding review-fix
  request already proved this unchanged host cannot start the POSIX runner. Runtime remains
  NOT RUN/BLOCKED; no result is inferred from the source correction.

## Fresh Official Requests

| Command | Requested run ID | Launcher exit | Attempt / counts / artifact | Outcome |
|---|---|---:|---|---|
| `verify.build` | `verify-20260716-level5-task5-final-build-01` | 1 | none | runner did not start; NOT RUN/BLOCKED |
| `verify.unit` | `verify-20260716-level5-task5-final-unit-01` | 1 | none | runner did not start; NOT RUN/BLOCKED |
| `verify.integration` | `verify-20260716-level5-task5-final-integration-01` | 1 | none | runner did not start; NOT RUN/BLOCKED |
| `verify.api-smoke` | `verify-20260716-level5-task5-final-api-smoke-01` | 1 | none | runner did not start; NOT RUN/BLOCKED |
| `verify.e2e` | `verify-20260716-level5-task5-final-e2e-01` | 1 | none | runner did not start; NOT RUN/BLOCKED |
| `verify.e2e` review fix | `verify-20260716-level5-task5-review-fix-e2e-01` | 1 | none | runner did not start; NOT RUN/BLOCKED |

Each request invoked `bash scripts/ai/command-runner.sh run <command> --run-id <id>`. Windows
`bash.exe` reported that no WSL distribution was installed before `command-runner.sh` could start.
Therefore there is no RUN_START, PRE_COMMAND, attempt ID, process exit, infrastructure, test count,
finalized artifact, or reconcilable runtime evidence for any request.

## Gates And Review

- Pre-QA: `BLOCKED` because all required product evidence is unavailable.
- QA: `implementation_status: BLOCKED` under the critical-data/user-flow Level 5 policy.
- Completion: `overall_decision: BLOCKED`; no PASS done claim exists.
- Independent whole-branch review: pending controller/reviewer handoff; no independent verdict is invented.

## Blockers And Next Evidence

A supported POSIX runner with Docker Engine/Compose must rerun all five commands separately, retain
their finalized artifacts, reconcile the registry only from those artifacts, and perform the
independent final review and completion gates. Runtime gates and feature runtime checklist items
must remain unchecked until that evidence exists.

## Final Whole-Branch Review Fix Wave

The independent final static review returned Critical 0, Important 3, plus Minor/evidence findings.
All findings were addressed in one source/document wave:

- Every potentially blocking Compose client operation now runs through a portable POSIX process
  watchdog. Startup, port discovery, every exec/admin/producer operation, failure `ps`/logs, and
  cleanup are bounded. Log capture and `down -v --remove-orphans` use separate deadlines, and cleanup
  preserves the original failure status. A forced-hang runtime helper check was NOT RUN because this
  host has no usable POSIX shell; static watchdog coverage is not reported as runtime proof.
- Outbox claimability, `claimed_at`, `claim_until`, publication completion, and failure timestamps
  now use repository-provided MySQL `CURRENT_TIMESTAMP` aligned with DATETIME column precision inside their transactions. The authored
  MySQL integration case pins the session DB clock to 2030 and asserts claimed time equals DB time,
  lease expiry equals DB time plus 30 seconds, and the value is separated from JVM wall time.
- The development Compose topology is explicitly local-only, binds MySQL/Redis/Kafka to loopback,
  parameterizes local ports and MySQL credentials, and retains coherent internal/external Kafka listeners.
- The runtime image uses an owned jar and non-root `cafe` user.
- E2E now asserts final point balance 7000, marker metadata `generation|1|1`, a repeated structural
  popular-menu response, and unchanged marker generation across the cache-hit request.
- Task 3 wording and reviewer/issue/index state were reconciled without a runtime-completion claim.

Focused source RED reproduced 8/8 findings against the prior state. Focused source GREEN passed 9/9
contracts after correction. Registry JSON parsing and `git diff --check` also passed as static checks.

Fresh official requests:

| Command | Requested run ID | Launcher exit | Runtime evidence |
|---|---|---:|---|
| `verify.integration` | `verify-20260716-level5-final-review-integration-01` | 1 | none; runner did not start |
| `verify.e2e` | `verify-20260716-level5-final-review-e2e-01` | 1 | none; runner did not start |

Both requests stopped at the Windows WSL launcher before RUN_START/PRE_COMMAND. No attempt ID,
process, infrastructure, test count, or finalized artifact exists. Integration/E2E, QA, registry
promotion, and overall completion remain NOT RUN/BLOCKED pending supported execution and re-review.

## Second Final-Review Fix Wave

- Focused source RED reproduced 4/4 findings: marker snapshot preceded the rebuilding request,
  cleanup did not explicitly terminate tracked active processes, the repository requested
  microseconds beyond DATETIME precision, and the lease test read managed entity state.
- Focused source GREEN passed 9/9 contracts. The first popular request now rebuilds the seven-day
  state, all seven marker values/generations are validated and snapshotted afterward, the second
  request is verified structurally, and its post-request seven-marker snapshot must be identical.
- The watchdog records active Compose target/watchdog PIDs in shared state. Cleanup disables traps,
  terminates and reaps both before failure logs/down, then uses new independently bounded watchdogs.
  Normal completion kills/reaps the watchdog and clears PID state. A helper-only forced-signal test
  was NOT RUN because this host has no usable POSIX shell; static inspection is not signal-runtime proof.
- Repository time now uses second-precision MySQL `CURRENT_TIMESTAMP`, aligned with schema DATETIME.
  The integration test flushes the claim and reads `claimed_at`/`claim_until` directly via JDBC,
  proving the authored assertions target durable values rather than managed entity fields.
- Registry JSON parsing and `git diff --check` passed as static checks.

Fresh official requests `verify-20260716-level5-second-final-integration-01` and
`verify-20260716-level5-second-final-e2e-01` each exited 1 at the Windows launcher before runner
startup. No RUN_START, PRE_COMMAND, attempt, process, infrastructure, count, or artifact exists;
runtime status remains NOT RUN/BLOCKED.
