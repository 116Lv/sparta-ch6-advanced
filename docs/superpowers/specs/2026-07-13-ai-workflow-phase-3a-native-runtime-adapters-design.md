# AI 워크플로 Phase 3A 네이티브 런타임 어댑터 설계

## 상태 및 범위

Phase 3A는 승인된 저장소 워크플로 주변에 호스트 네이티브 강제 적용 계약을 추가한다. Phase 1A부터 Phase 2C까지를 재설계하지 않는다. Phase 1B-3은 `completenessEvaluated: false` 및 `scope: INTEGRITY_ONLY`를 갖는 무결성 전용 상태로 유지된다.

이 단계는 adapter 탐색, command/file-read/search/tool-call 기능 보고, 우회 시도 탐지 및 정제된 기록, 완료 차단 및 Phase 2C 게이트 통합을 다룬다. Phase 3B CI 게이트, 영속적 CI 증거, 원격 runner 동등성 및 필수 CI adapter 가용성은 범위 밖으로 유지된다.

Gradle, build, 제품 test, server, Docker Compose, HTTP/curl/API, database, migration, seed, deployment 또는 infrastructure 명령은 실행할 수 없다. 검증에는 정적 검사, helper test, 계약 및 임시 fixture만 사용한다.

## 호스트 조사 및 지원 기준선

현재 호스트는 Codex desktop으로 식별되며 활성 agent에 저장소 shell, file read, search, tool-call 작업을 노출한다. 저장소 조사에서는 `.codex` hook 구성, host adapter 등록 manifest, pre-command, pre-file-read, pre-search, pre-tool-call interceptor를 설치할 수 있는 호출 가능 API를 찾지 못했다. 따라서 저장소 script는 호스트 전반의 interception을 증명할 수 없다.

Phase 3A에는 구현 시점에 지원되는 host-native adapter가 없으므로 supported-host registry는 비어 있고 최소 지원 host version도 없다. `codex-desktop`은 지원되는 adapter가 아닌 인식된 provisional identity다. canonical `hostVersion`은 `null`이고 `versionProvenance: UNPROBED`이며 저장소 policy는 version을 만들어서는 안 된다. 향후 host는 authoritative host version probe, 공식 hook-surface reference, trusted runtime producer identity, 그 source가 뒷받침하는 minimum version이 있을 때만 supported-host registry에 들어갈 수 있다. Supported-host matching에는 `versionProvenance: PROBED`와 authoritative SemVer 값이 필요하다.

알 수 없거나 provisional이거나 version 자격이 없는 host identity는 `UNSUPPORTED`다. host는 supported-host registry에 포함되었지만 유효한 runtime adapter 구성이 없는 경우에만 `NOT_CONFIGURED`가 된다.

현재 조사는 저장소 static probe로 재현할 수 있다. `.codex`, `.github`, `ai`, `scripts/ai`를 검사하고, `native`, `adapter`, `hook`, 네 surface 이름을 검색하며, 활성 host tool inventory에서 hook registration 작업을 검사한다. 이 probe들은 저장소 helper lifecycle hook은 찾았지만 native registration manifest 또는 호출 가능한 interceptor 설치 API는 찾지 못했다. 그 결과로 얻은 machine-readable current-host declaration은 저장소 policy evidence일 뿐이며 capability를 `UNSUPPORTED` 이상으로 승격할 수 없다.

## 검토한 접근 방식

### 권장: 호스트 선언을 갖는 저장소 계약

하나의 canonical repository contract를 유지하고 host-provided capability declaration을 수락한다. 저장소는 declaration을 검증하고 event를 정규화하며 redacted bypass attempt를 기록하고 native-adapter leaf result를 Phase 2C에 공급한다. 이 방식은 adapter에 product-command authority를 부여하지 않고 host 차이를 보존한다.

### 저장소 내 호스트별 구현

모든 host에 대해 executable integration을 제공한다. API가 있는 곳에서는 더 강한 interception을 제공할 수 있지만 저장소 policy를 host release detail에 결합하고, 현재 host에서는 registration surface 없이 정직하게 구현할 수 없다.

### 단일 범용 wrapper

모든 작업을 하나의 wrapper로 라우팅한다. command에는 단순하지만 editor read, search, external tool call을 신뢰성 있게 가로챌 수 없고, 부분 coverage를 host-native enforcement로 잘못 표현하게 된다.

host declaration을 갖는 repository contract를 선택한다.

## 책임 경계

`scripts/ai/command-runner.sh`는 계속 유일한 지원 product-command path다. Native adapter는 Gradle, server, Docker, HTTP, database, migration, seed, deployment, infrastructure 명령을 절대로 실행하지 않는다. host operation을 관찰하고 분류하고 차단하며 normalized event를 발행할 수 있다.

repository gateway는 command registration, parameter, approval, run lifecycle, cache reuse, evidence publication, integrity finalization을 소유한다. Native adapter는 host-surface discovery, 가능한 경우의 pre-operation observation, bypass detection, 가능한 경우의 immediate blocking, structured event delivery를 소유한다.

shell을 통해 file reading 또는 search를 시도하는 command는 `COMMAND` surface event로 기록하며 `FILE_READ` 또는 `SEARCH` 같은 intent classification을 갖는다. 이는 native file-read 또는 search hook의 증거가 아니다.

## 탐색 계약

canonical `ai/native-runtime-adapters.json` document는 저장소 작성 support policy만 포함한다.

- `schemaVersion`, `updatedAt`, 닫힌 adapter declaration 목록
- Adapter identity: `hostId`, `minimumHostVersion`, 지원 adapter version range, 허용된 trusted producer identifier
- 현재 호스트 분류, nullable host version, `UNPROBED|PROBED` provenance, non-secret repository probe reference
- 네 가지 필수 surface declaration: `COMMAND`, `FILE_READ`, `SEARCH`, `TOOL_CALL`
- Surface별 repository baseline status 및 reason code. Supported-host policy는 baseline 전용이며 runtime `ENFORCED`를 선언할 수 없다.
- Completion policy 및 Phase 2C check mapping

supported-host authority는 immutable `HostNativeTrust`로 internal evaluator에만 공급된다. 닫힌 descriptor, authoritative probe, pinned producer와 key fingerprint, replay-ledger root는 저장소 외부 경로로 해석되어야 한다. Canonical repository policy는 `supportedHosts`를 비워 두며, public repository CLI는 supported-host authority를 주입할 수 있는 descriptor, probe, ledger, policy, runtime snapshot, bypass fixture를 받지 않는다. 따라서 `UNSUPPORTED`/`UNPROBED` 경로에 남는다.

runtime discovery는 `ai/schemas/native-runtime-snapshot.schema.json`으로 닫힌 별도의 ephemeral snapshot이며 external host trust가 확립된 후에만 소비된다. 저장소 file은 authoritative host trust를 만들거나 수정할 수 없고 `ENFORCED`로 자체 승격할 수 없다. 각 향후 supported-host descriptor는 Ed25519 public-key fingerprint 및 producer identifier를 고정한다. snapshot은 raw public key를 제공하고 evaluator는 이를 signed fingerprint와 external trust pin 모두에 대해 hash한다. 현재 `taskKey`, 제한된 `bypassEventCount`, complete deduplicated event object 전체에 대해 계산한 `bypassEventSetSha256`를 바인딩한다. 해당 event object는 `eventId`로 정렬하고 object key를 정렬한 compact UTF-8 JSON으로 인코딩한다. 필수 `resolutionEventIds` member는 최대 64개 identifier의 고유 array이며 각 identifier는 최대 128자이고 현재 resolution을 주장하지 않을 때 비어 있다. Host producer는 `signature` member 없이 snapshot의 RFC 8785-compatible restricted canonical JSON byte에 서명하므로 task, event-set fact, resolution ID는 signed payload 내부에 있다. gate는 optional `cryptography.hazmat`로 detached signature를 검증한다. Restricted subset은 ASCII key와 string value, array, object, boolean, null, interoperable-range integer만 허용하며 float와 non-ASCII data는 거부한다. private key는 host가 소유하며 저장소, environment variable, command argument, snapshot 자체에서 절대로 수락하지 않는다.

signed snapshot은 signature와 producer identifier가 external host trust에 일치하고, host/version이 authoritative external probe와 일치하며, adapter version이 허용되고, signed `taskKey`와 one-use `gateInvocationId`가 current challenge에 일치하며, observation time이 300초보다 오래되지 않았고 미래가 아니며, 주장한 모든 blocking callback이 signed host-producer pre-execution challenge result를 통과할 때만 신뢰된다. Replay identity는 repository, producer, task, gate/challenge, attestation ID, nonce, signed event-set digest를 바인딩한다. trusted surface가 PASS가 되기 전에 file 및 directory durability를 갖는 external host-owned ledger에서 원자적으로 소비한다. process-local set은 defense in depth일 뿐이다. unsafe handle-relative primitive 또는 uncertain ledger publication, sync, close, cleanup은 fail closed한다. trust 후에는 PASS 또는 resolution binding을 수락하기 전에 signed bypass count와 digest가 complete supplied event set에 일치해야 한다. signature failure, unknown key, event-set mismatch, replay, callback failure, unavailable signature verification, ledger uncertainty는 supported host에서 `BLOCKED`다. 유효한 later-gate `RESOLVED` transition이 있으면 모든 current resolution `eventId`는 signed `resolutionEventIds` set에 정확히 일치해야 한다. missing, mismatched, duplicate, oversized, extra binding은 resolution-binding 또는 snapshot-contract reason으로 차단한다. Canonical `supportedHosts`는 비어 있으므로 현재 host는 PASS할 수 없고 모든 resolution claim은 계속 차단된다. temporary external trust, ledger, Ed25519 key는 complete supported-host path를 실행해 유효하게 서명되고 모든 `ENFORCED`인, 정확하게 bound된 resolution snapshot이 `PASS`를 만들 수 있음을 증명한다. 어떤 key, replay state, event-set state, resolution-binding state, evidence도 durable repository state가 되지 않는다.

result는 `claimedSurfaces`와 `trustedSurfaces`를 구분한다. 닫힌 snapshot claim은 진단을 위해 보고할 수 있지만 missing, malformed, stale, replayed, repository-authored, unallowlisted, unverifiable snapshot은 supported policy의 trusted `NOT_CONFIGURED` baseline을 유지하며 trusted `ENFORCED`를 절대로 발행하지 않는다. 허용되는 trusted transition은 `NOT_CONFIGURED -> AUDIT_ONLY -> ENFORCED`다. `UNSUPPORTED`는 host identity와 authoritative minimum version이 supported-host registry에 들어간 후에만 `NOT_CONFIGURED`가 될 수 있다. adapter는 fresh verified signature와 해당 surface의 verified signed blocking callback 없이 trusted `ENFORCED`를 발행할 수 없다.

## 기능 상태 의미

- `ENFORCED`: fresh discovery evidence가 작업이 실행 전에 관찰되고 fail-closed callback이 이를 차단할 수 있음을 증명한다. 탐지된 bypass는 차단된다.
- `AUDIT_ONLY`: 작업을 관찰 또는 재구성할 수 있지만 실행 전에 차단됨을 보장할 수 없다. 탐지는 evidence이지 enforcement가 아니다.
- `NOT_CONFIGURED`: host는 인식되지만 surface에 대해 유효하고 fresh한 adapter declaration/configuration이 없다.
- `UNSUPPORTED`: host 또는 surface에 선언된 host version에서 지원되는 adapter contract가 없다.

현재 Codex desktop 환경에서 네 native surface는 모두 `UNSUPPORTED`다. authoritative native registration surface나 minimum supported version이 증명되지 않았기 때문이다. repository gateway는 project command에 대해 enforced 상태로 남지만, 이 repository-only 사실은 native surface를 `ENFORCED`로 변경하지 않는다.

## 우회 시도 계약

각 normalized attempt는 다음을 기록한다.

- `attemptId`, 불변 `eventId`, `observedAt`, `hostId`, `hostVersion`, `adapterVersion`
- `surface`: `COMMAND`, `FILE_READ`, `SEARCH`, `TOOL_CALL`
- `operationType` 및 closed command intent classification. Native non-command surface는 operation type에 일치해야 하며 `commandIntent`를 가질 수 없다. shell-mediated logical operation은 `surface: COMMAND`와 일치하는 `commandIntent`를 사용한다.
- `statusAtObservation`
- `decision`: `BLOCKED` 또는 `ALLOWED_AUDIT_ONLY`
- `reasonCode`, `repositoryGatewayExpected`, `taskKey`, `gateInvocationId`, nullable 저장소 `runId`
- `deduplicationKey`, lifecycle state `DETECTED` 또는 `RESOLVED`, nullable `resolvedAt`, 닫힌 resolution reason
- `detectionEventId`, `detectionGateInvocationId`, `detectionEventSha256`: `DETECTED`에서는 모두 null이고 `RESOLVED`에서는 모두 non-null
- 정제된 target, argv, query, tool payload summary

contract는 raw environment value, authorization data, cookie, credential, request body, arbitrary tool payload, unbounded output을 금지한다. `summary` object에는 free-form string slot이 없다.

- `target`은 정확히 `NONE`, `REPOSITORY_PATH`이며 safe repository-relative `repositoryPath`가 있는 경우, 또는 `EXTERNAL_TARGET`이며 닫힌 `redactedCategory`와 SHA-256 digest가 있는 경우 중 하나다. absolute 또는 그 밖의 external raw target은 절대로 저장하지 않는다.
- `argumentSummary`는 `NONE`, `ALLOWLISTED_LITERALS`, `STRUCTURAL_PLACEHOLDERS` classification만, classification에 의해 제한된 0부터 64까지의 count, SHA-256 digest만 포함한다. argv, argument, raw-string member는 없다.
- `querySummary`는 digest 없는 `NONE`이거나 SHA-256 digest를 갖는 `TEXT_QUERY|STRUCTURED_QUERY`다. `toolPayloadSummary`는 digest 없는 `NONE`이거나 SHA-256 digest를 갖는 `STRUCTURED_PAYLOAD|OPAQUE_PAYLOAD`다. 이들의 closed conditional은 content, email, JSON, 기타 raw payload member를 거부한다.

허용된 모든 summary string은 512 Unicode scalar 및 512 UTF-8 byte로 제한되며 semantic secret-marker check 대상이다. redaction uncertainty는 publication을 차단하고 adapter leaf result를 `BLOCKED`에 매핑한다.

adapter producer는 observed attempt에 대해서만 record를 만든다. `NOT_OBSERVED`는 fabricated attempt가 아닌 adapter evaluation state다. `eventId`는 고유하며 같은 `eventId`의 반복 전송은 idempotent하다. `deduplicationKey`는 의미상 반복된 attempt를 그룹화하지만 original event를 절대로 제거하지 않는다. lifecycle이 `DETECTED`인 동안 attempt는 unresolved다. Resolution은 같은 `taskKey`, schema-allowlisted resolution reason, supported authoritatively probed host, fresh fully trusted all-`ENFORCED` adapter snapshot, 모든 current valid resolution에 대한 exact signed `resolutionEventIds` binding을 갖는 later gate invocation에서만 허용된다. signed resolution ID를 비교하기 전에 각 resolution은 immutable event ID, task, original gate invocation, deduplication key, canonical detection digest가 일치하는 prior detection 하나를 정확히 찾아야 한다. absent, duplicate, later, unrelated, digest-mismatched detection은 resolution을 invalid하게 만든다. exact valid resolution이 가리키지 않는 detection은 unresolved로 남는다. current gate가 발행한 모든 `DETECTED` event는 unresolved로 남으며 같은 deduplication group에 오래된 detection이 있어도 current-gate `RESOLVED` event가 소비할 수 없다. current `taskKey`의 일반 unresolved attempt는 snapshot trust evaluation 전에 차단한다. unsupported host, absent 또는 untrusted snapshot, missing, mismatched, extra binding은 resolution claim을 차단 상태로 유지한다.

## Fail-Closed 및 완료 정책

immediate fail-closed 동작은 `ENFORCED` surface에만 적용한다. `AUDIT_ONLY`는 attempt를 기록하고 Phase 3A host-native enforcement completion claim을 차단한다. `NOT_CONFIGURED`, `UNSUPPORTED`, stale discovery, adapter fault, malformed declaration, redaction uncertainty, missing required surface result, unresolved attempt도 해당 claim을 차단한다.

repository-only workflow는 host adapter가 구성되지 않았을 때 기존의 qualified Phase 2C result를 계속 보고할 수 있지만 native enforcement는 `NOT_CONFIGURED` 또는 `UNSUPPORTED`로 보고해야 한다. Phase 3A host-native enforcement PASS를 주장할 수 없다.

## Phase 2C 통합

Phase 3A는 승인된 minimum verification level을 변경하지 않고 모든 Phase 2C change type에 `native-runtime-adapter`를 required leaf check로 추가한다. Phase 3A evaluator는 `UNSUPPORTED` host를 host 및 네 trusted surface status를 reason과 evidence contract에 유지한 Phase 2C `NOT_APPLICABLE` leaf로 정규화한다. supported-host registry에 있는 host에서 `NOT_CONFIGURED`, stale discovery, signature failure, adapter fault, redaction uncertainty, unresolved attempt, unsafe resolution binding은 `BLOCKED`가 된다. unresolved bypass가 없고 exact signed resolution binding을 갖는 fully verified all-`ENFORCED` snapshot만 `PASS`에 도달한다. 이 방식은 supported-host fault를 completion-blocking으로 만들면서 resolution claim이 없을 때 unsupported host가 explicit repository-only qualification으로만 계속되게 한다.

- unresolved bypass attempt가 없고 모든 current resolution event에 exact signed binding이 있는 유효한 required `ENFORCED` surface: `PASS`.
- missing 또는 stale required capability: `NOT_CONFIGURED`, required이면 overall `BLOCKED`로 매핑.
- adapter 또는 redaction failure: `BLOCKED`.
- `ENFORCED` declaration에도 bypass가 허용되었거나 contract가 invalid한 경우: `FAIL`.
- unsupported host-native enforcement: adapter result `UNSUPPORTED`, explicit repository-only qualification과 함께 Phase 2C leaf `NOT_APPLICABLE`로 정규화.

Phase 1B-3 integrity result는 이 leaf를 충족하지 않으며 verification completeness를 확립할 수 없다.

## 검증 전략

test는 schema, external immutable host-trust path, public unsupported boundary, current-version provenance, restricted canonical byte, 실제 temporary Ed25519 verification, missing-crypto blocking, status transition, discovery freshness, minimum version, producer/key/signature/challenge/callback rejection, cross-process durable replay와 ledger fault, claimed/trusted separation, hook-specific semantic, bypass normalization, original-detection binding, redaction, completion blocking, Phase 2C mapping, repository gateway authority, current-host `UNSUPPORTED` 동작을 검증한다. 모든 mutable artifact는 복사된 repository fixture 밖 temporary directory 아래에 기록한다.

static check는 저장소 `.ai-runs`, non-fixture `artifact-manifest.json`, finalized non-fixture `run.json`, registry `VERIFIED` promotion이 생성되지 않음을 확인한다.

## Phase 3B 인계

Phase 3B는 CI adapter installation, CI fail-closed guarantee, remote-runner discovery, durable CI evidence, CI ledger provisioning 및 retention, required-check wiring, cross-host parity, CI retention/attestation을 소유한다. Phase 3A는 이후 작업에 필요한 local external-trust 및 durable-replay contract와 helper/static enforcement boundary만 제공한다.
