package com.ch6.cafe.domain.point.service;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.api.Assertions.assertAll;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoInteractions;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.point.dto.response.PointChargeResponse;
import com.ch6.cafe.domain.point.entity.PointHistory;
import com.ch6.cafe.domain.point.entity.PointHistoryType;
import com.ch6.cafe.domain.point.entity.UserPoint;
import com.ch6.cafe.domain.point.repository.PointHistoryRepository;
import com.ch6.cafe.domain.point.repository.UserPointRepository;
import com.ch6.cafe.global.lock.DistributedLockManager;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Supplier;
import java.util.stream.Stream;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.function.Executable;
import org.mockito.ArgumentCaptor;
import org.springframework.transaction.support.TransactionCallback;
import org.springframework.transaction.support.TransactionTemplate;

class PointChargeServiceTest {

    private final DistributedLockManager lockManager = mock(DistributedLockManager.class);
    private final TransactionTemplate transactionTemplate = mock(TransactionTemplate.class);
    private final UserPointRepository userPointRepository = mock(UserPointRepository.class);
    private final PointHistoryRepository pointHistoryRepository = mock(PointHistoryRepository.class);
    private final AtomicBoolean inLock = new AtomicBoolean();
    private final AtomicBoolean inTransaction = new AtomicBoolean();
    private final List<String> events = new ArrayList<>();

    private PointChargeService service;

    @BeforeEach
    void setUp() {
        events.clear();
        when(lockManager.withUserPointLock(anyLong(), any())).thenAnswer(invocation -> {
            assertThat(inLock.getAndSet(true)).isFalse();
            events.add("lock-enter");
            try {
                return invocation.<Supplier<?>>getArgument(1).get();
            } finally {
                events.add("lock-exit");
                inLock.set(false);
            }
        });
        when(transactionTemplate.execute(any())).thenAnswer(invocation -> {
            assertThat(inLock.get()).isTrue();
            assertThat(inTransaction.getAndSet(true)).isFalse();
            events.add("transaction-enter");
            try {
                return invocation.<TransactionCallback<?>>getArgument(0).doInTransaction(null);
            } finally {
                events.add("transaction-exit");
                inTransaction.set(false);
            }
        });
        when(userPointRepository.save(any(UserPoint.class))).thenAnswer(invocation -> {
            assertInsideLockAndTransaction();
            events.add("save-point");
            return invocation.getArgument(0);
        });
        when(pointHistoryRepository.save(any(PointHistory.class))).thenAnswer(invocation -> {
            assertInsideLockAndTransaction();
            events.add("save-history");
            return invocation.getArgument(0);
        });
        service = new PointChargeService(
                lockManager, transactionTemplate, userPointRepository, pointHistoryRepository);
    }

    @Test
    void chargesExistingAccountAndSavesMatchingHistoryInsideLock() {
        UserPoint account = new UserPoint(1L, 1_000L);
        when(userPointRepository.findByUserIdForUpdate(1L)).thenAnswer(invocation -> {
            assertInsideLockAndTransaction();
            events.add("find-for-update");
            return Optional.of(account);
        });

        PointChargeResponse response = service.charge(1L, 500L);

        ArgumentCaptor<UserPoint> pointCaptor = ArgumentCaptor.forClass(UserPoint.class);
        ArgumentCaptor<PointHistory> historyCaptor = ArgumentCaptor.forClass(PointHistory.class);
        verify(userPointRepository).findByUserIdForUpdate(1L);
        verify(userPointRepository).save(pointCaptor.capture());
        verify(pointHistoryRepository).save(historyCaptor.capture());

        assertThat(pointCaptor.getValue()).isSameAs(account);
        assertThat(account.getBalance()).isEqualTo(1_500L);
        assertThat(historyCaptor.getValue())
                .extracting(
                        PointHistory::getUserId,
                        PointHistory::getType,
                        PointHistory::getAmount,
                        PointHistory::getBalanceAfter)
                .containsExactly(1L, PointHistoryType.CHARGE, 500L, 1_500L);
        assertThat(response).isEqualTo(new PointChargeResponse(1L, 500L, 1_500L));
        assertThat(events).containsExactly(
                "lock-enter",
                "transaction-enter",
                "find-for-update",
                "save-point",
                "save-history",
                "transaction-exit",
                "lock-exit");
        assertThat(inLock).isFalse();
        assertThat(inTransaction).isFalse();
    }

    @Test
    void createsMissingPointAccountWithChargedBalance() {
        when(userPointRepository.findByUserIdForUpdate(1L)).thenReturn(Optional.empty());

        PointChargeResponse response = service.charge(1L, 700L);

        ArgumentCaptor<UserPoint> pointCaptor = ArgumentCaptor.forClass(UserPoint.class);
        ArgumentCaptor<PointHistory> historyCaptor = ArgumentCaptor.forClass(PointHistory.class);
        verify(userPointRepository).findByUserIdForUpdate(1L);
        verify(userPointRepository).save(pointCaptor.capture());
        verify(pointHistoryRepository).save(historyCaptor.capture());

        assertThat(pointCaptor.getValue().getUserId()).isEqualTo(1L);
        assertThat(pointCaptor.getValue().getBalance()).isEqualTo(700L);
        assertThat(historyCaptor.getValue())
                .extracting(
                        PointHistory::getUserId,
                        PointHistory::getType,
                        PointHistory::getAmount,
                        PointHistory::getBalanceAfter)
                .containsExactly(1L, PointHistoryType.CHARGE, 700L, 700L);
        assertThat(response).isEqualTo(new PointChargeResponse(1L, 700L, 700L));
    }

    @Test
    void rejectsInvalidInputBeforeEnteringLockOrTransaction() {
        long[][] invalidInputs = {
            {0L, 1L},
            {-1L, 1L},
            {1L, 0L},
            {1L, -1L}
        };

        assertAll(Stream.of(invalidInputs).map(input -> (Executable) () -> {
            verifyNoInteractions(
                    lockManager, transactionTemplate, userPointRepository, pointHistoryRepository);
            assertThatThrownBy(() -> service.charge(input[0], input[1]))
                    .isInstanceOf(IllegalArgumentException.class);
            verifyNoInteractions(
                    lockManager, transactionTemplate, userPointRepository, pointHistoryRepository);
        }));
    }

    @Test
    void doesNotSaveBalanceOrHistoryWhenChargeOverflows() {
        UserPoint account = new UserPoint(1L, Long.MAX_VALUE);
        when(userPointRepository.findByUserIdForUpdate(1L)).thenReturn(Optional.of(account));

        assertThatThrownBy(() -> service.charge(1L, 1L))
                .isInstanceOf(ArithmeticException.class);

        assertThat(account.getBalance()).isEqualTo(Long.MAX_VALUE);
        verify(lockManager).withUserPointLock(anyLong(), any());
        verify(transactionTemplate).execute(any());
        verify(userPointRepository).findByUserIdForUpdate(1L);
        verify(userPointRepository, never()).save(any(UserPoint.class));
        verifyNoInteractions(pointHistoryRepository);
        assertThat(inLock).isFalse();
        assertThat(inTransaction).isFalse();
    }

    private void assertInsideLockAndTransaction() {
        assertThat(inLock.get()).isTrue();
        assertThat(inTransaction.get()).isTrue();
    }
}
