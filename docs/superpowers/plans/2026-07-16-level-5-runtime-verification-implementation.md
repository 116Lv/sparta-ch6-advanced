# Level 5 Runtime Verification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Apply QueryDSL to production aggregation queries and add real MySQL, Redis, Kafka, HTTP, and Docker Compose verification behind five canonical runner commands.

**Architecture:** Spring Data JPA remains the CRUD/native-UPSERT entry point while a QueryDSL repository fragment owns aggregate reads. Testcontainers provides focused integration and real-server smoke suites; a Compose script provides black-box topology verification. The canonical registry is configured before product tests run and is promoted only from finalized runner evidence.

**Tech Stack:** Java 21, Spring Boot 4.1.0, Gradle, QueryDSL 5.1.0 Jakarta, MySQL 8.4, Redis 7.4, Kafka 3.8/Testcontainers, JUnit 5, Docker Compose, POSIX shell.

## Global Constraints

- Run Gradle, build, tests, servers, Docker Compose, HTTP, DB, migration, seed, and infrastructure commands only through `scripts/ai/command-runner.sh`.
- Preserve the existing uncommitted Spring Boot 4/Jackson 3/test-fixture compatibility changes.
- Keep the `daily_menu_sales` atomic increment as a MySQL native UPSERT.
- Do not promote any command to `VERIFIED` without finalized official runner evidence.
- Use real MySQL, Redis, Kafka, random-port HTTP, and Docker Compose for the scopes assigned below.
- Keep the application stateless; do not introduce JVM-local ownership or locks.
- Do not implement a load balancer, multiple deployed application instances, Redis Sentinel, or an operating-cluster deployment.
- Do not push or create a pull request.

---

### Task 1: Canonical Verification Commands and Test Boundaries

**Owning feature:** none

**Files:**
- Modify: `build.gradle`
- Modify: `ai/command-registry.json`
- Modify: `ai/command-registry.md`
- Test: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces Gradle tasks `test`, `integrationTest`, and `apiSmokeTest`.
- Produces registry commands `verify.build`, `verify.unit`, `verify.integration`, `verify.api-smoke`, and `verify.e2e` with fixed argv and `SAFE` classification.
- `verify.e2e` points to `scripts/e2e/verify-e2e.sh`, which Task 5 creates; until then it is configured but expected to fail because the executable is absent.

- [ ] **Step 1: Add a failing static contract test**

Add a focused helper test that parses `build.gradle` and `ai/command-registry.json` and asserts these exact mappings:

```text
verify.build       -> ./gradlew assemble
verify.unit        -> ./gradlew test
verify.integration -> ./gradlew integrationTest
verify.api-smoke   -> ./gradlew apiSmokeTest
verify.e2e         -> ./scripts/e2e/verify-e2e.sh
```

It must assert `CONFIGURED_UNVERIFIED`, `SAFE`, no parameters, and no `VERIFIED` evidence before runtime execution.

- [ ] **Step 2: Run the focused static test and verify RED**

Run the repository's static/helper test path (not a product command). Expected: FAIL because four registry commands are unavailable/not configured and the Gradle test tasks do not exist.

- [ ] **Step 3: Implement Gradle suite separation**

Configure:

```gradle
tasks.named('test') {
    useJUnitPlatform()
    exclude '**/*IntegrationTest.class', '**/*ApiSmokeTest.class'
}

tasks.register('integrationTest', Test) {
    description = 'Runs real-infrastructure Testcontainers integration tests.'
    group = 'verification'
    testClassesDirs = sourceSets.test.output.classesDirs
    classpath = sourceSets.test.runtimeClasspath
    useJUnitPlatform()
    include '**/*IntegrationTest.class'
    shouldRunAfter tasks.named('test')
}

tasks.register('apiSmokeTest', Test) {
    description = 'Runs random-port real HTTP API smoke tests.'
    group = 'verification'
    testClassesDirs = sourceSets.test.output.classesDirs
    classpath = sourceSets.test.runtimeClasspath
    useJUnitPlatform()
    include '**/*ApiSmokeTest.class'
    shouldRunAfter tasks.named('integrationTest')
}
```

Update the registry and Markdown summary with the exact argv above. Set configuration to `CONFIGURED_UNVERIFIED`, classification to `SAFE`, and static evidence only.

- [ ] **Step 4: Run focused static GREEN, then official baseline commands**

First rerun the static contract and expect PASS. Then use separate official run IDs through `scripts/ai/command-runner.sh` for `verify.build` and `verify.unit`. Record every run/attempt ID and exact counts in the issue work log; do not hide failures.

- [ ] **Step 5: Independent review and commit**

Review exact command isolation, registry/schema validity, and preservation of existing compatibility changes. Fix Critical/Important findings, re-review, then commit.

### Task 2: QueryDSL Production Aggregation

**Owning feature:** `specs/004-popular-menu`

**Files:**
- Create: `src/main/java/com/ch6/cafe/global/config/QueryDslConfig.java`
- Create: `src/main/java/com/ch6/cafe/domain/ranking/repository/DailyMenuSalesQueryRepository.java`
- Create: `src/main/java/com/ch6/cafe/domain/ranking/repository/DailyMenuSalesQueryRepositoryImpl.java`
- Modify: `src/main/java/com/ch6/cafe/domain/ranking/repository/DailyMenuSalesRepository.java`
- Modify: `src/test/java/com/ch6/cafe/domain/ranking/repository/DailyMenuSalesRepositoryMySqlIntegrationTest.java`

**Interfaces:**
- `DailyMenuSalesQueryRepository.aggregateBetween(LocalDate from, LocalDate to)` returns `List<MenuSalesAggregate>`.
- `DailyMenuSalesQueryRepository.summarizeBetween(LocalDate from, LocalDate to)` returns `List<DailySalesMetadataProjection>`.
- `DailyMenuSalesRepository` extends the fragment and retains `increment`, CRUD, and derived queries.

- [ ] **Step 1: Write QueryDSL-specific failing integration assertions**

Extend the MySQL integration test to assert inclusive bounds, outside-range exclusion, grouped totals, metadata grouping, and deterministic projection values. Add a static assertion that production aggregate methods are no longer annotated with JPQL `@Query`.

- [ ] **Step 2: Run `verify.integration` through the official runner and verify RED**

Expected: FAIL because the custom QueryDSL fragment/configuration is absent or the static contract still detects JPQL.

- [ ] **Step 3: Implement the repository fragment**

Construct `JPAQueryFactory` from `EntityManager`. Use `QDailyMenuSale.dailyMenuSale`, `between(from, to)`, `groupBy(menuId)` for aggregation, and `groupBy(salesDate)` for metadata. Map tuples into immutable implementations of the existing projection interfaces without changing service callers. Remove JPQL aggregate methods from the Spring Data interface; retain the native UPSERT exactly.

- [ ] **Step 4: Run `verify.integration` and verify GREEN**

Use a fresh official run ID. Confirm the QueryDSL/MySQL test and all existing MySQL/Redis integration tests pass; record counts, failures, errors, skips, and artifact paths.

- [ ] **Step 5: Independent review and commit**

Review that production code genuinely executes QueryDSL, date bounds and numeric types are correct, and the native UPSERT remains unchanged. Fix/re-review, then commit.

### Task 3: Real Kafka Broker Producer/Consumer Integration

**Owning feature:** `specs/003-order-payment`

**Files:**
- Create: `src/test/java/com/ch6/cafe/domain/outbox/publisher/OrderPaidKafkaIntegrationTest.java`
- Modify: `src/main/java/com/ch6/cafe/domain/outbox/publisher/OutboxPublisher.java`
- Modify: `src/main/java/com/ch6/cafe/domain/outbox/publisher/OrderPaidConsumer.java`
- Modify: `src/main/java/com/ch6/cafe/domain/outbox/service/OrderPaidAnalyticsService.java`
- Modify: `src/test/resources/application-test.yml`

**Interfaces:**
- Publisher sends to `coffee.order.paid` with decimal order/aggregate ID as Kafka key.
- Listener consumes the envelope and commits marker/effect using configured consumer group.
- Existing service-level tests continue to cover independent groups and forced transactional rollback when those cases cannot safely be represented by one live listener group.

- [ ] **Step 1: Write the broker-backed failing test**

Start MySQL and Kafka containers, register dynamic datasource/bootstrap properties, seed an Outbox event, invoke the real publisher, and use a real Kafka consumer plus bounded DB polling to assert topic, key, envelope, listener receipt, processed marker, and analytics effect. Add duplicate delivery and publisher-failure/retry assertions.

- [ ] **Step 2: Run `verify.integration` through the official runner and verify RED**

Expected: FAIL on the first missing wiring/behavior revealed by the real broker. Preserve the exact failure in the work log.

- [ ] **Step 3: Implement only required production corrections**

Make the minimum changes needed for deterministic broker publication and listener processing. Do not bypass Kafka, call the consumer directly for the broker proof, or weaken transaction boundaries.

- [ ] **Step 4: Run `verify.integration` and verify GREEN**

Confirm real broker producer/topic/consumer/MySQL behavior, same-group idempotency, independent-group service behavior, rollback, and publisher retry state. Record container types and test counts.

- [ ] **Step 5: Independent review and commit**

Review bounded waits, isolation, key correctness, at-least-once semantics, and failure-state assertions. Fix/re-review, then commit.

### Task 4: Random-Port Real HTTP API Smoke

**Owning feature:** none (cross-feature API verification)

**Files:**
- Create: `src/test/java/com/ch6/cafe/api/CafeApiSmokeTest.java`
- Modify: `src/test/resources/application-test.yml`

**Interfaces:**
- Uses `@SpringBootTest(webEnvironment = RANDOM_PORT)` and `java.net.http.HttpClient`.
- Uses real MySQL and Redis Testcontainers.
- Disables Kafka listener and Outbox scheduler for this suite; Kafka behavior is Task 3.

- [ ] **Step 1: Write failing real HTTP smoke cases**

Seed a user/menu through JDBC, send actual HTTP requests for menu list, point charge, order payment, and popular menu, then assert response status/body and durable state. Add invalid request and insufficient-point or missing-menu error requests and assert no unexpected 500.

- [ ] **Step 2: Run `verify.api-smoke` through the official runner and verify RED**

Expected: FAIL if any real-server wiring, JSON contract, or error mapping is incorrect. MockMvc output is not evidence.

- [ ] **Step 3: Implement minimum corrections**

Change only defects exposed by real requests. Keep business rules in services and preserve public contracts.

- [ ] **Step 4: Run `verify.api-smoke` and verify GREEN**

Record the real port mode, HTTP scenarios, response statuses, test counts, failures/errors/skips, and server log review outcome.

- [ ] **Step 5: Independent review and commit**

Review that no MockMvc path is used, all requests are real HTTP, and error assertions reject unexpected 500s. Fix/re-review, then commit.

### Task 5: Docker Compose Black-Box E2E and Evidence Reconciliation

**Owning feature:** none (repo-wide Level 5 verification)

**Files:**
- Create: `Dockerfile`
- Modify: `docker-compose.yml`
- Create: `docker-compose.e2e.yml`
- Create: `scripts/e2e/verify-e2e.sh`
- Modify: `ai/command-registry.json`
- Modify: `ai/command-registry.md`
- Modify: `docs/09-quality-operations-and-rules.md`
- Modify: `specs/003-order-payment/tasks.md`
- Modify: `specs/004-popular-menu/tasks.md`
- Modify: applicable issue work logs and completion evidence files

**Interfaces:**
- `scripts/e2e/verify-e2e.sh` is a no-argument POSIX command invoked only as `verify.e2e`.
- Compose services are `app`, `mysql`, `redis`, and `kafka`; app uses service DNS names.
- The script uses a unique Compose project name and always removes containers, networks, and volumes.

- [ ] **Step 1: Write the failing E2E contract/script**

Create the script first with strict mode, cleanup trap, bounded readiness, HTTP helper, SQL/Redis assertions, and expected scenario checks. Run `verify.e2e` through the official runner and preserve the expected RED because app image/topology wiring is absent.

- [ ] **Step 2: Implement the application image and Compose topology**

Build the Boot jar in a multi-stage image or copy a reproducibly built jar. Configure health checks and internal addresses (`mysql`, `redis`, `kafka`). Use ephemeral E2E volumes and no fixed container names in the overlay so repeated runs do not collide.

- [ ] **Step 3: Complete the black-box scenario**

The script must verify, in order: service readiness/Flyway; fixture creation; HTTP charge; HTTP order; MySQL order/payment/history/daily-sales/Outbox; Outbox `PUBLISHED`; processed marker and analytics effect; Redis daily ranking; popular-menu HTTP response; duplicate event without duplicate same-group analytics; and cleanup. On failure, print concise app and dependency logs before cleanup.

- [ ] **Step 4: Run all five official commands with fresh run IDs**

Run, separately and only through `scripts/ai/command-runner.sh`:

```text
verify.build
verify.unit
verify.integration
verify.api-smoke
verify.e2e
```

Record run ID, attempt ID, exit code, test counts, failures, errors, skips, infrastructure used, and finalized artifact path for every command. Run `git diff --check` as an administrative check. Reconcile registry state only from actual finalized artifacts.

- [ ] **Step 5: Update owner docs and deferred scope**

Replace the now-resolved quality-document open questions with the exact command boundaries and Testcontainers/Compose decision. Mark only genuinely passed task items. Record load balancer/multi-instance deployment as follow-up and Redis Sentinel as a future option; do not claim either is implemented.

- [ ] **Step 6: Independent final review and completion gates**

Generate a whole-branch review package. A fresh reviewer checks production/document/registry/evidence consistency and reports Critical/Important/Minor findings. Send all final findings in one fix wave, rerun covering official commands, and re-review. Then load and execute the repository pre-QA, QA, done-claim, and closure gates without overstating status. Commit final changes but do not push or open a PR.
