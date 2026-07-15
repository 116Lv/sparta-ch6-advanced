package com.ch6.cafe.global.lock;

import com.ch6.cafe.global.exception.BusinessException;
import com.ch6.cafe.global.exception.ErrorCode;

public class LockTimeoutException extends BusinessException {

    public LockTimeoutException() {
        super(ErrorCode.LOCK_TIMEOUT);
    }
}
