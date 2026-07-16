package com.ch6.cafe.domain.outbox.service;

import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import com.ch6.cafe.domain.outbox.entity.OutboxRecoveryAudit;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.outbox.repository.OutboxRecoveryAuditRepository;
import java.time.Clock;
import java.time.LocalDateTime;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OutboxRecoveryService {
    private final OutboxEventRepository eventRepository;
    private final OutboxRecoveryAuditRepository auditRepository;
    private final Clock clock;

    public OutboxRecoveryService(OutboxEventRepository eventRepository,
            OutboxRecoveryAuditRepository auditRepository, Clock clock) {
        this.eventRepository = eventRepository;
        this.auditRepository = auditRepository;
        this.clock = clock;
    }

    @Transactional
    public void requeueFailed(long eventId, String operator, String reason) {
        if (eventId <= 0) throw new IllegalArgumentException("Event ID must be positive.");
        if (operator == null || operator.isBlank()) throw new IllegalArgumentException("Operator must not be blank.");
        if (reason == null || reason.isBlank()) throw new IllegalArgumentException("Reason must not be blank.");
        OutboxEvent event = eventRepository.findByIdForUpdate(eventId)
                .orElseThrow(() -> new IllegalArgumentException("Outbox event was not found."));
        LocalDateTime now = LocalDateTime.now(clock);
        auditRepository.save(OutboxRecoveryAudit.capture(event, operator, reason, now));
        event.requeueFailed(now);
    }
}
