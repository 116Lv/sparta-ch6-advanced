# AI 워크플로 캐시

## 사람용 정책 참고 사항

`ai/workflow-cache.json`은 canonical Phase 2A cache record다. 이 Markdown file은 review 가능한 summary 및 policy note다. JSON이 canonical이다. Markdown은 실행 가능한 상태로 파싱하지 않는다.

제품 명령은 계속 NOT RUN이다. Phase 2A는 verification completeness를 평가하거나 durable command evidence를 만들거나 registry command를 `VERIFIED`로 표시하지 않는다.

repository script는 Phase 3 이전에 모든 host file read, search, external tool call을 가로챌 수 없다. 따라서 cache record는 reuse와 review를 지원하며 complete host telemetry가 아니다.

## 생성된 상태 요약

Canonical source: `ai/workflow-cache.json`

Phase 2A는 빈 cache로 시작했다. Phase 2B는 `ai/agent-handoff.json`, Phase 2A context-cache fallback summary, Phase 2B skills/handoff fallback summary를 연결하는 review 가능한 `HANDOFF_CONTEXT` record를 추가한다. Repo intake는 cache shape를 검증하고 proposal-only stale/uncertain entry를 보고한다. `HANDOFF_CONTEXT` entry의 `evidenceRefs`는 historical provenance를 보존하며 current handoff include/reusable scope를 허가하지 않는다. current reuse scope는 validated handoff에서만 오고 cache freshness는 entry의 digest-bound `key.paths`를 소비한다. raw log와 local `.ai-runs` evidence는 여기에 속하지 않는다.

current handoff cache digest는 unique activated trigger, effective required document, still-deferred document set, closed typed path scope를 포함한 schemaVersion 2 route-phase context를 bind한다. cache reuse는 `includePaths`를 넓히거나 canonical opt-in eligibility를 activation으로 취급하거나 deferred scope를 default search scope로 승격하거나 activated document를 optional로 만들지 않는다. route, phase, ownership, activation, required-context, active-Issue, typed-scope 변경에는 새 handoff/digest가 필요하다.

`READY` 또는 `PARTIAL` handoff에 대해 repo intake는 canonical handoff cache `STALE`/`UNCERTAIN` report를 detail을 보존한 top-level `BLOCKED` status 2로 변환한다. 이는 structural `PASS`가 stale route, phase, owner, trigger, Issue, typed-scope context reuse 허가로 오인되는 것을 막는다. 이미 `BLOCKED`인 handoff와 non-handoff cache entry는 handoff dispatch를 허가하지 않으므로 advisory invalidation report를 유지한다.

Repo intake는 single canonical ID `phase-2b-handoff-context`만 인식한다. 해당 entry가 `HANDOFF_CONTEXT`이고 정확히 하나의 `ai/agent-handoff.json` key binding을 가져야 하며 invalidation 계산 전 missing/duplicate canonical identity와 competing handoff binding을 거부한다. blocker status는 canonical entry report에서만 선택된다.

semantic validation은 globally unique cache entry ID와 각 path-based key 내 unique path identity도 요구한다. distinct entry 사이의 general input path 공유는 허용된다. canonical handoff path에 대한 경쟁 `HANDOFF_CONTEXT` binding만 cross-entry invalid state다.

Phase 2C는 verification completeness/task-change applicability에 `ai/verification-gates.md`, canonical `ai/verification-policy.json`, `scripts/ai/verification-gate.sh`의 review 가능한 link를 추가한다. `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, `FAIL` mapping은 change-type specific으로 남는다. 제품 명령은 static/helper gate에서 계속 NOT RUN이다.

Phase 3A는 `ai/native-runtime-adapters.json`, `ai/native-runtime-adapters.md`, closed native runtime snapshot schema를 reusable handoff context에 추가한다. runtime snapshot, signature, public key, callback proof, signed task/event-set fact, signed `resolutionEventIds`, challenge-consumption state, bypass attempt는 per-invocation input으로 남으며 reusable cache PASS evidence가 아니다. canonical current-host state는 unprobed version의 `UNSUPPORTED`로 남는다. raw-byte handoff digest는 `.gitattributes`가 `ai/agent-handoff.json`을 `-text`로 표시해 checkout EOL conversion을 막으므로 portable하다.

durable input이 있을 때 verification-decision cache entry는 선택된 change type에 대해 실제 aggregate된 exact ordered required-plus-optional check sequence를 bind한다. 모든 item은 check/producer-indexed이고 verified leaf-result reference/digest를 evidence path, digest, canonical schema에 bind한다. current entry point는 이 set을 절대로 좁히지 않는다. complete durable input이 없는 동안 canonical cache는 의도적으로 reusable verification decision을 포함하지 않는다.

native check는 정확한 logical result reference `ai/native-adapter-result.json`과 native-runtime-adapters schema를 갖는 exact canonical evidence `ai/native-runtime-adapters.json`만 수락한다. copied path의 matching byte는 stale이다. exact current binding도 native result에 durable task/gate/commit/policy/freshness envelope가 없으므로 uncertain이며 cache decision을 fresh하게 만들 수 없다.
