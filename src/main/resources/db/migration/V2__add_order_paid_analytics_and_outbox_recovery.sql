CREATE TABLE order_paid_analytics (
    consumer_group VARCHAR(100) NOT NULL,
    event_id BIGINT NOT NULL,
    aggregate_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    menu_id BIGINT NOT NULL,
    payment_amount BIGINT NOT NULL,
    processed_at DATETIME NOT NULL,
    PRIMARY KEY (consumer_group, event_id),
    UNIQUE KEY uk_order_paid_analytics_group_aggregate (consumer_group, aggregate_id),
    INDEX idx_order_paid_analytics_group_processed (consumer_group, processed_at),
    CONSTRAINT chk_order_paid_analytics_event_positive CHECK (event_id > 0),
    CONSTRAINT chk_order_paid_analytics_aggregate_positive CHECK (aggregate_id > 0),
    CONSTRAINT chk_order_paid_analytics_user_positive CHECK (user_id > 0),
    CONSTRAINT chk_order_paid_analytics_menu_positive CHECK (menu_id > 0),
    CONSTRAINT chk_order_paid_analytics_payment_positive CHECK (payment_amount > 0)
);

CREATE TABLE outbox_recovery_audits (
    id BIGINT NOT NULL AUTO_INCREMENT,
    event_id BIGINT NOT NULL,
    operator_name VARCHAR(100) NOT NULL,
    reason VARCHAR(500) NOT NULL,
    previous_retry_count INT NOT NULL,
    previous_error VARCHAR(1000) NULL,
    recovered_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_outbox_recovery_event_recovered (event_id, recovered_at),
    CONSTRAINT chk_outbox_recovery_operator_nonblank CHECK (CHAR_LENGTH(TRIM(operator_name)) > 0),
    CONSTRAINT chk_outbox_recovery_reason_nonblank CHECK (CHAR_LENGTH(TRIM(reason)) > 0),
    CONSTRAINT chk_outbox_recovery_retry_nonnegative CHECK (previous_retry_count >= 0),
    CONSTRAINT fk_outbox_recovery_event FOREIGN KEY (event_id) REFERENCES outbox_events (id)
);
