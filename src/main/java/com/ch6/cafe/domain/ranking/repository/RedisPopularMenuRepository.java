package com.ch6.cafe.domain.ranking.repository;

import com.ch6.cafe.domain.ranking.entity.DailyMenuSale;
import com.ch6.cafe.domain.ranking.entity.PopularMenu;
import java.time.Duration;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.springframework.data.redis.core.DefaultTypedTuple;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.stereotype.Repository;

@Repository
public class RedisPopularMenuRepository {

    private static final String KEY_PREFIX = "popular-menu:";
    private static final Duration DAILY_TTL = Duration.ofDays(14);
    private static final Duration UNION_TTL = Duration.ofMinutes(1);

    private final StringRedisTemplate redisTemplate;

    public RedisPopularMenuRepository(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public void increment(LocalDate date, long menuId) {
        String key = dailyKey(date);
        redisTemplate.opsForZSet().incrementScore(key, Long.toString(menuId), 1D);
        redisTemplate.expire(key, DAILY_TTL);
    }

    public List<PopularMenu> find(LocalDate to, int days) {
        List<String> keys = new ArrayList<>();
        for (int offset = 0; offset < days; offset++) {
            keys.add(dailyKey(to.minusDays(offset)));
        }

        boolean temporaryUnion = keys.size() > 1;
        String unionKey = KEY_PREFIX + "union:" + UUID.randomUUID();
        try {
            String readKey = keys.get(0);
            if (temporaryUnion) {
                redisTemplate.opsForZSet().unionAndStore(keys.get(0), keys.subList(1, keys.size()), unionKey);
                redisTemplate.expire(unionKey, UNION_TTL);
                readKey = unionKey;
            }
            Set<ZSetOperations.TypedTuple<String>> tuples =
                    redisTemplate.opsForZSet().reverseRangeWithScores(readKey, 0, -1);
            if (tuples == null) {
                return List.of();
            }
            return tuples.stream()
                    .filter(tuple -> tuple.getValue() != null && tuple.getScore() != null)
                    .map(tuple -> new PopularMenu(Long.parseLong(tuple.getValue()), tuple.getScore().longValue()))
                    .sorted(PopularMenu.ORDERING)
                    .toList();
        } finally {
            if (temporaryUnion) {
                redisTemplate.delete(unionKey);
            }
        }
    }

    public void rebuild(List<DailyMenuSale> sales) {
        Map<LocalDate, Map<Long, Double>> byDate = new HashMap<>();
        for (DailyMenuSale sale : sales) {
            LocalDate date = readDate(sale);
            long menuId = readMenuId(sale);
            double count = readOrderCount(sale);
            byDate.computeIfAbsent(date, ignored -> new HashMap<>()).put(menuId, count);
        }
        byDate.forEach((date, values) -> replace(date, values));
    }

    private void replace(LocalDate date, Map<Long, Double> values) {
        String key = dailyKey(date);
        redisTemplate.delete(key);
        Set<ZSetOperations.TypedTuple<String>> tuples = values.entrySet().stream()
                .map(entry -> new DefaultTypedTuple<>(Long.toString(entry.getKey()), entry.getValue()))
                .collect(java.util.stream.Collectors.toSet());
        if (!tuples.isEmpty()) {
            redisTemplate.opsForZSet().add(key, tuples);
            redisTemplate.expire(key, DAILY_TTL);
        }
    }

    private LocalDate readDate(DailyMenuSale sale) {
        return EntityAccess.salesDate(sale);
    }

    private long readMenuId(DailyMenuSale sale) {
        return EntityAccess.menuId(sale);
    }

    private long readOrderCount(DailyMenuSale sale) {
        return EntityAccess.orderCount(sale);
    }

    private String dailyKey(LocalDate date) {
        return KEY_PREFIX + date;
    }

    private static final class EntityAccess {
        private static LocalDate salesDate(DailyMenuSale sale) {
            return sale.getSalesDate();
        }

        private static long menuId(DailyMenuSale sale) {
            return sale.getMenuId();
        }

        private static long orderCount(DailyMenuSale sale) {
            return sale.getOrderCount();
        }
    }
}
