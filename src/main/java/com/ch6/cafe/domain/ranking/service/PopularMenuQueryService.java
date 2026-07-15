package com.ch6.cafe.domain.ranking.service;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import com.ch6.cafe.domain.ranking.dto.response.PopularMenuResponse;
import com.ch6.cafe.domain.ranking.entity.PopularMenu;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.Clock;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PopularMenuQueryService {

    private static final Logger log = LoggerFactory.getLogger(PopularMenuQueryService.class);
    private static final int REQUIRED_DAYS = 7;
    private static final int REQUIRED_LIMIT = 3;

    private final RedisPopularMenuRepository redisRepository;
    private final DailyMenuSalesRepository dailyRepository;
    private final MenuRepository menuRepository;
    private final RankingRebuildService rebuildService;
    private final Clock clock;

    public PopularMenuQueryService(
            RedisPopularMenuRepository redisRepository,
            DailyMenuSalesRepository dailyRepository,
            MenuRepository menuRepository,
            RankingRebuildService rebuildService,
            Clock clock) {
        this.redisRepository = redisRepository;
        this.dailyRepository = dailyRepository;
        this.menuRepository = menuRepository;
        this.rebuildService = rebuildService;
        this.clock = clock;
    }

    @Transactional(readOnly = true)
    public PopularMenuResponse getPopularMenus(int days, int limit) {
        validate(days, limit);
        LocalDate today = LocalDate.now(clock);
        Optional<List<PopularMenu>> cached = loadCached(today, days);
        if (cached.isPresent()) {
            List<PopularMenu> selected = cached.orElseThrow().stream().limit(limit).toList();
            Optional<List<PopularMenuResponse.MenuItem>> cachedItems = hydrateComplete(selected);
            if (cachedItems.isPresent()) {
                return new PopularMenuResponse(days, cachedItems.orElseThrow());
            }
            log.warn("Redis ranking referenced a missing menu; serving MySQL aggregate.");
        }

        List<PopularMenu> selected = loadDurable(today, days).stream().limit(limit).toList();
        List<PopularMenuResponse.MenuItem> items = hydrate(selected);
        try {
            rebuildService.rebuild(today, days);
        } catch (RuntimeException exception) {
            log.warn("Redis ranking rebuild failed; MySQL aggregate remains available.");
        }
        return new PopularMenuResponse(days, items);
    }

    private Optional<List<PopularMenuResponse.MenuItem>> hydrateComplete(List<PopularMenu> ranking) {
        List<PopularMenuResponse.MenuItem> items = hydrate(ranking);
        return items.size() == ranking.size() ? Optional.of(items) : Optional.empty();
    }

    private List<PopularMenuResponse.MenuItem> hydrate(List<PopularMenu> selected) {
        Map<Long, Menu> menus = menuRepository.findAllById(
                        selected.stream().map(PopularMenu::menuId).toList())
                .stream()
                .collect(Collectors.toMap(Menu::getId, Function.identity()));

        return selected.stream()
                .filter(item -> menus.containsKey(item.menuId()))
                .map(item -> {
                    Menu menu = menus.get(item.menuId());
                    return new PopularMenuResponse.MenuItem(
                            item.menuId(), menu.getName(), menu.getPrice(), item.orderCount());
                })
                .toList();
    }

    private Optional<List<PopularMenu>> loadCached(LocalDate today, int days) {
        try {
            return redisRepository.findComplete(today, days);
        } catch (RuntimeException exception) {
            log.warn("Redis ranking read failed; serving MySQL aggregate.");
            return Optional.empty();
        }
    }

    private List<PopularMenu> loadDurable(LocalDate today, int days) {
        LocalDate from = today.minusDays(days - 1L);
        return dailyRepository.aggregateBetween(from, today).stream()
                .map(row -> new PopularMenu(row.getMenuId(), row.getOrderCount()))
                .sorted(PopularMenu.ORDERING)
                .toList();
    }

    private void validate(int days, int limit) {
        if (days != REQUIRED_DAYS || limit != REQUIRED_LIMIT) {
            throw new IllegalArgumentException("Only days=7 and limit=3 are supported.");
        }
    }
}
