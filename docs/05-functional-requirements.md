# 05. Functional Requirements

## Feature Areas

### 1. Menu

사용자는 판매 중인 커피 메뉴 목록을 조회할 수 있다.

Included:

- 메뉴 ID, 이름, 가격 조회

Excluded:

- 메뉴 생성/수정/삭제
- 메뉴 옵션
- 재고 관리

### 2. Point

사용자는 포인트를 충전할 수 있다. 결제는 포인트로만 가능하다.

Included:

- 사용자 식별값 기반 포인트 충전
- 충전 이력 저장
- 동시성 제어

Excluded:

- 실제 PG 결제
- 충전 취소
- 포인트 만료

### 3. Order and Payment

사용자는 메뉴를 주문하고 포인트로 결제할 수 있다.

Included:

- 주문 생성
- 포인트 차감
- 결제 기록 저장
- Outbox 이벤트 저장
- Kafka 발행 준비

Excluded:

- 주문 취소
- 환불
- 배송/제조 상태 관리

### 4. Popular Menu

사용자는 최근 7일간 인기 있는 메뉴 TOP 3를 조회할 수 있다.

Included:

- Redis Sorted Set 기반 빠른 조회
- MySQL 일별 집계 테이블 기반 복구

Excluded:

- 개인화 추천
- 관리자 통계 화면

## Requirement List

| ID | Requirement | Priority | Spec |
|---|---|---:|---|
| FR-001 | 커피 메뉴 목록을 조회할 수 있다. | P0 | `specs/001-menu-query` |
| FR-002 | 사용자 식별값과 충전 금액으로 포인트를 충전할 수 있다. | P0 | `specs/002-point-charge` |
| FR-003 | 사용자 식별값과 메뉴 ID로 주문하고 포인트로 결제할 수 있다. | P0 | `specs/003-order-payment` |
| FR-004 | 주문 성공 내역을 데이터 수집 플랫폼으로 전송할 수 있도록 Outbox 이벤트를 저장한다. | P0 | `specs/003-order-payment` |
| FR-005 | 최근 7일간 인기 메뉴 3개를 조회할 수 있다. | P0 | `specs/004-popular-menu` |
| FR-006 | 인기 메뉴의 메뉴별 주문 횟수는 정확해야 한다. | P0 | `specs/004-popular-menu` |

## Priority Definition

### P0

과제 필수 요구사항이며 구현과 테스트가 필요하다.

### P1

핵심은 아니지만 설계 설명에 포함하면 좋은 요구사항이다.

### P2

추후 확장 후보이며 현재 구현 범위에서는 제외한다.

## Out of Scope

- 회원가입/로그인
- 인증/인가
- 관리자 페이지
- 실제 결제 연동
- 메뉴 관리 API
- 주문 취소/환불
- 프론트엔드 UI

## Open Questions

- Open Question: Kafka producer test만으로 데이터 수집 플랫폼 전송 검증을 충분히 보여줄 수 있는가, 아니면 Mock HTTP API도 함께 제공할 것인가?
