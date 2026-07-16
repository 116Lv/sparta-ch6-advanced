package com.ch6.cafe.global.response;

import com.ch6.cafe.global.exception.ErrorCode;
import java.util.Map;

public record ApiErrorResponse(ErrorBody error) {

    public static ApiErrorResponse of(ErrorCode code) {
        return new ApiErrorResponse(new ErrorBody(code.name(), code.message(), Map.of()));
    }

    public record ErrorBody(String code, String message, Map<String, Object> details) {
    }
}
