package com.ch6.cafe.domain.order.service;

import static java.util.concurrent.TimeUnit.SECONDS;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.doThrow;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.ch6.cafe.domain.menu.entity.Menu;
import com.ch6.cafe.domain.menu.entity.MenuStatus;
import com.ch6.cafe.domain.menu.repository.MenuRepository;
import com.ch6.cafe.domain.order.dto.response.OrderResponse;
import com.ch6.cafe.domain.order.entity.OrderStatus;
import com.ch6.cafe.domain.order.repository.OrderRepository;
import com.ch6.cafe.domain.order.repository.PaymentRepository;
import com.ch6.cafe.domain.outbox.publisher.OrderPaidConsumer;
import com.ch6.cafe.domain.outbox.publisher.OutboxPublisher;
import com.ch6.cafe.domain.outbox.repository.OutboxEventRepository;
import com.ch6.cafe.domain.point.entity.UserPoint;
import com.ch6.cafe.domain.point.exception.InsufficientPointException;
import com.ch6.cafe.domain.point.repository.PointHistoryRepository;
import com.ch6.cafe.domain.point.repository.UserPointRepository;
import com.ch6.cafe.domain.point.service.PointChargeService;
import com.ch6.cafe.domain.ranking.repository.DailyMenuSalesRepository;
import com.ch6.cafe.domain.ranking.repository.RedisPopularMenuRepository;
import com.ch6.cafe.domain.ranking.service.MenuSalesRecorder;
import com.ch6.cafe.global.lock.DistributedLockManager;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.time.Clock;
import java.time.LocalDateTime;
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
@SpringBootTest(properties = {
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.flyway.enabled=true",
        "spring.kafka.listener.auto-startup=false"
})
class OrderPaymentMySqlIntegrationTest {

    private static final long USER_ID = 1L;

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
        assertThat(pointHistoryRepository.count()).isEqualTo(2L);
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
        assertThat(pointHistoryRepository.count()).isEqualTo(2L);
        assertCommittedOrderGraph(2L, 2L);
    }

    @Test
    void lateSerializationFailureRollsBackEveryDurableOrderMutation() throws Exception {
        Menu menu = seedUserPointAndMenu(5_000L, 4_000L);
        ObjectMapper failingObjectMapper = mock(ObjectMapper.class);
        when(failingObjectMapper.writeValueAsString(any())).thenThrow(new JsonProcessingException("forced") {
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
    void redisRankingFailureAfterCommitDoesNotChangeCommittedOrderResult() {
        Menu menu = seedUserPointAndMenu(5_000L, 4_000L);
        doThrow(new DataAccessResourceFailureException("redis unavailable"))
                .when(redisRepository).increment(any(), anyLong());

        OrderResponse response = orderPaymentService.order(USER_ID, menu.getId());

        assertThat(response.status()).isEqualTo(OrderStatus.PAID);
        assertThat(response.orderId()).isPositive();
        assertThat(response.remainingPoint()).isEqualTo(1_000L);
        assertThat(currentBalance()).isEqualTo(1_000L).isNotNegative();
        assertThat(pointHistoryRepository.count()).isEqualTo(1L);
        assertCommittedOrderGraph(1L, 1L);
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

    private void assertCommittedOrderGraph(long expectedOrders, long expectedDailyCount) {
        assertThat(orderRepository.count()).isEqualTo(expectedOrders);
        assertThat(paymentRepository.count()).isEqualTo(expectedOrders);
        assertThat(outboxEventRepository.count()).isEqualTo(expectedOrders);
        assertThat(jdbcTemplate.queryForObject(
                "SELECT COUNT(DISTINCT order_id) FROM payments", Long.class)).isEqualTo(expectedOrders);
        assertThat(jdbcTemplate.queryForObject(
                "SELECT COUNT(DISTINCT aggregate_id) FROM outbox_events", Long.class)).isEqualTo(expectedOrders);
        assertThat(dailyMenuSalesRepository.findAll())
                .singleElement()
                .satisfies(sale -> assertThat(sale.getOrderCount()).isEqualTo(expectedDailyCount));
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
}
