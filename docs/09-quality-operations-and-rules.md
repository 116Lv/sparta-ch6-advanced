# 09. Quality, Operations, and Rules

## Testing Strategy

Testing rules are also governed by `ai/verification-levels.md` and `ai/qa-gate.md`.

The detailed business invariants are owned by [03. Domain Model](03-domain-model.md#consistency-invariants). Every concurrency, load, recovery, and failure test must check applicable invariants in addition to latency and error results.

### Unit Test

Write unit tests for:

- domain rules
- point balance validation
- order creation rules
- request validation helpers
- ranking policy

### Integration Test

Write integration tests for:

- repository behavior
- MySQL transaction behavior
- API controller behavior
- Outbox event persistence
- Redis ranking update

### Real API Verification

Any API behavior change requires real HTTP request verification against a running server unless blocked by missing project setup. If blocked, report `BLOCKED` with the reason.

### Concurrency Test

Write concurrency tests for:

- same user multiple orders
- same user charge and order at the same time
- lock timeout behavior

Required consistency assertions include no negative point balance, no lost point update, no duplicate payment for one order, and no missing Outbox event for a committed paid order.

## Performance and Load Test Plan

The scenarios and metrics below are fixed now. Numeric TPS and p95 targets are intentionally not fixed until a reproducible baseline run records the environment, dataset, instance counts, tool configuration, and bottleneck evidence. After that run, record the target values and regression tolerance in the verification evidence owner rather than silently inventing them in README.

### Workloads

| Scenario | Traffic shape | Purpose |
|---|---|---|
| Normal load | Menu reads, point charges, orders, and popular-menu reads with users distributed across keys | Establish baseline throughput, latency distribution, and resource use |
| Hot key | A high share of point mutations targets one user key | Measure serialization cost, timeout policy, fairness, and tail latency |
| Charge/order contention | Charges and orders run concurrently for the same users | Detect lost updates, negative balances, duplicate payment, and inconsistent histories |
| Outbox backlog | Build a READY backlog, then restore publisher/broker throughput while new orders continue | Measure claim fairness, recovery throughput, residence time, duplicates, and consumer lag |

Increase load in documented stages: warm-up, baseline steady state, expected peak, saturation, and recovery. Use the same dataset and traffic distribution when comparing alternatives.

### Redisson and DB pessimistic-lock comparison

Run the normal-load, hot-key, and charge/order-contention workloads twice with equivalent correctness rules:

1. Redisson admission control followed by the MySQL transaction.
2. MySQL pessimistic row locking without Redisson.

Compare throughput, p50/p95/p99 latency, error and timeout rates, lock wait, DB connection-pool active/waiting counts, and invariant violations. Redisson is justified only by evidence that DB-entry contention control or faster timeout behavior is valuable enough to offset Redis dependency, lease/watchdog risks, and the additional failure boundary.

### Metrics

Record at minimum:

- request throughput and successful business-operation throughput
- p50, p95, and p99 latency by endpoint and workload phase
- HTTP/operation error rate, lock timeout rate, and retry rate
- Redisson acquisition wait and hold time, or DB row-lock wait for the comparison path
- DB connection-pool active, idle, pending/waiting, timeout, and saturation signals
- Outbox backlog count and event residence time from `created_at` to `published_at`
- Outbox claim recovery count, publish retry count, and duplicate-delivery count
- Kafka producer error/retry rate and consumer lag by group and partition

Report correctness violations separately from transport or timeout errors. A higher TPS result is invalid if any mandatory invariant fails.

## Failure and Recovery Scenarios

| Failure | Injection and expected behavior | Recovery evidence |
|---|---|---|
| API instance failure | Stop one stateless API instance during traffic; the load balancer sends new requests to healthy instances | Error window, retry outcome, no in-memory ownership loss, invariants preserved |
| Outbox Publisher failure | Stop a worker after row claim and before publish or status update | Expired claim is reclaimed; no event omission; any duplicate is absorbed by consumer idempotency |
| Kafka consumer failure | Stop a consumer while partitions are active | Consumer-group rebalance dynamically assigns partitions; lag returns toward baseline; same-key order is preserved |
| Redis delay/unavailability | Delay or remove Redis during point mutation and ranking traffic | Point mutation fails with a controlled policy and never bypasses an unknown lock; ranking uses documented fallback/rebuild behavior |
| Lease/watchdog boundary | Pause or terminate a lock owner near the configured lease/watchdog boundary | No concurrent mutation breaks point/payment invariants; ownership checks prevent unsafe unlock |
| Kafka outage | Make the broker unavailable while orders continue | Committed orders retain retryable Outbox events; backlog and residence time grow observably, then drain after recovery |
| API overload | Drive traffic beyond saturation | Bounded timeouts and controlled errors occur; DB pool and lock waits expose the bottleneck; service recovers after load removal |

Redis Sentinel may be evaluated later for master failover, but it is not a current test-environment assumption and must not be counted as sharding or write-load distribution.

## Security Rules

- Do not log secrets, tokens, passwords, or sensitive personal data.
- Validate all user input on the server.
- Do not trust userId from request in real production auth contexts without principal verification.
- Do not expose stack traces in API responses.

## Logging Rules

- Log important business events with structured fields.
- Log order/payment failure reasons.
- Log Outbox publish failures and retry counts.
- Log unexpected exceptions.
- Do not log full sensitive payloads.

## Release Rules

The exact release workflow is not yet confirmed. Until a repository-owned workflow is accepted, apply these minimum rules:

- Do not merge without QA Gate evidence.
- PR description should include changed requirements and verification evidence.
- Breaking changes require documentation update.

## Migration Rules

- DB migration must be reviewed before deployment.
- Migration rollback or mitigation plan must be documented.
- API changes that depend on migration must state deployment order.

## Definition of Done

A feature is done only when:

1. Relevant spec acceptance criteria are satisfied.
2. Required verification level is met.
3. Tests were actually run or explicitly reported as not run.
4. API changes have real API verification evidence when applicable.
5. Unexpected 500 responses were checked.
6. Server logs were reviewed when real server verification was required.
7. Docs/specs/adr were updated if behavior changed.
8. Done claim follows `ai/done-claim-template.md`.

## Open Questions

- Open Question: What exact Gradle tasks should be used for integration and real API verification beyond `test`?
- Open Question: Will Testcontainers be required for MySQL, Redis, and Kafka integration tests?
