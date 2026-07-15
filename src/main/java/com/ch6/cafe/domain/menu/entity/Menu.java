package com.ch6.cafe.domain.menu.entity;

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
@Table(name = "menus")
public class Menu {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(nullable = false, length = 100)
    private String name;

    @Column(nullable = false)
    private long price;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private MenuStatus status;

    @Column(name = "created_at", nullable = false)
    private LocalDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private LocalDateTime updatedAt;

    protected Menu() {
    }

    public Menu(String name, long price, MenuStatus status) {
        if (name == null || name.isBlank() || price <= 0 || status == null) {
            throw new IllegalArgumentException("Menu data is invalid.");
        }
        this.name = name;
        this.price = price;
        this.status = status;
        this.createdAt = LocalDateTime.now();
        this.updatedAt = this.createdAt;
    }

    public Long getId() {
        return id;
    }

    public String getName() {
        return name;
    }

    public long getPrice() {
        return price;
    }

    public MenuStatus getStatus() {
        return status;
    }

    public boolean isOnSale() {
        return status == MenuStatus.ON_SALE;
    }
}
