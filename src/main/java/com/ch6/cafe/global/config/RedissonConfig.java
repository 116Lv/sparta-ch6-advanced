package com.ch6.cafe.global.config;

import org.redisson.Redisson;
import org.redisson.api.RedissonClient;
import org.redisson.config.Config;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class RedissonConfig {

    @Bean(destroyMethod = "shutdown")
    RedissonClient redissonClient(
            @Value("${redisson.address}") String address,
            @Value("${lock.point.watchdog-timeout-millis:30000}") long watchdogTimeoutMillis) {
        Config config = new Config();
        config.setLockWatchdogTimeout(watchdogTimeoutMillis);
        config.useSingleServer().setAddress(address);
        return Redisson.create(config);
    }
}
