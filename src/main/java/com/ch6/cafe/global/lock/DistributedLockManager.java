package com.ch6.cafe.global.lock;

import java.util.concurrent.TimeUnit;
import java.util.function.Supplier;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class DistributedLockManager {

    private static final Logger log = LoggerFactory.getLogger(DistributedLockManager.class);
    private static final String POINT_LOCK_PREFIX = "point:user:";

    private final RedissonClient redissonClient;
    private final long waitTimeMillis;

    public DistributedLockManager(
            RedissonClient redissonClient,
            @Value("${lock.point.wait-time-millis:200}") long waitTimeMillis) {
        this.redissonClient = redissonClient;
        this.waitTimeMillis = waitTimeMillis;
    }

    public <T> T withUserPointLock(long userId, Supplier<T> action) {
        RLock lock;
        boolean acquired;
        try {
            lock = redissonClient.getLock(POINT_LOCK_PREFIX + userId);
            acquired = lock.tryLock(waitTimeMillis, TimeUnit.MILLISECONDS);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new LockTimeoutException();
        } catch (RuntimeException exception) {
            throw new LockUnavailableException(exception);
        }

        if (!acquired) {
            throw new LockTimeoutException();
        }

        try {
            return action.get();
        } finally {
            releaseIfOwned(lock, userId);
        }
    }

    private void releaseIfOwned(RLock lock, long userId) {
        try {
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        } catch (RuntimeException exception) {
            log.error("Failed to verify or release point lock for userId={}", userId, exception);
        }
    }
}
