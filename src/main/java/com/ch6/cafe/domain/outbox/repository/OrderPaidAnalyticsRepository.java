package com.ch6.cafe.domain.outbox.repository;

import com.ch6.cafe.domain.outbox.entity.OrderPaidAnalytics;
import com.ch6.cafe.domain.outbox.entity.OrderPaidAnalyticsId;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OrderPaidAnalyticsRepository extends JpaRepository<OrderPaidAnalytics, OrderPaidAnalyticsId> {
}
