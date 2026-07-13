# AI Workflow Verification Gates

## Human Policy Notes

`ai/verification-policy.json` is the canonical Phase 2C source for verification completeness, task/change applicability, workflow entry points, and result mapping. This Markdown file explains the policy for agents and reviewers. JSON is canonical. Markdown is not parsed as executable state.

Product commands remain NOT RUN for Phase 2C helper/static verification. `scripts/ai/verification-gate.sh` evaluates only static/helper/contract inputs and must not launch Gradle, build, product/unit project tests, server, Docker Compose, HTTP/curl/API, database, migration, seed, or infrastructure commands.

## Entry Points

- `verification-level`: maps a change type to required verification checks.
- `api-smoke`: maps real API smoke requiredness for API-visible work.
- `failure-triage`: records failed or blocked leaf status before rerun or continuation.
- `review`: checks independent review and delegated-work readiness.
- `done-claim`: checks whether completion evidence is applicable before a done claim.

## Task/Change Applicability

Phase 2C defines task/change applicability by change type in `ai/verification-policy.json`. The supported change types are `documentation-only`, `static-workflow`, `domain-logic`, `db-api`, `auth-permission`, `critical-data`, and `user-flow`.

Verification completeness means every required check for the selected change type has an allowed mapped result and every inapplicable check is explicitly mapped with a reason. While `tracking_status` remains `pending_issue`, implementation QA may pass with a complete fallback, but issue-backed closure, reconciliation-complete, and unqualified overall DONE remain blocked.

## Result Mapping

- `NOT_CONFIGURED` on a required check maps to `BLOCKED`.
- `NOT_CONFIGURED` on an irrelevant or optional check maps to `NOT_APPLICABLE`.
- `NOT_APPLICABLE` is allowed only when the selected change type makes the check irrelevant.
- `BLOCKED` on a required check remains `BLOCKED`.
- `FAIL` on a required check remains `FAIL`.

`NOT_APPLICABLE` may be displayed as `N/A` in Markdown summaries, but executable JSON stores `NOT_APPLICABLE`.

## Evidence Boundary

Phase 2C static/helper gates do not create repository `.ai-runs`, artifact manifests, finalized `run.json`, registry `VERIFIED` transitions, issue-backed closure claims, reconciliation-complete claims, or unqualified overall DONE claims. Real project verification remains NOT RUN unless a later supported command-runner evidence path is explicitly used.
