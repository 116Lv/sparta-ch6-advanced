# Phase 3B CI Gates And Durable Evidence

Phase 3B starts after PR #11 was merged into `main` at commit
`400c00f35f9d21cbeec44b0f40f49dac564a4bb6`. It preserves the approved Phase
1A, 1B, 2A, 2B, 2C, and 3A baseline and does not redesign native adapter trust.
Phase 1B-3 remains `INTEGRITY_ONLY` with `completenessEvaluated: false`.

## Approaches Considered

1. Repository-only CI status contract with no workflow: lowest risk, but it
   would leave even the static repository contract unexercised.
2. Full product CI with Gradle and service dependencies: stronger product
   signal, but outside the approved Phase 3B evidence scope and would blur the
   product-command boundary.
3. Recommended: a static/helper GitHub Actions workflow plus a closed durable
   evidence contract. This exercises the repository contract without claiming
   that a required native-enforcement check exists, and it does not run Gradle,
   Docker, HTTP/API, database, migration, seed, deploy, or infrastructure
   commands.

## Authenticated Provenance And Durable Evidence Contract

This repository has no external GitHub/Sigstore verifier integration. The production gate remains unconditionally `NOT_CONFIGURED`, even if repository
Python code constructs a correct-looking provenance object and passes it to the
helper. The public `scripts/ai/ci-evidence-gate.sh` entry point has no provenance
argument and cannot produce PASS from repository files or `retainedRun` state.

The lower-level pure verifier models a future integration without granting
production authority. It requires an immutable `GitHubTrustedRunContext`
supplied by that external verifier. The provenance envelope and repository
`retainedRun` claim must independently match every field in that context; they
are never used to derive their own expected values. An older genuine run fails
when its identity differs from the trusted current-run context.

The closed provenance envelope binds the expected repository and workflow ref,
workflow SHA, head SHA, event name, workflow run ID and attempt, job ID,
artifact ID and digest, every artifact member path and SHA-256, task and gate
correlation, native evidence SHA-256, complete bypass event-set SHA-256, and
resolution event IDs. The verified attestation subject must equal the artifact
digest and its signer repository must be `116Lv/sparta-ch6-advanced`. Artifact
Production artifact members require a safe POSIX handle-relative backend using
pinned directory descriptors and `O_NOFOLLOW`. Path escape, symlink
substitution, identity races, and content tampering are rejected. When those
primitives are unavailable, non-POSIX production hosts fail closed with an
explicit backend-unavailable result. A unit-test-only member consumer exercises
the pure correlation verifier on Windows; it is not reachable from the
production gate and cannot establish authority.

Repository `retainedRun` and provenance are only claims. Correct-looking
repository files, frozen values, schema-valid booleans, or caller-selected
expected values cannot substitute for external verification. The minimum
retention is 90 days. Cache reuse is forbidden unless the workflow run identity
and all bindings match; handoff may reuse summaries only, never substitute them
for durable CI evidence.

The current repository has the repository-contract workflow file, but the
contract is `CONFIGURED_UNVERIFIED` and native enforcement is `NOT_CONFIGURED`.
This local run has no completed remote workflow run or retained artifact
identity or externally authenticated provenance. Therefore the public/local CI
evidence gate returns `NOT_CONFIGURED` with Phase 2C leaf `BLOCKED` and reason
`CI_GITHUB_PROVENANCE_NOT_AVAILABLE`.

## Hook Enforcement Levels

- Repository contract check `phase-3b-repository-contract` is `CONFIGURED_UNVERIFIED`; the workflow exists but has not been verified by a remote run in this task.
- Native enforcement check `phase-3b-native-enforcement` is `NOT_CONFIGURED` with `requiredCheckConfigured: false`; no GitHub required check or native adapter has been externally installed and attested.
- Current `codex-desktop` host: `UNSUPPORTED` / `HOST_UNSUPPORTED`; Phase 2C
  native leaf remains `NOT_APPLICABLE` with repository-only qualification.
- Remote runner completion: completion-blocking when run identity, artifact
  retention, or native adapter provenance is missing.

## Responsibility Boundary

The repository gateway owns registered command authority, run lifecycle,
artifact manifests, and registry promotion. CI/native enforcement owns discovery,
version provenance, remote runner attestation, bypass event durability, and
challenge/replay durability. CI evidence cannot promote registry `VERIFIED`,
close an Issue, or authorize an unqualified overall DONE claim by itself.
