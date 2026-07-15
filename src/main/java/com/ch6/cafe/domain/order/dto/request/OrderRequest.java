package com.ch6.cafe.domain.order.dto.request;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

public record OrderRequest(
        @NotNull @Positive Long userId,
        @NotNull @Positive Long menuId) {
}
