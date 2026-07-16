# Order-Paid Consumer and Outbox Recovery Design

## Status

Approved direction: implement a real local durable consumer effect while keeping an external data-platform API out of scope.

## Context

The current `OrderPaidConsumer` inserts `(consumer_group, event_id)` into `processed_events` and then returns. That is an idempotency marker without a business effect: the first delivery is acknowledged as processed even though no analytics data is stored, and later deliveries are discarded.

The same review found two adjacent Outbox gaps:

- a batch of claims receives one common lease before sequential Kafka sends, so later rows can expire before their send begins;
- `FAILED` is described as manually recoverable, but no audited recovery operation exists.

## Considered Approaches

### 1. Local durable analytics intake — selected

Persist a concrete analytics record in MySQL. The idempotency marker and analytics effect commit in one transaction. This is deterministic, testable, and does not introduce an unspecified external API.

### 2. Synchronous external analytics API

Call an external platform from the Kafka listener. This would require an API contract, authentication, timeout/retry policy, and an external idempotency contract that the assignment does not define. It remains out of scope.

### 3. Remove the Consumer

Keep Kafka consumption out of scope and delete the no-op consumer. This would be internally consistent, but the user selected an actual consumer implementation.

## Consumer Architecture

### Message contract

The listener accepts the existing envelope:

```json
{
  "eventId": 1,
  "eventType": "ORDER_PAID",
  "aggregateId": 100,
  "payload": {
    "userId": 1,
    "menuId": 10,
    "paymentAmount": 4500
  }
}
```

Every numeric identifier and `paymentAmount` must be positive. `eventType` must be exactly `ORDER_PAID`. Missing, null, non-numeric, or invalid values reject the delivery and create neither marker nor analytics record.

### Transaction boundary

`OrderPaidConsumer` owns Kafka deserialization and validation, then calls `OrderPaidAnalyticsService.apply(message)`.

`OrderPaidAnalyticsService.apply` is one MySQL transaction:

1. Insert `(consumer_group, event_id)` into `processed_events` with `INSERT IGNORE`.
2. If the insert returns `0`, return without applying an effect.
3. If the insert returns `1`, insert one `order_paid_analytics` record containing the consumer group, event ID, aggregate/order ID, user ID, menu ID, payment amount, and processed time.
4. Commit both writes together.

If analytics persistence fails, the transaction rolls back the marker. Kafka redelivery can therefore retry the complete effect. The marker is never committed before an absent effect.

### Analytics schema

`order_paid_analytics` uses `(consumer_group, event_id)` as its primary key and has a unique `(consumer_group, aggregate_id)` constraint. Required positive-value checks apply to event, aggregate, user, menu, and payment values. An index on `(consumer_group, processed_at)` supports group-owned analytics scans.

Different consumer groups may each apply their own logical copy of an event. The same group cannot apply the same event twice.

## Publisher Claim Safety

Keep the configured bounded cycle size, but claim only one row immediately before its publish attempt:

1. Start a short transaction.
2. select one claimable row with pessimistic locking and skip-locked semantics;
3. set a new token, owner, and deadline, then commit;
4. publish that row;
5. complete or fail it using the current token;
6. repeat until the cycle limit is reached or no row is claimable.

No later row holds a lease while earlier rows wait for Kafka acknowledgement. Multiple publisher instances still compete through row locks, and expired `PROCESSING` rows remain reclaimable.

## FAILED Recovery

Add an internal `OutboxRecoveryService.requeueFailed(eventId, operator, reason)` operation. It runs in one MySQL transaction:

1. lock the event by ID;
2. require `FAILED` state and nonblank operator/reason;
3. append an immutable `outbox_recovery_audits` row containing event ID, operator, reason, previous retry count/error, and recovery time;
4. transition the event to `READY`, reset retry count, clear claim metadata, and retain recovery provenance in the audit row.

No unauthenticated HTTP endpoint is added. The service is the repository-owned operation boundary for authorized maintenance tooling. The operational runbook must state that direct un-audited SQL requeue is prohibited.

## Failure Handling

- Kafka acknowledgement followed by DB completion failure remains an at-least-once duplicate boundary; the event is reclaimed later and consumer idempotency absorbs the duplicate.
- A stale publisher token cannot complete, fail, or requeue a reassigned `PROCESSING` claim.
- Exhausted automatic retries remain `FAILED` until the audited recovery service is invoked.
- Analytics-effect failure rolls back the processed marker and is retried through Kafka delivery semantics.
- Consumer validation failure creates no durable state and remains visible as listener failure.

## Verification Design

Static/unit coverage:

- claim/retry/publish/requeue entity transitions and stale-token rejection;
- consumer envelope validation;
- recovery audit field preservation.

MySQL integration coverage:

- two publisher workers claim different rows under `SKIP LOCKED`;
- expired claim recovery and stale-token completion rejection;
- acknowledged-publish/status-update failure leaves a reclaimable duplicate boundary;
- same group/event delivered twice produces one marker and one analytics record;
- different groups each produce one record;
- forced analytics persistence failure rolls back the marker;
- audited `FAILED -> READY` recovery and invalid recovery rejection.

Kafka integration coverage:

- duplicate delivery does not duplicate the analytics effect;
- topic is `coffee.order.paid` and producer key is aggregate ID;
- no global ordering assertion is made.

All runtime commands remain `NOT RUN` until the repository provides a `VERIFIED` command path.

## Documentation Updates

Update the canonical owners together with implementation:

- `specs/003-order-payment/spec.md`: include the local durable analytics consumer effect while retaining external API integration as out of scope;
- `docs/03-domain-model.md`: define the analytics effect and same-transaction idempotency invariant;
- `docs/07-data-and-api-contracts.md`: define `order_paid_analytics`, recovery audit schema, and transition contracts;
- `adr/ADR-002-transactional-outbox-kafka.md`: record claim-one-before-publish and audited FAILED recovery;
- `docs/09-quality-operations-and-rules.md`: add duplicate-effect and recovery verification requirements.

## Non-Goals

- external data-platform HTTP integration;
- exactly-once Kafka delivery;
- global Kafka ordering;
- unauthenticated recovery API;
- automatic replay of permanently failed events without an audit record.
