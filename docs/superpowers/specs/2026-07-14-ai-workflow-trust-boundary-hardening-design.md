# AI 워크플로 신뢰 경계 강화 설계

## 상태 및 범위

- 설계 상태: 2026-07-14 승인된 방향
- 소유 기능: 없음
- 기준선: GitHub `main` merge commit `26ba5e768c77139490abcb8fa66d2f696159c18b`
- 변경 유형: 저장소 전반의 정적 워크플로 보안 강화
- 제품 명령: NOT RUN

이 설계는 Phase 1B-3, Phase 2A/2B/2C, Phase 3A, Phase 3B의 증거 및 신뢰 경계를 강화한다. Gradle, 제품 테스트, 애플리케이션, Docker, HTTP/API, 데이터베이스, 마이그레이션, 시드, 배포 또는 인프라 명령을 실행하지 않는다. 실제 저장소 `.ai-runs` 증거를 만들거나, registry 명령을 `VERIFIED`로 승격하거나, Issue를 닫거나, branch를 push하거나, host 소유 증거 없이 native enforcement를 주장하지 않는다.

## 재현된 기준선 문제

병합된 기준선에는 반복되는 하나의 근본 원인이 있다. 호출자 작성 또는 저장소 작성 상태가 origin, content, correlation, freshness의 완전한 증명 없이 신뢰 경계를 넘을 수 있다.

1. Phase 1B-3은 최상위 done-claim 참조가 session command result를 가리키는지 검증하지만 check 자체의 `evidenceRefs`는 비어 있지 않기만 하면 된다. 따라서 check는 없거나 관련 없는 evidence를 인용할 수 있다. `notRunItems`는 completion claim과 비교하지 않는다. `verify-finalized`는 manifest artifact를 검증하지만 final `run.json`, done claim, gate result 및 session-derived graph를 재구성하여 비교하지 않는다. OPEN-to-FINALIZING 전환 후의 validation 실패에는 rollback 경로가 없다.
2. Phase 2C는 evidence envelope, digest, producer, task, gate, commit, policy, freshness를 검증하지 않고 호출자가 제공한 `checkId`, result enum, evidence path, reason을 허용한다. 필수 `NOT_APPLICABLE`을 허용하고 optional `FAIL`은 `NOT_APPLICABLE`로 변환되며 일부 static check는 기본값으로 `PASS`가 된다. Cache entry는 선택된 file digest만 바인딩한다. Skill 및 handoff schema는 array 크기를 제한하지만 서로 다른 required ID를 강제하지 않는다.
3. Phase 3A는 trusted producer, key fingerprint, supported host, current authoritative probe fact를 저장소 제어 policy에 유지한다. Test fixture path는 evaluator에 대한 executable input이다. Replay consumption은 in-process set이고 resolution correlation에는 영속적인 host 소유 detection ledger가 없다.
4. Phase 3B는 static contract workflow를 `phase-3b-ci-gates`로 레이블링하고, 예상된 `NOT_CONFIGURED` 종료를 workflow 성공으로 취급하며, 인증된 GitHub run, job, workflow, artifact, head-SHA provenance 없이 `AVAILABLE` 저장소 `retainedRun`과 저장소 로컬 file을 평가할 수 있다. `ai/project-state.json`은 여전히 CI workflow가 존재하지 않는다고 말한다.
5. `scripts/ai/tests/run-contract-tests.sh`는 shell contract만 실행한다. 선택된 workflow unit-test class는 전체 helper regression suite를 contract entry point의 일부로 만들지 않는다.

## 선택한 아키텍처

evidence 유형별 verifier를 갖춘 공통 validated-evidence contract를 사용한다. 이는 하나의 보편 schema가 아니다. 이는 하나의 fail-closed interface다. aggregation은 verifier가 생성한 result만 수락하고, 각 verifier는 자신의 evidence 유형에 맞는 권한을 증명한다.

모든 trusted result는 다음을 확립해야 한다.

- 닫힌 schema 및 semantic validity
- 정확한 content SHA-256 및 repository-relative 또는 external identity
- task key 및 gate invocation correlation
- 적용 가능한 경우 commit 및 policy identity
- producer identity 및 authority source
- 적용 가능한 경우 creation timestamp 및 제한된 freshness
- 단일 목적 evidence type. 따라서 policy document는 execution result를 대체할 수 없고 local file은 GitHub provenance를 대체할 수 없다.

구현은 하나의 거대한 validator 대신 이러한 검사를 작은 helper에 유지해야 한다. Phase별 코드는 자신의 authority model에 대해 계속 책임을 진다.

## 신뢰 권한 매트릭스

| Evidence 유형 | 권위 있는 producer | 필수 binding | 저장소 작성 대체물 |
| --- | --- | --- | --- |
| Phase 1B command/gate artifact | 한 run 내 지원되는 저장소 gateway | run, task, artifact path, digest, manifest graph | 금지됨 |
| Phase 2 verification leaf | validated result artifact를 갖는 명명된 leaf producer | task, gate, commit, policy digest, evidence digest, timestamp | policy-only PASS 금지됨 |
| Phase 2 cache decision | 소비된 모든 input에 대한 cache evaluator | 모든 evidence digest, policy digest, task/change classification, environment input | partial cache key 금지됨 |
| Phase 3A runtime attestation | host 소유의 권위 있는 producer 및 probe | repository, task, gate, nonce, event ledger, host/version, key | 저장소 key/probe/fixture 금지됨 |
| Phase 3B CI attestation | GitHub 소유 run/job/artifact context | repository, workflow identity, run ID, attempt, job ID, head SHA, artifact ID 및 digest | retained JSON/local file 금지됨 |

## Phase 1B-3 증거 그래프

finalizer는 불변 final artifact를 발행하기 전에 하나의 normalized evidence graph를 생성한다. 각 check reference는 active session의 artifact로 해소되어야 하고 모든 check evidence reference도 최상위 claim closure에 나타나야 한다. 중복, 부재, unbound, wrong-kind reference는 `INVALID_STATE`다.

`notRunItems`는 고유해야 하며 session에서 PASS 또는 실행되었다고 주장한 check, command, capability를 가리켜서는 안 된다. 모순된 not-run 항목이 있는 PASS completion claim은 `INVALID_STATE`다. Phase 1B가 적용 가능성을 증명할 수 없을 때 not-run만인 필수 capability는 `BLOCKED`다.

최종 `run.json`은 FINALIZING session, done claim, pre-done gate result, manifest에서 결정적으로 파생된다. `verify-finalized`는 해당 projection을 다시 계산하고 run/task identity, timestamp, result/reason, command 및 policy reference, evidence reference, redaction state, manifest closure, done-claim outcome, gate scope를 포함한 중요한 field를 교차 검사한다. 모든 tampering 또는 stale projection은 `INVALID_STATE`다.

첫 OPEN-to-FINALIZING compare-and-swap 전에 finalizer는 새 UUID를 만들고 닫힌 `.state/finalization-journals/<journal-id>.json`을 독점적으로 발행한다. 이 독립 권한에는 journal UUID, 정확한 source OPEN session, 정확한 intended FINALIZING session, claim-input reference, 예상 lock-recovery prefix가 포함된다. run session의 닫힌 최상위 `finalizationJournalIdentity`는 OPEN에서 null이고 FINALIZING에서 해당 journal path/UUID/digest와 같으며 FINALIZED receipt의 `journalIdentity`와 계속 같다. journal이 그 identity를 포함하므로 canonical digest는 내장된 digest만 64 ASCII zero로 정규화한 후 계산한다. 다른 field는 생략하거나 재작성하지 않는다. 모든 시도는 새 path를 사용하며 모든 발행된 journal은 불변 읽기 전용 audit history로 남는다.

final artifact를 발행하기 전에 두 번째 정확한 compare-and-swap은 해당 input을 `.state/run-session.json`에서 닫힌 FINALIZED receipt로 seal한다. 보존된 읽기 전용 receipt에는 complete run projection, canonical claim 및 gate identity, manifest identity, journal identity, 정확한 artifact path/kind identity가 포함된다. `run.json`과 변경 가능한 manifest surface는 소비자일 뿐 권한이 아니다.

finalization은 복구 가능한 transaction boundary를 사용한다. session의 journal identity만 active authority다. inactive schema-valid UUID journal은 OPEN 작업을 차단하지 않는다. 고정된 legacy marker는 절대로 수락하지 않으며 명시적으로 recovery-required 상태로 남는다. Rollback은 journal의 정확한 OPEN source와 허용된 lock-recovery suffix만 검증하고 해당 OPEN session을 compare-and-swap하여 active authority를 원자적으로 지운다. 발행된 journal은 절대로 삭제하지 않는다. FINALIZING 및 FINALIZED recovery는 cleanup, rollback 또는 resume 전에 session의 정확한 journal identity를 독립 authority와 추가로 검증한다. Publication uncertainty는 가능하게 발행된 session/journal에 대해 schema-valid rollback 또는 recovery-required result로 조정되며 escaped traceback이 되지 않는다. `run.json` 발행 전에 validation 또는 publication이 실패하면 recovery는 안전하게 귀속할 수 있는 partial final artifact만 제거하고 정확하게 검증된 OPEN source를 복원한다. cleanup이 안전함을 증명할 수 없으면 recovery state를 보존하고 BLOCKED를 반환한다. 불변 final JSON은 동일 directory temporary에 완전히 기록되고 file-fsynced되며, exclusive link가 이를 보이게 하기 전에 read-only로 변경되고 mode-verified된 후 directory-fsynced된다. 따라서 post-chmod uncertainty는 아무것도 발행하지 않고 post-link uncertainty는 read-only file만 노출할 수 있다. 성공한 resume 및 `ALREADY_FINALIZED` recovery는 정확한 claim, gate, manifest, run, session, active journal에 대한 read-only sealing을 호출하고 검증한다. raw FINALIZED state의 failed recovery는 lock을 해제하기 전에 session과 안전하게 식별된 journal에 read-only mode를 다시 적용한다. 발행된 `run.json`은 불변으로 남는다.

제어 우선순위는 다음과 같이 유지된다.

1. 잘못되었거나 모순된 evidence graph: `INVALID_STATE`
2. 차단 policy violation: `POLICY_VIOLATION`
3. 실행된 child 실패: `FAIL`
4. 필수 blocked/not-configured/not-applicable/skipped leaf: `BLOCKED`
5. 내부적으로 일관된 integrity-only evidence: `PASS`, `completenessEvaluated: false`

## Phase 2 검증, Cache, Skill 및 Handoff

호출자 leaf input은 자유 형식 result summary가 아니라 닫힌 verification leaf artifact에 대한 reference가 된다. artifact에는 check ID, result, task key, gate invocation ID, commit SHA, policy SHA-256, producer ID, produced timestamp, expiry/freshness bound, evidence reference, evidence SHA-256, evidence schema identity가 포함된다. loader는 verified leaf를 반환하기 전에 참조된 evidence content와 digest를 검증한다.

각 gate evaluation은 canonical verification policy를 정확히 한 번 bounded-read한다. Strict JSON parsing, schema validation, policy SHA-256은 모두 같은 byte snapshot을 소비한다. 그런 다음 하나의 recursively immutable policy value와 digest가 native leaf 및 모든 external leaf validation을 통해 흐른다. gate는 policy path를 다시 열지 않으므로 교체가 한 policy의 applicability semantics와 다른 policy의 identity를 결합할 수 없다.

gate는 canonical policy만으로 PASS를 절대로 만들지 않는다. 필수 leaf의 명시적 evidence가 없으면 `NOT_CONFIGURED`가 `BLOCKED`로 매핑된다. 필수 leaf는 canonical policy가 선택된 change type에 그 check가 관련 없음을 명시적으로 표시하고 일치하는 reason code를 제공할 때만 `NOT_APPLICABLE`일 수 있다. 호출자는 이를 선택할 수 없다. Optional failure는 `FAIL`로 계속 보이며 aggregate를 `FAIL`로 만든다. Optional `NOT_CONFIGURED` 또는 policy가 허용한 inapplicability는 `NOT_APPLICABLE`로 남을 수 있다.

Cache key는 decision에 도달하기 위해 사용된 모든 input을 포함한다. 선택된 change type에 대한 정확히 정렬된 required-plus-optional check sequence는 `verification_gate`가 aggregate하는 sequence와 동일하다. 현재 entry point는 producer filter가 아니라 correlation 및 applicability identity다. 모든 check/producer-indexed binding에는 verified leaf-result reference와 digest, evidence path, digest, canonical schema가 포함된다. Policy digest, change type, entry point, task/gate correlation, commit, environment input, expiry는 계속 bound된다. 누락, extra, duplicate, reordered, wrong-producer, wrong-schema, changed, expired, unavailable, unmapped input은 STALE 또는 UNCERTAIN이며 PASS를 재사용할 수 없다.

native binding은 논리 result reference를 `ai/native-adapter-result.json`으로, 실제 policy evidence를 native-runtime-adapters schema 아래의 `ai/native-runtime-adapters.json`으로 추가 고정한다. 동일한 byte라도 복사되거나 임의의 native path는 stale이다. 현재 native result에는 task, gate, commit, policy, freshness를 포함하는 영속적 envelope가 없으므로 정확한 현재 native binding도 여전히 uncertain하며 verification decision을 fresh하게 만들 수 없다.

Skill catalog semantic validation은 승인된 모든 skill ID를 정확히 한 번 요구한다. Handoff semantic validation은 catalog/policy가 선택한 서로 다른 모든 skill을 정확히 한 번 요구하고 missing, duplicate, unknown, wrong-document skill binding을 거부한다.

## Phase 3A Host 소유 신뢰

저장소 policy는 지원되지 않는 baseline state를 설명할 수 있지만 trusted producer, signing key, supported host, authoritative current version, production attestation을 도입할 수는 없다. Production trust anchor 및 probe는 저장소와 fixture namespace 밖의 host 소유 input을 통해 제공된다. 저장소 evaluator는 명시적 host channel을 통해서만 public verification material을 수락하며 attestation과 일치하도록 요구한다.

저장소 fixture 및 temporary key는 test 전용으로 남는다. production CLI는 승격을 위해 fixture policy, fixture snapshot, 저장소 제어 trust-anchor path를 거부한다. authoritative probe가 없는 Codex Desktop에서는 canonical result가 `UNSUPPORTED`/`UNPROBED`로 남고 한정된 저장소 동작으로만 매핑된다. 절대로 native enforcement PASS가 되지 않는다.

Replay 방지는 영속적인 host 소유 nonce/attestation ledger 또는 host-verified consumption receipt를 사용한다. process-local set은 defense in depth로만 남을 수 있다. ledger key는 repository, producer, task, gate, attestation ID, nonce, signed event-set digest를 바인딩한다. 다른 process에서 재사용하면 거부된다.

resolution은 원래 detection event ID와 그 불변 task, 원래 gate invocation, deduplication identity, event digest를 바인딩해야 한다. 이후 resolution gate와 signed attestation은 같은 원래 detection을 가리켜야 한다. 관련 없는 event 또는 resolution은 BLOCKED다.

## Phase 3B Contract와 Enforcement 분리

명시적으로 서로 다른 두 check를 만든다.

- `phase-3b-repository-contract`: static/helper/schema regression test를 실행하며 저장소 contract가 유효하면 green일 수 있다.
- `phase-3b-native-enforcement`: 실제 CI/native enforcement를 나타내며 필수 provenance, native installation, durable evidence, remote runner proof가 NOT_CONFIGURED 또는 BLOCKED인 동안 green이어서는 안 된다.

저장소 workflow는 contract diagnostics를 발행할 수 있지만 예상 enforcement `NOT_CONFIGURED` exit code 3을 enforcement 성공으로 변환해서는 안 된다. GitHub branch protection과 host 소유 evidence가 구성될 때까지 project state는 contract workflow가 존재하지만 native CI enforcement는 `NOT_CONFIGURED`로 남음을 보고한다.

CI PASS는 repository, workflow path 및 immutable workflow identity, run ID, attempt, job ID, event name, head SHA, artifact ID, artifact digest, 포함된 모든 file의 digest를 바인딩하는 GitHub 소유 provenance envelope를 요구한다. evaluator는 native evidence, bypass evidence, resolution ID도 같은 run, attempt, job, commit에 바인딩한다. 저장소 `retainedRun` object는 GitHub provenance와 비교할 claim일 뿐이며 그 자체로 권한이 아니다.

## 테스트 전략

각 production change는 RED-GREEN-REFACTOR를 따른다. implementation 전에 집중된 regression test를 추가하고 의도한 이유로 실패하는 것을 관찰한다.

필수 Phase 1B 테스트:

- unbound 및 존재하지 않는 check evidence
- 모순된 not-run claim
- tampered final `run.json` 및 stale final projection
- 오래된 생성 요약
- FINALIZING 진입 후 validation 및 injected I/O failure, 안전한 rollback 또는 복구 가능한 journal 동작 증명
- 허용된 lock-recovery suffix validation을 포함하여 명시적 `ALREADY_OPEN` recovery까지 OPEN과 journal이 정상 작업을 차단함
- 저널 경로/UUID/다이제스트 변조, 최초 CAS 세션 식별자 바인딩, FINALIZED 영수증 식별자 일치
- traceback 없이 publication uncertainty 및 runtime exception reconciliation, 모든 failed FINALIZED recovery에서 read-only mode repair
- post-chmod 및 post-link publication uncertainty, six-file recovery mode repair, OPEN rollback CAS 후 applied-error, 보존된 immutable audit journal, 고정 legacy-marker 거부, 서로 다른 next-attempt journal
- blocking policy 및 child failure에 대한 result precedence

필수 Phase 2 테스트:

- evidence 없는 PASS
- 일치하지 않는 task, gate, commit, evidence digest, policy digest, producer
- 만료된 evidence 및 stale cache key
- 필수 호출자 작성 `NOT_APPLICABLE`
- optional `FAIL` 가시성
- duplicate skill ID 및 누락된 distinct required skill

필수 Phase 3A 테스트:

- 저장소 제어 signing key 및 supported-host declaration
- 위조되었거나 저장소가 작성한 host probe
- 별도 process/ledger instance의 attestation replay
- 관련 없는 resolution 및 원래 detection 불일치
- stale 및 replayed nonce
- 현재 Codex Desktop이 계속 unprobed 및 unsupported 상태임

필수 Phase 3B 테스트:

- 가짜 retained run
- 잘못된 head SHA, run attempt, job, workflow identity
- artifact ID 또는 digest 불일치 및 tampered artifact content
- 관련 없는 GitHub run의 evidence
- contract check 성공이 enforcement status와 계속 구별됨

contract test entry point는 complete core Python helper regression suite와 shell contract test를 실행한다. 검증에는 shell syntax, JSON schema, negative fixture, `git diff --check`, 실제 `.ai-runs` 부재, non-fixture `VERIFIED`/`DONE` 출력 부재, 깨끗한 GitHub Issue/PR 상태도 포함된다. Test fixture는 temporary directory와 무해한 helper input만 사용한다.

## 문서 및 상태 동기화

좁은 canonical document와 그 generated summary를 함께 업데이트한다. `ai/project-state.json`은 CI workflow 존재와 native enforcement availability를 구분한다. Phase 1B는 integrity-only로 남는다. Phase 3A current host는 host 소유 evidence가 제공되지 않는 한 unprobed/unsupported로 남는다. Phase 3B contract availability는 required-check 또는 enforcement completion을 의미하지 않는다.

## 완료 및 외부 경계

저장소 contract test는 저장소 contract PASS만 확립할 수 있다. Native Phase 3A 및 CI Phase 3B enforcement는 host/GitHub가 authoritative probe, trust anchor, durable replay storage, run/job/artifact provenance, branch-protection configuration을 제공할 때까지 `NOT_CONFIGURED`, `UNSUPPORTED`, `BLOCKED`로 남는다. GitHub Action 성공만으로는 Phase 3 enforcement PASS가 아니다. Issue #10과 #12는 별도로 권한이 부여된 workflow를 통해 독립 closure criteria가 충족되지 않는 한 열려 있는 상태로 남는다.
