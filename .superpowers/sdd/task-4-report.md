# Task 4 Report: Random-Port Real HTTP API Smoke

## Status

- Implementation: complete by static inspection.
- Runtime verification: **NOT RUN / NOT PASS**. The supported POSIX command-runner entry point is unavailable on this Windows host.
- Owning feature: none; this suite crosses `specs/001-menu-query`, `specs/002-point-charge`, `specs/003-order-payment`, and `specs/004-popular-menu`.

## Files

- Created `src/test/java/com/ch6/cafe/api/CafeApiSmokeTest.java`.
- Modified `src/main/java/com/ch6/cafe/global/config/SchedulingConfig.java`.
- Modified `src/test/resources/application-test.yml`.
- Updated `ai/work-logs/no-issue/level-5-runtime-verification/implementation-agent.md`.

## Official Commands And Evidence

### RED request

Command:

```text
bash scripts/ai/command-runner.sh run verify.api-smoke --run-id verify-20260716-level5-task4-red-01
```

Result: exit 1 before `command-runner.sh` started. Windows `bash.exe` resolved to WSL and reported that no Linux distribution/POSIX runtime was installed. No `RUN_START`, `PRE_COMMAND`, attempt ID, product process, container, artifact, test count, failure count, error count, skip count, HTTP response evidence, or server log exists. RED was not observed and is not inferred.

### GREEN request

Command:

```text
bash scripts/ai/command-runner.sh run verify.api-smoke --run-id verify-20260716-level5-task4-green-01
```

Result: the same POSIX execution boundary stopped the request before the runner started. No `RUN_START`, `PRE_COMMAND`, attempt ID, product process, container, artifact, test count, failure count, error count, skip count, HTTP response evidence, or server log exists. GREEN/PASS is not claimed.

### Static checks

- `git diff --check`: exit 0.
- Source inspection: `RANDOM_PORT` and `java.net.http.HttpClient` present; MockMvc and TestRestTemplate absent.
- Source inspection: real `MySQLContainer` and Redis `GenericContainer` present with dynamic datasource/Redis/Redisson properties.
- Source inspection: Kafka listener startup and scheduled Outbox publication are disabled for the suite.
- Source inspection: every HTTP response goes through an assertion that rejects status 500 before checking the exact expected status.

Static checks do not prove compilation, application startup, container startup, HTTP behavior, durable state, or server-log cleanliness.

## HTTP Scenarios And Intended Assertions

1. `GET /api/v1/menus` -> exact 200 body for seeded Latte.
2. `POST /api/v1/users/101/points/charge` with 5000 -> exact 200 body; MySQL balance 5000 and one CHARGE history.
3. `POST /api/v1/orders` for the seeded menu -> exact 200 body with dynamic positive order ID, PAID status, payment amount 4000, remaining point 1000; MySQL verifies USE history, order, successful payment, daily sales count, and READY Outbox event.
4. `GET /api/v1/menus/popular?days=7&limit=3` -> exact 200 body with Latte order count 1, backed by real Redis plus durable MySQL fallback/rebuild behavior.
5. Point charge with amount 0 -> exact 400 `INVALID_REQUEST` envelope.
6. Order with only 1000 points -> exact 409 `INSUFFICIENT_POINT` envelope; balance preserved and no USE history, order, payment, daily sales, or Outbox row.

## Self-Review

- Fixtures are inserted by JDBC in FK-safe user-then-menu order; cleanup deletes dependent tables before parents.
- Redis ranking keys are cleared between cases.
- HTTP is not mocked; the client targets the injected random local port.
- JSON uses the repository's Jackson 3 `tools.jackson` API.
- No business rule moved into a controller; the only production change is conditional scheduling configuration.
- Shared `application-test.yml` does not disable Kafka listeners globally, preserving Task 3's real-listener integration test.

## Concerns

- The suite has not compiled or executed on this host. API status/body claims and durable-state assertions remain intended contracts, not observed runtime evidence.
- Server logs could not be reviewed because no application process started.
- A supported POSIX runner with Docker must run `verify.api-smoke` before registry promotion or any completion claim.

## Review Fix Evidence

### Focused source RED

The focused PowerShell source contract exited 1 before the review fix with these five expected violations:

```text
RED: missing second real popular-menu request
RED: missing bounded HttpRequest timeout
RED: missing seven-day completion-marker assertions
RED: missing Redis daily ranking assertion
RED: shared test profile disables Outbox scheduling
```

### Implemented review corrections

- Immediately after the paid order, the test asserts the production daily ZSET score and `generation|totalOrderCount|menuCount` marker for today. This fails if order-side Redis recording is swallowed.
- After the first popular-menu request, the test asserts exactly seven `popular-menu:complete:{date}` markers, validates each production marker encoding and counts, asserts that today is the sole non-empty daily ranking key with menu 201 scored at 1, then sends a second real HTTP request and asserts the same exact response.
- Shared `application-test.yml` no longer sets `outbox.publisher.enabled=false`; the inline smoke property remains, preserving Task 3 scheduling/listener behavior.
- Both GET and POST request builders set a ten-second `HttpRequest` timeout.

### Focused source GREEN

The revised focused source contract exited 0:

```text
GREEN: 7 focused Task 4 source contracts passed
```

This is static source evidence only, not compile or runtime evidence.

### Fresh official runner request

Command:

```text
bash scripts/ai/command-runner.sh run verify.api-smoke --run-id verify-20260716-level5-task4-review-green-01
```

Result: exit 1 before `command-runner.sh` started because Windows `bash.exe` reported no installed WSL distribution/POSIX runtime. No `RUN_START`, `PRE_COMMAND`, attempt ID, process, container, artifact, HTTP evidence, server log, or test/failure/error/skip count exists. PASS is not claimed.
