package com.ch6.cafe.domain.outbox.entity;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.LocalDateTime;
import org.junit.jupiter.api.Test;

class OutboxEventTest {

    @Test
    void onlyCurrentClaimCanCompletePublication() {
        OutboxEvent event = OutboxEvent.orderPaid(10L, "{\"userId\":1}");
        LocalDateTime now = LocalDateTime.now();
        event.claim("token-a", "publisher-a", now, now.plusSeconds(30));
        assertThatThrownBy(() -> event.markPublished("token-b", now.plusSeconds(1)))
                .isInstanceOf(IllegalStateException.class);
        event.markPublished("token-a", now.plusSeconds(1));
        assertThat(event.getStatus()).isEqualTo(OutboxStatus.PUBLISHED);
        assertThat(event.getClaimToken()).isNull();
    }

    @Test
    void expiredProcessingClaimCanBeReclaimed() {
        OutboxEvent event = OutboxEvent.orderPaid(10L, "{\"userId\":1}");
        LocalDateTime now = LocalDateTime.now();
        event.claim("old", "publisher-a", now.minusMinutes(1), now.minusSeconds(1));
        event.claim("new", "publisher-b", now, now.plusSeconds(30));
        assertThat(event.getClaimToken()).isEqualTo("new");
    }
}
