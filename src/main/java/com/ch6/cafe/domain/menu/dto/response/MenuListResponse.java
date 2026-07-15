package com.ch6.cafe.domain.menu.dto.response;

import java.util.List;

public record MenuListResponse(List<MenuResponse> menus) {

    public MenuListResponse {
        menus = List.copyOf(menus);
    }
}
