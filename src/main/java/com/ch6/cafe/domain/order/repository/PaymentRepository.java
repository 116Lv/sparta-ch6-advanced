package com.ch6.cafe.domain.order.repository;

import com.ch6.cafe.domain.order.entity.Payment;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PaymentRepository extends JpaRepository<Payment, Long> {
}
