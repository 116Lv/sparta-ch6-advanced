package com.ch6.cafe.domain.order.controller;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ch6.cafe.domain.order.dto.response.OrderResponse;
import com.ch6.cafe.domain.order.entity.OrderStatus;
import com.ch6.cafe.domain.order.exception.MenuNotFoundException;
import com.ch6.cafe.domain.order.service.OrderPaymentService;
import com.ch6.cafe.domain.point.exception.InsufficientPointException;
import com.ch6.cafe.global.exception.GlobalExceptionHandler;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(OrderController.class)
@Import(GlobalExceptionHandler.class)
class OrderControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private OrderPaymentService orderPaymentService;

    @Test
    void returnsPaidOrderContract() throws Exception {
        when(orderPaymentService.order(1L, 10L)).thenReturn(
                new OrderResponse(100L, 1L, 10L, 4_500L, 10_500L, OrderStatus.PAID));

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"userId\":1,\"menuId\":10}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.orderId").value(100L))
                .andExpect(jsonPath("$.paymentAmount").value(4_500L))
                .andExpect(jsonPath("$.remainingPoint").value(10_500L))
                .andExpect(jsonPath("$.status").value("PAID"));
    }

    @Test
    void rejectsMissingAndNonPositiveIdentifiers() throws Exception {
        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"menuId\":10}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_REQUEST"));

        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"userId\":1,\"menuId\":0}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_REQUEST"));
    }

    @Test
    void returnsDocumentedBusinessErrors() throws Exception {
        when(orderPaymentService.order(1L, 10L)).thenThrow(new MenuNotFoundException());
        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"userId\":1,\"menuId\":10}"))
                .andExpect(status().isNotFound())
                .andExpect(jsonPath("$.error.code").value("MENU_NOT_FOUND"));

        when(orderPaymentService.order(1L, 11L)).thenThrow(new InsufficientPointException());
        mockMvc.perform(post("/api/v1/orders")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"userId\":1,\"menuId\":11}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error.code").value("INSUFFICIENT_POINT"));
    }
}
