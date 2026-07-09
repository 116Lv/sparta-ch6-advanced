# Decisions: Point Charge

## Decision Log

### 2026-07-09: 포인트 충전에도 Redisson 분산락을 적용한다

## Context

포인트 충전은 주문/결제보다 단순하지만 같은 `user_points.balance`를 변경한다. 충전과 주문이 동시에 실행되면 최종 잔액 계산이 요청 순서에 따라 달라질 수 있다.

## Decision

포인트 변경 작업은 모두 `point:user:{userId}` Redisson lock을 사용한다.

## Reason

포인트 충전과 차감이 같은 기준으로 직렬화되어야 잔액 불변식을 설명하기 쉽다. 다수 서버 환경에서는 JVM 내부 lock이 의미가 없으므로 Redis 기반 분산락을 사용한다.

## Alternatives Considered

- DB row lock만 사용: DB 기준 일관성은 강하지만, 사용자 단위 임계구역 의도가 application 수준에서 덜 드러난다.
- Optimistic lock만 사용: 충돌 시 재시도 정책이 필요하고 과제 설명이 복잡해진다.

## Consequences

- Positive: 포인트 변경 경로가 일관된 동시성 정책을 가진다.
- Negative: Redis 장애 시 포인트 변경 요청이 실패할 수 있다.
- Follow-up: lock 실패 시 재시도 정책과 모니터링 지표를 추가할 수 있다.

