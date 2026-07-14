# AI Workflow Phase 3B CI Gates And Durable CI Evidence Design

## Status And Scope

Phase 3B follows merged PR #11 and Issue #12. The repository contract check
`phase-3b-repository-contract` is `CONFIGURED_UNVERIFIED`; it validates the
checked-in helper and shell contracts but is not a native enforcement check.
`phase-3b-native-enforcement` remains `NOT_CONFIGURED` with
`requiredCheckConfigured: false`. A green repository contract does not imply native enforcement `PASS`.

The approved Phase 3A baseline is unchanged: `codex-desktop` remains
`hostVersion: null` / `UNPROBED`, all four native surfaces are `UNSUPPORTED`,
and the Phase 2C native leaf maps to repository-qualified `NOT_APPLICABLE`.
Phase 1B-3 remains integrity-only and cannot mark a registry `VERIFIED` or
support an unqualified completion claim.

## Repository Contract Entry Point

The workflow installs pinned Python helper dependencies and invokes only
`scripts/ai/tests/run-contract-tests.sh` for helper and shell regressions. The
entry point resolves and enters the repository root, runs the full `scripts.ai.tests.test_workflow_helper` module exactly once, and then runs the
runtime-preflight and command-runner shell contract suites in that order.
`set -eu` in the entry point and `set -o pipefail` around the workflow's
diagnostic `tee` preserve a nonzero result from any suite.

Both shell suites exercise the repository gateway contracts only. The workflow
does not run product commands, call the CI evidence gate, create a native
enforcement job, or publish an enforcement result. Its retained output is
repository-contract diagnostics, not proof of native enforcement.

## External Trust Boundary

The production CI evidence gate remains unconditionally `NOT_CONFIGURED` until
an external GitHub/Sigstore verifier supplies authenticated current-run
authority. GitHub environment values such as run ID, run attempt, job,
workflow ref/SHA, and head SHA are correlation inputs; repository code cannot
self-certify them. A future verifier must cryptographically verify the artifact
attestation and signer identity, provide an independently trusted current-run
context, and bind both the provenance envelope and repository `retainedRun`
claim to that context.

Artifact members used by a future trusted path require the safe POSIX
handle-relative reader. A host without that backend fails closed. Constructible
repository values and matching local JSON do not provide external authority.

## Durable Evidence And Retention

A future enforcement PASS must bind repository, workflow ref and SHA, head
commit, event, workflow run ID and attempt, job ID, artifact ID and digest,
member digests, `taskKey`, `gateInvocationId`, native evidence digest, bypass
event-set SHA-256, `resolutionEventIds`, attestation subject, and signer
repository. Retention is at least 90 days. A cache or handoff record may
summarize those facts but cannot replace the authenticated retained artifact.

## Failure Policy

Unsupported or unprobed local hosts continue as repository-qualified
`NOT_APPLICABLE` for the native adapter leaf. Supported CI hosts without native
adapter installation, an installed required enforcement check, authenticated
durable evidence, or remote-runner provenance are completion-blocking.
The cross-process challenge and bypass event replay durability remain blocked until
the external trust path is installed and verified.
