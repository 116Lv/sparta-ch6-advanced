package com.ch6.cafe.domain.ranking.repository;

import com.ch6.cafe.domain.ranking.entity.DailyMenuSale;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface DailyMenuSalesRepository
        extends JpaRepository<DailyMenuSale, Long>, DailyMenuSalesQueryRepository {

    @Modifying
    @Query(value = """
            INSERT INTO daily_menu_sales
                (sales_date, menu_id, order_count, created_at, updated_at)
            VALUES (:salesDate, :menuId, 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
            ON DUPLICATE KEY UPDATE
                order_count = order_count + 1,
                updated_at = CURRENT_TIMESTAMP
            """, nativeQuery = true)
    int increment(@Param("salesDate") LocalDate salesDate, @Param("menuId") Long menuId);

    List<DailyMenuSale> findAllBySalesDateBetween(LocalDate from, LocalDate to);

    Optional<DailyMenuSale> findBySalesDateAndMenuId(LocalDate salesDate, Long menuId);
}
