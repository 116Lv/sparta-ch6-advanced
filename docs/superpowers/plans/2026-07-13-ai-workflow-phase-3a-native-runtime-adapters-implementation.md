# AI Workflow Phase 3A Native Runtime Adapters Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add machine-readable native adapter capability and bypass-attempt contracts, current-host `UNSUPPORTED` evaluation, and completion-blocking integration without product-command execution.

**Architecture:** Repository JSON declares supported hosts and baseline capability policy but cannot self-promote runtime enforcement. A static Python helper validates policy, evaluates ephemeral runtime snapshots and bypass-attempt fixtures, and emits a Phase 2C-compatible leaf result. The supported-host registry is empty in Phase 3A, so the current Codex desktop host is explicitly `UNSUPPORTED`; no runtime snapshot can become trusted evidence.

**Tech Stack:** Markdown, JSON Schema Draft 2020-12, Python 3 with `jsonschema`, Bash thin wrappers, Python `unittest`, temporary fixtures.

## Global Constraints

- Preserve every approved Phase 1A through Phase 2C decision.
- Phase 1B-3 remains `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`.
- `scripts/ai/command-runner.sh` remains the only supported product-command path.
- Phase 3A has no supported host-native adapter and no minimum supported host version.
- Current Codex desktop command, file-read, search, and tool-call surfaces are `UNSUPPORTED`.
- Do not execute Gradle, build, product/unit project tests, application server, Docker Compose, HTTP/curl/API, database, migration, seed, deployment, or infrastructure commands.
- Do not create repository `.ai-runs`, non-fixture `artifact-manifest.json`, or finalized non-fixture `run.json`.
- Do not promote any command registry entry to `VERIFIED`, close Issue #10 automatically, or claim unqualified overall `DONE`.
- Phase 3B owns CI installation, remote runner guarantees, durable CI evidence, cross-host parity, and CI retention/attestation.

---

## File Structure

- Create `ai/native-runtime-adapters.json`: repository-authored supported-host registry and current-host baseline.
- Create `ai/schemas/native-runtime-adapters.schema.json`: closed adapter policy schema.
- Create `ai/schemas/native-bypass-attempt.schema.json`: closed redacted bypass record schema.
- Create `ai/schemas/native-adapter-result.schema.json`: closed helper result and Phase 2C leaf contract.
- Create `ai/native-runtime-adapters.md`: human-readable discovery, status, redaction, and boundary policy.
- Create `scripts/ai/native-adapter-gate.sh`: static thin wrapper.
- Modify `scripts/ai/workflow_helper.py`: schema allowlist, adapter evaluation, bypass validation, and CLI.
- Modify `scripts/ai/tests/test_workflow_helper.py`: Phase 3A focused contract and temp-fixture tests.
- Modify `ai/verification-policy.json` and its schema: add `native-runtime-adapter` to every change type.
- Modify routing, cache, tool-call, handoff, verification, and command-runner documents to expose the boundary.
- Create `ai/work-logs/issue-10/*` and modify `ai/work-logs/index.md`: durable plan, implementation, and review record.

### Task 1: Work Log And Closed Schemas

**Files:**
- Create: `ai/work-logs/issue-10/README.md`
- Create: `ai/work-logs/issue-10/plan-reviewer.md`
- Create: `ai/work-logs/issue-10/implementation-agent.md`
- Create: `ai/work-logs/issue-10/reviewer.md`
- Create: `ai/schemas/native-runtime-adapters.schema.json`
- Create: `ai/schemas/native-bypass-attempt.schema.json`
- Create: `ai/schemas/native-adapter-result.schema.json`
- Modify: `ai/work-logs/index.md`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces schema names `native-runtime-adapters`, `native-bypass-attempt`, and `native-adapter-result`.
- Produces Issue #10 work-log state without Issue closure.

- [ ] **Step 1: Write failing schema and work-log tests**

```python
class Phase3ANativeRuntimeAdapterTests(unittest.TestCase):
    def test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed(self):
        helper = load_helper()
        self.assertIn("native-runtime-adapters", helper.SCHEMA_NAMES)
        self.assertIn("native-bypass-attempt", helper.SCHEMA_NAMES)
        self.assertIn("native-adapter-result", helper.SCHEMA_NAMES)
        summary = (REPOSITORY_ROOT / "ai/work-logs/issue-10/README.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/116Lv/sparta-ch6-advanced/issues/10", summary)
```

- [ ] **Step 2: Run the focused RED test**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v`
Expected: FAIL because schemas and work logs do not exist.

- [ ] **Step 3: Add closed schemas, schema allowlist entries, and work logs**

The adapter policy schema must allow complete supported-host declarations with minimum version, producer identifier, pinned Ed25519 key fingerprint, and four closed surfaces; the canonical Phase 3A instance alone has an empty `supportedHosts` array. It must also require current host identity, four closed surfaces, and `UNSUPPORTED` statuses. The bypass schema must require correlation, lifecycle, decision, bounded redacted summaries, and forbid secret-bearing raw fields. The result schema must expose adapter result `PASS|FAIL|BLOCKED|NOT_CONFIGURED|UNSUPPORTED` and Phase 2C leaf result `PASS|FAIL|BLOCKED|NOT_CONFIGURED|NOT_APPLICABLE`.

Add positive and negative schema vectors in the test body: validate one supported-host policy fixture; reject unknown properties, invalid enums, oversized summaries, raw `environment`/`payload`/`query`/`argv` fields, inconsistent `RESOLVED` timestamps, and missing correlation fields.

- [ ] **Step 4: Run the focused GREEN test and commit**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed -v`
Expected: PASS.

Commit: `git commit -m "feat: add phase 3a native adapter contracts (#10)"`

### Task 2: Canonical Policy And Current-Host Discovery

**Files:**
- Create: `ai/native-runtime-adapters.json`
- Create: `ai/native-runtime-adapters.md`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces schema-valid `ai/native-runtime-adapters.json` with `supportedHosts: []`.
- Produces current-host surface map: `COMMAND`, `FILE_READ`, `SEARCH`, `TOOL_CALL` all `UNSUPPORTED`.

- [ ] **Step 1: Write a failing policy test**

```python
def test_current_host_is_explicitly_unsupported_on_all_native_surfaces(self):
    policy = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/native-runtime-adapters.json")
    self.assertEqual(policy["supportedHosts"], [])
    self.assertEqual(policy["currentHost"]["hostId"], "codex-desktop")
    self.assertEqual({s["status"] for s in policy["currentHost"]["surfaces"]}, {"UNSUPPORTED"})
```

- [ ] **Step 2: Run RED, create policy/docs, run GREEN, and commit**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests.test_current_host_is_explicitly_unsupported_on_all_native_surfaces -v`
Expected before implementation: FAIL; after implementation: PASS.

Commit: `git commit -m "docs: declare current native adapter support state (#10)"`

### Task 3: Static Adapter Gate And Bypass Evaluation

**Files:**
- Create: `scripts/ai/native-adapter-gate.sh`
- Modify: `scripts/ai/workflow_helper.py`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Produces `native_adapter_gate(root, task_key, gate_invocation_id, runtime_snapshot_ref=None, bypass_attempts_ref=None, policy_ref="ai/native-runtime-adapters.json")` so temporary fixtures can exercise supported-host paths.
- Produces CLI `native-adapter-gate --repository-root --task-key --gate-invocation-id [--runtime-snapshot] [--bypass-attempts] --output`.
- Returns current host `UNSUPPORTED` and Phase 2C leaf `NOT_APPLICABLE` without creating `.ai-runs`.

- [ ] **Step 1: Write failing evaluator tests**

```python
def test_unsupported_host_maps_to_explicit_not_applicable_leaf(self):
    result, status = self.helper.native_adapter_gate(self.root, "issue-10", "gate-1")
    self.assertEqual((result["result"], status), ("UNSUPPORTED", 6))
    self.assertEqual(result["data"]["phase2CLeafResult"], "NOT_APPLICABLE")
    self.assertFalse((self.root / ".ai-runs").exists())

def test_repository_authored_or_unsigned_snapshot_cannot_self_promote(self):
    snapshot = self.write_temp_snapshot({"producerId": "fixture", "surfaces": []})
    result, status = self.helper.native_adapter_gate(self.root, "issue-10", "gate-2", snapshot)
    self.assertEqual((result["result"], status), ("UNSUPPORTED", 6))

def test_unresolved_bypass_and_redaction_uncertainty_block_completion(self):
    attempts = self.write_attempts([self.valid_attempt(lifecycle="DETECTED")])
    result, status = self.helper.native_adapter_gate(self.root, "issue-10", "gate-3", bypass_attempts_ref=attempts)
    self.assertEqual((result["result"], status), ("BLOCKED", 2))
```

- [ ] **Step 2: Run focused RED tests**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
Expected: FAIL because evaluator and wrapper do not exist.

- [ ] **Step 3: Implement minimal read-only evaluation**

Validate the canonical policy first. Reject repository-authored runtime snapshots as untrusted. Because canonical `supportedHosts` is empty, return `UNSUPPORTED` before any signature promotion path. With temporary supported-host policy fixtures, prove `NOT_CONFIGURED`, stale, bad signature metadata, callback failure, and `AUDIT_ONLY` are completion-blocking; fixture `ENFORCED` is contract-only and cannot become real trusted evidence.

Validate bypass-attempt fixtures against the closed schema. Add focused tests for mismatched `taskKey`, mismatched `gateInvocationId`, malformed records, redaction uncertainty, raw secret fields, summary byte/scalar bounds, repeated `eventId` idempotency, semantic `deduplicationKey` grouping without event deletion, `DETECTED`/`RESOLVED` transitions, unresolved completion blocking, and command-based file/search intent retaining `surface: COMMAND`. Do not execute or spawn any command.

- [ ] **Step 4: Add the fixed-argument shell wrapper, run GREEN, and commit**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
Expected: PASS.

Commit: `git commit -m "feat: evaluate native adapter enforcement state (#10)"`

### Task 4: Phase 2C And Repository Boundary Integration

**Files:**
- Modify: `ai/schemas/verification-policy.schema.json`
- Modify: `ai/verification-policy.json`
- Modify: `ai/verification-gates.md`
- Modify: `ai/cache-policy.md`
- Modify: `ai/tool-call-policy.md`
- Modify: `ai/agent-handoff.json`
- Modify: `ai/agent-handoff.md`
- Modify: `AGENTS.md`
- Modify: `ai/document-routing.md`
- Modify: `scripts/ai/tests/test_workflow_helper.py`

**Interfaces:**
- Adds `native-runtime-adapter` to every change type's required checks.
- Maps adapter `UNSUPPORTED` to leaf `NOT_APPLICABLE`; supported-host faults remain `BLOCKED`.
- Preserves `command-runner.sh` as the only product-command path.
- Extends `verification_gate(root, change_type, entry_point, leaf_results_ref=None, task_key=None, gate_invocation_id=None, runtime_snapshot_ref=None, bypass_attempts_ref=None)`.
- Adds `native_adapter_phase2c_leaf(root, task_key, gate_invocation_id, runtime_snapshot_ref=None, bypass_attempts_ref=None)` which invokes `native_adapter_gate()` in-process against the same canonical policy and returns the exact leaf object consumed by Phase 2C. No intermediate adapter-result file is accepted as gate input.

- [ ] **Step 1: Write failing integration tests**

```python
def test_native_adapter_leaf_is_required_for_every_change_type(self):
    policy = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/verification-policy.json")
    for change in policy["changeTypes"]:
        self.assertIn("native-runtime-adapter", change["requiredChecks"])

def test_every_change_type_aggregates_explicit_native_adapter_state(self):
    for change_type in self.CHANGE_TYPES:
        result, _ = self.helper.verification_gate(self.root, change_type, "verification-level", task_key="issue-10", gate_invocation_id="gate-u")
        self.assertEqual(self.native_check(result)["mappedResult"], "NOT_APPLICABLE")
        blocked_result, _ = self.helper.verification_gate(self.supported_root, change_type, "verification-level", task_key="issue-10", gate_invocation_id="gate-b")
        self.assertEqual(blocked_result["result"], "BLOCKED")

def test_repository_and_native_boundaries_are_documented(self):
    text = "\n".join(self.read_repository_text(p) for p in self.PHASE_3A_POLICY_DOCS)
    self.assertIn("only supported product-command path", text)
    self.assertIn("UNSUPPORTED", text)
    self.assertIn("Phase 3B", text)
```

- [ ] **Step 2: Run RED, integrate policy/docs/handoff, run GREEN, and commit**

Run: `python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v`
Expected before integration: FAIL; after integration: PASS.

Reserve `native-runtime-adapter` as an internal-only check ID. `load_verification_leaf_results()` must reject any external leaf-results entry with that ID as `INVALID_STATE/NATIVE_ADAPTER_LEAF_FORGED`. In the verification check loop, branch on this ID before any `leaf_results.get(...)` call and always invoke `native_adapter_phase2c_leaf()` with the current gate correlation. It must never use the existing static `registryCommandId: null` automatic PASS. If current host is absent from canonical `supportedHosts`, produce `NOT_APPLICABLE` with reason `HOST_UNSUPPORTED`; if present without authenticated enforcement, produce `NOT_CONFIGURED` or `BLOCKED`. The verification CLI accepts correlation plus optional runtime snapshot and bypass-attempt references and passes them directly to the in-process evaluator; it never accepts a precomputed adapter result.

Add negative integration tests that inject `{"checkId":"native-runtime-adapter","result":"PASS"}` through the ordinary leaf-results file for both canonical unsupported-host policy and a supported-host fixture; both must return `INVALID_STATE` with `NATIVE_ADAPTER_LEAF_FORGED`. Also test a repository-authored fake adapter result, correlation mismatch, policy digest mismatch, and a fixture `PASS` while canonical `supportedHosts` is empty. No CLI option may load those results, and direct helper misuse must return `BLOCKED` or canonical `NOT_APPLICABLE`, never `PASS`.

Commit: `git commit -m "docs: connect native adapters to workflow gates (#10)"`

### Task 5: Allowed Verification And Independent Review

**Files:**
- Modify: `ai/work-logs/issue-10/README.md`
- Modify: `ai/work-logs/issue-10/implementation-agent.md`
- Modify: `ai/work-logs/issue-10/reviewer.md`

**Interfaces:**
- Produces Phase 3A qualified PASS/FAIL evidence without native enforcement PASS.

- [ ] **Step 1: Run allowed verification**

```text
python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v
python -m unittest scripts.ai.tests.test_workflow_helper.Phase2CVerificationGateTests scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v
python -m unittest scripts.ai.tests.test_workflow_helper -v
bash scripts/ai/run-helper-tests.sh
bash scripts/ai/tests/run-contract-tests.sh
bash scripts/ai/runtime-preflight.sh
bash scripts/ai/repo-intake.sh --output -
bash scripts/ai/native-adapter-gate.sh --task-key issue-10 --gate-invocation-id final-static --output -
git diff --check
```

Expected: helper/static contracts PASS; native adapter gate reports `UNSUPPORTED` with Phase 2C leaf `NOT_APPLICABLE`; `runtime-preflight.sh` runs without `--record`; product commands remain NOT RUN. Record `git status --short` before and after the allowed commands and assert no runtime-generated repository files appear.

- [ ] **Step 2: Verify prohibited artifacts remain absent**

Check repository `.ai-runs`, non-fixture `artifact-manifest.json`, and non-fixture finalized `run.json`; expect all absent. Run `git diff --exit-code origin/main -- ai/command-registry.json` and require exit 0, proving Phase 3A neither changes command configuration status nor adds a new `VERIFIED` promotion.

- [ ] **Step 3: Obtain independent final review and record the result**

The reviewer checks the full diff, test evidence, host support claims, redaction, completion mapping, repository boundary, and Phase 3B deferral. Fix every Critical/Important finding and rerun affected checks.

- [ ] **Step 4: Commit final work-log evidence**

Commit: `git commit -m "docs: record phase 3a verification and review (#10)"`

## Self-Review

- Spec coverage: Tasks cover host support/version decision, discovery provenance, four hooks, statuses, bypass lifecycle/redaction, fail-closed/completion behavior, repository boundary, Phase 2C integration, and Phase 3B handoff.
- Placeholder scan: No implementation placeholder is used.
- Type consistency: `native-runtime-adapter`, `native-adapter-gate`, `UNSUPPORTED`, and `NOT_APPLICABLE` are consistent across schemas, helper, shell, tests, and policy.
