package com.ch6.cafe.domain.point.exception;

import com.ch6.cafe.global.exception.BusinessException;
import com.ch6.cafe.global.exception.ErrorCode;

public class InsufficientPointException extends BusinessException {

    public InsufficientPointException() {
        super(ErrorCode.INSUFFICIENT_POINT);
    }
}
