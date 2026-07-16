# ADR-001: Use Redisson Distributed Lock for User Point Mutations

## Status

Accepted

## Context

The coffee order system must work correctly when multiple application server instances are running.

Point charge and point payment both mutate the same user point balance. If the same user sends concurrent charge/order requests, the system must not produce a negative balance, lost update, or duplicated deduction.

JVM-local locking such as `synchronized` cannot protect shared state across multiple server instances.

MySQL pessimistic row locking is also valid in a multi-instance deployment because every API instance coordinates through the same database. The decision is therefore not based on a claim that database locking only works on one instance. The comparison is where contention is admitted and how quickly excess contention is rejected.

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

The lock does not replace the MySQL transaction, database constraints, or row-level consistency checks. Redisson controls contention before requests enter MySQL and applies a short, explicit acquisition timeout. MySQL still controls atomic persistence and is the final consistency boundary.

The intended sequence is:

1. Acquire `point:user:{userId}` with a bounded wait time.
2. Start the MySQL transaction only after lock acquisition.
3. Read and mutate the point row, save history and order/payment data, and commit.
4. Release only a lock owned by the current execution in a `finally` block.

This choice is conditional on comparative verification. The same contention scenarios must be measured with Redisson and with MySQL pessimistic locking before concluding that the extra Redis dependency is justified.

## Alternatives Considered

- JVM local lock: simple but only works within a single process.
- MySQL pessimistic lock only: valid across all application instances and provides strong DB-level consistency with fewer infrastructure dependencies, but all contenders occupy the database path and timeout behavior is coupled to database lock settings.
- MySQL optimistic lock only: useful under low contention, but requires retry policy and can make user-facing payment flows noisy.
- Redis command-only balance update: fast, but makes Redis the source of truth, which is not desired.

## Consequences

### Positive

- Works across multiple application instances.
- Makes user-level critical section explicit.
- Keeps point consistency policy consistent between charge and payment.
- Rejects excess same-user contention before it consumes a DB connection or waits on a DB row lock.
- Allows a short application-level lock acquisition timeout independently of the database lock timeout.

### Negative

- Redis availability affects point mutation APIs.
- Lock wait time and lease time must be configured carefully.
- Incorrect lock release handling can cause stuck or unsafe behavior.
- The service now crosses two failure boundaries, Redis for admission control and MySQL for persistence.
- A fixed lease can expire while the transaction is still running, allowing another owner to enter the critical section.

### Neutral / Trade-offs

- MySQL constraints and transactions are still required.
- Lock timeout should return a controlled `LOCK_TIMEOUT` response rather than an unexpected 500.
- Redisson's watchdog can extend a lock acquired without a fixed lease while the owner is healthy, but it is not a fencing mechanism. Client pauses, lost connectivity, owner failure, or watchdog interruption can still create an expiry boundary.
- The application must never bypass the lock when Redis is unavailable. It must fail in a controlled way unless a separately designed and verified DB-lock fallback is introduced.
- Database locking remains the simpler baseline and may be preferable if Redisson does not reduce DB pool pressure or tail latency under measured contention.

## Follow-up

- The implementation uses a 200 ms acquisition wait and Redisson watchdog renewal with a
  30-second watchdog timeout. It does not pass a fixed lease to `tryLock`, so fixed-lease and
  watchdog assumptions are not mixed.
- Unlock first checks `isHeldByCurrentThread()`. Redis acquisition failure never falls through
  to an unlocked point mutation.
- Add concurrency tests for same-user multiple orders.
- Add concurrency tests for charge and order running at the same time.
- Compare Redisson and MySQL pessimistic locking with identical normal-load and hot-user workloads. Measure throughput, p50/p95/p99 latency, error and timeout rate, lock wait time, and DB connection-pool usage.
- Inject Redis delay/unavailability and a transaction that approaches or exceeds the lease boundary. Verify that balances never become negative, updates are not lost, and duplicate payment is not created.

