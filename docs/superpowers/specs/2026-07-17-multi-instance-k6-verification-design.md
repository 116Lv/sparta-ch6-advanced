# 다중 인스턴스 k6 검증 설계

## 목표

두 개의 상호 교환 가능한 애플리케이션 인스턴스가 하나의 load balancer를 통해 트래픽을 처리하면서 MySQL, Redis, Kafka를 공유하고 저장소의 포인트, 주문, Outbox, consumer 멱등성 및 ranking 복구 불변식을 보존한다는 제한적이고 재현 가능한 증거를 추가한다.

## 범위

이는 검증 전용 인프라다. 프로덕션 Java 코드, 공개 API 계약, 데이터베이스 schema, 기능 요구 사항 또는 ADR 결정을 변경하지 않는다. P0/P1 unit, integration 및 API-smoke 증거는 P2 E2E 실행과 분리되어 남는다.

## 선택한 접근 방식

`verify.e2e`를 등록된 유일한 non-Gradle 명령으로 유지한다. `scripts/e2e/verify-e2e.sh`를 다음을 실행하는 thin sequencer로 변환한다.

1. `verify-single-instance.sh`의 기존 단일 인스턴스 black-box scenario
2. `verify-multi-instance.sh`의 새로운 제한적 다중 인스턴스/k6 scenario

이렇게 하면 닫힌 command allowlist를 보존하고 command-registry schema를 확장하거나 Gradle 뒤에 Docker 실행을 숨기지 않는다.

## 토폴로지

- MySQL `8.4`, Redis `7.4-alpine`, Kafka `3.8.0`을 공유한다.
- `app-1`과 `app-2`는 동일한 빌드 image와 서로 다른 `OUTBOX_PUBLISHER_OWNER` 값을 사용한다.
- 두 consumer는 `coffee-order-analytics`를 사용한다.
- `nginx:1.30.3-alpine`은 유일하게 loopback으로 publish된 endpoint다.
- Nginx는 `X-Upstream-Addr`를 추가하므로 테스트는 실패 전 두 구성 upstream socket이 요청을 처리했고 이후에는 생존자만 요청을 처리했음을 증명할 수 있다.
- `grafana/k6:2.1.0`은 one-shot Compose service로 실행되며 host k6 설치가 필요 없다.

## 시나리오

1. 격리된 Compose project를 시작하고 infrastructure, 두 app, nginx를 기다린다.
2. MySQL에 fixture user와 판매 가능한 메뉴 하나를 시드한다.
3. 공개 API를 통해 포인트 잔액을 설정한다.
4. 두 upstream 주소가 모두 관찰될 때까지 load-balancer endpoint를 반복 호출한다.
5. nginx를 통해 제한된 k6 정상 및 동일 사용자 경합 단계를 실행한다.
6. `app-1`을 중지하고, 중지 후 요청과 새 결제 완료 주문이 `app-2`를 통해 성공하도록 요구하며, Outbox 발행과 analytics 수렴을 기다린다.
7. Kafka 중복 메시지 하나를 주입하고 기존 marker/effect 수가 하나로 유지됨을 증명한다.
8. 변경 트래픽을 중지하고 Redis를 flush한 뒤 nginx를 통해 인기 메뉴를 호출하고 응답을 MySQL 집계와 비교하며 cache/marker 재구성을 검증한다.
9. k6 summary를 검증하고 runner stdout에 출력하며, 모든 프로세스, container, network, volume을 무조건 정리한다.

## 증거 및 주장 경계

scenario는 fixture 범위의 내구성 불변식을 단언한다.

- 모든 잔액은 음수가 아니다.
- `SUM(CHARGE) - SUM(USE) = balance`.
- 결제 완료 주문, 성공한 결제, USE 이력, ORDER_PAID Outbox 행, processed marker 및 analytics 효과는 예상 관계로 수렴한다.
- 각 주문의 결제는 하나를 초과하지 않는다.
- 예상 Outbox 행은 `PUBLISHED`에 도달한다.
- 중복 전송은 두 번째 내구성 consumer 효과를 만들지 않는다.
- 한 app이 중지된 후 새 주문이 완료된다.
- Redis 손실은 MySQL에서 파생된 인기 메뉴 결과를 변경하지 않으며 cache가 재구성된다.

이 실행은 publisher 공정성, 모든 claim 전환의 내구성 있는 관찰, 정확히 한 번 Kafka 발행 또는 전역/동일 키 순서를 주장하지 않는다. 현재 schema는 완료 후 claim 소유권을 지우고 내구성 있는 claim audit이 없으므로, 그러한 주장은 이 범위 밖의 프로덕션 instrumentation이 필요하다.

## 부하 결과 정책

k6는 처리량, 요청 수, 오류 수, p50/p95/p99 지연 시간을 기준 관찰값으로 기록한다. TPS 또는 지연 시간 통과 목표를 새로 만들지 않는다. threshold는 완료된 check와 예기치 않은 HTTP 실패 부재 같은 구조적 정확성만 다룬다. 기계가 읽을 수 있는 summary는 `build/reports/k6/<compose-project>/k6-summary.json`에 기록되고 검증되며 finalized runner stdout으로 출력된다. 생성된 부하 출력은 커밋하지 않는다.

## 실패 처리

모든 Compose, k6, SQL, Kafka 및 cleanup 작업은 제한된다. signal trap은 활성 child process를 종료하고 회수한다. 실패 출력에는 간결한 service log와 사용 가능한 k6 summary를 포함한다. cleanup은 항상 격리된 project와 volume을 제거한다.

## Registry 및 문서

`verify.e2e`는 정확한 argv와 disabled parameter를 유지한다. `inputPaths`는 umbrella, 두 scenario script, multi-instance Compose file, nginx configuration 및 k6 script를 포함하도록 확장된다. 실행 조정 중 명령은 일시적으로 `CONFIGURED_UNVERIFIED`일 수 있으며, fresh finalized evidence가 기록된 후에만 `VERIFIED`로 돌아간다. README와 environment/quality 문서는 정확한 image, entry point, scenario path 및 result location을 식별한다.

## 거부한 대안

- 새 non-Gradle `verify.multi-instance` 명령은 추가 가치가 거의 없는 데 비해 schema/helper trust boundary와 policy contract를 확장한다.
- Gradle `Exec` wrapper는 Docker process ownership을 불투명하게 만들고 명시적 executable allowlist를 약화한다.

## 승인

활성 Codex task에서 2026-07-17 저장소 소유자가 승인함.
