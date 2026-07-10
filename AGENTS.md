# AGENTS.md

## Role

You are an AI development agent working in this repository.

This project uses repository Markdown files as the source of truth. Do not rely on a separate Wiki or Notion document when making implementation decisions.

## First Rule

Follow `ai/document-routing.md` before changing code, docs, specs, ADRs, plans, tasks, or verification notes.

That routing step must explicitly determine the owning feature, or explicitly record that none exists. If a feature owns the work, load `specs/{feature}/spec.md` before subject-specific planning, implementation, verification, review, or normative documentation work.

Do not invent requirements. Do not claim tests passed unless you actually ran them. Do not claim completion without verification evidence.

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
