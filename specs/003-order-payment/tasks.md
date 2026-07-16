# Tasks: Order Payment

## 2026-07-15 Static Audit Tracking

- [x] Order graph, Outbox publishing, claim/retry lifecycle, and focused contract tests inspected/authored.
- [x] Consumer analytics effect, idempotent marker, rollback behavior, and audited FAILED recovery are tracked and authored.
- [ ] Product, Kafka, MySQL, Redis, migration, and real HTTP verification run through a supported VERIFIED command.
- [x] Docker Compose E2E topology and assertions authored for HTTP payment, durable order graph, Outbox publication, real-broker consumption, and same-group duplicate idempotency.
- [ ] Docker Compose E2E runtime gate passes through finalized `verify.e2e` evidence (NOT RUN/BLOCKED: supported POSIX runner unavailable on the current host).

## Phase 1: Design Check

- [ ] `docs/03-domain-model.md`와 `docs/09-quality-operations-and-rules.md`의 주문 트랜잭션/검증 기준 확인
- [ ] Outbox 이벤트 payload 확인
- [ ] 인기 메뉴 집계 반영 위치 확인

## Phase 2: Domain

- [ ] `Order` 엔티티 구현
- [ ] `Payment` 엔티티 구현
- [ ] `OutboxEvent` 엔티티 구현
- [ ] 포인트 차감 도메인 규칙 구현
- [ ] 잔액 부족 unit test 작성

## Phase 3: Application and Persistence

- [ ] `OrderRepository` 구현
- [ ] `PaymentRepository` 구현
- [ ] `OutboxEventRepository` 구현
- [ ] `DailyMenuSalesRepository` 구현
- [ ] Redis ranking adapter 구현
- [ ] `OrderPaymentService` 구현
- [ ] 주문/결제 integration test 작성

## Phase 4: API

- [ ] `OrderRequest` validation 구현
- [ ] `OrderResponse` 구현
- [ ] `OrderController` 구현
- [ ] error response 테스트 작성

## Phase 5: Event Publishing

- [ ] Outbox polling 로직 구현
- [ ] Kafka producer 구현
- [ ] 발행 성공 상태 변경 구현
- [ ] 발행 실패 재시도 상태 구현

## Phase 6: Verification

- [ ] 동일 사용자 동시 주문 테스트 작성
- [ ] 잔액 부족 시 주문 미생성 테스트 작성
- [ ] Outbox 이벤트 저장 테스트 작성
- [ ] Redis/DailyMenuSales 증가 테스트 작성
- [ ] checklist 갱신
- [ ] decisions 갱신
