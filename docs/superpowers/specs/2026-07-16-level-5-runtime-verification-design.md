# Level 5 Runtime Verification Design

## Status

Approved by the 2026-07-16 implementation request.

## Routing

- Work Route.
- `specs/004-popular-menu` owns the QueryDSL production-query change.
- `specs/003-order-payment` owns Kafka/Outbox behavior and broker verification.
- `Owning feature: none` applies to the repo-wide command registry, real HTTP smoke, Docker Compose E2E, and completion evidence.

## Goal

Align the repository's documented architecture, production code, real-infrastructure verification, and canonical command registry. Completion requires independent, reproducible commands for build, unit, integration, API smoke, and black-box E2E, all executed only through `scripts/ai/command-runner.sh`.

## Chosen Approach

Use two complementary verification layers.

1. Testcontainers integration tests provide repeatable developer and CI checks for MySQL, Redis, and Kafka. They validate repository queries, transaction boundaries, real broker publication/consumption, idempotency, rollback, and retry behavior.
2. Docker Compose black-box E2E starts the packaged application with MySQL, Redis, and Kafka, drives the public HTTP API, and inspects durable effects and cache state. It proves container wiring, Flyway startup, HTTP contracts, Outbox publication, consumer effects, and cleanup.

Using only Testcontainers would not prove the deployment topology or container networking. Using only Compose would make focused failures slower to isolate. The dual layer is therefore required.

## Production QueryDSL Design

Keep `DailyMenuSalesRepository` as the Spring Data JPA entry point and keep the MySQL native atomic UPSERT unchanged. Move aggregate and daily-metadata reads to a custom repository fragment implemented with `JPAQueryFactory` and generated `QDailyMenuSale` metadata.

The custom implementation returns the existing projection types, filters an inclusive date range, groups by the documented keys, and leaves final popular-menu tie ordering in the existing domain policy. A Spring configuration bean supplies `JPAQueryFactory` from `EntityManager`.

## Kafka Integration Design

A Testcontainers Kafka broker and MySQL container back a Spring integration test. The test invokes the real `OutboxPublisher`, reads the produced record to verify topic/key/envelope, and observes the real `@KafkaListener` consumer's MySQL marker and analytics effect.

Focused cases cover same-group duplicate delivery, independent groups at the analytics service boundary, transactional rollback on analytics persistence failure, and publisher retry state when the broker/send fails. Existing focused MySQL tests remain part of the integration command.

## Real HTTP Smoke Design

`ApiSmokeTest` runs Spring Boot on a random real port and uses Java's HTTP client rather than MockMvc. Testcontainers supplies MySQL and Redis; Kafka listener and scheduled publishing are disabled because broker behavior belongs to the Kafka integration suite. The test seeds only durable fixtures, then verifies menu query, point charge, paid order, popular-menu query, request validation, and representative business errors through actual HTTP request/response pairs.

## Docker Compose E2E Design

Add an application image and an E2E Compose overlay with health checks, internal Kafka addressing, isolated ephemeral volumes, and an application health endpoint or equivalent readiness probe. A POSIX script owns the scenario and installs a cleanup trap before startup.

The scenario starts all four services, waits for Flyway-backed application readiness, seeds a user and menu safely, charges points and places an order over HTTP, then verifies MySQL order/payment/history/daily-sales/Outbox rows. It waits for the Outbox publisher and consumer, verifies processed/analytics rows, checks Redis ranking state and the popular-menu API, injects a duplicate event, and confirms no duplicate analytics effect. It always runs `docker compose down -v --remove-orphans` for its unique project name.

## Official Command Design

Gradle separates tests by class naming:

- `test`: unit and non-infrastructure tests; excludes `*IntegrationTest` and `*ApiSmokeTest`.
- `integrationTest`: includes `*IntegrationTest`.
- `apiSmokeTest`: includes `*ApiSmokeTest`.

The canonical registry exposes:

- `verify.build` -> Gradle assemble/package without executing verification suites.
- `verify.unit` -> Gradle `test`.
- `verify.integration` -> Gradle `integrationTest`.
- `verify.api-smoke` -> Gradle `apiSmokeTest`.
- `verify.e2e` -> the E2E POSIX script.

All commands remain `CONFIGURED_UNVERIFIED` until a finalized official runner artifact proves the exact command passed. Evidence and Markdown summaries must reflect the artifact rather than anticipated success.

## Failure Handling

- QueryDSL tests must fail if date predicates, grouping, or projections are wrong.
- Kafka tests use bounded polling and preserve broker/persistence failures instead of masking them.
- API smoke reports unexpected HTTP 500 responses and captures server-side test output.
- E2E readiness and durable-state checks are bounded; any failure retains concise service logs before cleanup.
- Registry state is never promoted to `VERIFIED` without finalized runtime evidence.

## Deferred Scope

The following remain explicit follow-up work: a real load balancer, deployment of multiple application instances, Redis Sentinel, and an operating-cluster deployment. The implementation remains stateless and uses MySQL/Redis/Kafka coordination so those additions do not require JVM-local ownership.
