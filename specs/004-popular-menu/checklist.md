# Checklist: Popular Menu

## 2026-07-15 Audit Evidence

- [x] Implementation and authored tests satisfy the statically inspectable ranking completeness and recovery items.
- [x] Runtime test, Redis, database, and API evidence is available from supported VERIFIED commands and finalized manifests.
- [x] Static E2E implementation observes the daily Redis ranking and public popular-menu response.
- [x] E2E assertions have finalized Ubuntu-native Docker Compose runtime evidence.

## Spec Quality

- [x] 요구사항이 명확하다.
- [x] API 계약이 있다.
- [x] 실패 케이스가 있다.
- [x] 동시성/일관성 고려가 있다.
- [x] 테스트 기준이 있다.

## Implementation Quality

- [ ] 최근 7일 기준으로 조회한다.
- [ ] TOP 3를 반환한다.
- [ ] 주문 횟수 내림차순으로 정렬한다.
- [ ] 동률 시 메뉴 ID 오름차순으로 정렬한다.
- [ ] Redis Sorted Set을 사용한다.
- [ ] MySQL 일별 집계 테이블로 복구 가능하다.

## Test Quality

- [ ] TOP 3 조회 테스트가 있다.
- [ ] 기간 밖 주문 제외 테스트가 있다.
- [ ] 동률 정렬 테스트가 있다.
- [ ] Redis ranking update 테스트가 있다.
- [ ] MySQL 일별 집계 update 테스트가 있다.
- [ ] Redis 복구 테스트가 있다.

