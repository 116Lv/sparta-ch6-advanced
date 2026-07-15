package com.ch6.cafe.domain.ranking.repository;

import com.ch6.cafe.domain.ranking.entity.PopularMenu;
import java.time.Duration;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import org.springframework.data.redis.core.DefaultTypedTuple;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.data.redis.core.script.DefaultRedisScript;
import org.springframework.stereotype.Repository;

@Repository
public class RedisPopularMenuRepository {

    private static final String KEY_PREFIX = "popular-menu:";
    private static final String COMPLETE_PREFIX = "popular-menu:complete:";
    private static final String TEMP_PREFIX = "popular-menu:tmp:";
    private static final Duration DAILY_TTL = Duration.ofDays(14);
    private static final Duration TEMP_TTL = Duration.ofMinutes(1);
    private static final DefaultRedisScript<Long> REPLACE_SCRIPT = new DefaultRedisScript<>("""
            if redis.call('EXISTS', KEYS[1]) == 1 then
                redis.call('DEL', KEYS[2])
                redis.call('RENAME', KEYS[1], KEYS[2])
                redis.call('EXPIRE', KEYS[2], ARGV[1])
            else
                redis.call('DEL', KEYS[2])
            end
            redis.call('SET', KEYS[3], '1', 'EX', ARGV[1])
            return 1
            """, Long.class);

    private final StringRedisTemplate redisTemplate;

    public RedisPopularMenuRepository(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public Optional<List<PopularMenu>> findComplete(LocalDate to, int days) {
        List<String> dailyKeys = new ArrayList<>();
        List<String> markerKeys = new ArrayList<>();
        for (int offset = 0; offset < days; offset++) {
            LocalDate date = to.minusDays(offset);
            dailyKeys.add(dailyKey(date));
            markerKeys.add(completeKey(date));
        }
        if (!allMarkersExist(markerKeys)) {
            return Optional.empty();
        }

        String unionKey = KEY_PREFIX + "union:" + UUID.randomUUID();
        try {
            redisTemplate.opsForZSet().unionAndStore(
                    dailyKeys.get(0), dailyKeys.subList(1, dailyKeys.size()), unionKey);
            redisTemplate.expire(unionKey, TEMP_TTL);
            Set<ZSetOperations.TypedTuple<String>> tuples =
                    redisTemplate.opsForZSet().reverseRangeWithScores(unionKey, 0, -1);
            if (!allMarkersExist(markerKeys)) {
                return Optional.empty();
            }
            if (tuples == null) {
                return Optional.of(List.of());
            }
            return Optional.of(tuples.stream()
                    .filter(tuple -> tuple.getValue() != null && tuple.getScore() != null)
                    .map(tuple -> new PopularMenu(
                            Long.parseLong(tuple.getValue()), tuple.getScore().longValue()))
                    .sorted(PopularMenu.ORDERING)
                    .toList());
        } finally {
            redisTemplate.delete(unionKey);
        }
    }

    public void setAbsolute(LocalDate date, long menuId, long durableCount) {
        if (durableCount <= 0) {
            throw new IllegalArgumentException("Durable ranking count must be positive.");
        }
        String key = dailyKey(date);
        redisTemplate.opsForZSet().add(key, Long.toString(menuId), durableCount);
        redisTemplate.expire(key, DAILY_TTL);
    }

    public void replaceDate(LocalDate date, Map<Long, Long> counts) {
        String tempKey = TEMP_PREFIX + date + ":" + UUID.randomUUID();
        try {
            Set<ZSetOperations.TypedTuple<String>> tuples = counts.entrySet().stream()
                    .map(entry -> new DefaultTypedTuple<>(
                            Long.toString(entry.getKey()), entry.getValue().doubleValue()))
                    .collect(Collectors.toSet());
            if (!tuples.isEmpty()) {
                redisTemplate.opsForZSet().add(tempKey, tuples);
                redisTemplate.expire(tempKey, TEMP_TTL);
            }
            redisTemplate.execute(
                    REPLACE_SCRIPT,
                    List.of(tempKey, dailyKey(date), completeKey(date)),
                    Long.toString(DAILY_TTL.toSeconds()));
        } finally {
            redisTemplate.delete(tempKey);
        }
    }

    private boolean allMarkersExist(List<String> markerKeys) {
        return markerKeys.stream().allMatch(key -> Boolean.TRUE.equals(redisTemplate.hasKey(key)));
    }

    private String dailyKey(LocalDate date) {
        return KEY_PREFIX + date;
    }

    private String completeKey(LocalDate date) {
        return COMPLETE_PREFIX + date;
    }
}
