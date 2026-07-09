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
2. Increment Redis Sorted Set score for the menu.

For recent 7-day query:

1. Union the last 7 daily Sorted Sets.
2. Read top 3 by score.
3. Fetch menu details from MySQL.

If Redis data is unavailable or lost, rebuild ranking from MySQL `daily_menu_sales`.

## Alternatives Considered

- Orders table direct aggregation: strongest simplicity, but potentially expensive at read time.
- Redis Sorted Set only: fast reads, but weak recovery story.
- MySQL daily aggregate only: durable and accurate, but less suitable for frequent ranking reads.

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

## Follow-up

- Define Redis key TTL.
- Define reconciliation job or recovery command.
- Add tests for last-7-days calculation.
- Add tests for Redis rebuild from `daily_menu_sales`.

