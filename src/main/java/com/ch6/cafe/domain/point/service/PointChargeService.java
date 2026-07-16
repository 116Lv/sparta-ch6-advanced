package com.ch6.cafe.domain.point.service;

import com.ch6.cafe.domain.point.dto.response.PointChargeResponse;
import com.ch6.cafe.domain.point.entity.PointHistory;
import com.ch6.cafe.domain.point.entity.UserPoint;
import com.ch6.cafe.domain.point.repository.PointHistoryRepository;
import com.ch6.cafe.domain.point.repository.UserPointRepository;
import com.ch6.cafe.global.lock.DistributedLockManager;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class PointChargeService {

    private final DistributedLockManager lockManager;
    private final TransactionTemplate transactionTemplate;
    private final UserPointRepository userPointRepository;
    private final PointHistoryRepository pointHistoryRepository;

    public PointChargeService(
            DistributedLockManager lockManager,
            TransactionTemplate transactionTemplate,
            UserPointRepository userPointRepository,
            PointHistoryRepository pointHistoryRepository) {
        this.lockManager = lockManager;
        this.transactionTemplate = transactionTemplate;
        this.userPointRepository = userPointRepository;
        this.pointHistoryRepository = pointHistoryRepository;
    }

    public PointChargeResponse charge(long userId, long amount) {
        if (userId <= 0 || amount <= 0) {
            throw new IllegalArgumentException("User identifier and charge amount must be positive.");
        }
        return lockManager.withUserPointLock(userId, () -> transactionTemplate.execute(status -> {
            UserPoint point = userPointRepository.findByUserIdForUpdate(userId)
                    .orElseGet(() -> new UserPoint(userId, 0L));
            point.charge(amount);
            userPointRepository.save(point);
            pointHistoryRepository.save(PointHistory.charge(userId, amount, point.getBalance()));
            return new PointChargeResponse(userId, amount, point.getBalance());
        }));
    }
}
