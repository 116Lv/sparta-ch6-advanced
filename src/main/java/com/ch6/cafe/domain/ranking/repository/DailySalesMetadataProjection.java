package com.ch6.cafe.domain.ranking.repository;

import java.time.LocalDate;

public interface DailySalesMetadataProjection {

    LocalDate getSalesDate();

    Long getTotalOrderCount();

    Long getMenuCount();
}
