package com.ch6.cafe.domain.menu.dto.response;

import com.ch6.cafe.domain.menu.entity.Menu;

public record MenuResponse(long id, String name, long price) {

    public static MenuResponse from(Menu menu) {
        return new MenuResponse(menu.getId(), menu.getName(), menu.getPrice());
    }
}
