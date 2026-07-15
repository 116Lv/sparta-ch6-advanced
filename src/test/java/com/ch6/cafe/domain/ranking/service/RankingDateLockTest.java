package com.ch6.cafe.domain.ranking.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDate;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.Test;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;
import org.mockito.Mockito;

class RankingDateLockTest {

    @Test
    void serializesByDateAndReleasesOwnedLock() throws Exception {
        RedissonClient client = Mockito.mock(RedissonClient.class);
        RLock lock = Mockito.mock(RLock.class);
        when(client.getLock("ranking:date:2026-07-15")).thenReturn(lock);
        when(lock.tryLock(2, TimeUnit.SECONDS)).thenReturn(true);
        when(lock.isHeldByCurrentThread()).thenReturn(true);
        AtomicBoolean ran = new AtomicBoolean();

        new RankingDateLock(client).execute(LocalDate.of(2026, 7, 15), () -> ran.set(true));

        assertThat(ran).isTrue();
        verify(lock).unlock();
    }

    @Test
    void rejectsWorkWhenDateLockCannotBeAcquired() throws Exception {
        RedissonClient client = Mockito.mock(RedissonClient.class);
        RLock lock = Mockito.mock(RLock.class);
        when(client.getLock("ranking:date:2026-07-15")).thenReturn(lock);
        when(lock.tryLock(2, TimeUnit.SECONDS)).thenReturn(false);

        assertThatThrownBy(() -> new RankingDateLock(client).execute(
                LocalDate.of(2026, 7, 15), () -> {}))
                .isInstanceOf(IllegalStateException.class);
    }
}
