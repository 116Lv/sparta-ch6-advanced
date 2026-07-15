package com.ch6.cafe.domain.ranking.repository;

public record DailySalesMetadata(long totalOrderCount, long menuCount) {

    public DailySalesMetadata {
        if (totalOrderCount < 0 || menuCount < 0) {
            throw new IllegalArgumentException("Daily sales metadata cannot be negative.");
        }
    }
}
