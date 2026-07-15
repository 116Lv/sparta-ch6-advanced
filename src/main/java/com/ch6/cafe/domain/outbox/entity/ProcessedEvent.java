package com.ch6.cafe.domain.outbox.entity;

import jakarta.persistence.Column;
import jakarta.persistence.EmbeddedId;
import jakarta.persistence.Entity;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "processed_events")
public class ProcessedEvent {

    @EmbeddedId
    private ProcessedEventId id;

    @Column(name = "processed_at", nullable = false, updatable = false)
    private LocalDateTime processedAt;

    protected ProcessedEvent() {
    }
}
