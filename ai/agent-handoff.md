# AI Workflow Agent Handoff

## Human Policy Notes

`ai/agent-handoff.json` schemaVersion 2 is the canonical Phase 2B handoff packet. JSON is canonical. Markdown is not parsed as executable state. Product commands remain NOT RUN in Phase 2B.

## Required Context State

Every reusable or delegated handoff records:

- `routeId`, `taskPhase`, closed `activityId`, `owningFeature`, and `contextStatus`;
- closed `rediscoverySubjects`, empty outside workflow rediscovery;
- `repositoryContextRequired` plus unique exact `selectedDocuments`;
- unique `activatedTriggers`, `readDocuments`, documents still in `deferredDocuments`, and canonical `deferredDocumentTriggers`;
- current `includePaths` and canonical `deferredPaths`;
- `decisions`, `openQuestions`, and `remainingWork`;
- `remainingVerificationEvidence` and `rerouteTriggers`;
- `activeIssue: null` when no Issue-backed work-log context is selected, otherwise the active Issue summary plus only the current role logs; and
- skill, reusable-context, command-boundary, and later-phase records.

The snake-case work-log equivalents remain `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and `github_reconciliation_status`.

## Validation And Blocking

The helper selects the exact route-phase pair and validates that `activityId` is compatible. Activations must be canonical for that activity and pair. Effective required context combines base required documents with documents mapped by activated document triggers. If any are unread, or an activity-mandatory trigger is inactive, a handoff cannot be READY or PARTIAL; it must be `BLOCKED` or fail validation. Planning requires plan context without prematurely requiring tasks; execution and verification handoff retain their task gates; independent audit requires verification policy without impersonating an implementation handoff. Completion retains every completion gate. `feature-work` cannot dispatch with `owningFeature: none`.

Workflow rediscovery starts with only `ai/context-map.json`. READY and PARTIAL select at least one canonical subject, activate that subject's exact trigger, and read/include its exact mapped documents. Unknown or non-rediscovery subjects, unselected subject triggers, and extra subject documents or scopes are invalid.

The handoff preserves the full canonical trigger mapping with exactly one mapping per document-trigger identity; duplicate mappings are invalid rather than collapsed. `deferredDocuments` contains only documents still deferred after activated document triggers are removed and cannot overlap `readDocuments`. Every read is covered by an include scope. Selected documents are read and use matching exact scopes; activated deferred documents also use matching exact scopes. Additional scopes are limited to phase defaults, direct exact selections, and exact paths materialized beneath activated opt-ins. READY and PARTIAL read those materialized opt-in paths; BLOCKED may omit that read but cannot widen or use a foreign scope. These identity and scope checks also apply to BLOCKED handoffs. Changing phase or route requires re-routing and a new context check.

Answer Mode may set `repositoryContextRequired: false` with empty `selectedDocuments` for a genuinely repository-independent response. If it sets the flag true, it selects at least one exact document. Light Route always sets the flag true and selects at least one exact document. Feature and repository-workflow phases also set the flag true, but may leave `selectedDocuments` empty when canonical required documents already provide context.

## Narrow Active-Issue Scope

The `{"kind":"subtree","path":"ai/work-logs"}` scope is globally deferred. Answer, light-structure, feature-requirements, and any other handoff with no activated Issue/work-log scope use `activeIssue: null`. Activating a work-log opt-in, or carrying a work-log include/reusable ref, requires an `activeIssue` object and its canonical trigger. Its number, exact `https://github.com/116Lv/sparta-ch6-advanced/issues/{number}` URL, summary, and distinct role refs must agree exactly. The active URL permits no trailing slash, query, fragment, credentials, alternate host, port, or scheme. `includePaths` may then contain only exact scopes from that active ref set, and READY or PARTIAL reads every selected active ref; foreign, unlisted, subtree, direct-children, and descendant scopes are invalid even for `BLOCKED`. `reusableContextRefs` are repository-safe exact paths, cannot enter excluded scope, and may reference work logs only from the same active set. Historical `githubIssue` and `phase3AIssue` records remain separate provenance and need not equal the current active identity. Prior role logs are recovery hints, not canonical authority; confirm decisions in the owning spec, policy, schema, or ADR.

## Reuse Contract

Reuse the current handoff and its exact canonical references before rediscovering context. Do not load every historical cache entry, work log, skill document, or workflow policy. Cache or context exceptions must record the route, phase, trigger, and stale or missing input that required escalation.

`skillIds` must equal the catalog's complete distinct ID set exactly once. Schema uniqueness and helper semantic validation both enforce this set.

`notRunProjectCommands` is likewise a closed ordered boundary, not a free-form note: `Gradle`, `build`, `product/unit project tests`, `application server`, `Docker Compose`, `HTTP/curl/API`, `database`, `migration`, `seed`, and `infrastructure commands`. The schema and helper both reject omissions, additions, duplicates, replacements, and reordering.

## Verification And Completion Boundaries

Subagent work crossing into another phase must re-route. A subagent completion report does not replace Phase 2C verification, the QA gate, completion evidence, a done claim, or Issue closure checks. Missing verification or completion evidence remains `BLOCKED` or `PARTIAL`.

Phase 2B does not create repository `.ai-runs`, artifact manifests, finalized `run.json`, registry `VERIFIED` transitions, verification-completeness claims, issue-backed closure claims, reconciliation-complete claims, or unqualified overall DONE claims.

## Phase 3A Native Adapter Handoff

The current canonical packet is a repository-wide `INDEPENDENT_AUDIT` packet for active Issue #10. Its activated schema and active-Issue triggers opt in only to the directly required schema, that Issue summary, and the implementation/review role logs. The current host is `UNSUPPORTED`; any overall PASS remains repository-only qualified. The verification gate accepts no precomputed native result, and `scripts/ai/command-runner.sh` remains the only supported product-command path. Phase 3B owns durable CI evidence, remote-runner guarantees, and cross-host parity.
