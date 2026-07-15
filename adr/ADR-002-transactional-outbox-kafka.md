# ADR-002: Use Transactional Outbox and Kafka for Order Events

## Status

Accepted

## Context

The assignment requires order history to be sent to a data collection platform in real time.

Publishing directly to Kafka inside the order API flow creates consistency risks:

- DB commit may succeed but Kafka publish may fail.
- Kafka publish may succeed but DB transaction may roll back.
- Network latency can make the order API unstable.
- Failed publish attempts need retry and observability.

## Decision 1: Transactional Outbox

Use the Transactional Outbox pattern.

During the order/payment transaction, save:

- order
- payment
- point history
- daily menu aggregate
- outbox event

Then stateless Outbox Publisher workers claim and publish events independently from the order API.

Claim protocol:

1. In a short MySQL transaction, select at most one claimable row with row locking and skip rows already claimed by another worker.
2. Change that row to `PROCESSING`, record a unique claim token, claim owner, `claimed_at`, and `claim_until`, and commit the claim transaction.
3. Publish outside the claim transaction so a broker delay does not hold DB row locks or pre-lease later unstarted rows.
4. After Kafka acknowledges the record, mark it `PUBLISHED` only if the current claim token still matches. On a publish failure, use the same token check, increment retry metadata, and return the row to a retryable state according to the retry policy.
5. Repeat claim and publish up to the configured cycle size. An expired `PROCESSING` row is claimable with a new token after an instance failure.

Row claiming prevents two healthy workers from intentionally publishing the same row at the same time. It does not provide exactly-once delivery: a worker can publish successfully and fail before recording `PUBLISHED`. Consumers must use the immutable Outbox event ID as an idempotency key.

## Decision 2: Kafka

Use Kafka as the event transport after an Outbox row is claimed.

Kafka is selected independently from the Outbox reliability pattern because the expected integration benefits from:

- retained events that can be replayed after consumer repair or new consumer onboarding
- multiple consumer groups reading the same order-event stream independently
- partition-based parallel processing
- ordering within a partition for records that use the same partition key

The topic is partitioned and consumers run in consumer groups. Kafka assigns each partition to at most one consumer in a group at a time. When a consumer instance stops or joins, group rebalancing dynamically reassigns partitions to active instances. Different consumer groups receive their own logical copy of the stream.

Use a stable business key as the partition key wherever per-key ordering is required. Kafka does not guarantee global ordering across partitions.

Kafka topic:

```txt
coffee.order.paid
```

## Transactional Outbox Alternatives

- Direct Kafka publish in the order service: simple, but DB/Kafka consistency is weak.
- Direct Mock HTTP API call in the order transaction: simple for assignment demos, but couples external latency and failure to order success.
- Polling the orders table directly: avoids outbox table, but makes event status, retry, and deduplication less explicit.

## Messaging Alternatives

- RabbitMQ or another work queue is preferable when the primary need is low-latency task dispatch, per-message routing, acknowledgements, priorities, or short-lived messages that are removed after consumption, and replay or multiple independent consumer groups are not requirements.
- A synchronous HTTP integration is preferable when the caller needs an immediate response from one downstream service and can deliberately couple its availability and latency to the request.
- Database-only polling can be sufficient for a small single-consumer integration when introducing and operating a broker is not justified.

Kafka adds broker and partition operations, consumer-lag monitoring, and replay/idempotency responsibilities. It is not selected merely because the Outbox pattern is used.

## Consequences

### Positive

- Order success and event-to-publish persistence are committed together.
- Kafka failure does not force order API failure after DB commit.
- Retry is possible using Outbox event state.
- Event publishing becomes observable.
- Multiple publisher instances can share work through row claims.
- Kafka retains events for replay and supports independent consumer groups.

### Negative

- Requires an additional table and publisher process.
- Duplicate publish can occur if publisher fails after Kafka publish but before status update.
- Consumers should treat event ID as idempotency key.
- Stale claims require a deadline and recovery process.
- Kafka partition count bounds in-group parallelism and must be planned with the ordering key.

### Neutral / Trade-offs

- This pattern provides practical reliability, not a global distributed transaction.
- Real-time means near-real-time asynchronous delivery, not synchronous external delivery inside the user request.
- Delivery is at least once across the DB-to-Kafka boundary; consumer idempotency is mandatory.

## Follow-up

- The implementation polls every 1 second, claims at most 50 rows with a 30-second deadline,
  waits up to 5 seconds for the Kafka acknowledgement, and moves an event to `FAILED` after
  5 failed publication attempts.
- Claim selection uses a MySQL pessimistic row lock in a short transaction. A new UUID token is
  assigned to each row, and completion/retry takes the row lock again and verifies that token.
- `FAILED` is the audited-recovery boundary; automatic publication does not claim it. The application-owned recovery service records operator, reason, previous retry/error, and recovery time before atomically requeueing to `READY`. Direct unaudited SQL requeue is prohibited.
- Consumer idempotency is persisted by the composite key `(consumer_group, event_id)`, and the marker plus local `order_paid_analytics` effect commit atomically. An effect failure rolls back the marker.
- Add tests for Outbox saved on order success and not saved on order failure.
- Add tests for publisher success/failure state transitions.
- Add tests for competing publisher workers, process failure after claim, stale-claim recovery, and publish-acknowledged/status-update-failed duplicate delivery.
- Verify consumer idempotency, consumer-group rebalance after instance failure, partition parallelism, and same-key ordering.
- Measure Outbox residence time, backlog size, publish error rate, retry count, and Kafka consumer lag under normal load and an accumulated backlog.
