package com.ch6.cafe.domain.outbox.publisher;

import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ObjectNode;
import java.time.Duration;
import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.TimeUnit;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.domain.PageRequest;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionTemplate;

@Component
public class OutboxPublisher {

    private static final Logger log = LoggerFactory.getLogger(OutboxPublisher.class);
    private static final String TOPIC = "coffee.order.paid";

    private final OutboxEventRepository repository;
    private final KafkaTemplate<String, String> kafkaTemplate;
    private final TransactionTemplate transactionTemplate;
    private final ObjectMapper objectMapper;
    private final String owner;
    private final int batchSize;
    private final Duration claimDuration;
    private final int maxRetries;

    public OutboxPublisher(
            OutboxEventRepository repository,
            KafkaTemplate<String, String> kafkaTemplate,
            TransactionTemplate transactionTemplate,
            ObjectMapper objectMapper,
            @Value("${outbox.publisher.owner:${random.uuid}}") String owner,
            @Value("${outbox.publisher.batch-size:50}") int batchSize,
            @Value("${outbox.publisher.claim-seconds:30}") long claimSeconds,
            @Value("${outbox.publisher.max-retries:5}") int maxRetries) {
        this.repository = repository;
        this.kafkaTemplate = kafkaTemplate;
        this.transactionTemplate = transactionTemplate;
        this.objectMapper = objectMapper;
        this.owner = owner;
        this.batchSize = batchSize;
        this.claimDuration = Duration.ofSeconds(claimSeconds);
        this.maxRetries = maxRetries;
    }

    @Scheduled(fixedDelayString = "${outbox.publisher.poll-millis:1000}")
    public void publishBatch() {
        for (ClaimedEvent event : claimBatch()) {
            publish(event);
        }
    }

    private List<ClaimedEvent> claimBatch() {
        return transactionTemplate.execute(status -> {
            LocalDateTime now = LocalDateTime.now();
            List<OutboxEvent> events = repository.findClaimable(now, PageRequest.of(0, batchSize));
            return events.stream().map(event -> {
                String token = UUID.randomUUID().toString();
                event.claim(token, owner, now, now.plus(claimDuration));
                return new ClaimedEvent(
                        event.getId(), event.getAggregateId(), event.getEventType(), event.getPayload(), token,
                        event.getRetryCount());
            }).toList();
        });
    }

    private void publish(ClaimedEvent event) {
        try {
            String message = message(event);
            kafkaTemplate.send(TOPIC, Long.toString(event.aggregateId()), message)
                    .get(5, TimeUnit.SECONDS);
            complete(event.id(), event.token());
        } catch (Exception exception) {
            fail(event.id(), event.token(), exception.getClass().getSimpleName());
            log.warn("Outbox publish failed. eventId={}, attempt={}", event.id(), event.retryCount() + 1);
        }
    }

    private String message(ClaimedEvent event) throws Exception {
        JsonNode payload = objectMapper.readTree(event.payload());
        ObjectNode envelope = objectMapper.createObjectNode();
        envelope.put("eventId", event.id());
        envelope.put("eventType", event.eventType());
        envelope.put("aggregateId", event.aggregateId());
        envelope.set("payload", payload);
        return objectMapper.writeValueAsString(envelope);
    }

    private void complete(long id, String token) {
        transactionTemplate.executeWithoutResult(status -> repository.findByIdForUpdate(id)
                .filter(event -> token.equals(event.getClaimToken()))
                .ifPresent(event -> event.markPublished(token, LocalDateTime.now())));
    }

    private void fail(long id, String token, String error) {
        transactionTemplate.executeWithoutResult(status -> repository.findByIdForUpdate(id)
                .filter(event -> token.equals(event.getClaimToken()))
                .ifPresent(event -> event.markFailed(token, error, maxRetries, LocalDateTime.now())));
    }

    private record ClaimedEvent(
            long id, long aggregateId, String eventType, String payload, String token, int retryCount) {
    }
}
