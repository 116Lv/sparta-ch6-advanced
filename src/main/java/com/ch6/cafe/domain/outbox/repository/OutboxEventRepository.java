package com.ch6.cafe.domain.outbox.repository;

import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import jakarta.persistence.LockModeType;
import jakarta.persistence.QueryHint;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.data.jpa.repository.QueryHints;

public interface OutboxEventRepository extends JpaRepository<OutboxEvent, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @QueryHints(@QueryHint(name = "jakarta.persistence.lock.timeout", value = "-2"))
    @Query("""
            select event from OutboxEvent event
            where event.status = com.ch6.cafe.domain.outbox.entity.OutboxStatus.READY
               or (event.status = com.ch6.cafe.domain.outbox.entity.OutboxStatus.PROCESSING
                   and event.claimUntil < :now)
            order by event.createdAt asc
            """)
    List<OutboxEvent> findClaimable(@Param("now") LocalDateTime now, Pageable pageable);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select event from OutboxEvent event where event.id = :id")
    Optional<OutboxEvent> findByIdForUpdate(@Param("id") Long id);
}
