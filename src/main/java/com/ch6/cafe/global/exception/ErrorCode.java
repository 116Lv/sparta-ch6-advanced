package com.ch6.cafe.global.exception;

import org.springframework.http.HttpStatus;

public enum ErrorCode {
    INVALID_REQUEST(HttpStatus.BAD_REQUEST, "The request is invalid."),
    MENU_NOT_FOUND(HttpStatus.NOT_FOUND, "The menu was not found."),
    MENU_NOT_AVAILABLE(HttpStatus.CONFLICT, "The menu is not available."),
    INSUFFICIENT_POINT(HttpStatus.CONFLICT, "The point balance is insufficient."),
    LOCK_TIMEOUT(HttpStatus.CONFLICT, "Another point mutation for this user is in progress."),
    INTERNAL_ERROR(HttpStatus.INTERNAL_SERVER_ERROR, "An internal server error occurred.");

    private final HttpStatus status;
    private final String message;

    ErrorCode(HttpStatus status, String message) {
        this.status = status;
        this.message = message;
    }

    public HttpStatus status() {
        return status;
    }

    public String message() {
        return message;
    }
}
