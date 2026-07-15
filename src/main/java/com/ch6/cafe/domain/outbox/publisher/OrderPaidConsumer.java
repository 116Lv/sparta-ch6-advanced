package com.ch6.cafe.domain.outbox.publisher;

import com.ch6.cafe.domain.outbox.service.OrderPaidAnalyticsService;
import com.ch6.cafe.domain.outbox.service.OrderPaidMessage;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class OrderPaidConsumer {

    private final OrderPaidAnalyticsService analyticsService;
    private final ObjectMapper objectMapper;
    private final String consumerGroup;

    public OrderPaidConsumer(
            OrderPaidAnalyticsService analyticsService,
            ObjectMapper objectMapper,
            @Value("${spring.kafka.consumer.group-id:coffee-order-analytics}") String consumerGroup) {
        this.analyticsService = analyticsService;
        this.objectMapper = objectMapper;
        this.consumerGroup = consumerGroup;
    }

    @KafkaListener(topics = "coffee.order.paid", groupId = "${spring.kafka.consumer.group-id:coffee-order-analytics}")
    public void consume(String message) throws Exception {
        JsonNode event = objectMapper.readTree(message);
        if (event == null || !event.isObject()) {
            throw new IllegalArgumentException("ORDER_PAID event contract is invalid.");
        }
        JsonNode payload = event.path("payload");
        long eventId = positiveLong(event.path("eventId"));
        long aggregateId = positiveLong(event.path("aggregateId"));
        long userId = positiveLong(payload.path("userId"));
        long menuId = positiveLong(payload.path("menuId"));
        long paymentAmount = positiveLong(payload.path("paymentAmount"));
        String eventType = event.path("eventType").textValue();
        if (eventId <= 0 || aggregateId <= 0 || userId <= 0 || menuId <= 0 || paymentAmount <= 0
                || !"ORDER_PAID".equals(eventType)) {
            throw new IllegalArgumentException("ORDER_PAID event contract is invalid.");
        }
        analyticsService.apply(consumerGroup,
                new OrderPaidMessage(eventId, eventType, aggregateId, userId, menuId, paymentAmount));
    }

    private long positiveLong(JsonNode value) {
        return value.isIntegralNumber() && value.canConvertToLong() ? value.longValue() : 0;
    }

}
