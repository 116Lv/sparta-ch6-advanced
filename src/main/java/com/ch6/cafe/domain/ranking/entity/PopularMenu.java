package com.ch6.cafe.domain.ranking.entity;

import java.util.Comparator;

public record PopularMenu(long menuId, long orderCount) {

    public static final Comparator<PopularMenu> ORDERING =
            Comparator.comparingLong(PopularMenu::orderCount).reversed()
                    .thenComparingLong(PopularMenu::menuId);
}
