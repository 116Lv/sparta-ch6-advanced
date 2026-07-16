package com.ch6.cafe.domain.ranking.controller;

import com.ch6.cafe.domain.ranking.dto.response.PopularMenuResponse;
import com.ch6.cafe.domain.ranking.service.PopularMenuQueryService;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/menus/popular")
public class PopularMenuController {

    private final PopularMenuQueryService queryService;

    public PopularMenuController(PopularMenuQueryService queryService) {
        this.queryService = queryService;
    }

    @GetMapping
    public PopularMenuResponse getPopularMenus(
            @RequestParam(defaultValue = "7") int days,
            @RequestParam(defaultValue = "3") int limit) {
        return queryService.getPopularMenus(days, limit);
    }
}
