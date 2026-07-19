# Multi-instance k6 Verification Design

## Goal

Add bounded, reproducible evidence that two interchangeable application instances can serve traffic through one load balancer while sharing MySQL, Redis, and Kafka, preserving the repository's point, order, Outbox, consumer-idempotency, and ranking-recovery invariants.

## Scope

This is verification-only infrastructure. It does not change production Java code, public API contracts, database schemas, feature requirements, or ADR decisions. P0/P1 unit, integration, and API-smoke evidence remains separate from the P2 E2E run.

## Selected approach

Keep `verify.e2e` as the only registered non-Gradle command. Convert `scripts/e2e/verify-e2e.sh` into a thin sequencer that runs:

1. the existing single-instance black-box scenario in `verify-single-instance.sh`; and
2. a new bounded multi-instance/k6 scenario in `verify-multi-instance.sh`.

This preserves the closed command allowlist and avoids expanding the command-registry schema or hiding Docker execution behind Gradle.

## Topology

- MySQL `8.4`, Redis `7.4-alpine`, and Kafka `3.8.0` are shared.
- `app-1` and `app-2` use the same built image and distinct `OUTBOX_PUBLISHER_OWNER` values.
- Both consumers use `coffee-order-analytics`.
- `nginx:1.30.3-alpine` is the only loopback-published endpoint.
- Nginx adds `X-Upstream-Addr` so the test can prove both configured upstream sockets served requests before failure and only the survivor served requests afterward.
- `grafana/k6:2.1.0` runs as a one-shot Compose service; no host k6 installation is required.

## Scenario

1. Start an isolated Compose project and wait for infrastructure, both apps, and nginx.
2. Seed fixture users and one saleable menu in MySQL.
3. Establish point balances through the public API.
4. Repeatedly call the load-balancer endpoint until both upstream addresses are observed.
5. Run bounded k6 normal and same-user contention phases through nginx.
6. Stop `app-1`, require post-stop requests and a new paid order to succeed through `app-2`, and wait for Outbox publication and analytics convergence.
7. Inject one duplicate Kafka message and prove the existing marker/effect counts remain one.
8. Stop mutation traffic, flush Redis, call popular-menu through nginx, compare the response with the MySQL aggregate, and verify cache/marker rebuilding.
9. Validate k6 summaries, print them into runner stdout, and clean up all processes, containers, networks, and volumes unconditionally.

## Evidence and claim boundaries

The scenario asserts fixture-scoped durable invariants:

- every balance is non-negative;
- `SUM(CHARGE) - SUM(USE) = balance`;
- paid orders, successful payments, USE histories, ORDER_PAID Outbox rows, processed markers, and analytics effects converge to the expected relationships;
- no order has more than one payment;
- expected Outbox rows reach `PUBLISHED`;
- duplicate delivery creates no second durable consumer effect;
- a new order completes after one app stops;
- Redis loss does not change the MySQL-derived popular-menu result and the cache is rebuilt.

The run does not claim publisher fairness, durable observation of every claim transition, exactly-once Kafka publication, or global/same-key ordering. The current schema clears claim ownership after completion and has no durable claim audit, so those claims would require production instrumentation outside this scope.

## Load result policy

k6 records throughput, request counts, error counts, and p50/p95/p99 latency as baseline observations. No TPS or latency pass target is invented. Thresholds cover only structural correctness, such as completed checks and absence of unexpected HTTP failures. Machine-readable summaries are written to `build/reports/k6/<compose-project>/k6-summary.json`, validated, and emitted into finalized runner stdout; generated load outputs are not committed.

## Failure handling

Every Compose, k6, SQL, Kafka, and cleanup operation is bounded. Signal traps terminate and reap active child processes. Failure output includes concise service logs and any available k6 summary. Cleanup always removes the isolated project and volumes.

## Registry and documentation

`verify.e2e` keeps its exact argv and disabled parameters. Its `inputPaths` expands to include the umbrella, both scenario scripts, multi-instance Compose file, nginx configuration, and k6 script. During execution reconciliation, the command may temporarily be `CONFIGURED_UNVERIFIED`; it returns to `VERIFIED` only after fresh finalized evidence is recorded. README and environment/quality docs identify the exact images, entry point, scenario path, and result location.

## Alternatives rejected

- A new non-Gradle `verify.multi-instance` command would expand schema/helper trust boundaries and policy contracts for little additional value.
- A Gradle `Exec` wrapper would obscure Docker process ownership and weaken the explicit executable allowlist.

## Approval

Approved by the repository owner on 2026-07-17 in the active Codex task.
