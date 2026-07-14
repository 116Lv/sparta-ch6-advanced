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

A CI evidence PASS requires an immutable `GitHubCiProvenance` envelope supplied
in memory only after an external GitHub/Sigstore verifier authenticates its
attestation. The public `scripts/ai/ci-evidence-gate.sh` entry point has no
provenance argument, always calls the helper with `github_provenance=None`, and
therefore cannot produce PASS from repository files or `retainedRun` state.

The closed provenance envelope binds the expected repository and workflow ref,
workflow SHA, head SHA, event name, workflow run ID and attempt, job ID,
artifact ID and digest, every artifact member path and SHA-256, task and gate
correlation, native evidence SHA-256, complete bypass event-set SHA-256, and
resolution event IDs. The verified attestation subject must equal the artifact
digest and its signer repository must be `116Lv/sparta-ch6-advanced`. Artifact
members are read through pinned, no-follow file identities and rehashed before
PASS; path escape, symlink substitution, identity races, and content tampering
are rejected.

Repository `retainedRun` is only a claim compared field-for-field with the
authenticated provenance. Correct-looking repository files cannot create the
provenance value and cannot substitute for external verification. The minimum
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
