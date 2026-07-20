# Phase 3B CI 게이트 및 내구성 증거

Phase 3B는 PR #11이 commit `400c00f35f9d21cbeec44b0f40f49dac564a4bb6`에서 `main`으로 병합된 뒤 시작한다. 승인된 Phase 1A, 1B, 2A, 2B, 2C, 3A 기준선을 보존하며 native adapter trust를 재설계하지 않는다. Phase 1B-3은 `completenessEvaluated: false`인 `INTEGRITY_ONLY`로 유지한다.

## 검토한 접근 방식

1. workflow가 없는 repository-only CI 상태 계약: 위험은 가장 낮지만 정적 저장소 계약조차 실행되지 않는다.
2. Gradle 및 service 의존성을 갖춘 전체 product CI: product 신호는 강하지만 승인된 Phase 3B 증거 범위 밖이고 product-command 경계를 흐리게 한다.
3. 권장: 정적/helper GitHub Actions workflow와 닫힌 내구성 증거 계약. 필수 native-enforcement 검사가 존재한다고 주장하지 않고 저장소 계약을 실행하며 Gradle, Docker, HTTP/API, database, migration, seed, deploy, infrastructure 명령을 실행하지 않는다.

## 인증된 Provenance 및 내구성 증거 계약

이 저장소에는 외부 GitHub/Sigstore verifier 통합이 없다. 저장소 Python 코드가 올바르게 보이는 provenance 객체를 만들고 helper에 전달하더라도 production gate는 무조건 `NOT_CONFIGURED`로 유지한다. 공개 `scripts/ai/ci-evidence-gate.sh` 진입점에는 provenance 인자가 없으며 저장소 파일이나 `retainedRun` 상태에서 PASS를 만들 수 없다.

하위 pure verifier는 production 권한을 부여하지 않고 향후 통합을 모델링한다. 외부 verifier가 제공하는 변경 불가능한 `GitHubTrustedRunContext`가 필요하다. provenance envelope와 저장소 `retainedRun` 주장은 해당 컨텍스트의 모든 필드와 독립적으로 일치해야 하며 자체 예상 값을 도출하는 데 절대 사용하지 않는다. 이전의 실제 run은 identity가 신뢰하는 현재-run 컨텍스트와 다르면 실패한다.

닫힌 provenance envelope는 예상 저장소와 workflow ref, workflow SHA, head SHA, event name, workflow run ID·attempt, job ID, artifact ID·digest, 모든 artifact member 경로·SHA-256, task·gate correlation, native evidence SHA-256, 완전한 bypass event-set SHA-256, resolution event ID를 결합한다. 검증된 attestation subject는 artifact digest와 같아야 하며 signer repository는 `116Lv/sparta-ch6-advanced`여야 한다. production artifact member에는 고정된 directory descriptor와 `O_NOFOLLOW`를 사용하는 안전한 POSIX handle-relative backend가 필요하다. path escape, symlink 대체, identity race, 콘텐츠 변조는 거부한다. 이 primitive를 사용할 수 없으면 non-POSIX production host는 명시적 backend-unavailable 결과로 fail-closed한다. unit-test 전용 member consumer는 Windows에서 pure correlation verifier를 실행하지만 production gate에서 도달할 수 없고 권한을 수립할 수 없다.

저장소 `retainedRun`과 provenance는 주장일 뿐이다. 올바르게 보이는 저장소 파일, 고정 값, schema-유효 boolean 또는 caller가 선택한 예상 값은 외부 검증을 대체할 수 없다. 최소 보존 기간은 90일이다. workflow run identity와 모든 binding이 일치하지 않으면 cache 재사용은 금지한다. handoff는 요약만 재사용할 수 있으며 내구성 CI 증거로 대체해서는 안 된다.

현재 저장소에는 repository-contract workflow 파일이 있지만 계약은 `CONFIGURED_UNVERIFIED`이고 native enforcement는 `NOT_CONFIGURED`다. 이 로컬 run에는 완료된 remote workflow run, retained artifact identity, 외부 인증 provenance가 없다. 따라서 공개/로컬 CI evidence gate는 Phase 2C leaf `BLOCKED`, 사유 `CI_GITHUB_PROVENANCE_NOT_AVAILABLE`와 함께 `NOT_CONFIGURED`를 반환한다.

## 훅 강제 적용 수준

- Repository contract 검사 `phase-3b-repository-contract`는 `CONFIGURED_UNVERIFIED`다. workflow는 존재하지만 이 작업에서 remote run으로 검증하지 않았다.
- Native enforcement 검사 `phase-3b-native-enforcement`는 `requiredCheckConfigured: false`인 `NOT_CONFIGURED`다. GitHub required check 또는 native adapter가 외부에 설치·attest되지 않았다.
- 현재 `codex-desktop` host: `UNSUPPORTED` / `HOST_UNSUPPORTED`; Phase 2C native leaf는 repository-only 한정으로 `NOT_APPLICABLE`를 유지한다.
- Remote runner 완료: run identity, artifact 보존 또는 native adapter provenance가 없으면 완료를 차단한다.

## 책임 경계

저장소 gateway는 등록된 명령 권한, run 수명 주기, artifact manifest, 레지스트리 승격을 소유한다. CI/native enforcement는 탐색, version provenance, remote runner attestation, bypass event 내구성, challenge/replay 내구성을 소유한다. CI 증거는 그 자체로 레지스트리 `VERIFIED`를 승격하거나 Issue를 닫거나 제한 없는 전체 DONE 주장을 승인할 수 없다.
