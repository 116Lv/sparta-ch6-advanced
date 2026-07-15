package com.ch6.cafe.domain.ranking.repository;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.anyCollection;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import java.time.LocalDate;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.data.redis.core.DefaultTypedTuple;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.data.redis.core.ValueOperations;
import org.springframework.data.redis.core.ZSetOperations;
import org.springframework.data.redis.core.script.RedisScript;

class RedisPopularMenuRepositoryTest {

    @Test
    void replacementPopulatesAndExpiresTemporaryKeyInsideAtomicScript() {
        StringRedisTemplate template = mock(StringRedisTemplate.class);
        @SuppressWarnings("unchecked")
        ArgumentCaptor<RedisScript<Long>> scriptCaptor = ArgumentCaptor.forClass(RedisScript.class);
        @SuppressWarnings({"unchecked", "rawtypes"})
        ArgumentCaptor<List<String>> keysCaptor = (ArgumentCaptor) ArgumentCaptor.forClass(List.class);
        ArgumentCaptor<Object[]> argumentsCaptor = ArgumentCaptor.forClass(Object[].class);
        Map<Long, Long> counts = new LinkedHashMap<>();
        counts.put(11L, 5L);
        counts.put(22L, 3L);

        new RedisPopularMenuRepository(template)
                .replaceDate(LocalDate.of(2026, 7, 15), counts);

        verify(template).execute(
                scriptCaptor.capture(),
                keysCaptor.capture(),
                argumentsCaptor.capture());
        verify(template, never()).opsForZSet();

        assertThat(keysCaptor.getValue()).hasSize(3);
        assertThat(keysCaptor.getValue().get(0)).startsWith("popular-menu:tmp:2026-07-15:");
        assertThat(keysCaptor.getValue().subList(1, 3)).containsExactly(
                "popular-menu:2026-07-15",
                "popular-menu:complete:2026-07-15");

        String script = scriptCaptor.getValue().getScriptAsString();
        assertThat(script).contains("redis.call('ZADD', KEYS[1]");
        assertThat(script).contains("redis.call('EXPIRE', KEYS[1], ARGV[2])");
        assertThat(script.indexOf("redis.call('ZADD', KEYS[1]"))
                .isLessThan(script.indexOf("redis.call('EXPIRE', KEYS[1], ARGV[2])"));
        assertThat(script.indexOf("redis.call('EXPIRE', KEYS[1], ARGV[2])"))
                .isLessThan(script.indexOf("redis.call('RENAME', KEYS[1], KEYS[2])"));
        assertThat(argumentsCaptor.getValue()).hasSize(7);
        assertThat(argumentsCaptor.getValue()[0]).isEqualTo("1209600");
        assertThat(argumentsCaptor.getValue()[1]).isEqualTo("60");
        assertThat(argumentsCaptor.getValue()[2].toString()).matches("[^|]+\\|8\\|2");
        assertThat(argumentsCaptor.getValue()).endsWith("5", "11", "3", "22");
    }

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
