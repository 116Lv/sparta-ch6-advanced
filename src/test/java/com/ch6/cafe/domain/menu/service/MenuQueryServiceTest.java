package com.ch6.cafe.domain.menu.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.menu.dto.response.MenuListResponse;
import com.ch6.cafe.domain.menu.dto.response.MenuResponse;
import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import java.util.List;
import org.junit.jupiter.api.Test;
import org.springframework.test.util.ReflectionTestUtils;

class MenuQueryServiceTest {

    private final MenuRepository menuRepository = mock(MenuRepository.class);
    private final MenuQueryService menuQueryService = new MenuQueryService(menuRepository);

    @Test
    void requestsOnSaleMenusAndMapsRepositoryOrder() {
        Menu latte = menu(30L, "Latte", 5500L);
        Menu americano = menu(10L, "Americano", 4500L);
        when(menuRepository.findAllByStatusOrderByIdAsc(MenuStatus.ON_SALE))
                .thenReturn(List.of(latte, americano));

        MenuListResponse response = menuQueryService.getOnSaleMenus();

        assertThat(response.menus()).containsExactly(
                new MenuResponse(30L, "Latte", 5500L),
                new MenuResponse(10L, "Americano", 4500L));
        verify(menuRepository).findAllByStatusOrderByIdAsc(MenuStatus.ON_SALE);
    }

    @Test
    void returnsEmptyMenusWhenRepositoryHasNoOnSaleMenus() {
        when(menuRepository.findAllByStatusOrderByIdAsc(MenuStatus.ON_SALE))
                .thenReturn(List.of());

        MenuListResponse response = menuQueryService.getOnSaleMenus();

        assertThat(response.menus()).isEmpty();
        verify(menuRepository).findAllByStatusOrderByIdAsc(MenuStatus.ON_SALE);
    }

    private Menu menu(long id, String name, long price) {
        Menu menu = new Menu(name, price, MenuStatus.ON_SALE);
        ReflectionTestUtils.setField(menu, "id", id);
        return menu;
    }
}
