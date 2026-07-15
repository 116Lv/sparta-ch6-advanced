# Checklist: Order Payment

## 2026-07-15 Audit Evidence

- [x] Implementation and authored tests cover the durable order graph, publisher, consumer analytics, and recovery path.
- [ ] Runtime test, Kafka, database, migration, and API evidence is available from a supported VERIFIED command.

## Spec Quality

- [x] 요구사항이 명확하다.
- [x] API 계약이 있다.
- [x] 실패 케이스가 있다.
- [x] 동시성/일관성 고려가 있다.
- [x] 테스트 기준이 있다.

## Implementation Quality

- [ ] 주문/결제는 Redisson lock 안에서 실행된다.
- [ ] 포인트 차감, 주문, 결제, Outbox 저장은 같은 DB 트랜잭션이다.
- [ ] 잔액 부족 시 모든 변경이 rollback된다.
- [ ] 주문 성공 시 Outbox 이벤트가 저장된다.
- [ ] Kafka 발행 실패가 주문 실패로 이어지지 않는다.
- [ ] 일별 메뉴 집계가 증가한다.
- [ ] Redis Sorted Set score가 증가한다.

## Test Quality

- [ ] 주문 성공 테스트가 있다.
- [ ] 잔액 부족 실패 테스트가 있다.
- [ ] 판매 불가 메뉴 실패 테스트가 있다.
- [ ] 동일 사용자 동시 주문 테스트가 있다.
- [ ] Outbox 이벤트 저장 테스트가 있다.
- [ ] Kafka 발행 실패 재시도 테스트가 있다.

