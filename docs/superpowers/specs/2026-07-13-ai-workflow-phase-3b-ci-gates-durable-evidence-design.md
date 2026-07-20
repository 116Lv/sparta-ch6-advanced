# AI 워크플로 단계 3B CI 게이트 및 영속적 CI 증거 설계

## Machine-contract 리터럴

다음 문구는 repository contract test가 검사하는 호환성 리터럴이므로 번역하지 않는다.

- `phase-3b-repository-contract` is `CONFIGURED_UNVERIFIED`.
- `phase-3b-native-enforcement` remains `NOT_CONFIGURED`.
- A green repository contract does not imply native enforcement `PASS`.
- Production authority requires an external GitHub/Sigstore verifier.
- The entry point runs the full `scripts.ai.tests.test_workflow_helper` module exactly once through `scripts/ai/tests/run-contract-tests.sh`.

## 상태 및 범위

단계 3B는 병합된 PR #11 및 Issue #12를 따른다. 저장소 계약 검사 `phase-3b-repository-contract`는 `CONFIGURED_UNVERIFIED`이며, 체크인된 헬퍼 및 셸 계약을 검증하지만 네이티브 강제 검사(Enforcement check)는 아니다. `phase-3b-native-enforcement`는 `NOT_CONFIGURED`로 남아 있으며 `requiredCheckConfigured: false`다. 저장소 계약이 green이라고 해서 네이티브 강제가 `PASS`임을 뜻하지 않는다.

승인된 단계 3A 기준선은 변하지 않았다. `codex-desktop`은 계속 `hostVersion: null` / `UNPROBED`이고, 네 개의 네이티브 surface는 모두 `UNSUPPORTED`이며, 단계 2C 네이티브 leaf는 저장소 한정 `NOT_APPLICABLE`로 매핑된다. 단계 1B-3은 여전히 무결성 전용이며 registry를 `VERIFIED`로 표시하거나 제한 없는 완료 주장을 뒷받침할 수 없다.

## 저장소 계약 진입점

워크플로는 고정된 Python 헬퍼 의존성을 설치하고 헬퍼 및 셸 회귀에 `scripts/ai/tests/run-contract-tests.sh`만 호출한다. 진입점은 저장소 루트를 확인하고 진입하여 전체 `scripts.ai.tests.test_workflow_helper` 모듈을 정확히 한 번 실행한 다음, runtime-preflight와 command-runner 셸 계약 모음을 그 순서로 실행한다. 진입점의 `set -eu`와 `set -o pipefail`은 워크플로 진단 `tee` 주변에서 어느 모음에서든 0이 아닌 결과를 보존한다.

두 셸 모음은 저장소 게이트웨이 계약만 실행한다. 워크플로는 제품 명령을 실행하지 않고, CI 증거 게이트를 호출하지 않으며, 네이티브 강제 작업을 만들거나 강제 결과를 발행하지 않는다. 보존된 출력은 저장소 계약 진단이며 네이티브 강제의 증거가 아니다.

## 외부 신뢰 경계

프로덕션 CI 증거 게이트는 외부 GitHub/Sigstore 검증기가 인증된 현재 실행 권한을 제공할 때까지 무조건 `NOT_CONFIGURED`로 남는다. 실행 ID, 실행 시도, 작업, 워크플로 ref/SHA, head SHA와 같은 GitHub 환경 값은 상관관계 입력이다. 저장소 코드는 이를 자체 인증할 수 없다. 향후 검증기는 아티팩트 attestation과 서명자 ID를 암호학적으로 검증하고, 독립적으로 신뢰되는 현재 실행 컨텍스트를 제공하며, provenance envelope와 저장소 `retainedRun` 주장을 모두 그 컨텍스트에 바인딩해야 한다.

향후 신뢰 경로에서 사용하는 아티팩트 구성원은 안전한 POSIX handle-relative reader를 요구한다. 해당 backend가 없는 호스트는 fail closed한다. 구성 가능한 저장소 값과 일치하는 로컬 JSON은 외부 권한을 제공하지 않는다.

## 영속적 증거 및 보존

향후 enforcement PASS는 저장소, workflow ref 및 SHA, head commit, event, workflow run ID 및 attempt, job ID, artifact ID 및 digest, member digest, `taskKey`, `gateInvocationId`, native evidence digest, bypass event-set SHA-256, `resolutionEventIds`, attestation subject 및 signer repository를 바인딩해야 한다. 보존 기간은 최소 90일이다. cache 또는 handoff record는 이러한 사실을 요약할 수 있지만 인증된 보존 아티팩트를 대체할 수 없다.

## 실패 정책

지원되지 않거나 프로브되지 않은 로컬 호스트는 네이티브 adapter leaf에 대해 저장소 한정 `NOT_APPLICABLE`로 계속 처리된다. 네이티브 adapter 설치, 설치된 필수 enforcement check, 인증된 영속적 증거 또는 remote-runner provenance가 없는 지원 CI 호스트는 완료를 차단한다. cross-process challenge와 bypass event replay 영속성은 외부 신뢰 경로가 설치되고 검증될 때까지 차단된 상태로 남는다.
