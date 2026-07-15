package com.ch6.cafe.domain.outbox.service;

import com.ch6.cafe.domain.outbox.entity.OrderPaidAnalytics;
import com.ch6.cafe.domain.outbox.repository.OrderPaidAnalyticsRepository;
import com.ch6.cafe.domain.outbox.repository.ProcessedEventRepository;
import java.time.Clock;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderPaidAnalyticsService {
    private final ProcessedEventRepository processedEventRepository;
    private final OrderPaidAnalyticsRepository analyticsRepository;
    private final Clock clock;

    public OrderPaidAnalyticsService(ProcessedEventRepository processedEventRepository,
            OrderPaidAnalyticsRepository analyticsRepository, Clock clock) {
        this.processedEventRepository = processedEventRepository;
        this.analyticsRepository = analyticsRepository;
        this.clock = clock;
    }

    @Transactional
    public boolean apply(String consumerGroup, OrderPaidMessage message) {
        if (consumerGroup == null || consumerGroup.isBlank()) {
            throw new IllegalArgumentException("Consumer group must not be blank.");
        }
        int inserted = processedEventRepository.markProcessed(message.eventId(), consumerGroup);
        if (inserted == 0) return false;
        analyticsRepository.saveAndFlush(OrderPaidAnalytics.from(consumerGroup, message, LocalDateTime.now(clock)));
        return true;
    }
}
