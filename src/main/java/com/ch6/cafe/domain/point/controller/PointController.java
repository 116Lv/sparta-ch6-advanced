package com.ch6.cafe.domain.point.controller;

import com.ch6.cafe.domain.point.dto.request.PointChargeRequest;
import com.ch6.cafe.domain.point.dto.response.PointChargeResponse;
import com.ch6.cafe.domain.point.service.PointChargeService;
import jakarta.validation.Valid;
import jakarta.validation.constraints.Positive;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@Validated
@RestController
@RequestMapping("/api/v1/users/{userId}/points")
public class PointController {

    private final PointChargeService pointChargeService;

    public PointController(PointChargeService pointChargeService) {
        this.pointChargeService = pointChargeService;
    }

    @PostMapping("/charge")
    public PointChargeResponse charge(
            @PathVariable @Positive long userId,
            @Valid @RequestBody PointChargeRequest request) {
        return pointChargeService.charge(userId, request.amount());
    }
}
