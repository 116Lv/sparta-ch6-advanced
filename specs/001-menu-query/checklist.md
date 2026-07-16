# Checklist: Menu Query

## 2026-07-15 Audit Evidence

- [x] Implementation and authored tests satisfy the statically inspectable checklist items.
- [ ] Runtime test and API evidence is available from a supported VERIFIED command.

## Spec Quality

- [x] 요구사항이 명확하다.
- [x] API 계약이 있다.
- [x] 실패 케이스가 있다.
- [x] 동시성/일관성 고려가 있다.
- [x] 테스트 기준이 있다.

## Implementation Quality

- [ ] 판매 중 메뉴만 조회한다.
- [ ] 메뉴 ID, 이름, 가격을 반환한다.
- [ ] controller에 비즈니스 로직이 없다.
- [ ] 주문 API가 메뉴 가격을 주문 시점에 다시 조회한다.

## Test Quality

- [ ] 판매 중 메뉴 조회 테스트가 있다.
- [ ] 품절/삭제 메뉴 제외 테스트가 있다.
- [ ] 빈 목록 테스트가 있다.

