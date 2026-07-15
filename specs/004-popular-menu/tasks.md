# Tasks: Popular Menu

## 2026-07-15 Static Audit Tracking

- [x] MySQL authority, seven-day completeness markers, generation checks, fallback rebuild, and absolute updates are tracked and authored.
- [x] Temporary ZSET population, safety TTL, live replacement, and marker publication are atomic in one Lua script.
- [ ] Product, Redis, MySQL, Docker, and real HTTP verification run through a supported VERIFIED command.

## Phase 1: Design Check

- [ ] `docs/03-domain-model.md`와 `docs/09-quality-operations-and-rules.md`의 인기 메뉴 전략 확인
- [ ] Redis key 정책 확인
- [ ] 일별 집계 테이블 unique constraint 확인

## Phase 2: Domain

- [ ] `DailyMenuSale` 엔티티 구현
- [ ] `PopularMenu` DTO/domain 구현
- [ ] 정렬 정책 구현

## Phase 3: Application and Persistence

- [ ] `DailyMenuSalesRepository` 구현
- [ ] `RedisPopularMenuRepository` 구현
- [ ] `MenuSalesRecorder` 구현
- [ ] `PopularMenuQueryService` 구현
- [ ] Redis union 조회 구현

## Phase 4: API

- [ ] `PopularMenuController` 구현
- [ ] `PopularMenuResponse` 구현
- [ ] days/limit validation 구현

## Phase 5: Verification

- [ ] 최근 7일 TOP 3 테스트 작성
- [ ] 기간 밖 주문 제외 테스트 작성
- [ ] 동률 정렬 테스트 작성
- [ ] Redis 유실 복구 테스트 작성
- [ ] checklist 갱신
- [ ] decisions 갱신
