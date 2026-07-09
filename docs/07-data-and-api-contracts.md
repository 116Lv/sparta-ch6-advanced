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
| status | varchar(20) | not null | `READY`, `PUBLISHED`, `FAILED` |
| retry_count | int | not null | Retry count |
| created_at | datetime | not null | Created time |
| published_at | datetime | nullable | Published time |

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
- TODO: Define concrete retention periods.

## Open Questions

- Open Question: Should `payload` use MySQL JSON type or text column for portability?
- Open Question: What is the exact outbox retention period?
