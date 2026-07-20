# AI 워크플로 검증 게이트

## 사람용 정책 참고 사항

`ai/verification-policy.json`은 verification completeness, task/change applicability, workflow entry point, result mapping을 위한 canonical Phase 2C source다. 이 Markdown file은 agent와 reviewer에게 policy를 설명한다. JSON이 canonical이다. Markdown은 실행 가능한 상태로 파싱하지 않는다.

Phase 2C helper/static verification에서 제품 명령은 계속 NOT RUN이다. `scripts/ai/verification-gate.sh`는 static/helper/contract input만 평가하며 Gradle, build, product/unit project test, server, Docker Compose, HTTP/curl/API, database, migration, seed, infrastructure 명령을 실행해서는 안 된다.

## 진입점

- `verification-level`: change type을 required verification check에 매핑한다.
- `api-smoke`: API-visible work의 real API smoke requiredness를 매핑한다.
- `failure-triage`: rerun 또는 continuation 전 failed/blocked leaf status를 기록한다.
- `review`: independent review와 delegated-work readiness를 검사한다.
- `done-claim`: done claim 전 completion evidence가 applicable한지 검사한다.

## 작업/변경 적용 가능성

Phase 2C는 `ai/verification-policy.json`에서 change type별 task/change applicability를 정의한다. 지원되는 change type은 `documentation-only`, `static-workflow`, `domain-logic`, `db-api`, `auth-permission`, `critical-data`, `user-flow`이다.

verification completeness는 선택된 change type의 모든 required check에 allowed mapped result가 있고 every inapplicable check가 reason과 함께 explicit하게 mapped됨을 뜻한다. `tracking_status`가 `pending_issue`인 동안 complete fallback으로 implementation QA가 통과할 수 있지만 issue-backed closure, reconciliation-complete, unqualified overall DONE은 계속 차단된다.

## 결과 매핑

- required check의 `NOT_CONFIGURED`는 `BLOCKED`로 매핑된다.
- irrelevant 또는 optional check의 `NOT_CONFIGURED`는 `NOT_APPLICABLE`로 매핑된다.
- missing non-native leaf는 `NOT_CONFIGURED`다. canonical policy는 configuration과 applicability를 설명하지만 leaf `PASS` evidence를 공급하지 않는다.
- caller-supplied `NOT_APPLICABLE`은 선택된 change type이 해당 check의 canonical `notApplicableFor` array에 있을 때만 허용된다. 그렇지 않으면 required check를 포함해 `BLOCKED`로 매핑된다.
- internal native adapter의 canonical unsupported-host result는 유일한 non-caller exception이며 explicit repository-only qualification을 유지한다.
- required check의 `BLOCKED`는 `BLOCKED`로 남는다.
- `FAIL`은 required/optional check 모두에서 `FAIL`로 보이며 aggregate result에서 `BLOCKED`보다 우선한다.

`NOT_APPLICABLE`은 Markdown summary에서 `N/A`로 표시할 수 있지만 executable JSON은 `NOT_APPLICABLE`을 저장한다.

모든 check output은 두 closed shape 중 하나로 같은 다섯 leaf-identity key를 가진다. verified external/native check는 다섯 key가 모두 non-null이어야 한다. missing, synthesized, policy-derived check는 다섯 key가 모두 null이어야 하며 raw 또는 mapped `PASS`/`FAIL`을 보고할 수 없으므로 verified evidence로 validation될 수 없다. external leaf의 `leafResultSha256`은 loader가 path를 다시 열지 않고 parse/accept한 exact bounded byte에서 파생되며 `evidenceRef`는 존재할 때 bound evidence artifact를 가리킨다. internal native leaf는 `ai/native-adapter-result.json`, 해당 canonical in-process result의 SHA-256, canonical producer, checked-out commit, canonical policy digest를 기록한다. 한 gate evaluation은 `ai/verification-policy.json`을 정확히 한 번 bounded-read한다. strict parsing, schema validation, SHA-256 derivation, native identity, external leaf check는 같은 recursively immutable snapshot을 사용하므로 replacement race가 policy semantic과 identity를 섞을 수 없다.

## 네이티브 런타임 어댑터 말단

`native-runtime-adapter`는 모든 change type의 internal-only required check다. `scripts/ai/verification-gate.sh`는 `--task-key`, `--gate-invocation-id`를 요구하며 진단을 위해 `--runtime-snapshot`, `--bypass-attempts`를 in-process evaluator에 직접 전달할 수 있다. 이 repository input은 immutable external `HostNativeTrust`를 제공하거나 public path를 canonical unsupported host 이상으로 승격할 수 없다. public `native-adapter-gate` CLI는 supported-host PASS를 만들 수 있는 host descriptor, probe, trust anchor, ledger, policy, snapshot, bypass fixture를 수락하지 않는다. gate는 precomputed native adapter result를 절대로 수락하지 않는다. 이 check ID를 포함하는 일반 `--leaf-results-file` input은 forged state이며 leaf lookup 전에 `NATIVE_ADAPTER_LEAF_FORGED`와 함께 `INVALID_STATE`를 반환한다.

verification loop는 current correlation으로 `native_adapter_phase2c_leaf()`를 호출한다. 이 helper는 canonical `ai/native-runtime-adapters.json`에 대해 `native_adapter_gate()`를 호출한다. check는 static `registryCommandId: null` PASS fallback에 도달하지 않는다. invalid task/gate correlation은 fail closed한다.

현재 host version은 `null`/`UNPROBED`이고 host는 `UNSUPPORTED`다. adapter result `UNSUPPORTED`는 `HOST_UNSUPPORTED` reason과 함께 raw/mapped `NOT_APPLICABLE`로 매핑된다. overall PASS는 `REPOSITORY_ONLY_HOST_UNSUPPORTED`로 qualified되며 repository gate만 증명한다. supported-host matching에는 authoritative `PROBED` version이 필요하다. supported host에서 missing authenticated enforcement은 `NOT_CONFIGURED` 또는 `BLOCKED`다. producer/key/signature/freshness/challenge/replay/callback/crypto, redaction, correlation, bypass fault는 `BLOCKED` 또는 `FAIL`로 남는다.

result는 `claimedSurfaces`와 `trustedSurfaces`를 구분한다. policy surface는 baseline 전용이며 runtime `ENFORCED`를 선언할 수 없다. missing/rejected snapshot은 trusted `NOT_CONFIGURED` surface를 유지한다. immutable external host trust와 closed, fresh, Ed25519 snapshot, signed callback proof, external durable replay ledger의 atomic consumption만 trusted `ENFORCED`를 발행할 수 있다. process-local replay set은 defense in depth뿐이다. 네 trusted surface와 unresolved bypass 부재가 native adapter `PASS`에 모두 필요하다. later-gate `RESOLVED` event는 current resolution event ID를 signed snapshot byte 안의 bounded unique `resolutionEventIds` array와 비교하기 전에 event ID, task, original gate invocation, deduplication key, canonical detection digest로 prior detection 하나에 정확히 bind되어야 한다. missing, unrelated, multiple, later, digest-mismatched detection과 missing, mismatched, duplicate, oversized, extra signed resolution ID는 canonical unsupported host에서의 resolution claim 또는 trusted snapshot 없는 claim처럼 차단한다. canonical `supportedHosts`는 비어 있으므로 이 supported path는 temporary external host trust, key, ledger로만 실행되며 durable repository evidence를 만들지 않는다.

`scripts/ai/command-runner.sh`는 계속 유일한 지원 product-command path다. native adapter는 product command를 실행하지 않는다. Phase 3B는 CI adapter installation, remote-runner guarantee, durable CI evidence, CI ledger provisioning/retention, cross-host parity를 소유한다.

## 증거 경계

Phase 2C 및 Phase 3A static/helper gate는 repository `.ai-runs`, artifact manifest, finalized `run.json`, registry `VERIFIED` transition, issue-backed closure claim, reconciliation-complete claim, unqualified overall DONE claim을 만들지 않는다. Phase 1B-3은 scope `INTEGRITY_ONLY`와 함께 `completenessEvaluated: false`로 남는다. real project verification은 supported command-runner evidence path가 명시적으로 사용되지 않는 한 계속 NOT RUN이다.
