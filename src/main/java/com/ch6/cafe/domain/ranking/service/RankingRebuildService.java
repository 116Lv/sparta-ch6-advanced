package com.ch6.cafe.domain.ranking.service;

import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import org.springframework.stereotype.Service;

@Service
public class RankingRebuildService {

    private final DailyMenuSalesRepository dailyRepository;
    private final RedisPopularMenuRepository redisRepository;

    public RankingRebuildService(
            DailyMenuSalesRepository dailyRepository,
            RedisPopularMenuRepository redisRepository) {
        this.dailyRepository = dailyRepository;
        this.redisRepository = redisRepository;
    }

    public void rebuild(LocalDate to, int days) {
        LocalDate from = to.minusDays(days - 1L);
        redisRepository.rebuild(dailyRepository.findAllBySalesDateBetween(from, to));
    }
}
