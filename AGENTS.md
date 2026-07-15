# AGENTS.md

## Role

You are an AI development agent working in this repository.

Repository Markdown files are the source of truth. Do not invent requirements or substitute a separate Wiki or Notion page for repository policy.

## Core Reading Principle

> Read late, read narrow, escalate only when the task phase requires it.

Start with the smallest route that can safely answer or perform the task. Do not preload onboarding, planning, execution, verification, or completion documents before their phase begins.

## First Rule

Use `ai/document-routing.md` to classify the task before changing code, normative documentation, specs, ADRs, plans, tasks, or verification notes.

The routing result selects one of these lanes:

- **Answer Mode**: a small question or explanation with no repository change. Read only directly referenced or directly relevant material.
- **Light Route**: structure discovery, focused explanation, or non-normative documentation maintenance. Read only the narrow files needed for that purpose.
- **Work Route**: planning, implementation, normative documentation, review, verification, or completion work. Determine the owning feature first, or explicitly record `Owning feature: none` for genuinely repo-wide work.

If Work Route is feature-owned, read `specs/{feature}/spec.md` before subject-specific planning, implementation, verification, review, or normative documentation changes.

## Phase-Gated Reading

After the route and owning feature are known, load documents only when the current phase requires them:

| Phase | Read when needed |
|---|---|
| Answer / explanation | Only the directly relevant file or section. No default project-wide reading list. |
| Light structure discovery | Relevant directories/files; use `README.md` or `docs/00-index.md` only for first-time onboarding or broad project mapping. |
| Requirements / feature work | Owning `specs/{feature}/spec.md`, then only the subject owner docs selected by `ai/document-routing.md`. |
| Planning / implementation | `plan.md` when creating or executing an implementation plan. |
| Execution / verification handoff | `tasks.md` when executing work or handing it to verification. |
| Decision work | `decisions.md` only to confirm an existing feature decision or record a new one; use a relevant ADR for project-wide decisions. |
| Verification | Relevant verification policy and evidence documents only when verification is being designed, run, reviewed, or reported. |
| Completion claim | `checklist.md`, `ai/qa-gate.md`, `ai/done-claim-template.md`, and applicable sections of `ai/issue-completion-checklist.md` immediately before or during the completion sequence. |

`plan.md`, `tasks.md`, `decisions.md`, and `checklist.md` are not a bundle. Reading `spec.md` does not automatically require reading the other four files.

## Conditional Repository State Reading

Do not read canonical state files on every task. Read them when the task must rediscover or verify repository structure, commands, ports, environments, helper-runtime state, or verification capability:

1. `ai/project-state.json` for canonical project and environment facts.
2. `ai/command-registry.json` for canonical command capability and verification state.
3. Their Markdown summaries only when human policy or explanation is needed.
4. Context/cache/tool-budget documents only when route, cache, rediscovery, or resource policy is relevant.
5. Skill catalog and handoff documents only when selecting skills, delegating work, or reusing a handoff.

JSON is canonical. Markdown summaries must not override or contradict JSON.

## Command And Evidence Safety

- AI agents must not directly run Gradle, build, product or unit tests, application servers, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands.
- `scripts/ai/command-runner.sh` is the only supported project-command path after Phase 1B-2.
- Direct project-command execution remains prohibited. There is no temporary direct-command exception.
- `RISKY` and `DESTRUCTIVE` commands remain prohibited; approval records are audit-only and never grant execution authority.
- Non-POSIX project-command execution remains `NOT_CONFIGURED` and prohibited.
- Standalone `workflow-gate.sh` stages never launch project commands.
- Commands with `NOT_CONFIGURED`, `UNKNOWN`, `STALE`, or `UNCERTAIN` status are not executable. No command becomes `VERIFIED` without recorded runtime evidence.
- A command run manually by a human outside the AI workflow is not workflow evidence and must not be reported as a passed check.
- Static inspection, documentation edits, and host-approved version-control operations remain allowed administrative operations.

Phase 1B-3 adds integrity-only finalization, artifact manifests, finalized `run.json`, and done-claim checks for supported-path run evidence. Phase 1B-3 reports `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`; it does not prove verification completeness, registry `VERIFIED`, reconciliation-complete, issue-backed closure, or unqualified overall `DONE` claims.

Crash-left `FINALIZING` or receipt-bearing `FINALIZED` runs must be reconciled through `scripts/ai/done-claim-check.sh recover-finalization <run-id>` using the active retained read-only `.state/finalization-journals/<journal-id>.json`. Recovery resumes only a valid journal-bound sealed receipt; invalid or missing journal/receipt authority and any legacy fixed `.state/finalization-journal.json` marker remain `BLOCKED`. Recovery never rolls back after `run.json` exists.

Do not overstate later workflow phases. Phase 2A/2B do not execute product commands or prove completion; Phase 2C static/helper gates keep product commands `NOT RUN`; Phase 3A unsupported-host results are repository-only qualified; Phase 3B owns CI and remote-runner guarantees. Read the phase owner documents only when work touches those guarantees.

## Minimal Document Map

- `README.md`: assignment overview and high-level rationale; onboarding or broad overview, not mandatory per task.
- `docs/00-index.md`: documentation map; first-time or broad navigation, not mandatory per task.
- `ai/document-routing.md`: task lanes, ownership, subject routes, and phase-gated reading.
- `docs/01`-`09`: product, permission, domain, flow, requirement, architecture, contract, UI, and quality owner documents selected by route.
- `specs/{feature}/`: feature requirements plus phase-specific plan, tasks, decisions, and checklist files.
- `adr/`: project-wide architecture decisions.
- `ai/project-state.json` and `ai/command-registry.json`: canonical rediscovery inputs, read only when relevant.
- `ai/*`: workflow and verification policy, loaded only by the route and task phase.

## Development Flow

1. Classify the task as Answer Mode, Light Route, or Work Route.
2. For Work Route, record the owning feature outcome. If feature-owned, read its `spec.md` first.
3. Read only the subject owner documents needed for the current change.
4. Escalate to phase-specific feature files only when entering their phase:
   - `plan.md`: implementation planning or plan execution
   - `tasks.md`: execution or verification handoff
   - `decisions.md`: existing or new decision work
   - `checklist.md`: immediately before a completion claim
5. Implement, document, review, or verify within the selected route.
6. If behavior, contracts, requirements, or architecture changed, update their owner docs or ADRs.
7. Before a completion claim, load and follow the applicable verification and completion documents. Late loading changes timing, not rigor.

## Delegation And Issue Workflow

Only when dispatching subagents, read `ai/subagent-workflow.md` and `ai/github-issue-planning.md`, then create and maintain the required Issue-scoped work logs. Do not preload delegation documents for single-agent work.

Only when review and evidence are ready:

1. Complete the applicable pre-QA sections of `ai/issue-completion-checklist.md`.
2. Run the `ai/qa-gate.md` process and record the result.
3. Create the completion report from `ai/done-claim-template.md`.
4. Complete applicable closure sections and close an Issue only when every closure condition passes.

`ai/lazycodex-runbook.md` is a verification-avoidance prevention runbook. It is not a token-saving or optional-verification feature; load it when unsupported completion behavior must be corrected or reviewed.

## Non-Negotiable Rules

- Do not say tests passed if they were not run through a supported path.
- Do not claim API verification without real request/response evidence when API behavior changed.
- Do not ignore unexpected 500 errors or hide failures by changing requirements.
- Do not claim completion without verification evidence.
- Do not leave TODOs, temporary fallbacks, or debug logging in production code unless explicitly documented and approved.
- Do not put business rules in controllers or UI components.
- Do not change project-wide architecture decisions without updating `adr/`.
- Re-route before continuing when task scope changes.

## Conditional Detail References

Load these only when their subject or phase applies: `ai/agent.rules.md`, `ai/implementation-guardrails.md`, `ai/verification-levels.md`, `ai/reviewer-checklist.md`, `ai/subagent-workflow.md`, `ai/github-issue-planning.md`, `ai/issue-completion-checklist.md`, `ai/qa-gate.md`, and `ai/done-claim-template.md`.
