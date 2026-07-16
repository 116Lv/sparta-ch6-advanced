package com.ch6.cafe.domain.order.service;

import static java.util.concurrent.TimeUnit.MILLISECONDS;
import static java.util.concurrent.TimeUnit.SECONDS;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.doAnswer;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.times;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.verifyNoMoreInteractions;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import com.ch6.cafe.domain.order.dto.response.OrderResponse;
import com.ch6.cafe.domain.order.entity.Order;
import com.ch6.cafe.domain.order.entity.OrderStatus;
import com.ch6.cafe.domain.order.entity.Payment;
import com.ch6.cafe.domain.order.entity.PaymentStatus;
import com.ch6.cafe.domain.order.repository.OrderRepository;
import com.ch6.cafe.domain.order.repository.PaymentRepository;
import com.ch6.cafe.domain.outbox.entity.OutboxEvent;
import com.ch6.cafe.domain.outbox.entity.OutboxStatus;
import com.ch6.cafe.domain.outbox.publisher.OrderPaidConsumer;
import com.ch6.cafe.domain.outbox.publisher.OutboxPublisher;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.point.entity.PointHistory;
import com.ch6.cafe.domain.point.entity.PointHistoryType;
import com.ch6.cafe.domain.point.entity.UserPoint;
import com.ch6.cafe.domain.point.exception.InsufficientPointException;
import com.ch6.cafe.domain.point.repository.PointHistoryRepository;
import com.ch6.cafe.domain.point.repository.UserPointRepository;
import com.ch6.cafe.domain.point.service.PointChargeService;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import com.ch6.cafe.domain.ranking.service.MenuSalesRecorder;
import com.ch6.cafe.domain.ranking.service.RankingDateLock;
import com.ch6.cafe.global.lock.DistributedLockManager;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;
import java.time.Clock;
import java.time.Instant;
import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.locks.ReentrantLock;
import java.util.function.Supplier;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.redisson.api.RedissonClient;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;
import org.springframework.dao.DataAccessResourceFailureException;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.springframework.test.context.bean.override.mockito.MockitoBean;
import org.springframework.transaction.support.TransactionTemplate;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

@Testcontainers
@ActiveProfiles("test")
@Import(OrderPaymentMySqlIntegrationTest.FixedClockConfig.class)
@SpringBootTest(properties = {
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.flyway.enabled=true",
        "spring.kafka.listener.auto-startup=false"
})
class OrderPaymentMySqlIntegrationTest {

    private static final long USER_ID = 1L;
    private static final LocalDate EXPECTED_DATE = LocalDate.of(2026, 7, 16);

    @Container
    static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.4.0");

    @DynamicPropertySource
    static void mysqlProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);
        registry.add("spring.datasource.driver-class-name", MYSQL::getDriverClassName);
    }

    @MockitoBean
    private DistributedLockManager lockManager;

    @MockitoBean
    private RedisPopularMenuRepository redisRepository;

    @MockitoBean
    private RedissonClient redissonClient;

    @MockitoBean
    private RankingDateLock rankingDateLock;

    @MockitoBean
    private OutboxPublisher outboxPublisher;

    @MockitoBean
    private OrderPaidConsumer orderPaidConsumer;

    @Autowired
    private OrderPaymentService orderPaymentService;

    @Autowired
    private PointChargeService pointChargeService;

    @Autowired
    private MenuSalesRecorder salesRecorder;

    @Autowired
    private TransactionTemplate transactionTemplate;

    @Autowired
    private Clock clock;

    @Autowired
    private MenuRepository menuRepository;

    @Autowired
    private UserPointRepository userPointRepository;

    @Autowired
    private PointHistoryRepository pointHistoryRepository;

    @Autowired
    private OrderRepository orderRepository;

    @Autowired
    private PaymentRepository paymentRepository;

    @Autowired
    private DailyMenuSalesRepository dailyMenuSalesRepository;

    @Autowired
    private OutboxEventRepository outboxEventRepository;

    @Autowired
    private ObjectMapper objectMapper;

    @Autowired
    private JdbcTemplate jdbcTemplate;

    private final Map<Long, ReentrantLock> userLocks = new ConcurrentHashMap<>();

    @BeforeEach
    void setUp() {
        cleanDatabase();
        userLocks.clear();
        when(lockManager.withUserPointLock(anyLong(), org.mockito.ArgumentMatchers.<Supplier<Object>>any()))
                .thenAnswer(invocation -> {
                    long userId = invocation.getArgument(0);
                    Supplier<?> action = invocation.getArgument(1);
                    ReentrantLock lock = userLocks.computeIfAbsent(userId, ignored -> new ReentrantLock());
                    lock.lock();
                    try {
                        return action.get();
                    } finally {
                        lock.unlock();
                    }
                });
        doAnswer(invocation -> {
            invocation.<Runnable>getArgument(1).run();
            return null;
        }).when(rankingDateLock).execute(any(), any());
    }

    @Test
    void concurrentChargeAndOrderPreserveBalanceHistoriesAndCommittedOrderGraph() throws Exception {
        Menu menu = seedUserPointAndMenu(4_000L, 4_000L);

        List<Boolean> outcomes = runTogether(
                () -> {
                    pointChargeService.charge(USER_ID, 3_000L);
                    return true;
                },
                () -> {
                    orderPaymentService.order(USER_ID, menu.getId());
                    return true;
                });

        assertThat(outcomes).containsExactlyInAnyOrder(true, true);
        assertThat(currentBalance()).isEqualTo(3_000L).isNotNegative();
        assertChargeOrderHistory();
        assertCommittedOrderGraph(1L, 1L);
    }

    @Test
    void concurrentOrdersCommitOnlyAffordableOrdersWithoutPartialGraphs() throws Exception {
        Menu menu = seedUserPointAndMenu(8_000L, 4_000L);
        Callable<Boolean> order = () -> {
            try {
                orderPaymentService.order(USER_ID, menu.getId());
                return true;
            } catch (InsufficientPointException exception) {
                return false;
            }
        };

        List<Boolean> outcomes = runTogether(order, order, order);

        assertThat(outcomes).containsExactlyInAnyOrder(true, true, false);
        assertThat(currentBalance()).isZero().isNotNegative();
        assertHistorySequence(
                new ExpectedHistory(PointHistoryType.USE, 4_000L, 4_000L),
                new ExpectedHistory(PointHistoryType.USE, 4_000L, 0L));
        assertCommittedOrderGraph(2L, 2L);
    }

    @Test
    void mysqlPessimisticLockSerializesOverlappingTransactionsWithoutApplicationLock() throws Exception {
        seedUserPointAndMenu(0L, 4_000L);
        ExecutorService executor = Executors.newFixedThreadPool(2);
        CountDownLatch firstLocked = new CountDownLatch(1);
        CountDownLatch releaseFirst = new CountDownLatch(1);
        CountDownLatch secondStarted = new CountDownLatch(1);
        CountDownLatch secondCompleted = new CountDownLatch(1);
        Future<?> first = executor.submit(() -> transactionTemplate.executeWithoutResult(status -> {
            UserPoint point = userPointRepository.findByUserIdForUpdate(USER_ID).orElseThrow();
            point.charge(1_000L);
            pointHistoryRepository.save(PointHistory.charge(USER_ID, 1_000L, point.getBalance()));
            firstLocked.countDown();
            awaitLatch(releaseFirst);
        }));
        Future<?> second = null;
        try {
            assertThat(firstLocked.await(5, SECONDS)).isTrue();
            second = executor.submit(() -> {
                transactionTemplate.executeWithoutResult(status -> {
                    secondStarted.countDown();
                    UserPoint point = userPointRepository.findByUserIdForUpdate(USER_ID).orElseThrow();
                    point.charge(1_000L);
                    pointHistoryRepository.save(PointHistory.charge(USER_ID, 1_000L, point.getBalance()));
                });
                secondCompleted.countDown();
            });
            assertThat(secondStarted.await(5, SECONDS)).isTrue();
            assertThat(secondCompleted.await(250, MILLISECONDS)).isFalse();
        } finally {
            releaseFirst.countDown();
            first.get(5, SECONDS);
            if (second != null) {
                second.get(5, SECONDS);
            }
            executor.shutdownNow();
        }

        assertThat(currentBalance()).isEqualTo(2_000L).isNotNegative();
        assertHistorySequence(
                new ExpectedHistory(PointHistoryType.CHARGE, 1_000L, 1_000L),
                new ExpectedHistory(PointHistoryType.CHARGE, 1_000L, 2_000L));
    }

    @Test
    void lateSerializationFailureRollsBackEveryDurableOrderMutation() throws Exception {
        Menu menu = seedUserPointAndMenu(5_000L, 4_000L);
        ObjectMapper failingObjectMapper = mock(ObjectMapper.class);
        when(failingObjectMapper.writeValueAsString(any())).thenThrow(new JacksonException("forced") {
        });
        OrderPaymentService failingService = new OrderPaymentService(
                lockManager,
                transactionTemplate,
                menuRepository,
                userPointRepository,
                pointHistoryRepository,
                orderRepository,
                paymentRepository,
                outboxEventRepository,
                salesRecorder,
                failingObjectMapper,
                clock);

        assertThatThrownBy(() -> failingService.order(USER_ID, menu.getId()))
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("payload serialization failed");

        assertThat(currentBalance()).isEqualTo(5_000L);
        assertThat(pointHistoryRepository.count()).isZero();
        assertThat(orderRepository.count()).isZero();
        assertThat(paymentRepository.count()).isZero();
        assertThat(dailyMenuSalesRepository.count()).isZero();
        assertThat(outboxEventRepository.count()).isZero();
    }

    @Test
    void redisRankingFailureAfterCommitDoesNotChangeCommittedOrderResult() throws Exception {
        Menu menu = seedUserPointAndMenu(5_000L, 4_000L);
        doThrow(new DataAccessResourceFailureException("redis unavailable"))
                .when(redisRepository).setAbsolute(any(), anyLong(), anyLong(), anyLong(), anyLong());

        OrderResponse response = orderPaymentService.order(USER_ID, menu.getId());

        assertThat(response.status()).isEqualTo(OrderStatus.PAID);
        assertThat(response.orderId()).isPositive();
        assertThat(response.remainingPoint()).isEqualTo(1_000L);
        assertThat(currentBalance()).isEqualTo(1_000L).isNotNegative();
        assertHistorySequence(new ExpectedHistory(PointHistoryType.USE, 4_000L, 1_000L));
        assertCommittedOrderGraph(1L, 1L);
        verify(redisRepository, times(1)).setAbsolute(EXPECTED_DATE, menu.getId(), 1L, 1L, 1L);
        verifyNoMoreInteractions(redisRepository);
    }

    private Menu seedUserPointAndMenu(long balance, long menuPrice) {
        LocalDateTime now = LocalDateTime.now(clock);
        jdbcTemplate.update(
                "INSERT INTO users (id, created_at, updated_at) VALUES (?, ?, ?)",
                USER_ID, now, now);
        userPointRepository.saveAndFlush(new UserPoint(USER_ID, balance));
        return menuRepository.saveAndFlush(new Menu("Latte", menuPrice, MenuStatus.ON_SALE));
    }

    private long currentBalance() {
        return userPointRepository.findAll().stream()
                .filter(point -> point.getUserId().equals(USER_ID))
                .findFirst()
                .orElseThrow()
                .getBalance();
    }

    private void assertChargeOrderHistory() {
        List<PointHistory> histories = historiesInCommitOrder();
        assertThat(histories).hasSize(2);
        if (histories.get(0).getType() == PointHistoryType.CHARGE) {
            assertHistorySequence(
                    new ExpectedHistory(PointHistoryType.CHARGE, 3_000L, 7_000L),
                    new ExpectedHistory(PointHistoryType.USE, 4_000L, 3_000L));
        } else {
            assertHistorySequence(
                    new ExpectedHistory(PointHistoryType.USE, 4_000L, 0L),
                    new ExpectedHistory(PointHistoryType.CHARGE, 3_000L, 3_000L));
        }
    }

    private void assertHistorySequence(ExpectedHistory... expected) {
        List<PointHistory> histories = historiesInCommitOrder();
        assertThat(histories).hasSize(expected.length);
        for (int index = 0; index < expected.length; index++) {
            PointHistory actual = histories.get(index);
            ExpectedHistory transition = expected[index];
            assertThat(actual.getUserId()).isEqualTo(USER_ID);
            assertThat(actual.getType()).isEqualTo(transition.type());
            assertThat(actual.getAmount()).isEqualTo(transition.amount());
            assertThat(actual.getBalanceAfter()).isEqualTo(transition.balanceAfter());
        }
    }

    private List<PointHistory> historiesInCommitOrder() {
        return pointHistoryRepository.findAll(org.springframework.data.domain.Sort.by("id"));
    }

    private void assertCommittedOrderGraph(long expectedOrders, long expectedDailyCount) throws JacksonException {
        List<Order> orders = orderRepository.findAll();
        List<Payment> payments = paymentRepository.findAll();
        List<OutboxEvent> events = outboxEventRepository.findAll();
        assertThat(orders).hasSize((int) expectedOrders);
        assertThat(payments).hasSize((int) expectedOrders);
        assertThat(events).hasSize((int) expectedOrders);
        for (Order order : orders) {
            assertThat(order.getStatus()).isEqualTo(OrderStatus.PAID);
            Payment payment = payments.stream()
                    .filter(candidate -> candidate.getOrderId().equals(order.getId()))
                    .findFirst()
                    .orElseThrow();
            assertThat(payment.getUserId()).isEqualTo(order.getUserId());
            assertThat(payment.getAmount()).isEqualTo(order.getOrderPrice());
            assertThat(payment.getStatus()).isEqualTo(PaymentStatus.SUCCESS);

            OutboxEvent event = events.stream()
                    .filter(candidate -> candidate.getAggregateId().equals(order.getId()))
                    .findFirst()
                    .orElseThrow();
            assertThat(event.getEventType()).isEqualTo("ORDER_PAID");
            assertThat(event.getStatus()).isEqualTo(OutboxStatus.READY);
            JsonNode payload = objectMapper.readTree(event.getPayload());
            assertThat(payload.path("userId").longValue()).isEqualTo(order.getUserId());
            assertThat(payload.path("menuId").longValue()).isEqualTo(order.getMenuId());
            assertThat(payload.path("paymentAmount").longValue()).isEqualTo(order.getOrderPrice());
        }
        assertThat(dailyMenuSalesRepository.findAll())
                .singleElement()
                .satisfies(sale -> {
                    assertThat(sale.getSalesDate()).isEqualTo(EXPECTED_DATE);
                    assertThat(sale.getOrderCount()).isEqualTo(expectedDailyCount);
                });
    }

    private static void awaitLatch(CountDownLatch latch) {
        try {
            if (!latch.await(5, SECONDS)) {
                throw new IllegalStateException("transaction coordination timed out");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("transaction coordination interrupted", exception);
        }
    }

    @SafeVarargs
    private final List<Boolean> runTogether(Callable<Boolean>... tasks) throws Exception {
        ExecutorService executor = Executors.newFixedThreadPool(tasks.length);
        CountDownLatch ready = new CountDownLatch(tasks.length);
        CountDownLatch start = new CountDownLatch(1);
        List<Future<Boolean>> futures = new ArrayList<>();
        try {
            for (Callable<Boolean> task : tasks) {
                futures.add(executor.submit(() -> {
                    ready.countDown();
                    if (!start.await(5, SECONDS)) {
                        throw new IllegalStateException("concurrent test start timed out");
                    }
                    return task.call();
                }));
            }
            assertThat(ready.await(5, SECONDS)).isTrue();
            start.countDown();
            List<Boolean> outcomes = new ArrayList<>();
            for (Future<Boolean> future : futures) {
                outcomes.add(future.get(15, SECONDS));
            }
            return outcomes;
        } finally {
            start.countDown();
            executor.shutdownNow();
        }
    }

    private void cleanDatabase() {
        jdbcTemplate.update("DELETE FROM processed_events");
        jdbcTemplate.update("DELETE FROM outbox_events");
        jdbcTemplate.update("DELETE FROM payments");
        jdbcTemplate.update("DELETE FROM daily_menu_sales");
        jdbcTemplate.update("DELETE FROM point_histories");
        jdbcTemplate.update("DELETE FROM orders");
        jdbcTemplate.update("DELETE FROM user_points");
        jdbcTemplate.update("DELETE FROM menus");
        jdbcTemplate.update("DELETE FROM users");
    }

    private record ExpectedHistory(PointHistoryType type, long amount, long balanceAfter) {
    }

    @TestConfiguration(proxyBeanMethods = false)
    static class FixedClockConfig {

        @Bean
        @Primary
        Clock fixedTestClock() {
            return Clock.fixed(
                    Instant.parse("2026-07-16T01:00:00Z"),
                    ZoneId.of("Asia/Seoul"));
        }
    }
}
