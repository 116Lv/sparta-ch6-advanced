package com.ch6.cafe.global.lock;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.Test;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.springframework.data.redis.RedisConnectionFailureException;

class DistributedLockManagerTest {

    private final RedissonClient redissonClient = org.mockito.Mockito.mock(RedissonClient.class);
    private final RLock lock = org.mockito.Mockito.mock(RLock.class);
    private final DistributedLockManager manager = new DistributedLockManager(redissonClient, 200L);

    @Test
    void usesSharedPointKeyAndUnlocksOnlyWhenOwned() throws InterruptedException {
        when(redissonClient.getLock("point:user:7")).thenReturn(lock);
        when(lock.tryLock(200L, TimeUnit.MILLISECONDS)).thenReturn(true);
        when(lock.isHeldByCurrentThread()).thenReturn(true);
        assertThat(manager.withUserPointLock(7L, () -> "ok")).isEqualTo("ok");
        verify(lock).unlock();
    }

    @Test
    void doesNotBypassRedisFailure() {
        when(redissonClient.getLock("point:user:7")).thenThrow(new RedisConnectionFailureException("down"));
        assertThatThrownBy(() -> manager.withUserPointLock(7L, () -> "unsafe"))
                .isInstanceOf(LockUnavailableException.class);
    }
}
