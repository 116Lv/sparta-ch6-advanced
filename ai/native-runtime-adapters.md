# 네이티브 런타임 어댑터 정책

`ai/native-runtime-adapters.json`은 기준 저장소 지원 정책이다. 실행 계약은 `ai/schemas/native-runtime-adapters.schema.json`, `ai/schemas/native-runtime-snapshot.schema.json`, `ai/schemas/native-adapter-result.schema.json`, `ai/schemas/native-bypass-attempt.schema.json`이다. 결과 매핑은 `ai/verification-gates.md`가 소유하며, 승인된 아키텍처는 `docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md`에 기록한다.

## 현재 호스트 탐색

기준 현재 host는 `hostVersion: null`, `versionProvenance: UNPROBED`인 `codex-desktop`다. `supportedHosts: []`가 기준으로 유지된다. 저장소 선언은 host version을 임의로 만들 수 없으며, supported-host 일치에는 권위 있는 `PROBED` SemVer 값이 필요하다.

이 host에는 네이티브 등록 manifest나 호출 가능한 interceptor 설치 API가 없다. 따라서 저장소 shell, file-read, search, tool-call 접근은 네이티브 interception을 증명하지 않는다.

| 표면 | 상태 | 사유 코드 |
| --- | --- | --- |
| `COMMAND` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `FILE_READ` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `SEARCH` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `TOOL_CALL` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |

이는 명시적 repository-only 한정과 함께 Phase 2C `NOT_APPLICABLE` leaf로 매핑된다. 네이티브 강제 적용이 아니다.

## 책임 경계

`scripts/ai/command-runner.sh`는 유일하게 지원되는 product-command 경로로 유지한다. 저장소 gateway는 명령 등록, parameter 검증, 승인 검사, run 수명 주기, 증거 게시, 무결성 finalization을 소유한다. 네이티브 adapter는 host 작업을 관찰·분류·차단·보고할 수 있지만 product command를 실행하거나 저장소 gateway 권한을 부여하지 않는다.

host producer는 권위 있는 host-version probing, pre-operation hook 등록, 일회성 challenge 처리, callback 실행, signing, 외부 내구성 replay ledger를 소유한다. 내부 evaluator는 변경 불가능한 `HostNativeTrust`를 통해서만 이 사실을 수락한다. descriptor, probe, ledger root는 저장소 밖에서 해석되어야 한다. 공개 저장소 CLI는 host trust, supported-host 정책, probe, ledger를 주입할 수 없으므로 기준 unsupported-host 경로에 남는다. 저장소 evaluator는 schema 검증, trust 검증, claimed/trusted 정규화, bypass 수명 주기 검사, Phase 2C 매핑을 소유한다.

## 서명된 스냅샷 신뢰

supported-host 스냅샷은 `ai/schemas/native-runtime-snapshot.schema.json`으로 닫힌다. 서명된 payload는 신뢰하는 `producerId`, `hostId`, `hostVersion`, adapter 버전, `observedAt`, 현재 `taskKey`, `gateInvocationId`, 제한된 bypass 이벤트 수 및 완전한 이벤트 집합 SHA-256, 제한된 고유 `resolutionEventIds` 배열, 네 표면 전체, 표면별 callback 증명, 원시 Ed25519 공개 키와 그 SHA-256 fingerprint를 결합한다. 분리된 `signature` member는 해당 member를 제거한 스냅샷에 서명한다.

신뢰에는 다음이 모두 필요하다.

- 현재 정책에 일치하는 supported host와 `PROBED` 권위 host version이 있다.
- producer, host, host version, adapter range, `gateInvocationId`가 일치한다.
- `observedAt`은 미래가 아니며 300초(`300 seconds`) 이내다.
- 제공된 공개 키는 서명된 fingerprint 및 정책에 고정된 공개 키 fingerprint 모두와 hash가 일치한다.
- `cryptography.hazmat` Ed25519 검증이 분리된 signature를 수락한다.
- 모든 `ENFORCED` 표면에는 callback이 실행 전 작업을 관찰하고 같은 challenge에 `BLOCKED`를 반환했다는 서명된 증거가 있다.
- 서명된 이벤트 수와 기준 이벤트 집합 digest가 제공된 모든 deduplicated bypass 레코드와 정확히 일치한다.
- 서명된 `resolutionEventIds`가 빈 배열을 포함해 현재 유효한 이후 gate `RESOLVED` 이벤트 ID와 정확히 같다.
- 신뢰 표면이 통과하기 전에 서명된 attestation identity를 외부 host 소유 replay ledger에서 원자적으로 소비한다. 프로세스 내 일회성 집합은 심층 방어일 뿐이다.

선택 crypto 의존성은 fail-closed다. Ed25519 지원을 사용할 수 없으면 `BLOCKED`다. evaluator는 private key를 수락하지 않는다. 안전한 handle-relative ledger 게시와 directory durability가 필요하며, 안전한 backend를 사용할 수 없거나 write, sync, close, cleanup이 불확실하면 fail-closed한다. test는 임시 외부 ledger, key, fixture만 만들며 key material, replay 상태, runtime 증거를 내구성 저장소 상태에 쓰지 않는다.

## 주장된 상태와 신뢰 상태 (Claimed And Trusted Status)

`claimedSurfaces`는 닫힌 스냅샷의 선언을 기록한다. `trustedSurfaces`는 완전한 trust chain을 통과한 내용만 기록한다. 누락된 스냅샷은 supported 정책의 `NOT_CONFIGURED` 기준선을 사용한다. malformed, 거부, stale, replayed 또는 검증 불가 스냅샷은 닫힌 주장을 표시할 수 있지만, trusted surface는 승격되지 않은 기준선으로 유지하며 절대 `ENFORCED`가 되지 않는다.

supported-host 정책 표면은 `NOT_CONFIGURED`로 제한되며 저장소 파일은 runtime `ENFORCED`를 선언할 수 없다. 서명된 스냅샷은 표면을 신뢰하는 `AUDIT_ONLY` 또는 `ENFORCED`로 승격할 수 있지만, `PASS`에는 유효한 서명 callback 증명과 미해결 bypass 시도가 없는 네 신뢰 표면 전체의 `ENFORCED`가 필요하다. 서명된 resolution ID는 누락, 상이 또는 추가된 현재 resolution 이벤트의 증거로 재사용할 수 없다.

## 기준 서명 바이트

signature encoder는 RFC 8785 호환 제한 부분집합(`RFC 8785-compatible restricted subset`)을 사용한다. 서명 데이터에는 ASCII 문자열 key 객체, 배열, ASCII 문자열, boolean, null, 상호 운용 범위 `[-9007199254740991, 9007199254740991]`의 정수만 포함할 수 있다. float, 비ASCII key 또는 값, 다른 Python type은 거부한다. ASCII key는 Python `sort_keys` 순서를 RFC 8785 key 순서와 byte-identical하게 하며, compact UTF-8 JSON에는 중요하지 않은 whitespace가 없다.

정규화 전 알려진 vector:

```json
{"z":["ASCII",true,null,7],"signature":{"algorithm":"Ed25519","encoding":"BASE64","value":"excluded"},"a":{"k":"v"}}
```

`signature` 제거 후 알려진 기준 바이트:

```json
{"a":{"k":"v"},"z":["ASCII",true,null,7]}
```

## 구조화된 정제와 bypass 수명 주기

`ai/schemas/native-bypass-attempt.schema.json`은 닫힌 요약만 허용한다. 저장소 target은 제한된 안전 상대 경로다. 외부 target, argument set, query, tool payload는 적용할 때 닫힌 분류, 수, SHA-256 digest를 사용한다. 원시 authorization 데이터, cookie, credential, environment 값, 요청 본문, argv, query text, payload, 절대 외부 target은 금지한다. 정제 불확실성은 완료를 차단한다.

`surface`, `operationType`, `commandIntent`는 닫힌 의미 matrix를 사용한다. 네이티브 `FILE_READ`, `SEARCH`, `TOOL_CALL` 레코드는 작업과 일치하고 command intent를 생략한다. shell 매개 논리 작업은 `COMMAND`를 표면으로 유지하고 논리 작업에 맞는 command intent를 가진다.

각 관찰 이벤트는 `DETECTED`로 시작한다. `detectionEventId`, `detectionGateInvocationId`, `detectionEventSha256` 필드는 null이다. 같은 `eventId`의 반복 전달은 멱등이며 `deduplicationKey`는 이벤트를 group화하지만 원본을 제거하지 않는다. 이후 `RESOLVED` 이벤트는 같은 task, 이후 관찰, 다른 gate invocation, 닫힌 allowlisted resolution reason, null이 아닌 원본 탐지 binding 필드를 사용해야 한다. evaluator는 변경 불가능한 이벤트 ID, task, 원본 gate invocation, deduplication identity, 기준 이벤트 digest가 모두 resolution과 일치하는 선행 `DETECTED` 이벤트를 정확히 하나 찾는다. 존재하지 않거나 중복되거나 이후이거나 관련 없거나 digest가 다른 탐지는 해제할 수 없고, group의 다른 탐지는 미해결로 남는다. 현재 gate의 탐지는 현재 gate resolution이 뒤따르더라도 미해결로 남는다.

유효한 이후 gate 전환은 지원되고 권위 있게 probed된 host에서만 해제할 수 있다. 해당 host에는 서명 task, 완전한 이벤트 수, 기준 이벤트 집합 digest가 gate 입력과 일치하고 서명된 `resolutionEventIds`가 모든 현재 resolution 이벤트와 일치하는 최신 신뢰 전체-`ENFORCED` 스냅샷이 있어야 한다. 누락 스냅샷 및 누락·불일치·중복·과대·추가 서명 binding은 차단하며, 기준 unsupported-host resolution 주장도 차단한다. 일반 미해결 시도는 스냅샷 trust 평가 전에 차단하고 Phase 3A는 내구성 bypass 증거를 보존하거나 게시하지 않는다.

## Phase 3B 소유권

Phase 3B는 CI adapter 설치, remote-runner 보장, 내구성 CI 증거, CI ledger 프로비저닝 및 보존, required-check 연결, cross-host parity, attestation을 소유한다. Phase 3A는 로컬 external-ledger 계약과 fail-closed evaluator만 제공한다. Phase 1B-3은 `INTEGRITY_ONLY`로 유지하며, 어떤 native 결과도 레지스트리 명령을 `VERIFIED`로 승격하거나 Issue를 닫거나 제한 없는 전체 `DONE` 주장을 승인하지 않는다.
