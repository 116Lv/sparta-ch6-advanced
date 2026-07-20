# Coffee Shop Order System

다중 서버 환경에서 포인트 충전, 커피 주문·결제, 인기 메뉴 집계, 주문 이벤트 전송을 일관성 있게 처리하는 Spring Boot 백엔드 프로젝트입니다.

이 과제는 API 구현뿐 아니라 동시 요청에서 포인트 잔액을 지키는 방법, 주문과 이벤트를 함께 보존하는 방법, Redis 장애 후 인기 메뉴를 복구하는 방법을 설계하고 검증하는 데 초점을 둡니다.

## 1. 프로젝트 소개와 핵심 요구사항

### 필수 기능

| 기능 | 설명 |
|---|---|
| 커피 메뉴 조회 | 판매 중인 메뉴의 ID, 이름, 가격을 조회합니다. |
| 포인트 충전 | 사용자 식별값과 충전 금액을 받아 1원당 1P를 충전합니다. |
| 주문·결제 | 메뉴를 주문하고 사용자의 포인트로 결제합니다. |
| 인기 메뉴 조회 | 최근 7일간 주문 횟수가 많은 메뉴 3개를 조회합니다. |

### 설계 요구사항

- 여러 애플리케이션 인스턴스가 실행되어도 포인트와 주문 데이터가 깨지지 않아야 합니다.
- 포인트 충전·차감과 주문 생성의 동시성 문제를 처리해야 합니다.
- 주문, 결제, 이벤트 발행, 인기 메뉴 집계의 일관성과 장애 복구를 고려해야 합니다.
- 정상·실패·동시성·외부 인프라 장애 경로를 테스트해야 합니다.

로그인 기능은 과제 범위에 포함되지 않습니다. API의 `userId`는 인증 수단이 아니라 미리 준비한 포인트 계정의 사용자를 식별하는 값입니다.

## 2. 기술 스택

| 영역 | 기술 |
|---|---|
| Backend | Spring Boot `4.1.0` |
| Language | Java `21` |
| Build | Gradle Wrapper `9.0.0` |
| Persistence | Spring Data JPA, QueryDSL, Flyway |
| Database | MySQL `8.4` |
| Lock | Redisson, MySQL 트랜잭션·제약조건 |
| Cache / Ranking | Redis Sorted Set |
| Event Streaming | Kafka |
| Reliability | Transactional Outbox, consumer 멱등성 |
| Test | JUnit 5, Spring Boot Test, Testcontainers, k6 |

애플리케이션은 `com.ch6.cafe.global`과 `com.ch6.cafe.domain.{menu,point,order,ranking,outbox}`로 나누고, 각 도메인에서 `controller -> service -> repository` 방향을 사용합니다.

## 3. 로컬 실행 방법

### 준비물

- Java 21
- Docker Engine 또는 Docker Desktop
- Docker Compose
- Windows PowerShell 또는 POSIX shell

Windows·WSL·Docker 환경의 상세 기준은 [로컬 개발 환경 문서](docs/local-development-environment.md)를 참고하세요.

### 3.1 의존성 실행

저장소 루트에서 MySQL, Redis, Kafka를 실행합니다.

```powershell
docker compose up -d
docker compose ps
```

기본 연결 정보는 다음과 같습니다.

| 서비스 | 주소 | 기본 계정 |
|---|---|---|
| MySQL | `127.0.0.1:3306` | database `cafe`, user `cafe`, password `cafe` |
| Redis | `127.0.0.1:6379` | - |
| Kafka | `127.0.0.1:9092` | - |

Compose 포트와 MySQL 계정은 `CAFE_MYSQL_*`, `CAFE_REDIS_PORT`, `CAFE_KAFKA_PORT`로 바꿀 수 있습니다. 값을 바꾸면 `src/main/resources/application.yml`의 datasource, Redis, Redisson, Kafka 연결 정보도 같은 값으로 맞춰야 합니다.

### 3.2 Spring Boot 애플리케이션 실행

Windows PowerShell:

```powershell
.\gradlew.bat bootRun
```

Linux 또는 WSL:

```bash
./gradlew bootRun
```

애플리케이션은 종료할 때까지 계속 실행되며 기본 주소는 `http://localhost:8080`입니다. 시작 과정에서 Flyway가 `src/main/resources/db/migration/`의 스키마를 적용합니다.

종료할 때는 애플리케이션 터미널에서 `Ctrl+C`를 누릅니다. 로컬 의존성까지 내리려면 다음 명령을 실행합니다.

```powershell
docker compose down
```

볼륨의 MySQL 데이터를 함께 지우려는 경우에만 `docker compose down -v`를 사용하세요.

### 3.3 API 호출용 샘플 데이터 준비

Flyway migration은 테이블을 만들지만 사용자와 메뉴를 자동으로 넣지 않습니다. 빈 DB에서 API를 호출하려면 다음 명령으로 사용자와 판매 중인 메뉴를 한 건씩 추가합니다.

```powershell
docker compose exec -T mysql mysql -ucafe -pcafe cafe -e "INSERT INTO users(created_at,updated_at) VALUES(NOW(),NOW()); SET @uid=LAST_INSERT_ID(); INSERT INTO menus(name,price,status,created_at,updated_at) VALUES('Americano',4500,'ON_SALE',NOW(),NOW()); SET @mid=LAST_INSERT_ID(); SELECT @uid AS userId,@mid AS menuId;"
```

출력된 `userId`와 `menuId`를 다음 API 호출에 사용합니다.

## 4. Postman으로 API 호출하기

1. `docker compose up -d`와 `bootRun`으로 서버를 실행합니다.
2. Postman 환경에 `baseUrl`을 `http://localhost:8080`으로 등록합니다.
3. 샘플 데이터 명령이 출력한 값을 `userId`, `menuId` 환경변수로 등록합니다.
4. 포인트를 먼저 충전한 뒤 주문 API를 호출합니다.

### 포인트 충전 예시

- Method: `POST`
- URL: `{{baseUrl}}/api/v1/users/{{userId}}/points/charge`
- Header: `Content-Type: application/json`
- Body → raw → JSON:

```json
{
  "amount": 10000
}
```

### 주문·결제 예시

- Method: `POST`
- URL: `{{baseUrl}}/api/v1/orders`
- Header: `Content-Type: application/json`
- Body → raw → JSON:

```json
{
  "userId": 1,
  "menuId": 1
}
```

위 JSON의 수치는 예시입니다. 실제로는 샘플 데이터 명령에서 확인한 ID를 사용하세요.

## 5. 주요 API

### 5.1 커피 메뉴 목록 조회

```http
GET /api/v1/menus
```

```json
{
  "menus": [
    {
      "id": 1,
      "name": "Americano",
      "price": 4500
    }
  ]
}
```

### 5.2 포인트 충전

```http
POST /api/v1/users/{userId}/points/charge
```

```json
{
  "amount": 10000
}
```

```json
{
  "userId": 1,
  "chargedAmount": 10000,
  "balance": 10000
}
```

### 5.3 커피 주문·결제

```http
POST /api/v1/orders
```

```json
{
  "userId": 1,
  "menuId": 1
}
```

```json
{
  "orderId": 1,
  "userId": 1,
  "menuId": 1,
  "paymentAmount": 4500,
  "remainingPoint": 5500,
  "status": "PAID"
}
```

### 5.4 인기 메뉴 조회

```http
GET /api/v1/menus/popular?days=7&limit=3
```

`days`와 `limit`을 생략하면 각각 `7`, `3`을 사용합니다.

```json
{
  "periodDays": 7,
  "menus": [
    {
      "menuId": 1,
      "name": "Americano",
      "price": 4500,
      "orderCount": 1
    }
  ]
}
```

오류 응답 형식과 상태 코드는 [데이터 및 API 계약](docs/07-data-and-api-contracts.md)에서 확인할 수 있습니다.

## 6. 핵심 설계와 기술 선택 이유

### 애플리케이션 기반: Spring Boot + JPA + QueryDSL

Spring Boot의 REST API, 트랜잭션, JPA, Kafka, Redis 통합을 활용해 프레임워크 구성보다 주문·결제 정합성과 장애 대응에 집중합니다. 기본 저장과 상태 변경은 JPA로 처리하고, 기간 조건과 집계처럼 조건 조합이 필요한 조회에는 타입 안정성과 동적 조건 구성이 용이한 QueryDSL을 사용합니다.

주문, 결제, 포인트, Outbox 이벤트, 일별 메뉴 집계의 정합성 기준 저장소는 MySQL입니다. Redis와 Kafka는 각각 조회 성능과 비동기 이벤트 전송을 위한 보조 인프라입니다.

### 포인트 동시성: Redisson + MySQL

동일 사용자의 충전과 주문은 `point:user:{userId}` 분산락으로 직렬화합니다. 락 안에서 MySQL 트랜잭션과 row lock, 제약조건을 사용하므로 Redis는 진입 경합을 줄이고 MySQL은 최종 일관성 경계를 담당합니다. lease 만료와 Redis 장애가 추가되는 비용을 고려해 DB 비관적 락과의 부하·지연 비교가 필요합니다.

### 주문 이벤트: Transactional Outbox + Kafka

주문, 결제, 포인트 이력, Outbox 이벤트를 같은 MySQL 트랜잭션에 저장합니다. Publisher는 `READY` 이벤트를 claim해 Kafka로 발행하고, 발행 성공 후 `PUBLISHED`로 변경합니다. 발행 성공과 상태 기록 사이에서 장애가 나면 중복 발행될 수 있으므로 consumer는 event ID를 기준으로 멱등 처리합니다.

Kafka는 이벤트 보존과 replay, 여러 consumer group의 독립 소비, partition 병렬 처리, 같은 partition key의 순서 보존을 위해 선택했습니다. replay나 여러 consumer group이 필요 없는 짧은 작업 전달·우선순위·복잡한 routing이 중심이라면 RabbitMQ 같은 작업 큐가 더 적합할 수 있습니다.

### 인기 메뉴: Redis Sorted Set + MySQL 일별 집계

Redis Sorted Set으로 최근 7일 순위를 빠르게 조회하되, `daily_menu_sales`를 복구 가능한 기준 데이터로 유지합니다. Redis 데이터가 없거나 불완전하면 MySQL 일별 집계에서 응답하고 Redis를 다시 구성합니다.

주문 테이블을 매번 직접 집계하는 방식은 단순하지만 조회 비용이 커질 수 있고, Redis만 사용하는 방식은 데이터 유실 시 복구 기준이 약합니다. Redis Sorted Set과 MySQL 일별 집계를 함께 사용해 빠른 조회와 복구 가능성을 절충합니다.

### 패키지 구조

도메인별로 controller, service, repository를 배치해 기능 응집도를 높이고, controller에는 HTTP 변환과 validation만 둡니다. 주문·결제·락·Outbox 같은 비즈니스 규칙은 service와 domain에 둡니다.

각 선택의 대안과 한계는 [ADR 목록](#8-상세-문서)에서 확인할 수 있습니다.

## 7. 테스트 및 자동 검증 방법

### 개발자가 직접 실행하는 Gradle 검증

Windows PowerShell:

```powershell
.\gradlew.bat test
.\gradlew.bat integrationTest
.\gradlew.bat apiSmokeTest
.\gradlew.bat assemble
```

| 명령 | 범위 |
|---|---|
| `test` | 단위·슬라이스 테스트. `*IntegrationTest`, `*ApiSmokeTest` 제외 |
| `integrationTest` | MySQL·Redis·Kafka Testcontainers 통합 테스트 |
| `apiSmokeTest` | random port에서 실행한 실제 HTTP API smoke test |
| `assemble` | 컴파일·패키징 가능 여부 |

### 일회성 E2E 자동 검증

`verify.e2e`는 단일 인스턴스 시나리오와 다중 인스턴스·nginx·Docker k6 시나리오를 차례로 실행합니다. 성공·실패와 관계없이 종료 trap이 애플리케이션과 Compose 컨테이너·볼륨을 정리하므로, 검증이 끝나면 서버도 종료됩니다.

따라서 `verify.e2e`는 한 번 실행하고 정리하는 자동 검증 경로입니다. 일반 개발 서버가 없다는 뜻이 아니며, 로컬 개발에서는 앞서 설명한 `docker compose up -d`와 `bootRun`으로 애플리케이션을 계속 실행하고 Postman으로 `localhost:8080` API를 호출할 수 있습니다.

AI command registry의 `server.dev` 미등록 상태는 자동화 레지스트리에 별도 개발 서버 command ID가 없다는 뜻일 뿐, Spring Boot 애플리케이션을 개발 서버로 실행할 수 없다는 뜻이 아닙니다. 자동화 명령·증적·finalization 규칙은 과제 본문에서 분리해 [AI command registry](ai/command-registry.md)와 [검증 규칙](ai/verification-gates.md)에 기록합니다.

최근 저장소 증적에는 `verify.build`, `verify.unit`, `verify.integration`, `verify.api-smoke`, `verify.e2e` 실행 기록이 있습니다. 이 기록은 각 artifact가 보존됐음을 보여주지만, finalization 범위가 `INTEGRITY_ONLY`이고 `completenessEvaluated: false`이므로 모든 검증이 완전하다는 주장을 자체적으로 증명하지는 않습니다.

## 8. 상세 문서

### 프로젝트 문서

- [문서 인덱스](docs/00-index.md)
- [제품 비전](docs/01-product-vision.md)
- [사용자와 권한](docs/02-users-and-permissions.md)
- [도메인 모델과 일관성 조건](docs/03-domain-model.md)
- [주요 사용자 흐름](docs/04-user-flows.md)
- [기능 요구사항](docs/05-functional-requirements.md)
- [시스템 아키텍처](docs/06-system-architecture.md)
- [데이터 및 API 계약](docs/07-data-and-api-contracts.md)
- [UI 및 프런트엔드 가이드라인](docs/08-ui-and-frontend-guidelines.md)
- [품질·운영·검증 규칙](docs/09-quality-operations-and-rules.md)
- [로컬 개발 환경](docs/local-development-environment.md)
- [포인트 동시성·Outbox·Redis 복구 트러블슈팅](docs/til/2026-07-16-cafe-consistency-troubleshooting.md)

### 아키텍처 결정 기록

- [ADR 템플릿](adr/ADR-000-template.md)
- [ADR-001: Redisson 분산락](adr/ADR-001-redisson-distributed-lock.md)
- [ADR-002: Transactional Outbox와 Kafka](adr/ADR-002-transactional-outbox-kafka.md)
- [ADR-003: Redis Sorted Set과 일별 집계](adr/ADR-003-redis-sorted-set-daily-aggregation.md)
- [ADR-004: 도메인 패키지와 3계층 구조](adr/ADR-004-domain-packages-three-layer.md)

### 기능별 명세

- [메뉴 목록 조회](specs/001-menu-query/spec.md)
- [포인트 충전](specs/002-point-charge/spec.md)
- [주문·결제](specs/003-order-payment/spec.md)
- [인기 메뉴 조회](specs/004-popular-menu/spec.md)
