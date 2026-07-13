# AI Workflow Phase 3B CI Gates And Durable CI Evidence Design

## Status And Scope

Phase 3B follows merged PR #11 and Issue #12. It adds a machine-readable CI
capability/status contract, a static GitHub Actions gate, and a durable evidence
policy. It does not change the approved Phase 3A native adapter baseline:
`codex-desktop` remains `hostVersion: null` / `UNPROBED`, all four native
surfaces are `UNSUPPORTED`, and Phase 2C native leaf mapping remains
`NOT_APPLICABLE` with repository-only qualification.

## Recommended Approach

Use a static/helper CI workflow and a closed durable evidence contract. Compared
with a docs-only contract, this gives GitHub a concrete required-check surface.
Compared with full product CI, it avoids running commands outside the approved AI
workflow boundary. The workflow runs only helper/static checks and the CI evidence
gate wrapper.

## Durable Evidence And Retention

A future PASS must bind repository, commit SHA, workflow run ID, job ID, attempt,
`taskKey`, `gateInvocationId`, native adapter status digest, bypass event-set
SHA-256, and `resolutionEventIds`. Retention is at least 90 days. A cache or
handoff record can summarize those facts but cannot replace the retained remote
run artifact.

## Failure Policy

Unsupported or unprobed local hosts continue as repository-qualified
`NOT_APPLICABLE` for the native adapter leaf. Supported CI hosts without native
adapter installation, durable evidence, or remote runner provenance are
completion-blocking. cross-process challenge and bypass replay durability remain
blocked until durable CI evidence exists.
