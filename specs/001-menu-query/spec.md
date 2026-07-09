# Feature Spec: Menu Query

## Status

Ready

## Related Documents

- `README.md`
- `docs/05-functional-requirements.md`
- `docs/03-domain-model.md`
- `docs/07-data-and-api-contracts.md`

## Background

사용자는 주문 전에 커피 메뉴 목록을 조회할 수 있어야 한다. 메뉴 데이터는 주문/결제의 기준 가격이 되므로 ID, 이름, 가격을 명확히 제공한다.

## Scope

### In Scope

- 판매 중인 커피 메뉴 목록 조회
- 메뉴 ID, 이름, 가격 반환
- 기본 정렬 기준 정의

### Out of Scope

- 메뉴 생성/수정/삭제 API
- 관리자 기능
- 메뉴 옵션, 사이즈, 재고 관리

## Requirements

### R-001: 메뉴 목록 조회

Description:

판매 중인 메뉴 목록을 조회한다.

Acceptance Criteria:

- `ON_SALE` 상태의 메뉴만 반환한다.
- 응답에는 `id`, `name`, `price`가 포함된다.
- 기본 정렬은 `id` 오름차순이다.

## API Contract

Method and path:

`GET /api/v1/menus`

Response:

```json
{
  "menus": [
    {
      "id": 1,
      "name": "Americano",
      "price": 4500
    }
  ]
}
```

Errors:

- `INTERNAL_ERROR`

## Data Changes

- `menus` 테이블을 조회한다.

## Consistency and Concurrency

메뉴 조회는 읽기 전용 기능이다. 동시성 제어가 필요한 기능은 아니지만, 주문 시에는 메뉴 가격을 다시 조회하여 주문 시점 가격을 `orders.order_price`에 저장한다.

## Test Cases

- 판매 중인 메뉴만 조회된다.
- 품절 또는 삭제 상태 메뉴는 제외된다.
- 메뉴가 없으면 빈 배열을 반환한다.

## Open Questions

- 없음
