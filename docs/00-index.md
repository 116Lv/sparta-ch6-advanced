# 00. Project Knowledge Index

## Purpose

This `docs/` directory is the project Wiki replacement and source of truth, but task routing and required reading order are defined by `ai/document-routing.md`.

The project should be understandable from repository Markdown files alone. External Wiki or Notion pages are not considered canonical unless their content is copied into this repository.

## Reading Order

### First-Time Project Understanding

1. `README.md`
2. `docs/01-product-vision.md`
3. `docs/03-domain-model.md`
4. `docs/05-functional-requirements.md`
5. `docs/06-system-architecture.md`
6. `docs/07-data-and-api-contracts.md`
7. `docs/09-quality-operations-and-rules.md`

### Feature Development

1. `AGENTS.md`
2. `ai/document-routing.md`
3. Run the routing gate and record the owning feature outcome.
4. If the work is feature-owned, read `specs/{feature}/spec.md` first.
5. When dispatching subagents, read `ai/subagent-workflow.md` and `ai/github-issue-planning.md`, create one GitHub Issue per cohesive, independently closable work item, and initialize `ai/work-logs/issue-{number}/README.md` plus role-specific logs. Use `tracking_status: pending_issue` only after a documented creation failure; keep workflow progress in `status`.
6. Then read only the relevant `docs/00~09`, `ai/*`, and phase-gated `specs/{feature}/*` files required by `ai/document-routing.md`.
7. `ai/verification-levels.md` when verification is required.
8. Complete the pre-QA sections of `ai/issue-completion-checklist.md` after review and evidence are ready.
9. Run `ai/qa-gate.md`.
10. Create the completion report from `ai/done-claim-template.md`.
11. Complete the closure sections of `ai/issue-completion-checklist.md`, then close the Issue only if every closure condition passes.

### Delegated Work Recovery

For interrupted or resumed delegated work, start with `ai/work-logs/index.md`, then the relevant `ai/work-logs/issue-{number}/README.md`, then the latest role-specific agent log. For a temporary GitHub outage, use the documented `ai/work-logs/no-issue/` fallback. Reconciliation must move the full fallback directory to `issue-{number}/` and preserve the prior path in migration history before the eventual Issue can close.

## Document Map

| Document | Purpose |
|---|---|
| `01-product-vision.md` | Product purpose, users, goals, non-goals, success criteria |
| `02-users-and-permissions.md` | User types, roles, permission matrix, auth rules |
| `03-domain-model.md` | Core domain concepts, entities, relationships, business rules |
| `04-user-flows.md` | Main user flows, edge cases, success/failure states |
| `05-functional-requirements.md` | Requirement IDs, priorities, linked specs |
| `06-system-architecture.md` | Tech stack, layers, dependency direction, forbidden patterns |
| `07-data-and-api-contracts.md` | DB principles, API contracts, error format, events |
| `08-ui-and-frontend-guidelines.md` | UI rules, forms, tables, loading/error/empty states |
| `09-quality-operations-and-rules.md` | Testing, security, logging, release, migration, DoD |

## AI Workflow And Delegated Work

| Document | Purpose |
|---|---|
| `ai/document-routing.md` | First ownership and reading-order gate for every task |
| `ai/subagent-workflow.md` | Dispatch, handoff, agent-role, and orchestrator rules |
| `ai/github-issue-planning.md` | GitHub Issue boundaries, tracking/progress statuses, lifecycle, and reconciliation |
| `ai/github-issue-template.md` | Required GitHub Issue body for delegated work |
| `ai/work-log-template.md` | Issue summary and role-specific work-log formats |
| `ai/work-logs/README.md` | Work-log storage and recovery rules |
| `ai/work-logs/index.md` | Index of issue-scoped and pending reconciliation work |
| `ai/issue-completion-checklist.md` | Pre-QA readiness and post-claim GitHub Issue-closure checks |
| `ai/qa-gate.md` | Final verification and delegated-work evidence gate |
| `ai/done-claim-template.md` | Evidence-based completion report format |

## Source of Truth Rules

- Product goals live in `docs/01-product-vision.md`.
- Permission rules live in `docs/02-users-and-permissions.md`.
- Domain and business rules live in `docs/03-domain-model.md`.
- API and DB contracts live in `docs/07-data-and-api-contracts.md`.
- Testing and operations rules live in `docs/09-quality-operations-and-rules.md`.
- Document routing rules live in `ai/document-routing.md`.
- AI workflow rules live in `ai/*`.
- Delegated work uses GitHub Issues for external task tracking and `ai/work-logs/issue-{number}/` for durable execution evidence. `tracking_status` records Issue availability; `status` records workflow progress. A complete pending fallback may pass implementation QA but must be reconciled before an issue-backed claim, unqualified overall `DONE`, reconciliation completion, or Issue closure.
- Feature-specific execution details live in `specs/*`.
- Project-wide architecture decisions live in `adr/*`.

Do not duplicate the same rule across many files. Link to the owner document instead.

## How to Update Docs

Update docs when:

- a business rule changes
- an API request/response changes
- a DB table or event contract changes
- an architecture decision changes
- testing or completion criteria change
- auth / permission / identity / `userId` semantics change
- a feature spec is added or completed

When a project-wide technical decision changes, add or update an ADR.

## Open Questions

- TODO: Confirm exact Gradle task names after Spring Boot scaffolding exists.
- TODO: Confirm whether this repository will include frontend UI or backend API only.
