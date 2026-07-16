package com.ch6.cafe.domain.outbox.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Embeddable;
import java.io.Serializable;
import java.util.Objects;

@Embeddable
public class ProcessedEventId implements Serializable {

    @Column(name = "consumer_group", nullable = false, length = 100)
    private String consumerGroup;

    @Column(name = "event_id", nullable = false)
    private Long eventId;

    protected ProcessedEventId() {
    }

    public ProcessedEventId(String consumerGroup, Long eventId) {
        this.consumerGroup = consumerGroup;
        this.eventId = eventId;
    }

    @Override
    public boolean equals(Object object) {
        if (this == object) return true;
        if (!(object instanceof ProcessedEventId other)) return false;
        return Objects.equals(consumerGroup, other.consumerGroup) && Objects.equals(eventId, other.eventId);
    }

    @Override
    public int hashCode() {
        return Objects.hash(consumerGroup, eventId);
    }
}
