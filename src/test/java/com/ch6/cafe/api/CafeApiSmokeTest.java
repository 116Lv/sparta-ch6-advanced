package com.ch6.cafe.api;

import static org.assertj.core.api.Assertions.assertThat;
import static org.springframework.boot.test.context.SpringBootTest.WebEnvironment.RANDOM_PORT;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Clock;
import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneId;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import java.util.stream.IntStream;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.context.TestConfiguration;
import org.springframework.boot.test.web.server.LocalServerPort;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Import;
import org.springframework.context.annotation.Primary;
import org.springframework.context.ApplicationContext;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.containers.MySQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;
import tools.jackson.core.JacksonException;
import tools.jackson.databind.JsonNode;
import tools.jackson.databind.ObjectMapper;

@Testcontainers
@ActiveProfiles("test")
@Import(CafeApiSmokeTest.FixedClockConfig.class)
@SpringBootTest(webEnvironment = RANDOM_PORT, properties = {
        "spring.jpa.hibernate.ddl-auto=validate",
        "spring.flyway.enabled=true",
        "spring.kafka.listener.auto-startup=false",
        "outbox.publisher.enabled=false"
})
class CafeApiSmokeTest {

    private static final long USER_ID = 101L;
    private static final long MENU_ID = 201L;
    private static final Duration REQUEST_TIMEOUT = Duration.ofSeconds(10);
    private static final String POPULAR_MENU_PATH = "/api/v1/menus/popular?days=7&limit=3";

    @Container
    static final MySQLContainer<?> MYSQL = new MySQLContainer<>("mysql:8.4.0");

    @Container
    static final GenericContainer<?> REDIS =
            new GenericContainer<>(DockerImageName.parse("redis:7.4-alpine")).withExposedPorts(6379);

    @DynamicPropertySource
    static void infrastructureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", MYSQL::getJdbcUrl);
        registry.add("spring.datasource.username", MYSQL::getUsername);
        registry.add("spring.datasource.password", MYSQL::getPassword);
        registry.add("spring.datasource.driver-class-name", MYSQL::getDriverClassName);
        registry.add("spring.data.redis.host", REDIS::getHost);
        registry.add("spring.data.redis.port", () -> REDIS.getMappedPort(6379));
        registry.add("redisson.address", () -> "redis://" + REDIS.getHost() + ":" + REDIS.getMappedPort(6379));
    }

    @LocalServerPort private int port;
    @Autowired private ApplicationContext applicationContext;
    @Autowired private JdbcTemplate jdbcTemplate;
    @Autowired private ObjectMapper objectMapper;
    @Autowired private StringRedisTemplate redisTemplate;
    @Autowired private Clock clock;

    private final HttpClient httpClient = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(5))
            .build();

    @BeforeEach
    void setUp() {
        cleanDatabase();
        Set<String> rankingKeys = redisTemplate.keys("popular-menu:*");
        if (rankingKeys != null && !rankingKeys.isEmpty()) {
            redisTemplate.delete(rankingKeys);
        }
        jdbcTemplate.update(
                "INSERT INTO users (id, created_at, updated_at) VALUES (?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                USER_ID);
        jdbcTemplate.update(
                "INSERT INTO menus (id, name, price, status, created_at, updated_at) "
                        + "VALUES (?, 'Latte', 4000, 'ON_SALE', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)",
                MENU_ID);
    }

    @Test
    void realHttpFlowQueriesMenuChargesPointsPaysOrderAndQueriesPopularity() throws Exception {
        assertThat(applicationContext.containsBean(
                "org.springframework.context.annotation.internalScheduledAnnotationProcessor"))
                .as("the API smoke suite must not start the Outbox scheduler")
                .isFalse();

        HttpResult menus = get("/api/v1/menus");
        assertStatus(menus, 200);
        assertJson(menus, "{\"menus\":[{\"id\":201,\"name\":\"Latte\",\"price\":4000}]}");

        HttpResult charge = post("/api/v1/users/101/points/charge", "{\"amount\":5000}");
        assertStatus(charge, 200);
        assertJson(charge, "{\"userId\":101,\"chargedAmount\":5000,\"balance\":5000}");
        assertThat(queryLong("SELECT balance FROM user_points WHERE user_id = ?", USER_ID)).isEqualTo(5_000L);
        assertThat(queryLong("SELECT COUNT(*) FROM point_histories WHERE user_id = ? AND type = 'CHARGE'", USER_ID)).isOne();

        HttpResult order = post("/api/v1/orders", "{\"userId\":101,\"menuId\":201}");
        assertStatus(order, 200);
        JsonNode actualOrder = json(order.body());
        long orderId = actualOrder.path("orderId").longValue();
        assertThat(orderId).isPositive();
        assertThat(actualOrder).isEqualTo(json("""
                {"orderId":%d,"userId":101,"menuId":201,"paymentAmount":4000,"remainingPoint":1000,"status":"PAID"}
                """.formatted(orderId)));

        assertThat(queryLong("SELECT balance FROM user_points WHERE user_id = ?", USER_ID)).isEqualTo(1_000L);
        assertThat(queryLong("SELECT COUNT(*) FROM point_histories WHERE user_id = ? AND type = 'USE' AND amount = 4000 AND balance_after = 1000", USER_ID)).isOne();
        assertThat(queryLong("SELECT COUNT(*) FROM orders WHERE id = ? AND user_id = ? AND menu_id = ? AND order_price = 4000 AND status = 'PAID'", orderId, USER_ID, MENU_ID)).isOne();
        assertThat(queryLong("SELECT COUNT(*) FROM payments WHERE order_id = ? AND user_id = ? AND amount = 4000 AND status = 'SUCCESS'", orderId, USER_ID)).isOne();
        assertThat(queryLong("SELECT order_count FROM daily_menu_sales WHERE menu_id = ?", MENU_ID)).isOne();
        assertThat(queryLong("SELECT COUNT(*) FROM outbox_events WHERE aggregate_id = ? AND event_type = 'ORDER_PAID' AND status = 'READY'", orderId)).isOne();

        LocalDate today = LocalDate.now(clock);
        assertRecordedDailyRanking(today);

        HttpResult popular = get(POPULAR_MENU_PATH);
        assertStatus(popular, 200);
        String expectedPopular = """
                {"periodDays":7,"menus":[{"menuId":201,"name":"Latte","price":4000,"orderCount":1}]}
                """;
        assertJson(popular, expectedPopular);
        assertCompleteSevenDayRanking(today);
        Map<String, String> markersBeforeCachedRequest = completionMarkerSnapshot(today);

        HttpResult cachedPopular = get(POPULAR_MENU_PATH);
        assertStatus(cachedPopular, 200);
        assertJson(cachedPopular, expectedPopular);
        assertThat(completionMarkerSnapshot(today)).isEqualTo(markersBeforeCachedRequest);
    }

    @Test
    void realHttpRejectsInvalidRequestAndInsufficientPointWithoutPartialOrderState() throws Exception {
        HttpResult invalid = post("/api/v1/users/101/points/charge", "{\"amount\":0}");
        assertStatus(invalid, 400);
        assertJson(invalid, """
                {"error":{"code":"INVALID_REQUEST","message":"The request is invalid.","details":{}}}
                """);

        HttpResult charge = post("/api/v1/users/101/points/charge", "{\"amount\":1000}");
        assertStatus(charge, 200);
        assertJson(charge, "{\"userId\":101,\"chargedAmount\":1000,\"balance\":1000}");

        HttpResult insufficient = post("/api/v1/orders", "{\"userId\":101,\"menuId\":201}");
        assertStatus(insufficient, 409);
        assertJson(insufficient, """
                {"error":{"code":"INSUFFICIENT_POINT","message":"The point balance is insufficient.","details":{}}}
                """);

        assertThat(queryLong("SELECT balance FROM user_points WHERE user_id = ?", USER_ID)).isEqualTo(1_000L);
        assertThat(queryLong("SELECT COUNT(*) FROM point_histories WHERE user_id = ? AND type = 'USE'", USER_ID)).isZero();
        assertThat(queryLong("SELECT COUNT(*) FROM orders")).isZero();
        assertThat(queryLong("SELECT COUNT(*) FROM payments")).isZero();
        assertThat(queryLong("SELECT COUNT(*) FROM daily_menu_sales")).isZero();
        assertThat(queryLong("SELECT COUNT(*) FROM outbox_events")).isZero();
    }

    private HttpResult get(String path) throws Exception {
        return send(HttpRequest.newBuilder(uri(path))
                .timeout(REQUEST_TIMEOUT)
                .GET()
                .build());
    }

    private HttpResult post(String path, String body) throws Exception {
        return send(HttpRequest.newBuilder(uri(path))
                .timeout(REQUEST_TIMEOUT)
                .header("Content-Type", "application/json")
                .POST(HttpRequest.BodyPublishers.ofString(body))
                .build());
    }

    private HttpResult send(HttpRequest request) throws Exception {
        HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
        return new HttpResult(response.statusCode(), response.body());
    }

    private URI uri(String path) {
        return URI.create("http://127.0.0.1:" + port + path);
    }

    private void assertStatus(HttpResult result, int expectedStatus) {
        assertThat(result.status()).as("HTTP response body: %s", result.body())
                .isNotEqualTo(500)
                .isEqualTo(expectedStatus);
    }

    private void assertJson(HttpResult result, String expected) throws JacksonException {
        assertThat(json(result.body())).isEqualTo(json(expected));
    }

    private JsonNode json(String source) throws JacksonException {
        return objectMapper.readTree(source);
    }

    private long queryLong(String sql, Object... arguments) {
        Long result = jdbcTemplate.queryForObject(sql, Long.class, arguments);
        assertThat(result).isNotNull();
        return result;
    }

    private void assertRecordedDailyRanking(LocalDate today) {
        String dataKey = "popular-menu:" + today;
        assertThat(redisTemplate.opsForZSet().score(dataKey, Long.toString(MENU_ID))).isEqualTo(1D);
        assertThat(redisTemplate.opsForZSet().zCard(dataKey)).isOne();
        assertMarker(redisTemplate.opsForValue().get("popular-menu:complete:" + today), 1L, 1L);
    }

    private void assertCompleteSevenDayRanking(LocalDate today) {
        Set<String> expectedMarkers = IntStream.range(0, 7)
                .mapToObj(offset -> "popular-menu:complete:" + today.minusDays(offset))
                .collect(Collectors.toSet());
        assertThat(redisTemplate.keys("popular-menu:complete:*")).isEqualTo(expectedMarkers);

        for (int offset = 0; offset < 7; offset++) {
            LocalDate date = today.minusDays(offset);
            assertMarker(
                    redisTemplate.opsForValue().get("popular-menu:complete:" + date),
                    offset == 0 ? 1L : 0L,
                    offset == 0 ? 1L : 0L);
        }

        Set<String> dataKeys = redisTemplate.keys("popular-menu:*").stream()
                .filter(key -> key.matches("popular-menu:\\d{4}-\\d{2}-\\d{2}"))
                .collect(Collectors.toSet());
        assertThat(dataKeys).containsExactly("popular-menu:" + today);
        assertRecordedDailyRanking(today);
    }

    private void assertMarker(String encoded, long expectedTotalCount, long expectedMenuCount) {
        assertThat(encoded).isNotBlank();
        String[] parts = encoded.split("\\|", -1);
        assertThat(parts).hasSize(3);
        assertThat(UUID.fromString(parts[0])).isNotNull();
        assertThat(Long.parseLong(parts[1])).isEqualTo(expectedTotalCount);
        assertThat(Long.parseLong(parts[2])).isEqualTo(expectedMenuCount);
    }

    private Map<String, String> completionMarkerSnapshot(LocalDate today) {
        Map<String, String> markers = new LinkedHashMap<>();
        for (int offset = 0; offset < 7; offset++) {
            String key = "popular-menu:complete:" + today.minusDays(offset);
            String value = redisTemplate.opsForValue().get(key);
            assertThat(value).as("completion marker %s", key).isNotNull();
            markers.put(key, value);
        }
        return Map.copyOf(markers);
    }

    private void cleanDatabase() {
        for (String table : new String[] {
                "outbox_recovery_audits", "order_paid_analytics", "processed_events", "outbox_events",
                "payments", "daily_menu_sales", "point_histories", "orders", "user_points", "menus", "users"
        }) {
            jdbcTemplate.update("DELETE FROM " + table);
        }
    }

    private record HttpResult(int status, String body) {
    }

    @TestConfiguration(proxyBeanMethods = false)
    static class FixedClockConfig {

        @Bean
        @Primary
        Clock fixedApiSmokeClock() {
            return Clock.fixed(
                    Instant.parse("2026-07-16T01:00:00Z"),
                    ZoneId.of("Asia/Seoul"));
        }
    }
}
