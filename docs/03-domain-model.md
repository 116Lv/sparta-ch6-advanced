# 03. Domain Model

## Core Concepts

### User

커피를 주문하고 포인트를 보유하는 사용자다.

Rules:

- 사용자는 하나의 포인트 계정을 가진다.
- 현재 과제에서는 request의 사용자 식별값으로 사용자를 식별한다.

### Menu

주문 가능한 커피 메뉴다.

Rules:

- 가격은 0보다 커야 한다.
- 판매 중인 메뉴만 주문할 수 있다.
- 과거 주문의 가격 보존을 위해 주문 시점 가격을 `orders.order_price`에 저장한다.

### UserPoint

사용자의 현재 포인트 잔액이다.

Rules:

- 잔액은 음수가 될 수 없다.
- 동일 사용자의 포인트 변경은 Redisson 분산락으로 직렬화한다.
- 포인트 변경은 이력으로 남긴다.

### PointHistory

포인트 충전과 사용 이력이다.

Rules:

- 충전은 `CHARGE`, 사용은 `USE` 타입으로 저장한다.
- 장애 분석과 잔액 검증을 위해 이력은 삭제하지 않는다.

### Order

사용자가 특정 메뉴를 주문한 기록이다.

Rules:

- 주문 생성과 결제 성공은 같은 트랜잭션에서 처리한다.
- 잔액 부족 시 주문을 생성하지 않는다.

### Payment

주문에 대한 포인트 결제 기록이다.

Rules:

- 결제 수단은 포인트만 허용한다.
- 결제 금액은 주문 시점의 메뉴 가격과 같아야 한다.

### OutboxEvent

외부 데이터 수집 플랫폼으로 전송해야 하는 주문 이벤트다.

Rules:

- 주문 트랜잭션 안에서 저장한다.
- Kafka 발행 성공 시 `PUBLISHED`로 변경한다.
- 발행 실패 시 재시도 대상으로 남긴다.

### DailyMenuSale

메뉴별 일별 주문 집계다.

Rules:

- 주문 성공 시 해당 날짜와 메뉴의 주문 횟수를 증가시킨다.
- Redis 인기 메뉴 랭킹 복구 기준으로 사용한다.

## Entities

| Entity | Purpose |
|---|---|
| User | 주문 사용자 |
| Menu | 커피 메뉴 |
| UserPoint | 현재 포인트 잔액 |
| PointHistory | 포인트 충전/사용 이력 |
| Order | 주문 기록 |
| Payment | 포인트 결제 기록 |
| OutboxEvent | Kafka 발행 대상 이벤트 |
| DailyMenuSale | 메뉴별 일별 주문 집계 |

## Relationships

```txt
User 1:1 UserPoint
User 1:N PointHistory
User 1:N Order
Menu 1:N Order
Order 1:1 Payment
Order 1:N OutboxEvent
Menu 1:N DailyMenuSale
```

## Business Rules

### BR-001: 포인트 잔액은 음수가 될 수 없다

주문 금액이 현재 포인트 잔액보다 크면 주문과 결제를 생성하지 않는다.

### BR-002: 포인트 변경은 사용자 단위로 직렬화한다

동일 사용자의 충전/주문 요청은 Redisson 분산락을 통해 동시에 실행되지 않도록 한다.

### BR-003: 주문과 결제는 원자적으로 처리한다

포인트 차감, 주문 생성, 결제 저장, 포인트 이력 저장은 하나의 MySQL 트랜잭션에 포함한다.

### BR-004: 주문 성공 이벤트는 유실되면 안 된다

주문이 성공했다면 외부 전송 대상 이벤트가 Outbox에 반드시 저장되어야 한다.

### BR-005: 인기 메뉴 주문 횟수는 복구 가능해야 한다

Redis Sorted Set은 빠른 조회용이며, MySQL `daily_menu_sales`가 복구 기준이다.

## Glossary

| Term | Meaning |
|---|---|
| Point | 결제에 사용하는 선불 잔액. 1원은 1P |
| Distributed Lock | 다수 서버 환경에서 공유 자원 접근을 직렬화하는 락 |
| Outbox | DB 트랜잭션과 이벤트 발행을 분리하기 위한 이벤트 저장 테이블 |
| Popular Menu | 최근 7일 주문 횟수 기준 TOP 메뉴 |

## Open Questions

- Open Question: 주문 취소/환불 도메인을 추후 포함할 것인가?
- Open Question: 메뉴 품절 상태를 구현할 것인가, 문서상 상태만 둘 것인가?

