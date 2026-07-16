package com.ch6.cafe.domain.outbox.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
public class OrderPaidAnalyticsId implements Serializable {
    @Column(name = "consumer_group", nullable = false, length = 100)
    private String consumerGroup;
    @Column(name = "event_id", nullable = false)
    private Long eventId;

    protected OrderPaidAnalyticsId() {
    }

    public OrderPaidAnalyticsId(String consumerGroup, Long eventId) {
        this.consumerGroup = consumerGroup;
        this.eventId = eventId;
    }

    public String getConsumerGroup() { return consumerGroup; }
    public Long getEventId() { return eventId; }

    @Override public boolean equals(Object object) {
        if (this == object) return true;
        if (!(object instanceof OrderPaidAnalyticsId other)) return false;
        return Objects.equals(consumerGroup, other.consumerGroup) && Objects.equals(eventId, other.eventId);
    }

    @Override public int hashCode() { return Objects.hash(consumerGroup, eventId); }
}
