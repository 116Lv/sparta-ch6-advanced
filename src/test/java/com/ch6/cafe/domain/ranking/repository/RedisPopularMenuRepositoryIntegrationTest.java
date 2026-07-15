package com.ch6.cafe.domain.ranking.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.ch6.cafe.domain.ranking.entity.PopularMenu;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import org.junit.jupiter.api.AfterAll;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeAll;
import org.junit.jupiter.api.Test;
import org.springframework.data.redis.connection.RedisStandaloneConfiguration;
import org.springframework.data.redis.connection.lettuce.LettuceConnectionFactory;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

@Testcontainers
class RedisPopularMenuRepositoryIntegrationTest {

    @Container
    static final GenericContainer<?> REDIS =
            new GenericContainer<>(DockerImageName.parse("redis:7.4-alpine")).withExposedPorts(6379);

    private static LettuceConnectionFactory connectionFactory;
    private static StringRedisTemplate template;
    private static RedisPopularMenuRepository repository;

    @BeforeAll
    static void connect() {
        RedisStandaloneConfiguration configuration =
                new RedisStandaloneConfiguration(REDIS.getHost(), REDIS.getMappedPort(6379));
        connectionFactory = new LettuceConnectionFactory(configuration);
        connectionFactory.afterPropertiesSet();
        template = new StringRedisTemplate(connectionFactory);
        template.afterPropertiesSet();
        repository = new RedisPopularMenuRepository(template);
    }

    @AfterEach
    void clearRedis() {
        Set<String> keys = template.keys("popular-menu:*");
        if (keys != null && !keys.isEmpty()) {
            template.delete(keys);
        }
    }

    @AfterAll
    static void disconnect() {
        if (connectionFactory != null) {
            connectionFactory.destroy();
        }
    }

    @Test
    void readsOnlyWhenEveryDayHasCompletenessMarker() {
        LocalDate to = LocalDate.of(2026, 7, 15);
        repository.replaceDate(to, Map.of(1L, 5L));
        template.opsForZSet().add("popular-menu:2026-07-14", "2", 9D);

        Map<LocalDate, DailySalesMetadata> expected = Map.of(
                to, new DailySalesMetadata(5L, 1L),
                to.minusDays(1), new DailySalesMetadata(9L, 1L));
        assertThat(repository.findComplete(to, 2, expected)).isEmpty();

        repository.replaceDate(to.minusDays(1), Map.of(2L, 9L));
        assertThat(repository.findComplete(to, 2, expected)).hasValueSatisfying(ranking ->
                assertThat(ranking).extracting(PopularMenu::menuId).containsExactly(2L, 1L));
    }

    @Test
    void emptyReplacementDeletesStaleRankingAndMarksDateComplete() {
        LocalDate date = LocalDate.of(2026, 7, 15);
        repository.replaceDate(date, Map.of(1L, 5L));

        repository.replaceDate(date, Map.of());

        assertThat(template.hasKey("popular-menu:2026-07-15")).isFalse();
        assertThat(template.hasKey("popular-menu:complete:2026-07-15")).isTrue();
        assertThat(repository.findComplete(date, 1, Map.of(date, new DailySalesMetadata(0L, 0L))))
                .hasValue(List.of());
    }

    @Test
    void replacementSetsDailyTtlAndAlwaysCleansTemporaryKeys() {
        LocalDate date = LocalDate.of(2026, 7, 15);

        repository.replaceDate(date, Map.of(1L, 5L, 2L, 3L));

        Long dataTtl = template.getExpire("popular-menu:2026-07-15", TimeUnit.DAYS);
        Long markerTtl = template.getExpire("popular-menu:complete:2026-07-15", TimeUnit.DAYS);
        assertThat(dataTtl).isBetween(13L, 14L);
        assertThat(markerTtl).isBetween(13L, 14L);
        assertThat(template.keys("popular-menu:tmp:*")).isEmpty();
    }

    @Test
    void absoluteAssignmentPublishesNewCompleteGenerationFromDurableMetadata() {
        LocalDate date = LocalDate.of(2026, 7, 15);
        repository.replaceDate(date, Map.of(1L, 5L));
        repository.setAbsolute(date, 1L, 6L, 6L, 1L);
        assertThat(template.opsForZSet().score("popular-menu:2026-07-15", "1")).isEqualTo(6D);

        template.delete("popular-menu:complete:2026-07-15");
        repository.setAbsolute(date, 1L, 7L, 7L, 1L);

        assertThat(template.opsForZSet().score("popular-menu:2026-07-15", "1")).isEqualTo(7D);
        assertThat(template.hasKey("popular-menu:complete:2026-07-15")).isTrue();
        assertThat(repository.findComplete(
                date, 1, Map.of(date, new DailySalesMetadata(7L, 1L))))
                .hasValueSatisfying(ranking -> assertThat(ranking)
                        .extracting(PopularMenu::orderCount)
                        .containsExactly(7L));
    }

    @Test
    void markerSurvivingDataLossIsRejectedAgainstDurableMetadata() {
        LocalDate date = LocalDate.of(2026, 7, 15);
        repository.replaceDate(date, Map.of(1L, 5L));
        template.delete("popular-menu:2026-07-15");

        assertThat(repository.findComplete(
                date, 1, Map.of(date, new DailySalesMetadata(5L, 1L)))).isEmpty();
    }

    @Test
    void oldGenerationMetadataIsRejectedAfterDurableCountAdvances() {
        LocalDate date = LocalDate.of(2026, 7, 15);
        repository.replaceDate(date, Map.of(1L, 5L));

        assertThat(repository.findComplete(
                date, 1, Map.of(date, new DailySalesMetadata(6L, 1L)))).isEmpty();
    }
}
