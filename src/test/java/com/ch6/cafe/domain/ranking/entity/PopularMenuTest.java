package com.ch6.cafe.domain.ranking.entity;

import static org.assertj.core.api.Assertions.assertThat;

import java.util.ArrayList;
import java.util.List;
import org.junit.jupiter.api.Test;

class PopularMenuTest {

    @Test
    void sortsByCountDescendingThenMenuIdAscending() {
        List<PopularMenu> menus = new ArrayList<>(List.of(
                new PopularMenu(3L, 10L), new PopularMenu(1L, 10L), new PopularMenu(2L, 11L)));
        menus.sort(PopularMenu.ORDERING);
        assertThat(menus).extracting(PopularMenu::menuId).containsExactly(2L, 1L, 3L);
    }
}
