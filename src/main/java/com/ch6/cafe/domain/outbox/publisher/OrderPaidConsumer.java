package com.ch6.cafe.domain.outbox.publisher;

import com.ch6.cafe.domain.outbox.repository.ProcessedEventRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
public class OrderPaidConsumer {

    private final ProcessedEventRepository processedEventRepository;
    private final ObjectMapper objectMapper;
    private final String consumerGroup;

    public OrderPaidConsumer(
            ProcessedEventRepository processedEventRepository,
            ObjectMapper objectMapper,
            @Value("${spring.kafka.consumer.group-id:coffee-order-analytics}") String consumerGroup) {
        this.processedEventRepository = processedEventRepository;
        this.objectMapper = objectMapper;
        this.consumerGroup = consumerGroup;
    }

    @KafkaListener(topics = "coffee.order.paid", groupId = "${spring.kafka.consumer.group-id:coffee-order-analytics}")
    @Transactional
    public void consume(String message) throws Exception {
        JsonNode event = objectMapper.readTree(message);
        long eventId = event.path("eventId").longValue();
        long aggregateId = event.path("aggregateId").longValue();
        String eventType = event.path("eventType").textValue();
        if (eventId <= 0 || aggregateId <= 0 || !"ORDER_PAID".equals(eventType)
                || event.path("payload").isMissingNode()) {
            throw new IllegalArgumentException("ORDER_PAID event contract is invalid.");
        }
        boolean firstDelivery = processedEventRepository.markProcessed(eventId, consumerGroup) == 1;
        if (!firstDelivery) {
            return;
        }
    }
}
