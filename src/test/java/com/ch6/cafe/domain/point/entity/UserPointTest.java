package com.ch6.cafe.domain.point.entity;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import com.ch6.cafe.domain.point.exception.InsufficientPointException;
import org.junit.jupiter.api.Test;

class UserPointTest {

    @Test
    void chargesPositiveAmount() {
        UserPoint point = new UserPoint(1L, 1_000L);
        point.charge(500L);
        assertThat(point.getBalance()).isEqualTo(1_500L);
    }

    @Test
    void rejectsNonPositiveCharge() {
        UserPoint point = new UserPoint(1L, 1_000L);
        assertThatThrownBy(() -> point.charge(0L)).isInstanceOf(IllegalArgumentException.class);
    }

    @Test
    void neverAllowsNegativeBalance() {
        UserPoint point = new UserPoint(1L, 1_000L);
        assertThatThrownBy(() -> point.use(1_001L)).isInstanceOf(InsufficientPointException.class);
        assertThat(point.getBalance()).isEqualTo(1_000L);
    }
}
