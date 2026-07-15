# Document Routing

## Purpose

Choose the minimum owner documents and feature files required by the current task phase.

> Read late, read narrow, escalate only when the task phase requires it.

This rule reduces reading scope and timing; it does not reduce verification, evidence, or completion standards.

## Step 1: Choose The Smallest Safe Route

### Answer Mode

Use Answer Mode for a small question or explanation that makes no repository change, establishes no new requirement or decision, performs no verification, and makes no completion claim.

- Read only a file or section directly referenced by the question or strictly required to answer it.
- Do not load `README.md`, `docs/00-index.md`, every feature spec, workflow state, or completion documents by default.
- Owning-feature recording is not required unless the answer turns into normative feature work, review, or verification.

### Light Route

Use Light Route for focused structure discovery, first-pass orientation, or non-normative wording/index maintenance.

- Inspect only the relevant directory, file, or narrow search result.
- Use `README.md` and `docs/00-index.md` for first-time onboarding or broad project mapping, not as per-task prerequisites.
- For non-normative wording, read only the directly affected document.
- Re-route to Work Route if the task starts changing requirements, behavior, contracts, architecture, authentication, verification policy, or completion criteria.

### Work Route

Use Work Route for implementation, implementation planning, normative documentation, feature decisions, review, verification, or completion work.

Before subject-specific work:

1. Determine the owning feature.
2. Record `Owning feature: specs/{feature}` or `Owning feature: none`.
3. If feature-owned, read `specs/{feature}/spec.md` first.
4. Read only the subject owner documents selected below.

Use `Owning feature: none` only for genuinely repo-wide policy, ADR-only architecture work, or non-feature maintenance. Do not force a feature owner for global contributor guidance.

## Step 2: Escalate By Task Phase

For an owning `specs/{feature}/` directory, load each file independently:

| File | Earliest required phase |
|---|---|
| `spec.md` | Before feature requirements, planning, implementation, normative documentation, review, or verification. |
| `plan.md` | When creating an implementation plan or entering plan execution. |
| `tasks.md` | When executing tracked work or preparing/receiving a verification handoff. |
| `decisions.md` | When an existing decision must be confirmed or a new feature decision is required. |
| `checklist.md` | Immediately before evaluating or making a completion claim. |

Do not read all five at route entry. A later file may link backward to earlier context, but an earlier phase does not preload later files.

## Step 3: Select Subject Owners

| Trigger | Minimum owner documents | Add only when applicable |
|---|---|---|
| Product scope, goals, non-goals | `docs/01-product-vision.md`, `docs/05-functional-requirements.md`, owning `spec.md` | Acceptance-criteria owners linked by the spec. |
| Auth, permission, identity, principal, account ownership, `userId` semantics | `docs/02-users-and-permissions.md`, owning `spec.md` | Contract doc when request or response semantics change. |
| Domain rules, entities, invariants | `docs/03-domain-model.md`, owning `spec.md` | `docs/04-user-flows.md` for flow effects; requirements doc only when requirements change. |
| Architecture, layers, module boundaries | `docs/06-system-architecture.md` | Existing `decisions.md` or relevant ADR only when a decision is involved. |
| DB schema, API request/response, errors, events | `docs/07-data-and-api-contracts.md`, owning `spec.md` | Permission doc when identity/auth semantics are involved. |
| UI behavior or client flow | `docs/08-ui-and-frontend-guidelines.md`, owning `spec.md` | User-flow and permission owners when applicable. |
| Testing, security, release, verification rules | `docs/09-quality-operations-and-rules.md` plus the directly relevant verification policy | `checklist.md` and completion documents only at completion evaluation. |
| AI context, cache, tool limits, resource budgets, repo intake | Only the directly relevant file among `ai/context-map.md`, `ai/cache-policy.md`, `ai/tool-call-policy.md`, `ai/resource-budget.md`, `ai/workflow-cache.md` | Canonical JSON only when facts must be rediscovered or validated. |
| Skill selection, delegation, reusable handoff | The applicable skill or handoff owner | Catalog/cache/work-log documents only when needed for selection or reuse. |
| Verification completeness, gate behavior, native adapter state | The directly relevant verification policy or executable gate source | QA/work-log/completion documents only when the verification or completion phase requires them. |
| Non-normative wording, index, report text | Only the directly affected document | Re-route by subject if semantics change. |

## Conditional Canonical State

Read `ai/project-state.json` and `ai/command-registry.json` only when the task needs to rediscover or validate repository structure, commands, ports, environments, helper runtime, or verification capability.

- JSON is canonical when loaded.
- Markdown summaries provide human policy and explanation but do not override JSON.
- Do not load cache, tool-call, resource-budget, skill-catalog, or handoff files unless their subject is active.
- Prefer a known current fact or narrow lookup over broad rediscovery, subject to cache freshness rules.

## Verification And Completion Escalation

Heavy verification documents are late-phase controls:

- Read relevant verification policy when verification is planned, executed, reviewed, or reported.
- Read `tasks.md` for verification handoff, not for initial feature understanding.
- Read `checklist.md` immediately before judging feature completion.
- Read `ai/issue-completion-checklist.md`, `ai/qa-gate.md`, and `ai/done-claim-template.md` only when entering their respective pre-QA, QA, done-claim, or closure steps.
- Read `ai/lazycodex-runbook.md` when an AI completion claim lacks evidence or a reviewer must correct verification-avoidance behavior.

Late loading never authorizes skipping a required gate. It prevents the gate documents from being loaded before they can be acted on.

## Documentation Changes

### Feature-Owned Normative Change

1. Record the owning feature.
2. Read its `spec.md` first.
3. Read only the additional subject owners required by the change.
4. Update the narrowest canonical owner.
5. Load phase-specific files only if the task enters their phase.

### Repo-Wide Or Non-Normative Change

Record `Owning feature: none` for repo-wide normative work and state why. For Answer Mode or a Light Route non-normative edit, ownership recording is optional until the task escalates.

## Delegation Route

Only when dispatching subagents, load `ai/subagent-workflow.md`, `ai/github-issue-planning.md`, and the handoff/work-log records required for that delegation. Every handoff should contain the owning feature, files already read, decisions, open questions, and remaining evidence. Single-agent work does not preload delegation policy.

## Re-Routing Rule

Stop and re-route when scope changes. Typical escalations include:

- Answer Mode becomes a repository change.
- A Light Route wording edit changes a normative rule.
- A domain change also changes an API contract.
- Implementation reaches verification or completion.

Keep already loaded context only when it remains relevant; do not use re-routing as a reason to load every possible downstream document.
