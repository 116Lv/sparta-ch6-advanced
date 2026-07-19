package com.ch6.cafe.domain.menu.repository;

import static org.assertj.core.api.Assertions.assertThat;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import com.ch6.cafe.domain.outbox.publisher.OutboxPublisher;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import java.util.List;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
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
class MenuRepositoryMySqlIntegrationTest {

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
    @Autowired MenuRepository repository;
    @Autowired JdbcTemplate jdbc;

    @BeforeEach
    void seed() {
        jdbc.update("DELETE FROM menus");
        insert(30L, "Latte", 5500L, MenuStatus.ON_SALE);
        insert(10L, "Americano", 4500L, MenuStatus.ON_SALE);
        insert(20L, "Mocha", 6000L, MenuStatus.SOLD_OUT);
        insert(40L, "Espresso", 4000L, MenuStatus.DELETED);
    }

    @Test
    void findsOnlyOnSaleMenusOrderedByIdAscending() {
        List<Menu> menus = repository.findAllByStatusOrderByIdAsc(MenuStatus.ON_SALE);

        assertThat(menus).extracting(Menu::getId).containsExactly(10L, 30L);
        assertThat(menus).extracting(Menu::getStatus)
                .containsExactly(MenuStatus.ON_SALE, MenuStatus.ON_SALE);
        assertThat(menus).extracting(Menu::getName)
                .containsExactly("Americano", "Latte");
        assertThat(menus).extracting(Menu::getPrice)
                .containsExactly(4500L, 5500L);
    }

    private void insert(long id, String name, long price, MenuStatus status) {
        jdbc.update("""
                INSERT INTO menus (id, name, price, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """, id, name, price, status.name());
    }
}
