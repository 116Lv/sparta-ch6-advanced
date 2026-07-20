# AI 워크플로 에이전트 인계

## 사람용 정책 참고 사항

`ai/agent-handoff.json` schemaVersion 2는 canonical Phase 2B handoff packet이다. JSON이 canonical이다. Markdown은 실행 가능한 상태로 파싱하지 않는다. 제품 명령은 Phase 2B에서 계속 NOT RUN이다.

## 필수 컨텍스트 상태

모든 reusable 또는 delegated handoff는 다음을 기록한다.

- `routeId`, `taskPhase`, closed `activityId`, `owningFeature`, `contextStatus`
- workflow rediscovery 밖에서는 비어 있는 closed `rediscoverySubjects`
- `repositoryContextRequired`와 unique exact `selectedDocuments`
- unique `activatedTriggers`, `readDocuments`, `deferredDocuments`에 아직 있는 document, canonical `deferredDocumentTriggers`
- current `includePaths`, canonical `deferredPaths`
- `decisions`, `openQuestions`, `remainingWork`
- `remainingVerificationEvidence`, `rerouteTriggers`
- Issue-backed work-log context를 선택하지 않았으면 `activeIssue: null`, 그 외에는 active Issue summary와 current role log만
- skill, reusable-context, command-boundary, later-phase record

snake-case work-log equivalent는 `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, `github_reconciliation_status`로 남는다.

## 검증 및 차단

helper는 exact route-phase pair를 선택하고 `activityId` 호환성을 검증한다. activation은 해당 activity/pair에 canonical이어야 한다. effective required context는 base required document와 activated document trigger가 매핑한 document를 결합한다. 하나라도 unread이거나 activity-mandatory trigger가 inactive이면 handoff는 READY/PARTIAL일 수 없고 `BLOCKED`이거나 validation에 실패해야 한다. planning은 task를 성급히 요구하지 않고 plan context를 요구한다. execution/verification handoff는 task gate를 유지한다. independent audit은 implementation handoff를 가장하지 않고 verification policy를 요구한다. completion은 모든 completion gate를 유지한다. `feature-work`는 `owningFeature: none`으로 dispatch할 수 없다.

workflow rediscovery는 `ai/context-map.json` 하나로 시작한다. READY/PARTIAL은 적어도 하나의 canonical subject를 선택하고 subject의 exact trigger를 activate하며 exact mapped document를 read/include한다. unknown/non-rediscovery subject, unselected subject trigger, extra subject document/scope는 invalid다.

handoff는 document-trigger identity당 정확히 하나인 full canonical trigger mapping을 보존한다. duplicate mapping은 collapse하지 않고 invalid다. `deferredDocuments`에는 activated document trigger를 제거한 뒤에도 deferred인 document만 있고 `readDocuments`와 overlap할 수 없다. 모든 read는 include scope에 포함된다. selected document는 read되고 matching exact scope를 사용한다. activated deferred document도 matching exact scope를 사용한다. additional scope는 phase default, direct exact selection, activated opt-in 아래 materialized된 exact path로 제한된다. READY/PARTIAL은 materialized opt-in path를 read한다. BLOCKED는 해당 read를 생략할 수 있지만 scope를 widen하거나 foreign scope를 사용할 수 없다. 이 identity/scope 검사는 BLOCKED handoff에도 적용된다. phase/route 변경에는 re-routing과 new context check가 필요하다.

Answer Mode는 진정으로 repository-independent response에 대해 empty `selectedDocuments`와 `repositoryContextRequired: false`를 설정할 수 있다. flag를 true로 설정하면 적어도 exact document 하나를 선택한다. Light Route는 항상 flag를 true로 설정하고 적어도 exact document 하나를 선택한다. feature/repository-workflow phase도 flag를 true로 설정하지만 canonical required document가 이미 context를 제공하면 `selectedDocuments`는 비워 둘 수 있다.

## 좁은 Active-Issue 범위

`{"kind":"subtree","path":"ai/work-logs"}` scope는 전역적으로 deferred된다. Answer, light-structure, feature-requirements, activated Issue/work-log scope가 없는 모든 handoff는 `activeIssue: null`을 사용한다. work-log opt-in activation 또는 work-log include/reusable ref에는 `activeIssue` object와 canonical trigger가 필요하다. number, 정확한 `https://github.com/116Lv/sparta-ch6-advanced/issues/{number}` URL, summary, distinct role ref는 정확히 일치해야 한다. active URL에는 trailing slash, query, fragment, credential, alternate host, port, scheme가 허용되지 않는다. 이후 `includePaths`에는 active ref set의 exact scope만 포함될 수 있고 READY/PARTIAL은 selected active ref를 모두 읽는다. foreign, unlisted, subtree, direct-children, descendant scope는 `BLOCKED`에도 invalid다. `reusableContextRefs`는 repository-safe exact path이며 excluded scope에 들어갈 수 없고 같은 active set의 work log만 참조할 수 있다. historical `githubIssue`, `phase3AIssue` record는 별도 provenance로 남으며 current active identity와 같을 필요가 없다. prior role log는 recovery hint일 뿐 canonical authority가 아니므로 owning spec, policy, schema, ADR에서 decision을 확인한다.

## 재사용 계약

context를 재발견하기 전에 current handoff와 exact canonical reference를 reuse한다. 모든 historical cache entry, work log, skill document, workflow policy를 로드하지 않는다. cache/context exception에는 escalation이 필요했던 route, phase, trigger, stale/missing input을 기록해야 한다.

`skillIds`는 catalog의 complete distinct ID set과 정확히 한 번씩 같아야 한다. schema uniqueness와 helper semantic validation이 모두 이 set을 강제한다.

`notRunProjectCommands`도 free-form note가 아닌 closed ordered boundary다. `Gradle`, `build`, `product/unit project tests`, `application server`, `Docker Compose`, `HTTP/curl/API`, `database`, `migration`, `seed`, `infrastructure commands`. schema/helper는 omission, addition, duplicate, replacement, reordering을 모두 거부한다.

## 검증 및 완료 경계

다른 phase로 넘어가는 subagent 작업은 re-route해야 한다. subagent completion report는 Phase 2C verification, QA gate, completion evidence, done claim, Issue closure check를 대체하지 않는다. missing verification/completion evidence는 `BLOCKED` 또는 `PARTIAL`로 남는다.

Phase 2B는 repository `.ai-runs`, artifact manifest, finalized `run.json`, registry `VERIFIED` transition, verification-completeness claim, issue-backed closure claim, reconciliation-complete claim, unqualified overall DONE claim을 만들지 않는다.

## Phase 3A 네이티브 어댑터 인계

현재 canonical packet은 active Issue #10의 repository-wide `INDEPENDENT_AUDIT` packet이다. activated schema/active-Issue trigger는 직접 필요한 schema, 해당 Issue summary, implementation/review role log에만 opt in한다. current host는 `UNSUPPORTED`이며 overall PASS는 repository-only qualified로 남는다. verification gate는 precomputed native result를 수락하지 않으며 `scripts/ai/command-runner.sh`는 계속 유일한 지원 product-command path다. Phase 3B는 durable CI evidence, remote-runner guarantee, cross-host parity를 소유한다.
