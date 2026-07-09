# Implementation Plan: Popular Menu

## Summary

주문 성공 시 날짜별 Redis Sorted Set과 MySQL 일별 집계 테이블을 함께 갱신한다. 조회 시에는 최근 7일 Sorted Set을 union하여 TOP 3를 반환한다.

## Technical Approach

- API: `PopularMenuController`
- Application: `PopularMenuQueryService`, `MenuSalesRecorder`
- Domain: ranking policy
- Persistence: `DailyMenuSalesRepository`, `MenuRepository`
- External: Redis Sorted Set
- Test: integration test, Redis recovery test

## Files to Add

- `ranking/api/PopularMenuController.java`
- `ranking/api/PopularMenuResponse.java`
- `ranking/application/PopularMenuQueryService.java`
- `ranking/application/MenuSalesRecorder.java`
- `ranking/infrastructure/RedisPopularMenuRepository.java`
- `ranking/infrastructure/DailyMenuSalesRepository.java`
- `ranking/domain/PopularMenu.java`

## Files to Modify

- `OrderPaymentService`에서 주문 성공 후 `MenuSalesRecorder` 호출
- schema 또는 migration

## Steps

1. `daily_menu_sales` 엔티티와 repository를 구현한다.
2. Redis Sorted Set adapter를 구현한다.
3. 주문 성공 시 일별 집계와 Redis score 증가 로직을 연결한다.
4. 최근 7일 Redis union 조회를 구현한다.
5. 메뉴 상세 정보와 orderCount를 조합한다.
6. Redis 복구용 MySQL 집계 조회를 구현한다.
7. TOP 3, 기간 제외, 복구 테스트를 작성한다.

## Risks

- Redis와 MySQL 갱신 시점이 다를 수 있다.
- Redis union key 관리와 TTL 정책이 필요하다.
- 주문 API 트랜잭션과 Redis 갱신의 실패 경계를 명확히 해야 한다.

## Rollback Plan

- Redis 조회 문제가 있으면 MySQL `daily_menu_sales` 기준 조회로 fallback한다.

