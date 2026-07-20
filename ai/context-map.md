# AI 워크플로 컨텍스트 맵

## 사람용 정책 참고 사항

`ai/context-map.json` schemaVersion 2는 Phase 2A route, phase, lazy-loading, search-scope rule의 canonical source다. JSON이 canonical이다. Markdown은 실행 가능한 상태로 파싱하지 않는다.

지배 원칙은 다음과 같다. **늦게 읽고, 좁게 읽으며, task phase가 요구할 때만 escalate한다.** deferred reading은 필수 document 또는 gate를 건너뛸 수 있게 하지 않는다. 선택한 route 또는 phase를 알 수 없거나 불완전하거나 더 이상 task와 일치하지 않으면 re-route한다. 그래도 필수 context를 확립할 수 없으면 추측하지 말고 `BLOCKED`를 보고한다.

제품 명령은 계속 NOT RUN이다. Phase 2A는 verification completeness를 평가하거나 registry entry를 `VERIFIED`로 표시하거나 host-wide interception을 주장하지 않는다.

## 정식 경로 및 단계 모델

| Route | 소유 기능 | Canonical phase | 기본 동작 |
|---|---|---|---|
| `answer` | 없음 | `answer` | 직접 관련된 material만 읽는다. workflow-policy를 미리 읽지 않는다. |
| `light-structure` | 없음(direct-document route) | `light-structure` | 좁은 file 또는 search result를 사용한다. broad mapping이 실제로 필요할 때만 onboarding index를 로드한다. |
| `feature-work` | 필수 | `feature-requirements`, `implementation`, `verification`, `completion` | `specs/{feature}/spec.md`로 시작한다. trigger 전까지 plan, task, decision, checklist, verification, completion document를 지연한다. |
| `repo-wide-ai-workflow` | 없음 허용 | `implementation`, `verification`, `completion`, `workflow-rediscovery` | phase owner document만 로드한다. rediscovery는 context map으로 시작하고 선택된 policy 또는 state subject만 활성화한다. |

각 phase는 다음 executable field를 포함한다.

- `repositoryContextMode`: `answer/answer`에는 의미상 고정된 `OPTIONAL`, 모든 light-structure, feature, repository-workflow phase에는 `REQUIRED`
- `requiredDocuments`: phase에 대해 이미 읽어야 하는 최소 document
- `deferredDocuments`: 선언된 trigger가 실행될 때까지 읽지 않는 document
- `deferredDocumentTriggers`: trigger-to-document mapping
- `activityRequirements`: 각 activity에 필수인 닫힌 activity ID와 canonical trigger
- `rediscoverySubjects`: workflow rediscovery 밖에서는 비어 있고, 그 안에서는 닫힌 subject-to-trigger-to-document mapping
- `includePaths`: route와 phase의 typed default search scope
- `optInPaths`: 기록된 trigger에만 추가할 수 있는 전역적으로 deferred된 typed scope
- `rerouteTriggers`: 현재 route-phase selection을 무효화하는 조건

`workflow-rediscovery`는 universal baseline으로 `ai/context-map.json`만 요구한다. non-BLOCKED handoff는 `rediscoverySubjects`에서 routing policy, cache policy, workflow-cache state, tool policy, resource budget, project state, command registry 중 적어도 하나의 닫힌 subject를 선택한다. 각 selection은 정확히 canonical trigger와 document만 활성화한다. 선택하지 않은 subject는 document나 scope를 추가할 수 없다. 이는 이전의 9-document set을 원자적으로 로드하지 않게 한다. Answer, light structure, 일반 feature 이해, non-normative wording change는 rediscovery context를 상속하지 않는다. Answer Mode에는 deferred-document trigger가 없다. reroute condition이 실행되면 destination phase가 자신의 context를 공급한다. Light structure는 `README.md`와 `docs/00-index.md`의 direct onboarding trigger만 유지한다. requirement, behavior, contract, architecture, verification-policy change는 destination context를 로드하기 전에 reroute한다. Answer Mode는 선택된 repository document가 전혀 없을 때만 `repositoryContextRequired: false`를 사용할 수 있다. repository-dependent answer와 모든 Light Route는 exact document를 명시적으로 선택한다. 이는 intent를 추론하거나 무거운 policy document를 미리 로드하지 않고 context need를 기록한다.

## 단계 게이트가 적용된 기능 읽기

- Requirements는 소유 `spec.md` 하나로 시작한다. `specs` directory와 다른 feature spec은 필수 context가 아니다.
- Implementation은 plan 생성 또는 실행 중에만 `plan.md`를, execution 또는 verification handoff에만 `tasks.md`를, 실제 decision lookup 또는 change에만 `decisions.md`를 로드한다.
- `PLANNING`은 plan trigger가 필요하지만 task trigger는 필요하지 않다. `EXECUTION`은 plan과 task context가 필요하고 `VERIFICATION_HANDOFF`는 task gate를 유지한다.
- Feature `INDEPENDENT_AUDIT`는 implementation task record 없이 applicable verification policy가 필요하다. feature `VERIFICATION_HANDOFF`는 둘 다 필요하다.
- Feature completion은 checklist, QA gate, done-claim, Issue-closure trigger를 필수로 만든다. repository-wide completion은 QA, done-claim, Issue-closure trigger를 필수로 만든다. 늦은 로드는 gate를 약화하지 않는다. non-BLOCKED completion handoff는 effective required document를 모두 활성화하고 읽으며, `BLOCKED`는 누락된 mandatory context를 명시적으로 보존할 수 있다.

## 유예 경로와 제외 경로

`includePaths`, `optInPaths[].path`, `deferredPaths`, `excludedPaths`는 닫힌 `pathScope` object를 사용한다. 지원되는 kind는 `exact`(`{"kind":"exact","path":"AGENTS.md"}`), `subtree`(`{"kind":"subtree","path":"src/main"}`), 단순 extension suffix를 갖는 `direct-children`(`{"kind":"direct-children","path":"ai","suffix":".md"}`), `descendant-directory`(`{"kind":"descendant-directory","name":"__pycache__"}`)뿐이다. scope field는 glob string을 수락하지 않는다.

`deferredPaths`는 일반 broad search에서 제외되지만 일치하는 phase `optInPaths` trigger로 사용할 수 있다.

- subtree `ai/work-logs`: active Issue summary와 current role log에만 opt in
- subtree `ai/fixtures`: 직접 관련된 workflow fixture 또는 fixture-backed test에 opt in
- subtree `ai/schemas`: schema contract task에 opt in
- subtree `docs/superpowers`: 직접 관련된 historical design decision 확인에만 opt in

`excludedPaths`는 `.ai-runs`, `.git`, `build`, `.gradle`, `.idea`, `.worktrees`의 subtree scope와 `__pycache__`라는 descendant-directory scope를 사용한다.

excluded path는 include 또는 opt in할 수 없다. 모든 required document는 default include scope에 포함되고 default include는 phase-deferred document를 포함할 수 없다. opt-in path는 canonical deferred set에서 와야 하고 handoff는 정확한 canonical trigger가 `activatedTriggers`에 나타난 후에만 exact descendant scope를 materialize할 수 있다.

## 검증 계약

helper는 모든 exact path-bearing field와 typed scope를 검증한다. percent sign, traversal component, glob syntax, URI, drive, UNC path, backslash는 표현할 수 없다. `{feature}` placeholder는 exact `specs/{feature}/...` path에서만 유효하다. route ID는 고유해야 하고 phase ID는 각 route 내에서 고유해야 하며 route-phase pair와 허용 activity는 canonical이어야 하고 required/deferred document는 disjoint해야 하며 `deferredDocuments`는 deferred-document trigger mapping의 union과 같아야 한다. reroute-only document는 orphan deferred entry로 남지 않고 destination phase로 rerouting 후 로드한다. phase 안에서 document-trigger identity와 opt-in-trigger identity는 각각 고유하고 두 identity set은 disjoint이며 각 activity의 mandatory trigger는 canonical identity를 선택한다. rediscovery subject identity 및 trigger/document mapping은 exact하고 closed다.

unknown route 또는 phase 값은 validation error다. `repo-intake`는 더 무거운 route로 조용히 fallback하지 않는다.

## 하위 에이전트 및 인계 오버레이

delegation은 deferred reading을 대체하지 않는다. `ai/agent-handoff.json`은 route, task phase, closed `activityId`, 모든 closed `rediscoverySubjects`, owning feature, unique `activatedTriggers`, read document, 아직 deferred인 document, canonical trigger mapping, current include/deferred path, decision, open question, remaining work, remaining verification evidence, re-route trigger를 기록한다.

helper는 handoff를 이 context map과 비교한다. `activityId`는 선택한 route-phase와 호환되어야 하고 해당 activity의 mandatory trigger만 필요하다. `activatedTriggers`는 canonical document 및 opt-in trigger의 subset이어야 한다. effective required document는 base `requiredDocuments`와 activated document trigger가 매핑한 document이며 READY와 PARTIAL은 모두 읽어야 한다. 모든 read document는 `includePaths`에 포함되고 read는 deferred 상태로 남지 않으며 selected document는 읽히고 일치하는 exact scope가 있어야 하며 activated deferred document는 일치하는 exact scope를 얻는다. extra scope는 phase default, direct exact selection, selected rediscovery subject document, activated opt-in 아래에서 materialize된 exact path로 닫힌다. READY와 PARTIAL은 materialize된 모든 exact path를 읽고, BLOCKED는 그 read를 생략할 수 있지만 scope를 넓히거나 foreign scope를 사용할 수 없다. `deferredDocuments`는 activated document-trigger document를 뺀 canonical deferred set과 정확히 같다. `BLOCKED`만 mandatory activation 또는 effective required read를 생략할 수 있으며 canonical trigger array와 scope authorization은 계속 적용된다. owning feature 없는 feature work는 invalid이고 `NONE_ALLOWED`, `DIRECT_DOCUMENT` route는 `owningFeature: none`이 필요하다.

## 저장소 Surface

| Surface ID | Path | Owner |
|---|---|---|
| `product-source` | `src/main` | product feature spec |
| `product-tests` | `src/test` | product feature spec |
| `feature-specs` | `specs` | owning feature |
| `ai-workflow` | `ai`, `scripts/ai` | repo-wide AI workflow |
| `project-docs` | `docs`, `README.md` | documentation route |

## Phase 2A 경계

repository script는 Phase 3 이전에 모든 host file read, search, external tool call을 가로챌 수 없다. map은 canonical policy, schema validation, 검토 가능한 intake behavior를 제공하지만 모든 host action을 기술적으로 방지하거나 project state를 자동으로 재작성하지 않는다.
