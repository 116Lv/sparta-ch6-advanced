package com.ch6.cafe.domain.menu.controller;

import com.ch6.cafe.domain.menu.dto.response.MenuListResponse;
import com.ch6.cafe.domain.menu.service.MenuQueryService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/menus")
public class MenuController {

    private final MenuQueryService menuQueryService;

    public MenuController(MenuQueryService menuQueryService) {
        this.menuQueryService = menuQueryService;
    }

    @GetMapping
    public MenuListResponse getMenus() {
        return menuQueryService.getOnSaleMenus();
    }
}
