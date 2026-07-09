# Implementation Plan: Order Payment

## Summary

주문/결제 유스케이스는 Redisson lock과 MySQL transaction을 함께 사용한다. 주문 성공 이벤트는 Outbox에 저장하고 Kafka 발행은 별도 publisher가 처리한다.

## Technical Approach

- API: `OrderController`
- Application: `OrderPaymentService`
- Domain: `Order`, `Payment`, `UserPoint`
- Persistence: JPA repositories, QueryDSL if needed
- External: Redisson, Redis Sorted Set, Kafka Outbox publisher
- Test: integration test, concurrency test, outbox test

## Files to Add

- `order/api/OrderController.java`
- `order/api/OrderRequest.java`
- `order/api/OrderResponse.java`
- `order/application/OrderPaymentService.java`
- `order/domain/Order.java`
- `order/domain/OrderStatus.java`
- `order/domain/Payment.java`
- `order/domain/PaymentStatus.java`
- `order/infrastructure/OrderRepository.java`
- `order/infrastructure/PaymentRepository.java`
- `outbox/domain/OutboxEvent.java`
- `outbox/infrastructure/OutboxEventRepository.java`
- `outbox/application/OutboxPublisher.java`
- `ranking/application/MenuSalesRecorder.java`
- `ranking/infrastructure/RedisPopularMenuRepository.java`
- `ranking/infrastructure/DailyMenuSalesRepository.java`

## Files to Modify

- `point` module for point use operation
- schema 또는 migration
- global error handler

## Steps

1. 주문/결제 엔티티를 정의한다.
2. Outbox 이벤트 엔티티를 정의한다.
3. 포인트 차감 도메인 메서드를 구현한다.
4. 일별 메뉴 집계 증가 repository를 구현한다.
5. Redis Sorted Set 증가 adapter를 구현한다.
6. `OrderPaymentService`에서 lock과 transaction 경계를 구성한다.
7. 주문 API를 구현한다.
8. Outbox publisher를 구현한다.
9. 정상/실패/동시성/Outbox 테스트를 작성한다.

## Risks

- Redis ranking update가 트랜잭션 밖에서 실패할 수 있다.
- Outbox publisher가 중복 발행할 수 있으므로 eventId 기반 멱등성을 고려해야 한다.
- lock lease time 설정이 부적절하면 동시성 제어가 깨질 수 있다.

## Rollback Plan

- Kafka 발행 문제가 있어도 주문 API는 Outbox 저장까지만 책임지므로 주문 기능은 유지된다.
- Redis 랭킹 문제가 있으면 MySQL 일별 집계 기준 조회 또는 복구 작업으로 전환한다.

