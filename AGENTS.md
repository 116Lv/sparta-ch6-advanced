# AGENTS.md

## Role

You are an AI development agent working in this repository.

This project uses repository Markdown files as the source of truth. Do not rely on a separate Wiki or Notion document when making implementation decisions.

## First Rule

Follow `ai/document-routing.md` before changing code, docs, specs, ADRs, plans, tasks, or verification notes.

That routing step must explicitly determine the owning feature, or explicitly record that none exists. If a feature owns the work, load `specs/{feature}/spec.md` before subject-specific planning, implementation, verification, review, or normative documentation work.

Do not invent requirements. Do not claim tests passed unless you actually ran them. Do not claim completion without verification evidence.

## Mandatory Workflow State

Before rediscovering repository structure, commands, ports, environments, or verification capabilities, read:

1. `ai/project-state.json` - canonical project state
2. `ai/command-registry.json` - canonical command capability registry
3. `ai/project-state.md` and `ai/command-registry.md` - human policy and summaries
4. `ai/context-map.md`, `ai/cache-policy.md`, `ai/tool-call-policy.md`, `ai/resource-budget.md`, and `ai/workflow-cache.md` when route, cache, or rediscovery policy is relevant
5. `ai/skills/README.md`, `ai/skill-catalog.json`, `ai/agent-handoff.md`, and `ai/agent-handoff.json` when skill selection, delegated handoff, or reusable context is relevant

JSON is canonical. Markdown summaries must not override or contradict JSON.

Phase 1A provides state and registry contracts only. It does not provide a command gateway, native tool interception, or CI enforcement. Do not describe Phase 1A as complete command enforcement.

During Phase 1A work, do not execute project commands. Keep `verify.unit` as `CONFIGURED_UNVERIFIED`; keep lint, dedicated integration test, E2E, migration, seed, and API smoke as `NOT_CONFIGURED`; and keep application port 8080 as `INFERRED`.

Phase 1B-1 provides current recorded LOCAL runtime preflight and pure command resolution. A successful recorded preflight makes the LOCAL helper runtime `VERIFIED` using durable scrubbed environment-local evidence. A current-preflight mismatch blocks invocation and makes cached evidence stale for that invocation. CI remains `NOT_CONFIGURED`.

Phase 1B-2 adds the repository execution gateway and structured per-run evidence. `scripts/ai/command-runner.sh` is the only supported project-command path after Phase 1B-2. Direct project-command execution remains prohibited. `RISKY` and `DESTRUCTIVE` commands remain prohibited; approval records are audit-only and never grant execution authority. Non-POSIX project-command execution remains `NOT_CONFIGURED` and prohibited. Standalone `workflow-gate.sh` stages never launch project commands.

Phase 1B-3 adds integrity-only finalization, artifact manifests, finalized `run.json`, and done-claim checks for supported-path run evidence. Phase 1B-3 reports `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`; it does not prove verification completeness, registry `VERIFIED`, reconciliation-complete, issue-backed closure, or unqualified overall `DONE` claims.
Crash-left `FINALIZING` or receipt-bearing `FINALIZED` runs must be reconciled through `scripts/ai/done-claim-check.sh recover-finalization <run-id>` using the active retained read-only `.state/finalization-journals/<journal-id>.json`. Recovery resumes only a valid journal-bound sealed receipt; invalid or missing journal/receipt authority and any legacy fixed `.state/finalization-journal.json` marker remain `BLOCKED`, while valid inconsistent pre-publication artifacts are removed before compare-and-swapping the exact journal source back to `OPEN`. Per-attempt journals are immutable audit records and are never deleted; recovery never rolls back after `run.json` exists.

Phase 2A adds context intake and cache-control policy through `ai/context-map.md`, `ai/cache-policy.md`, `ai/tool-call-policy.md`, `ai/resource-budget.md`, `ai/workflow-cache.md`, and their canonical JSON records where present. Phase 2A repo intake is read-only/proposal-only for project-state refresh and command-discovery updates. It does not execute product commands, create repository `.ai-runs` evidence, mark registry commands `VERIFIED`, evaluate verification completeness, or claim host-wide file-read/search/tool-call interception.

Phase 2B adds skill contracts and handoff reuse through `ai/skills/README.md`, `ai/skill-catalog.json`, `ai/agent-handoff.md`, and `ai/agent-handoff.json`. Phase 2B does not execute product commands, create repository `.ai-runs` evidence, create artifact manifests or finalized `run.json`, mark registry commands `VERIFIED`, evaluate verification completeness, reconcile GitHub Issues, or support issue-backed closure, reconciliation-complete, or unqualified overall DONE claims.

Phase 2C adds verification completeness and task/change applicability policy through `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh`. Phase 2C static/helper gates map `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` by change type. Product commands remain NOT RUN; the Phase 2C gate must not create repository `.ai-runs`, artifact manifests, finalized `run.json`, registry `VERIFIED` transitions, issue-backed closure, reconciliation-complete claims, or unqualified overall DONE claims while `tracking_status` remains `pending_issue`.

Phase 3A requires the internal `native-runtime-adapter` leaf for every Phase 2C change type. The verification gate evaluates it in-process with the same task and gate correlation; external or precomputed adapter leaf results are invalid. The current Codex desktop host version is `null`/`UNPROBED` and the host is `UNSUPPORTED`, so the native leaf is `NOT_APPLICABLE` with reason `HOST_UNSUPPORTED` and any overall PASS is repository-only qualified. Supported-host matching requires an authoritative `PROBED` version. Only a fresh, challenge-bound, Ed25519-verified snapshot with signed blocking callback proof can promote trusted surfaces to `ENFORCED`; a later-gate `RESOLVED` transition also requires every current resolution event ID to match the snapshot's signed `resolutionEventIds` exactly. Unavailable crypto, an adapter fault, missing authenticated enforcement, correlation fault, unresolved bypass, or unsafe resolution binding remains completion-blocking. `scripts/ai/command-runner.sh` remains the only supported product-command path; native adapters observe or block host operations but never execute product commands. Phase 1B-3 remains `INTEGRITY_ONLY`, and Phase 3B owns CI installation, remote-runner guarantees, durable CI evidence, and cross-host parity.

AI agents must not directly run Gradle, build, product or unit project tests, application server, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands. There is no temporary direct-command exception for AI agents. Static file inspection, documentation edits, and host-approved version-control operations remain allowed administrative workflow operations.

A command run manually by a human outside the AI workflow does not make a registry entry `VERIFIED`, does not count as workflow evidence, and must not be reported by an agent as a passed check. Only Phase 1B-2 command-runner evidence may transition a project-command entry to `VERIFIED`.

Commands with `NOT_CONFIGURED`, `UNKNOWN`, `STALE`, or `UNCERTAIN` status are not executable. No command may be marked `VERIFIED` without recorded runtime evidence.

## Document Map

Start with `ai/document-routing.md` for routing, owning-feature detection, and phase-gated reading order. Then use only the owner documents selected by that route.

- `README.md`: assignment summary and high-level design rationale
- `docs/00-index.md`: documentation map and reading order
- `docs/01-product-vision.md`: product purpose, goals, non-goals
- `docs/02-users-and-permissions.md`: user types, roles, auth rules
- `docs/03-domain-model.md`: domain concepts and business rules
- `docs/04-user-flows.md`: main user flows and edge cases
- `docs/05-functional-requirements.md`: requirement list and linked specs
- `docs/06-system-architecture.md`: architecture and layer rules
- `docs/07-data-and-api-contracts.md`: DB, API, event contracts
- `docs/08-ui-and-frontend-guidelines.md`: UI guidance, if frontend is added
- `docs/09-quality-operations-and-rules.md`: test, security, release, DoD
- `ai/document-routing.md`: routing rules for which docs/spec files to load and when
- `ai/project-state.json`: canonical project facts, paths, ports, environments, and helper-runtime state
- `ai/command-registry.json`: canonical command capability and verification state
- `ai/project-state.md` and `ai/command-registry.md`: human policy notes and generated state summaries
- `ai/context-map.md`: repository context routes, surfaces, generated/excluded paths, and minimal reading routes
- `ai/cache-policy.md`: cache keys, freshness, reuse, and conservative invalidation rules
- `ai/tool-call-policy.md`: broad search, file-read, command rediscovery, and host-tool boundary policy
- `ai/resource-budget.md`: numeric discovery budgets and exception-recording rules
- `ai/workflow-cache.md`: human policy and summary for reusable scrubbed workflow-cache records
- `ai/skills/README.md`: Phase 2B skill contract index
- `ai/skill-catalog.json`: canonical Phase 2B skill catalog
- `ai/agent-handoff.md` and `ai/agent-handoff.json`: Phase 2B handoff state and reusable context packet
- `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh`: Phase 2C executable verification/applicability gates
- `ai/schemas/`: closed JSON Schema contracts for executable AI workflow state
- `ai/*`: AI workflow, delegated-work tracking, verification, QA gate, and done-claim rules
- `ai/subagent-workflow.md`: mandatory dispatch and handoff rules for delegated work
- `ai/github-issue-planning.md`: Issue boundaries, tracking/progress statuses, lifecycle, and `pending_issue` reconciliation
- `ai/github-issue-template.md`: copy-ready Issue body for delegated work
- `ai/work-log-template.md`: issue summary and role-log formats
- `ai/work-logs/README.md` and `ai/work-logs/index.md`: work-log recovery and active Issue index
- `specs/*`: feature-level execution documents
- `adr/*`: architecture decision records

## Required Reading Order

1. `README.md`
2. `docs/00-index.md`
3. `ai/document-routing.md`
4. Run the routing gate and record the owning feature outcome.
5. If the work is feature-owned, read `specs/{feature}/spec.md` first.
6. Then read only the route-selected owner docs from `docs/00~09` and relevant `ai/*` files required by `ai/document-routing.md`.
7. Read `specs/{feature}/plan.md` only for planning or implementation planning/execution.
8. Read `specs/{feature}/tasks.md` only for execution or verification handoff.
9. Read `specs/{feature}/decisions.md` only when prior feature decisions exist or new decisions are made.
10. Read `specs/{feature}/checklist.md` only before completion claims.
11. When dispatching subagents, read `ai/subagent-workflow.md` and `ai/github-issue-planning.md` before dispatching. Create one Issue per cohesive, independently closable work item and initialize its `ai/work-logs/issue-{number}/` summary and role logs. Use `tracking_status: pending_issue` only after a documented Issue-creation failure; keep workflow progress in `status`.
12. When review and evidence are ready, complete the pre-QA sections of `ai/issue-completion-checklist.md`.
13. Run `ai/qa-gate.md` and record the implementation result.
14. Create the completion report from `ai/done-claim-template.md` after QA.
15. Only after the done claim exists, complete the closure sections of `ai/issue-completion-checklist.md` and close the Issue if every closure condition passes.

## Development Flow

Follow `ai/document-routing.md` for task classification, owning-feature detection, and phase-gated reading.

1. Run the routing gate and record the owning feature outcome.
2. If the work is feature-owned, read `specs/{feature}/spec.md` before subject-specific planning, implementation, verification, review, or normative documentation work.
3. Read only the additional owner docs and `ai/*` files required by the selected route.
4. Perform only the phase-appropriate work for the task:
   - update `spec.md` for requirements or acceptance-criteria changes
   - use `plan.md` for planning / implementation planning
   - use `tasks.md` for execution / verification handoff
   - use `decisions.md` when feature decisions are involved
   - use `checklist.md` before completion claims
5. Implement, review, verify, or update documentation according to the selected route.
6. Verify according to `ai/verification-levels.md` when verification is required.
7. Update docs/specs/ADR if behavior, contracts, requirements, or architecture changed.
8. When subagents are dispatched, follow `ai/subagent-workflow.md`, create and maintain the Issue-scoped work logs, and record every role's evidence. A complete `tracking_status: pending_issue` fallback may pass implementation QA, but it must be reconciled before an issue-backed claim, unqualified overall `DONE`, reconciliation completion, or Issue closure.
9. Follow the completion sequence exactly: review/evidence ready -> pre-QA sections of `ai/issue-completion-checklist.md` -> `ai/qa-gate.md` -> `ai/done-claim-template.md` -> closure sections of `ai/issue-completion-checklist.md` and Issue closure.

## Non-Negotiable Rules

- Do not say tests passed if they were not run.
- Do not say API verification is complete without real HTTP request evidence when API behavior changed.
- Do not ignore unexpected 500 errors.
- Do not hide failures by changing requirements.
- Do not leave TODO, temporary fallback, or debug logging in production code unless explicitly documented and approved.
- Do not put business rules in controllers or UI components.
- Do not change architecture decisions without updating `adr/`.

## Details

Follow the detailed AI rules in:

- `ai/agent.rules.md`
- `ai/document-routing.md`
- `ai/implementation-guardrails.md`
- `ai/subagent-workflow.md`
- `ai/github-issue-planning.md`
- `ai/github-issue-template.md`
- `ai/work-log-template.md`
- `ai/work-logs/README.md`
- `ai/work-logs/index.md`
- `ai/verification-levels.md`
- `ai/issue-completion-checklist.md`
- `ai/qa-gate.md`
- `ai/done-claim-template.md`
- `ai/reviewer-checklist.md`
