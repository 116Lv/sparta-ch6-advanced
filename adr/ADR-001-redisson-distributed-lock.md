# ADR-001: Use Redisson Distributed Lock for User Point Mutations

## Status

Accepted

## Context

The coffee order system must work correctly when multiple application server instances are running.

Point charge and point payment both mutate the same user point balance. If the same user sends concurrent charge/order requests, the system must not produce a negative balance, lost update, or duplicated deduction.

JVM-local locking such as `synchronized` cannot protect shared state across multiple server instances.

## Decision

Use Redisson distributed lock for user-level point mutation flows.

Lock key format:

```txt
point:user:{userId}
```

The lock protects:

- point charge
- point deduction during order/payment
- charge and order running concurrently for the same user

The lock does not replace the MySQL transaction. Redisson controls entry to the user-level critical section, while MySQL transaction controls atomic persistence.

## Alternatives Considered

- JVM local lock: simple but only works within a single process.
- MySQL pessimistic lock only: strong DB-level consistency, but all contention reaches the database first.
- MySQL optimistic lock only: useful under low contention, but requires retry policy and can make user-facing payment flows noisy.
- Redis command-only balance update: fast, but makes Redis the source of truth, which is not desired.

## Consequences

### Positive

- Works across multiple application instances.
- Makes user-level critical section explicit.
- Keeps point consistency policy consistent between charge and payment.
- Reduces avoidable DB race contention for the same user.

### Negative

- Redis availability affects point mutation APIs.
- Lock wait time and lease time must be configured carefully.
- Incorrect lock release handling can cause stuck or unsafe behavior.

### Neutral / Trade-offs

- MySQL constraints and transactions are still required.
- Lock timeout should return a controlled `LOCK_TIMEOUT` response rather than an unexpected 500.

## Follow-up

- Define concrete wait time and lease time after implementation performance is known.
- Add concurrency tests for same-user multiple orders.
- Add concurrency tests for charge and order running at the same time.

