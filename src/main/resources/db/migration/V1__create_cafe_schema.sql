CREATE TABLE users (
    id BIGINT NOT NULL AUTO_INCREMENT,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id)
);

CREATE TABLE menus (
    id BIGINT NOT NULL AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,
    price BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT chk_menus_price_positive CHECK (price > 0),
    CONSTRAINT chk_menus_status CHECK (status IN ('ON_SALE', 'SOLD_OUT', 'DELETED'))
);

CREATE TABLE user_points (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    balance BIGINT NOT NULL,
    version BIGINT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_user_points_user UNIQUE (user_id),
    CONSTRAINT chk_user_points_balance_nonnegative CHECK (balance >= 0),
    CONSTRAINT fk_user_points_user FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE point_histories (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    type VARCHAR(20) NOT NULL,
    amount BIGINT NOT NULL,
    balance_after BIGINT NOT NULL,
    reason VARCHAR(100) NOT NULL,
    created_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_point_histories_user_created (user_id, created_at),
    CONSTRAINT chk_point_histories_amount_positive CHECK (amount > 0),
    CONSTRAINT chk_point_histories_balance_nonnegative CHECK (balance_after >= 0),
    CONSTRAINT fk_point_histories_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT chk_point_histories_type CHECK (type IN ('CHARGE', 'USE'))
);

CREATE TABLE orders (
    id BIGINT NOT NULL AUTO_INCREMENT,
    user_id BIGINT NOT NULL,
    menu_id BIGINT NOT NULL,
    order_price BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    ordered_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_orders_user_ordered (user_id, ordered_at),
    CONSTRAINT chk_orders_price_positive CHECK (order_price > 0),
    CONSTRAINT fk_orders_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT fk_orders_menu FOREIGN KEY (menu_id) REFERENCES menus (id),
    CONSTRAINT chk_orders_status CHECK (status IN ('PAID', 'CANCELED'))
);

CREATE TABLE payments (
    id BIGINT NOT NULL AUTO_INCREMENT,
    order_id BIGINT NOT NULL,
    user_id BIGINT NOT NULL,
    amount BIGINT NOT NULL,
    status VARCHAR(20) NOT NULL,
    paid_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_payments_order UNIQUE (order_id),
    CONSTRAINT chk_payments_amount_positive CHECK (amount > 0),
    CONSTRAINT fk_payments_order FOREIGN KEY (order_id) REFERENCES orders (id),
    CONSTRAINT fk_payments_user FOREIGN KEY (user_id) REFERENCES users (id),
    CONSTRAINT chk_payments_status CHECK (status IN ('SUCCESS', 'FAILED'))
);

CREATE TABLE daily_menu_sales (
    id BIGINT NOT NULL AUTO_INCREMENT,
    sales_date DATE NOT NULL,
    menu_id BIGINT NOT NULL,
    order_count BIGINT NOT NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    PRIMARY KEY (id),
    CONSTRAINT uk_daily_menu_sales_date_menu UNIQUE (sales_date, menu_id),
    CONSTRAINT chk_daily_menu_sales_count_nonnegative CHECK (order_count >= 0),
    CONSTRAINT fk_daily_menu_sales_menu FOREIGN KEY (menu_id) REFERENCES menus (id)
);

CREATE TABLE outbox_events (
    id BIGINT NOT NULL AUTO_INCREMENT,
    aggregate_type VARCHAR(50) NOT NULL,
    aggregate_id BIGINT NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    payload JSON NOT NULL,
    status VARCHAR(20) NOT NULL,
    retry_count INT NOT NULL,
    claim_token VARCHAR(100) NULL,
    claim_owner VARCHAR(100) NULL,
    claimed_at DATETIME NULL,
    claim_until DATETIME NULL,
    last_error VARCHAR(1000) NULL,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,
    published_at DATETIME NULL,
    PRIMARY KEY (id),
    INDEX idx_outbox_claim (status, claim_until, created_at),
    CONSTRAINT chk_outbox_retry_nonnegative CHECK (retry_count >= 0),
    CONSTRAINT fk_outbox_order FOREIGN KEY (aggregate_id) REFERENCES orders (id),
    CONSTRAINT uk_outbox_aggregate_event UNIQUE (aggregate_type, aggregate_id, event_type),
    CONSTRAINT chk_outbox_status CHECK (status IN ('READY', 'PROCESSING', 'PUBLISHED', 'FAILED'))
);

CREATE TABLE processed_events (
    consumer_group VARCHAR(100) NOT NULL,
    event_id BIGINT NOT NULL,
    processed_at DATETIME NOT NULL,
    PRIMARY KEY (consumer_group, event_id)
);
