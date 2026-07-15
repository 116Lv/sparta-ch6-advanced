package com.ch6.cafe.domain.ranking.service;

import java.time.LocalDate;
import java.util.concurrent.TimeUnit;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.stereotype.Component;

@Component
public class RankingDateLock {

    private static final String LOCK_PREFIX = "ranking:date:";
    private static final long WAIT_SECONDS = 2L;

    private final RedissonClient redissonClient;

    public RankingDateLock(RedissonClient redissonClient) {
        this.redissonClient = redissonClient;
    }

    public void execute(LocalDate date, Runnable action) {
        RLock lock = redissonClient.getLock(LOCK_PREFIX + date);
        boolean acquired;
        try {
            acquired = lock.tryLock(WAIT_SECONDS, TimeUnit.SECONDS);
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("Interrupted while acquiring ranking date lock.", exception);
        }
        if (!acquired) {
            throw new IllegalStateException("Ranking date lock acquisition timed out.");
        }
        try {
            action.run();
        } finally {
            if (lock.isHeldByCurrentThread()) {
                lock.unlock();
            }
        }
    }
}
