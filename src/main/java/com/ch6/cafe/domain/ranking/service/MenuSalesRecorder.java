package com.ch6.cafe.domain.ranking.service;

import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import org.slf4j.Logger;
import org.springframework.dao.DataAccessException;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MenuSalesRecorder {

    private static final Logger log = LoggerFactory.getLogger(MenuSalesRecorder.class);

    private final DailyMenuSalesRepository dailyRepository;
    private final RedisPopularMenuRepository redisRepository;

    public MenuSalesRecorder(
            DailyMenuSalesRepository dailyRepository,
            RedisPopularMenuRepository redisRepository) {
        this.dailyRepository = dailyRepository;
        this.redisRepository = redisRepository;
    }

    public void recordDurable(LocalDate date, long menuId) {
        dailyRepository.increment(date, menuId);
    }

    public void recordCache(LocalDate date, long menuId) {
        try {
            redisRepository.increment(date, menuId);
        } catch (DataAccessException exception) {
            log.warn("Redis ranking update failed; MySQL aggregate remains the recovery source. menuId={}", menuId);
        }
    }
}
