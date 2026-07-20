# 주문 결제 완료 Consumer 및 Outbox 복구 설계

## 상태

승인된 방향: 외부 데이터 플랫폼 API는 범위 밖으로 유지하면서 실제 로컬 내구성 consumer 효과를 구현한다.

## 배경

현재 `OrderPaidConsumer`는 `(consumer_group, event_id)`를 `processed_events`에 삽입한 후 반환한다. 이는 비즈니스 효과가 없는 멱등성 마커다. analytics 데이터가 저장되지 않았는데도 첫 전송은 처리된 것으로 확인되고 이후 전송은 폐기된다.

같은 검토에서 인접한 Outbox 공백 두 가지도 발견했다.

- 순차 Kafka 전송 전에 점유 batch가 하나의 공통 임대를 받으므로 후속 행은 전송이 시작되기 전에 만료될 수 있다.
- `FAILED`는 수동으로 복구 가능하다고 설명되지만 감사된 복구 작업이 없다.

## 검토한 접근 방식

### 1. 로컬 내구성 analytics 수집 — 선택됨

구체적인 analytics record를 MySQL에 영속화한다. 멱등성 마커와 analytics 효과는 하나의 트랜잭션에서 커밋된다. 이는 결정적이고 테스트 가능하며, 정의되지 않은 외부 API를 도입하지 않는다.

### 2. 동기 외부 analytics API

Kafka listener에서 외부 플랫폼을 호출한다. 이는 과제가 정의하지 않는 API 계약, 인증, 타임아웃/재시도 정책 및 외부 멱등성 계약을 요구한다. 범위 밖으로 남는다.

### 3. Consumer 제거

Kafka 소비를 범위 밖으로 유지하고 아무 동작도 하지 않는 consumer를 삭제한다. 이는 내부적으로 일관적이지만 사용자는 실제 consumer 구현을 선택했다.

## Consumer 아키텍처

### 메시지 계약

listener는 기존 envelope를 수락한다.

```json
{
  "eventId": 1,
  "eventType": "ORDER_PAID",
  "aggregateId": 100,
  "payload": {
    "userId": 1,
    "menuId": 10,
    "paymentAmount": 4500
  }
}
```

모든 숫자 식별자와 `paymentAmount`는 양수여야 한다. `eventType`은 정확히 `ORDER_PAID`여야 한다. 누락, null, 숫자가 아님 또는 유효하지 않은 값은 전송을 거부하고 marker나 analytics record를 모두 만들지 않는다.

### 트랜잭션 경계

`OrderPaidConsumer`는 Kafka 역직렬화와 검증을 소유한 다음 `OrderPaidAnalyticsService.apply(message)`를 호출한다.

`OrderPaidAnalyticsService.apply`는 하나의 MySQL 트랜잭션이다.

1. `(consumer_group, event_id)`를 `processed_events`에 `INSERT IGNORE`로 삽입한다.
2. 삽입이 `0`을 반환하면 효과를 적용하지 않고 반환한다.
3. 삽입이 `1`을 반환하면 consumer group, event ID, aggregate/order ID, user ID, menu ID, 결제 금액 및 처리 시간을 포함하는 `order_paid_analytics` record 하나를 삽입한다.
4. 두 쓰기를 함께 커밋한다.

analytics 영속성이 실패하면 트랜잭션은 marker를 롤백한다. 따라서 Kafka 재전송은 완전한 효과를 재시도할 수 있다. marker는 효과가 없는 상태로 절대로 커밋되지 않는다.

### Analytics schema

`order_paid_analytics`는 `(consumer_group, event_id)`를 primary key로 사용하고 고유한 `(consumer_group, aggregate_id)` 제약 조건을 가진다. event, aggregate, user, menu, payment 값에는 필수 양수 값 검사가 적용된다. `(consumer_group, processed_at)` 인덱스는 group이 소유한 analytics scan을 지원한다.

서로 다른 consumer group은 각자 이벤트의 논리적 사본을 적용할 수 있다. 동일 group은 같은 이벤트를 두 번 적용할 수 없다.

## Publisher 점유 안전성

구성된 제한 cycle 크기는 유지하되, 각 발행 시도 직전에 행 하나만 점유한다.

1. 짧은 트랜잭션을 시작한다.
2. 비관적 락과 skip-locked semantics로 점유 가능한 행 하나를 선택한다.
3. 새 token, owner, deadline을 설정한 후 커밋한다.
4. 해당 행을 발행한다.
5. 현재 token을 사용하여 완료 또는 실패 처리한다.
6. cycle 제한에 도달하거나 점유 가능한 행이 없을 때까지 반복한다.

이전 행이 Kafka 확인을 기다리는 동안 후속 행은 임대를 보유하지 않는다. 여러 publisher 인스턴스는 여전히 행 락을 통해 경쟁하고 만료된 `PROCESSING` 행은 계속 재점유할 수 있다.

## FAILED 복구

내부 `OutboxRecoveryService.requeueFailed(eventId, operator, reason)` 작업을 추가한다. 하나의 MySQL 트랜잭션에서 실행한다.

1. ID로 이벤트를 락한다.
2. `FAILED` 상태 및 비어 있지 않은 operator/reason을 요구한다.
3. event ID, operator, reason, 이전 재시도 횟수/오류 및 복구 시간을 포함하는 불변 `outbox_recovery_audits` 행을 추가한다.
4. 이벤트를 `READY`로 전환하고 재시도 횟수를 초기화하며 점유 메타데이터를 지우고 audit 행에 복구 provenance를 유지한다.

인증되지 않은 HTTP endpoint는 추가하지 않는다. service는 권한 있는 유지보수 도구를 위한 저장소 소유 작업 경계다. 운영 runbook은 감사되지 않은 직접 SQL 재대기열이 금지됨을 명시해야 한다.

## 실패 처리

- Kafka 확인 후 DB 완료 실패는 최소 한 번 중복 경계로 남는다. 이벤트는 나중에 재점유되고 consumer 멱등성이 중복을 흡수한다.
- 오래된 publisher token은 재할당된 `PROCESSING` 점유를 완료, 실패 또는 재대기열할 수 없다.
- 소진된 자동 재시도는 감사된 복구 service가 호출될 때까지 `FAILED`로 남는다.
- Analytics 효과 실패는 processed marker를 롤백하며 Kafka 전송 semantics를 통해 재시도된다.
- Consumer 검증 실패는 내구성 상태를 만들지 않으며 listener 실패로 보인다.

## 검증 설계

정적/unit 적용 범위:

- claim/retry/publish/requeue entity 전환 및 오래된 token 거부
- consumer envelope 검증
- recovery audit 필드 보존

MySQL integration 적용 범위:

- 두 publisher worker가 `SKIP LOCKED` 아래에서 서로 다른 행을 점유한다.
- 만료된 점유 복구 및 오래된 token 완료 거부
- 확인된 발행/상태 업데이트 실패는 재점유 가능한 중복 경계를 남긴다.
- 동일 group/event를 두 번 전송하면 marker 하나와 analytics record 하나가 생성된다.
- 서로 다른 group은 각각 record 하나를 생성한다.
- 강제된 analytics 영속성 실패는 marker를 롤백한다.
- 감사된 `FAILED -> READY` 복구 및 유효하지 않은 복구 거부

Kafka integration 적용 범위:

- 중복 전송은 analytics 효과를 중복하지 않는다.
- topic은 `coffee.order.paid`이고 producer key는 aggregate ID다.
- 전역 순서 단언은 하지 않는다.

모든 런타임 명령은 `NOT RUN`으로 남으며, 이는 저장소가 `VERIFIED` 명령 경로를 제공할 때까지다.

## 문서 업데이트

구현과 함께 canonical owner를 업데이트한다.

- `specs/003-order-payment/spec.md`: 외부 API 통합은 범위 밖으로 유지하면서 로컬 내구성 analytics consumer 효과를 포함한다.
- `docs/03-domain-model.md`: analytics 효과와 동일 트랜잭션 멱등성 불변식을 정의한다.
- `docs/07-data-and-api-contracts.md`: `order_paid_analytics`, recovery audit schema 및 전환 계약을 정의한다.
- `adr/ADR-002-transactional-outbox-kafka.md`: publish 직전 하나 점유와 감사된 FAILED 복구를 기록한다.
- `docs/09-quality-operations-and-rules.md`: 중복 효과 및 복구 검증 요구 사항을 추가한다.

## 비목표

- 외부 데이터 플랫폼 HTTP 통합
- 정확히 한 번 Kafka 전송
- 전역 Kafka 순서
- 인증되지 않은 복구 API
- audit record 없이 영구 실패 이벤트를 자동 재생하는 것
