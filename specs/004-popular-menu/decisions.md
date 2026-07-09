# Decisions: Popular Menu

## Decision Log

### 2026-07-09: 인기 메뉴는 Redis Sorted Set과 일별 집계 테이블을 함께 사용한다

## Context

인기 메뉴 조회는 최근 7일 주문 횟수 기준 TOP 3를 반환해야 한다. 주문 테이블을 매번 직접 집계하면 데이터가 늘어날수록 조회 비용이 커진다. 반대로 Redis만 사용하면 빠르지만 데이터 유실 시 정확성을 설명하기 어렵다.

## Decision

주문 성공 시 Redis Sorted Set과 MySQL `daily_menu_sales`를 함께 갱신한다. 조회는 Redis를 우선 사용하고, 복구 기준은 MySQL 일별 집계 테이블로 둔다.

## Reason

Redis Sorted Set은 랭킹 조회에 적합하고 빠르다. MySQL 일별 집계 테이블은 정확성 검증과 복구 기준으로 적합하다. 두 방식을 함께 사용하면 조회 성능과 데이터 복구 가능성을 모두 설명할 수 있다.

## Alternatives Considered

- 주문 테이블 직접 `GROUP BY`: 구현은 단순하지만 트래픽과 데이터가 늘면 조회 비용이 커진다.
- Redis Sorted Set만 사용: 조회는 빠르지만 Redis 장애나 유실 시 정확성 보장이 약하다.
- 일별 집계 테이블만 사용: 정확성은 좋지만 실시간 랭킹 조회 성능과 확장성 설명이 약하다.

## Consequences

- Positive: 빠른 인기 메뉴 조회와 복구 가능성을 함께 확보한다.
- Negative: 주문 성공 시 갱신해야 할 데이터가 늘어난다.
- Follow-up: Redis 갱신 실패 시 보정 배치를 추가할 수 있다.

