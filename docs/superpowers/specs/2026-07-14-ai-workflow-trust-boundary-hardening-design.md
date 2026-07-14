# AI Workflow Trust Boundary Hardening Design

## Status And Scope

- Design status: approved direction on 2026-07-14
- Owning feature: none
- Baseline: GitHub `main` merge commit `26ba5e768c77139490abcb8fa66d2f696159c18b`
- Change type: repo-wide static workflow security hardening
- Product commands: NOT RUN

This design hardens the Phase 1B-3, Phase 2A/2B/2C, Phase 3A, and Phase 3B
evidence and trust boundaries. It does not run Gradle, product tests, the
application, Docker, HTTP/API, databases, migrations, seeds, deployment, or
infrastructure commands. It does not create real repository `.ai-runs`
evidence, promote registry commands to `VERIFIED`, close Issues, push a branch,
or claim native enforcement without host-owned proof.

## Reproduced Baseline Problems

The merged baseline has one recurring root cause: caller-authored or
repository-authored state can cross a trust boundary without a complete proof
of origin, content, correlation, and freshness.

1. Phase 1B-3 verifies that top-level done-claim references name session command
   results, but a check's own `evidenceRefs` only needs to be non-empty. A check
   can therefore cite evidence that is absent or unrelated. `notRunItems` is not
   compared with completion claims. `verify-finalized` verifies manifest
   artifacts but does not reconstruct and compare the final `run.json`, done
   claim, gate result, and session-derived graph. Validation failures after the
   OPEN-to-FINALIZING transition have no rollback path.
2. Phase 2C accepts caller-provided `checkId`, result enum, evidence path, and
   reason without validating an evidence envelope, digest, producer, task, gate,
   commit, policy, or freshness. Required `NOT_APPLICABLE` is accepted, optional
   `FAIL` is converted to `NOT_APPLICABLE`, and some static checks default to
   `PASS`. Cache entries bind only selected file digests. Skill and handoff
   schemas constrain array sizes but do not enforce distinct required IDs.
3. Phase 3A keeps trusted producer, key fingerprint, supported host, and current
   authoritative probe facts in repository-controlled policy. Test fixture
   paths are executable inputs to the evaluator. Replay consumption is an
   in-process set, and resolution correlation does not have a durable host-owned
   detection ledger.
4. Phase 3B labels a static contract workflow as `phase-3b-ci-gates`, treats the
   expected `NOT_CONFIGURED` exit as workflow success, and can evaluate an
   `AVAILABLE` repository `retainedRun` plus repository-local files without
   authenticated GitHub run, job, workflow, artifact, and head-SHA provenance.
   `ai/project-state.json` still says that no CI workflow exists.
5. `scripts/ai/tests/run-contract-tests.sh` runs shell contracts only. The
   selected workflow unit-test classes do not make the full helper regression
   suite part of the contract entry point.

## Chosen Architecture

Use a common validated-evidence contract with evidence-type-specific verifiers.
This is not one universal schema. It is one fail-closed interface: aggregation
accepts only a verifier-produced result, and each verifier proves the authority
appropriate to its evidence type.

Every trusted result must establish:

- closed schema and semantic validity;
- exact content SHA-256 and repository-relative or external identity;
- task key and gate invocation correlation;
- commit and policy identity where applicable;
- producer identity and authority source;
- creation timestamp and bounded freshness where applicable; and
- single-purpose evidence type, so a policy document cannot substitute for an
  execution result and a local file cannot substitute for GitHub provenance.

The implementation should keep these checks in small helpers rather than a
single monolithic validator. Phase-specific code remains responsible for its
own authority model.

## Trust Authority Matrix

| Evidence type | Authoritative producer | Required binding | Repository-authored substitute |
| --- | --- | --- | --- |
| Phase 1B command/gate artifact | supported repository gateway within one run | run, task, artifact path, digest, manifest graph | forbidden |
| Phase 2 verification leaf | named leaf producer with validated result artifact | task, gate, commit, policy digest, evidence digest, timestamp | policy-only PASS forbidden |
| Phase 2 cache decision | cache evaluator over every consumed input | all evidence digests, policy digest, task/change classification, environment input | partial cache key forbidden |
| Phase 3A runtime attestation | host-owned authoritative producer and probe | repository, task, gate, nonce, event ledger, host/version, key | repository key/probe/fixture forbidden |
| Phase 3B CI attestation | GitHub-owned run/job/artifact context | repository, workflow identity, run ID, attempt, job ID, head SHA, artifact ID and digest | retained JSON/local file forbidden |

## Phase 1B-3 Evidence Graph

The finalizer builds one normalized evidence graph before publishing immutable
final artifacts. Each check reference must resolve to an artifact in the active
session and every check evidence reference must also appear in the top-level
claim closure. Duplicate, absent, unbound, or wrong-kind references are
`INVALID_STATE`.

`notRunItems` must be unique and must not name a check, command, or capability
claimed as PASS or executed in the session. A PASS completion claim with a
contradictory not-run entry is `INVALID_STATE`; a required capability that is
only not-run is `BLOCKED` when applicability cannot be proven by Phase 1B.

The final `run.json` is deterministically derived from the FINALIZING session,
done claim, pre-done gate result, and manifest. `verify-finalized` recomputes
that projection and cross-checks important fields including run/task identity,
timestamps, result/reason, command and policy references, evidence references,
redaction state, manifest closure, done-claim outcome, and gate scope. Any
tampering or stale projection is `INVALID_STATE`.

Before the first OPEN-to-FINALIZING compare-and-swap, the finalizer creates a
fresh UUID and exclusively publishes closed
`.state/finalization-journals/<journal-id>.json`. This independent authority
contains a journal UUID, exact source OPEN session, exact intended FINALIZING
session, claim-input reference, and expected lock-recovery prefix. The run
session's closed top-level `finalizationJournalIdentity` is null in OPEN, equals
that journal path/UUID/digest in FINALIZING, and remains equal to the FINALIZED
receipt's `journalIdentity`. Because the journal embeds that identity, its
canonical digest is computed after normalizing only the embedded digest to 64
ASCII zeroes; no other field is omitted or rewritten. Every attempt uses a new
path, and every published journal remains immutable read-only audit history.

Before final artifacts are published, a second exact compare-and-swap seals
those inputs as a closed FINALIZED receipt in `.state/run-session.json`. The
retained read-only receipt contains the complete run projection, canonical
claim and gate identities, manifest identity, journal identity, and exact
artifact path/kind identities; `run.json` and the mutable manifest surface are
consumers, not the authority.

Finalization uses a recoverable transaction boundary. Only the journal identity
in the session is active authority; inactive schema-valid UUID journals do not
block OPEN work. A fixed legacy marker is never accepted and remains explicit
recovery-required. Rollback validates the journal's exact OPEN source plus only
an allowed lock-recovery suffix and compare-and-swaps that OPEN session, which
atomically clears active authority. It never deletes a published journal.
FINALIZING and FINALIZED recovery additionally validate the session's exact
journal identity against the independent authority before cleanup, rollback,
or resume. Publication uncertainty is reconciled against the possibly
published session/journal into a schema-valid rollback or recovery-required
result, never an escaped traceback. If validation or publication fails before
`run.json` is published, recovery removes only safely attributable partial
final artifacts and restores the exact validated OPEN source. If cleanup
cannot be proved safe, it retains the recovery state and returns BLOCKED.
Immutable final JSON is fully written and file-fsynced in a same-directory
temporary, changed to read-only and mode-verified before an exclusive link
makes it visible, then directory-fsynced. Thus post-chmod uncertainty publishes
nothing and post-link uncertainty can expose only a read-only file. Successful
resume and `ALREADY_FINALIZED` recovery call and verify read-only sealing for
the exact claim, gate, manifest, run, session, and active journal. Failed
recovery over raw FINALIZED state reapplies read-only mode to the session and
safely identified journal before releasing the lock. A published `run.json`
remains immutable.

Control precedence remains:

1. malformed or contradictory evidence graph: `INVALID_STATE`;
2. blocking policy violation: `POLICY_VIOLATION`;
3. executed child failure: `FAIL`;
4. required blocked/not-configured/not-applicable/skipped leaf: `BLOCKED`;
5. internally consistent integrity-only evidence: `PASS` with
   `completenessEvaluated: false`.

## Phase 2 Verification, Cache, Skills, And Handoff

Caller leaf input becomes a reference to a closed verification leaf artifact,
not a free-form result summary. The artifact includes the check ID, result,
task key, gate invocation ID, commit SHA, policy SHA-256, producer ID, produced
timestamp, expiry/freshness bound, evidence reference, evidence SHA-256, and
evidence schema identity. The loader validates the referenced evidence content
and digest before returning a verified leaf.

Each gate evaluation bounded-reads the canonical verification policy exactly
once. Strict JSON parsing, schema validation, and the policy SHA-256 all consume
that same byte snapshot; one recursively immutable policy value and its digest
then flow through the native leaf and every external leaf validation. The gate
never reopens the policy path, so replacement cannot combine one policy's
applicability semantics with another policy's identity.

The gate never creates a PASS from only canonical policy. Missing explicit
evidence for a required leaf is `NOT_CONFIGURED` mapped to `BLOCKED`. A required
leaf may be `NOT_APPLICABLE` only when canonical policy explicitly marks that
check irrelevant for the selected change type and supplies the matching reason
code; a caller cannot choose it. Optional failures remain visible as `FAIL` and
make the aggregate `FAIL`. Optional `NOT_CONFIGURED` or policy-authorized
inapplicability may remain `NOT_APPLICABLE`.

Cache keys cover every input used to reach the decision. The exact ordered
required-plus-optional check sequence for the selected change type is identical
to the sequence aggregated by `verification_gate`; the current entry point is
correlation and applicability identity, not a producer filter. Every
check/producer-indexed binding includes the verified leaf-result reference and
digest plus the evidence path, digest, and canonical schema. Policy digest,
change type, entry point, task/gate correlation, commit, environment input, and
expiry remain bound. Missing, extra, duplicate, reordered, wrong-producer,
wrong-schema, changed, expired, unavailable, or unmapped inputs are STALE or
UNCERTAIN and cannot reuse PASS.

The native binding additionally fixes the logical result reference to
`ai/native-adapter-result.json` and its actual policy evidence to
`ai/native-runtime-adapters.json` under the native-runtime-adapters schema.
Copied or arbitrary native paths are stale even for identical bytes. Because
the current native result does not contain a durable task, gate, commit, policy,
and freshness envelope, the exact current native binding is still uncertain
and cannot make a verification decision fresh.

Skill catalog semantic validation requires every approved skill ID exactly once.
Handoff semantic validation requires every distinct skill selected by the
catalog/policy exactly once and rejects missing, duplicate, unknown, or
wrong-document skill bindings.

## Phase 3A Host-Owned Trust

Repository policy may describe unsupported baseline state but cannot introduce
a trusted producer, signing key, supported host, authoritative current version,
or production attestation. Production trust anchors and probes are supplied
through a host-owned input outside repository and fixture namespaces. The
repository evaluator accepts their public verification material only through
that explicit host channel and requires it to match the attestation.

Repository fixtures and temporary keys remain test-only. The production CLI
rejects fixture policy, fixture snapshot, and repository-controlled trust-anchor
paths for promotion. On Codex Desktop without an authoritative probe, the
canonical result stays `UNSUPPORTED`/`UNPROBED` and maps only to qualified
repository behavior; it never becomes native enforcement PASS.

Replay prevention uses a durable host-owned nonce/attestation ledger or a
host-verified consumption receipt. A process-local set may remain only as
defense in depth. The ledger key binds repository, producer, task, gate,
attestation ID, nonce, and signed event-set digest. Reuse in another process is
rejected.

A resolution must bind the original detection event ID and its immutable task,
original gate invocation, deduplication identity, and event digest. The later
resolution gate and signed attestation must name the same original detection;
an unrelated event or resolution is BLOCKED.

## Phase 3B Contract And Enforcement Separation

Create two explicitly different checks:

- `phase-3b-repository-contract`: runs static/helper/schema regression tests and
  may be green when the repository contract is valid.
- `phase-3b-native-enforcement`: represents actual CI/native enforcement and
  must not be green while required provenance, native installation, durable
  evidence, or remote runner proof is NOT_CONFIGURED or BLOCKED.

The repository workflow may publish contract diagnostics, but it must not
translate expected enforcement `NOT_CONFIGURED` exit code 3 into enforcement
success. Until GitHub branch protection and host-owned evidence are configured,
project state reports that the contract workflow exists while native CI
enforcement remains `NOT_CONFIGURED`.

CI PASS requires a GitHub-owned provenance envelope binding repository, workflow
path and immutable workflow identity, run ID, attempt, job ID, event name, head
SHA, artifact ID, artifact digest, and the digests of every included file. The
evaluator also binds native evidence, bypass evidence, and resolution IDs to the
same run, attempt, job, and commit. A repository `retainedRun` object is only a
claim to compare against GitHub provenance, never authority by itself.

## Test Strategy

Each production change follows RED-GREEN-REFACTOR. A focused regression test is
added and observed failing for the intended reason before implementation.

Required Phase 1B tests:

- unbound and nonexistent check evidence;
- contradictory not-run claims;
- tampered final `run.json` and stale final projection;
- stale generated summary;
- validation and injected I/O failure after entering FINALIZING, proving safe
  rollback or recoverable journal behavior;
- OPEN plus journal blocking normal operations until explicit `ALREADY_OPEN`
  recovery, including allowed lock-recovery suffix validation;
- journal path/UUID/digest tampering, first-CAS session identity binding, and
  FINALIZED receipt identity equality;
- publication uncertainty and runtime exception reconciliation without a
  traceback, plus read-only mode repair on every failed FINALIZED recovery;
- post-chmod and post-link publication uncertainty, six-file recovery mode
  repair, applied-error after OPEN rollback CAS, retained immutable audit
  journals, fixed legacy-marker rejection, and a distinct next-attempt journal;
- result precedence for blocking policy and child failure.

Required Phase 2 tests:

- evidence-free PASS;
- mismatched task, gate, commit, evidence digest, policy digest, and producer;
- expired evidence and stale cache keys;
- required caller-authored `NOT_APPLICABLE`;
- optional `FAIL` visibility;
- duplicate skill ID and missing distinct required skill.

Required Phase 3A tests:

- repository-controlled signing key and supported-host declaration;
- forged or repository-authored host probe;
- attestation replay from a separate process/ledger instance;
- unrelated resolution and original detection mismatch;
- stale and replayed nonce;
- current Codex Desktop remaining unprobed and unsupported.

Required Phase 3B tests:

- fake retained run;
- wrong head SHA, run attempt, job, and workflow identity;
- artifact ID or digest mismatch and tampered artifact contents;
- evidence from an unrelated GitHub run;
- contract check success remaining distinct from enforcement status.

The contract test entry point runs the complete core Python helper regression
suite plus shell contract tests. Verification also includes shell syntax, JSON
schema and negative fixtures, `git diff --check`, absence of real `.ai-runs`,
absence of non-fixture `VERIFIED`/`DONE` outputs, and a clean GitHub Issue/PR
state. Test fixtures use temporary directories and harmless helper inputs only.

## Documentation And State Synchronization

Update the narrow canonical documents and their generated summaries together.
`ai/project-state.json` distinguishes CI workflow presence from native
enforcement availability. Phase 1B remains integrity-only. Phase 3A current host
remains unprobed/unsupported unless host-owned evidence is supplied. Phase 3B
contract availability does not imply required-check or enforcement completion.

## Completion And External Boundaries

Repository contract tests can establish only repository contract PASS. Native
Phase 3A and CI Phase 3B enforcement remain `NOT_CONFIGURED`, `UNSUPPORTED`, or
`BLOCKED` until the host/GitHub provides authoritative probes, trust anchors,
durable replay storage, run/job/artifact provenance, and branch-protection
configuration. GitHub Action success alone is not Phase 3 enforcement PASS.
Issues #10 and #12 remain open unless their independent closure criteria are
satisfied through a separately authorized workflow.
