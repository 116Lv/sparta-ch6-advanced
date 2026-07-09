# Decisions: Order Payment

## Decision Log

### 2026-07-09: 주문/결제는 Redisson lock과 MySQL transaction을 함께 사용한다

## Context

동일 사용자가 동시에 여러 주문을 요청하면 포인트 잔액이 중복 차감되거나 음수가 될 수 있다. 애플리케이션 서버가 여러 대라면 JVM 내부 lock은 사용할 수 없다.

## Decision

주문/결제 유스케이스는 `point:user:{userId}` Redisson lock을 획득한 뒤 MySQL transaction 안에서 처리한다.

## Reason

Redisson lock은 다수 서버 환경에서 사용자 단위 임계구역을 보장한다. MySQL transaction은 포인트 차감, 주문, 결제, Outbox 저장의 원자성을 보장한다. 두 기술은 서로 대체 관계가 아니라 역할이 다르다.

## Alternatives Considered

- synchronized: 단일 JVM에서만 유효하다.
- DB pessimistic lock만 사용: 정합성은 강하지만 application 수준에서 사용자 단위 진입 제어 의도가 약하다.
- optimistic lock: 충돌 재시도 설계가 필요하고 사용자 경험이 흔들릴 수 있다.

## Consequences

- Positive: 다수 서버 환경에서도 포인트 차감 경합을 제어할 수 있다.
- Negative: Redis 장애 시 주문 처리가 제한된다.
- Follow-up: lock 획득 실패율과 평균 대기 시간을 모니터링한다.

### 2026-07-09: 주문 이벤트는 Transactional Outbox로 저장한다

## Context

주문 성공 후 데이터 수집 플랫폼으로 실시간 전송해야 한다. 하지만 Kafka 발행을 주문 트랜잭션 내부에서 직접 수행하면 DB commit과 메시지 발행의 원자성을 보장하기 어렵다.

## Decision

주문 트랜잭션 안에서는 Outbox 이벤트만 저장한다. Kafka 발행은 별도 publisher가 처리한다.

## Reason

Outbox를 사용하면 주문 성공과 이벤트 발행 대상 저장을 같은 DB 트랜잭션으로 묶을 수 있다. Kafka 발행 실패는 재시도 가능하며, 주문 API의 성공 여부와 직접 결합하지 않는다.

## Alternatives Considered

- 주문 API에서 Kafka 직접 발행: 구현은 단순하지만 DB commit과 메시지 발행의 불일치 가능성이 있다.
- 외부 Mock API 직접 호출: 네트워크 지연과 실패가 주문 API에 직접 영향을 준다.

## Consequences

- Positive: 이벤트 유실 가능성을 줄이고 재시도 가능하다.
- Negative: Outbox publisher와 상태 관리가 추가된다.
- Follow-up: 이벤트 중복 발행에 대비해 consumer 멱등성을 고려한다.

