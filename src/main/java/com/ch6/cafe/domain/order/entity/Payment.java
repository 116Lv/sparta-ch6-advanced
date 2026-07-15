package com.ch6.cafe.domain.order.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.EnumType;
import jakarta.persistence.Enumerated;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.LocalDateTime;

@Entity
@Table(name = "payments", uniqueConstraints = @UniqueConstraint(name = "uk_payments_order", columnNames = "order_id"))
public class Payment {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "order_id", nullable = false, updatable = false)
    private Long orderId;

    @Column(name = "user_id", nullable = false, updatable = false)
    private Long userId;

    @Column(nullable = false, updatable = false)
    private long amount;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private PaymentStatus status;

    @Column(name = "paid_at", nullable = false, updatable = false)
    private LocalDateTime paidAt;

    protected Payment() {
    }

    public Payment(Long orderId, Long userId, long amount) {
        this.orderId = orderId;
        this.userId = userId;
        this.amount = amount;
        this.status = PaymentStatus.SUCCESS;
        this.paidAt = LocalDateTime.now();
    }
}
