# 09. 품질, 운영 및 규칙

## 테스트 전략

테스트 규칙은 `ai/verification-levels.md` 및 `ai/qa-gate.md`의 적용도 받는다.

상세 비즈니스 불변식은 [03. 도메인 모델](03-domain-model.md#정합성-불변식)이 소유한다. 모든 동시성, 부하, 복구 및 장애 테스트는 지연 시간과 오류 결과에 더해 적용 가능한 불변식을 확인해야 한다.

### 단위 테스트

다음에 대한 단위 테스트를 작성한다.

- 도메인 규칙
- 포인트 잔액 검증
- 주문 생성 규칙
- 요청 검증 helper
- 랭킹 정책

### 통합 테스트

다음에 대한 통합 테스트를 작성한다.

- repository 동작
- MySQL 트랜잭션 동작
- API controller 동작
- Outbox 이벤트 영속화
- Redis 랭킹 갱신

인기 메뉴 검증은 포함되는 7일 범위, 범위 밖 제외, 상위 3개 동률 정렬, 정확한 `days=7&limit=3` 검증, 고정 clock 정렬, 모든 marker 캐시 적중, 일부 marker 유실, 완전한 빈 날짜, stale key 삭제, TTL 및 임시 key 정리, 누락 메뉴 및 Redis 실패 대체, 결정론적 rebuild/update 인터리빙을 포함해야 한다. MySQL 수치는 모든 장애 경우에 정합성 기준으로 유지된다.

정확한 검증 경계는 저장소 소유 명령이다. `verify.unit`은 Gradle `test`를 실행하고 `*IntegrationTest`, `*ApiSmokeTest`를 제외한다. `verify.integration`은 Testcontainers 기반 MySQL, Redis, Kafka를 대상으로 Gradle `integrationTest`를 실행한다. `verify.api-smoke`는 무작위 포트의 실제 HTTP 서버와 Testcontainers MySQL/Redis로 Gradle `apiSmokeTest`를 실행한다. `verify.e2e`는 무인수 `scripts/e2e/verify-e2e.sh` sequencer를 실행한다. 보존된 단일 인스턴스 Docker Compose 블랙박스 시나리오를 먼저 실행한 뒤 설정된 다중 인스턴스/nginx/k6 시나리오를 실행한다. `verify.build`는 검증 suite를 실행하지 않고 Gradle `assemble`을 실행한다. 모든 명령은 finalized 공식 runner 증거가 정확한 argv를 증명할 때까지 `CONFIGURED_UNVERIFIED` 상태를 유지해야 한다.

Testcontainers는 집중된 인프라 통합 및 API smoke suite에 필요하다. Docker Compose는 배포된 토폴로지 전반의 패키징 애플리케이션, service-DNS, Flyway, broker, 내구성 상태, cache, public HTTP, 멱등성 및 정리 검증에도 필요하다.

### 다중 인스턴스 E2E 및 부하 경계

P2 검증 토폴로지는 `docker-compose.multi-instance.yml`이다. MySQL, Redis, Kafka를 `app-1`, `app-2`가 공유하고, loopback에는 `nginx:1.30.3-alpine`만 공개하며, `grafana/k6:2.1.0`을 profile-gated one-shot 컨테이너로 실행한다. 공개 부하 시나리오는 `scripts/k6/multi-instance.js`다. 기계 판독 JSON 요약은 호스트의 `build/reports/k6/<compose-project>/k6-summary.json`(컨테이너의 `/results/k6-summary.json`)에 기록되며 `scripts/e2e/verify-multi-instance.sh`가 검증하고 runner stdout에 출력한다. 이 경로에서는 호스트 k6 설치가 필요하지도 지원되지도 않는다.

제한된 시나리오는 두 upstream socket, 정상 및 동일 사용자 경합 트래픽, 한 인스턴스 장애, fixture 범위의 내구성 있는 point/order/Outbox/consumer 불변식, 중복 전달 멱등성, MySQL 기반 Redis 손실 랭킹 복구를 관찰하도록 구성된다. TPS나 지연 시간 임계값을 임의로 만들지 않고 처리량과 p50/p95/p99를 기준 관찰값으로 기록한다. publisher 공정성, 모든 claim 전환의 내구성 있는 관측, exactly-once Kafka 발행, 전역/동일 키 순서를 증명하지는 않는다.

최신 finalized 실행 `verify-20260717-assignment-p2-e2e-03`, 시도 `1a5979e9-f360-4804-8bb6-8f1a2d20c224`는 변경된 `verify.e2e` 명령을 종료 코드 0으로 완료했다. k6 요약은 요청 60개, 검사 120개, 실패한 요청 또는 검사 0개, 초당 요청 6.44491566218543개, p50 6.7699985 ms, p95 56.77538449999978 ms, p99 761.2199300399985 ms를 기록했다. 이 처리율과 지연 시간은 SLO 임계값이 아닌 관찰값이다. `prepare`와 `verify-finalized`도 종료 코드 0으로 완료했지만, finalization 범위는 `completenessEvaluated: false`인 `INTEGRITY_ONLY`다. 산출물 무결성은 검증 완전성이나 앞서 증명하지 않는다고 명시한 항목을 독립적으로 확립하지 않는다.

### 실제 API 검증

API 동작 변경은 프로젝트 설정 부재로 막히지 않는 한 실행 중인 서버에 대한 실제 HTTP 요청 검증이 필요하다. 막힌 경우 사유와 함께 `BLOCKED`를 보고한다.

### 동시성 테스트

다음에 대한 동시성 테스트를 작성한다.

- 같은 사용자의 여러 주문
- 같은 사용자의 동시 충전 및 주문
- lock timeout 동작

필수 정합성 검증에는 음수 포인트 잔액 없음, 포인트 lost update 없음, 주문 하나당 중복 결제 없음, 커밋된 결제 완료 주문의 Outbox 이벤트 누락 없음을 포함한다.

필수 이벤트 검증에는 consumer group의 최초 전달에 대한 하나의 marker와 하나의 analytics 효과, 중복 전달의 추가 내구성 상태 없음, 서로 다른 group의 독립 효과, analytics 영속화 실패 시 marker와 효과 모두 롤백을 포함한다. 잘못된 payload는 두 테이블 행 모두 만들면 안 된다.

Publisher 검증은 발행 직전 행 하나 claim, 경쟁 worker, 만료 claim 재배정, stale-token 거부, acknowledgement/status-update 중복 경계, 재시도 1~4의 `READY` 복귀, 재시도 5의 `FAILED` 전환을 포함해야 한다.

영구 실패 복구 검증은 `FAILED`만 `READY`로 전환되고, 재시도/오류/claim 상태가 삭제되며, 운영자·사유·이전 재시도/오류·시각이 정확히 하나의 감사 행에 보존됨을 증명해야 한다. 공백 provenance, `FAILED`가 아닌 상태, 누락 이벤트 또는 트랜잭션 실패는 이벤트와 감사 상태를 모두 변경하지 않아야 한다. 감사 없는 직접 SQL requeue는 금지하며, 인증되지 않은 복구 endpoint가 service를 노출해서는 안 된다.

### 추가형 스키마 롤아웃과 롤백

`order_paid_analytics` 또는 `outbox_recovery_audits`에 쓰는 애플리케이션 인스턴스보다 먼저 마이그레이션 V2를 배포한다. 마이그레이션은 추가형이므로 새 테이블을 만드는 동안 이전 애플리케이션 인스턴스는 계속 실행할 수 있다. 마이그레이션 성공 뒤에만 새 consumer와 감사 복구 코드를 롤아웃한다. Kafka listener 트래픽이나 복구 작업을 활성화하기 전에 테이블, 제약 조건, 인덱스, 애플리케이션 매핑 호환성을 검증한다.

새 애플리케이션을 롤백해야 하면 새 listener/recovery writer를 중지 또는 비활성화하고, 추가된 테이블과 감사/분석 데이터를 보존한 채 애플리케이션 인스턴스를 롤백한다. 테이블을 긴급 롤백으로 삭제하면 내구성 효과와 복구 provenance를 파괴하므로 삭제하지 않는다. 호환되지 않는 애플리케이션 또는 마이그레이션 동작은 검토된 forward-fix 마이그레이션으로 복구한 뒤 재배포하고 Kafka 소비를 재개한다. consumer 멱등성이 이미 커밋된 이벤트의 재생을 흡수한다.

## 성능 및 부하 테스트 계획

아래 시나리오와 지표는 지금 고정한다. 수치 TPS 및 p95 목표는 재현 가능한 기준 실행이 환경, 데이터세트, 인스턴스 수, 도구 구성, 병목 증거를 기록할 때까지 의도적으로 고정하지 않는다. 그 실행 뒤 목표 값과 회귀 허용 범위를 README에 조용히 임의로 추가하지 말고 검증 증거 소유 문서에 기록한다.

### 워크로드

| 시나리오 | 트래픽 형태 | 목적 |
|---|---|---|
| 일반 부하 | 키 전반에 사용자를 분산한 메뉴 조회, 포인트 충전, 주문, 인기 메뉴 조회 | 기준 처리량, 지연 시간 분포, 리소스 사용량 설정 |
| Hot key | 포인트 변경의 높은 비율이 사용자 키 하나를 대상으로 함 | 직렬화 비용, timeout 정책, 공정성, tail latency 측정 |
| 충전/주문 경합 | 같은 사용자에 대해 충전과 주문을 동시에 실행 | lost update, 음수 잔액, 중복 결제, 불일치 이력 감지 |
| Outbox backlog | 새 주문이 계속되는 동안 `READY` backlog를 만들고 publisher/broker 처리량 복구 | claim 공정성, 복구 처리량, 체류 시간, 중복, consumer lag 측정 |

문서화된 단계인 warm-up, 기준 정상 상태, 예상 peak, saturation, recovery로 부하를 증가시킨다. 대안을 비교할 때 동일한 데이터세트와 트래픽 분포를 사용한다.

### Redisson과 DB 비관적 락 비교

동일한 정합성 규칙으로 일반 부하, hot-key, 충전/주문 경합 워크로드를 두 번 실행한다.

1. Redisson 진입 제어 후 MySQL 트랜잭션.
2. Redisson 없이 MySQL 비관적 행 락.

처리량, p50/p95/p99 지연 시간, 오류와 timeout 비율, lock 대기, DB connection-pool active/waiting 수, 불변식 위반을 비교한다. Redisson은 DB 진입 경합 제어 또는 더 빠른 timeout 동작이 Redis 의존성, lease/watchdog 위험 및 추가 장애 경계보다 충분히 가치 있다는 증거가 있을 때만 정당화된다.

### 지표

최소한 다음을 기록한다.

- 요청 처리량과 성공 비즈니스 작업 처리량
- endpoint 및 워크로드 단계별 p50, p95, p99 지연 시간
- HTTP/작업 오류율, lock timeout 비율, 재시도 비율
- Redisson 획득 대기 및 보유 시간 또는 비교 경로의 DB 행 lock 대기
- DB connection-pool active, idle, pending/waiting, timeout, saturation 신호
- `created_at`부터 `published_at`까지 Outbox backlog 수와 이벤트 체류 시간
- Outbox claim 복구 수, 발행 재시도 수, 중복 전달 수
- Kafka producer 오류/재시도 비율과 group/partition별 consumer lag

정합성 위반은 전송 또는 timeout 오류와 별도로 보고한다. 필수 불변식 하나라도 실패하면 더 높은 TPS 결과는 무효다.

## 장애 및 복구 시나리오

| 장애 | 주입 및 기대 동작 | 복구 증거 |
|---|---|---|
| API 인스턴스 장애 | 트래픽 중 stateless API 인스턴스 하나를 중지한다. 로드 밸런서는 새 요청을 정상 인스턴스로 보낸다. | 오류 구간, 재시도 결과, 메모리 내 소유권 유실 없음, 불변식 보존 |
| Outbox Publisher 장애 | 행 claim 후 발행 또는 상태 갱신 전에 worker를 중지한다. | 만료 claim 재획득, 이벤트 누락 없음, 모든 중복은 consumer 멱등성이 흡수 |
| Kafka consumer 장애 | 파티션이 활성인 동안 consumer를 중지한다. | consumer-group 리밸런싱이 파티션을 동적으로 배정, lag가 기준 상태로 회복, 동일 키 순서 보존 |
| Redis 지연/사용 불가 | 포인트 변경 및 랭킹 트래픽 중 Redis를 지연 또는 제거한다. | 포인트 변경은 제어된 정책으로 실패하고 알 수 없는 lock을 우회하지 않음, 랭킹은 문서화된 대체/rebuild 동작 사용 |
| Lease/watchdog 경계 | 설정된 lease/watchdog 경계 근처에서 lock 소유자를 일시 중지 또는 종료한다. | 동시 변경이 point/payment 불변식을 깨지 않음, 소유권 검사가 안전하지 않은 unlock 방지 |
| Kafka 중단 | 주문이 계속되는 동안 broker를 사용할 수 없게 한다. | 커밋된 주문은 재시도 가능한 Outbox 이벤트를 보존, backlog와 체류 시간은 관측 가능하게 증가한 뒤 복구 후 소진 |
| API 과부하 | saturation을 넘어서 트래픽을 유도한다. | 제한된 timeout과 제어된 오류, DB pool과 lock 대기가 병목 노출, 부하 제거 후 service 복구 |

Redis Sentinel은 추후 master failover 용도로 평가할 수 있으나 현재 테스트 환경 가정이 아니며 샤딩이나 쓰기 부하 분산으로 계산해서는 안 된다.

저장소에는 이제 제한된 nginx 기반 2개 애플리케이션 검증 토폴로지가 있다. 이는 테스트 인프라이지 운영 배포 manifest나 운영 로드 밸런서 가용성 증거가 아니다. Redis Sentinel은 계속 향후 가용성 선택지이며 현재 검증 인프라가 아니다.

## 보안 규칙

- secret, token, password 또는 민감한 개인 데이터를 로그에 남기지 않는다.
- 모든 사용자 입력을 서버에서 검증한다.
- 실제 운영 인증 컨텍스트에서는 principal 검증 없이 요청의 userId를 신뢰하지 않는다.
- API 응답에 stack trace를 노출하지 않는다.

## 로깅 규칙

- 중요한 비즈니스 이벤트를 구조화된 필드로 로그한다.
- 주문/결제 실패 사유를 로그한다.
- Outbox 발행 실패와 재시도 횟수를 로그한다.
- 예상하지 못한 예외를 로그한다.
- 민감한 전체 payload를 로그하지 않는다.

## 릴리스 규칙

정확한 릴리스 워크플로는 아직 확인되지 않았다. 저장소 소유 워크플로가 승인되기 전까지 다음 최소 규칙을 적용한다.

- QA Gate 증거 없이 병합하지 않는다.
- PR 설명은 변경된 요구사항과 검증 증거를 포함해야 한다.
- 호환성이 깨지는 변경에는 문서 업데이트가 필요하다.

### 로컬 Compose 경계

루트 `docker-compose.yml`은 운영 배포 manifest가 아닌 로컬 개발 전용 의존성 토폴로지다. MySQL, Redis, Kafka 포트는 `127.0.0.1`에만 바인딩한다. 로컬 호스트 포트와 MySQL 자격 증명은 Compose 파일에 문서화된 `CAFE_*` 환경 변수로 매개변수화한다. Kafka는 내부 service-DNS와 loopback 외부 listener를 분리해 유지한다. 운영 자격 증명, 운영 로드 밸런싱, 다중 인스턴스 배포 작업, 운영 클러스터 토폴로지는 외부 배포 관심사로 남는다. 별도 `docker-compose.multi-instance.yml`은 제한된 검증에만 존재한다.

## 마이그레이션 규칙

- DB 마이그레이션은 배포 전 검토해야 한다.
- 마이그레이션 롤백 또는 완화 계획을 문서화해야 한다.
- 마이그레이션에 의존하는 API 변경은 배포 순서를 명시해야 한다.

## 완료 정의

기능은 다음을 모두 만족할 때만 완료다.

1. 관련 명세 수락 기준을 충족했다.
2. 요구 검증 수준을 충족했다.
3. 테스트를 실제 실행했거나 실행하지 않았음을 명시적으로 보고했다.
4. 적용 가능한 경우 API 변경에 실제 API 검증 증거가 있다.
5. 예상하지 못한 500 응답을 확인했다.
6. 실제 서버 검증이 필요했을 때 서버 로그를 검토했다.
7. 동작이 변경되면 docs/specs/adr을 갱신했다.
8. 완료 주장은 `ai/done-claim-template.md`를 따른다.

## 확정된 검증 결정

- 정확한 작업 경계는 `assemble`, `test`, `integrationTest`, `apiSmokeTest`, 무인수 Compose script이며, 위의 다섯 `verify.*` 명령으로 노출한다.
- Testcontainers는 집중된 MySQL, Redis, Kafka 통합을 담당하고 Docker Compose는 패키지 단일/다중 인스턴스 블랙박스 토폴로지를 담당한다. 작성된 구성은 런타임 `PASS` 증거가 아니다.
