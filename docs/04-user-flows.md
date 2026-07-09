# 04. User Flows

## Flow Template

Each flow should define:

- Goal
- Actors
- Preconditions
- Steps
- Success State
- Failure States
- Edge Cases

## Core Flows

### Flow 1: 메뉴 목록 조회

Goal:

사용자가 주문 가능한 커피 메뉴를 확인한다.

Actors:

- API Client
- User

Steps:

1. 클라이언트가 `GET /api/v1/menus`를 호출한다.
2. 서버는 판매 중인 메뉴를 조회한다.
3. 서버는 메뉴 ID, 이름, 가격을 반환한다.

Success State:

- 클라이언트는 주문 가능한 메뉴 목록을 받는다.

Failure States:

- 예상하지 못한 서버 오류는 `500`으로 반환된다.

### Flow 2: 포인트 충전

Goal:

사용자가 주문에 사용할 포인트를 충전한다.

Actors:

- API Client
- User

Steps:

1. 클라이언트가 사용자 식별값과 충전 금액을 전달한다.
2. 서버는 충전 금액이 양수인지 검증한다.
3. 서버는 사용자 단위 Redisson lock을 획득한다.
4. 서버는 MySQL 트랜잭션 안에서 포인트 잔액을 증가시킨다.
5. 서버는 포인트 충전 이력을 저장한다.
6. 서버는 lock을 해제하고 충전 후 잔액을 반환한다.

Success State:

- 포인트 잔액이 증가한다.
- 충전 이력이 남는다.

Failure States:

- 충전 금액이 0 이하이면 `400`.
- lock 획득 실패 시 `409`.

### Flow 3: 커피 주문/결제

Goal:

사용자가 메뉴를 주문하고 포인트로 결제한다.

Actors:

- API Client
- User

Steps:

1. 클라이언트가 사용자 식별값과 메뉴 ID를 전달한다.
2. 서버는 사용자 단위 Redisson lock을 획득한다.
3. 서버는 메뉴 판매 가능 여부를 확인한다.
4. 서버는 포인트 잔액을 확인한다.
5. 서버는 포인트를 차감한다.
6. 서버는 포인트 사용 이력을 저장한다.
7. 서버는 주문과 결제를 저장한다.
8. 서버는 일별 메뉴 집계를 증가시킨다.
9. 서버는 Outbox 이벤트를 저장한다.
10. 서버는 트랜잭션을 commit한다.
11. 서버는 Redis Sorted Set을 갱신한다.
12. 서버는 주문 결과를 반환한다.

Success State:

- 주문과 결제가 생성된다.
- 포인트가 차감된다.
- Outbox 이벤트가 생성된다.
- 인기 메뉴 집계가 반영된다.

Failure States:

- 메뉴가 없으면 `404`.
- 판매 중이 아니면 `409`.
- 잔액이 부족하면 `409`.
- lock 획득 실패 시 `409`.

### Flow 4: 인기 메뉴 조회

Goal:

사용자가 최근 7일간 인기 있는 메뉴 3개를 확인한다.

Actors:

- API Client
- User

Steps:

1. 클라이언트가 `GET /api/v1/menus/popular?days=7&limit=3`을 호출한다.
2. 서버는 최근 7일 Redis Sorted Set을 union한다.
3. 서버는 TOP 3 메뉴 ID와 주문 횟수를 구한다.
4. 서버는 메뉴 상세 정보를 MySQL에서 조회한다.
5. 서버는 메뉴 정보와 주문 횟수를 반환한다.

Success State:

- 최근 7일 기준 인기 메뉴 TOP 3가 반환된다.

Failure States:

- Redis 조회 실패 시 MySQL 일별 집계 fallback 또는 복구 전략을 사용한다.

## Edge Cases

- 같은 사용자가 동시에 여러 주문을 요청한다.
- 충전과 주문이 동시에 요청된다.
- Kafka 발행이 실패한다.
- Redis 랭킹 데이터가 유실된다.
- 메뉴 가격이 주문 직전에 변경된다.

## Failure States

Failure handling details are owned by `docs/07-data-and-api-contracts.md#error-format` and `docs/09-quality-operations-and-rules.md`.

## Open Questions

- Open Question: Redis 갱신 실패를 주문 API 응답에 반영할 것인가, 보정 대상으로만 남길 것인가?

