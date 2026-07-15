package com.ch6.cafe.domain.point.entity;

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
@Table(name = "point_histories")
public class PointHistory {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, updatable = false)
    private Long userId;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20, updatable = false)
    private PointHistoryType type;

    @Column(nullable = false, updatable = false)
    private long amount;

    @Column(name = "balance_after", nullable = false, updatable = false)
    private long balanceAfter;

    @Column(nullable = false, length = 100, updatable = false)
    private String reason;

    @Column(name = "created_at", nullable = false, updatable = false)
    private LocalDateTime createdAt;

    protected PointHistory() {
    }

    private PointHistory(Long userId, PointHistoryType type, long amount, long balanceAfter, String reason) {
        this.userId = userId;
        this.type = type;
        this.amount = amount;
        this.balanceAfter = balanceAfter;
        this.reason = reason;
        this.createdAt = LocalDateTime.now();
    }

    public static PointHistory charge(Long userId, long amount, long balanceAfter) {
        return new PointHistory(userId, PointHistoryType.CHARGE, amount, balanceAfter, "POINT_CHARGE");
    }

    public static PointHistory use(Long userId, long amount, long balanceAfter) {
        return new PointHistory(userId, PointHistoryType.USE, amount, balanceAfter, "ORDER_PAYMENT");
    }

    public Long getUserId() {
        return userId;
    }

    public PointHistoryType getType() {
        return type;
    }

    public long getAmount() {
        return amount;
    }

    public long getBalanceAfter() {
        return balanceAfter;
    }
}
