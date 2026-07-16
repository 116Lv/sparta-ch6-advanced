# Implementation Plan: Point Charge

## Summary

포인트 충전 요청은 Redisson lock 획득 후 MySQL 트랜잭션 안에서 잔액 증가와 이력 저장을 처리한다.

## Technical Approach

- Controller: `PointController`
- Service: `PointChargeService`
- Entity: `UserPoint`, `PointHistory`
- Repository: `UserPointRepository`, `PointHistoryRepository`
- External: Redisson lock
- Test: integration test, concurrency test

## Files to Add

- `src/main/java/com/ch6/cafe/domain/point/controller/PointController.java`
- `src/main/java/com/ch6/cafe/domain/point/dto/request/PointChargeRequest.java`
- `src/main/java/com/ch6/cafe/domain/point/dto/response/PointChargeResponse.java`
- `src/main/java/com/ch6/cafe/domain/point/service/PointChargeService.java`
- `src/main/java/com/ch6/cafe/domain/point/entity/UserPoint.java`
- `src/main/java/com/ch6/cafe/domain/point/entity/PointHistory.java`
- `src/main/java/com/ch6/cafe/domain/point/entity/PointHistoryType.java`
- `src/main/java/com/ch6/cafe/domain/point/repository/UserPointRepository.java`
- `src/main/java/com/ch6/cafe/domain/point/repository/PointHistoryRepository.java`
- `src/main/java/com/ch6/cafe/global/lock/DistributedLockManager.java`

## Files to Modify

- schema 또는 migration
- global error handler

## Steps

1. 포인트 엔티티와 이력 엔티티를 정의한다.
2. 충전 금액 validation을 구현한다.
3. Redisson lock wrapper를 구현한다.
4. `PointChargeService`에서 비즈니스 규칙, lock, transaction 경계를 구성한다.
5. 충전 API를 구현한다.
6. 정상/실패/동시성 테스트를 작성한다.

## Risks

- lock lease time이 너무 짧으면 트랜잭션 도중 lock이 해제될 수 있다.
- lock wait time이 너무 길면 API 응답 지연이 커질 수 있다.

## Rollback Plan

- 문제가 발생하면 검증된 MySQL 비관적 락 경로로 전환할 수 있다. 락 없이 단순 트랜잭션만 사용하는 방식으로 낮추지 않는다.

