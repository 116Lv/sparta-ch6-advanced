# ADR-003: Use Redis Sorted Set with MySQL Daily Menu Aggregation

## Status

Accepted

## Context

The popular menu API must return the top 3 menus for the last 7 days, and menu order counts must be accurate.

Querying the full orders table with `GROUP BY` on every request is simple but can become expensive as order volume grows. Using only Redis Sorted Set gives fast ranking reads but makes recovery and correctness harder to explain if Redis data is lost.

## Decision

Use both:

- Redis Sorted Set for fast popular menu reads
- MySQL `daily_menu_sales` table as the durable aggregation and recovery source

Daily Redis key format:

```txt
popular-menu:{yyyy-MM-dd}
```

On successful order:

1. Increment MySQL `daily_menu_sales`.
2. After commit, take the date-scoped ranking lock, read the durable count, and assign that
   absolute value to the Redis member. This update does not create a completeness marker.

For the recent 7-day query:

1. Require a `popular-menu:complete:{yyyy-MM-dd}` marker for every requested date.
2. Union the last 7 daily Sorted Sets only when the range is complete.
3. Read top 3 by score and fetch menu details from MySQL.
4. If a marker or menu is missing, return the MySQL aggregate and rebuild all seven dates.

If Redis data is unavailable or lost, rebuild ranking from MySQL `daily_menu_sales`.

Redis Sentinel is not part of the confirmed implementation. It is a future availability option if automatic promotion of a replica is required after Redis master failure. Sentinel monitors and coordinates failover; it does not shard data, distribute write load across masters, or increase write throughput. Sharding or write distribution would require a separate Redis Cluster or application-level partitioning decision.

## Alternatives Considered

- Orders table direct aggregation: strongest simplicity, but potentially expensive at read time.
- Redis Sorted Set only: fast reads, but weak recovery story.
- MySQL daily aggregate only: durable and accurate, but less suitable for frequent ranking reads.
- Redis Sentinel: can automate master failover when replicas exist, but adds operational complexity and does not solve sharding or write-load distribution. Deferred until availability requirements and failure tests justify it.

## Consequences

### Positive

- Popular menu read path is fast.
- MySQL remains the durable source for counts.
- Redis recovery is possible.
- The design clearly separates performance storage from source-of-truth storage.

### Negative

- Write path updates both MySQL and Redis.
- Redis update failure needs reconciliation.
- Daily key TTL and rebuild policy must be defined.

### Neutral / Trade-offs

- If MySQL update succeeds and Redis update fails, the system remains recoverable.
- The API may need fallback behavior if Redis is down.
- Sentinel must not be described as a current dependency or as a scaling mechanism unless a later ADR accepts and verifies it.

## Follow-up

- Daily ranking keys use a 14-day TTL; temporary union keys use a 1-minute TTL and are deleted
  after the query.
- Daily completeness markers use the same 14-day TTL. A complete empty date has a marker and no
  live ZSET.
- `RankingRebuildService` reconstructs every date under the same date-scoped lock used by
  post-commit updates. It atomically replaces or deletes the live generation before publishing
  the marker.
- A missing marker, Redis failure, or unresolved cached menu serves the MySQL aggregate and
  attempts reconstruction without changing the committed order result.
- Add tests for last-7-days calculation.
- Add tests for Redis rebuild from `daily_menu_sales`.
- Test Redis unavailability and recovery first; use the evidence to decide whether a later Sentinel ADR is warranted.

