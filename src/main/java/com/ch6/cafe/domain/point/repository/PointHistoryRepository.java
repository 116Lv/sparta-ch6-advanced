package com.ch6.cafe.domain.point.repository;

import com.ch6.cafe.domain.point.entity.PointHistory;
import org.springframework.data.jpa.repository.JpaRepository;

public interface PointHistoryRepository extends JpaRepository<PointHistory, Long> {
}
