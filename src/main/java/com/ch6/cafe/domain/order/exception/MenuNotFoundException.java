package com.ch6.cafe.domain.order.exception;

import com.ch6.cafe.global.exception.BusinessException;
import com.ch6.cafe.global.exception.ErrorCode;

public class MenuNotFoundException extends BusinessException {

    public MenuNotFoundException() {
        super(ErrorCode.MENU_NOT_FOUND);
    }
}
