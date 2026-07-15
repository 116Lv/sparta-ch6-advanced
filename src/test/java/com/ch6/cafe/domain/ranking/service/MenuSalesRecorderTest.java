package com.ch6.cafe.domain.ranking.service;

import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.ranking.entity.DailyMenuSale;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import java.util.Optional;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

class MenuSalesRecorderTest {

    private final DailyMenuSalesRepository dailyRepository = Mockito.mock(DailyMenuSalesRepository.class);
    private final RedisPopularMenuRepository redisRepository = Mockito.mock(RedisPopularMenuRepository.class);
    private final RankingDateLock dateLock = Mockito.mock(RankingDateLock.class);
    private final MenuSalesRecorder recorder;

    MenuSalesRecorderTest() {
        Mockito.doAnswer(invocation -> {
            invocation.<Runnable>getArgument(1).run();
            return null;
        }).when(dateLock).execute(Mockito.any(), Mockito.any());
        recorder = new MenuSalesRecorder(dailyRepository, redisRepository, dateLock);
    }

    @Test
    void cacheUpdateAssignsDurableAbsoluteCountInsteadOfIncrementing() {
        LocalDate date = LocalDate.of(2026, 7, 15);
        DailyMenuSale sale = Mockito.mock(DailyMenuSale.class);
        when(sale.getOrderCount()).thenReturn(12L);
        when(dailyRepository.findBySalesDateAndMenuId(date, 3L)).thenReturn(Optional.of(sale));

        recorder.recordCache(date, 3L);

        verify(redisRepository).setAbsolute(date, 3L, 12L);
        verify(dateLock).execute(Mockito.eq(date), Mockito.any());
    }

    @Test
    void missingDurableAggregateNeverInventsCacheState() {
        LocalDate date = LocalDate.of(2026, 7, 15);
        when(dailyRepository.findBySalesDateAndMenuId(date, 3L)).thenReturn(Optional.empty());

        recorder.recordCache(date, 3L);

        verify(redisRepository, never()).setAbsolute(date, 3L, 0L);
    }
}
