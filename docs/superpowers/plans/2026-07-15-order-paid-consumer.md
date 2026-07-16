# Durable Order-Paid Consumer Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the no-op Kafka consumer marker with a transactional, idempotent analytics effect and close the adjacent publisher-lease and permanent-failure recovery gaps.

**Architecture:** `OrderPaidConsumer` validates the Kafka envelope and delegates to a transactional service. That service inserts the existing per-group processed marker and one durable analytics row atomically. The publisher claims one row immediately before each send, while an audited recovery service owns `FAILED -> READY` transitions.

**Tech Stack:** Java 21, Spring Boot 4.1, Spring Data JPA, MySQL/Flyway, Kafka, Testcontainers, JUnit 5.

## Global Constraints

- Work only in `C:\Users\lbw01\GitHub\sparta-ch6-advanced`; do not create a worktree or repository copy.
- Preserve commit `0ee04b6`; all corrections are additional commits.
- Topic is exactly `coffee.order.paid`; producer key is decimal `aggregateId`.
- Delivery is at least once; no global ordering or exactly-once claim is allowed.
- Idempotency scope is exactly `(consumer_group, event_id)`.
- External data-platform HTTP integration remains out of scope.
- Do not add an unauthenticated recovery endpoint.
- Do not run Gradle, tests, Docker, server, HTTP, database, migration, seed, or infrastructure commands. Record them as `NOT RUN / BLOCKED` because no command is `VERIFIED`.
- Use tests-first file ordering, but do not claim RED/GREEN execution evidence.
- No placeholders, empty packages, direct Kafka publishing in the order transaction, requirement weakening, or test deletion.

---

### Task 1: Implement the complete Task 3 consistency correction

**Files:**

- Modify: `specs/003-order-payment/spec.md`
- Modify: `docs/03-domain-model.md`
- Modify: `docs/07-data-and-api-contracts.md`
- Modify: `docs/09-quality-operations-and-rules.md`
- Modify: `adr/ADR-002-transactional-outbox-kafka.md`
- Create: `src/main/resources/db/migration/V2__add_order_paid_analytics_and_outbox_recovery.sql`
- Create: `src/main/java/com/ch6/cafe/domain/outbox/entity/OrderPaidAnalyticsId.java`
- Create: `src/main/java/com/ch6/cafe/domain/outbox/entity/OrderPaidAnalytics.java`
- Create: `src/main/java/com/ch6/cafe/domain/outbox/entity/OutboxRecoveryAudit.java`
- Create: `src/main/java/com/ch6/cafe/domain/outbox/repository/OrderPaidAnalyticsRepository.java`
- Create: `src/main/java/com/ch6/cafe/domain/outbox/repository/OutboxRecoveryAuditRepository.java`
- Create: `src/main/java/com/ch6/cafe/domain/outbox/service/OrderPaidAnalyticsService.java`
- Create: `src/main/java/com/ch6/cafe/domain/outbox/service/OutboxRecoveryService.java`
- Modify: `src/main/java/com/ch6/cafe/domain/outbox/entity/OutboxEvent.java`
- Modify: `src/main/java/com/ch6/cafe/domain/outbox/publisher/OrderPaidConsumer.java`
- Modify: `src/main/java/com/ch6/cafe/domain/outbox/publisher/OutboxPublisher.java`
- Test: `src/test/java/com/ch6/cafe/domain/outbox/publisher/OrderPaidConsumerMySqlIntegrationTest.java`
- Test: `src/test/java/com/ch6/cafe/domain/outbox/publisher/OutboxPublisherMySqlIntegrationTest.java`
- Test: `src/test/java/com/ch6/cafe/domain/outbox/service/OutboxRecoveryServiceMySqlIntegrationTest.java`
- Test: `src/test/java/com/ch6/cafe/domain/outbox/entity/OutboxEventTest.java`

**Interfaces:**

- `OrderPaidAnalyticsService.apply(String consumerGroup, OrderPaidMessage message): boolean` returns `true` only for the first group/event delivery.
- `OrderPaidMessage(long eventId, String eventType, long aggregateId, long userId, long menuId, long paymentAmount)` is a validated immutable record nested in, or colocated with, the consumer.
- `OutboxRecoveryService.requeueFailed(long eventId, String operator, String reason): void` is the only application-owned permanent-failure recovery operation.
- `OutboxEvent.requeueFailed(LocalDateTime now): void` accepts only `FAILED`, resets retry count, clears claim metadata, and changes status to `READY`.
- `OutboxPublisher.claimNext(): Optional<ClaimedEvent>` claims at most one row in one short transaction.

- [ ] **Step 1: Update canonical contracts before behavior**

Record the approved local durable analytics effect in `specs/003-order-payment/spec.md`, while retaining the external platform API as out of scope. Define:

```text
first delivery in one consumer group
  = processed_events marker + order_paid_analytics row in one transaction
duplicate in the same group
  = neither a second marker nor a second analytics effect
analytics write failure
  = marker rollback and retryable Kafka delivery
```

Update the owner documents with the exact table contracts, `FAILED -> READY` audited recovery, and claim-one-before-publish protocol. Remove wording that describes `processed_events` as a sufficient effect by itself.

- [ ] **Step 2: Write schema and mapping tests first**

Add MySQL integration assertions that the following migration contract exists and is enforced:

```sql
CREATE TABLE order_paid_analytics (
    consumer_group VARCHAR(100) NOT NULL,
    event_id BIGINT NOT NULL,
    aggregate_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    menu_id BIGINT NOT NULL,
    payment_amount BIGINT NOT NULL,
    processed_at DATETIME NOT NULL,
    PRIMARY KEY (consumer_group, event_id),
    UNIQUE KEY uk_order_paid_analytics_group_aggregate (consumer_group, aggregate_id),
    INDEX idx_order_paid_analytics_group_processed (consumer_group, processed_at),
    CONSTRAINT chk_order_paid_analytics_event_positive CHECK (event_id > 0),
    CONSTRAINT chk_order_paid_analytics_aggregate_positive CHECK (aggregate_id > 0),
    CONSTRAINT chk_order_paid_analytics_user_positive CHECK (user_id > 0),
    CONSTRAINT chk_order_paid_analytics_menu_positive CHECK (menu_id > 0),
    CONSTRAINT chk_order_paid_analytics_payment_positive CHECK (payment_amount > 0)
);
```

Also create `outbox_recovery_audits` with an auto-increment ID, `event_id`, nonblank operator/reason columns, previous retry/error fields, and `recovered_at`; add an `(event_id, recovered_at)` index and FK to `outbox_events`.

Expected execution: `NOT RUN / BLOCKED` by command policy.

- [ ] **Step 3: Implement the transactional consumer effect**

Make the consumer validate the complete envelope before persistence:

```java
if (eventId <= 0 || aggregateId <= 0 || userId <= 0 || menuId <= 0
        || paymentAmount <= 0 || !"ORDER_PAID".equals(eventType)) {
    throw new IllegalArgumentException("ORDER_PAID event contract is invalid.");
}
analyticsService.apply(consumerGroup, message);
```

Implement one service transaction:

```java
@Transactional
public boolean apply(String consumerGroup, OrderPaidMessage message) {
    int inserted = processedEventRepository.markProcessed(message.eventId(), consumerGroup);
    if (inserted == 0) {
        return false;
    }
    analyticsRepository.save(OrderPaidAnalytics.from(consumerGroup, message));
    return true;
}
```

The analytics entity must persist every validated payload field and use `(consumer_group,event_id)` as its embedded ID. Do not catch persistence errors; rollback must include the marker.

- [ ] **Step 4: Add consumer idempotency and atomicity tests**

Using Testcontainers MySQL and real repositories/services, assert:

```text
same group + same event twice -> 1 marker, 1 analytics row
different groups + same event -> 2 markers, 2 analytics rows
forced analytics save failure -> 0 committed markers, 0 analytics rows
invalid payload -> 0 markers, 0 analytics rows
analytics row fields exactly equal aggregateId/userId/menuId/paymentAmount
```

Include a Kafka listener-level duplicate-delivery case using the existing Kafka test dependency where statically credible. Do not replace the effect service with a mock in the atomicity tests.

Expected execution: `NOT RUN / BLOCKED`.

- [ ] **Step 5: Change publisher claiming to claim immediately before send**

Replace whole-batch lease acquisition with:

```java
public void publishBatch() {
    for (int processed = 0; processed < batchSize; processed++) {
        Optional<ClaimedEvent> event = claimNext();
        if (event.isEmpty()) {
            return;
        }
        publish(event.get());
    }
}
```

`claimNext` must query with `PageRequest.of(0, 1)`, create a unique token, persist owner/start/deadline in a short transaction, and return after commit. Keep stale-token completion/failure filtering and expired-claim recovery.

- [ ] **Step 6: Add publisher concurrency and duplicate-boundary tests**

With real MySQL repository locking and controlled Kafka send futures, assert:

```text
two workers claim different READY rows
one slow send does not pre-lease an unstarted later row
expired PROCESSING row receives a new token
old token cannot mark PUBLISHED or FAILED
acknowledged Kafka send + completion DB failure leaves an at-least-once reclaim path
retry 1..4 returns READY; retry 5 becomes FAILED
producer topic == coffee.order.paid
producer key == decimal aggregateId
```

Inspect generated SQL only through an authorized future runtime; statically preserve the `jakarta.persistence.lock.timeout=-2` skip-locked hint and report SQL effectiveness as `NOT RUN`.

- [ ] **Step 7: Implement audited FAILED recovery**

Add the entity transition:

```java
public void requeueFailed(LocalDateTime now) {
    if (status != OutboxStatus.FAILED) {
        throw new IllegalStateException("Only FAILED events can be requeued.");
    }
    status = OutboxStatus.READY;
    retryCount = 0;
    lastError = null;
    clearClaim(now);
}
```

The service must validate `eventId > 0` and nonblank operator/reason, lock the event, snapshot retry/error into an immutable audit row, then requeue. A missing or non-FAILED event must fail without an audit row or transition. Do not expose this service through an unauthenticated controller.

- [ ] **Step 8: Add recovery tests**

Assert with MySQL:

```text
FAILED event -> one audit + READY + retry 0 + cleared claim/error
READY/PROCESSING/PUBLISHED event -> rejected, no audit
blank operator/reason -> rejected, no audit
recovery transaction failure -> neither audit nor state transition commits
requeued event is claimable by the normal publisher path
```

Expected execution: `NOT RUN / BLOCKED`.

- [ ] **Step 9: Perform static verification and self-review**

Run only allowed administrative/static checks:

```text
git diff --check
git status --short --branch
rg for direct KafkaTemplate use in order service
rg for topic, producer key, statuses, claim fields, composite IDs, and recovery transitions
compare entity/table columns against docs/07-data-and-api-contracts.md
inspect every new test for non-vacuous business assertions
```

Record compilation, Gradle tests, MySQL, Kafka, Docker, migration, and generated-SQL verification as `NOT RUN / BLOCKED`.

- [ ] **Step 10: Commit the cohesive correction**

After root review stages only intended canonical docs, production code, migration, and tests:

```bash
git commit -m "fix: implement durable order event consumption"
```

Do not push or create a PR.
