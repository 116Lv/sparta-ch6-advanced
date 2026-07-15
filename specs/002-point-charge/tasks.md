# Tasks: Point Charge

## 2026-07-15 Static Audit Tracking

- [x] Point domain, persistence, locking, API, concurrency scenarios, and focused contract tests inspected/authored.
- [ ] Product tests and real HTTP verification run through a supported VERIFIED command.

## Phase 1: Design Check

- [ ] `docs/03-domain-model.md`와 `docs/09-quality-operations-and-rules.md`의 lock/검증 정책 확인
- [ ] 포인트 충전 API 계약 확인
- [ ] 충전 금액 validation 기준 확인

## Phase 2: Domain

- [ ] `UserPoint` 엔티티 구현
- [ ] `PointHistory` 엔티티 구현
- [ ] 충전 도메인 메서드 구현
- [ ] 잔액 음수 불가 규칙 테스트 작성

## Phase 3: Application and Persistence

- [ ] `UserPointRepository` 구현
- [ ] `PointHistoryRepository` 구현
- [ ] `DistributedLockManager` 구현
- [ ] `PointChargeService` 구현
- [ ] 충전 integration test 작성

## Phase 4: API

- [ ] `PointChargeRequest` validation 구현
- [ ] `PointChargeResponse` 구현
- [ ] `PointController` 구현
- [ ] error response 테스트 작성

## Phase 5: Verification

- [ ] 동일 사용자 동시 충전 테스트 작성
- [ ] 충전과 주문 동시 요청 테스트 계획 확인
- [ ] checklist 갱신
- [ ] decisions 갱신
