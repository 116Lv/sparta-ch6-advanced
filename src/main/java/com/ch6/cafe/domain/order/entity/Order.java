package com.ch6.cafe.domain.order.entity;

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
@Table(name = "orders")
public class Order {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "user_id", nullable = false, updatable = false)
    private Long userId;

    @Column(name = "menu_id", nullable = false, updatable = false)
    private Long menuId;

    @Column(name = "order_price", nullable = false, updatable = false)
    private long orderPrice;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private OrderStatus status;

    @Column(name = "ordered_at", nullable = false, updatable = false)
    private LocalDateTime orderedAt;

    protected Order() {
    }

    public Order(Long userId, Long menuId, long orderPrice, LocalDateTime orderedAt) {
        this.userId = userId;
        this.menuId = menuId;
        this.orderPrice = orderPrice;
        this.status = OrderStatus.PAID;
        this.orderedAt = orderedAt;
    }

    public Long getId() {
        return id;
    }

    public Long getUserId() {
        return userId;
    }

    public Long getMenuId() {
        return menuId;
    }

    public long getOrderPrice() {
        return orderPrice;
    }

    public OrderStatus getStatus() {
        return status;
    }

    public LocalDateTime getOrderedAt() {
        return orderedAt;
    }
}
