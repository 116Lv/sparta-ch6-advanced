package com.ch6.cafe.global.lock;

import static java.util.concurrent.TimeUnit.MILLISECONDS;
import static java.util.concurrent.TimeUnit.SECONDS;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

import java.time.Duration;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;
import org.testcontainers.utility.DockerImageName;

@Testcontainers
class DistributedLockManagerRedisIntegrationTest {

    private static final Duration WATCHDOG_TIMEOUT = Duration.ofMillis(600);

    @Container
    static final GenericContainer<?> REDIS = new GenericContainer<>(DockerImageName.parse("redis:7.4-alpine"))
            .withExposedPorts(6379);

    private RedissonClient redissonClient;

    @BeforeEach
    void setUp() {
        redissonClient = clientFor(REDIS, WATCHDOG_TIMEOUT);
    }

    @AfterEach
    void tearDown() {
        if (redissonClient != null && !redissonClient.isShutdown()) {
            redissonClient.shutdown();
        }
    }

    @Test
    void sameKeyContenderTimesOutWhileOwnerActionIsStillRunning() throws Exception {
        DistributedLockManager owner = new DistributedLockManager(redissonClient, 500L);
        DistributedLockManager contender = new DistributedLockManager(redissonClient, 100L);
        CountDownLatch ownerEntered = new CountDownLatch(1);
        CountDownLatch releaseOwner = new CountDownLatch(1);
        AtomicBoolean contenderActionRan = new AtomicBoolean();
        ExecutorService executor = Executors.newSingleThreadExecutor();
        Future<String> ownerResult = executor.submit(() -> owner.withUserPointLock(1L, () -> {
            ownerEntered.countDown();
            await(releaseOwner);
            return "owner";
        }));
        try {
            assertThat(ownerEntered.await(5, SECONDS)).isTrue();

            assertThatThrownBy(() -> contender.withUserPointLock(1L, () -> {
                contenderActionRan.set(true);
                return "contender";
            })).isInstanceOf(LockTimeoutException.class);

            assertThat(contenderActionRan).isFalse();
        } finally {
            releaseOwner.countDown();
            assertThat(ownerResult.get(5, SECONDS)).isEqualTo("owner");
            executor.shutdownNow();
        }
    }

    @Test
    void watchdogAcquisitionRemainsExclusiveBeyondConfiguredWatchdogTimeout() throws Exception {
        DistributedLockManager owner = new DistributedLockManager(redissonClient, 500L);
        DistributedLockManager contender = new DistributedLockManager(redissonClient, 120L);
        CountDownLatch ownerEntered = new CountDownLatch(1);
        CountDownLatch beyondWatchdog = new CountDownLatch(1);
        CountDownLatch releaseOwner = new CountDownLatch(1);
        AtomicBoolean contenderActionRan = new AtomicBoolean();
        ExecutorService ownerExecutor = Executors.newSingleThreadExecutor();
        ScheduledExecutorService timer = Executors.newSingleThreadScheduledExecutor();
        Future<?> ownerResult = ownerExecutor.submit(() -> owner.withUserPointLock(2L, () -> {
            ownerEntered.countDown();
            await(releaseOwner);
            return null;
        }));
        try {
            assertThat(ownerEntered.await(5, SECONDS)).isTrue();
            timer.schedule(beyondWatchdog::countDown, WATCHDOG_TIMEOUT.multipliedBy(2).toMillis(), MILLISECONDS);
            assertThat(beyondWatchdog.await(3, SECONDS)).isTrue();

            assertThatThrownBy(() -> contender.withUserPointLock(2L, () -> {
                contenderActionRan.set(true);
                return null;
            })).isInstanceOf(LockTimeoutException.class);
            assertThat(contenderActionRan).isFalse();
        } finally {
            releaseOwner.countDown();
            ownerResult.get(5, SECONDS);
            timer.shutdownNow();
            ownerExecutor.shutdownNow();
        }
    }

    @Test
    void ownedReleaseAllowsLaterAcquisitionOfSameKey() {
        DistributedLockManager manager = new DistributedLockManager(redissonClient, 500L);

        assertThat(manager.withUserPointLock(3L, () -> "first")).isEqualTo("first");
        assertThat(manager.withUserPointLock(3L, () -> "second")).isEqualTo("second");
    }

    @Test
    void redisOutageNeverRunsProtectedAction() {
        GenericContainer<?> disposableRedis = new GenericContainer<>(DockerImageName.parse("redis:7.4-alpine"))
                .withExposedPorts(6379);
        disposableRedis.start();
        RedissonClient outageClient = clientFor(disposableRedis, WATCHDOG_TIMEOUT);
        DistributedLockManager manager = new DistributedLockManager(outageClient, 100L);
        AtomicBoolean actionRan = new AtomicBoolean();
        try {
            assertThat(manager.withUserPointLock(4L, () -> "connected")).isEqualTo("connected");
            disposableRedis.stop();

            assertThatThrownBy(() -> manager.withUserPointLock(4L, () -> {
                actionRan.set(true);
                return "unsafe";
            })).isInstanceOf(LockUnavailableException.class);
            assertThat(actionRan).isFalse();
        } finally {
            if (!outageClient.isShutdown()) {
                outageClient.shutdown();
            }
            if (disposableRedis.isRunning()) {
                disposableRedis.stop();
            }
        }
    }

    private static RedissonClient clientFor(GenericContainer<?> redis, Duration watchdogTimeout) {
        Config config = new Config();
        config.setLockWatchdogTimeout(watchdogTimeout.toMillis());
        config.useSingleServer()
                .setAddress("redis://" + redis.getHost() + ":" + redis.getMappedPort(6379))
                .setConnectTimeout(500)
                .setTimeout(500)
                .setRetryAttempts(0);
        return Redisson.create(config);
    }

    private static void await(CountDownLatch latch) {
        try {
            if (!latch.await(5, SECONDS)) {
                throw new IllegalStateException("test coordination timed out");
            }
        } catch (InterruptedException exception) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("test coordination interrupted", exception);
        }
    }
}
