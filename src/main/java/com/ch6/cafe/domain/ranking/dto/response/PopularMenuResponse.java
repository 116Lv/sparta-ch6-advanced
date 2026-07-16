package com.ch6.cafe.domain.ranking.dto.response;

import java.util.List;

public record PopularMenuResponse(int periodDays, List<MenuItem> menus) {

    public PopularMenuResponse {
        menus = List.copyOf(menus);
    }

    public record MenuItem(long menuId, String name, long price, long orderCount) {
    }
}
