# 로컬 개발 환경

## 목적

이 문서는 확인된 로컬 개발 및 검증 환경을 사람이 읽을 수 있는 단일 참조 문서다. 저장소 전체 명령 권한은 계속 `ai/command-registry.json`에서 오며, 이 파일은 지원 도구와 체크아웃의 위치 및 Windows 사용자 컨텍스트 혼동을 피하는 방법을 기록한다.

마지막 확인: 2026-07-17 (Asia/Seoul).

## 확인된 호스트 구성

| 항목 | 확인된 값 또는 위치 | 비고 |
|---|---|---|
| WSL을 소유한 Windows 사용자 | `desktop-r45p2ef\lbw01` | WSL 배포판은 Windows 사용자별로 등록된다. |
| AI 샌드박스 Windows 사용자 | `desktop-r45p2ef\codexsandboxoffline` | 이 계정에서 비관리자로 실행한 `wsl.exe --list`는 `lbw01`이 정상 Ubuntu 배포판을 소유하더라도 배포판이 없다고 보고할 수 있다. |
| WSL 배포판 | `Ubuntu`, WSL 2 | `Running` 상태를 확인했다. `lbw01` 컨텍스트에서 `wsl.exe -d Ubuntu -- ...`를 사용한다. |
| Linux 사용자와 홈 | `lbw01`, `/home/lbw01` | UID/GID 1000, `docker` group 구성원이다. |
| Windows 작업 저장소 | `C:\Users\lbw01\GitHub\sparta-ch6-advanced` | 현재 커밋되지 않은 과제 변경의 기준 작업 트리다. |
| Windows 저장소의 WSL 경로 | `/mnt/c/Users/lbw01/GitHub/sparta-ch6-advanced` | 점검에는 유용하지만 Windows 줄바꿈과 Git 모드 처리가 공식 POSIX 실행에는 부적합할 수 있다. |
| WSL 네이티브 검증 체크아웃 | `/home/lbw01/sparta-ch6-advanced-submission-20260717-03`, `/home/lbw01/sparta-ch6-advanced-final-aef5df0`, `/home/lbw01/sparta-ch6-advanced-runtime-fixed-0ea2493`, `/home/lbw01/sparta-ch6-advanced-runtime-20260716` | `submission-20260717-03` 체크아웃은 현재 P0/P1 검증에 사용했다. 모든 체크아웃은 오래될 수 있으며 Windows 작업 트리와 자동 동기화되지 않는다. |
| WSL 가상 디스크 | `C:\Users\lbw01\AppData\Local\wsl\{39d5274d-dca1-499b-a7eb-a3d09cd004f1}\ext4.vhdx` | 복구 단서일 뿐이다. WSL 사용 중에는 직접 편집, 이동, 마운트 또는 삭제하지 않는다. 재등록 뒤 GUID는 바뀔 수 있다. |

이전 `POSIX_EXECUTION_NOT_CONFIGURED` 진단은 Windows Python으로 runner를 실행하거나 샌드박스 Windows 계정에서 WSL을 조회했기 때문에 발생했다. 이는 `lbw01` Ubuntu 배포판이 없다는 뜻이 아니었다.

## 확인된 런타임 및 컨테이너 도구

| 도구 | 확인된 상태 |
|---|---|
| WSL kernel | `6.18.33.2-microsoft-standard-WSL2` on `x86_64` |
| Ubuntu Python | `python3` 명령의 Python `3.14.4` |
| Docker Desktop WSL 배포판 | `docker-desktop`, WSL 2, `Running` |
| Docker client/server | `29.5.3` / `29.5.3` |
| Docker Compose | `5.1.4` |
| Ubuntu 내부 Docker context | `default` |
| k6 호스트 바이너리 | 2026-07-17 기준 미설치 |
| k6 Docker 이미지 | `grafana/k6:2.1.0`; 2026-07-17의 최신 P2 E2E 실행에서 pull/cache 및 실행됨 |
| nginx Docker 이미지 | `nginx:1.30.3-alpine`; 2026-07-17의 최신 P2 E2E 실행에서 pull/cache 및 실행됨 |

k6 방식은 호스트 전체 설치 대신 버전이 고정된 Docker 이미지다. 현재 `docker-compose.multi-instance.yml`의 profile-gated `k6` service로 설정되어 있으며, 별도의 k6 command ID는 없다. 등록된 유일한 진입점은 SAFE 무인수 `verify.e2e`이며 `scripts/ai/command-runner.sh`를 통해 호출한다. 구현은 먼저 `scripts/e2e/verify-single-instance.sh`를 실행하고 이어서 `scripts/e2e/verify-multi-instance.sh`를 실행한다. 부하 시나리오는 `scripts/k6/multi-instance.js`, nginx 설정은 `scripts/e2e/nginx.conf`, 기계 판독 결과는 호스트의 `build/reports/k6/<compose-project>/k6-summary.json`(k6 컨테이너에서는 `/results/k6-summary.json`)이다. 생성된 결과는 런타임 증거이며 커밋하지 않는다.

최신 finalized 실행 `verify-20260717-assignment-p2-e2e-03`, 시도 `1a5979e9-f360-4804-8bb6-8f1a2d20c224`는 Ubuntu 네이티브 체크아웃에서 변경된 sequencer를 실행해 `2026-07-16T19:40:52Z`에 종료 코드 0으로 완료했다. k6 요약은 요청 60개, 검사 120개, 실패한 요청 또는 검사 0개, 초당 요청 6.44491566218543개, p50 6.7699985 ms, p95 56.77538449999978 ms, p99 761.2199300399985 ms를 기록했다. 이에 따라 레지스트리는 `verify.e2e`를 `VERIFIED`로 기록한다. 이전 2026-07-16 산출물은 이전 단일 인스턴스 구현에 대한 과거 증거로만 남는다.

실행은 `2026-07-16T19:42:37Z`에 finalized되었고 `prepare`, `verify-finalized`가 모두 종료 코드 0으로 완료했다. finalization 범위는 `completenessEvaluated: false`인 `INTEGRITY_ONLY`로 유지된다. 따라서 이는 산출물 무결성을 확인할 뿐 검증 완전성, TPS/지연 시간 SLO, publisher 공정성, 모든 claim 전환의 내구성 있는 관측 또는 exactly-once Kafka 발행을 독립적으로 증명하지 않는다.

## 저장소 실행 위치

- 지원되는 프로젝트 명령 게이트웨이: `scripts/ai/command-runner.sh`
- 기준 명령 정의와 상태: `ai/command-registry.json`
- 로컬 의존성 토폴로지: `docker-compose.yml`
- 등록된 블랙박스 sequencer: `scripts/e2e/verify-e2e.sh`
- 보존된 단일 인스턴스 시나리오: `scripts/e2e/verify-single-instance.sh`
- 다중 인스턴스 Compose 및 시나리오 runner: `docker-compose.multi-instance.yml`, `scripts/e2e/verify-multi-instance.sh`
- 로드 밸런서 및 Docker k6 입력: `scripts/e2e/nginx.conf`, `scripts/k6/multi-instance.js`
- 보조 런타임 증거: `ai/evidence/local-helper-runtime.json`
- 공식 실행 증거: 지원된 runner 세션 뒤 `.ai-runs/<run-id>/`

AI와 자동화는 Gradle, Docker Compose, 애플리케이션 서버, HTTP 클라이언트, 데이터베이스 또는 인프라 명령을 직접 호출해서는 안 된다. LF/실행 비트가 보존되는 WSL 네이티브 체크아웃에서 게이트웨이를 통해 등록된 `verify.*` 명령을 실행하고, 세션마다 새 실행 ID를 사용한다.

기존 WSL 네이티브 체크아웃을 재사용하기 전에는 해당 Git HEAD와 작업 트리 내용을 기준 Windows 체크아웃과 비교한다. Windows의 현재 커밋되지 않은 변경은 Linux 체크아웃이 존재한다는 이유만으로 반영되지 않는다.

## 로컬 의존성 기본값

루트 `docker-compose.yml`은 개발 전용 기본값을 정의한다. 이는 저장소 기본값이며 개인 또는 운영 자격 증명이 아니다.

| 서비스 | 주소 | 개발 기본값 |
|---|---|---|
| MySQL | `127.0.0.1:3306` | 데이터베이스 `cafe`, 사용자 `cafe`, 비밀번호 `cafe`, root 비밀번호 `root` |
| Redis | `127.0.0.1:6379` | 로컬 Compose 파일에서 비밀번호 없음 |
| Kafka | `127.0.0.1:9092` | plaintext 로컬 listener |

MySQL 값은 `CAFE_MYSQL_DATABASE`, `CAFE_MYSQL_USER`, `CAFE_MYSQL_PASSWORD`, `CAFE_MYSQL_ROOT_PASSWORD`, `CAFE_MYSQL_PORT`로 재정의할 수 있다. Redis와 Kafka 호스트 포트에는 `CAFE_REDIS_PORT`, `CAFE_KAFKA_PORT`를 사용한다. 재정의 값은 Redisson 주소를 포함해 `src/main/resources/application.yml`과 일치해야 한다. 개발자의 개인 로컬 비밀번호를 이 문서나 Git에 추가하지 않는다.

필수 테스트에서 저장소 Compose/Testcontainers 기본값 대신 이미 실행 중인 외부 MySQL 인스턴스를 사용해야 할 때만 저장소 소유자에게 MySQL 연결 세부 정보를 요청한다.

## 신뢰할 수 있는 환경 점검

다음 호스트 점검은 샌드박스 계정이 아닌 실제 `lbw01` Windows 컨텍스트에서 실행한다.

```powershell
wsl.exe --list --verbose
wsl.exe -d Ubuntu -- sh -lc 'id; uname -a; docker version; docker compose version'
```

기대 식별 사실은 Windows 사용자 `desktop-r45p2ef\lbw01`, WSL 배포판 `Ubuntu`, Linux 사용자 `lbw01`이다. `wsl.exe --list --verbose`에서 배포판이 없다고 표시되면 먼저 `whoami`를 확인한다. Windows 사용자 컨텍스트 불일치를 배제하기 전에는 Ubuntu를 재설치하거나 재등록하지 않는다.

## 유지 관리 규칙

배포판 이름, 체크아웃 위치, Docker/Compose 버전, 보조 런타임, 로컬 의존성 기본값, k6 이미지/tag, 부하 테스트 진입점 또는 증거 위치가 변경될 때 이 문서를 갱신한다. 같은 시스템 사실을 여러 곳에서 관리하지 않도록 README에는 필수 조건과 이 문서 링크만 둔다.
