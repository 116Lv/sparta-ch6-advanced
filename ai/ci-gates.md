# Phase 3B CI Gates And Durable Evidence

Phase 3B starts after PR #11 was merged into `main` at commit
`400c00f35f9d21cbeec44b0f40f49dac564a4bb6`. It preserves the approved Phase
1A, 1B, 2A, 2B, 2C, and 3A baseline and does not redesign native adapter trust.
Phase 1B-3 remains `INTEGRITY_ONLY` with `completenessEvaluated: false`.

## Approaches Considered

1. Repository-only CI status contract with no workflow: lowest risk, but it
   would leave required CI gate wiring unexercised.
2. Full product CI with Gradle and service dependencies: stronger product
   signal, but outside the approved Phase 3B evidence scope and would blur the
   product-command boundary.
3. Recommended: a static/helper GitHub Actions workflow plus a closed durable
   evidence contract. This wires a required CI gate without running Gradle,
   Docker, HTTP/API, database, migration, seed, deploy, or infrastructure
   commands.

## Durable Evidence Contract

A CI evidence PASS requires retained GitHub Actions evidence bound to repository,
commit SHA, workflow run ID, job ID, run attempt, `taskKey`,
`gateInvocationId`, native adapter status digest, complete bypass event-set
SHA-256, and `resolutionEventIds`. The minimum retention is 90 days. Cache reuse
is forbidden unless the workflow run identity and all bindings match; handoff may
reuse summaries only, never substitute them for durable CI evidence.

The current repository has a CI workflow file, but this local run has no
completed remote workflow run or retained artifact identity. Therefore the local
CI evidence gate returns `NOT_CONFIGURED` with Phase 2C leaf `BLOCKED` and reason
`CI_EVIDENCE_NOT_AVAILABLE`.

## Hook Enforcement Levels

- GitHub Actions required check: configured as `phase-3b-ci-gates`, but durable
  run evidence is not yet available locally.
- CI native adapter installation: `NOT_CONFIGURED`; supported CI hosts must fail
  closed until installed and attested.
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
