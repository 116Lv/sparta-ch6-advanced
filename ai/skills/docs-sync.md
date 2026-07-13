# Docs Sync Skill

## Purpose

Update only route-selected canonical documents and keep summaries consistent with JSON sources of truth.

## Required Inputs

- Routing outcome
- Route-selected docs
- Canonical JSON refs when present

## Allowed Operations

- Update narrow owner docs.
- Link to canonical JSON instead of duplicating executable rules.

## Prohibited Operations

- Product commands remain NOT RUN in Phase 2B.
- Do not manually override generated summaries independently of canonical JSON.
- Do not change product requirements through workflow-only docs.

## Evidence Outputs

- Changed doc list.
- Work-log rationale and route record.

## Handoff And Reuse

Handoffs include `skill_ids`, `handoff_state_ref`, `reusable_context_refs`, `not_run_project_commands`, and changed docs.

## Phase 2B Boundary

Docs sync is limited to AI workflow skill, handoff, and reusable-context integration.
