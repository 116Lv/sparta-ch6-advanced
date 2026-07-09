# Implementation Plan: Point Charge

## Summary

포인트 충전 요청은 Redisson lock 획득 후 MySQL 트랜잭션 안에서 잔액 증가와 이력 저장을 처리한다.

## Technical Approach

- API: `PointController`
- Application: `PointChargeService`
- Domain: `UserPoint`, `PointHistory`
- Persistence: `UserPointRepository`, `PointHistoryRepository`
- External: Redisson lock
- Test: integration test, concurrency test

## Files to Add

- `point/api/PointController.java`
- `point/api/PointChargeRequest.java`
- `point/api/PointChargeResponse.java`
- `point/application/PointChargeService.java`
- `point/domain/UserPoint.java`
- `point/domain/PointHistory.java`
- `point/domain/PointHistoryType.java`
- `point/infrastructure/UserPointRepository.java`
- `point/infrastructure/PointHistoryRepository.java`
- `common/lock/DistributedLockManager.java`

## Files to Modify

- schema 또는 migration
- global error handler

## Steps

1. 포인트 엔티티와 이력 엔티티를 정의한다.
2. 충전 금액 validation을 구현한다.
3. Redisson lock wrapper를 구현한다.
4. `PointChargeService`에서 lock과 transaction 경계를 구성한다.
5. 충전 API를 구현한다.
6. 정상/실패/동시성 테스트를 작성한다.

## Risks

- lock lease time이 너무 짧으면 트랜잭션 도중 lock이 해제될 수 있다.
- lock wait time이 너무 길면 API 응답 지연이 커질 수 있다.

## Rollback Plan

- 문제가 발생하면 lock 적용 전 단순 트랜잭션 방식으로 되돌릴 수 있으나, 다수 서버 동시성 보장은 약해진다.

