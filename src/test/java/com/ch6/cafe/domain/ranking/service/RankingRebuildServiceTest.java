package com.ch6.cafe.domain.ranking.service;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.ranking.entity.DailyMenuSale;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.junit.jupiter.api.Test;
import org.mockito.Mockito;

class RankingRebuildServiceTest {

    @Test
    void rebuildReplacesEveryDateIncludingEmptyDates() {
        DailyMenuSalesRepository daily = Mockito.mock(DailyMenuSalesRepository.class);
        RedisPopularMenuRepository redis = Mockito.mock(RedisPopularMenuRepository.class);
        RankingDateLock dateLock = Mockito.mock(RankingDateLock.class);
        Mockito.doAnswer(invocation -> {
            invocation.<Runnable>getArgument(1).run();
            return null;
        }).when(dateLock).execute(Mockito.any(), Mockito.any());
        DailyMenuSale sale = Mockito.mock(DailyMenuSale.class);
        when(sale.getSalesDate()).thenReturn(LocalDate.of(2026, 7, 14));
        when(sale.getMenuId()).thenReturn(5L);
        when(sale.getOrderCount()).thenReturn(2L);
        when(daily.findAllBySalesDateBetween(LocalDate.of(2026, 7, 13), LocalDate.of(2026, 7, 13)))
                .thenReturn(List.of());
        when(daily.findAllBySalesDateBetween(LocalDate.of(2026, 7, 14), LocalDate.of(2026, 7, 14)))
                .thenReturn(List.of(sale));
        when(daily.findAllBySalesDateBetween(LocalDate.of(2026, 7, 15), LocalDate.of(2026, 7, 15)))
                .thenReturn(List.of());

        new RankingRebuildService(daily, redis, dateLock).rebuild(LocalDate.of(2026, 7, 15), 3);

        verify(redis).replaceDate(LocalDate.of(2026, 7, 13), Map.of());
        verify(redis).replaceDate(LocalDate.of(2026, 7, 14), Map.of(5L, 2L));
        verify(redis).replaceDate(LocalDate.of(2026, 7, 15), Map.of());
    }
}
