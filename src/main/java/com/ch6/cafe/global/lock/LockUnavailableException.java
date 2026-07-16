package com.ch6.cafe.global.lock;

import com.ch6.cafe.global.exception.BusinessException;
import com.ch6.cafe.global.exception.ErrorCode;

public class LockUnavailableException extends BusinessException {

    public LockUnavailableException(Throwable cause) {
        super(ErrorCode.LOCK_TIMEOUT);
        initCause(cause);
    }
}
