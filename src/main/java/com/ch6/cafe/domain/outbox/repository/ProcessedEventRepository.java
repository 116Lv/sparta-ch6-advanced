package com.ch6.cafe.domain.outbox.repository;

import com.ch6.cafe.domain.outbox.entity.ProcessedEvent;
import com.ch6.cafe.domain.outbox.entity.ProcessedEventId;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface ProcessedEventRepository extends JpaRepository<ProcessedEvent, ProcessedEventId> {

    @Modifying
    @Query(value = """
            INSERT IGNORE INTO processed_events (event_id, consumer_group, processed_at)
            VALUES (:eventId, :consumerGroup, CURRENT_TIMESTAMP)
            """, nativeQuery = true)
    int markProcessed(@Param("eventId") long eventId, @Param("consumerGroup") String consumerGroup);
}
