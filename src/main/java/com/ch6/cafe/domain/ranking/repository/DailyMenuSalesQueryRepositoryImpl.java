package com.ch6.cafe.domain.ranking.repository;

import static com.ch6.cafe.domain.ranking.entity.QDailyMenuSale.dailyMenuSale;

import com.querydsl.core.types.dsl.NumberExpression;
import com.querydsl.jpa.impl.JPAQueryFactory;
import java.time.LocalDate;
import java.util.List;

public class DailyMenuSalesQueryRepositoryImpl implements DailyMenuSalesQueryRepository {

    private final JPAQueryFactory queryFactory;

    public DailyMenuSalesQueryRepositoryImpl(JPAQueryFactory queryFactory) {
        this.queryFactory = queryFactory;
    }

    @Override
    public List<MenuSalesAggregate> aggregateBetween(LocalDate from, LocalDate to) {
        NumberExpression<Long> totalOrderCount = dailyMenuSale.orderCount.sum();

        return queryFactory
                .select(dailyMenuSale.menuId, totalOrderCount)
                .from(dailyMenuSale)
                .where(dailyMenuSale.salesDate.between(from, to))
                .groupBy(dailyMenuSale.menuId)
                .fetch()
                .stream()
                .<MenuSalesAggregate>map(tuple -> new MenuSalesAggregateResult(
                        tuple.get(dailyMenuSale.menuId),
                        tuple.get(totalOrderCount)))
                .toList();
    }

    @Override
    public List<DailySalesMetadataProjection> summarizeBetween(LocalDate from, LocalDate to) {
        NumberExpression<Long> totalOrderCount = dailyMenuSale.orderCount.sum();
        NumberExpression<Long> menuCount = dailyMenuSale.count();

        return queryFactory
                .select(
                        dailyMenuSale.salesDate,
                        totalOrderCount,
                        menuCount)
                .from(dailyMenuSale)
                .where(dailyMenuSale.salesDate.between(from, to))
                .groupBy(dailyMenuSale.salesDate)
                .fetch()
                .stream()
                .<DailySalesMetadataProjection>map(tuple -> new DailySalesMetadataResult(
                        tuple.get(dailyMenuSale.salesDate),
                        tuple.get(totalOrderCount),
                        tuple.get(menuCount)))
                .toList();
    }

    private record MenuSalesAggregateResult(Long menuId, Long orderCount)
            implements MenuSalesAggregate {

        @Override
        public Long getMenuId() {
            return menuId;
        }

        @Override
        public Long getOrderCount() {
            return orderCount;
        }
    }

    private record DailySalesMetadataResult(LocalDate salesDate, Long totalOrderCount, Long menuCount)
            implements DailySalesMetadataProjection {

        @Override
        public LocalDate getSalesDate() {
            return salesDate;
        }

        @Override
        public Long getTotalOrderCount() {
            return totalOrderCount;
        }

        @Override
        public Long getMenuCount() {
            return menuCount;
        }
    }
}
