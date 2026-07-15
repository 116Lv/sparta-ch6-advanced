# Popular Menu Cache Consistency Design

## Context

MySQL `daily_menu_sales` is the durable source and Redis daily sorted sets are the fast read model. A non-empty Redis union is not proof that every requested day is complete, and snapshot rebuilds can conflict with post-commit increments.

## Decision

Keep the Redis-first design and add an explicit completeness protocol.

- Each daily ZSET `popular-menu:{yyyy-MM-dd}` has a completeness marker
  `popular-menu:complete:{yyyy-MM-dd}` containing a unique generation, durable total count, and
  durable member count, with the same 14-day TTL.
- Before trusting Redis, the query reads lightweight per-date MySQL total/member metadata for all
  seven days. Marker metadata, ZSET cardinality, and score sum must match MySQL; marker values must
  remain identical across the union read.
- A range is cache-readable only when all requested daily markers exist. Missing any marker causes a MySQL response and a rebuild of every date in the range, including dates with no rows.
- Rebuild creates a temporary daily ZSET, then atomically replaces or deletes the live key and writes the completeness marker.
- Cache updates and rebuilds use the same date-scoped lock. Post-commit updates read the durable MySQL count and set the Redis member to that absolute value; they do not blindly increment a possibly rebuilt snapshot.
- A post-commit update atomically writes the known absolute member value and publishes a new marker
  from metadata read under the same date lock. If it fails, the previous marker no longer matches
  the advanced MySQL metadata and the next query falls back.
- Query and order date calculations use the same injected `Clock`.
- The public contract remains recent seven days and top three: only `days=7` and `limit=3` are accepted.
- A cached member whose menu cannot be resolved is treated as cache corruption. The request uses the durable result and initiates rebuild instead of returning a shortened list.

## Failure and concurrency behavior

Redis read, write, lock, or rebuild failure never changes the committed order. A request with incomplete or unusable cache state returns the MySQL aggregate. Date-scoped locking plus absolute score assignment makes rebuild and post-commit cache updates convergent and prevents duplicate increments from snapshot overlap.

The DB commit and cache update are not a distributed transaction. The documented consistency boundary remains post-commit recoverability: Redis is trusted only after the completeness protocol succeeds, while MySQL remains authoritative whenever completeness is uncertain.

## Verification

Author tests for the exact inclusive seven-day range, outside-range exclusion, top-three/tie order, fixed-clock date alignment, malformed and noncanonical parameters, all-marker cache hits, partial marker loss, empty-date stale-key removal, temporary-key cleanup and TTL, missing-menu fallback, Redis failure fallback, and deterministic rebuild/update interleavings. Runtime execution remains `NOT RUN` when repository command policy provides no VERIFIED product command.
