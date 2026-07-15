package com.ch6.cafe.domain.order.service;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import com.ch6.cafe.domain.order.dto.response.OrderResponse;
import com.ch6.cafe.domain.order.entity.Order;
import com.ch6.cafe.domain.order.entity.Payment;
import com.ch6.cafe.domain.order.exception.MenuNotAvailableException;
import com.ch6.cafe.domain.order.exception.MenuNotFoundException;
import com.ch6.cafe.domain.order.repository.OrderRepository;
import com.ch6.cafe.domain.order.repository.PaymentRepository;
import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.point.entity.PointHistory;
import com.ch6.cafe.domain.point.entity.UserPoint;
import com.ch6.cafe.domain.point.exception.InsufficientPointException;
import com.ch6.cafe.domain.point.repository.PointHistoryRepository;
import com.ch6.cafe.domain.point.repository.UserPointRepository;
import com.ch6.cafe.domain.ranking.service.MenuSalesRecorder;
import com.ch6.cafe.global.lock.DistributedLockManager;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.LocalDate;
import java.util.Map;
import org.springframework.stereotype.Service;
import org.springframework.transaction.support.TransactionTemplate;

@Service
public class OrderPaymentService {

    private final DistributedLockManager lockManager;
    private final TransactionTemplate transactionTemplate;
    private final MenuRepository menuRepository;
    private final UserPointRepository userPointRepository;
    private final PointHistoryRepository pointHistoryRepository;
    private final OrderRepository orderRepository;
    private final PaymentRepository paymentRepository;
    private final OutboxEventRepository outboxEventRepository;
    private final MenuSalesRecorder salesRecorder;
    private final ObjectMapper objectMapper;

    public OrderPaymentService(
            DistributedLockManager lockManager,
            TransactionTemplate transactionTemplate,
            MenuRepository menuRepository,
            UserPointRepository userPointRepository,
            PointHistoryRepository pointHistoryRepository,
            OrderRepository orderRepository,
            PaymentRepository paymentRepository,
            OutboxEventRepository outboxEventRepository,
            MenuSalesRecorder salesRecorder,
            ObjectMapper objectMapper) {
        this.lockManager = lockManager;
        this.transactionTemplate = transactionTemplate;
        this.menuRepository = menuRepository;
        this.userPointRepository = userPointRepository;
        this.pointHistoryRepository = pointHistoryRepository;
        this.orderRepository = orderRepository;
        this.paymentRepository = paymentRepository;
        this.outboxEventRepository = outboxEventRepository;
        this.salesRecorder = salesRecorder;
        this.objectMapper = objectMapper;
    }

    public OrderResponse order(long userId, long menuId) {
        if (userId <= 0 || menuId <= 0) {
            throw new IllegalArgumentException("User and menu identifiers must be positive.");
        }
        LocalDate salesDate = LocalDate.now();
        OrderResponse response = lockManager.withUserPointLock(userId, () ->
                transactionTemplate.execute(status -> executeOrder(userId, menuId, salesDate)));
        salesRecorder.recordCache(salesDate, menuId);
        return response;
    }

    private OrderResponse executeOrder(long userId, long menuId, LocalDate salesDate) {
        Menu menu = menuRepository.findById(menuId).orElseThrow(MenuNotFoundException::new);
        if (!menu.isOnSale()) {
            throw new MenuNotAvailableException();
        }

        UserPoint point = userPointRepository.findByUserIdForUpdate(userId)
                .orElseThrow(InsufficientPointException::new);
        point.use(menu.getPrice());
        pointHistoryRepository.save(PointHistory.use(userId, menu.getPrice(), point.getBalance()));

        Order order = orderRepository.save(new Order(userId, menuId, menu.getPrice()));
        paymentRepository.save(new Payment(order.getId(), userId, menu.getPrice()));
        salesRecorder.recordDurable(salesDate, menuId);
        outboxEventRepository.save(OutboxEvent.orderPaid(order.getId(), orderPaidPayload(userId, menuId, menu.getPrice())));

        return new OrderResponse(
                order.getId(),
                userId,
                menuId,
                menu.getPrice(),
                point.getBalance(),
                order.getStatus());
    }

    private String orderPaidPayload(long userId, long menuId, long paymentAmount) {
        try {
            return objectMapper.writeValueAsString(Map.of(
                    "userId", userId,
                    "menuId", menuId,
                    "paymentAmount", paymentAmount));
        } catch (JsonProcessingException exception) {
            throw new IllegalStateException("ORDER_PAID payload serialization failed.", exception);
        }
    }
}
