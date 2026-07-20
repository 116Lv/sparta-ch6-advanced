# 00. 프로젝트 지식 색인

## 목적

이 `docs/` 디렉터리는 프로젝트 Wiki를 대체하는 기준 문서 저장소다. 다만 작업 라우팅과 필수 읽기 순서는 `ai/document-routing.md`에서 정의한다.

프로젝트는 저장소의 Markdown 파일만으로 이해할 수 있어야 한다. 외부 Wiki 또는 Notion 페이지는 그 내용이 이 저장소에 복사되지 않는 한 기준 문서로 간주하지 않는다.

## 읽기 순서

### 프로젝트를 처음 이해할 때

1. `README.md`
2. `docs/01-product-vision.md`
3. `docs/03-domain-model.md`
4. `docs/05-functional-requirements.md`
5. `docs/06-system-architecture.md`
6. `docs/07-data-and-api-contracts.md`
7. `docs/09-quality-operations-and-rules.md`

### 기능 개발

1. `AGENTS.md`
2. `ai/document-routing.md`
3. Work Route를 사용하고 기능 소유 결과를 기록한다.
4. 작업이 기능 소유인 경우 먼저 `specs/{feature}/spec.md`를 읽는다.
5. 하위 에이전트를 배정할 때 `ai/subagent-workflow.md`와 `ai/github-issue-planning.md`를 읽고, 독립적으로 종료할 수 있는 응집된 작업 항목마다 하나의 GitHub Issue를 생성한 뒤 `ai/work-logs/issue-{number}/README.md`와 역할별 로그를 초기화한다. 문서화된 생성 실패가 발생한 뒤에만 `tracking_status: pending_issue`를 사용하며, 워크플로 진행 상태는 `status`에 유지한다.
6. 이후 `ai/document-routing.md`가 요구하는 관련 `docs/00~09`, `ai/*`, 단계별 `specs/{feature}/*` 파일만 읽는다.
7. 검증이 필요하면 `ai/verification-levels.md`를 읽는다.
8. 검토와 증거가 준비된 뒤 `ai/issue-completion-checklist.md`의 사전 QA 항목을 완료한다.
9. `ai/qa-gate.md`를 실행한다.
10. `ai/done-claim-template.md`로 완료 보고서를 작성한다.
11. `ai/issue-completion-checklist.md`의 종료 항목을 완료한 뒤, 모든 종료 조건을 통과한 경우에만 Issue를 닫는다.

### 위임 작업 복구

중단되었거나 재개된 위임 작업은 `ai/work-logs/index.md`, 관련 `ai/work-logs/issue-{number}/README.md`, 최신 역할별 에이전트 로그 순으로 시작한다. GitHub가 일시적으로 중단된 경우에는 문서화된 `ai/work-logs/no-issue/` 대체 경로를 사용한다. 이후 Issue를 닫기 전에 조정 작업에서 전체 대체 디렉터리를 `issue-{number}/`로 이동하고 이전 경로를 마이그레이션 이력에 보존해야 한다.

## 문서 맵

| 문서 | 목적 |
|---|---|
| `01-product-vision.md` | 제품 목적, 사용자, 목표, 비목표, 성공 기준 |
| `02-users-and-permissions.md` | 사용자 유형, 역할, 권한 매트릭스, 인증 규칙 |
| `03-domain-model.md` | 핵심 도메인 개념, 엔터티, 관계, 비즈니스 규칙 |
| `04-user-flows.md` | 주요 사용자 흐름, 예외 사례, 성공/실패 상태 |
| `05-functional-requirements.md` | 요구사항 ID, 우선순위, 연결된 명세 |
| `06-system-architecture.md` | 기술 스택, 계층, 의존성 방향, 금지 패턴 |
| `07-data-and-api-contracts.md` | DB 원칙, API 계약, 오류 형식, 이벤트 |
| `08-ui-and-frontend-guidelines.md` | UI 규칙, 폼, 테이블, 로딩/오류/빈 상태 |
| `09-quality-operations-and-rules.md` | 테스트, 보안, 로깅, 릴리스, 마이그레이션, DoD |
| `local-development-environment.md` | 확인된 Windows/WSL/Docker/체크아웃 환경, 로컬 의존성 기본값, 러너 위치, k6 설정 상태 |

## AI 워크플로와 위임 작업

| 문서 | 목적 |
|---|---|
| `ai/document-routing.md` | 작업 분류, Work Route 소유권, 단계별 읽기 |
| `ai/context-map.md` | Phase 2A 경로 ID, 저장소 영역, 생성/제외 경로, 최소 읽기 경로 |
| `ai/cache-policy.md` | Phase 2A 캐시 키, 최신성, 재사용, 보수적 무효화 규칙 |
| `ai/tool-call-policy.md` | 광범위한 검색, 반복 읽기, 명령 재탐색, 호스트 도구 제한에 대한 Phase 2A 정책 |
| `ai/resource-budget.md` | Phase 2A 기본 탐색 예산 및 예외 기록 규칙 |
| `ai/workflow-cache.md` | 재사용 가능한 워크플로 캐시 레코드를 위한 Phase 2A 검토 가능 요약 |
| `ai/skills/README.md` | Phase 2B 스킬 계약 색인 |
| `ai/skill-catalog.json` | 기준 Phase 2B 스킬 카탈로그 |
| `ai/agent-handoff.md` | Phase 2B 핸드오프 상태 및 재사용 가능한 컨텍스트 정책 |
| `ai/agent-handoff.json` | 기준 Phase 2B 핸드오프 패킷 |
| `ai/verification-gates.md` | Phase 2C 검증 완전성, 작업/변경 적용 가능성, 결과 매핑 정책 |
| `ai/verification-policy.json` | 기준 Phase 2C 검증 정책 |
| `scripts/ai/verification-gate.sh` | Phase 2C 정적/보조 검증 게이트 진입점 |
| `ai/subagent-workflow.md` | 배정, 핸드오프, 에이전트 역할, 오케스트레이터 규칙 |
| `ai/github-issue-planning.md` | GitHub Issue 경계, 추적/진행 상태, 수명 주기, 조정 |
| `ai/github-issue-template.md` | 위임 작업에 필요한 GitHub Issue 본문 |
| `ai/work-log-template.md` | Issue 요약 및 역할별 작업 로그 형식 |
| `ai/work-logs/README.md` | 작업 로그 저장 및 복구 규칙 |
| `ai/work-logs/index.md` | Issue 범위 작업 및 조정 대기 작업의 색인 |
| `ai/issue-completion-checklist.md` | QA 전 준비 상태 및 완료 주장 후 GitHub Issue 종료 점검 |
| `ai/qa-gate.md` | 최종 검증 및 위임 작업 증거 게이트 |
| `ai/done-claim-template.md` | 증거 기반 완료 보고서 형식 |

## 기준 문서 규칙

- 제품 목표는 `docs/01-product-vision.md`에 둔다.
- 권한 규칙은 `docs/02-users-and-permissions.md`에 둔다.
- 도메인 및 비즈니스 규칙은 `docs/03-domain-model.md`에 둔다.
- API 및 DB 계약은 `docs/07-data-and-api-contracts.md`에 둔다.
- 테스트 및 운영 규칙은 `docs/09-quality-operations-and-rules.md`에 둔다.
- 문서 라우팅 규칙은 `ai/document-routing.md`에 둔다.
- Phase 2A 경로 및 캐시 제어 규칙은 `ai/context-map.md`, `ai/cache-policy.md`, `ai/tool-call-policy.md`, `ai/resource-budget.md`, `ai/workflow-cache.md`에 둔다.
- Phase 2B 스킬 및 핸드오프 재사용 규칙은 `ai/skills/README.md`, `ai/skill-catalog.json`, `ai/agent-handoff.md`, `ai/agent-handoff.json`에 둔다.
- Phase 2C 검증 완전성 및 작업/변경 적용 가능성 규칙은 `ai/verification-gates.md`, `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`에 둔다. `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL` 매핑은 변경 유형별로 다르다. 제품 명령은 정적/보조 게이트에서 `NOT RUN` 상태를 유지한다.
- AI 워크플로 규칙은 `ai/*`에 둔다.
- 위임 작업은 외부 작업 추적에 GitHub Issues를 사용하고, 지속적인 실행 증거에 `ai/work-logs/issue-{number}/`를 사용한다. `tracking_status`는 Issue 사용 가능 여부를, `status`는 워크플로 진행 상태를 기록한다. 완료된 대기 대체 작업은 구현 QA를 통과할 수 있으나 Issue 기반 주장, 제한 없는 전체 `DONE`, 조정 완료 또는 Issue 종료 전에 조정해야 한다.
- 기능별 실행 세부 사항은 `specs/*`에 둔다.
- 프로젝트 전반의 아키텍처 결정은 `adr/*`에 둔다.

같은 규칙을 여러 파일에 중복하지 않는다. 대신 소유 문서로 연결한다.

## 문서 업데이트 방법

다음 경우 문서를 업데이트한다.

- 비즈니스 규칙이 변경될 때
- API 요청/응답이 변경될 때
- DB 테이블 또는 이벤트 계약이 변경될 때
- 아키텍처 결정이 변경될 때
- 테스트 또는 완료 기준이 변경될 때
- 인증/권한/식별/`userId` 의미가 변경될 때
- 기능 명세가 추가되거나 완료될 때

프로젝트 전반의 기술 결정이 변경되면 ADR을 추가하거나 업데이트한다.

## 확인된 상태와 미해결 질문

- 확인됨: 현재 검증용 Gradle task는 `test`, `integrationTest`, `apiSmokeTest`, `assemble`이다.
- TODO: 이 저장소가 프런트엔드 UI를 포함할지, 백엔드 API만 포함할지 확인한다.
