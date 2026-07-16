package com.ch6.cafe.domain.outbox.publisher;

import static java.util.concurrent.TimeUnit.SECONDS;
import static org.assertj.core.api.Assertions.assertThat;

import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import com.ch6.cafe.domain.outbox.entity.OutboxStatus;
import com.ch6.cafe.domain.outbox.repository.OrderPaidAnalyticsRepository;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.outbox.repository.ProcessedEventRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import com.ch6.cafe.global.lock.DistributedLockManager;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.apache.kafka.clients.consumer.ConsumerRecords;
import org.apache.kafka.clients.consumer.KafkaConsumer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.kafka.core.DefaultKafkaProducerFactory;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.transaction.support.TransactionTemplate;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.kafka.KafkaContainer;
import org.testcontainers.utility.DockerImageName;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

@Testcontainers
@ActiveProfiles("test")
@SpringBootTest(properties = {
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.flyway.enabled=true",
        "outbox.publisher.poll-millis=600000"
})
class OrderPaidKafkaIntegrationTest {

    private static final String TOPIC = "coffee.order.paid";
    private static final String CONSUMER_GROUP = "coffee-order-analytics-kafka-test";
    private static final Duration TIMEOUT = Duration.ofSeconds(15);

    @Container
    static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.4.0");

    @Container
    static final KafkaContainer KAFKA = new KafkaContainer(
            DockerImageName.parse("apache/kafka-native:3.8.0"));

    @DynamicPropertySource
    static void infrastructureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);
        registry.add("spring.datasource.driver-class-name", MYSQL::getDriverClassName);
        registry.add("spring.kafka.bootstrap-servers", KAFKA::getBootstrapServers);
        registry.add("spring.kafka.consumer.group-id", () -> CONSUMER_GROUP);
    }

    @MockitoBean DistributedLockManager lockManager;
    @MockitoBean RedisPopularMenuRepository redisRepository;
    @MockitoBean RedissonClient redissonClient;

    @Autowired OutboxPublisher publisher;
    @Autowired OutboxEventRepository outboxRepository;
    @Autowired ProcessedEventRepository processedRepository;
    @Autowired OrderPaidAnalyticsRepository analyticsRepository;
    @Autowired KafkaTemplate<String, String> kafkaTemplate;
    @Autowired TransactionTemplate transactions;
    @Autowired ObjectMapper objectMapper;
    @Autowired JdbcTemplate jdbcTemplate;

    @BeforeEach
    void clean() {
        jdbcTemplate.update("DELETE FROM order_paid_analytics");
        jdbcTemplate.update("DELETE FROM processed_events");
        jdbcTemplate.update("DELETE FROM outbox_recovery_audits");
        jdbcTemplate.update("DELETE FROM outbox_events");
        jdbcTemplate.update("DELETE FROM orders");
        jdbcTemplate.update("DELETE FROM menus");
        jdbcTemplate.update("DELETE FROM users");
    }

    @Test
    void publisherSendsAggregateKeyAndListenerCommitsOneEffectForBrokerDuplicate() throws Exception {
        OutboxEvent event = seedEvent(101L);

        try (KafkaConsumer<String, String> observer = observer()) {
            observer.subscribe(Set.of(TOPIC));
            awaitAssignment(observer);

            publisher.publishBatch();

            ConsumerRecord<String, String> record = awaitRecord(observer, event.getId());
            assertThat(record.topic()).isEqualTo(TOPIC);
            assertThat(record.key()).isEqualTo("101");
            JsonNode envelope = objectMapper.readTree(record.value());
            assertThat(envelope.path("eventId").longValue()).isEqualTo(event.getId());
            assertThat(envelope.path("eventType").textValue()).isEqualTo("ORDER_PAID");
            assertThat(envelope.path("aggregateId").longValue()).isEqualTo(101L);
            assertThat(envelope.path("payload").path("paymentAmount").longValue()).isEqualTo(4_500L);

            awaitDatabaseState(event.getId(), 1, 1);
            assertThat(outboxRepository.findById(event.getId()).orElseThrow().getStatus())
                    .isEqualTo(OutboxStatus.PUBLISHED);

            kafkaTemplate.send(TOPIC, record.partition(), record.key(), record.value()).get(5, SECONDS);
            long sentinelEventId = event.getId() + 1_000_000;
            kafkaTemplate.send(TOPIC, record.partition(), "102", message(sentinelEventId, 102L))
                    .get(5, SECONDS);

            awaitDatabaseState(sentinelEventId, 2, 2);
            assertThat(jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM processed_events WHERE consumer_group = ? AND event_id = ?",
                    Integer.class, CONSUMER_GROUP, event.getId())).isOne();
            assertThat(jdbcTemplate.queryForObject(
                    "SELECT COUNT(*) FROM order_paid_analytics WHERE consumer_group = ? AND event_id = ?",
                    Integer.class, CONSUMER_GROUP, event.getId())).isOne();
        }
    }

    @Test
    void realProducerFailureReturnsClaimToRetryableReadyState() {
        OutboxEvent event = seedEvent(201L);
        Map<String, Object> properties = new HashMap<>();
        properties.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "127.0.0.1:1");
        properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        properties.put(ProducerConfig.MAX_BLOCK_MS_CONFIG, 500);
        properties.put(ProducerConfig.REQUEST_TIMEOUT_MS_CONFIG, 500);
        properties.put(ProducerConfig.DELIVERY_TIMEOUT_MS_CONFIG, 1_000);
        properties.put(ProducerConfig.RETRIES_CONFIG, 0);
        DefaultKafkaProducerFactory<String, String> factory = new DefaultKafkaProducerFactory<>(properties);
        try {
            OutboxPublisher failingPublisher = new OutboxPublisher(
                    outboxRepository, new KafkaTemplate<>(factory), transactions, objectMapper,
                    "broker-failure-test", 1, 30, 5);

            failingPublisher.publishBatch();

            OutboxEvent retryable = outboxRepository.findById(event.getId()).orElseThrow();
            assertThat(retryable.getStatus()).isEqualTo(OutboxStatus.READY);
            assertThat(retryable.getRetryCount()).isOne();
            assertThat(retryable.getLastError()).isNotBlank();
            assertThat(retryable.getClaimToken()).isNull();
            assertThat(retryable.getClaimOwner()).isNull();
        } finally {
            factory.destroy();
        }
    }

    private KafkaConsumer<String, String> observer() {
        Map<String, Object> properties = new HashMap<>();
        properties.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, KAFKA.getBootstrapServers());
        properties.put(ConsumerConfig.GROUP_ID_CONFIG, "broker-observer-" + UUID.randomUUID());
        properties.put(ConsumerConfig.AUTO_OFFSET_RESET_CONFIG, "earliest");
        properties.put(ConsumerConfig.ENABLE_AUTO_COMMIT_CONFIG, false);
        properties.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        properties.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        return new KafkaConsumer<>(properties);
    }

    private void awaitAssignment(KafkaConsumer<String, String> consumer) {
        long deadline = System.nanoTime() + TIMEOUT.toNanos();
        while (consumer.assignment().isEmpty() && System.nanoTime() < deadline) {
            consumer.poll(Duration.ofMillis(250));
        }
        assertThat(consumer.assignment()).as("observer assignment before publishing").isNotEmpty();
    }

    private ConsumerRecord<String, String> awaitRecord(KafkaConsumer<String, String> consumer, long eventId)
            throws Exception {
        long deadline = System.nanoTime() + TIMEOUT.toNanos();
        while (System.nanoTime() < deadline) {
            ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(250));
            for (ConsumerRecord<String, String> record : records) {
                if (objectMapper.readTree(record.value()).path("eventId").longValue() == eventId) {
                    return record;
                }
            }
        }
        throw new AssertionError("Timed out waiting for event " + eventId + " on " + TOPIC);
    }

    private void awaitDatabaseState(long eventId, long expectedMarkers, long expectedEffects) throws Exception {
        long deadline = System.nanoTime() + TIMEOUT.toNanos();
        AssertionError lastFailure = null;
        while (System.nanoTime() < deadline) {
            try {
                assertThat(processedRepository.count()).isEqualTo(expectedMarkers);
                assertThat(analyticsRepository.count()).isEqualTo(expectedEffects);
                assertThat(jdbcTemplate.queryForObject(
                        "SELECT COUNT(*) FROM processed_events WHERE consumer_group = ? AND event_id = ?",
                        Integer.class, CONSUMER_GROUP, eventId)).isOne();
                return;
            } catch (AssertionError failure) {
                lastFailure = failure;
                Thread.sleep(50);
            }
        }
        throw new AssertionError("Timed out waiting for durable Kafka consumer state", lastFailure);
    }

    private OutboxEvent seedEvent(long aggregateId) {
        LocalDateTime now = LocalDateTime.now();
        jdbcTemplate.update("INSERT INTO users (id, created_at, updated_at) VALUES (1, ?, ?)", now, now);
        jdbcTemplate.update("INSERT INTO menus (id, name, price, status, created_at, updated_at) "
                + "VALUES (1, 'Latte', 4500, 'ON_SALE', ?, ?)", now, now);
        jdbcTemplate.update("INSERT INTO orders (id, user_id, menu_id, order_price, status, ordered_at) "
                + "VALUES (?, 1, 1, 4500, 'PAID', ?)", aggregateId, now);
        jdbcTemplate.update("INSERT INTO outbox_events "
                + "(aggregate_type, aggregate_id, event_type, payload, status, retry_count, created_at, updated_at) "
                + "VALUES ('ORDER', ?, 'ORDER_PAID', "
                + "JSON_OBJECT('userId', 1, 'menuId', 1, 'paymentAmount', 4500), 'READY', 0, ?, ?)",
                aggregateId, now, now);
        return outboxRepository.findAll().getFirst();
    }

    private String message(long eventId, long aggregateId) {
        return "{\"eventId\":" + eventId + ",\"eventType\":\"ORDER_PAID\",\"aggregateId\":" + aggregateId
                + ",\"payload\":{\"userId\":1,\"menuId\":1,\"paymentAmount\":4500}}";
    }
}
