# Feature Spec: Order Payment

## Status

Ready

## Related Documents

- `README.md`
- `docs/05-functional-requirements.md`
- `docs/03-domain-model.md`
- `docs/07-data-and-api-contracts.md`
- `docs/09-quality-operations-and-rules.md`

## Background

사용자는 메뉴를 선택해 커피를 주문하고 포인트로 결제한다. 이 기능은 포인트 차감, 주문 생성, 결제 기록, 인기 메뉴 집계, 외부 데이터 수집 이벤트 생성이 함께 일어나는 핵심 유스케이스다.

## Scope

### In Scope

- 사용자 식별값과 메뉴 ID를 입력받아 주문 생성
- 포인트 잔액 검증 및 차감
- 주문과 결제 저장
- 포인트 사용 이력 저장
- 일별 메뉴 집계 증가
- Outbox 이벤트 저장
- Kafka 발행을 위한 이벤트 payload 정의
- 동일 사용자 동시 주문 제어

### Out of Scope

- 주문 취소/환불
- 실제 외부 데이터 플랫폼 API 구현
- 재고 관리

## Requirements

### R-001: 주문/결제 성공

Description:

사용자가 판매 중인 메뉴를 주문하면 메뉴 가격만큼 포인트가 차감되고 주문과 결제가 생성된다.

Acceptance Criteria:

- 메뉴가 존재하고 `ON_SALE` 상태여야 한다.
- 사용자 포인트 잔액이 메뉴 가격 이상이어야 한다.
- 주문 가격은 주문 시점 메뉴 가격으로 저장한다.
- 주문, 결제, 포인트 차감, 포인트 이력, Outbox 이벤트는 같은 트랜잭션으로 저장한다.

### R-002: 잔액 부족 실패

Description:

포인트 잔액이 부족하면 주문과 결제를 생성하지 않는다.

Acceptance Criteria:

- `INSUFFICIENT_POINT` 에러를 반환한다.
- 포인트 잔액은 변경되지 않는다.
- 주문, 결제, Outbox 이벤트가 생성되지 않는다.

### R-003: 주문 이벤트 생성

Description:

주문 성공 시 데이터 수집 플랫폼으로 보낼 이벤트를 Outbox에 저장한다.

Acceptance Criteria:

- `outbox_events`에 `ORDER_PAID` 이벤트가 `READY` 상태로 저장된다.
- payload에는 `userId`, `menuId`, `paymentAmount`가 포함된다.
- Kafka 발행 실패가 주문 API 실패로 이어지지 않는다.

### R-004: 주문 결제 이벤트의 내구성 있는 로컬 소비

Description:

`coffee.order.paid`의 `ORDER_PAID` 이벤트를 로컬 분석 입력으로 소비한다. 외부 데이터 플랫폼 API 연동은 여전히 범위 밖이다.

Acceptance Criteria:

- 하나의 consumer group에서 최초 전달은 `processed_events` marker와 `order_paid_analytics` 효과를 하나의 MySQL 트랜잭션으로 저장한다.
- 같은 consumer group의 동일 event 재전달은 marker와 분석 효과를 모두 중복 생성하지 않는다.
- 서로 다른 consumer group은 동일 event에 대해 각자의 marker와 분석 효과를 한 번씩 저장할 수 있다.
- 분석 저장 실패 시 marker도 rollback되어 Kafka 재전달이 전체 효과를 다시 시도할 수 있다.
- event ID, aggregate/order ID, user ID, menu ID, payment amount는 모두 양수이고 event type은 정확히 `ORDER_PAID`여야 한다.

## API Contract

Method and path:

`POST /api/v1/orders`

Request:

```json
{
  "userId": 1,
  "menuId": 10
}
```

Response:

```json
{
  "orderId": 100,
  "userId": 1,
  "menuId": 10,
  "paymentAmount": 4500,
  "remainingPoint": 10500,
  "status": "PAID"
}
```

Errors:

- `INVALID_REQUEST`: userId 또는 menuId 누락
- `MENU_NOT_FOUND`: 메뉴 없음
- `MENU_NOT_AVAILABLE`: 판매 중인 메뉴 아님
- `INSUFFICIENT_POINT`: 잔액 부족
- `LOCK_TIMEOUT`: 동일 사용자 주문/충전 처리 중
- `INTERNAL_ERROR`

## Data Changes

- `user_points.balance` 차감
- `point_histories`에 `USE` 이력 추가
- `orders` 추가
- `payments` 추가
- `daily_menu_sales` 증가
- `outbox_events`에 `ORDER_PAID` 이벤트 추가
- commit 후 해당 날짜의 현재 MySQL durable count를 Redis Sorted Set score에 절대값으로 대입하고 completeness metadata 게시

## Consistency and Concurrency

주문/결제는 `point:user:{userId}` Redisson lock으로 동일 사용자 요청을 직렬화한다. lock 획득 후 MySQL 트랜잭션을 시작하고, 포인트 차감부터 Outbox 이벤트 저장까지 원자적으로 처리한다.

Kafka 발행은 API 트랜잭션에서 직접 수행하지 않는다. Outbox 이벤트 저장까지만 주문 트랜잭션에 포함한다.

주문 트랜잭션에서는 MySQL `daily_menu_sales.order_count`를 증가시킨다. commit 후 `ranking:date:{yyyy-MM-dd}` lock 안에서 현재 durable count와 total/member metadata를 다시 읽고, Redis `ZADD`로 score를 절대값 대입하면서 completeness metadata를 게시한다. Redis 갱신 실패는 이미 commit된 주문을 rollback하지 않으며 MySQL 집계가 복구 기준이다. 따라서 post-commit 갱신을 재시도해도 Redis snapshot 증가 방식의 중복 누적 drift가 발생하지 않는다.

## Test Cases

- 주문/결제 성공
- 잔액 부족 실패
- 판매 중이 아닌 메뉴 주문 실패
- 동일 사용자 동시 주문 시 잔액 음수 방지
- 주문 성공 시 Outbox 이벤트 저장
- 주문 실패 시 Outbox 이벤트 미저장
- 일별 메뉴 집계 증가
- commit 후 Redis score 절대값 대입과 completeness metadata 게시
- Redis 갱신 실패 시 주문 유지 및 MySQL 기준 복구
- 동일 durable count 재시도 시 Redis score drift 방지
- 동일 consumer group의 동일 이벤트 중복 전달 시 분석 효과 1건 유지
- 분석 효과 저장 실패 시 processed marker 동시 rollback
- `FAILED` Outbox 이벤트의 감사된 `READY` 복구

## Open Questions

- 없음
