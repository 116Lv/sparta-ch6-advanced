package com.ch6.cafe.domain.menu.service;

import com.ch6.cafe.domain.menu.dto.response.MenuListResponse;
import com.ch6.cafe.domain.menu.dto.response.MenuResponse;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class MenuQueryService {

    private final MenuRepository menuRepository;

    public MenuQueryService(MenuRepository menuRepository) {
        this.menuRepository = menuRepository;
    }

    @Transactional(readOnly = true)
    public MenuListResponse getOnSaleMenus() {
        return new MenuListResponse(menuRepository.findAllByStatusOrderByIdAsc(MenuStatus.ON_SALE)
                .stream()
                .map(MenuResponse::from)
                .toList());
    }
}
