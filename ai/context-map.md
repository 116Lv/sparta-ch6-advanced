# AI Workflow Context Map

## Human Policy Notes

`ai/context-map.json` schemaVersion 2 is the canonical source for Phase 2A route, phase, lazy-loading, and search-scope rules. JSON is canonical. Markdown is not parsed as executable state.

The governing principle is: **Read late, read narrow, escalate only when the task phase requires it.** Deferred reading never permits a required document or gate to be skipped. When the selected route or phase is unknown, incomplete, or no longer matches the task, re-route; if required context still cannot be established, report `BLOCKED` rather than guessing.

Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness, mark registry entries `VERIFIED`, or claim host-wide interception.

## Canonical Route And Phase Model

| Route | Owning feature | Canonical phases | Default behavior |
|---|---|---|---|
| `answer` | none | `answer` | Read only directly relevant material. No workflow-policy preload. |
| `light-structure` | none (direct-document route) | `light-structure` | Use narrow files or search results; load onboarding indexes only when broad mapping is actually needed. |
| `feature-work` | required | `feature-requirements`, `implementation`, `verification`, `completion` | Start with `specs/{feature}/spec.md`; delay plan, tasks, decisions, checklist, verification, and completion documents until their triggers. |
| `repo-wide-ai-workflow` | none allowed | `implementation`, `verification`, `completion`, `workflow-rediscovery` | Load only phase owner documents. Rediscovery starts with the context map and activates only the selected policy or state subject. |

Each phase contains these executable fields:

- `repositoryContextMode`: semantically fixed to `OPTIONAL` for `answer/answer` and `REQUIRED` for every light-structure, feature, and repository-workflow phase;
- `requiredDocuments`: minimum documents that must already be read for the phase;
- `deferredDocuments`: documents that remain unread until a declared trigger fires;
- `deferredDocumentTriggers`: the trigger-to-document mapping;
- `activityRequirements`: closed activity IDs and the canonical triggers mandatory for each activity;
- `rediscoverySubjects`: empty outside workflow rediscovery; there it is the closed subject-to-trigger-to-document mapping;
- `includePaths`: typed default search scopes for the route and phase;
- `optInPaths`: globally deferred typed scopes that may be added only for the recorded trigger; and
- `rerouteTriggers`: conditions that invalidate the current route-phase selection.

`workflow-rediscovery` requires only `ai/context-map.json` as its universal baseline. A non-BLOCKED handoff selects at least one closed subject in `rediscoverySubjects`: routing policy, cache policy, workflow-cache state, tool policy, resource budget, project state, or command registry. Each selection activates exactly its canonical trigger and exact documents; unselected subjects cannot add documents or scopes. This avoids loading the former nine-document set atomically. Answer, light structure, normal feature understanding, and non-normative wording changes do not inherit rediscovery context. Answer Mode has no deferred-document trigger; when its reroute condition fires, the destination phase supplies its own context. Light structure retains only the direct onboarding trigger for `README.md` and `docs/00-index.md`; requirement, behavior, contract, architecture, and verification-policy changes reroute before loading destination context. Answer Mode may use `repositoryContextRequired: false` only with no selected repository documents. Repository-dependent answers and every Light Route select exact documents explicitly; this records context need without inferring intent or preloading heavy policy documents.

## Phase-Gated Feature Reading

- Requirements starts with only the owning `spec.md`; the `specs` directory and other feature specs are not required context.
- Implementation loads `plan.md` only while creating or executing a plan, `tasks.md` only for execution or verification handoff, and `decisions.md` only for a real decision lookup or change.
- `PLANNING` requires the plan trigger but not the task trigger. `EXECUTION` requires plan and task context, while `VERIFICATION_HANDOFF` preserves the task gate.
- Feature `INDEPENDENT_AUDIT` requires the applicable verification policy without requiring the implementation task record; feature `VERIFICATION_HANDOFF` requires both.
- Feature completion makes its checklist, QA gate, done-claim, and Issue-closure triggers mandatory. Repository-wide completion makes its QA, done-claim, and Issue-closure triggers mandatory. Late loading does not weaken any gate: a non-BLOCKED completion handoff activates and reads every effective required document, while `BLOCKED` may preserve missing mandatory context explicitly.

## Deferred Paths Versus Excluded Paths

`includePaths`, `optInPaths[].path`, `deferredPaths`, and `excludedPaths` use a closed `pathScope` object. The only supported kinds are `exact` (`{"kind":"exact","path":"AGENTS.md"}`), `subtree` (`{"kind":"subtree","path":"src/main"}`), `direct-children` with a simple extension suffix (`{"kind":"direct-children","path":"ai","suffix":".md"}`), and `descendant-directory` (`{"kind":"descendant-directory","name":"__pycache__"}`). Scope fields do not accept glob strings.

`deferredPaths` are omitted from ordinary broad searches but remain available through a matching phase `optInPaths` trigger:

- subtree `ai/work-logs`: opt in only to the active Issue summary and current role logs;
- subtree `ai/fixtures`: opt in for directly related workflow fixtures or fixture-backed tests;
- subtree `ai/schemas`: opt in for a schema contract task; and
- subtree `docs/superpowers`: opt in only to confirm a directly relevant historical design decision.

`excludedPaths` use subtree scopes for `.ai-runs`, `.git`, `build`, `.gradle`, `.idea`, and `.worktrees`, plus the descendant-directory scope named `__pycache__`.

An excluded path cannot be included or opted in. Every required document is covered by a default include scope, while no default include may cover a phase-deferred document. Opt-in paths must come from the canonical deferred set, and a handoff may materialize only exact descendant scopes after the exact canonical trigger appears in `activatedTriggers`.

## Validation Contract

The helper validates every exact path-bearing field and typed scope. Percent signs, traversal components, glob syntax, URIs, drives, UNC paths, and backslashes cannot be represented. The `{feature}` placeholder is valid only in an exact `specs/{feature}/...` path. Route IDs must be unique, phase IDs must be unique within each route, route-phase pairs and allowed activities must be canonical, required and deferred documents must be disjoint, and `deferredDocuments` must equal the union of deferred-document trigger mappings. Reroute-only documents are loaded after rerouting into the destination phase rather than left as orphan deferred entries. Within a phase, document-trigger identities are unique, opt-in-trigger identities are unique, and the two identity sets are disjoint; each activity's mandatory triggers select canonical identities. Rediscovery subject identities and their trigger/document mappings are exact and closed.

Unknown route or phase values are validation errors. `repo-intake` does not silently fall back to a heavier route.

## Subagent And Handoff Overlay

Delegation does not replace deferred reading. `ai/agent-handoff.json` records the route, task phase, closed `activityId`, any closed `rediscoverySubjects`, owning feature, unique `activatedTriggers`, read documents, documents still deferred, canonical trigger mappings, current include/deferred paths, decisions, open questions, remaining work, remaining verification evidence, and re-route triggers.

The helper compares a handoff with this context map. `activityId` must be compatible with the selected route-phase, and only that activity's mandatory triggers are required. `activatedTriggers` must be a subset of canonical document and opt-in triggers. Effective required documents are base `requiredDocuments` plus documents mapped by activated document triggers; READY and PARTIAL must have read all of them. Every read document is covered by `includePaths`, no read remains deferred, selected documents are read and have matching exact scopes, and activated deferred documents gain matching exact scopes. Extra scopes are closed to phase defaults, direct exact selections, selected rediscovery subject documents, and exact paths materialized beneath activated opt-ins. READY and PARTIAL read every materialized exact path; BLOCKED may omit that read but cannot widen or use a foreign scope. `deferredDocuments` is exactly the canonical deferred set minus activated document-trigger documents. Only `BLOCKED` may omit mandatory activation or effective required reads; canonical trigger arrays and scope authorization still apply. Feature work without an owning feature is invalid; `NONE_ALLOWED` and `DIRECT_DOCUMENT` routes require `owningFeature: none`.

## Repository Surfaces

| Surface ID | Paths | Owner |
|---|---|---|
| `product-source` | `src/main` | product feature specs |
| `product-tests` | `src/test` | product feature specs |
| `feature-specs` | `specs` | owning feature |
| `ai-workflow` | `ai`, `scripts/ai` | repo-wide AI workflow |
| `project-docs` | `docs`, `README.md` | documentation routes |

## Phase 2A Boundary

repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. The map provides canonical policy, schema validation, and reviewable intake behavior; it does not technically prevent every host action or rewrite project state automatically.
