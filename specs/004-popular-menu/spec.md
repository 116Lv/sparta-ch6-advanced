# Feature Spec: Popular Menu

## Status

Ready

## Related Documents

- `README.md`
- `docs/05-functional-requirements.md`
- `docs/03-domain-model.md`
- `docs/07-data-and-api-contracts.md`
- `docs/09-quality-operations-and-rules.md`

## Background

사용자는 최근 7일간 인기 있는 메뉴 3개를 조회할 수 있어야 한다. 주문 횟수는 정확해야 하며, 조회 성능도 고려해야 한다.

## Scope

### In Scope

- 최근 7일 인기 메뉴 TOP 3 조회
- Redis Sorted Set 기반 빠른 랭킹 조회
- MySQL `daily_menu_sales` 기준 집계 보관
- Redis 유실 시 복구 전략

### Out of Scope

- 개인화 추천
- 카테고리별 인기 메뉴
- 실시간 스트리밍 대시보드
- 관리자 통계 화면

## Requirements

### R-001: 인기 메뉴 TOP 3 조회

Description:

최근 7일간 주문 횟수가 많은 메뉴 3개를 조회한다.

Acceptance Criteria:

- 최근 7일 범위의 주문 수만 포함한다.
- 메뉴별 주문 횟수를 반환한다.
- 주문 횟수 내림차순으로 정렬한다.
- 동률이면 메뉴 ID 오름차순으로 정렬한다.

### R-002: 주문 횟수 정확성

Description:

Redis 조회 성능을 활용하되, MySQL 일별 집계 테이블을 기준 데이터로 유지한다.

Acceptance Criteria:

- 주문 성공 시 Redis Sorted Set score가 증가한다.
- 주문 성공 시 `daily_menu_sales.order_count`가 증가한다.
- Redis 데이터가 유실되어도 MySQL 기준으로 재구성할 수 있다.

## API Contract

Method and path:

`GET /api/v1/menus/popular?days=7&limit=3`

Response:

```json
{
  "periodDays": 7,
  "menus": [
    {
      "menuId": 10,
      "name": "Americano",
      "price": 4500,
      "orderCount": 120
    }
  ]
}
```

Errors:

- `INVALID_REQUEST`: days 또는 limit 값이 허용 범위를 벗어남
- `INTERNAL_ERROR`

## Data Changes

조회 API 자체는 데이터를 변경하지 않는다. 주문 성공 시 다음 데이터가 갱신된다.

- Redis Sorted Set: `popular-menu:{yyyy-MM-dd}`
- MySQL: `daily_menu_sales`

## Consistency and Concurrency

인기 메뉴 조회는 Redis를 우선 사용한다. Redis는 빠른 조회용이며 기준 데이터는 MySQL 일별 집계 테이블이다. Redis 갱신 실패가 발생해도 주문 성공 트랜잭션에서 `daily_menu_sales`가 증가했다면 복구 가능하다.

## Test Cases

- 최근 7일 TOP 3 조회
- 기간 밖 주문 제외
- 동률 시 메뉴 ID 오름차순 정렬
- Redis Sorted Set 기준 조회
- MySQL 일별 집계 기준 복구
- 주문 성공 시 Redis와 MySQL 집계 증가

## Open Questions

- 없음
