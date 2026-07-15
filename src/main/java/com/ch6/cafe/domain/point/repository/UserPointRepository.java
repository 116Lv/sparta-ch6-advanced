package com.ch6.cafe.domain.point.repository;

import com.ch6.cafe.domain.point.entity.UserPoint;
import jakarta.persistence.LockModeType;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;

public interface UserPointRepository extends JpaRepository<UserPoint, Long> {

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("select point from UserPoint point where point.userId = :userId")
    Optional<UserPoint> findByUserIdForUpdate(@Param("userId") Long userId);
}
