package com.ch6.cafe.domain.ranking.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyCollection;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.core.DefaultTypedTuple;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.data.redis.core.ZSetOperations;

class RedisPopularMenuRepositoryTest {

    @Test
    void generationChangingAcrossUnionReadIsRejected() {
        StringRedisTemplate template = mock(StringRedisTemplate.class);
        @SuppressWarnings("unchecked")
        ValueOperations<String, String> values = mock(ValueOperations.class);
        @SuppressWarnings("unchecked")
        ZSetOperations<String, String> zset = mock(ZSetOperations.class);
        when(template.opsForValue()).thenReturn(values);
        when(template.opsForZSet()).thenReturn(zset);
        when(values.multiGet(anyCollection()))
                .thenReturn(List.of("generation-a|5|1"), List.of("generation-b|5|1"));
        when(template.hasKey(anyString())).thenReturn(true);
        when(zset.zCard(anyString())).thenReturn(1L);
        Set<ZSetOperations.TypedTuple<String>> data =
                Set.of(new DefaultTypedTuple<>("1", 5D));
        when(zset.rangeWithScores(anyString(), anyLong(), anyLong())).thenReturn(data);
        when(zset.reverseRangeWithScores(anyString(), anyLong(), anyLong())).thenReturn(data);

        LocalDate date = LocalDate.of(2026, 7, 15);
        assertThat(new RedisPopularMenuRepository(template).findComplete(
                date, 1, Map.of(date, new DailySalesMetadata(5L, 1L)))).isEmpty();
    }
}
