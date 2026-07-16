package com.ch6.cafe.domain.outbox.publisher;

import static java.util.concurrent.TimeUnit.SECONDS;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyString;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import com.ch6.cafe.domain.outbox.entity.OutboxStatus;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import com.ch6.cafe.global.lock.DistributedLockManager;
import tools.jackson.databind.ObjectMapper;
import java.time.LocalDateTime;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.function.Consumer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.support.SendResult;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.transaction.support.TransactionTemplate;
import org.springframework.transaction.TransactionStatus;
import org.springframework.transaction.support.TransactionCallback;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
@ActiveProfiles("test")
@SpringBootTest(properties = {"spring.jpa.hibernate.ddl-auto=validate", "spring.flyway.enabled=true", "spring.kafka.listener.auto-startup=false"})
class OutboxPublisherMySqlIntegrationTest {
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
    @MockitoBean OrderPaidConsumer consumer;
    @MockitoBean OutboxPublisher outboxPublisher;
    @MockitoBean KafkaTemplate<String, String> kafkaTemplate;
    @Autowired OutboxEventRepository repository;
    @Autowired TransactionTemplate transactions;
    @Autowired ObjectMapper objectMapper;
    @Autowired JdbcTemplate jdbcTemplate;

    @BeforeEach void clean() {
        jdbcTemplate.update("DELETE FROM outbox_recovery_audits");
        jdbcTemplate.update("DELETE FROM outbox_events");
        jdbcTemplate.update("DELETE FROM orders");
        jdbcTemplate.update("DELETE FROM menus");
        jdbcTemplate.update("DELETE FROM users");
    }

    @Test void independentWorkersClaimDifferentRowsOneAtATime() {
        seedEvents(2);
        var firstClaim = publisher("worker-a", 2).claimNext();
        var secondClaim = publisher("worker-b", 2).claimNext();
        assertThat(firstClaim).isPresent();
        assertThat(secondClaim).isPresent();
        assertThat(secondClaim.orElseThrow().id()).isNotEqualTo(firstClaim.orElseThrow().id());
        assertThat(repository.findAll()).allMatch(event -> event.getStatus() == OutboxStatus.PROCESSING);
    }

    @Test void databaseTimeControlsClaimLeaseDespiteJvmClockSkew() {
        seedEvents(1);
        LocalDateTime[] observed = new LocalDateTime[3];

        transactions.executeWithoutResult(status -> {
            jdbcTemplate.execute("SET timestamp = 1893456000");
            try {
                observed[0] = repository.currentDatabaseTime();
                publisher("database-clock-worker", 1).claimNext().orElseThrow();
                repository.flush();
                OutboxEvent claimed = repository.findAll().getFirst();
                observed[1] = claimed.getClaimedAt();
                observed[2] = claimed.getClaimUntil();
            } finally {
                jdbcTemplate.execute("SET timestamp = 0");
            }
        });

        assertThat(observed[1]).isEqualTo(observed[0]);
        assertThat(observed[2]).isEqualTo(observed[0].plusSeconds(30));
        assertThat(observed[0]).isNotBetween(
                LocalDateTime.now().minusMinutes(1), LocalDateTime.now().plusMinutes(1));
    }

    @Test void slowSendDoesNotPreleaseLaterRowAndUsesCanonicalTopicAndAggregateKey() throws Exception {
        seedEvents(2);
        CompletableFuture<SendResult<String, String>> send = new CompletableFuture<>();
        CountDownLatch invoked = new CountDownLatch(1);
        when(kafkaTemplate.send(anyString(), anyString(), anyString())).thenAnswer(call -> {
            assertThat(call.getArgument(0, String.class)).isEqualTo("coffee.order.paid");
            assertThat(call.getArgument(1, String.class)).isEqualTo("1");
            invoked.countDown();
            return send;
        });
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<?> task = executor.submit(publisher("worker-a", 1)::publishBatch);
        try {
            assertThat(invoked.await(5, SECONDS)).isTrue();
            assertThat(repository.findAll()).extracting(OutboxEvent::getStatus)
                    .containsExactlyInAnyOrder(OutboxStatus.PROCESSING, OutboxStatus.READY);
            send.complete(mock(SendResult.class));
            task.get(5, SECONDS);
        } finally {
            executor.shutdownNow();
        }
    }

    @Test void expiredProcessingRowGetsNewTokenAndRejectsTheOldToken() {
        seedEvents(1);
        OutboxPublisher publisher = publisher("worker-a", 1);
        OutboxPublisher.ClaimedEvent oldClaim = publisher.claimNext().orElseThrow();
        jdbcTemplate.update("UPDATE outbox_events SET claim_until = ? WHERE id = ?", LocalDateTime.now().minusSeconds(1), oldClaim.id());

        OutboxPublisher.ClaimedEvent reassigned = publisher("worker-b", 1).claimNext().orElseThrow();
        OutboxEvent event = repository.findById(reassigned.id()).orElseThrow();

        assertThat(reassigned.token()).isNotEqualTo(oldClaim.token());
        assertThatThrownBy(() -> event.markPublished(oldClaim.token(), LocalDateTime.now()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("Outbox claim token is stale.");
    }

    @Test void acknowledgedSendWithCompletionFailureReturnsToAReclaimableDuplicateBoundary() {
        seedEvents(1);
        when(kafkaTemplate.send(anyString(), anyString(), anyString()))
                .thenReturn(CompletableFuture.completedFuture(mock(SendResult.class)));
        OutboxPublisher publisher = new OutboxPublisher(
                repository, kafkaTemplate, failFirstCompletionTransaction(), objectMapper,
                "worker-a", 1, 30, 5);

        publisher.publishBatch();

        OutboxEvent retryable = repository.findAll().getFirst();
        assertThat(retryable.getStatus()).isEqualTo(OutboxStatus.READY);
        assertThat(retryable.getRetryCount()).isOne();
        assertThat(retryable.getClaimToken()).isNull();
        OutboxPublisher.ClaimedEvent reclaimed = publisher("worker-b", 1).claimNext().orElseThrow();
        assertThat(reclaimed.id()).isEqualTo(retryable.getId());
        verify(kafkaTemplate, times(1)).send(
                eq("coffee.order.paid"), eq("1"), org.mockito.ArgumentMatchers.anyString());
    }

    private OutboxPublisher publisher(String owner, int batchSize) {
        return new OutboxPublisher(repository, kafkaTemplate, transactions, objectMapper, owner, batchSize, 30, 5);
    }

    private TransactionTemplate failFirstCompletionTransaction() {
        AtomicInteger completionAttempts = new AtomicInteger();
        return new TransactionTemplate(transactions.getTransactionManager()) {
            @Override
            public <T> T execute(TransactionCallback<T> action) {
                return transactions.execute(action);
            }

            @Override
            public void executeWithoutResult(Consumer<TransactionStatus> action) {
                if (completionAttempts.getAndIncrement() == 0) {
                    throw new DataAccessResourceFailureException("forced completion failure");
                }
                transactions.executeWithoutResult(action);
            }
        };
    }

    private void seedEvents(int count) {
        LocalDateTime now = LocalDateTime.now();
        jdbcTemplate.update("INSERT INTO users (id, created_at, updated_at) VALUES (1, ?, ?)", now, now);
        jdbcTemplate.update("INSERT INTO menus (id, name, price, status, created_at, updated_at) VALUES (1, 'Latte', 4500, 'ON_SALE', ?, ?)", now, now);
        for (int id = 1; id <= count; id++) {
            jdbcTemplate.update("INSERT INTO orders (id, user_id, menu_id, order_price, status, ordered_at) VALUES (?, 1, 1, 4500, 'PAID', ?)", id, now);
            jdbcTemplate.update("INSERT INTO outbox_events (aggregate_type, aggregate_id, event_type, payload, status, retry_count, created_at, updated_at) VALUES ('ORDER', ?, 'ORDER_PAID', JSON_OBJECT('userId', 1, 'menuId', 1, 'paymentAmount', 4500), 'READY', 0, ?, ?)", id, now.plusSeconds(id), now);
        }
    }
}
