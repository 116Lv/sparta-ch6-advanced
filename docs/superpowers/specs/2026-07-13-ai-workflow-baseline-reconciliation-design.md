# AI Workflow Baseline Stabilization And Reconciliation Design

## Goal

Stabilize the approved Phase 1A through Phase 2C repository baseline, preserve all established phase boundaries, and reconcile the five `pending_issue` work-log units when GitHub Issue access is available.

This work does not begin Phase 3, execute product commands, create repository `.ai-runs` evidence, publish artifact manifests or finalized `run.json`, or promote command-registry entries to `VERIFIED`.

## Approved Baseline

The following decisions remain unchanged:

- Phase 1A, Phase 1B, Phase 2A, Phase 2B, and Phase 2C implementation results are accepted baselines.
- Phase 1B-3 remains integrity-only with `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.
- Phase 2C verification completeness and applicability apply only through its static/helper/contract gates.
- Product commands remain NOT RUN unless a separately approved later phase authorizes them.
- No issue-backed closure, reconciliation-complete claim, or unqualified overall DONE claim is allowed before reconciliation actually succeeds.

## Scope

### Baseline Stabilization

1. Inspect the full working tree and classify every changed or untracked path as an approved Phase 1A-2C artifact, an unrelated user change, or an unsafe/generated artifact.
2. Run only the established non-product helper, schema, shell-contract, preflight, repo-intake, and static consistency checks.
3. Confirm that the repository contains no real `.ai-runs`, non-fixture `artifact-manifest.json`, finalized `run.json`, secrets, or unintended registry `VERIFIED` state.
4. Correct only genuine consistency defects discovered by those checks. Approved behavior and phase boundaries are not redesigned.
5. Create intentional baseline commits grouped by coherent phase or infrastructure boundary. Unrelated user changes are excluded.

### GitHub Issue Reconciliation

Reconciliation covers these five existing fallback units:

- `phase-1b-command-gateway`
- `phase-2a-context-cache`
- `phase-2b-skills-handoff`
- `phase-2c-verification-gates`
- `subagent-workflow-20260710`

For each unit, the orchestrator follows `ai/github-issue-planning.md`:

1. Check current GitHub authentication and repository Issue permissions.
2. Create exactly one GitHub Issue from the recorded `expected_issue_scope` and current evidence.
3. Move the entire fallback directory from `ai/work-logs/no-issue/<work-key>/` to `ai/work-logs/issue-<number>/`.
4. Update every summary and role log with the real Issue number and URL, `tracking_status: issue_backed`, `reconciliation_required: false`, timestamps, and complete migration history.
5. Replace the work-log index entry and preserve the former path in migration records.
6. Add an Issue comment linking the migrated repository log and summarizing work completed before Issue creation.

Reconciliation is atomic per work unit. If any step after Issue creation fails, that unit remains explicitly incomplete and is not reported as reconciled. Successfully reconciled units do not depend on all other units succeeding.

## Commit Strategy

The recommended strategy is a small ordered commit series rather than one oversized checkpoint:

1. Phase 1B command gateway and integrity contracts.
2. Phase 2A context intake and cache controls.
3. Phase 2B skills and handoff contracts.
4. Phase 2C verification/applicability gates and document integration.
5. GitHub reconciliation metadata and directory migrations.

Phase 1A history is already committed and is not rewritten. Commit boundaries may be combined only where files are genuinely shared across phases and splitting them would create an invalid intermediate repository state.

## Failure Handling

- GitHub still returns the recorded 403: preserve the exact error, keep all affected units `pending_issue`, and stop reconciliation without fabricating Issue numbers or state.
- Authentication succeeds but Issue creation fails: record the new exact failure and timestamp while preserving previous attempt history.
- Issue creation succeeds but local migration fails: keep the Issue open, record reconciliation as incomplete, and retry the repository migration without creating a duplicate Issue.
- A validation check fails: diagnose and fix only the defect in scope, then rerun the relevant non-product checks.
- An unrelated working-tree change overlaps a target file: preserve it and isolate the baseline hunk; ask for direction only when safe separation is impossible.

## Verification

Allowed verification is limited to static/helper/contract/temp-fixture checks already accepted for Phase 2C, including:

- focused and full `workflow_helper` unit tests;
- helper shell contract tests;
- runtime preflight and read-only repo intake;
- schema and generated-summary consistency checks;
- `git diff --check` and static scans for forbidden evidence/state;
- GitHub metadata reads and Issue operations required for reconciliation.

The following remain NOT RUN: Gradle tests/builds, product server startup, Docker Compose, HTTP/API smoke calls, database operations, migrations, seeds, and product-command execution through command-runner.

## Completion Criteria

Baseline stabilization passes when the intended Phase 1A-2C repository state is validated, forbidden artifacts and state transitions are absent, and coherent baseline commits are created without unrelated changes.

GitHub reconciliation passes only for a work unit after all six reconciliation steps are complete. If GitHub authorization remains unavailable, baseline stabilization may pass while reconciliation remains `pending_issue`; no issue-backed closure, reconciliation-complete claim, or unqualified overall DONE claim is made.

Phase 3A and Phase 3B remain separate future design and implementation efforts after this stabilization work.
