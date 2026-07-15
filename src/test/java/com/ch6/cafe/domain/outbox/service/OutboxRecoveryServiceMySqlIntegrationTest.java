package com.ch6.cafe.domain.outbox.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.doThrow;

import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import com.ch6.cafe.domain.outbox.entity.OutboxStatus;
import com.ch6.cafe.domain.outbox.publisher.OutboxPublisher;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.outbox.repository.OutboxRecoveryAuditRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import com.ch6.cafe.global.lock.DistributedLockManager;
import java.time.LocalDateTime;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.data.domain.PageRequest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.context.bean.override.mockito.MockitoSpyBean;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
@ActiveProfiles("test")
@SpringBootTest(properties = {"spring.jpa.hibernate.ddl-auto=validate", "spring.flyway.enabled=true", "spring.kafka.listener.auto-startup=false"})
class OutboxRecoveryServiceMySqlIntegrationTest {
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
    @Autowired OutboxRecoveryService service;
    @Autowired OutboxEventRepository eventRepository;
    @MockitoSpyBean OutboxRecoveryAuditRepository auditRepository;
    @Autowired JdbcTemplate jdbcTemplate;

    @BeforeEach void clean() {
        jdbcTemplate.update("DELETE FROM outbox_recovery_audits");
        jdbcTemplate.update("DELETE FROM outbox_events");
        jdbcTemplate.update("DELETE FROM orders");
        jdbcTemplate.update("DELETE FROM menus");
        jdbcTemplate.update("DELETE FROM users");
    }

    @Test void migrationProvidesTheRecoveryAuditContract() {
        assertThat(jdbcTemplate.queryForList("SELECT column_name FROM information_schema.columns WHERE table_schema = DATABASE() AND table_name = 'outbox_recovery_audits' ORDER BY ordinal_position", String.class))
                .containsExactly("id", "event_id", "operator_name", "reason", "previous_retry_count", "previous_error", "recovered_at");
        assertThat(jdbcTemplate.queryForList("SELECT DISTINCT index_name FROM information_schema.statistics WHERE table_schema = DATABASE() AND table_name = 'outbox_recovery_audits'", String.class))
                .contains("PRIMARY", "idx_outbox_recovery_event_recovered");
        assertThat(jdbcTemplate.queryForObject("SELECT COUNT(*) FROM information_schema.referential_constraints WHERE constraint_schema = DATABASE() AND table_name = 'outbox_recovery_audits' AND constraint_name = 'fk_outbox_recovery_event'", Integer.class)).isOne();
    }

    @Test void failedEventIsAuditedAndRequeuedForNormalClaiming() {
        long eventId = seedEvent("FAILED", 5, "broker unavailable");
        service.requeueFailed(eventId, "operator-7", "broker incident resolved");
        OutboxEvent event = eventRepository.findById(eventId).orElseThrow();
        assertThat(event.getStatus()).isEqualTo(OutboxStatus.READY);
        assertThat(event.getRetryCount()).isZero();
        assertThat(event.getLastError()).isNull();
        assertThat(event.getClaimToken()).isNull();
        assertThat(eventRepository.findClaimable(LocalDateTime.now(), PageRequest.of(0, 1)))
                .extracting(OutboxEvent::getId).containsExactly(eventId);
        assertThat(auditRepository.findAll()).singleElement().satisfies(audit -> {
            assertThat(audit.getEventId()).isEqualTo(eventId);
            assertThat(audit.getOperator()).isEqualTo("operator-7");
            assertThat(audit.getReason()).isEqualTo("broker incident resolved");
            assertThat(audit.getPreviousRetryCount()).isEqualTo(5);
            assertThat(audit.getPreviousError()).isEqualTo("broker unavailable");
            assertThat(audit.getRecoveredAt()).isNotNull();
        });
    }

    @Test void readyEventAndBlankProvenanceAreRejectedWithoutAudit() {
        long ready = seedEvent("READY", 0, null);
        assertThatThrownBy(() -> service.requeueFailed(ready, "operator", "reason")).isInstanceOf(IllegalStateException.class);
        assertThatThrownBy(() -> service.requeueFailed(ready, " ", "reason")).isInstanceOf(IllegalArgumentException.class);
        assertThat(auditRepository.count()).isZero();
        assertThat(eventRepository.findById(ready).orElseThrow().getStatus()).isEqualTo(OutboxStatus.READY);
    }

    @Test void processingPublishedMissingAndBlankReasonAreRejectedWithoutMutationOrAudit() {
        long eventId = seedEvent("PROCESSING", 2, "in flight");

        assertThatThrownBy(() -> service.requeueFailed(eventId, "operator", "reason"))
                .isInstanceOf(IllegalStateException.class);
        assertUnchanged(eventId, OutboxStatus.PROCESSING, 2, "in flight");

        jdbcTemplate.update("UPDATE outbox_events SET status = 'PUBLISHED' WHERE id = ?", eventId);
        assertThatThrownBy(() -> service.requeueFailed(eventId, "operator", "reason"))
                .isInstanceOf(IllegalStateException.class);
        assertUnchanged(eventId, OutboxStatus.PUBLISHED, 2, "in flight");

        assertThatThrownBy(() -> service.requeueFailed(eventId + 999, "operator", "reason"))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Outbox event was not found.");

        jdbcTemplate.update("UPDATE outbox_events SET status = 'FAILED' WHERE id = ?", eventId);
        assertThatThrownBy(() -> service.requeueFailed(eventId, "operator", " "))
                .isInstanceOf(IllegalArgumentException.class)
                .hasMessage("Reason must not be blank.");
        assertUnchanged(eventId, OutboxStatus.FAILED, 2, "in flight");
        assertThat(auditRepository.count()).isZero();
    }

    @Test void recoveryPersistenceFailureRollsBackAuditAndStateTransition() {
        long failed = seedEvent("FAILED", 5, "permanent");
        doThrow(new DataAccessResourceFailureException("forced audit failure")).when(auditRepository).save(any());
        assertThatThrownBy(() -> service.requeueFailed(failed, "operator", "reason"))
                .isInstanceOf(DataAccessResourceFailureException.class);
        OutboxEvent unchanged = eventRepository.findById(failed).orElseThrow();
        assertThat(unchanged.getStatus()).isEqualTo(OutboxStatus.FAILED);
        assertThat(unchanged.getRetryCount()).isEqualTo(5);
        assertThat(unchanged.getLastError()).isEqualTo("permanent");
        assertThat(auditRepository.count()).isZero();
    }

    private long seedEvent(String status, int retryCount, String error) {
        LocalDateTime now = LocalDateTime.now();
        jdbcTemplate.update("INSERT INTO users (id, created_at, updated_at) VALUES (1, ?, ?)", now, now);
        jdbcTemplate.update("INSERT INTO menus (id, name, price, status, created_at, updated_at) VALUES (1, 'Latte', 4500, 'ON_SALE', ?, ?)", now, now);
        jdbcTemplate.update("INSERT INTO orders (id, user_id, menu_id, order_price, status, ordered_at) VALUES (1, 1, 1, 4500, 'PAID', ?)", now);
        jdbcTemplate.update("INSERT INTO outbox_events (aggregate_type, aggregate_id, event_type, payload, status, retry_count, last_error, created_at, updated_at) VALUES ('ORDER', 1, 'ORDER_PAID', JSON_OBJECT('userId', 1, 'menuId', 1, 'paymentAmount', 4500), ?, ?, ?, ?, ?)", status, retryCount, error, now, now);
        return jdbcTemplate.queryForObject("SELECT id FROM outbox_events", Long.class);
    }

    private void assertUnchanged(long eventId, OutboxStatus status, int retryCount, String lastError) {
        OutboxEvent event = eventRepository.findById(eventId).orElseThrow();
        assertThat(event.getStatus()).isEqualTo(status);
        assertThat(event.getRetryCount()).isEqualTo(retryCount);
        assertThat(event.getLastError()).isEqualTo(lastError);
        assertThat(auditRepository.count()).isZero();
    }
}
