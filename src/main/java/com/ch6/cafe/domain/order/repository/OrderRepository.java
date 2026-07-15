package com.ch6.cafe.domain.order.repository;

import com.ch6.cafe.domain.order.entity.Order;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OrderRepository extends JpaRepository<Order, Long> {
}
