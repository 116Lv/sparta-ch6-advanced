package com.ch6.cafe.domain.order.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import com.ch6.cafe.domain.order.entity.Order;
import com.ch6.cafe.domain.order.repository.OrderRepository;
import com.ch6.cafe.domain.order.repository.PaymentRepository;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.point.entity.UserPoint;
import com.ch6.cafe.domain.point.repository.PointHistoryRepository;
import com.ch6.cafe.domain.point.repository.UserPointRepository;
import com.ch6.cafe.domain.ranking.service.MenuSalesRecorder;
import com.ch6.cafe.global.lock.DistributedLockManager;
import tools.jackson.databind.ObjectMapper;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Supplier;
import org.junit.jupiter.api.Test;
import org.mockito.ArgumentCaptor;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.transaction.support.TransactionCallback;
import org.springframework.transaction.support.TransactionTemplate;

class OrderPaymentServiceClockTest {

    @Test
    void capturesOrderTimeAfterLockAndUsesItsDateForDurableAndCacheAggregation() {
        ZoneId zone = ZoneId.of("Asia/Seoul");
        AtomicReference<Instant> now = new AtomicReference<>(
                LocalDateTime.of(2026, 7, 15, 23, 59, 59).atZone(zone).toInstant());
        Clock clock = new MutableClock(now, zone);
        LocalDateTime expectedOrderTime = LocalDateTime.of(2026, 7, 16, 0, 0, 1);

        DistributedLockManager lockManager = mock(DistributedLockManager.class);
        when(lockManager.withUserPointLock(eq(1L), any())).thenAnswer(invocation -> {
            now.set(expectedOrderTime.atZone(zone).toInstant());
            return invocation.<Supplier<?>>getArgument(1).get();
        });
        TransactionTemplate transactionTemplate = mock(TransactionTemplate.class);
        when(transactionTemplate.execute(any())).thenAnswer(invocation ->
                invocation.<TransactionCallback<?>>getArgument(0).doInTransaction(null));

        MenuRepository menuRepository = mock(MenuRepository.class);
        UserPointRepository userPointRepository = mock(UserPointRepository.class);
        PointHistoryRepository pointHistoryRepository = mock(PointHistoryRepository.class);
        OrderRepository orderRepository = mock(OrderRepository.class);
        PaymentRepository paymentRepository = mock(PaymentRepository.class);
        OutboxEventRepository outboxEventRepository = mock(OutboxEventRepository.class);
        MenuSalesRecorder salesRecorder = mock(MenuSalesRecorder.class);
        when(menuRepository.findById(10L)).thenReturn(Optional.of(new Menu("Latte", 4_000L, MenuStatus.ON_SALE)));
        when(userPointRepository.findByUserIdForUpdate(1L)).thenReturn(Optional.of(new UserPoint(1L, 5_000L)));
        when(orderRepository.save(any(Order.class))).thenAnswer(invocation -> {
            Order order = invocation.getArgument(0);
            ReflectionTestUtils.setField(order, "id", 100L);
            return order;
        });

        OrderPaymentService service = new OrderPaymentService(
                lockManager, transactionTemplate, menuRepository, userPointRepository,
                pointHistoryRepository, orderRepository, paymentRepository, outboxEventRepository,
                salesRecorder, new ObjectMapper(), clock);

        service.order(1L, 10L);

        ArgumentCaptor<Order> orderCaptor = ArgumentCaptor.forClass(Order.class);
        verify(orderRepository).save(orderCaptor.capture());
        assertThat(orderCaptor.getValue().getOrderedAt()).isEqualTo(expectedOrderTime);
        LocalDate expectedDate = expectedOrderTime.toLocalDate();
        verify(salesRecorder).recordDurable(expectedDate, 10L);
        verify(salesRecorder).recordCache(expectedDate, 10L);
    }

    @Test
    void durablePersistenceFailureEscapesTransactionBoundaryAndSkipsCacheUpdate() {
        Clock clock = Clock.fixed(Instant.parse("2026-07-16T01:00:00Z"), ZoneId.of("Asia/Seoul"));
        LocalDate salesDate = LocalDateTime.now(clock).toLocalDate();
        IllegalStateException persistenceFailure = new IllegalStateException("durable aggregate write failed");

        DistributedLockManager lockManager = mock(DistributedLockManager.class);
        when(lockManager.withUserPointLock(eq(1L), any())).thenAnswer(invocation ->
                invocation.<Supplier<?>>getArgument(1).get());
        TransactionTemplate transactionTemplate = mock(TransactionTemplate.class);
        when(transactionTemplate.execute(any())).thenAnswer(invocation ->
                invocation.<TransactionCallback<?>>getArgument(0).doInTransaction(null));

        MenuRepository menuRepository = mock(MenuRepository.class);
        UserPointRepository userPointRepository = mock(UserPointRepository.class);
        PointHistoryRepository pointHistoryRepository = mock(PointHistoryRepository.class);
        OrderRepository orderRepository = mock(OrderRepository.class);
        PaymentRepository paymentRepository = mock(PaymentRepository.class);
        OutboxEventRepository outboxEventRepository = mock(OutboxEventRepository.class);
        MenuSalesRecorder salesRecorder = mock(MenuSalesRecorder.class);
        when(menuRepository.findById(10L)).thenReturn(Optional.of(new Menu("Latte", 4_000L, MenuStatus.ON_SALE)));
        when(userPointRepository.findByUserIdForUpdate(1L)).thenReturn(Optional.of(new UserPoint(1L, 5_000L)));
        when(orderRepository.save(any(Order.class))).thenAnswer(invocation -> invocation.getArgument(0));
        org.mockito.Mockito.doThrow(persistenceFailure).when(salesRecorder).recordDurable(salesDate, 10L);

        OrderPaymentService service = new OrderPaymentService(
                lockManager, transactionTemplate, menuRepository, userPointRepository,
                pointHistoryRepository, orderRepository, paymentRepository, outboxEventRepository,
                salesRecorder, new ObjectMapper(), clock);

        assertThatThrownBy(() -> service.order(1L, 10L)).isSameAs(persistenceFailure);

        verify(salesRecorder, never()).recordCache(any(), eq(10L));
        verify(outboxEventRepository, never()).save(any());
    }

    private static final class MutableClock extends Clock {
        private final AtomicReference<Instant> current;
        private final ZoneId zone;

        private MutableClock(AtomicReference<Instant> current, ZoneId zone) {
            this.current = current;
            this.zone = zone;
        }

        @Override
        public ZoneId getZone() {
            return zone;
        }

        @Override
        public Clock withZone(ZoneId newZone) {
            return new MutableClock(current, newZone);
        }

        @Override
        public Instant instant() {
            return current.get();
        }
    }
}
