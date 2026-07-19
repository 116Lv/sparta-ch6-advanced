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
    // Publish the live ZSET (or delete it for an empty date) and its completeness marker in one
    // Lua execution so readers cannot accept data from a different generation than the marker.
    private static final DefaultRedisScript<Long> REPLACE_SCRIPT = new DefaultRedisScript<>("""
            redis.call('DEL', KEYS[1])
            for index = 4, #ARGV, 2 do
                redis.call('ZADD', KEYS[1], ARGV[index], ARGV[index + 1])
            end
            if redis.call('EXISTS', KEYS[1]) == 1 then
                redis.call('EXPIRE', KEYS[1], ARGV[2])
                redis.call('RENAME', KEYS[1], KEYS[2])
                redis.call('EXPIRE', KEYS[2], ARGV[1])
            else
                redis.call('DEL', KEYS[2])
            end
            redis.call('SET', KEYS[3], ARGV[3], 'EX', ARGV[1])
            return 1
            """, Long.class);
    private static final DefaultRedisScript<Long> ABSOLUTE_UPDATE_SCRIPT = new DefaultRedisScript<>("""
            redis.call('ZADD', KEYS[1], ARGV[1], ARGV[2])
            redis.call('EXPIRE', KEYS[1], ARGV[3])
            redis.call('SET', KEYS[2], ARGV[4], 'EX', ARGV[3])
            return 1
            """, Long.class);

    private final StringRedisTemplate redisTemplate;

    public RedisPopularMenuRepository(StringRedisTemplate redisTemplate) {
        this.redisTemplate = redisTemplate;
    }

    public Optional<List<PopularMenu>> findComplete(
            LocalDate to, int days, Map<LocalDate, DailySalesMetadata> expected) {
        List<String> dailyKeys = new ArrayList<>();
        List<String> markerKeys = new ArrayList<>();
        List<LocalDate> dates = new ArrayList<>();
        for (int offset = 0; offset < days; offset++) {
            LocalDate date = to.minusDays(offset);
            dates.add(date);
            dailyKeys.add(dailyKey(date));
            markerKeys.add(completeKey(date));
        }
        List<String> firstMarkers = redisTemplate.opsForValue().multiGet(markerKeys);
        if (!validSnapshot(dates, dailyKeys, firstMarkers, expected)) {
            return Optional.empty();
        }

        String unionKey = KEY_PREFIX + "union:" + UUID.randomUUID();
        try {
            redisTemplate.opsForZSet().unionAndStore(
                    dailyKeys.get(0), dailyKeys.subList(1, dailyKeys.size()), unionKey);
            redisTemplate.expire(unionKey, TEMP_TTL);
            Set<ZSetOperations.TypedTuple<String>> tuples =
                    redisTemplate.opsForZSet().reverseRangeWithScores(unionKey, 0, -1);
            // If the second marker read differs from the first, the union may span generations;
            // reject it so the caller falls back to durable MySQL data.
            List<String> secondMarkers = redisTemplate.opsForValue().multiGet(markerKeys);
            if (!firstMarkers.equals(secondMarkers)
                    || !validSnapshot(dates, dailyKeys, secondMarkers, expected)) {
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

    public void setAbsolute(
            LocalDate date,
            long menuId,
            long durableCount,
            long durableTotalCount,
            long durableMemberCount) {
        if (durableCount <= 0 || durableTotalCount <= 0 || durableMemberCount <= 0) {
            throw new IllegalArgumentException("Durable ranking metadata must be positive.");
        }
        redisTemplate.execute(
                ABSOLUTE_UPDATE_SCRIPT,
                List.of(dailyKey(date), completeKey(date)),
                Long.toString(durableCount),
                Long.toString(menuId),
                Long.toString(DAILY_TTL.toSeconds()),
                markerValue(durableTotalCount, durableMemberCount));
    }

    public void replaceDate(LocalDate date, Map<Long, Long> counts) {
        String tempKey = TEMP_PREFIX + date + ":" + UUID.randomUUID();
        try {
            List<String> arguments = new ArrayList<>();
            arguments.add(Long.toString(DAILY_TTL.toSeconds()));
            arguments.add(Long.toString(TEMP_TTL.toSeconds()));
            arguments.add(markerValue(
                    counts.values().stream().mapToLong(Long::longValue).sum(),
                    counts.size()));
            for (Map.Entry<Long, Long> entry : counts.entrySet()) {
                arguments.add(Long.toString(entry.getValue()));
                arguments.add(Long.toString(entry.getKey()));
            }
            redisTemplate.execute(
                    REPLACE_SCRIPT,
                    List.of(tempKey, dailyKey(date), completeKey(date)),
                    arguments.toArray());
        } finally {
            redisTemplate.delete(tempKey);
        }
    }

    private boolean validSnapshot(
            List<LocalDate> dates,
            List<String> dailyKeys,
            List<String> encodedMarkers,
            Map<LocalDate, DailySalesMetadata> expected) {
        if (encodedMarkers == null || encodedMarkers.size() != dates.size()) {
            return false;
        }
        for (int index = 0; index < dates.size(); index++) {
            Marker marker = parseMarker(encodedMarkers.get(index));
            DailySalesMetadata durable = expected.get(dates.get(index));
            if (marker == null || durable == null
                    || marker.totalOrderCount() != durable.totalOrderCount()
                    || marker.menuCount() != durable.menuCount()
                    || !validDailyData(dailyKeys.get(index), durable)) {
                return false;
            }
        }
        return true;
    }

    private boolean validDailyData(String key, DailySalesMetadata expected) {
        Boolean exists = redisTemplate.hasKey(key);
        if (expected.menuCount() == 0) {
            return !Boolean.TRUE.equals(exists) && expected.totalOrderCount() == 0;
        }
        if (!Boolean.TRUE.equals(exists)) {
            return false;
        }
        Long size = redisTemplate.opsForZSet().zCard(key);
        Set<ZSetOperations.TypedTuple<String>> tuples =
                redisTemplate.opsForZSet().rangeWithScores(key, 0, -1);
        if (size == null || size != expected.menuCount() || tuples == null || tuples.size() != size) {
            return false;
        }
        long total = 0L;
        for (ZSetOperations.TypedTuple<String> tuple : tuples) {
            if (tuple.getValue() == null || tuple.getScore() == null
                    || tuple.getScore() <= 0 || tuple.getScore() != Math.rint(tuple.getScore())) {
                return false;
            }
            total = Math.addExact(total, tuple.getScore().longValue());
        }
        return total == expected.totalOrderCount();
    }

    private Marker parseMarker(String encoded) {
        if (encoded == null) {
            return null;
        }
        String[] parts = encoded.split("\\|", -1);
        if (parts.length != 3 || parts[0].isBlank()) {
            return null;
        }
        try {
            return new Marker(parts[0], Long.parseLong(parts[1]), Long.parseLong(parts[2]));
        } catch (NumberFormatException exception) {
            return null;
        }
    }

    private String markerValue(long totalOrderCount, long menuCount) {
        return UUID.randomUUID() + "|" + totalOrderCount + "|" + menuCount;
    }

    private String dailyKey(LocalDate date) {
        return KEY_PREFIX + date;
    }

    private String completeKey(LocalDate date) {
        return COMPLETE_PREFIX + date;
    }

    private record Marker(String generation, long totalOrderCount, long menuCount) {
    }
}
