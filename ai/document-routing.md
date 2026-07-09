# Document Routing

## Purpose

Use this guide to choose the minimum owner documents and feature-spec files before planning, implementation, verification, review, or completion claims.

This is not a read-everything rule. Read the owner docs for the change, the owning feature-spec files required for the current phase, and linked ADRs or AI rules only when the route calls for them.

## Mandatory Routing Gate

Run this gate before subject-specific planning, implementation, verification, review, or normative documentation work.

1. Determine the owning feature for the task.
2. Record one of these outcomes explicitly:
   - `Owning feature: specs/{feature}`
   - `Owning feature: none`
3. If an owning feature exists, load `specs/{feature}/spec.md` before doing any subject-specific planning, implementation, verification, review, or normative documentation work.
4. If no owning feature exists, continue in a repo-wide lane and state why no feature owns the work.

This gate is mandatory even when the task looks documentation-only, verification-only, or small.

## Ownership Outcomes

### Feature-Owned Work

Use the feature-owned lane when the task changes, explains, verifies, or constrains behavior that belongs to one feature. Load `specs/{feature}/spec.md` first, then continue into the relevant subject documents, plan, tasks, verification, or documentation updates.

Examples:

- Document payment failure rules for order payment.
- Verify API behavior for point charge.
- Update acceptance criteria for popular menu ranking.

### No Owning Feature

Use `Owning feature: none` only when the work is genuinely repo-wide or not feature-owned.

Common valid cases:

- Repo-wide policy or workflow guidance.
- ADR-only architecture decision work.
- Truly non-feature maintenance such as formatting rules, repository structure, or global contributor guidance.

Do not invent or force a feature branch for this category.

## Feature-Spec Loading Timing

For the owning `specs/{feature}/` directory:

- Read `spec.md` before planning or drafting requirements.
- Read `plan.md` before implementation planning or execution.
- Read `tasks.md` before execution or verification handoff.
- Read `decisions.md` when prior feature decisions exist or when new decisions are made.
- Read `checklist.md` before any completion claim.

## Owner Routes

| Trigger | Must read / update | Notes |
|---|---|---|
| Product scope, goals, non-goals | `docs/01-product-vision.md`, `docs/05-functional-requirements.md`, owning `spec.md` | Use when requirements or acceptance criteria change. |
| Auth, permission, role, user identity, principal, account ownership, `userId` semantics | `docs/02-users-and-permissions.md`, owning `spec.md` | Mandatory whenever auth or identity meaning changes. If request `userId` is interpreted, verified, trusted, or replaced, this route applies. |
| Domain rules, entities, invariants | `docs/03-domain-model.md`, `docs/04-user-flows.md`, owning `spec.md` | Add `docs/05-functional-requirements.md` if requirements changed. |
| Architecture, layers, module boundaries, major technical decisions | `docs/06-system-architecture.md`, `decisions.md`, relevant ADR | Add or update ADR when the decision is project-wide. |
| DB schema, API request/response, error contract, events | `docs/07-data-and-api-contracts.md`, owning `spec.md` | Add `docs/02-users-and-permissions.md` too if identity or authorization semantics change. |
| UI behavior, screens, client-side flows | `docs/08-ui-and-frontend-guidelines.md`, `docs/04-user-flows.md`, owning `spec.md` | UI-only permission checks are not enough; include auth route when needed. |
| Testing rules, verification, security checks, release rules, completion criteria | `docs/09-quality-operations-and-rules.md`, `checklist.md`, relevant `ai/*` file | Use for QA gate, done-claim, verification-level, or DoD changes. |
| Documentation-only wording, index, status, report text | Only the directly affected doc | This route is only for non-normative edits. If the doc changes requirements, behavior, contracts, architecture, auth, verification, or completion criteria, route by that subject instead. |

## Documentation-Only Lane

A documentation-only task is still routed by ownership first.

### If A Feature Owns The Document Change

1. Record `Owning feature: specs/{feature}`.
2. Load `specs/{feature}/spec.md` first.
3. Then read only the additional owner documents needed for the requested doc change.
4. Update the narrowest canonical document instead of broad project docs when possible.

Examples:

- "Clarify retry behavior for point charge" -> load `specs/002-point-charge/spec.md`, then the relevant contract or quality doc.
- "Document menu query cache invalidation rule" -> load `specs/001-menu-query/spec.md`, then the architecture or contract doc it affects.

### If No Feature Owns The Document Change

Record `Owning feature: none`, then continue in the repo-wide lane.

Examples:

- Add a new ADR.
- Tighten repository-wide AI workflow guidance.
- Fix the project documentation index.

## Subagent Workflow Summary

- Main Dev Agent: choose the route, identify the owning feature/spec, and do the final consistency check.
- Specification Agent: update `spec.md` and clarify requirements.
- Implementation Agent: execute from `plan.md`.
- Test / API Verification Agent: verify from `tasks.md` and repo verification rules.
- Documentation Agent: update owner docs, `decisions.md`, ADRs, and cross-links.
- Review Agent: confirm the right route was followed and block unsupported completion claims.

Every handoff should carry:

- Owning feature/spec.
- Files already read.
- Decisions already made.
- Open questions.
- Evidence still required.

## Re-Routing Rule

Stop and re-route before continuing if the task grows from one type into another.

Examples:

- A domain logic task becomes an API contract task.
- A code task also changes acceptance criteria.
- A doc-only wording task becomes an architecture decision change.

Do not continue on the old reading route once the task scope changes.

