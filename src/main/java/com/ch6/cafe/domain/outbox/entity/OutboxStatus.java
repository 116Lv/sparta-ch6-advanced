package com.ch6.cafe.domain.outbox.entity;

public enum OutboxStatus {
    READY,
    PROCESSING,
    PUBLISHED,
    FAILED
}
