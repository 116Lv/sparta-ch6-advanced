# ADR-002: Use Transactional Outbox for Kafka Order Events

## Status

Accepted

## Context

The assignment requires order history to be sent to a data collection platform in real time.

Publishing directly to Kafka inside the order API flow creates consistency risks:

- DB commit may succeed but Kafka publish may fail.
- Kafka publish may succeed but DB transaction may roll back.
- Network latency can make the order API unstable.
- Failed publish attempts need retry and observability.

## Decision

Use the Transactional Outbox pattern.

During the order/payment transaction, save:

- order
- payment
- point history
- daily menu aggregate
- outbox event

Then a separate Outbox Publisher reads `READY` events and publishes them to Kafka. On success, it marks the event as `PUBLISHED`. On failure, it increments retry metadata and leaves the event retryable.

Kafka topic:

```txt
coffee.order.paid
```

## Alternatives Considered

- Direct Kafka publish in the order service: simple, but DB/Kafka consistency is weak.
- Direct Mock HTTP API call in the order transaction: simple for assignment demos, but couples external latency and failure to order success.
- Polling the orders table directly: avoids outbox table, but makes event status, retry, and deduplication less explicit.

## Consequences

### Positive

- Order success and event-to-publish persistence are committed together.
- Kafka failure does not force order API failure after DB commit.
- Retry is possible using Outbox event state.
- Event publishing becomes observable.

### Negative

- Requires an additional table and publisher process.
- Duplicate publish can occur if publisher fails after Kafka publish but before status update.
- Consumers should treat event ID as idempotency key.

### Neutral / Trade-offs

- This pattern provides practical reliability, not a global distributed transaction.
- Real-time means near-real-time asynchronous delivery, not synchronous external delivery inside the user request.

## Follow-up

- Define retry interval and max retry count.
- Define dead-letter or manual recovery policy for permanently failing events.
- Add tests for Outbox saved on order success and not saved on order failure.
- Add tests for publisher success/failure state transitions.
- For assignment verification, decide whether Kafka Producer mock tests are enough or a separate Mock HTTP data collection API should be added.
