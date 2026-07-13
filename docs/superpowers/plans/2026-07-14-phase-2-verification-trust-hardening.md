# Phase 2 Verification Trust Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prevent caller-authored verification PASS, fail-open aggregation, under-bound cache reuse, and duplicate or incomplete skill handoffs.

**Architecture:** Replace free-form leaf summaries with referenced, digest-bound leaf artifacts. Aggregate only verified leaves, include every decision input in cache identity, and add semantic exact-set validation for skills and handoffs.

**Tech Stack:** Python 3.9+, `unittest`, Draft 2020-12 JSON Schema, SHA-256.

## Global Constraints

- Product commands and real `.ai-runs` remain NOT RUN.
- A policy document or caller-provided enum cannot create PASS.
- Required `NOT_APPLICABLE` requires canonical applicability authority; optional FAIL remains FAIL.
- Cache PASS reuse fails closed on any missing, changed, expired, or unbound input.
- Phase 3A native leaf remains internal-only and is not accepted from leaf files.

## File Map

- Create `ai/schemas/verification-leaf-result.schema.json`: closed verified leaf artifact.
- Modify `ai/schemas/verification-gate-result.schema.json`: expose verified evidence identity.
- Modify `ai/schemas/verification-policy.schema.json` and `ai/verification-policy.json`: producer and applicability authority.
- Modify `ai/schemas/skill-catalog.schema.json` and `ai/schemas/agent-handoff.schema.json`: structural bounds.
- Modify `ai/schemas/workflow-cache.schema.json` and `ai/workflow-cache.json`: complete cache identity.
- Modify `scripts/ai/workflow_helper.py`: semantic verification, aggregation, cache, catalog, handoff.
- Modify `scripts/ai/tests/test_workflow_helper.py`: Phase 2 negative regressions.
- Modify `ai/verification-gates.md`, `ai/cache-policy.md`, `ai/skills/README.md`, and `ai/agent-handoff.md`: normative behavior.

---

### Task 1: Require Closed, Digest-Bound Leaf Artifacts

**Files:**
- Create: `ai/schemas/verification-leaf-result.schema.json`
- Modify: `scripts/ai/tests/test_workflow_helper.py:6203`
- Modify: `scripts/ai/workflow_helper.py:5610`
- Modify: `ai/schemas/verification-policy.schema.json`
- Modify: `ai/verification-policy.json`

**Interfaces:**
- Produces: `load_verified_leaf_results(root, refs_file, task_key, gate_invocation_id, commit_sha, policy) -> dict[str, dict]`
- Produces: `verified_leaf_result(root, reference, expected, policy_sha256) -> dict`
- Produces: `repository_commit_sha(root: Path) -> str`; production derives HEAD with `git rev-parse`, while tests patch this read-only probe to a fixed 40-hex value.
- Input file shape: `{ "leafResultRefs": ["repository/relative/result.json"] }`

- [ ] **Step 1: Add failing evidence-free and mismatch tests**

Add tests that write the legacy payload below and assert `INVALID_STATE` with `VERIFICATION_LEAF_RESULTS_INVALID`:

```python
{"results": [{"checkId": "review-gate", "result": "PASS", "evidenceRef": None, "reason": None}]}
```

Add a helper that writes a valid leaf and its evidence, then mutate one field at a time: `taskKey`, `gateInvocationId`, `commitSha`, `policySha256`, `producerId`, `evidence.sha256`, `producedAt`, and `expiresAt`. Each mismatch must fail before aggregation.

Patch `repository_commit_sha` to `0123456789abcdef0123456789abcdef01234567` in these temporary copied-repository tests. The public CLI does not accept a caller `--commit-sha`; it probes the checked-out repository HEAD.

- [ ] **Step 2: Run the new Phase 2C tests and confirm RED**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests -v
```

Expected: new tests FAIL because the baseline accepts `checkId` plus result enum without artifact validation.

- [ ] **Step 3: Add the closed leaf schema**

Create a Draft 2020-12 schema requiring exactly these fields:

```json
{
  "$schema": "ai/schemas/verification-leaf-result.schema.json",
  "$id": "ai/fixtures/phase-2c/review-gate.json",
  "schemaVersion": 1,
  "checkId": "review-gate",
  "result": "PASS",
  "taskKey": "issue-10",
  "gateInvocationId": "gate-review",
  "commitSha": "0123456789abcdef0123456789abcdef01234567",
  "policySha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "producerId": "review-gate",
  "producedAt": "2026-07-14T00:00:00Z",
  "expiresAt": "2026-07-14T00:05:00Z",
  "evidence": {
    "ref": "ai/fixtures/phase-2c/review-evidence.json",
    "schema": "ai/schemas/gateway-result.schema.json",
    "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"
  },
  "reason": null
}
```

Use closed enums for result and producer IDs, strict UTC timestamps, 40-lowercase-hex commit SHA, 64-lowercase-hex digests, and safe repository paths. PASS and FAIL require non-null evidence; other results may use null only when policy permits.

- [ ] **Step 4: Implement verified loading**

```python
def verified_leaf_result(root, reference, expected, policy_sha256):
    path = resolve_repository_file(root, reference)
    leaf = read_json(path)
    validate(root, leaf, "ai/schemas/verification-leaf-result.schema.json")
    if leaf["$id"] != Path(reference).as_posix():
        raise InvalidStateError([validation_error("VERIFICATION_LEAF_ID_MISMATCH")])
    for field in ("taskKey", "gateInvocationId", "commitSha"):
        if leaf[field] != expected[field]:
            raise InvalidStateError([validation_error("VERIFICATION_LEAF_CORRELATION_MISMATCH")])
    if leaf["policySha256"] != policy_sha256:
        raise InvalidStateError([validation_error("VERIFICATION_LEAF_POLICY_MISMATCH")])
    if leaf["producerId"] != expected["producerId"]:
        raise InvalidStateError([validation_error("VERIFICATION_LEAF_PRODUCER_MISMATCH")])
    produced = parse_rfc3339_timestamp(leaf["producedAt"])[0]
    expires = parse_rfc3339_timestamp(leaf["expiresAt"])[0]
    now = dt.datetime.now(dt.timezone.utc)
    if not produced <= now <= expires or expires - produced > dt.timedelta(minutes=5):
        raise InvalidStateError([validation_error("VERIFICATION_LEAF_STALE")])
    evidence = leaf["evidence"]
    evidence_path = resolve_repository_file(root, evidence["ref"])
    validate(root, read_json(evidence_path), evidence["schema"])
    if digest(evidence_path) != evidence["sha256"]:
        raise InvalidStateError([validation_error("VERIFICATION_LEAF_DIGEST_MISMATCH")])
    return leaf
```

Register the schema in `SCHEMA_NAMES`. Add `producerId` and a closed `notApplicableFor` array to each policy check. Reject the native adapter ID before loading external leaf refs.

Implement `repository_commit_sha` with `subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], shell=False, check=True, text=True, capture_output=True)` and strict 40-lowercase-hex validation. Missing or malformed Git state is `NOT_CONFIGURED`/BLOCKED for a required verification gate, never caller fallback.

- [ ] **Step 5: Run the mismatch matrix and confirm GREEN**

Expected: every mismatch returns exit 5; valid bound artifacts reach aggregation.

- [ ] **Step 6: Commit leaf verification**

```powershell
git add ai/schemas/verification-leaf-result.schema.json ai/schemas/verification-policy.schema.json ai/verification-policy.json scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): verify phase 2 leaf evidence"
```

### Task 2: Make Verification Aggregation Fail Closed

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py:6257`
- Modify: `scripts/ai/workflow_helper.py:5683-5730`
- Modify: `ai/schemas/verification-gate-result.schema.json`
- Modify: `ai/verification-gates.md`

**Interfaces:**
- Produces: `map_verification_leaf(raw_result: str, required: bool, policy_allows_na: bool) -> str`
- Produces: `aggregate_verification_gate(mapped_checks: list[dict]) -> str`

- [ ] **Step 1: Add failing required-N/A and optional-FAIL tests**

```python
def test_required_caller_not_applicable_is_blocked(self):
    ref = self.write_bound_leaf("review-gate", "NOT_APPLICABLE")
    result, status = self.run_gate_with_refs("documentation-only", "review", [ref])
    self.assertEqual((result["result"], status), ("BLOCKED", 2))

def test_optional_fail_remains_visible(self):
    ref = self.write_bound_leaf("verify.api-smoke", "FAIL")
    result, status = self.run_gate_with_refs("documentation-only", "verification-level", [ref])
    self.assertEqual((result["result"], status), ("FAIL", 1))
```

- [ ] **Step 2: Run both tests and confirm RED**

Expected: baseline maps required `NOT_APPLICABLE` to N/A and optional FAIL to N/A/PASS.

- [ ] **Step 3: Replace result mapping and remove static PASS defaults**

```python
def map_verification_leaf(raw_result, required, policy_allows_na):
    if raw_result == "FAIL":
        return "FAIL"
    if raw_result == "PASS":
        return "PASS"
    if raw_result == "NOT_APPLICABLE":
        return "NOT_APPLICABLE" if policy_allows_na else "BLOCKED"
    if raw_result in ("BLOCKED", "NOT_CONFIGURED"):
        return "BLOCKED" if required else "NOT_APPLICABLE"
    if raw_result == "SKIPPED_WITH_REASON":
        return "BLOCKED" if required else "SKIPPED_WITH_REASON"
    return "BLOCKED"

def aggregate_verification_gate(mapped_checks):
    results = [item["mappedResult"] for item in mapped_checks]
    if "FAIL" in results:
        return "FAIL"
    if "BLOCKED" in results or "NOT_CONFIGURED" in results:
        return "BLOCKED"
    return "PASS"
```

Change `default_leaf_result_for_check` so every missing non-native check is `NOT_CONFIGURED`; canonical policy is configuration evidence, not leaf PASS evidence. Compute `policy_allows_na` only from the selected change type and check's canonical `notApplicableFor` membership.

- [ ] **Step 4: Include verified identity in gate output**

Add `leafResultRef`, `leafResultSha256`, `producerId`, `commitSha`, and `policySha256` to each verified check in `verification-gate-result.schema.json`. Native leaf uses its internal evaluator result reference and canonical policy digest.

- [ ] **Step 5: Run all Phase 2C and Phase 3A integration tests**

Expected: Phase 2C tests PASS after converting existing explicit leaves to bound artifacts; internal native leaf tests remain PASS.

- [ ] **Step 6: Commit fail-closed aggregation**

```powershell
git add ai/schemas/verification-gate-result.schema.json ai/verification-gates.md scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): fail closed phase 2 aggregation"
```

### Task 3: Bind Cache Decisions And Enforce Exact Skill/Handoff Sets

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py:5891-6202`
- Modify: `scripts/ai/workflow_helper.py:5490`
- Modify: `ai/schemas/workflow-cache.schema.json`
- Modify: `ai/workflow-cache.json`
- Modify: `ai/schemas/skill-catalog.schema.json`
- Modify: `ai/schemas/agent-handoff.schema.json`
- Modify: `ai/cache-policy.md`
- Modify: `ai/skills/README.md`
- Modify: `ai/agent-handoff.md`

**Interfaces:**
- Produces: `cache_entry_identity(entry: dict) -> tuple`
- Produces: `validate_skill_catalog_semantics(catalog: dict) -> None`
- Produces: `validate_handoff_skill_set(handoff: dict, catalog: dict) -> None`

- [ ] **Step 1: Add failing stale-cache, duplicate-skill, and missing-skill tests**

For cache, mutate policy digest, evidence digest, commit, task key, gate ID, producer, change type, entry point, and expiry while leaving the existing path digest unchanged; assert STALE or UNCERTAIN. For skills, duplicate one allowed ID while preserving array length seven. For handoff, duplicate one ID so a different required skill is absent. Assert `INVALID_STATE`.

- [ ] **Step 2: Run Phase 2A and Phase 2B classes and confirm RED**

Expected: baseline reports cache FRESH and schemas accept duplicate/missing distinct IDs.

- [ ] **Step 3: Extend cache identity**

Require each verification cache key to contain:

```json
{
  "taskKey": "issue-10",
  "gateInvocationId": "gate-review",
  "commitSha": "0123456789abcdef0123456789abcdef01234567",
  "changeType": "documentation-only",
  "entryPoint": "review",
  "policySha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "producerIds": ["review-gate"],
  "evidence": [{"path": "ai/fixtures/evidence.json", "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}],
  "environmentFingerprint": null,
  "expiresAt": "2026-07-14T00:05:00Z"
}
```

`cache_invalidation_report` validates every field, file digest, producer set, and expiry. Missing mapping is UNCERTAIN; mismatch or expiry is STALE.

- [ ] **Step 4: Add semantic exact-set validation**

```python
REQUIRED_SKILL_IDS = {
    "repo-intake", "command-runner", "verification-runner",
    "api-smoke-verifier", "failure-triage", "docs-sync", "review-gate",
}

def validate_skill_catalog_semantics(catalog):
    ids = [skill["id"] for skill in catalog["skills"]]
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_SKILL_IDS:
        raise InvalidStateError([validation_error("SKILL_CATALOG_ID_SET_INVALID")])

def validate_handoff_skill_set(handoff, catalog):
    expected = {skill["id"] for skill in catalog["skills"]}
    actual = handoff["skillIds"]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise InvalidStateError([validation_error("HANDOFF_REQUIRED_SKILL_MISSING")])
```

Call these after schema validation in repo intake and Phase 2 handoff tests. Add `uniqueItems: true` to both schema arrays as defense in depth.

- [ ] **Step 5: Run Phase 2A, 2B, and 2C tests**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2AContextCacheTests scripts.ai.tests.test_workflow_helper.Phase2ARepoIntakeTests scripts.ai.tests.test_workflow_helper.Phase2BSkillsHandoffTests scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests -v
git diff --check
```

Expected: exit 0; no repository `.ai-runs` created.

- [ ] **Step 6: Commit cache and handoff integrity**

```powershell
git add ai/schemas/workflow-cache.schema.json ai/workflow-cache.json ai/schemas/skill-catalog.schema.json ai/schemas/agent-handoff.schema.json ai/cache-policy.md ai/skills/README.md ai/agent-handoff.md scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): bind phase 2 cache and handoff state"
```
