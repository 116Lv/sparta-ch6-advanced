package com.ch6.cafe.domain.menu.repository;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface MenuRepository extends JpaRepository<Menu, Long> {

    List<Menu> findAllByStatusOrderByIdAsc(MenuStatus status);
}
