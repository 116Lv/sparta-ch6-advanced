package com.ch6.cafe.domain.order.controller;

import com.ch6.cafe.domain.order.dto.request.OrderRequest;
import com.ch6.cafe.domain.order.dto.response.OrderResponse;
import com.ch6.cafe.domain.order.service.OrderPaymentService;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final OrderPaymentService orderPaymentService;

    public OrderController(OrderPaymentService orderPaymentService) {
        this.orderPaymentService = orderPaymentService;
    }

    @PostMapping
    public OrderResponse order(@Valid @RequestBody OrderRequest request) {
        return orderPaymentService.order(request.userId(), request.menuId());
    }
}
