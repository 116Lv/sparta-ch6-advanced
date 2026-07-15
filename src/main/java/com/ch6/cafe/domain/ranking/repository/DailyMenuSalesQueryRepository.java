package com.ch6.cafe.domain.ranking.repository;

import java.time.LocalDate;
import java.util.List;

public interface DailyMenuSalesQueryRepository {

    List<MenuSalesAggregate> aggregateBetween(LocalDate from, LocalDate to);

    List<DailySalesMetadataProjection> summarizeBetween(LocalDate from, LocalDate to);
}
