# 06. System Architecture

## Tech Stack

Confirmed for assignment design:

- Backend: Spring Boot
- Spring Boot version: `4.1.0`
- Build tool: Gradle
- Java version: `21`
- Base package: `com.ch6.cafe`
- Persistence: Spring Data JPA
- Dynamic query option: QueryDSL
- Database: MySQL
- Distributed lock: Redisson
- Ranking/cache: Redis Sorted Set
- Event streaming: Kafka
- Reliability pattern: Transactional Outbox

Gradle plugin baseline:

```gradle
plugins {
    id 'java'
    id 'org.springframework.boot' version '4.1.0'
    id 'io.spring.dependency-management' version '1.1.7'
}
```

## Application Structure

Suggested package structure:

```txt
com.ch6.cafe
  menu
    api
    application
    domain
    infrastructure
  point
    api
    application
    domain
    infrastructure
  order
    api
    application
    domain
    infrastructure
  ranking
    api
    application
    domain
    infrastructure
  outbox
    application
    domain
    infrastructure
  common
    error
    lock
    time
```

## Layer Responsibilities

### api

- HTTP request/response mapping
- Request validation
- Error response mapping
- No business rules

### application

- Use case orchestration
- Transaction boundary
- Distributed lock orchestration
- Coordination between domain and infrastructure

### domain

- Entities
- Value objects
- Business rules
- No direct dependency on Spring MVC, Redis, Kafka, or DB clients

### infrastructure

- JPA repositories
- QueryDSL repositories
- Redisson adapter
- Redis ranking adapter
- Kafka producer
- Outbox publisher

## Dependency Direction

```txt
api -> application -> domain
application -> infrastructure interfaces/adapters
infrastructure -> external systems
```

## Forbidden Patterns

- Business logic in controller
- Business rules in UI components
- Direct Kafka publish inside order transaction instead of Outbox event save
- JVM local lock for multi-instance point consistency
- Redis as the only source of truth for popular menu counts
- Swallowing exceptions and returning success
- Claiming verification without command/API evidence

## ADR References

- `adr/ADR-000-template.md`
- TODO: Create ADR for Redisson lock choice.
- TODO: Create ADR for Kafka Outbox choice.
- TODO: Create ADR for Redis Sorted Set + daily aggregate choice.

## Open Questions

- Open Question: Does `org.springframework.boot` version `4.1.0` resolve in the target development environment?
