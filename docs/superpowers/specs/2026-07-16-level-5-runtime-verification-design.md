# 레벨 5 런타임 검증 설계

## 상태

2026-07-16 구현 요청에서 승인됨.

## 라우팅

- Work Route.
- `specs/004-popular-menu`이 QueryDSL 프로덕션 쿼리 변경을 소유한다.
- `specs/003-order-payment`가 Kafka/Outbox 동작 및 브로커 검증을 소유한다.
- `Owning feature: none`은 저장소 전체 command registry, 실제 HTTP smoke, Docker Compose E2E 및 완료 증거에 적용한다.

## 목표

저장소에 문서화된 아키텍처, 프로덕션 코드, 실제 인프라 검증 및 canonical command registry를 정렬한다. 완료에는 build, unit, integration, API smoke, black-box E2E를 위한 독립적이고 재현 가능한 명령이 필요하며, 모두 `scripts/ai/command-runner.sh`를 통해서만 실행한다.

## 선택한 접근 방식

상호 보완적인 두 검증 계층을 사용한다.

1. Testcontainers integration test는 MySQL, Redis, Kafka에 대해 반복 가능한 개발자 및 CI 검사를 제공한다. 저장소 쿼리, 트랜잭션 경계, 실제 broker 발행/소비, 멱등성, 롤백, 재시도 동작을 검증한다.
2. Docker Compose black-box E2E는 MySQL, Redis, Kafka와 함께 패키징된 애플리케이션을 시작하고 공개 HTTP API를 구동하며 내구성 효과와 캐시 상태를 검사한다. 컨테이너 연결, Flyway 시작, HTTP 계약, Outbox 발행, consumer 효과 및 정리를 증명한다.

Testcontainers만 사용하면 배포 토폴로지나 컨테이너 네트워킹을 증명하지 못한다. Compose만 사용하면 집중된 실패를 격리하는 속도가 느려진다. 따라서 이중 계층이 필요하다.

## 프로덕션 QueryDSL 설계

`DailyMenuSalesRepository`를 Spring Data JPA 진입점으로 유지하고 MySQL native atomic UPSERT는 변경하지 않는다. 집계 및 일별 메타데이터 읽기를 `JPAQueryFactory`와 생성된 `QDailyMenuSale` 메타데이터로 구현한 custom repository fragment로 이동한다.

custom 구현은 기존 projection type을 반환하고, 포함 날짜 범위를 필터링하며, 문서화된 키로 그룹화하고, 최종 인기 메뉴 동점 순서는 기존 domain policy에 맡긴다. Spring configuration bean은 `JPAQueryFactory`를 `EntityManager`로부터 제공한다.

## Kafka 통합 설계

Testcontainers Kafka broker와 MySQL container가 Spring integration test를 지원한다. 테스트는 실제 `OutboxPublisher`를 호출하고, 생성된 레코드를 읽어 topic/key/envelope를 검증하며, 실제 `@KafkaListener` consumer의 MySQL marker와 analytics 효과를 관찰한다.

집중 사례는 동일 그룹 중복 전송, analytics service 경계에서 독립 그룹, analytics 영속성 실패 시 트랜잭션 롤백 및 broker/send 실패 시 publisher 재시도 상태를 다룬다. 기존 집중 MySQL 테스트는 integration command의 일부로 남는다.

## 실제 HTTP Smoke 설계

`ApiSmokeTest`는 Spring Boot를 임의의 실제 포트에서 실행하고 MockMvc가 아닌 Java HTTP client를 사용한다. Testcontainers가 MySQL과 Redis를 제공한다. broker 동작은 Kafka integration suite에 속하므로 Kafka listener와 scheduled publishing은 비활성화한다. 테스트는 내구성 fixture만 시드한 다음 실제 HTTP 요청/응답 쌍을 통해 메뉴 조회, 포인트 충전, 결제 완료 주문, 인기 메뉴 조회, 요청 검증 및 대표적인 비즈니스 오류를 검증한다.

## Docker Compose E2E 설계

애플리케이션 이미지와 health check, 내부 Kafka 주소 지정, 격리된 임시 volume, 애플리케이션 health endpoint 또는 이에 준하는 readiness probe를 갖춘 E2E Compose overlay를 추가한다. POSIX script가 시나리오를 소유하고 시작 전에 cleanup trap을 설치한다.

시나리오는 네 개 서비스를 모두 시작하고, Flyway 기반 애플리케이션 readiness를 기다리고, 사용자와 메뉴를 안전하게 시드하고, HTTP로 포인트를 충전하고 주문한다. 그 후 MySQL order/payment/history/daily-sales/Outbox 행을 검증한다. Outbox publisher와 consumer를 기다리고, processed/analytics 행을 검증하며, Redis ranking 상태와 인기 메뉴 API를 확인하고, 중복 이벤트를 주입해 analytics 효과가 중복되지 않음을 확인한다. 고유 project name에 대해 항상 `docker compose down -v --remove-orphans`를 실행한다.

## 공식 명령 설계

Gradle은 클래스 이름으로 테스트를 분리한다.

- `test`: unit 및 비인프라 테스트. `*IntegrationTest`와 `*ApiSmokeTest`를 제외한다.
- `integrationTest`: `*IntegrationTest`를 포함한다.
- `apiSmokeTest`: `*ApiSmokeTest`를 포함한다.

canonical registry는 다음을 노출한다.

- `verify.build` -> 검증 모음 실행 없이 Gradle assemble/package.
- `verify.unit` -> Gradle `test`.
- `verify.integration` -> Gradle `integrationTest`.
- `verify.api-smoke` -> Gradle `apiSmokeTest`.
- `verify.e2e` -> E2E POSIX script.

정확한 명령이 통과했음을 finalized official runner artifact가 증명할 때까지 모든 명령은 `CONFIGURED_UNVERIFIED`로 남는다. 증거와 Markdown summary는 예상된 성공이 아니라 artifact를 반영해야 한다.

## 실패 처리

- 날짜 predicate, grouping 또는 projection이 잘못되면 QueryDSL 테스트는 실패해야 한다.
- Kafka 테스트는 제한된 polling을 사용하고 broker/영속성 실패를 감추지 않고 보존한다.
- API smoke는 예기치 않은 HTTP 500 응답을 보고하고 서버 측 테스트 출력을 캡처한다.
- E2E readiness 및 내구성 상태 검사는 제한되며, 모든 실패는 정리 전에 간결한 service log를 보존한다.
- finalized runtime evidence 없이 registry 상태를 절대로 `VERIFIED`로 승격하지 않는다.

## 보류된 범위

다음은 명시적인 후속 작업으로 남는다. 실제 load balancer, 여러 애플리케이션 인스턴스 배포, Redis Sentinel 및 운영 클러스터 배포. 구현은 상태 비저장으로 유지하고 MySQL/Redis/Kafka 조정을 사용하므로 이러한 추가에 JVM 로컬 소유권이 필요하지 않다.
