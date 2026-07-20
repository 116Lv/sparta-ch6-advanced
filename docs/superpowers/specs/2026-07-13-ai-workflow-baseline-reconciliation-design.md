# AI 워크플로 기준선 안정화 및 조정 설계

## 목표

승인된 Phase 1A부터 Phase 2C까지의 저장소 기준선을 안정화하고, 확립된 모든 단계 경계를 보존하며, GitHub Issue 접근이 가능해질 때 다섯 개의 `pending_issue` 작업 로그 단위를 조정한다.

이 작업은 Phase 3을 시작하거나, 제품 명령을 실행하거나, 저장소 `.ai-runs` 증거를 생성하거나, 아티팩트 매니페스트 또는 확정된 `run.json`을 게시하거나, command registry 항목을 `VERIFIED`로 승격하지 않는다.

## 승인된 기준선

다음 결정은 변경되지 않는다.

- Phase 1A, Phase 1B, Phase 2A, Phase 2B 및 Phase 2C 구현 결과는 승인된 기준선이다.
- Phase 1B-3은 `completenessEvaluated: false` 및 `scope: INTEGRITY_ONLY`를 갖는 무결성 전용 상태로 유지된다.
- Phase 2C 검증 완전성과 적용 가능성은 해당 정적/helper/contract 게이트를 통해서만 적용된다.
- 별도로 승인된 후속 단계가 권한을 부여하지 않는 한 제품 명령은 NOT RUN으로 유지된다.
- 실제 조정이 성공하기 전에는 Issue 기반 종료, 조정 완료 주장 또는 제한 없는 전체 DONE 주장을 허용하지 않는다.

## 범위

### 기준선 안정화

1. 전체 작업 트리를 검사하고 변경되었거나 추적되지 않는 모든 경로를 승인된 Phase 1A-2C 아티팩트, 관련 없는 사용자 변경 또는 안전하지 않은/생성된 아티팩트로 분류한다.
2. 이미 확립된 비제품 helper, schema, shell-contract, preflight, repo-intake 및 정적 일관성 검사만 실행한다.
3. 저장소에 실제 `.ai-runs`, 비-fixture `artifact-manifest.json`, 확정된 `run.json`, 비밀 정보 또는 의도하지 않은 registry `VERIFIED` 상태가 없음을 확인한다.
4. 이러한 검사에서 발견한 실제 일관성 결함만 수정한다. 승인된 동작과 단계 경계는 재설계하지 않는다.
5. 일관된 단계 또는 인프라 경계별로 묶은 의도적인 기준선 커밋을 생성한다. 관련 없는 사용자 변경은 제외한다.

### GitHub Issue 조정

조정은 다음 다섯 기존 fallback 단위를 대상으로 한다.

- `phase-1b-command-gateway`
- `phase-2a-context-cache`
- `phase-2b-skills-handoff`
- `phase-2c-verification-gates`
- `subagent-workflow-20260710`

각 단위에 대해 orchestrator는 `ai/github-issue-planning.md`를 따른다.

1. 현재 GitHub 인증 및 저장소 Issue 권한을 확인한다.
2. 기록된 `expected_issue_scope` 및 현재 증거로부터 정확히 하나의 GitHub Issue를 생성한다.
3. 전체 fallback 디렉터리를 `ai/work-logs/no-issue/<work-key>/`에서 `ai/work-logs/issue-<number>/`로 이동한다.
4. 모든 요약 및 역할 로그를 실제 Issue 번호와 URL, `tracking_status: issue_backed`, `reconciliation_required: false`, 타임스탬프 및 완전한 migration history로 갱신한다.
5. 작업 로그 인덱스 항목을 교체하고 이전 경로를 migration 기록에 보존한다.
6. 마이그레이션된 저장소 로그를 연결하고 Issue 생성 전에 완료한 작업을 요약하는 Issue 댓글을 추가한다.

조정은 작업 단위별로 원자적이다. Issue 생성 후 어떤 단계라도 실패하면 해당 단위는 명시적으로 미완료 상태를 유지하며 조정되었다고 보고하지 않는다. 성공적으로 조정된 단위는 다른 모든 단위의 성공에 의존하지 않는다.

## 커밋 전략

권장 전략은 하나의 과도하게 큰 체크포인트가 아니라, 작고 순서가 있는 커밋 시리즈다.

1. Phase 1B command gateway 및 무결성 계약.
2. Phase 2A context intake 및 cache control.
3. Phase 2B skill 및 handoff 계약.
4. Phase 2C 검증/적용 가능성 게이트 및 문서 통합.
5. GitHub 조정 메타데이터 및 디렉터리 마이그레이션.

Phase 1A 이력은 이미 커밋되었으며 다시 작성하지 않는다. 파일이 실제로 단계 간에 공유되고 분리하면 중간 저장소 상태가 무효가 되는 경우에만 커밋 경계를 결합할 수 있다.

## 실패 처리

- GitHub가 기록된 403을 계속 반환하는 경우: 정확한 오류를 보존하고, 영향을 받는 모든 단위를 `pending_issue`로 유지하며, Issue 번호나 상태를 날조하지 않고 조정을 중단한다.
- 인증은 성공했으나 Issue 생성이 실패한 경우: 이전 시도 이력을 보존하면서 새 정확한 실패와 타임스탬프를 기록한다.
- Issue 생성은 성공했으나 로컬 마이그레이션이 실패한 경우: Issue를 열린 상태로 유지하고, 조정을 미완료로 기록하며, 중복 Issue를 만들지 않고 저장소 마이그레이션을 재시도한다.
- 검증 검사가 실패한 경우: 범위 내 결함만 진단 및 수정한 뒤 관련 비제품 검사를 다시 실행한다.
- 관련 없는 작업 트리 변경이 대상 파일과 겹치는 경우: 이를 보존하고 기준선 hunk를 분리한다. 안전하게 분리할 수 없을 때만 지시를 요청한다.

## 검증

허용되는 검증은 다음을 포함하여, 이미 Phase 2C에서 승인된 정적/helper/contract/temp-fixture 검사로 제한된다.

- 집중 및 전체 `workflow_helper` 단위 테스트
- helper shell 계약 테스트
- runtime preflight 및 읽기 전용 repo intake
- schema 및 generated-summary 일관성 검사
- `git diff --check` 및 금지된 증거/상태에 대한 정적 스캔
- 조정에 필요한 GitHub 메타데이터 읽기 및 Issue 작업

다음은 계속 NOT RUN이다. Gradle 테스트/빌드, 제품 서버 시작, Docker Compose, HTTP/API smoke 호출, 데이터베이스 작업, 마이그레이션, 시드 및 command-runner를 통한 제품 명령 실행.

## 완료 기준

의도한 Phase 1A-2C 저장소 상태가 검증되고, 금지된 아티팩트 및 상태 전이가 없으며, 관련 없는 변경 없이 일관된 기준선 커밋이 생성되면 기준선 안정화가 통과한다.

GitHub 조정은 여섯 조정 단계가 모두 완료된 후에만 작업 단위별로 통과한다. GitHub 권한을 계속 사용할 수 없으면 기준선 안정화는 통과할 수 있지만 조정은 `pending_issue`로 유지된다. 이 경우 Issue 기반 종료, 조정 완료 주장 또는 제한 없는 전체 DONE 주장은 하지 않는다.

Phase 3A 및 Phase 3B는 이 안정화 작업 이후의 별도 미래 설계 및 구현 노력으로 유지된다.
