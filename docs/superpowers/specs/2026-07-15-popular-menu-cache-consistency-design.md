# Popular Menu Cache Consistency Design

## Context

MySQL `daily_menu_sales` is the durable source and Redis daily sorted sets are the fast read model. A non-empty Redis union is not proof that every requested day is complete, and snapshot rebuilds can conflict with post-commit increments.

## Decision

Keep the Redis-first design and add an explicit completeness protocol.

- Each daily ZSET `popular-menu:{yyyy-MM-dd}` has a completeness marker `popular-menu:complete:{yyyy-MM-dd}` with the same 14-day TTL.
- A range is cache-readable only when all requested daily markers exist. Missing any marker causes a MySQL response and a rebuild of every date in the range, including dates with no rows.
- Rebuild creates a temporary daily ZSET, then atomically replaces or deletes the live key and writes the completeness marker.
- Cache updates and rebuilds use the same date-scoped lock. Post-commit updates read the durable MySQL count and set the Redis member to that absolute value; they do not blindly increment a possibly rebuilt snapshot.
- When a date is not complete, a post-commit update may write the known member value but must not create the completeness marker. The next query falls back and rebuilds the full date.
- Query and order date calculations use the same injected `Clock`.
- The public contract remains recent seven days and top three: only `days=7` and `limit=3` are accepted.
- A cached member whose menu cannot be resolved is treated as cache corruption. The request uses the durable result and initiates rebuild instead of returning a shortened list.

## Failure and concurrency behavior

Redis read, write, lock, or rebuild failure never changes the committed order. A request with incomplete or unusable cache state returns the MySQL aggregate. Date-scoped locking plus absolute score assignment makes rebuild and post-commit cache updates convergent and prevents duplicate increments from snapshot overlap.

The DB commit and cache update are not a distributed transaction. The documented consistency boundary remains post-commit recoverability: Redis is trusted only after the completeness protocol succeeds, while MySQL remains authoritative whenever completeness is uncertain.

## Verification

Author tests for the exact inclusive seven-day range, outside-range exclusion, top-three/tie order, fixed-clock date alignment, malformed and noncanonical parameters, all-marker cache hits, partial marker loss, empty-date stale-key removal, temporary-key cleanup and TTL, missing-menu fallback, Redis failure fallback, and deterministic rebuild/update interleavings. Runtime execution remains `NOT RUN` when repository command policy provides no VERIFIED product command.
