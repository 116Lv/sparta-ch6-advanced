package com.ch6.cafe.domain.ranking.controller;

import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ch6.cafe.domain.ranking.service.PopularMenuQueryService;
import com.ch6.cafe.global.exception.GlobalExceptionHandler;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(PopularMenuController.class)
@Import(GlobalExceptionHandler.class)
class PopularMenuControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private PopularMenuQueryService queryService;

    @Test
    void returnsInvalidRequestWhenDaysIsNotNumeric() throws Exception {
        mockMvc.perform(get("/api/v1/menus/popular")
                        .param("days", "abc")
                        .param("limit", "3"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_REQUEST"));
    }
}
