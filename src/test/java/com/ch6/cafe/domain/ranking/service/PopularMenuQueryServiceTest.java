package com.ch6.cafe.domain.ranking.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import com.ch6.cafe.domain.ranking.dto.response.PopularMenuResponse;
import com.ch6.cafe.domain.ranking.entity.PopularMenu;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.DailySalesMetadata;
import com.ch6.cafe.domain.ranking.repository.MenuSalesAggregate;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.lang.reflect.Field;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;
import java.util.Optional;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

class PopularMenuQueryServiceTest {

    private final RedisPopularMenuRepository redisRepository = mock(RedisPopularMenuRepository.class);
    private final DailyMenuSalesRepository dailyRepository = mock(DailyMenuSalesRepository.class);
    private final MenuRepository menuRepository = mock(MenuRepository.class);
    private final RankingRebuildService rebuildService = mock(RankingRebuildService.class);
    private final Clock clock = Clock.fixed(
            Instant.parse("2026-07-15T16:30:00Z"), ZoneId.of("Asia/Seoul"));
    private PopularMenuQueryService service;

    @BeforeEach
    void setUp() {
        when(dailyRepository.summarizeBetween(any(), any())).thenReturn(List.of());
        service = new PopularMenuQueryService(
                redisRepository, dailyRepository, menuRepository, rebuildService, clock);
    }

    @Test
    void completeCacheHitUsesInjectedClockAndReturnsTopThreeWithTieOrder() {
        LocalDate today = LocalDate.of(2026, 7, 16);
        when(redisRepository.findComplete(today, 7, emptyMetadata(today))).thenReturn(Optional.of(List.of(
                new PopularMenu(2L, 12L), new PopularMenu(1L, 10L),
                new PopularMenu(3L, 10L), new PopularMenu(4L, 1L))));
        when(menuRepository.findAllById(List.of(2L, 1L, 3L))).thenReturn(List.of(
                menu(2L, "Latte"), menu(1L, "Americano"), menu(3L, "Mocha")));

        PopularMenuResponse response = service.getPopularMenus(7, 3);

        assertThat(response.periodDays()).isEqualTo(7);
        assertThat(response.menus()).extracting(PopularMenuResponse.MenuItem::menuId)
                .containsExactly(2L, 1L, 3L);
        verify(dailyRepository, never()).aggregateBetween(any(), any());
    }

    @Test
    void incompleteCacheUsesInclusiveSevenDayDurableWindowAndRebuildsFullRange() {
        LocalDate today = LocalDate.of(2026, 7, 16);
        when(redisRepository.findComplete(today, 7, emptyMetadata(today))).thenReturn(Optional.empty());
        when(dailyRepository.aggregateBetween(LocalDate.of(2026, 7, 10), today))
                .thenReturn(List.of(aggregate(7L, 4L)));
        when(menuRepository.findAllById(List.of(7L))).thenReturn(List.of(menu(7L, "Flat White")));

        PopularMenuResponse response = service.getPopularMenus(7, 3);

        assertThat(response.menus()).extracting(PopularMenuResponse.MenuItem::orderCount)
                .containsExactly(4L);
        verify(rebuildService).rebuild(today, 7);
    }

    @Test
    void missingCachedMenuFallsBackToDurableRankingAndRebuildsInsteadOfShortening() {
        LocalDate today = LocalDate.of(2026, 7, 16);
        when(redisRepository.findComplete(today, 7, emptyMetadata(today))).thenReturn(Optional.of(List.of(
                new PopularMenu(99L, 20L), new PopularMenu(1L, 10L))));
        when(menuRepository.findAllById(List.of(99L, 1L))).thenReturn(List.of(menu(1L, "Americano")));
        when(dailyRepository.aggregateBetween(LocalDate.of(2026, 7, 10), today))
                .thenReturn(List.of(aggregate(1L, 10L), aggregate(2L, 8L)));
        when(menuRepository.findAllById(List.of(1L, 2L)))
                .thenReturn(List.of(menu(1L, "Americano"), menu(2L, "Latte")));

        PopularMenuResponse response = service.getPopularMenus(7, 3);

        assertThat(response.menus()).extracting(PopularMenuResponse.MenuItem::menuId)
                .containsExactly(1L, 2L);
        verify(rebuildService).rebuild(today, 7);
    }

    @Test
    void redisFailureStillReturnsDurableTopThreeInCanonicalOrder() {
        LocalDate today = LocalDate.of(2026, 7, 16);
        when(redisRepository.findComplete(today, 7, emptyMetadata(today)))
                .thenThrow(new RuntimeException("redis unavailable"));
        when(dailyRepository.aggregateBetween(LocalDate.of(2026, 7, 10), today)).thenReturn(List.of(
                aggregate(4L, 9L), aggregate(2L, 11L), aggregate(1L, 9L), aggregate(3L, 8L)));
        when(menuRepository.findAllById(List.of(2L, 1L, 4L))).thenReturn(List.of(
                menu(1L, "A"), menu(2L, "B"), menu(4L, "D")));

        PopularMenuResponse response = service.getPopularMenus(7, 3);

        assertThat(response.menus()).extracting(PopularMenuResponse.MenuItem::menuId)
                .containsExactly(2L, 1L, 4L);
    }

    @Test
    void rejectsEveryNonCanonicalDaysOrLimitValue() {
        assertThatThrownBy(() -> service.getPopularMenus(6, 3)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.getPopularMenus(8, 3)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.getPopularMenus(7, 2)).isInstanceOf(IllegalArgumentException.class);
        assertThatThrownBy(() -> service.getPopularMenus(7, 4)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void completeEmptyCacheIsAHitAndDoesNotQueryDurableStorage() {
        LocalDate today = LocalDate.of(2026, 7, 16);
        when(redisRepository.findComplete(today, 7, emptyMetadata(today))).thenReturn(Optional.of(List.of()));

        PopularMenuResponse response = service.getPopularMenus(7, 3);

        assertThat(response.menus()).isEmpty();
        verify(dailyRepository, never()).aggregateBetween(any(), any());
    }

    private Menu menu(long id, String name) {
        Menu menu = new Menu(name, 4500L, MenuStatus.ON_SALE);
        try {
            Field field = Menu.class.getDeclaredField("id");
            field.setAccessible(true);
            field.set(menu, id);
            return menu;
        } catch (ReflectiveOperationException exception) {
            throw new AssertionError(exception);
        }
    }

    private MenuSalesAggregate aggregate(long menuId, long count) {
        return new MenuSalesAggregate() {
            @Override public Long getMenuId() { return menuId; }
            @Override public Long getOrderCount() { return count; }
        };
    }

    private java.util.Map<LocalDate, DailySalesMetadata> emptyMetadata(LocalDate to) {
        java.util.Map<LocalDate, DailySalesMetadata> result = new java.util.LinkedHashMap<>();
        for (int offset = 6; offset >= 0; offset--) {
            result.put(to.minusDays(offset), new DailySalesMetadata(0L, 0L));
        }
        return result;
    }
}
