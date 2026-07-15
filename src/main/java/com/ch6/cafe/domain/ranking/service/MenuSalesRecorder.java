package com.ch6.cafe.domain.ranking.service;

import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.DailySalesMetadataProjection;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.time.LocalDate;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class MenuSalesRecorder {

    private static final Logger log = LoggerFactory.getLogger(MenuSalesRecorder.class);

    private final DailyMenuSalesRepository dailyRepository;
    private final RedisPopularMenuRepository redisRepository;
    private final RankingDateLock dateLock;

    public MenuSalesRecorder(
            DailyMenuSalesRepository dailyRepository,
            RedisPopularMenuRepository redisRepository,
            RankingDateLock dateLock) {
        this.dailyRepository = dailyRepository;
        this.redisRepository = redisRepository;
        this.dateLock = dateLock;
    }

    public void recordDurable(LocalDate date, long menuId) {
        dailyRepository.increment(date, menuId);
    }

    public void recordCache(LocalDate date, long menuId) {
        try {
            dateLock.execute(date, () -> {
                DailySalesMetadataProjection metadata = dailyRepository.summarizeBetween(date, date)
                        .stream()
                        .findFirst()
                        .orElse(null);
                if (metadata == null) {
                    return;
                }
                dailyRepository.findBySalesDateAndMenuId(date, menuId).ifPresent(sale ->
                        redisRepository.setAbsolute(
                                date,
                                menuId,
                                sale.getOrderCount(),
                                metadata.getTotalOrderCount(),
                                metadata.getMenuCount()));
            });
        } catch (RuntimeException exception) {
            log.warn(
                    "Redis ranking update failed; MySQL aggregate remains the recovery source. menuId={}",
                    menuId,
                    exception);
        }
    }
}
