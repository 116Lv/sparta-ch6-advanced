package com.ch6.cafe.domain.ranking.service;

import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import java.util.Map;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;

@Service
public class RankingRebuildService {

    private final DailyMenuSalesRepository dailyRepository;
    private final RedisPopularMenuRepository redisRepository;
    private final RankingDateLock dateLock;

    public RankingRebuildService(
            DailyMenuSalesRepository dailyRepository,
            RedisPopularMenuRepository redisRepository,
            RankingDateLock dateLock) {
        this.dailyRepository = dailyRepository;
        this.redisRepository = redisRepository;
        this.dateLock = dateLock;
    }

    public void rebuild(LocalDate to, int days) {
        LocalDate from = to.minusDays(days - 1L);
        for (LocalDate date = from; !date.isAfter(to); date = date.plusDays(1)) {
            LocalDate rebuildDate = date;
            dateLock.execute(rebuildDate, () -> {
                Map<Long, Long> counts = dailyRepository
                        .findAllBySalesDateBetween(rebuildDate, rebuildDate)
                        .stream()
                        .collect(Collectors.toMap(
                                sale -> sale.getMenuId(), sale -> sale.getOrderCount()));
                redisRepository.replaceDate(rebuildDate, counts);
            });
        }
    }
}
