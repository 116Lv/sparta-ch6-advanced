package com.ch6.cafe.domain.outbox.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "outbox_recovery_audits")
public class OutboxRecoveryAudit {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY) private Long id;
    @Column(name = "event_id", nullable = false, updatable = false) private Long eventId;
    @Column(name = "operator_name", nullable = false, length = 100, updatable = false) private String operator;
    @Column(nullable = false, length = 500, updatable = false) private String reason;
    @Column(name = "previous_retry_count", nullable = false, updatable = false) private int previousRetryCount;
    @Column(name = "previous_error", length = 1000, updatable = false) private String previousError;
    @Column(name = "recovered_at", nullable = false, updatable = false) private LocalDateTime recoveredAt;

    protected OutboxRecoveryAudit() {
    }

    public static OutboxRecoveryAudit capture(OutboxEvent event, String operator, String reason, LocalDateTime now) {
        OutboxRecoveryAudit audit = new OutboxRecoveryAudit();
        audit.eventId = event.getId();
        audit.operator = operator;
        audit.reason = reason;
        audit.previousRetryCount = event.getRetryCount();
        audit.previousError = event.getLastError();
        audit.recoveredAt = now;
        return audit;
    }

    public Long getEventId() { return eventId; }
    public String getOperator() { return operator; }
    public String getReason() { return reason; }
    public int getPreviousRetryCount() { return previousRetryCount; }
    public String getPreviousError() { return previousError; }
    public LocalDateTime getRecoveredAt() { return recoveredAt; }
}
