# Implementation Plan: Menu Query

## Summary

Spring MVC Controller에서 메뉴 목록 요청을 받고, application service가 menu repository를 통해 판매 중인 메뉴를 조회한다.

## Technical Approach

- API: `MenuController`
- Application: `MenuQueryService`
- Domain: `Menu`, `MenuStatus`
- Persistence: `MenuRepository`
- External: 없음
- Test: controller slice 또는 integration test

## Files to Add

- `menu/api/MenuController.java`
- `menu/api/MenuResponse.java`
- `menu/application/MenuQueryService.java`
- `menu/domain/Menu.java`
- `menu/domain/MenuStatus.java`
- `menu/infrastructure/MenuRepository.java`
- `menu/MenuQueryIntegrationTest.java`

## Files to Modify

- 초기 schema 또는 migration
- seed data 또는 test fixture

## Steps

1. `Menu` 엔티티와 `MenuStatus`를 정의한다.
2. 판매 중 메뉴 조회 repository method를 작성한다.
3. `MenuQueryService`에서 조회 결과를 DTO로 변환한다.
4. `GET /api/v1/menus` controller를 구현한다.
5. 판매 중/품절/삭제 메뉴 필터링 테스트를 작성한다.

## Risks

- 메뉴 가격이 주문 시점에 변경될 수 있으므로 주문 API에서 메뉴 가격을 다시 확인해야 한다.

## Rollback Plan

- 메뉴 조회 기능은 읽기 전용이므로 배포 문제 발생 시 controller route를 비활성화하면 된다.

