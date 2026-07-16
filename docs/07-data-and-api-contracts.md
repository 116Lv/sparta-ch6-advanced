# 07. Data and API Contracts

## Database Principles

- MySQL is the source of truth for orders, payments, points, outbox events, and daily menu sales.
- Redis is not the source of truth.
- Kafka is not the source of truth.
- All important business tables should include created/updated timestamps where appropriate.
- Money-like values use integer types.
- Point balance cannot be negative.

## Entities / Tables

### users

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | User ID |
| created_at | datetime | not null | Created time |
| updated_at | datetime | not null | Updated time |

### menus

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | Menu ID |
| name | varchar(100) | not null | Menu name |
| price | bigint | not null | Price |
| status | varchar(20) | not null | `ON_SALE`, `SOLD_OUT`, `DELETED` |
| created_at | datetime | not null | Created time |
| updated_at | datetime | not null | Updated time |

### user_points

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | Point account ID |
| user_id | bigint | unique, not null | User ID |
| balance | bigint | not null | Current balance |
| version | bigint | not null | Version/change tracking |
| created_at | datetime | not null | Created time |
| updated_at | datetime | not null | Updated time |

### point_histories

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | History ID |
| user_id | bigint | not null | User ID |
| type | varchar(20) | not null | `CHARGE`, `USE` |
| amount | bigint | not null | Changed amount |
| balance_after | bigint | not null | Balance after change |
| reason | varchar(100) | not null | Change reason |
| created_at | datetime | not null | Created time |

### orders

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | Order ID |
| user_id | bigint | not null | User ID |
| menu_id | bigint | not null | Menu ID |
| order_price | bigint | not null | Menu price at order time |
| status | varchar(20) | not null | `PAID`, `CANCELED` |
| ordered_at | datetime | not null | Ordered time |

### payments

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | Payment ID |
| order_id | bigint | unique, not null | Order ID |
| user_id | bigint | not null | User ID |
| amount | bigint | not null | Payment amount |
| status | varchar(20) | not null | `SUCCESS`, `FAILED` |
| paid_at | datetime | not null | Paid time |

### outbox_events

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | Event ID |
| aggregate_type | varchar(50) | not null | Example: `ORDER` |
| aggregate_id | bigint | not null | Order ID |
| event_type | varchar(100) | not null | Example: `ORDER_PAID` |
| payload | json | not null | Kafka payload |
| status | varchar(20) | not null | `READY`, `PROCESSING`, `PUBLISHED`, `FAILED` |
| retry_count | int | not null | Retry count |
| claim_token | varchar(100) | nullable | Unique token for the current publisher claim |
| claim_owner | varchar(100) | nullable | Publisher instance identifier for observability |
| claimed_at | datetime | nullable | Claim start time |
| claim_until | datetime | nullable | Deadline after which an unfinished claim is recoverable |
| last_error | varchar(1000) | nullable | Most recent publish failure summary without sensitive payload data |
| created_at | datetime | not null | Created time |
| updated_at | datetime | not null | Last state-change time |
| published_at | datetime | nullable | Published time |

Outbox state rules:

- The order transaction inserts `READY`; it never publishes directly to Kafka.
- A Publisher claims at most one row in a short transaction immediately before its publish attempt, changes it to `PROCESSING` with a new `claim_token` and `claim_until`, commits, publishes, and repeats up to the configured cycle size.
- Only the current `claim_token` may complete or retry a claim. This prevents a stale worker from updating a row after its expired claim was reassigned.
- A `PROCESSING` row whose `claim_until` has passed can be reclaimed with a new token.
- Kafka acknowledgement changes the matching claim to `PUBLISHED`. A retryable failure increments `retry_count` and returns the row to `READY`; exhausted retries become `FAILED` until the audited recovery service is invoked.
- Clearing claim metadata is part of every transition out of `PROCESSING`.

### daily_menu_sales

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK | Aggregate ID |
| sales_date | date | unique with menu_id, not null | Sales date |
| menu_id | bigint | unique with sales_date, not null | Menu ID |
| order_count | bigint | not null | Order count |
| created_at | datetime | not null | Created time |
| updated_at | datetime | not null | Updated time |

## API Style

- Use REST-style JSON APIs.
- Use `/api/v1` prefix.
- Use clear resource names.
- Return consistent error response bodies.

## Request / Response Rules

- Request body should be JSON.
- Response body should be JSON.
- Numeric IDs are represented as numbers unless project conventions decide otherwise.
- Money/point amounts are integer values.

## Error Format

```json
{
  "error": {
    "code": "INSUFFICIENT_POINT",
    "message": "포인트 잔액이 부족합니다.",
    "details": {}
  }
}
```

## Status Code Rules

| Code | Status | Meaning |
|---|---:|---|
| INVALID_REQUEST | 400 | Invalid request format or value |
| UNAUTHORIZED | 401 | Authentication required |
| FORBIDDEN | 403 | Permission denied |
| MENU_NOT_FOUND | 404 | Menu not found |
| MENU_NOT_AVAILABLE | 409 | Menu is not available |
| INSUFFICIENT_POINT | 409 | Not enough point balance |
| LOCK_TIMEOUT | 409 | User-level lock acquisition failed |
| INTERNAL_ERROR | 500 | Unexpected server error |

## API Contracts

Detailed feature API contracts are owned by:

- `specs/001-menu-query/spec.md`
- `specs/002-point-charge/spec.md`
- `specs/003-order-payment/spec.md`
- `specs/004-popular-menu/spec.md`

## User Identifier Rule

This assignment does not include login.

`userId` is used as an explicit request value to identify the point account owner. This is not an authentication mechanism. It is an assignment-level simplification so point charge and order/payment APIs can be tested without implementing login.

If authentication is added later, request `userId` must be replaced or verified against the authenticated principal.

## Data Retention Rules

- Point histories should not be deleted.
- Orders and payments should not be hard-deleted by default.
- Outbox events may be archived after successful publication and retention period.

## Open Questions

- Open Question: What is the exact outbox retention period?

## Popular Menu Cache Contract

`GET /api/v1/menus/popular` accepts only `days=7&limit=3`. The inclusive range is the application
clock's current date and the preceding six dates. Results order by `orderCount DESC, menuId ASC`.

MySQL `daily_menu_sales` is authoritative. A Redis range is usable only when every date marker's
generation, durable total, and durable member count agree with lightweight MySQL metadata and the
daily ZSET's cardinality/score sum. Marker generations must not change during the union read.
Daily data and marker keys expire after 14 days;
one-minute temporary union/rebuild keys are always cleaned up. Incomplete, unavailable, or
unresolvable cache data falls back to MySQL and triggers a full-range rebuild including empty
dates.

## Implemented Event Consumption Contract

### processed_events

| Column | Type | Constraint | Description |
|---|---|---|---|
| consumer_group | varchar(100) | PK with event_id | Kafka consumer group |
| event_id | bigint | PK with consumer_group | Immutable Outbox event ID |
| processed_at | datetime | not null | First accepted delivery time |

The Kafka topic is `coffee.order.paid`. The producer uses `aggregate_id` as the partition key,
so ordering is limited to one aggregate key and global ordering is not assumed. The message is:

```json
{
  "eventId": 1,
  "eventType": "ORDER_PAID",
  "aggregateId": 100,
  "payload": { "userId": 1, "menuId": 10, "paymentAmount": 4500 }
}
```

Each consumer group inserts `(consumer_group, event_id)` with `INSERT IGNORE` and writes its
`order_paid_analytics` effect in the same transaction. A redelivery therefore creates neither a
second marker nor a second effect. An analytics write failure rolls back the marker.

### order_paid_analytics

| Column | Type | Constraint | Description |
|---|---|---|---|
| consumer_group | varchar(100) | PK with event_id | Kafka consumer group |
| event_id | bigint | PK with consumer_group, positive | Immutable Outbox event ID |
| aggregate_id | bigint | unique with consumer_group, positive | Order ID |
| user_id | bigint | positive, not null | Ordering user ID |
| menu_id | bigint | positive, not null | Ordered menu ID |
| payment_amount | bigint | positive, not null | Paid amount |
| processed_at | datetime | not null | Durable effect time |

An index on `(consumer_group, processed_at)` supports consumer-group-owned scans.

### outbox_recovery_audits

| Column | Type | Constraint | Description |
|---|---|---|---|
| id | bigint | PK, auto increment | Audit ID |
| event_id | bigint | FK to outbox_events, not null | Recovered Outbox event |
| operator_name | varchar(100) | nonblank, not null | Authorized operator identity |
| reason | varchar(500) | nonblank, not null | Recovery reason |
| previous_retry_count | int | nonnegative, not null | Retry count before recovery |
| previous_error | varchar(1000) | nullable | Last error before recovery |
| recovered_at | datetime | not null | Recovery time |

The table has an index on `(event_id, recovered_at)`. `OutboxRecoveryService.requeueFailed`
locks the event, appends the immutable audit, and performs `FAILED -> READY` with retry count zero
and cleared error/claim metadata in one transaction. Missing or non-`FAILED` events are rejected
without an audit. Direct unaudited SQL requeue is prohibited.
