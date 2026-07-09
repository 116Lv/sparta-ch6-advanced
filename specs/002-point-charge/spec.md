# Feature Spec: Point Charge

## Status

Ready

## Related Documents

- `README.md`
- `docs/05-functional-requirements.md`
- `docs/03-domain-model.md`
- `docs/09-quality-operations-and-rules.md`

## Background

결제는 포인트로만 가능하다. 사용자는 주문 전에 포인트를 충전할 수 있어야 하며, 충전 결과는 잔액과 이력으로 남아야 한다.

## Scope

### In Scope

- 사용자 식별값과 충전 금액을 입력받아 포인트 충전
- 충전 후 잔액 반환
- 포인트 충전 이력 저장
- 동일 사용자 포인트 변경 동시성 제어

### Out of Scope

- 실제 PG 결제 연동
- 충전 취소
- 포인트 만료
- 사용자 인증/인가

## Requirements

### R-001: 포인트 충전

Description:

사용자에게 요청 금액만큼 포인트를 충전한다.

Acceptance Criteria:

- 충전 금액은 0보다 커야 한다.
- 1원은 1P로 계산한다.
- 충전 후 `user_points.balance`가 증가한다.
- `point_histories`에 `CHARGE` 이력이 저장된다.
- 동일 사용자의 충전/주문 동시 요청에도 잔액이 정확해야 한다.

## API Contract

Method and path:

`POST /api/v1/users/{userId}/points/charge`

Request:

```json
{
  "amount": 10000
}
```

Response:

```json
{
  "userId": 1,
  "chargedAmount": 10000,
  "balance": 15000
}
```

Errors:

- `INVALID_REQUEST`: 충전 금액이 0 이하
- `LOCK_TIMEOUT`: 동일 사용자 포인트 변경 요청 처리 중
- `INTERNAL_ERROR`

## Data Changes

- `user_points.balance` 증가
- `point_histories`에 충전 이력 추가

## Consistency and Concurrency

포인트 충전은 주문/결제와 같은 `point:user:{userId}` Redisson lock을 사용한다. 같은 사용자의 충전과 주문이 동시에 실행되면 최종 잔액 계산이 꼬일 수 있으므로 사용자 단위로 직렬화한다.

## Test Cases

- 포인트 충전 성공
- 0 이하 금액 충전 실패
- 충전 이력 저장
- 동일 사용자 동시 충전 시 최종 잔액 정확성 검증
- 충전과 주문 동시 요청 시 잔액 불변식 검증

## Open Questions

- 없음
