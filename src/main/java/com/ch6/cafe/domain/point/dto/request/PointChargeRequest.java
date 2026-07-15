package com.ch6.cafe.domain.point.dto.request;

import jakarta.validation.constraints.Positive;

public record PointChargeRequest(@Positive long amount) {
}
