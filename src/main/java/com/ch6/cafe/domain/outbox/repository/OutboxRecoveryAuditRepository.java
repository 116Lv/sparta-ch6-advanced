package com.ch6.cafe.domain.outbox.repository;

import com.ch6.cafe.domain.outbox.entity.OutboxRecoveryAudit;
import org.springframework.data.jpa.repository.JpaRepository;

public interface OutboxRecoveryAuditRepository extends JpaRepository<OutboxRecoveryAudit, Long> {
}
