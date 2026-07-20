# AI 워크플로 캐시 정책

## 사람용 정책 참고 사항

`ai/workflow-cache.json`은 canonical Phase 2A cache record다. 이 Markdown file은 freshness와 invalidation policy를 설명한다. JSON이 canonical이다. Markdown은 실행 가능한 상태로 파싱하지 않는다.

제품 명령은 계속 NOT RUN이다. Phase 2A는 verification completeness를 평가하지 않고 ignored local evidence를 durable cross-machine proof로 승격하지 않는다.

## 캐시 키

file-read entry는 normalized repository-relative path와 SHA-256 content digest로 키가 지정된다. command evidence summary는 지원 command gateway의 command ID, argv hash, working directory, declared input fingerprint, allowlisted environment fingerprint로 키가 지정된다.

모든 cache entry ID는 전역적으로 고유하다. 하나의 path-based cache entry 안에서는 경쟁 record가 서로 다른 digest를 가져도 각 repository-relative path identity는 한 번만 나타날 수 있다. kind와 reuse purpose가 다를 수 있으므로 서로 다른 cache entry가 같은 일반 input path를 정당하게 bind할 수 있다. 아래의 더 엄격한 canonical handoff anti-spoof rule은 유일한 cross-entry path exclusion으로 남는다.

verification-decision entry는 task key, gate invocation ID, checked-out commit SHA, change type, entry point, verification-policy SHA-256, 선택된 change type의 required check 뒤 optional check를 `verification_gate`가 소비하는 정확한 ordered check set을 포함하는 distinct closed key를 사용한다. entry point는 correlation identity와 applicability input으로 남으며 consumed set을 filter하지 않는다. 각 producer/check-indexed binding에는 verified leaf-result reference와 SHA-256, evidence path, SHA-256, canonical schema가 포함된다. key는 relevant environment fingerprint와 expiry도 bind한다. task/gate identifier는 mandatory lookup identity이지만 repo intake는 이들에 대해 external authority를 주장하지 않는다. non-null environment fingerprint는 authoritative current environment mapping이 생길 때까지 `UNCERTAIN`이다.

## 최신성 규칙

cache entry는 모든 declared path가 예상대로 존재하고 모든 recorded digest가 일치할 때만 `FRESH`다. verification-decision reuse에는 current commit/policy digest, exact ordered canonical check/producer set, 모든 leaf-result/evidence digest, canonical evidence schema, leaf correlation/freshness, unexpired decision도 일치해야 한다. missing, extra, duplicate, reordered, wrong-producer, wrong-schema, digest-mismatched known binding은 `STALE`이다. unavailable path 또는 unmapped classification, task/gate identity, policy/commit source, environment input은 다른 proven mismatch/expiry가 entry를 `STALE`로 만들지 않는 한 `UNCERTAIN`이다.

native cache binding에는 추가 fixed identity가 있다. `leafResultRef`는 정확히 `ai/native-adapter-result.json`이어야 하고 evidence는 `ai/schemas/native-runtime-adapters.schema.json`으로 검증된 `ai/native-runtime-adapters.json`이어야 한다. byte/digest가 일치해도 복사되거나 임의의 native result/evidence path는 `STALE`이다. 현재 native result schema에는 durable task, gate, commit, policy, freshness envelope가 없으므로 다른 조건이 정확한 native binding도 해당 correlated durable envelope가 생길 때까지 `UNCERTAIN`이며 `FRESH` verification decision을 막는다.

canonical cache는 commit 또는 short-lived expiry가 self-referential이거나 즉시 stale해질 reusable verification PASS decision을 materialize하지 않는다. 이 decision은 모든 durable input이 있을 때만 기록할 수 있다.

## 보수적 Invalidation

dependency mapping이 불완전하거나 모호하면 workflow는 unsafe reuse보다 re-verification을 선택한다. Phase 2A repo intake는 proposal-only `projectStateRefresh`, `commandDiscoveryUpdates` record를 보고할 수 있지만 command를 실행하거나 `.ai-runs`를 만들거나 registry command를 `VERIFIED`로 표시하지 않는다.

route/handoff reuse는 phase-sensitive다. 한 phase의 cached read가 이후 phase의 required document를 optional로 만들지 않으며 task-phase, owning-feature, activated-trigger, effective-required, still-deferred-set 변경은 handoff가 re-routed될 때까지 reuse를 무효화한다. deferred document는 activation까지 unread로 남고 이후 required context가 되어 still-deferred set에서 나간다.

`READY` 또는 `PARTIAL` handoff의 canonical `HANDOFF_CONTEXT` entry가 `ai/agent-handoff.json`을 bind하지만 `STALE`/`UNCERTAIN`을 보고하면 repo intake는 fail closed한다. top-level result는 status 2, `HANDOFF_CONTEXT_CACHE_STALE` 또는 `HANDOFF_CONTEXT_CACHE_UNCERTAIN`인 `BLOCKED`이며 full cache invalidation report는 `data`에 남는다. 이미 `BLOCKED`인 handoff는 dispatch-ready가 아니므로 cache result는 advisory로 남고 repo intake는 여전히 structural validation을 통과할 수 있다. 다른 cache kind의 `STALE`/`UNCERTAIN` entry는 advisory로 남는다.

canonical handoff cache identity는 closed다. 정확히 하나의 entry가 ID `phase-2b-handoff-context`를 가져야 하고 그 entry는 `HANDOFF_CONTEXT`이며 key는 `ai/agent-handoff.json`을 정확히 한 번 bind해야 한다. missing, duplicate, wrong-kind, wrong-path canonical entry는 invalid state다. canonical handoff path를 bind하는 다른 `HANDOFF_CONTEXT` entry는 ambiguous invalid state이며 freshness evaluation 전에 거부되어 spoof entry가 `BLOCKED`를 강제하거나 reuse를 허가할 수 없다.

## 증거 경계

repository script는 Phase 3 이전에 모든 host file read, search, external tool call을 가로챌 수 없다. 따라서 cache policy는 total technical interception을 주장하지 않고 structured record, work log, handoff note, review gate를 결합한다.

## Phase 3A 네이티브 경계

현재 host-native adapter state는 `hostVersion: null`, `versionProvenance: UNPROBED`인 `UNSUPPORTED`다. native runtime snapshot과 bypass-attempt reference는 task/gate ID로 correlation된 per-invocation input이며 reusable cached PASS result가 아니다. cached, repository-authored, digest-mismatched, correlation-mismatched, 그 밖의 precomputed `native-runtime-adapter` leaf는 verification을 충족할 수 없다. supported-host snapshot은 fresh하고 Ed25519-verified이며 task와 one-use gate challenge에 bind되고 signed count/SHA-256으로 complete canonical bypass event set을 authenticate하며 current later-gate resolution event ID를 signed `resolutionEventIds`에 정확히 bind해야 한다. in-process replay와 resolution-binding state는 ephemeral이며 Phase 3B가 cross-process challenge와 event-set durability를 소유한다.

`FRESH` handoff cache entry는 raw-byte SHA-256을 사용한다. `.gitattributes`는 `ai/agent-handoff.json`을 `-text`로 표시하므로 Git은 line ending을 재작성하지 않으며 recorded digest는 LF/CRLF-default checkout host에서 재현 가능하다.

`scripts/ai/command-runner.sh`는 계속 유일한 지원 product-command path다. native adapter는 cache reuse로 command execution authority를 얻지 않는다. unsupported-host verification은 explicit repository-only qualification이 있을 때만 통과할 수 있고 supported-host fault는 completion-blocking으로 남는다. Phase 3B는 durable CI evidence, remote-runner cache parity, CI adapter availability를 소유한다.
