package com.ch6.cafe.domain.ranking.entity;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.Table;
import jakarta.persistence.UniqueConstraint;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "daily_menu_sales", uniqueConstraints = @UniqueConstraint(
        name = "uk_daily_menu_sales_date_menu", columnNames = {"sales_date", "menu_id"}))
public class DailyMenuSale {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(name = "sales_date", nullable = false, updatable = false)
    private LocalDate salesDate;

    @Column(name = "menu_id", nullable = false, updatable = false)
    private Long menuId;

    @Column(name = "order_count", nullable = false)
    private long orderCount;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected DailyMenuSale() {
    }

    public LocalDate getSalesDate() {
        return salesDate;
    }

    public Long getMenuId() {
        return menuId;
    }

    public long getOrderCount() {
        return orderCount;
    }
}
