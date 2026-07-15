package com.ch6.cafe.domain.outbox.service;

public record OrderPaidMessage(
        long eventId, String eventType, long aggregateId, long userId, long menuId, long paymentAmount) {

    public OrderPaidMessage {
        if (eventId <= 0 || aggregateId <= 0 || userId <= 0 || menuId <= 0
                || paymentAmount <= 0 || !"ORDER_PAID".equals(eventType)) {
            throw new IllegalArgumentException("ORDER_PAID event contract is invalid.");
        }
    }
}
