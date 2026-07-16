package com.ch6.cafe.domain.point.controller;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.post;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ch6.cafe.domain.point.dto.response.PointChargeResponse;
import com.ch6.cafe.domain.point.service.PointChargeService;
import com.ch6.cafe.global.exception.GlobalExceptionHandler;
import com.ch6.cafe.global.lock.LockTimeoutException;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.http.MediaType;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(PointController.class)
@Import(GlobalExceptionHandler.class)
class PointControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private PointChargeService pointChargeService;

    @Test
    void chargesPositiveAmountUsingPathUserId() throws Exception {
        when(pointChargeService.charge(1L, 10_000L))
                .thenReturn(new PointChargeResponse(1L, 10_000L, 15_000L));

        mockMvc.perform(post("/api/v1/users/1/points/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":10000}"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.userId").value(1L))
                .andExpect(jsonPath("$.chargedAmount").value(10_000L))
                .andExpect(jsonPath("$.balance").value(15_000L));
    }

    @Test
    void rejectsNonPositiveAmountAndMalformedUserId() throws Exception {
        mockMvc.perform(post("/api/v1/users/1/points/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":0}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_REQUEST"));

        mockMvc.perform(post("/api/v1/users/not-a-number/points/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":10000}"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_REQUEST"));
    }

    @Test
    void returnsDocumentedLockTimeoutError() throws Exception {
        when(pointChargeService.charge(1L, 10_000L)).thenThrow(new LockTimeoutException());

        mockMvc.perform(post("/api/v1/users/1/points/charge")
                        .contentType(MediaType.APPLICATION_JSON)
                        .content("{\"amount\":10000}"))
                .andExpect(status().isConflict())
                .andExpect(jsonPath("$.error.code").value("LOCK_TIMEOUT"));
    }
}
