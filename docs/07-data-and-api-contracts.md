# 07. 데이터 및 API 계약

## 데이터베이스 원칙

- MySQL은 주문, 결제, 포인트, Outbox 이벤트, 일별 메뉴 판매의 정합성 기준 저장소다.
- Redis는 정합성 기준 저장소가 아니다.
- Kafka는 정합성 기준 저장소가 아니다.
- 중요한 비즈니스 테이블에는 적절한 경우 생성/갱신 시각을 포함해야 한다.
- 금액과 유사한 값에는 정수 타입을 사용한다.
- 포인트 잔액은 음수가 될 수 없다.

## 엔터티 / 테이블

### users

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 사용자 ID |
| created_at | datetime | not null | 생성 시각 |
| updated_at | datetime | not null | 갱신 시각 |

### menus

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 메뉴 ID |
| name | varchar(100) | not null | 메뉴 이름 |
| price | bigint | not null | 가격 |
| status | varchar(20) | not null | `ON_SALE`, `SOLD_OUT`, `DELETED` |
| created_at | datetime | not null | 생성 시각 |
| updated_at | datetime | not null | 갱신 시각 |

### user_points

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 포인트 계정 ID |
| user_id | bigint | unique, not null | 사용자 ID |
| balance | bigint | not null | 현재 잔액 |
| version | bigint | not null | 버전/변경 추적 |
| created_at | datetime | not null | 생성 시각 |
| updated_at | datetime | not null | 갱신 시각 |

### point_histories

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 이력 ID |
| user_id | bigint | not null | 사용자 ID |
| type | varchar(20) | not null | `CHARGE`, `USE` |
| amount | bigint | not null | 변경 금액 |
| balance_after | bigint | not null | 변경 후 잔액 |
| reason | varchar(100) | not null | 변경 사유 |
| created_at | datetime | not null | 생성 시각 |

### orders

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 주문 ID |
| user_id | bigint | not null | 사용자 ID |
| menu_id | bigint | not null | 메뉴 ID |
| order_price | bigint | not null | 주문 시점 메뉴 가격 |
| status | varchar(20) | not null | `PAID`, `CANCELED` |
| ordered_at | datetime | not null | 주문 시각 |

### payments

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 결제 ID |
| order_id | bigint | unique, not null | 주문 ID |
| user_id | bigint | not null | 사용자 ID |
| amount | bigint | not null | 결제 금액 |
| status | varchar(20) | not null | `SUCCESS`, `FAILED` |
| paid_at | datetime | not null | 결제 시각 |

### outbox_events

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 이벤트 ID |
| aggregate_type | varchar(50) | not null | 예: `ORDER` |
| aggregate_id | bigint | not null | 주문 ID |
| event_type | varchar(100) | not null | 예: `ORDER_PAID` |
| payload | json | not null | Kafka payload |
| status | varchar(20) | not null | `READY`, `PROCESSING`, `PUBLISHED`, `FAILED` |
| retry_count | int | not null | 재시도 횟수 |
| claim_token | varchar(100) | nullable | 현재 Publisher claim을 위한 고유 token |
| claim_owner | varchar(100) | nullable | 관측성을 위한 Publisher 인스턴스 식별자 |
| claimed_at | datetime | nullable | claim 시작 시각 |
| claim_until | datetime | nullable | 미완료 claim을 복구할 수 있는 마감 시각 |
| last_error | varchar(1000) | nullable | 민감한 payload 데이터 없이 기록한 최근 발행 실패 요약 |
| created_at | datetime | not null | 생성 시각 |
| updated_at | datetime | not null | 마지막 상태 변경 시각 |
| published_at | datetime | nullable | 발행 시각 |

Outbox 상태 규칙:

- 주문 트랜잭션은 `READY`를 삽입하며 Kafka에 직접 발행하지 않는다.
- Publisher는 발행 시도 직전에 짧은 트랜잭션으로 최대 하나의 행을 claim하고, 새 `claim_token`과 `claim_until`을 사용해 `PROCESSING`으로 변경한 뒤 커밋하고 발행하며, 설정된 주기 크기만큼 반복한다.
- 현재 `claim_token`만 claim을 완료하거나 재시도할 수 있다. 이 규칙은 만료된 claim이 재배정된 뒤 오래된 worker가 행을 갱신하는 일을 막는다.
- `claim_until`이 지난 `PROCESSING` 행은 새 token으로 재claim할 수 있다.
- Kafka 확인은 일치하는 claim을 `PUBLISHED`로 변경한다. 재시도 가능한 실패는 `retry_count`를 증가시키고 행을 `READY`로 되돌린다. 재시도가 소진되면 감사 복구 service를 호출할 때까지 `FAILED`가 된다.
- claim 메타데이터 삭제는 `PROCESSING`에서 나가는 모든 전환의 일부다.

### daily_menu_sales

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK | 집계 ID |
| sales_date | date | unique with menu_id, not null | 판매 날짜 |
| menu_id | bigint | unique with sales_date, not null | 메뉴 ID |
| order_count | bigint | not null | 주문 횟수 |
| created_at | datetime | not null | 생성 시각 |
| updated_at | datetime | not null | 갱신 시각 |

## API 스타일

- REST 스타일 JSON API를 사용한다.
- `/api/v1` 접두사를 사용한다.
- 명확한 리소스 이름을 사용한다.
- 일관된 오류 응답 본문을 반환한다.

## 요청 / 응답 규칙

- 요청 본문은 JSON이어야 한다.
- 응답 본문은 JSON이어야 한다.
- 숫자 ID는 프로젝트 관례가 달리 정하지 않는 한 숫자로 표현한다.
- 금액/포인트 값은 정수 값이다.

## 오류 형식

```json
{
  "error": {
    "code": "INSUFFICIENT_POINT",
    "message": "포인트 잔액이 부족합니다.",
    "details": {}
  }
}
```

## 상태 코드 규칙

| 코드 | 상태 | 의미 |
|---|---:|---|
| INVALID_REQUEST | 400 | 잘못된 요청 형식 또는 값 |
| UNAUTHORIZED | 401 | 인증 필요 |
| FORBIDDEN | 403 | 권한 거부 |
| MENU_NOT_FOUND | 404 | 메뉴를 찾을 수 없음 |
| MENU_NOT_AVAILABLE | 409 | 메뉴를 이용할 수 없음 |
| INSUFFICIENT_POINT | 409 | 포인트 잔액 부족 |
| LOCK_TIMEOUT | 409 | 사용자 단위 락 획득 실패 |
| INTERNAL_ERROR | 500 | 예상하지 못한 서버 오류 |

## API 계약

세부 기능 API 계약은 다음 문서가 소유한다.

- `specs/001-menu-query/spec.md`
- `specs/002-point-charge/spec.md`
- `specs/003-order-payment/spec.md`
- `specs/004-popular-menu/spec.md`

## 사용자 식별자 규칙

이 과제에는 로그인이 포함되지 않는다.

`userId`는 포인트 계정 소유자를 식별하는 명시적 요청 값으로 사용한다. 이는 인증 메커니즘이 아니다. 로그인 구현 없이 포인트 충전과 주문/결제 API를 테스트할 수 있도록 한 과제 수준의 단순화다.

추후 인증을 추가하면 요청 `userId`를 인증된 principal로 대체하거나, 인증된 principal과 일치하는지 검증해야 한다.

## 데이터 보존 규칙

- 포인트 이력은 삭제하지 않아야 한다.
- 주문과 결제는 기본적으로 hard-delete하지 않아야 한다.
- Outbox 이벤트는 발행 성공 및 보존 기간 후 아카이브할 수 있다.

## 미해결 질문

- 미해결 질문: 정확한 outbox 보존 기간은 얼마인가?

## 인기 메뉴 캐시 계약

`GET /api/v1/menus/popular`은 `days=7&limit=3`만 허용한다. 포함 범위는 애플리케이션 clock의 현재 날짜와 그 이전 6일이다. 결과는 `orderCount DESC, menuId ASC`로 정렬한다.

MySQL `daily_menu_sales`가 정합성 기준이다. Redis 범위는 모든 날짜 marker의 generation, 영속 총계, 영속 member 수가 경량 MySQL 메타데이터 및 일별 ZSET의 cardinality/score 합계와 일치할 때만 사용할 수 있다. union 읽기 중에 marker generation이 변경되어서는 안 된다. 일별 데이터와 marker key는 14일 후 만료한다. 1분짜리 임시 union/rebuild key는 항상 정리한다. 불완전하거나 사용할 수 없거나 해석할 수 없는 캐시 데이터는 MySQL로 대체하고 빈 날짜를 포함하는 전체 범위를 재구성한다.

## 구현된 이벤트 소비 계약

### processed_events

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| consumer_group | varchar(100) | PK with event_id | Kafka consumer group |
| event_id | bigint | PK with consumer_group | 불변 Outbox 이벤트 ID |
| processed_at | datetime | not null | 최초 수락된 전달 시각 |

Kafka topic은 `coffee.order.paid`다. producer는 `aggregate_id`를 partition key로 사용하므로 순서는 aggregate key 하나로 제한되며 전역 순서를 가정하지 않는다. 메시지는 다음과 같다.

```json
{
  "eventId": 1,
  "eventType": "ORDER_PAID",
  "aggregateId": 100,
  "payload": { "userId": 1, "menuId": 10, "paymentAmount": 4500 }
}
```

각 consumer group은 `INSERT IGNORE`로 `(consumer_group, event_id)`를 삽입하고 동일 트랜잭션에서 `order_paid_analytics` 효과를 기록한다. 따라서 재전달은 두 번째 마커나 두 번째 효과를 만들지 않는다. 분석 쓰기 실패는 마커를 롤백한다.

### order_paid_analytics

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| consumer_group | varchar(100) | PK with event_id | Kafka consumer group |
| event_id | bigint | PK with consumer_group, positive | 불변 Outbox 이벤트 ID |
| aggregate_id | bigint | unique with consumer_group, positive | 주문 ID |
| user_id | bigint | positive, not null | 주문 사용자 ID |
| menu_id | bigint | positive, not null | 주문한 메뉴 ID |
| payment_amount | bigint | positive, not null | 결제 금액 |
| processed_at | datetime | not null | 내구성 있는 효과 시각 |

`(consumer_group, processed_at)` 인덱스는 consumer-group 소유 스캔을 지원한다.

### outbox_recovery_audits

| 열 | 타입 | 제약 조건 | 설명 |
|---|---|---|---|
| id | bigint | PK, auto increment | 감사 ID |
| event_id | bigint | FK to outbox_events, not null | 복구된 Outbox 이벤트 |
| operator_name | varchar(100) | nonblank, not null | 인가된 운영자 식별자 |
| reason | varchar(500) | nonblank, not null | 복구 사유 |
| previous_retry_count | int | nonnegative, not null | 복구 전 재시도 횟수 |
| previous_error | varchar(1000) | nullable | 복구 전 마지막 오류 |
| recovered_at | datetime | not null | 복구 시각 |

이 테이블에는 `(event_id, recovered_at)` 인덱스가 있다. `OutboxRecoveryService.requeueFailed`는 이벤트를 lock하고 불변 감사를 추가한 뒤 하나의 트랜잭션으로 재시도 횟수 0 및 삭제된 오류/claim 메타데이터와 함께 `FAILED -> READY`를 수행한다. 이벤트가 없거나 `FAILED`가 아닌 이벤트는 감사 없이 거부한다. 감사 없는 직접 SQL requeue는 금지한다.
