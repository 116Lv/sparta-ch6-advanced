package com.ch6.cafe.domain.ranking.controller;

import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ch6.cafe.domain.ranking.dto.response.PopularMenuResponse;
import com.ch6.cafe.domain.ranking.service.PopularMenuQueryService;
import com.ch6.cafe.global.exception.GlobalExceptionHandler;
import java.util.List;
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
    void appliesDocumentedDefaultsAndReturnsPopularMenuContract() throws Exception {
        when(queryService.getPopularMenus(7, 3)).thenReturn(new PopularMenuResponse(
                7, List.of(new PopularMenuResponse.MenuItem(10L, "Americano", 4_500L, 120L))));

        mockMvc.perform(get("/api/v1/menus/popular"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.periodDays").value(7))
                .andExpect(jsonPath("$.menus[0].menuId").value(10L))
                .andExpect(jsonPath("$.menus[0].orderCount").value(120L));
        verify(queryService).getPopularMenus(7, 3);
    }

    @Test
    void returnsInvalidRequestWhenDaysIsNotNumeric() throws Exception {
        mockMvc.perform(get("/api/v1/menus/popular")
                        .param("days", "abc")
                        .param("limit", "3"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_REQUEST"));
    }

    @Test
    void returnsInvalidRequestForNonCanonicalRange() throws Exception {
        when(queryService.getPopularMenus(6, 3))
                .thenThrow(new IllegalArgumentException("Only days=7 and limit=3 are supported."));

        mockMvc.perform(get("/api/v1/menus/popular")
                        .param("days", "6")
                        .param("limit", "3"))
                .andExpect(status().isBadRequest())
                .andExpect(jsonPath("$.error.code").value("INVALID_REQUEST"));
    }
}
