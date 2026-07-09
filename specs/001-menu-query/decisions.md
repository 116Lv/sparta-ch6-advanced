# Decisions: Menu Query

## Decision Log

### 2026-07-09: 메뉴 조회는 DB 기준으로 단순 조회한다

## Context

메뉴 데이터는 변경 빈도가 낮아 캐싱 후보가 될 수 있다.

## Decision

초기 구현은 MySQL 조회를 기준으로 한다. Redis 캐시는 도입하지 않는다.

## Reason

과제의 핵심은 포인트, 주문, 인기 메뉴의 동시성과 정합성이다. 메뉴 목록은 단순 조회이며 데이터 규모도 작다고 가정한다. 캐시를 먼저 도입하면 캐시 무효화 전략까지 설명해야 하므로 초기 범위에서는 제외한다.

## Alternatives Considered

- Redis 캐시: 조회 성능은 좋아지지만 메뉴 변경 시 무효화 전략이 필요하다.
- Application local cache: 다수 서버 환경에서 서버별 캐시 불일치가 생길 수 있다.

## Consequences

- Positive: 구현이 단순하고 MySQL 기준 정합성이 명확하다.
- Negative: 메뉴 수와 트래픽이 매우 커지면 조회 부하가 증가할 수 있다.
- Follow-up: 메뉴 조회 트래픽이 커지면 Redis cache-aside를 검토한다.

