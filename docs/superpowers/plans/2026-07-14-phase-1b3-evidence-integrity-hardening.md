# Phase 1B-3 Evidence Integrity Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Phase 1B-3 finalization reject unbound, contradictory, stale, or tampered evidence and recover safely from pre-publication failures.

**Architecture:** Keep Phase 1B-3 integrity-only. Add explicit evidence-graph validation, deterministic final-run projection verification, and a recoverable finalization transaction around the existing OPEN/FINALIZING lifecycle.

**Tech Stack:** Python 3.9+, `unittest`, Draft 2020-12 JSON Schema, POSIX shell contracts.

## Global Constraints

- Do not run Gradle, product tests, servers, Docker, HTTP/API, databases, migrations, seeds, deploys, or infrastructure commands.
- Do not create real repository `.ai-runs`; tests use temporary copied repositories only.
- Preserve `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.
- Do not weaken existing assertions or change child failure/policy precedence to obtain green tests.
- Commit only this slice before starting Phase 2 hardening.

## File Map

- Modify `scripts/ai/tests/test_workflow_helper.py`: Phase 1B-3 negative and recovery regressions.
- Modify `scripts/ai/workflow_helper.py`: evidence graph, final projection, verification, rollback.
- Modify `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`: finalization recovery and cross-check contract.

---

### Task 1: Bind Every Check To Session Evidence And Reject Contradictory Not-Run Claims

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py:5541`
- Modify: `scripts/ai/workflow_helper.py:4790`

**Interfaces:**
- Consumes: `done_claim_semantic_result(root: Path, session: dict, claim: dict) -> tuple[str, str | None]`
- Produces: `validated_done_claim_evidence(root: Path, session: dict, claim: dict) -> dict[str, dict]`
- Produces: `validate_not_run_consistency(session: dict, claim: dict) -> None`

- [ ] **Step 1: Add failing evidence-binding and not-run tests**

Add these methods to `Phase1B3DoneClaimGateTests`:

```python
def test_check_evidence_must_be_top_level_and_bound_to_session(self):
    self.publish_command_result(exit_code=0)
    claim = self.done_claim()
    claim["checks"][0]["evidenceRefs"] = ["ai/verification-policy.json"]
    with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
        result, status = self.helper.prepare_done_claim(
            self.root, "run-1", self.write_claim(claim),
        )
    self.assertEqual((result["result"], status), ("INVALID_STATE", 5))
    self.assertEqual(result["reason"], "DONE_CLAIM_CHECK_EVIDENCE_UNBOUND")

def test_pass_check_cannot_also_be_declared_not_run(self):
    self.publish_command_result(exit_code=0)
    claim = self.done_claim()
    claim["notRunItems"] = [{"id": "verify.unit", "reason": "not executed"}]
    with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
        result, status = self.helper.prepare_done_claim(
            self.root, "run-1", self.write_claim(claim),
        )
    self.assertEqual((result["result"], status), ("INVALID_STATE", 5))
    self.assertEqual(result["reason"], "DONE_CLAIM_NOT_RUN_CONTRADICTION")
```

- [ ] **Step 2: Run the focused tests and confirm RED**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_check_evidence_must_be_top_level_and_bound_to_session scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_pass_check_cannot_also_be_declared_not_run -v
```

Expected: both tests FAIL because the baseline either accepts the claim or returns a later unrelated reason.

- [ ] **Step 3: Implement strict graph validation**

Add before `done_claim_semantic_result`:

```python
def validated_done_claim_evidence(root, session, claim):
    command_refs = set(session["commandResultRefs"])
    session_refs = command_refs | set(session["gateResultRefs"])
    top_level_refs = set(claim.get("evidenceRefs", []))
    check_refs = {
        reference
        for check in claim.get("checks", [])
        for reference in check.get("evidenceRefs", [])
    }
    resolved = {}
    for check in claim.get("checks", []):
        for reference in check.get("evidenceRefs", []):
            if reference not in top_level_refs or reference not in session_refs:
                raise InvalidStateError([validation_error(
                    "DONE_CLAIM_CHECK_EVIDENCE_UNBOUND",
                    message="check evidence must be present in the claim and active session",
                )])
            schema_path = (
                "ai/schemas/command-result.schema.json"
                if reference in command_refs
                else "ai/schemas/gateway-result.schema.json"
            )
            _path, artifact = read_run_reference(root, reference, schema_path)
            resolved[reference] = artifact
    if top_level_refs != check_refs or not command_refs.issubset(top_level_refs):
        raise InvalidStateError([validation_error(
            "DONE_CLAIM_EVIDENCE_CLOSURE_MISMATCH",
            message="top-level evidence must equal check evidence and include every command result",
        )])
    return resolved

def validate_not_run_consistency(session, claim):
    check_ids = {check["id"] for check in claim.get("checks", [])}
    command_ids = {
        reservation["commandId"] for reservation in session.get("reservations", [])
        if reservation.get("state") != "RESERVED"
    }
    not_run_ids = [item["id"] for item in claim.get("notRunItems", [])]
    if len(not_run_ids) != len(set(not_run_ids)):
        raise InvalidStateError([validation_error(
            "DONE_CLAIM_NOT_RUN_DUPLICATE", message="not-run IDs must be unique",
        )])
    if set(not_run_ids) & (check_ids | command_ids):
        raise InvalidStateError([validation_error(
            "DONE_CLAIM_NOT_RUN_CONTRADICTION",
            message="a claimed or executed check cannot also be not-run",
        )])
```

Call both helpers after run/task identity checks and before result aggregation. Use the resolved command results rather than reopening caller-selected paths in later loops.

- [ ] **Step 4: Run the Phase 1B-3 class and confirm GREEN**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v
```

Expected: PASS, including the two new tests and all prior precedence tests.

- [ ] **Step 5: Commit the evidence graph change**

```powershell
git add scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): bind phase 1b3 claim evidence"
```

### Task 2: Recompute And Verify The Final Run Projection

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py:5684`
- Modify: `scripts/ai/workflow_helper.py:4937-5090`

**Interfaces:**
- Consumes: final `done-claim.json`, pre-done gate result, manifest, and `run.json`
- Produces: `validate_final_run_projection(run_index: dict, claim: dict, gate: dict, manifest: dict) -> None`

- [ ] **Step 1: Add failing tampered-run and stale-projection tests**

```python
def test_verify_finalized_rejects_tampered_run_json(self):
    self.publish_command_result(exit_code=0)
    with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
        result, status = self.helper.prepare_done_claim(
            self.root, "run-1", self.write_claim(self.done_claim()),
        )
    self.assertEqual((result["result"], status), ("PASS", 0))
    path = self.root / ".ai-runs" / "run-1" / "run.json"
    path.chmod(0o600)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["taskKey"] = "other-task"
    path.write_text(json.dumps(payload), encoding="utf-8")
    verified, verify_status = self.helper.verify_finalized_run(self.root, "run-1")
    self.assertEqual((verified["result"], verify_status), ("INVALID_STATE", 5))
    self.assertEqual(verified["reason"], "FINAL_RUN_PROJECTION_MISMATCH")
```

Add `test_verify_finalized_rejects_stale_run_result` with the same setup, mutate `run.json.result` from `PASS` to `BLOCKED`, and assert `INVALID_STATE`, exit 5, and `FINAL_RUN_PROJECTION_MISMATCH`.

- [ ] **Step 2: Run the new projection tests and confirm RED**

Run:

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_verify_finalized_rejects_tampered_run_json scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests.test_verify_finalized_rejects_stale_run_result -v
```

Expected: FAIL because baseline `verify_finalized_run` excludes `run.json` from the manifest and does not cross-check it.

- [ ] **Step 3: Implement deterministic projection validation**

```python
def validate_final_run_projection(run_index, claim, gate, manifest):
    expected_evidence = [
        f".ai-runs/{run_index['runId']}/done-claim.json",
        f".ai-runs/{run_index['runId']}/artifact-manifest.json",
        f".ai-runs/{run_index['runId']}/gate-results/pre-done-claim.json",
    ]
    mismatched = (
        run_index["runId"] != claim["runId"]
        or run_index["taskKey"] != claim["taskKey"]
        or run_index["result"] != final_run_result_for(gate["result"])
        or run_index["evidenceRefs"] != expected_evidence
        or gate.get("data") is not None and gate["data"]["manifestRef"] != manifest["$id"]
    )
    if mismatched:
        raise InvalidStateError([validation_error(
            "FINAL_RUN_PROJECTION_MISMATCH",
            message="run.json does not match claim, gate, and manifest",
        )])
```

In `verify_finalized_run`, load the done claim and gate result through their schemas, validate manifest closure, then call this helper before returning PASS. Also compare `commandResultRefs`, `approvalRefs`, and `policyViolationRefs` to the manifest kinds.

- [ ] **Step 4: Run projection and full Phase 1B-3 tests**

Expected: all Phase 1B-3 tests PASS; tampering remains read-only and returns exit 5.

- [ ] **Step 5: Commit final projection verification**

```powershell
git add scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): verify finalized run projection"
```

### Task 3: Roll Back Failed Finalization Safely

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py:5738`
- Modify: `scripts/ai/workflow_helper.py:5090-5140`
- Modify: `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md`

**Interfaces:**
- Produces: `rollback_finalization(root: Path, original_session: dict, final_refs: Sequence[str]) -> None`
- Preserves: published `run.json` is never rolled back.

- [ ] **Step 1: Add failing validation and I/O rollback tests**

Patch `publish_done_gate_manifest_run` once to raise `InvalidStateError` and once to raise `OSError` before `run.json` publication. Assert exit 5, restored session state `OPEN`, absence of `run.json`, manifest, done claim, and pre-done gate result, and ability to retry successfully.

- [ ] **Step 2: Run rollback tests and confirm RED**

Expected: FAIL because the baseline leaves `.state/run-session.json` in `FINALIZING`.

- [ ] **Step 3: Implement bounded rollback**

```python
def rollback_finalization(root, original_session, final_refs, acquired):
    root = Path(root).resolve(strict=True)
    run = root / ".ai-runs" / original_session["runId"]
    if (run / "run.json").exists():
        raise RegistryBlockedError([validation_error(
            "FINALIZATION_ALREADY_PUBLISHED",
            message="published run.json cannot be rolled back",
        )])
    for reference in final_refs:
        path = root / reference
        if path.exists():
            path.chmod(0o600)
            path.unlink()
    replace_run_session(
        root,
        run / ".state" / "run-session.json",
        original_session,
        acquired,
        expected_state="FINALIZING",
    )
```

Capture the exact OPEN session before transition. On any validation/publication exception before `run.json` exists, invoke rollback with the same validated `acquired` lock owner and require the current session state to be FINALIZING. Never add an unlocked rollback bypass. If rollback itself fails, return `BLOCKED` with `FINALIZATION_RECOVERY_REQUIRED` and preserve the FINALIZING state for explicit recovery.

- [ ] **Step 4: Run rollback, precedence, and stale-summary tests**

Expected: PASS; both injected failures restore OPEN or return the explicit recovery-required result without false finalization.

- [ ] **Step 5: Update the Phase 1B specification**

Document check-level evidence closure, not-run contradiction handling, final projection verification, and the exact rollback/recovery boundary. Preserve integrity-only wording.

- [ ] **Step 6: Run slice verification**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase1B3DoneClaimGateTests -v
git diff --check
```

Expected: exit 0 for both commands and no `.ai-runs` under the repository root.

- [ ] **Step 7: Commit the recovery contract**

```powershell
git add scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py docs/superpowers/specs/2026-07-10-ai-workflow-phase-1b-spec.md
git commit -m "fix(ai): recover failed phase 1b3 finalization"
```
