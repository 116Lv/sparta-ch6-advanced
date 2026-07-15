package com.ch6.cafe.domain.outbox.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import java.time.LocalDateTime;

@Entity
@Table(name = "outbox_events")
public class OutboxEvent {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "aggregate_type", nullable = false, length = 50, updatable = false)
    private String aggregateType;

    @Column(name = "aggregate_id", nullable = false, updatable = false)
    private Long aggregateId;

    @Column(name = "event_type", nullable = false, length = 100, updatable = false)
    private String eventType;

    @Column(nullable = false, columnDefinition = "json", updatable = false)
    private String payload;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private OutboxStatus status;

    @Column(name = "retry_count", nullable = false)
    private int retryCount;

    @Column(name = "claim_token", length = 100)
    private String claimToken;

    @Column(name = "claim_owner", length = 100)
    private String claimOwner;

    @Column(name = "claimed_at")
    private LocalDateTime claimedAt;

    @Column(name = "claim_until")
    private LocalDateTime claimUntil;

    @Column(name = "last_error", length = 1000)
    private String lastError;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    @Column(name = "published_at")
    private LocalDateTime publishedAt;

    protected OutboxEvent() {
    }

    private OutboxEvent(Long aggregateId, String payload) {
        this.aggregateType = "ORDER";
        this.aggregateId = aggregateId;
        this.eventType = "ORDER_PAID";
        this.payload = payload;
        this.status = OutboxStatus.READY;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = this.createdAt;
    }

    public static OutboxEvent orderPaid(Long orderId, String payload) {
        return new OutboxEvent(orderId, payload);
    }

    public void claim(String token, String owner, LocalDateTime now, LocalDateTime until) {
        boolean ready = status == OutboxStatus.READY;
        boolean expired = status == OutboxStatus.PROCESSING
                && claimUntil != null
                && claimUntil.isBefore(now);
        if (!ready && !expired) {
            throw new IllegalStateException("Outbox event is not claimable.");
        }
        this.status = OutboxStatus.PROCESSING;
        this.claimToken = token;
        this.claimOwner = owner;
        this.claimedAt = now;
        this.claimUntil = until;
        this.updatedAt = now;
    }

    public void markPublished(String token, LocalDateTime now) {
        requireCurrentClaim(token);
        this.status = OutboxStatus.PUBLISHED;
        this.publishedAt = now;
        this.lastError = null;
        clearClaim(now);
    }

    public void markFailed(String token, String error, int maxRetries, LocalDateTime now) {
        requireCurrentClaim(token);
        this.retryCount++;
        this.status = retryCount >= maxRetries ? OutboxStatus.FAILED : OutboxStatus.READY;
        this.lastError = error;
        clearClaim(now);
    }

    private void requireCurrentClaim(String token) {
        if (status != OutboxStatus.PROCESSING || token == null || !token.equals(claimToken)) {
            throw new IllegalStateException("Outbox claim token is stale.");
        }
    }

    private void clearClaim(LocalDateTime now) {
        this.claimToken = null;
        this.claimOwner = null;
        this.claimedAt = null;
        this.claimUntil = null;
        this.updatedAt = now;
    }

    public Long getId() {
        return id;
    }

    public Long getAggregateId() {
        return aggregateId;
    }

    public String getEventType() {
        return eventType;
    }

    public String getPayload() {
        return payload;
    }

    public OutboxStatus getStatus() {
        return status;
    }

    public String getClaimToken() {
        return claimToken;
    }

    public int getRetryCount() {
        return retryCount;
    }
}
