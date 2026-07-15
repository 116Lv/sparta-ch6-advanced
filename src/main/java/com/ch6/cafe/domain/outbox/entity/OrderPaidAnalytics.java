package com.ch6.cafe.domain.outbox.entity;

import com.ch6.cafe.domain.outbox.service.OrderPaidMessage;
import jakarta.persistence.Column;
import jakarta.persistence.EmbeddedId;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "order_paid_analytics")
public class OrderPaidAnalytics {
    @EmbeddedId private OrderPaidAnalyticsId id;
    @Column(name = "aggregate_id", nullable = false, updatable = false) private Long aggregateId;
    @Column(name = "user_id", nullable = false, updatable = false) private Long userId;
    @Column(name = "menu_id", nullable = false, updatable = false) private Long menuId;
    @Column(name = "payment_amount", nullable = false, updatable = false) private Long paymentAmount;
    @Column(name = "processed_at", nullable = false, updatable = false) private LocalDateTime processedAt;

    protected OrderPaidAnalytics() {
    }

    public static OrderPaidAnalytics from(String consumerGroup, OrderPaidMessage message, LocalDateTime now) {
        OrderPaidAnalytics analytics = new OrderPaidAnalytics();
        analytics.id = new OrderPaidAnalyticsId(consumerGroup, message.eventId());
        analytics.aggregateId = message.aggregateId();
        analytics.userId = message.userId();
        analytics.menuId = message.menuId();
        analytics.paymentAmount = message.paymentAmount();
        analytics.processedAt = now;
        return analytics;
    }

    public OrderPaidAnalyticsId getId() { return id; }
    public Long getAggregateId() { return aggregateId; }
    public Long getUserId() { return userId; }
    public Long getMenuId() { return menuId; }
    public Long getPaymentAmount() { return paymentAmount; }
    public LocalDateTime getProcessedAt() { return processedAt; }
}
