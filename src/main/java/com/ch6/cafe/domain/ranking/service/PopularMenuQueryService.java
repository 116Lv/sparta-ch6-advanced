package com.ch6.cafe.domain.ranking.service;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import com.ch6.cafe.domain.ranking.dto.response.PopularMenuResponse;
import com.ch6.cafe.domain.ranking.entity.PopularMenu;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.dao.DataAccessException;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class PopularMenuQueryService {

    private static final Logger log = LoggerFactory.getLogger(PopularMenuQueryService.class);
    private static final int MAX_DAYS = 30;
    private static final int MAX_LIMIT = 100;

    private final RedisPopularMenuRepository redisRepository;
    private final DailyMenuSalesRepository dailyRepository;
    private final MenuRepository menuRepository;
    private final RankingRebuildService rebuildService;

    public PopularMenuQueryService(
            RedisPopularMenuRepository redisRepository,
            DailyMenuSalesRepository dailyRepository,
            MenuRepository menuRepository,
            RankingRebuildService rebuildService) {
        this.redisRepository = redisRepository;
        this.dailyRepository = dailyRepository;
        this.menuRepository = menuRepository;
        this.rebuildService = rebuildService;
    }

    @Transactional(readOnly = true)
    public PopularMenuResponse getPopularMenus(int days, int limit) {
        validate(days, limit);
        LocalDate today = LocalDate.now();
        List<PopularMenu> ranking = loadRanking(today, days);
        List<PopularMenu> selected = ranking.stream().limit(limit).toList();
        Map<Long, Menu> menus = menuRepository.findAllById(
                        selected.stream().map(PopularMenu::menuId).toList())
                .stream()
                .collect(Collectors.toMap(Menu::getId, Function.identity()));

        List<PopularMenuResponse.MenuItem> items = selected.stream()
                .filter(item -> menus.containsKey(item.menuId()))
                .map(item -> {
                    Menu menu = menus.get(item.menuId());
                    return new PopularMenuResponse.MenuItem(
                            item.menuId(), menu.getName(), menu.getPrice(), item.orderCount());
                })
                .toList();
        return new PopularMenuResponse(days, items);
    }

    private List<PopularMenu> loadRanking(LocalDate today, int days) {
        try {
            List<PopularMenu> cached = redisRepository.find(today, days);
            if (!cached.isEmpty()) {
                return cached;
            }
        } catch (DataAccessException exception) {
            log.warn("Redis ranking read failed; serving MySQL aggregate.");
        }

        LocalDate from = today.minusDays(days - 1L);
        List<PopularMenu> durable = dailyRepository.aggregateBetween(from, today).stream()
                .map(row -> new PopularMenu(row.getMenuId(), row.getOrderCount()))
                .sorted(PopularMenu.ORDERING)
                .toList();
        try {
            rebuildService.rebuild(today, days);
        } catch (DataAccessException exception) {
            log.warn("Redis ranking rebuild failed; MySQL aggregate remains available.");
        }
        return durable;
    }

    private void validate(int days, int limit) {
        if (days < 1 || days > MAX_DAYS || limit < 1 || limit > MAX_LIMIT) {
            throw new IllegalArgumentException("days or limit is outside the allowed range.");
        }
    }
}
