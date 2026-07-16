package com.ch6.cafe.domain.point.entity;

import com.ch6.cafe.domain.point.exception.InsufficientPointException;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import jakarta.persistence.Version;
import java.time.LocalDateTime;

@Entity
@Table(name = "user_points", uniqueConstraints = @UniqueConstraint(name = "uk_user_points_user", columnNames = "user_id"))
public class UserPoint {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, updatable = false)
    private Long userId;

    @Column(nullable = false)
    private long balance;

    @Version
    @Column(nullable = false)
    private Long version;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected UserPoint() {
    }

    public UserPoint(Long userId, long balance) {
        if (userId == null || userId <= 0 || balance < 0) {
            throw new IllegalArgumentException("Point account data is invalid.");
        }
        this.userId = userId;
        this.balance = balance;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = this.createdAt;
    }

    public void charge(long amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Charge amount must be positive.");
        }
        balance = Math.addExact(balance, amount);
        updatedAt = LocalDateTime.now();
    }

    public void use(long amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Usage amount must be positive.");
        }
        if (balance < amount) {
            throw new InsufficientPointException();
        }
        balance -= amount;
        updatedAt = LocalDateTime.now();
    }

    public Long getUserId() {
        return userId;
    }

    public long getBalance() {
        return balance;
    }
}
