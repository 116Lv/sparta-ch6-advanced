package com.ch6.cafe.domain.ranking.service;

import static java.util.concurrent.TimeUnit.SECONDS;
import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.ranking.entity.DailyMenuSale;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.DailySalesMetadataProjection;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;
import java.util.concurrent.locks.ReentrantLock;
import org.junit.jupiter.api.Test;
import org.redisson.api.RLock;
import org.redisson.api.RedissonClient;

class RankingCacheInterleavingTest {

    @Test
    void rebuildFirstThenAbsoluteUpdateEndsAtDurableCount() throws Exception {
        try (Harness harness = new Harness()) {
            harness.durable.set(5L);
            CountDownLatch rebuildInsideLock = new CountDownLatch(1);
            CountDownLatch releaseRebuild = new CountDownLatch(1);
            harness.beforeReplace.set(() -> await(rebuildInsideLock, releaseRebuild));

            Future<?> rebuild = harness.executor.submit(() -> harness.rebuild.rebuild(harness.date, 1));
            assertThat(rebuildInsideLock.await(2, SECONDS)).isTrue();
            harness.durable.set(6L);
            Future<?> update = harness.executor.submit(() -> harness.recorder.recordCache(harness.date, 1L));
            releaseRebuild.countDown();

            rebuild.get(2, SECONDS);
            update.get(2, SECONDS);
            assertThat(harness.cached).hasValue(6L);
        }
    }

    @Test
    void absoluteUpdateFirstThenRebuildReadsCurrentDurableCount() throws Exception {
        try (Harness harness = new Harness()) {
            harness.durable.set(6L);
            CountDownLatch updateInsideLock = new CountDownLatch(1);
            CountDownLatch releaseUpdate = new CountDownLatch(1);
            harness.beforeAbsolute.set(() -> await(updateInsideLock, releaseUpdate));

            Future<?> update = harness.executor.submit(() -> harness.recorder.recordCache(harness.date, 1L));
            assertThat(updateInsideLock.await(2, SECONDS)).isTrue();
            Future<?> rebuild = harness.executor.submit(() -> harness.rebuild.rebuild(harness.date, 1));
            releaseUpdate.countDown();

            update.get(2, SECONDS);
            rebuild.get(2, SECONDS);
            assertThat(harness.cached).hasValue(6L);
        }
    }

    private static void await(CountDownLatch entered, CountDownLatch release) {
        entered.countDown();
        try {
            if (!release.await(2, SECONDS)) {
                throw new AssertionError("Timed out waiting to release deterministic interleaving.");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new AssertionError(exception);
        }
    }

    private static final class Harness implements AutoCloseable {
        private final LocalDate date = LocalDate.of(2026, 7, 15);
        private final AtomicLong durable = new AtomicLong();
        private final AtomicLong cached = new AtomicLong();
        private final AtomicReference<Runnable> beforeReplace = new AtomicReference<>(() -> {});
        private final AtomicReference<Runnable> beforeAbsolute = new AtomicReference<>(() -> {});
        private final ExecutorService executor = Executors.newFixedThreadPool(2);
        private final MenuSalesRecorder recorder;
        private final RankingRebuildService rebuild;

        private Harness() throws InterruptedException {
            ReentrantLock javaLock = new ReentrantLock();
            RLock redissonLock = mock(RLock.class);
            when(redissonLock.tryLock(anyLong(), any())).thenAnswer(invocation ->
                    javaLock.tryLock(invocation.getArgument(0), invocation.getArgument(1)));
            when(redissonLock.isHeldByCurrentThread()).thenAnswer(ignored -> javaLock.isHeldByCurrentThread());
            doAnswer(ignored -> {
                javaLock.unlock();
                return null;
            }).when(redissonLock).unlock();
            RedissonClient redisson = mock(RedissonClient.class);
            when(redisson.getLock("ranking:date:" + date)).thenReturn(redissonLock);
            RankingDateLock dateLock = new RankingDateLock(redisson);

            DailyMenuSalesRepository daily = mock(DailyMenuSalesRepository.class);
            DailyMenuSale sale = mock(DailyMenuSale.class);
            when(sale.getSalesDate()).thenReturn(date);
            when(sale.getMenuId()).thenReturn(1L);
            when(sale.getOrderCount()).thenAnswer(ignored -> durable.get());
            when(daily.findAllBySalesDateBetween(date, date)).thenReturn(List.of(sale));
            when(daily.findBySalesDateAndMenuId(date, 1L)).thenReturn(Optional.of(sale));
            DailySalesMetadataProjection metadata = mock(DailySalesMetadataProjection.class);
            when(metadata.getSalesDate()).thenReturn(date);
            when(metadata.getTotalOrderCount()).thenAnswer(ignored -> durable.get());
            when(metadata.getMenuCount()).thenReturn(1L);
            when(daily.summarizeBetween(date, date)).thenReturn(List.of(metadata));

            RedisPopularMenuRepository redis = mock(RedisPopularMenuRepository.class);
            doAnswer(invocation -> {
                beforeReplace.get().run();
                Map<Long, Long> counts = invocation.getArgument(1);
                cached.set(counts.getOrDefault(1L, 0L));
                return null;
            }).when(redis).replaceDate(any(), any());
            doAnswer(invocation -> {
                beforeAbsolute.get().run();
                cached.set(invocation.getArgument(2));
                return null;
            }).when(redis).setAbsolute(any(), anyLong(), anyLong(), anyLong(), anyLong());

            recorder = new MenuSalesRecorder(daily, redis, dateLock);
            rebuild = new RankingRebuildService(daily, redis, dateLock);
        }

        @Override
        public void close() {
            executor.shutdownNow();
        }
    }
}
