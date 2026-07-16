package com.ch6.cafe.domain.menu.controller;

import static org.mockito.Mockito.when;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.get;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.jsonPath;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.status;

import com.ch6.cafe.domain.menu.dto.response.MenuListResponse;
import com.ch6.cafe.domain.menu.dto.response.MenuResponse;
import com.ch6.cafe.domain.menu.service.MenuQueryService;
import com.ch6.cafe.global.exception.GlobalExceptionHandler;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.webmvc.test.autoconfigure.WebMvcTest;
import org.springframework.context.annotation.Import;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.test.web.servlet.MockMvc;

@WebMvcTest(MenuController.class)
@Import(GlobalExceptionHandler.class)
class MenuControllerTest {

    @Autowired
    private MockMvc mockMvc;

    @MockitoBean
    private MenuQueryService menuQueryService;

    @Test
    void returnsOnSaleMenuContract() throws Exception {
        when(menuQueryService.getOnSaleMenus()).thenReturn(
                new MenuListResponse(List.of(new MenuResponse(1L, "Americano", 4_500L))));

        mockMvc.perform(get("/api/v1/menus"))
                .andExpect(status().isOk())
                .andExpect(jsonPath("$.menus[0].id").value(1L))
                .andExpect(jsonPath("$.menus[0].name").value("Americano"))
                .andExpect(jsonPath("$.menus[0].price").value(4_500L));
    }

    @Test
    void mapsUnexpectedMenuQueryFailureToDocumentedInternalError() throws Exception {
        when(menuQueryService.getOnSaleMenus()).thenThrow(new IllegalStateException("database unavailable"));

        mockMvc.perform(get("/api/v1/menus"))
                .andExpect(status().isInternalServerError())
                .andExpect(jsonPath("$.error.code").value("INTERNAL_ERROR"));
    }
}
