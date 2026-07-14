---
issue: 14
issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/14
agent: reviewer
tracking_status: issue_backed
status: in_progress
owning_feature: "none"
current_owner: reviewer
started_at: 2026-07-14T03:02:02+09:00
ended_at:
last_updated: 2026-07-14T03:05:47+09:00
branch: codex/ai-workflow-trust-hardening
related_files:
  - docs/superpowers/specs/2026-07-14-ai-workflow-trust-boundary-hardening-design.md
  - docs/superpowers/plans/2026-07-14-phase-1b3-evidence-integrity-hardening.md
  - scripts/ai/workflow_helper.py
  - scripts/ai/tests/test_workflow_helper.py
changed_files:
  - ai/work-logs/issue-14/reviewer.md
commands_run: []
tests_run: []
blockers: []
skill_ids:
  - review-gate
  - verification-runner
handoff_state_ref: ai/agent-handoff.json
reusable_context_refs:
  - ai/workflow-cache.json
  - ai/verification-policy.json
not_run_project_commands:
  - Gradle
  - build
  - product/unit project tests
  - application server
  - Docker Compose
  - HTTP/curl/API
  - database
  - migration
  - seed
  - infrastructure commands
github_reconciliation_status: issue_backed
reconciliation_required: false
issue_creation_attempted_at: 2026-07-14T02:48:51+09:00
issue_creation_failure_reason:
expected_issue_scope: AI workflow trust-boundary hardening across Phases 1B-3 through 3B
migration_history: []
---

# Summary

Independently review each committed task for exact spec compliance and code quality before the next task begins.

# Work Done

- Task 1 review inputs prepared by the orchestrator.

# Current State

Ready to review global Task 1 / Phase 1B-3 local Task 1.

# Decisions

- Use the task brief and recorded commit range as the review boundary.

# Verification Evidence

- Command: Not run; task reviewer starts from implementer TDD evidence and the generated diff package.
- Result: NOT RUN

# Blockers

- None

# Next Handoff

- Next role: reviewer
- Required reading:
  - [Phase 1B-3 execution plan](../../docs/superpowers/plans/2026-07-14-phase-1b3-evidence-integrity-hardening.md)
- Context links:
  - [Issue summary](README.md)
  - [Implementation role log](implementation-agent.md)
- Remaining work: Produce both spec-compliance and task-quality verdicts for Task 1.
- Evidence required: File-and-line strengths/findings and approval or required fixes.

## Task 1 Review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- The required regressions are present at `scripts/ai/tests/test_workflow_helper.py:5658-5678`; evidence binding, closure, and not-run validation are implemented at `scripts/ai/workflow_helper.py:4793-4840`, invoked after identity checks at `scripts/ai/workflow_helper.py:4843-4849`, and resolved command artifacts are reused at `scripts/ai/workflow_helper.py:4875-4881`.
- Existing integrity-only expectations remain asserted: `completenessEvaluated: false` and `scope: INTEGRITY_ONLY` at `scripts/ai/tests/test_workflow_helper.py:5648-5649`.
- Cannot verify from diff that the recorded RED/GREEN commands actually ran or that no prohibited commands ran; the review package contains only recorded execution claims at `ai/work-logs/issue-14/implementation-agent.md:20-29`.

### Strengths

- Check evidence must belong to both the top-level claim and active session before schema-aware resolution (`scripts/ai/workflow_helper.py:4794-4816`).
- Exact evidence closure includes every session command result (`scripts/ai/workflow_helper.py:4817-4822`).
- Duplicate and contradictory not-run IDs receive distinct validation reasons (`scripts/ai/workflow_helper.py:4831-4840`).
- Identity validation retains precedence over the newly added semantic validators (`scripts/ai/workflow_helper.py:4843-4849`).
- Both required trust-boundary regressions assert exact result, status, and reason (`scripts/ai/tests/test_workflow_helper.py:5658-5678`).

### Issues

#### Minor (Nice to Have)

- The new duplicate-not-run branch lacks a directly added regression in this slice; the added tests cover unbound evidence and check/not-run contradiction only (`scripts/ai/workflow_helper.py:4832-4835`, `scripts/ai/tests/test_workflow_helper.py:5658-5678`).

### Assessment

- Task quality: Approved.
- Reasoning: The implementation matches the prescribed validation graph, ordering, and artifact reuse without weakening visible integrity assertions. The only concern is optional direct coverage for one newly introduced validation branch.

## Task 2 Review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- The required projection checks, schema-loaded inputs, and integrity-only output fields are implemented at `scripts/ai/workflow_helper.py:5016-5044`, `scripts/ai/workflow_helper.py:5157-5167`, and `scripts/ai/workflow_helper.py:5175-5176`.
- Cannot verify from diff that the reported RED/GREEN and 12-test commands actually ran; those execution claims appear only in `.superpowers/sdd/task-2-phase1b3-report.md:23`, `.superpowers/sdd/task-2-phase1b3-report.md:34`, `.superpowers/sdd/task-2-phase1b3-report.md:44`, and `.superpowers/sdd/task-2-phase1b3-report.md:48`.

### Strengths

- Projection validation covers run and claim identity, the gate-derived result, exact final evidence ordering, all three manifest-kind reference sets, and manifest binding (`scripts/ai/workflow_helper.py:5030-5038`).
- Finalized-run verification checks directory closure before schema-loading the claim and gate and invoking projection validation (`scripts/ai/workflow_helper.py:5155-5167`).
- Both required regressions assert exit 5 and `FINAL_RUN_PROJECTION_MISMATCH` for tampered task identity and stale result (`scripts/ai/tests/test_workflow_helper.py:5723-5753`).
- `completenessEvaluated: false` and `scope: INTEGRITY_ONLY` remain preserved (`scripts/ai/workflow_helper.py:5175-5176`).

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None.

#### Minor (Nice to Have)

- None.

### Assessment

- Task quality: Approved.
- Reasoning: The implementation matches the specified deterministic projection contract and preserves the integrity-only verification boundary. No correctness or scope violation is visible in the packaged diff (`scripts/ai/workflow_helper.py:5016-5044`, `scripts/ai/workflow_helper.py:5155-5176`).

## Task 3 Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- The prior Critical durable-replacement defect is closed: failed OPEN-to-FINALIZING and FINALIZING-to-OPEN replacements reconcile the exact full session while validating the retained lock before and after the read (`scripts/ai/workflow_helper.py:5114-5120`, `scripts/ai/workflow_helper.py:5173-5176`, `scripts/ai/workflow_helper.py:5312-5321`).
- Both post-apply fault regressions assert deep equality with the complete captured OPEN snapshot (`scripts/ai/tests/test_workflow_helper.py:5904-5932`, `scripts/ai/tests/test_workflow_helper.py:5934-5971`).
- Publication remains rollback-blocking, rollback requires the exact finalization refs and FINALIZING projection, and cleanup retains secure path resolution and lock validation (`scripts/ai/workflow_helper.py:5130-5163`).
- Integrity-only semantics remain preserved (`scripts/ai/workflow_helper.py:5005-5006`, `scripts/ai/tests/test_workflow_helper.py:5670-5671`).
- The updated report records the test file, exact focused command, focused RED/GREEN results, surrounding-class result, and diff-check result (`.superpowers/sdd/task-3-phase1b3-report.md:24`, `.superpowers/sdd/task-3-phase1b3-report.md:56-63`). Per the review constraint, these commands were not independently rerun.

### Strengths

- Reconciliation distinguishes the exact original OPEN snapshot, exact expected FINALIZING projection, and any conflicting or unreadable state without adding an unlocked or state-only bypass (`scripts/ai/workflow_helper.py:5306-5321`).
- Successful rollback preserves the original validation or I/O result; ambiguous or unsafe rollback maps to `FINALIZATION_RECOVERY_REQUIRED` (`scripts/ai/workflow_helper.py:5287-5296`, `scripts/ai/workflow_helper.py:5334-5354`).
- The specification documents the exact-session, publication, cleanup, and explicit-recovery boundary while retaining `INTEGRITY_ONLY` scope (`docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md:344-350`).

### Issues

#### Critical (Must Fix)

- None. The prior Critical is closed by exact post-replacement session reconciliation and the two full-snapshot regressions (`scripts/ai/workflow_helper.py:5173-5176`, `scripts/ai/workflow_helper.py:5312-5321`, `scripts/ai/tests/test_workflow_helper.py:5904-5971`).

#### Important (Should Fix)

- None.

#### Minor (Nice to Have)

- The updated report says Issue #14 remains `in_progress`, while the committed Issue work log is `in_review` (`.superpowers/sdd/task-3-phase1b3-report.md:6`, `ai/work-logs/issue-14/README.md:5`). This is non-blocking status metadata drift.

### Assessment

- Task quality: Approved.
- Reasoning: Static re-review confirms the prior Critical is closed, rollback remains lock-bound and exact-session guarded, and publication remains irreversible. Only the non-blocking report/work-log status drift remains.

## Task 4 Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- The prior Important evidence TOCTOU issue is closed: the evidence path is opened once, the read is bounded to 65,536 bytes, and SHA-256, strict JSON parsing, and schema validation all consume the same captured bytes (`scripts/ai/workflow_helper.py:5870-5898`, `scripts/ai/workflow_helper.py:6006-6014`).
- Canonical evidence-schema mismatch still precedes evidence resolution, malformed and oversized evidence preserve fail-closed reasons, schema validation precedes digest mismatch, and external native leaves are rejected before referenced evidence lookup (`scripts/ai/workflow_helper.py:5932-5943`, `scripts/ai/workflow_helper.py:6001-6014`).
- The regression coverage exercises second-open replacement, malformed JSON, oversize rejection, schema-before-digest precedence, and native-forgery precedence (`scripts/ai/tests/test_workflow_helper.py:6681-6805`).

### Strengths

- The single-read regression substitutes replacement bytes on a hypothetical second open and asserts that the evidence path is opened exactly once (`scripts/ai/tests/test_workflow_helper.py:6681-6715`).
- The bounded reader rejects the 65,537th byte before decoding, while retaining the existing duplicate-key, non-finite-number, and malformed-JSON reason mapping (`scripts/ai/workflow_helper.py:5870-5898`).
- Hashing and validation remain ordered for safe error precedence while sharing the identical immutable byte snapshot (`scripts/ai/workflow_helper.py:6007-6014`).

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. The prior Important TOCTOU finding is closed.

#### Minor (Nice to Have)

- None.

### Assessment

- Task quality: Approved.
- Reasoning: The evidence reopen path has been removed, the bounded single-read implementation binds parsing, schema validation, and hashing to identical bytes, and the required reason precedence and native boundary remain intact. No findings remain.

## Task 5 Final Re-review (2026-07-14)

### Routing Outcome

- Owning feature: none. This is repo-wide Phase 2C/3A verification-gate infrastructure and a non-normative review-log update.

### Spec Compliance

- Verdict: Spec compliant.
- The prior Important verified-identity nullability finding is closed. The result schema now has mutually exclusive verified/all-string and synthesized/all-null identity shapes; missing or partially null verified identities satisfy neither branch (`ai/schemas/verification-gate-result.schema.json:43-93`).
- The prior Important accepted-leaf digest reopen finding is closed. Referenced leaf bytes and the parsed value are captured in one bounded open, passed through verification, and `leafResultSha256` is derived from those exact accepted bytes without reopening the path (`scripts/ai/workflow_helper.py:5919-5969`, `scripts/ai/workflow_helper.py:5979-6044`).
- The prior Important synthesized `mappedResult` finding is closed. The all-null schema branch excludes both raw and mapped `PASS`/`FAIL`, and the regression covers mapped-only PASS and FAIL mutations while raw `NOT_CONFIGURED` remains unchanged (`ai/schemas/verification-gate-result.schema.json:82-92`, `scripts/ai/tests/test_workflow_helper.py:6822-6836`).
- Required caller `NOT_APPLICABLE` remains canonical-policy-only, optional `FAIL` remains visible, missing required leaves fail closed, and aggregate precedence remains `FAIL` before `BLOCKED` (`scripts/ai/workflow_helper.py:6074-6103`, `scripts/ai/workflow_helper.py:7055-7074`).
- Internal native identity and repository-only `HOST_UNSUPPORTED` qualification remain preserved, as does external native-forgery precedence (`scripts/ai/workflow_helper.py:6790-6807`, `scripts/ai/workflow_helper.py:6976-6984`, `scripts/ai/workflow_helper.py:7083-7091`, `scripts/ai/tests/test_workflow_helper.py:7009-7032`).
- The implementation-agent binding is `verification-runner`, `failure-triage`, and `docs-sync`, with reusable references `ai/workflow-cache.json`, `ai/verification-policy.json`, and `ai/native-runtime-adapters.json`. `review-gate` belongs to the independent reviewer handoff; it is not missing from the implementation-agent dispatch (`ai/work-logs/issue-14/implementation-agent.md:31-39`, `ai/work-logs/issue-14/implementation-agent.md:525-528`).
- The implementation log records focused RED/GREEN evidence and a final Phase 2C/3A result of 111 passing tests. Per the review constraint, these commands were not independently rerun (`ai/work-logs/issue-14/implementation-agent.md:510-520`).

### Strengths

- The schema regression directly tests missing/null verified identity, a valid synthesized all-null record, and both mapped-only PASS/FAIL bypasses (`scripts/ai/tests/test_workflow_helper.py:6775-6850`).
- The replacement regression asserts exactly one leaf-path open and binds output identity to the first accepted byte sequence (`scripts/ai/tests/test_workflow_helper.py:6852-6899`).
- The focused Task 5 tests supply explicit PASS companions for unrelated required checks, isolating required-N/A and optional-FAIL behavior from missing evidence (`scripts/ai/tests/test_workflow_helper.py:6532-6562`, `scripts/ai/tests/test_workflow_helper.py:6713-6723`).

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. All three prior Important findings are closed.

#### Minor (Nice to Have)

- None.

### Assessment

- Task quality: Approved.
- Reasoning: Static final re-review confirms fail-closed aggregation, exclusive identity shapes, exact accepted-byte digest binding, mapped-only synthesized-result closure, native boundary preservation, and accurate role metadata. No findings remain.

## Task 6 Final Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- Verification-decision identity remains closed over task, gate, commit, classification, policy, exact producers, exact evidence, environment, and expiry.
- Canonical verification policy parsing, schema validation, hashing, and producer derivation use one bounded immutable read.
- Deterministic `STALE` findings override accumulated `UNCERTAIN` findings while retaining all diagnostics.
- Evidence open/read failures are guarded, recorded as `UNCERTAIN`, and do not prevent independent safe evidence or expiry checks; unsafe paths are not opened.
- The exact seven-skill catalog and handoff ID sets remain enforced structurally and semantically.

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. The policy TOCTOU, compound-classification precedence, and evidence read-time findings are closed.

#### Minor (Nice to Have)

- None. The terminal-newline SHA-256 schema finding is closed.

### Assessment

- Task quality: Approved.
- Reasoning: Final static re-review confirms that all policy snapshot, classification precedence, exact-end digest, and evidence read-time findings are closed. No issues remain for Task 6.

## Task 7 Final Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- Repository policy remains unable to declare supported hosts or promote repository-owned keys and probe facts.
- Public native CLI evaluation retains `host_trust=None` and exposes no descriptor, probe, ledger, policy, snapshot, or bypass trust-injection arguments.
- External host descriptor, probe, and ledger paths remain outside-repository, non-symlink, compiled-validation inputs.
- `HostNativeTrust` now recursively copies mappings into fresh read-only values and sequences into tuples during `__post_init__`, detaching direct and loader construction from caller-owned mutable aliases.
- Evaluator mapping and sequence access remains compatible with the deeply immutable trust value, and Python 3.9 annotation compatibility remains preserved.

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. The prior mutable descriptor/probe and nested-surface alias finding is closed.

#### Minor (Nice to Have)

- None.

### Assessment

- Task quality: Approved.
- Reasoning: Final static re-review confirms deep host-trust immutability, external authority ownership, canonical unsupported repository state, and public CLI isolation. No issues remain for Task 7.

## Task 8 Final Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- Durable replay identity remains closed over repository, producer, task, gate, attestation ID, nonce, and signed event-set digest.
- The production backend now pins an owner-only ledger directory handle, verifies type/device/inode/owner/mode identity, and creates only the digest basename with handle-relative `O_CREAT | O_EXCL | O_NOFOLLOW`.
- Publication writes with progress checks, fsyncs and closes the record, fsyncs the pinned directory entry, and blocks on any record or directory close/sync uncertainty.
- Failure cleanup closes the record, unlinks relative to the same pinned directory, and fsyncs the directory after removal.
- Unsupported Windows production backends fail closed without a pathname fallback; canonical public unsupported-host behavior remains unchanged.
- Real POSIX cross-process and directory-symlink tests are recorded as explicit Windows platform skips, while simultaneous contention, directory identity mismatch, durability, cleanup, and fault controls execute through focused primitive-level tests.

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. The prior directory durability and validation-to-open path-race findings are closed.

#### Minor (Nice to Have)

- None.

### Assessment

- Task quality: Approved.
- Reasoning: Final static re-review confirms pinned handle-relative publication, durable directory synchronization, fail-closed cleanup, precise replay mapping, and transparent platform-skip evidence. No issues remain for Task 8.

## Task 9 Final Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- `DETECTED` records require null original-detection binding fields, while `RESOLVED` records require non-null detection event, original gate invocation, and canonical detection digest bindings.
- Canonical detection hashing excludes only the five lifecycle resolution-binding fields specified by the task.
- Each current resolution must match exactly one earlier detection by event ID, task, original gate, deduplication key, digest, and strict observation ordering before signed resolution event IDs are compared.
- Unmatched detections remain unresolved, duplicate event delivery retains its idempotent/conflict contract, and durable replay, external host trust, public unsupported behavior, and documentation boundaries remain preserved.
- A full delivered-event pre-scan now gives current-gate detections deterministic `NATIVE_BYPASS_UNRESOLVED` precedence before per-group invalid-resolution evaluation, independent of deduplication-group insertion order.

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. The prior cross-group current-gate detection precedence finding is closed.

#### Minor (Nice to Have)

- None.

### Assessment

- Task quality: Approved.
- Reasoning: Final re-review confirms exact original-detection binding, canonical digest construction, deterministic lifecycle precedence, fail-closed signed-resolution ordering, and preserved native trust boundaries. No issues remain for Task 9.

## Task 10 Final Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- Repository-contract and native-enforcement identities remain separated in helper results, shell-wrapper fallbacks, and operator documentation.
- `taskKey` and `gateInvocationId` now share exact string, `1..128`, and identifier-regex validation aligned with the result schema.
- The 128-character boundary is accepted, while 129-character values are independently normalized to `"invalid"`, remain schema-valid, and do not leak the raw oversized input into the result.
- Wrapper forwarding and fallback output preserve the same correlation and identity contract without a new bypass.

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. The initial two findings covering mixed required-check identity and stale configured-check documentation were closed in `beb427a`.
- None. The follow-up correlation-length/schema-boundary finding was closed in `b646c22`.

#### Minor (Nice to Have)

- None.

### Verification

- Tests were not re-run during the final read-only re-review.
- Reviewed the committed evidence recording 142 passing Phase 2C/3A/3B tests and 2 pre-existing Windows platform skips.

### Assessment

- Task quality: Approved.
- Reasoning: Final static re-review confirms exact correlation validation, schema-valid invalid normalization without oversized raw-value leakage, wrapper consistency, and closure of the prior identity and documentation findings. No Critical, Important, or Minor issues remain for Task 10.

## Task 11 Final Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- The production/public CI evidence gate has no constructible-object PASS path and remains unconditionally `NOT_CONFIGURED` while external GitHub/Sigstore verification is absent.
- The lower pure verifier is not presented as production authority. Provenance and repository `retainedRun` independently bind every run, workflow, artifact, correlation, native, bypass, resolution, signer, and subject field to a separate immutable trusted current-run context.
- Production artifact-member reads require safe POSIX handle-relative `dir_fd` and `O_NOFOLLOW` pinning for every path component. Non-POSIX production hosts fail closed because the unsafe pathname fallback was removed.
- Exact member identity and digest semantics, non-null provenance identity for schema-valid PASS results, fail-closed result shapes, the Task 10 identity split, and the Task 12 scope boundary remain preserved.

### Issues

#### Critical (Must Fix)

- None. The initial forgeable `GitHubCiProvenance` authority and constructible-object production PASS finding was closed in `d8834f9` by removing the production PASS path.

#### Important (Should Fix)

- None. The prior attacker-controlled local expected-identity and old/unrelated-run replay finding was closed in `d8834f9` by independently comparing both claims with a separate trusted current-run context.
- None. The prior non-POSIX pathname fallback race finding was closed in `d8834f9` by requiring the pinned POSIX backend and failing closed when it is unavailable.

#### Minor (Nice to Have)

- None.

### Verification

- Tests were not re-run during the final read-only re-review.
- Reviewed the committed evidence recording 153 passing Phase 2C/3A/3B tests and 3 explicit platform-capability skips.

### Assessment

- Task quality: Approved.
- Reasoning: Final static re-review confirms closure of the external-authority, trusted-current-run, replay, and artifact-member TOCTOU findings. No Critical, Important, or Minor issues remain for Task 11.

## Task 12 Final Re-review (2026-07-14)

### Spec Compliance

- Verdict: Spec compliant.
- The contract entry script resolves the repository root and runs the exact full helper unittest module once before the runtime-preflight and command-runner shell suites under `set -eu`.
- The workflow provisions pinned dependencies and delegates regressions only to the complete entrypoint. Its exact job and six-step model preserves `pipefail`, failure diagnostics upload, and the repository-contract/native-enforcement distinction.
- Semantic validators compare the complete executable shell sequence and the closed workflow model rather than relying on substring counts. Comments and blank lines are excluded, while dead branches, duplicates, selective runners, malformed indentation, and duplicate or extra YAML authority are rejected.
- The workflow top level is closed over its exact name, `pull_request` plus `push` to `main`, `contents: read` permissions, and one `jobs` mapping. Unapproved `BASH_ENV`, concurrency, trigger, permission, or trailing top-level changes cannot satisfy the validator.

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. The initial substring-gameable semantic-test finding was closed in `9f064cb` by validating the exact executable entry sequence and indentation-aware workflow job/step model.
- None. The initial missing successful exact full-module evidence finding was closed by the committed post-fix single-process evidence.
- None. The follow-up unmodeled workflow top-level and `BASH_ENV` authority finding was closed in `fa9e415` by requiring the complete approved top-level sequence and rejecting every extra or trailing top-level block.

#### Minor (Nice to Have)

- None.

### Verification

- Tests were not re-run during the final read-only re-review.
- Reviewed the final post-`fa9e415` exact command evidence: exit `0`, 418 tests passed in `192.707s`, and 20 explicit platform-capability skips.

### Assessment

- Task quality: Approved.
- Reasoning: Final static re-review confirms complete shell and workflow execution modeling, closed workflow authority, correct failure propagation and diagnostics, and successful exact single-process coverage. No Critical, Important, or Minor issues remain for Task 12.

## Final Integration Review (2026-07-14)

### Review Scope

- Base: `26ba5e768c77139490abcb8fa66d2f696159c18b`
- Head: `ed7d2eaed25d145db24a9e51a38651f0c350eecb`
- Reviewed the complete base-to-head integration across Phase 1B-3 evidence/finalization, Phase 2 leaf/cache/aggregation trust, Phase 3A host trust/replay/resolution binding, Phase 3B contract/enforcement separation and GitHub provenance, schemas, public CLI reachability, documentation, tests, and work-log evidence.
- This was a read-only code and evidence review. Tests were not re-run. The recorded final evidence reviewed was the exact Python helper module command at exit `0`, 418 tests in `192.707s`, with 20 explicit platform-capability skips, plus recorded shell syntax, schema, diff, and artifact checks.

### Strengths

- Public native and CI CLIs fail closed: repository-controlled inputs cannot create supported-host or authenticated CI PASS.
- Repository-contract green is separated from native enforcement `NOT_CONFIGURED`; no unsupported registry `VERIFIED`, native-enforcement, Issue-closure, or unqualified overall `DONE` claim was found.
- Leaf/evidence bounded reads, exact correlation and digest checks, POSIX handle-relative artifact reads, and the external replay-ledger primitives provide strong defense-in-depth foundations.
- The recorded exact-suite evidence is specific and properly qualified. No generated `.ai-runs`, `__pycache__`, or temporary provenance artifact was present in the reviewed worktree, and the base-to-head diff check was clean.

### Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

1. `scripts/ai/workflow_helper.py:5033` - finalized-run verification covers only a subset of the claimed deterministic projection.
   - Why: `validate_final_run_projection()` checks run/task/result and selected references, but does not bind `startedAt`, `endedAt`, `workingDirectory`, `environment`, `redactionApplied`, `reason`, manifest `$id`/`runId`, or the complete claim/gate outcome. Because `run.json` is excluded from the manifest, schema-valid mutation of these fields can still return verification PASS. This contradicts `docs/superpowers/specs/2026-07-14-ai-workflow-trust-boundary-hardening-design.md:96-101`.
   - Fix: persist an immutable finalization projection/receipt or retained session snapshot containing every derived field, compare every `run.json` field and artifact identity against it, and add mutation coverage for each field and non-PASS manifest identity.

2. `scripts/ai/workflow_helper.py:7770` and `scripts/ai/workflow_helper.py:6248` - verification-policy semantics and policy digests come from separate reads.
   - Why: the gate parses policy, reopens it for the native policy digest, then reopens it again while verifying external leaves. A replacement race can bind policy-A semantics to policy-B digests and expose different policy identities across checks in one result.
   - Fix: bounded-read `verification-policy.json` once, parse and validate that byte buffer, derive one SHA-256 from it, pass both policy and digest through every native/external leaf path, and add a replacement-race regression asserting one read and one policy identity.

3. `scripts/ai/workflow_helper.py:5782` and `scripts/ai/workflow_helper.py:5848` - verification-decision cache identity is under-bound.
   - Why: expected producers are filtered to checks whose own `entryPoint` equals the current entrypoint, while `verification_gate()` aggregates all required and optional checks for the change type. A review cache can therefore be FRESH with only `review-gate`, omitting native, done-claim, static, and other inputs actually consumed. Evidence paths are also not associated with a producer, leaf digest, or evidence schema, so an arbitrary matching file can satisfy the evidence list.
   - Fix: either narrow gate aggregation to the same documented producer set or bind cache identity to every check actually consumed. Store producer-indexed leaf-result digest plus evidence reference, digest, and schema, and classify every missing, extra, or unmapped binding as STALE or UNCERTAIN.

4. `scripts/ai/workflow_helper.py:7166` and `scripts/ai/workflow_helper.py:7317` - the durable replay identity is consumed before full semantic validation.
   - Why: `consume_native_attestation()` runs after signature/callback checks but before confirming that every surface is ENFORCED, the current bypass count/set matches, and resolution IDs match. A mismatched invocation can permanently consume a valid attestation and cause the subsequent correct invocation to be rejected as replay.
   - Fix: consume the durable nonce only after enforcement, bypass-set, and resolution bindings all pass. Add tests proving every pre-consumption BLOCKED path leaves no ledger record while concurrent fully valid evaluations still yield one PASS and one replay rejection.

#### Minor (Nice to Have)

1. `scripts/ai/ci-evidence-gate.sh:38` and `scripts/ai/ci-evidence-gate.sh:63` - shell fallbacks report only 10 of the canonical 16 durable bindings.
   - Why: they omit workflow ref/SHA, event name, artifact ID/digest, and artifact members. The result schema accepts this under-bound list, so fallback output misstates the current contract even though it remains fail-closed.
   - Fix: emit the exact canonical binding list in both fallbacks and constrain the schemas to that exact set.

2. `ai/work-logs/issue-14/README.md:5` - the recovery summary is stale relative to committed final evidence and review logs.
   - Why: it still lists only the 120-test baseline, marks the reviewer log `in_progress`, and says final re-review is pending, while the role logs contain the final 418-test evidence and Task 12 final re-review.
   - Fix: synchronize metadata, current state, evidence summary, and next handoff while preserving `in_review` until these integration findings are resolved.

### Recommendations

- Add focused regressions for all four Important findings, then rerun the exact helper module and the recorded shell/schema/diff checks.
- Pin GitHub Actions to immutable commit SHAs and install Python dependencies from hash-locked artifacts; version assertions alone are not dependency provenance.
- Remaining risk, not a finding: external GitHub/Sigstore verification, branch protection, `phase-3b-native-enforcement`, remote-runner proof, and production host trust remain uninstalled. Canonical state correctly reports these as `NOT_CONFIGURED`.

### Assessment

- Ready to merge: With fixes.
- No Critical issue was found, but the four Important integration findings should be closed before merge.

## Task 13 Final Projection Integration Re-review (2026-07-14)

### Review History

- The initial integration review found the finalized `run.json` projection under-bound: schema-valid mutations could pass because the retained authority did not cover every derived run field, complete claim/gate outcomes, manifest identity, or artifact identities.
- Review loop 1: `9692fba` (`fix(ai): bind complete final run projection`) added the closed receipt projection and artifact identities. Re-review then found no public crash recovery and no complete pre-receipt session anchor.
- Review loop 2: `4035894` (`fix(ai): recover interrupted finalization safely`) added explicit recovery and the complete session snapshot anchor. Re-review found recovery still depended on mutable/current state, omitted the custom claim input, mishandled crash-left manifests and stale-lock history, and could leak runtime/write uncertainty.
- Review loop 3: `9a225e8` (`fix(ai): anchor finalization recovery journal`) added independent journal authority and bounded recovery. Re-review found that the active session did not bind the exact journal, OPEN-plus-active-journal work could proceed, prepare uncertainty was incomplete, and failed FINALIZED recovery did not consistently restore read-only control files.
- Review loop 4: `779c947` (`fix(ai): bind sessions to finalization journals`) bound the normalized journal identity into FINALIZING/FINALIZED sessions and closed structured uncertainty handling. Re-review found two remaining Important gaps: final JSON became visible before read-only sealing, and rollback restored OPEN before a fallible journal deletion/fsync cleanup.
- Review loop 5: `050ba82` (`fix(ai): seal final evidence before visibility`) made every final JSON temporary read-only and mode-verified before its exclusive link, repaired all six final/control modes during successful recovery, and replaced the fixed deletable marker with immutable per-attempt UUID journals. The OPEN compare-and-swap now clears only the active identity; prior journals remain read-only audit history, and legacy fixed markers fail closed.

### Final Issues

#### Critical (Must Fix)

- None.

#### Important (Should Fix)

- None. Both final-loop Important findings are closed by `050ba82`.

#### Minor (Nice to Have)

- None.

### Verification

- Tests were not re-run during this final read-only approval review.
- Reviewed evidence commit `110dd20`, which records five focused regressions passing in `9.660s` and the committed-HEAD bounded helper/schema suite passing 98 tests in `120.527s` with exit `0`.
- The recorded cache-free Python AST checks, touched-schema JSON parsing, and `git diff --check` also exited `0`. No Gradle, product, server, Docker, HTTP/API, database, migration, deployment, GitHub mutation, or real repository `.ai-runs` operation was run.

### Assessment

- Task quality: Approved.
- Ready to merge: Yes for the Task 13 final-projection/finalization integration scope.
- Reasoning: The five review loops close the complete projection authority, crash recovery, independent and session-bound journal identity, uncertainty reconciliation, pre-visibility immutability, recovery mode repair, and rollback cleanup-window findings. Final scoped review found Critical 0, Important 0, and Minor 0.

## Task 14 Verification Policy Snapshot Re-review (2026-07-14)

### Issues

- Critical: None.
- Important: None. `2b67cd7` closes the policy replacement-race finding by bounded-reading the canonical policy exactly once and deriving strict parsing, schema validation, applicability semantics, and SHA-256 identity from that one byte snapshot.
- Minor: None.

### Verification And Assessment

- Tests were not re-run during this read-only review. Reviewed evidence commit `99a15b3`, which records 133 passing Phase 2C/3A tests with 2 explicit Windows capability skips, plus successful focused snapshot/race regressions and static checks.
- The recursively frozen policy value and its one digest are passed unchanged to the native leaf and every external leaf verifier; validation reopens only the approved schema, and malformed or inconsistent state fails closed.
- Task quality: Approved. Final scoped review found Critical 0, Important 0, and Minor 0.

## Task 15 Cache Full-Consumer Binding Re-review (2026-07-14)

### Issues

- Critical: None.
- Important: None. `4cc8757` closes the native cache-authority gap by requiring the fixed current result/evidence references, schemas, and digests; copied or otherwise arbitrary paths are `STALE`, while an exact native binding remains explicitly `UNCERTAIN` and cannot become `FRESH` without a durable correlated native leaf envelope.
- Minor: None.

### Verification And Assessment

- Tests were not re-run during this final read-only approval review. Reviewed evidence commit `1e9c223`, which records 49 passing Phase 2A/2B/2C tests in `49.500s`, plus successful static checks.
- `STALE` retains precedence, and the external binding behavior remains unchanged and aligned with the documented schema.
- Task quality: Approved. Final scoped review found Critical 0, Important 0, and Minor 0.

## Task 16 Deferred Native Nonce Consumption Re-review (2026-07-14)

### Issues

- Critical: None.
- Important: None. `5e4afa1` defers durable nonce consumption until every surface is `ENFORCED` and the bypass count, bypass set, and resolution-event bindings have all passed.
- Minor: None.

### Verification And Assessment

- Tests were not re-run during this final read-only approval review. Reviewed evidence commit `2540d62`, which records the focused GREEN run passing 4 tests in `1.685s` and the Phase 3A class passing 110 tests in `31.951s` with 2 explicit Windows capability skips.
- All six semantic BLOCK paths precede ledger mutation; the same-nonce corrected retry and atomic one-PASS/one-replay concurrency behavior are covered. No new TOCTOU, authority, or ordering gap was found.
- Task quality: Approved. Final scoped review found Critical 0, Important 0, and Minor 0.
