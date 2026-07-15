package com.ch6.cafe.domain.outbox.publisher;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.ch6.cafe.domain.outbox.repository.OrderPaidAnalyticsRepository;
import com.ch6.cafe.domain.outbox.repository.ProcessedEventRepository;
import com.ch6.cafe.domain.outbox.service.OrderPaidAnalyticsService;
import com.ch6.cafe.domain.outbox.service.OrderPaidMessage;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import com.ch6.cafe.global.lock.DistributedLockManager;
import com.fasterxml.jackson.databind.ObjectMapper;
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
@SpringBootTest(properties = {"spring.jpa.hibernate.ddl-auto=validate", "spring.flyway.enabled=true", "spring.kafka.listener.auto-startup=false"})
class OrderPaidConsumerMySqlIntegrationTest {
    @Container static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.4.0");
    @DynamicPropertySource static void mysqlProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);
        registry.add("spring.datasource.driver-class-name", MYSQL::getDriverClassName);
    }
    @MockitoBean DistributedLockManager lockManager;
    @MockitoBean RedisPopularMenuRepository redisRepository;
    @MockitoBean RedissonClient redissonClient;
    @MockitoBean OutboxPublisher outboxPublisher;
    @Autowired OrderPaidAnalyticsService service;
    @Autowired OrderPaidAnalyticsRepository analyticsRepository;
    @Autowired ProcessedEventRepository processedRepository;
    @Autowired ObjectMapper objectMapper;
    @Autowired JdbcTemplate jdbcTemplate;

    @BeforeEach void clean() {
        jdbcTemplate.update("DELETE FROM order_paid_analytics");
        jdbcTemplate.update("DELETE FROM processed_events");
    }

    @Test void migrationProvidesTheDurableAnalyticsContract() {
        assertThat(jdbcTemplate.queryForObject("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'order_paid_analytics'", Integer.class)).isOne();
        assertThat(jdbcTemplate.queryForList("SELECT column_name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'order_paid_analytics' ORDER BY ordinal_position", String.class))
                .containsExactly("consumer_group", "event_id", "aggregate_id", "user_id", "menu_id", "payment_amount", "processed_at");
        assertThat(jdbcTemplate.queryForList("SELECT DISTINCT index_name FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'order_paid_analytics'", String.class))
                .contains("PRIMARY", "uk_order_paid_analytics_group_aggregate", "idx_order_paid_analytics_group_processed");
    }

    @Test void listenerDuplicateDeliveryCommitsOneMarkerAndOneExactAnalyticsEffect() throws Exception {
        OrderPaidConsumer consumer = new OrderPaidConsumer(service, objectMapper, "analytics-a");
        String json = message(11, 101, 7, 17, 4_500);
        consumer.consume(json);
        consumer.consume(json);
        assertThat(processedRepository.count()).isOne();
        assertThat(analyticsRepository.findAll()).singleElement().satisfies(effect -> {
            assertThat(effect.getId().getConsumerGroup()).isEqualTo("analytics-a");
            assertThat(effect.getId().getEventId()).isEqualTo(11L);
            assertThat(effect.getAggregateId()).isEqualTo(101L);
            assertThat(effect.getUserId()).isEqualTo(7L);
            assertThat(effect.getMenuId()).isEqualTo(17L);
            assertThat(effect.getPaymentAmount()).isEqualTo(4_500L);
        });
    }

    @Test void differentGroupsEachCommitTheirOwnEffect() {
        var message = new OrderPaidMessage(11, "ORDER_PAID", 101, 7, 17, 4_500);
        assertThat(service.apply("analytics-a", message)).isTrue();
        assertThat(service.apply("analytics-b", message)).isTrue();
        assertThat(processedRepository.count()).isEqualTo(2);
        assertThat(analyticsRepository.count()).isEqualTo(2);
    }

    @Test void analyticsConstraintFailureRollsBackTheNewMarker() {
        service.apply("analytics-a", new OrderPaidMessage(11, "ORDER_PAID", 101, 7, 17, 4_500));
        assertThatThrownBy(() -> service.apply("analytics-a", new OrderPaidMessage(12, "ORDER_PAID", 101, 8, 18, 5_000)))
                .isInstanceOf(RuntimeException.class);
        assertThat(processedRepository.count()).isOne();
        assertThat(analyticsRepository.count()).isOne();
    }

    @Test void missingNullNonNumericAndOutOfRangeValuesCreateNoDurableState() {
        OrderPaidConsumer consumer = new OrderPaidConsumer(service, objectMapper, "analytics-a");
        String[] invalidMessages = {
                "{\"eventId\":11,\"eventType\":\"ORDER_PAID\",\"aggregateId\":101,\"payload\":{\"userId\":7,\"menuId\":17}}",
                "{\"eventId\":11,\"eventType\":\"ORDER_PAID\",\"aggregateId\":101,\"payload\":{\"userId\":null,\"menuId\":17,\"paymentAmount\":4500}}",
                "{\"eventId\":11,\"eventType\":\"ORDER_PAID\",\"aggregateId\":101,\"payload\":{\"userId\":7,\"menuId\":\"17\",\"paymentAmount\":4500}}",
                "{\"eventId\":18446744073709551617,\"eventType\":\"ORDER_PAID\",\"aggregateId\":101,\"payload\":{\"userId\":7,\"menuId\":17,\"paymentAmount\":4500}}"
        };

        for (String invalidMessage : invalidMessages) {
            assertThatThrownBy(() -> consumer.consume(invalidMessage))
                    .isInstanceOf(IllegalArgumentException.class)
                    .hasMessage("ORDER_PAID event contract is invalid.");
            assertThat(processedRepository.count()).isZero();
            assertThat(analyticsRepository.count()).isZero();
        }
    }

    private String message(long eventId, long aggregateId, long userId, long menuId, long amount) {
        return "{\"eventId\":" + eventId + ",\"eventType\":\"ORDER_PAID\",\"aggregateId\":" + aggregateId
                + ",\"payload\":{\"userId\":" + userId + ",\"menuId\":" + menuId + ",\"paymentAmount\":" + amount + "}}";
    }
}
