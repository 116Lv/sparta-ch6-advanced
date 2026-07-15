package com.ch6.cafe.domain.ranking.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.ch6.cafe.domain.outbox.publisher.OutboxPublisher;
import com.ch6.cafe.domain.ranking.entity.PopularMenu;
import java.time.LocalDate;
import java.util.Arrays;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.data.jpa.repository.Query;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
@ActiveProfiles("test")
@SpringBootTest(properties = {
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.flyway.enabled=true",
        "spring.kafka.listener.auto-startup=false"
})
class DailyMenuSalesRepositoryMySqlIntegrationTest {

    @Container
    static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.4.0");

    @DynamicPropertySource
    static void mysqlProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);
        registry.add("spring.datasource.driver-class-name", MYSQL::getDriverClassName);
    }

    @MockitoBean RedisPopularMenuRepository redisRepository;
    @MockitoBean RedissonClient redissonClient;
    @MockitoBean OutboxPublisher outboxPublisher;
    @Autowired DailyMenuSalesRepository repository;
    @Autowired JdbcTemplate jdbc;

    @BeforeEach
    void seed() {
        jdbc.update("DELETE FROM daily_menu_sales");
        jdbc.update("DELETE FROM menus");
        for (long id = 1; id <= 4; id++) {
            jdbc.update("""
                    INSERT INTO menus (id, name, price, status, created_at, updated_at)
                    VALUES (?, ?, 4500, 'ON_SALE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    """, id, "menu-" + id);
        }
        insert(LocalDate.of(2026, 7, 9), 4L, 100L);
        insert(LocalDate.of(2026, 7, 10), 1L, 4L);
        insert(LocalDate.of(2026, 7, 16), 1L, 3L);
        insert(LocalDate.of(2026, 7, 16), 2L, 7L);
        insert(LocalDate.of(2026, 7, 16), 3L, 6L);
    }

    @Test
    void inclusiveWindowExcludesOutsideDateAndProvidesDailyMetadataForTopThreeTiePolicy() {
        LocalDate from = LocalDate.of(2026, 7, 10);
        LocalDate to = LocalDate.of(2026, 7, 16);

        List<PopularMenu> ranking = repository.aggregateBetween(from, to).stream()
                .map(row -> new PopularMenu(row.getMenuId(), row.getOrderCount()))
                .sorted(PopularMenu.ORDERING)
                .toList();
        List<DailySalesMetadataProjection> metadata = repository.summarizeBetween(from, to);

        assertThat(ranking).extracting(PopularMenu::menuId).containsExactly(1L, 2L, 3L);
        assertThat(ranking).extracting(PopularMenu::orderCount).containsExactly(7L, 7L, 6L);
        assertThat(ranking).extracting(PopularMenu::menuId).doesNotContain(4L);
        assertThat(metadata)
                .extracting(
                        DailySalesMetadataProjection::getSalesDate,
                        DailySalesMetadataProjection::getTotalOrderCount,
                        DailySalesMetadataProjection::getMenuCount)
                .containsExactlyInAnyOrder(
                        org.assertj.core.groups.Tuple.tuple(LocalDate.of(2026, 7, 10), 4L, 1L),
                        org.assertj.core.groups.Tuple.tuple(LocalDate.of(2026, 7, 16), 16L, 3L));
    }

    @Test
    void aggregateReadsAreImplementedByQueryDslFragmentRatherThanJpqlQueries() {
        assertThat(Arrays.stream(DailyMenuSalesRepository.class.getDeclaredMethods())
                .filter(method -> method.isAnnotationPresent(Query.class))
                .map(method -> method.getName())
                .toList())
                .containsExactly("increment");
    }

    private void insert(LocalDate date, long menuId, long count) {
        jdbc.update("""
                INSERT INTO daily_menu_sales
                    (sales_date, menu_id, order_count, created_at, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, date, menuId, count);
    }
}
