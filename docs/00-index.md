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
5. Then read only the relevant `docs/00~09`, `ai/*`, and phase-gated `specs/{feature}/*` files required by `ai/document-routing.md`.
6. `ai/verification-levels.md` when verification is required.
7. `ai/qa-gate.md` before completion claims.
8. `ai/done-claim-template.md` before reporting completion.

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

## Source of Truth Rules

- Product goals live in `docs/01-product-vision.md`.
- Permission rules live in `docs/02-users-and-permissions.md`.
- Domain and business rules live in `docs/03-domain-model.md`.
- API and DB contracts live in `docs/07-data-and-api-contracts.md`.
- Testing and operations rules live in `docs/09-quality-operations-and-rules.md`.
- Document routing rules live in `ai/document-routing.md`.
- AI workflow rules live in `ai/*`.
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
