package com.ch6.cafe.domain.order.dto.response;

import com.ch6.cafe.domain.order.entity.OrderStatus;

public record OrderResponse(
        long orderId,
        long userId,
        long menuId,
        long paymentAmount,
        long remainingPoint,
        OrderStatus status) {
}
