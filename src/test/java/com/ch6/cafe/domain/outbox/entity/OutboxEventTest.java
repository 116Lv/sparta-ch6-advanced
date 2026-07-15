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

    @Test
    void fifthFailureBecomesPermanentAndEarlierFailuresReturnReady() {
        OutboxEvent event = OutboxEvent.orderPaid(10L, "{\"userId\":1}");
        LocalDateTime now = LocalDateTime.now();
        for (int attempt = 1; attempt <= 5; attempt++) {
            String token = "token-" + attempt;
            event.claim(token, "publisher", now.plusSeconds(attempt), now.plusSeconds(attempt + 30));
            event.markFailed(token, "broker unavailable", 5, now.plusSeconds(attempt + 1));
            assertThat(event.getRetryCount()).isEqualTo(attempt);
            assertThat(event.getStatus()).isEqualTo(attempt < 5 ? OutboxStatus.READY : OutboxStatus.FAILED);
            assertThat(event.getClaimToken()).isNull();
        }
    }

    @Test
    void onlyFailedEventCanBeRequeuedAndRecoveryClearsTransientFailureState() {
        OutboxEvent ready = OutboxEvent.orderPaid(10L, "{\"userId\":1}");
        assertThatThrownBy(() -> ready.requeueFailed(LocalDateTime.now()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessage("Only FAILED events can be requeued.");

        LocalDateTime now = LocalDateTime.now();
        ready.claim("token", "publisher", now, now.plusSeconds(30));
        ready.markFailed("token", "permanent", 1, now.plusSeconds(1));
        ready.requeueFailed(now.plusSeconds(2));

        assertThat(ready.getStatus()).isEqualTo(OutboxStatus.READY);
        assertThat(ready.getRetryCount()).isZero();
        assertThat(ready.getClaimToken()).isNull();
        assertThat(ready.getClaimOwner()).isNull();
        assertThat(ready.getClaimedAt()).isNull();
        assertThat(ready.getClaimUntil()).isNull();
        assertThat(ready.getLastError()).isNull();
    }
}
