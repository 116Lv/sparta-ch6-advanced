# Task 3 Report: Real Kafka Broker Producer/Consumer Integration

## Status

- Implementation: authored and statically inspected; compilation and runtime behavior remain unverified.
- Runtime verification: `NOT RUN` because both official attempts stopped at `PRE_COMMAND` with `POSIX_EXECUTION_NOT_CONFIGURED`.
- Owning feature: `specs/003-order-payment`.

## Commands and evidence

All product-command attempts used the repository-owned runner. Gradle was never invoked directly.

1. RED
   - Command: `scripts/ai/command-runner.sh start --run-id verify-20260716-level5-task3-red-01 --task-key level-5-runtime-verification`
   - Result: `RUN_START PASS`.
   - Command: `scripts/ai/command-runner.sh run verify.integration --run-id verify-20260716-level5-task3-red-01`
   - Result: `PRE_COMMAND NOT_CONFIGURED`, reason `POSIX_EXECUTION_NOT_CONFIGURED`.
   - No attempt ID was reserved; no Gradle process, containers, artifact, or test count exists.
2. GREEN
   - Command: `scripts/ai/command-runner.sh start --run-id verify-20260716-level5-task3-green-01 --task-key level-5-runtime-verification`
   - Result: `RUN_START PASS`.
   - Command: `scripts/ai/command-runner.sh run verify.integration --run-id verify-20260716-level5-task3-green-01`
   - Result: `PRE_COMMAND NOT_CONFIGURED`, reason `POSIX_EXECUTION_NOT_CONFIGURED`.
   - No attempt ID was reserved; no Gradle process, containers, artifact, or test count exists.
3. Static administration
   - `git diff --check`: exit 0; only the existing Git CRLF normalization warning for `application-test.yml` was emitted.
   - Inspected the cached Spring Kafka 4.1 `KafkaTemplate` API and Testcontainers 1.20.4 `KafkaContainer` constructor/API signatures. This is static compatibility evidence, not compilation or a test pass.

## Files

- Created `src/test/java/com/ch6/cafe/domain/outbox/publisher/OrderPaidKafkaIntegrationTest.java`.
- Modified `src/test/resources/application-test.yml`.
- Updated `ai/work-logs/no-issue/level-5-runtime-verification/implementation-agent.md`.
- Created this report.
- No production source changed: static inspection showed the existing publisher, listener, and analytics service already implement the approved key, envelope, group, and transaction boundaries.

## Coverage design

- MySQL 8.4 and Apache Kafka 3.8 Testcontainers are registered through dynamic datasource and bootstrap-server properties.
- The real `OutboxPublisher` claims a seeded row and sends to `coffee.order.paid`.
- An independent real Kafka consumer observes the produced record and asserts the decimal aggregate/order ID key plus the canonical envelope.
- The real `@KafkaListener` is evidenced through bounded MySQL polling for the configured-group processed marker and exact analytics effect; the consumer method is never called directly.
- A broker duplicate is followed by a sentinel on the same observed partition. Observing the sentinel marker/effect proves the listener crossed the earlier duplicate, after which the original marker/effect remains exactly one.
- A real Kafka producer configured against a closed endpoint exercises publish failure without mocked send behavior and asserts `READY`, retry count 1, nonblank error, and cleared claim ownership.
- Existing `OrderPaidConsumerMySqlIntegrationTest` remains the focused MySQL boundary for different-group independence and rollback of marker plus analytics effect when the analytics constraint fails.
- Existing publisher MySQL tests remain responsible for retries 1-5, competing claims, expiry, stale tokens, and acknowledgement/status-update duplicate boundaries.

## Self-review

- All Kafka and DB waits have a 15-second deadline; Kafka polling uses 250 ms bounds and DB polling sleeps only while the bounded condition remains unmet.
- Duplicate and sentinel records are explicitly sent to the observed partition, so sentinel completion orders after duplicate handling.
- The observer uses an independent random group and cannot satisfy the application listener's durable DB assertions.
- The broker-failure producer has bounded metadata/request/delivery configuration and is always destroyed.
- Test cleanup respects foreign-key order and the Kafka container is isolated to the class.
- No direct Gradle, consumer-direct-call broker proof, unbounded sleep, weakened transaction, or mocked Kafka send was introduced.

## Concerns

- Compilation, Testcontainers startup, Kafka listener assignment, MySQL migration compatibility, and runtime assertions are unverified on this Windows host. Do not infer PASS from static review.
- The official integration command must be rerun on a configured POSIX execution path. Any compile or runtime failure must be handled with a new RED/GREEN cycle and fresh run IDs.
- The shared integration suite may be container-heavy; actual timing and flake behavior remain unknown until supported execution produces evidence.

## Review-fix evidence

- Review scope: assert the complete canonical payload and exact durable analytics values in the live broker path; replace the assumed-closed fixed port with a test-controlled non-Kafka endpoint.
- Source RED command inspected `OrderPaidKafkaIntegrationTest.java` for the required contracts and exited 1 with four expected violations:
  - `missing payload userId assertion`
  - `missing payload menuId assertion`
  - `missing exact persisted analytics field assertions`
  - `hard-coded assumed-closed broker endpoint`
- Source GREEN command exited 0 and confirmed assertions for payload `userId`, payload `menuId`, persisted `aggregateId`, `userId`, `menuId`, and `paymentAmount`, plus an ephemeral bound `ServerSocket`, selected local port, producer-factory cleanup, and absence of `127.0.0.1:1`.
- The failure-path test now owns a loopback `ServerSocket` on an OS-selected port. The socket deliberately does not speak Kafka, remains bound for the publish attempt, and closes through try-with-resources. Kafka metadata/request/delivery timeouts remain bounded and the producer factory closes in `finally`.
- Official command: `scripts/ai/command-runner.sh start --run-id verify-20260716-level5-task3-review-green-01 --task-key level-5-runtime-verification`; result `RUN_START PASS`.
- Official command: `scripts/ai/command-runner.sh run verify.integration --run-id verify-20260716-level5-task3-review-green-01`; result `PRE_COMMAND NOT_CONFIGURED`, reason `POSIX_EXECUTION_NOT_CONFIGURED`.
- No attempt ID, Gradle process, container execution, artifact, or test count was produced. The review fix remains runtime-unverified.
