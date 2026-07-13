# Phase 3A Native Trust Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ensure repository policy, repository fixtures, temporary keys, process memory, or unrelated resolutions cannot create production native enforcement PASS.

**Architecture:** Canonical repository state remains unsupported baseline only. A future supported-host evaluation requires a non-CLI host-owned trust context outside the repository, including authoritative probe, trust anchor, and durable replay ledger; the public repository CLI cannot inject this authority.

**Tech Stack:** Python 3.9+, `unittest`, Draft 2020-12 JSON Schema, Ed25519 verification, atomic filesystem operations.

## Global Constraints

- Current Codex Desktop stays `hostVersion: null`, `UNPROBED`, and `UNSUPPORTED`.
- Canonical repository policy cannot contain a production trusted signing key or supported-host promotion.
- Repository fixture paths and temporary keys are test inputs only and cannot reach public CLI PASS.
- A process-local replay set is defense in depth only, never the authoritative replay decision.
- Product commands and real native operations remain NOT RUN.

## File Map

- Create `ai/schemas/host-native-trust.schema.json`: host-owned trust/probe descriptor contract used only by the internal evaluator boundary.
- Modify `ai/schemas/native-runtime-adapters.schema.json`: canonical `supportedHosts` is empty baseline only.
- Modify `ai/schemas/native-bypass-attempt.schema.json`: bind resolutions to original detections.
- Modify `scripts/ai/workflow_helper.py`: host trust context, durable replay ledger, detection binding.
- Modify `scripts/ai/tests/test_workflow_helper.py`: repository-key, forged-probe, cross-process replay, unrelated-resolution regressions.
- Modify `scripts/ai/tests/native-adapter-gate.sh`: public CLI remains unsupported without host context.
- Modify `ai/native-runtime-adapters.md`, `ai/verification-gates.md`, and Phase 3A design: corrected boundary.

---

### Task 1: Remove Repository-Controlled Production Trust Promotion

**Files:**
- Create: `ai/schemas/host-native-trust.schema.json`
- Modify: `ai/schemas/native-runtime-adapters.schema.json`
- Modify: `scripts/ai/tests/test_workflow_helper.py:6493`
- Modify: `scripts/ai/workflow_helper.py:5842-6170`

**Interfaces:**
- Produces: `HostNativeTrust` immutable value with `descriptor`, `probe`, and `ledger_root`.
- Produces: `load_host_native_trust(repository_root, descriptor_path, probe_path, ledger_root) -> HostNativeTrust`
- Changes: `native_adapter_gate(root, task_key, gate_invocation_id, runtime_snapshot_ref=None, bypass_attempts_ref=None, policy_ref="ai/native-runtime-adapters.json", host_trust: HostNativeTrust | None = None)`

- [ ] **Step 1: Add failing repository-key and forged-probe tests**

Add tests proving that a modified repository `native-runtime-adapters.json` with a supported host and temporary key cannot make `run_native_adapter_gate_cli` PASS. Add a repository fixture claiming `PROBED` version and assert `HOST_UNSUPPORTED`. Add a valid external host context test for the lower-level evaluator only.

- [ ] **Step 2: Run focused tests and confirm RED**

Expected: baseline accepts repository fixture policy plus temporary signed snapshot on the supported path.

- [ ] **Step 3: Make canonical policy baseline-only**

In `native-runtime-adapters.schema.json`, constrain canonical `supportedHosts` to an empty array. Keep current host surfaces exactly four `UNSUPPORTED` entries. Reject a non-empty canonical list during semantic validation even if a copied schema is weakened.

- [ ] **Step 4: Add the external host trust descriptor**

Use this closed shape:

```json
{
  "$schema": "ai/schemas/host-native-trust.schema.json",
  "schemaVersion": 1,
  "producerId": "codex-host-runtime",
  "hostId": "supported-host",
  "minimumHostVersion": "1.0.0",
  "adapterVersionRange": ">=1.0.0 <2.0.0",
  "ed25519PublicKeyFingerprint": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "surfaces": ["COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL"]
}
```

The authoritative probe separately contains `hostId`, `hostVersion`, `versionProvenance: PROBED`, `producerId`, and `observedAt`. `load_host_native_trust` requires descriptor, probe, and ledger paths to resolve outside the repository root, rejects symlinks, validates both documents, and requires matching producer/host identity.

Repeat the critical closed-key, identifier, SemVer, four-surface exact-set, producer/host match, key-fingerprint, and `PROBED` checks in Python semantic validation. The repository-owned schema is defense in depth and cannot loosen the compiled trust checks.

- [ ] **Step 5: Gate supported evaluation on explicit host context**

```python
@dataclasses.dataclass(frozen=True)
class HostNativeTrust:
    descriptor: dict
    probe: dict
    ledger_root: Path

def native_adapter_supported_host(policy, host_trust=None):
    if host_trust is None:
        return None
    probe = host_trust.probe
    descriptor = host_trust.descriptor
    if probe["versionProvenance"] != "PROBED":
        return None
    if probe["hostId"] != descriptor["hostId"]:
        return None
    if native_semver_key(probe["hostVersion"]) < native_semver_key(descriptor["minimumHostVersion"]):
        return None
    return descriptor
```

`run_native_adapter_gate_cli` never accepts descriptor, probe, ledger, policy override, or test fixture arguments and always calls with `host_trust=None`. Tests may call the lower-level evaluator with a `HostNativeTrust` constructed from temporary paths outside the copied repository.

- [ ] **Step 6: Run current-host, forged-probe, and signed-snapshot tests**

Expected: public CLI remains UNSUPPORTED; repository key/probe fixtures cannot promote; lower-level external host context can verify a valid signature.

- [ ] **Step 7: Commit the authority split**

```powershell
git add ai/schemas/host-native-trust.schema.json ai/schemas/native-runtime-adapters.schema.json scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): move native trust outside repository"
```

### Task 2: Persist One-Use Attestation Consumption Across Processes

**Files:**
- Modify: `scripts/ai/tests/test_workflow_helper.py:7262`
- Modify: `scripts/ai/workflow_helper.py:6085`

**Interfaces:**
- Produces: `consume_native_attestation(ledger_root: Path, identity: dict) -> None`
- Ledger identity binds repository digest, producer, task, gate, attestation ID, nonce, and event-set SHA-256.

- [ ] **Step 1: Add a failing cross-process replay test**

Use two independent Python processes against the same temporary external ledger directory. The first valid signed attestation returns PASS; the second returns BLOCKED with `NATIVE_ADAPTER_CHALLENGE_REPLAYED`. Clear `NATIVE_CONSUMED_CHALLENGES` between invocations to prove memory is not authoritative.

- [ ] **Step 2: Run the replay test and confirm RED**

Expected: both processes PASS because the baseline set is process-local.

- [ ] **Step 3: Implement atomic durable consumption**

```python
def consume_native_attestation(ledger_root, identity):
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    key = hashlib.sha256(canonical).hexdigest()
    destination = secure_host_ledger_path(ledger_root, f"{key}.json")
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    try:
        descriptor = os.open(str(destination), flags, 0o600)
    except FileExistsError as error:
        raise NativeReplayError("NATIVE_ADAPTER_CHALLENGE_REPLAYED") from error
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            handle.write(canonical)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        destination.unlink(missing_ok=True)
        raise
```

Call only after schema, correlation, freshness, key, signature, and callback verification and before returning trusted surfaces. Keep the in-memory set after durable consumption as an additional same-process check.

- [ ] **Step 4: Test replay, stale nonce, future nonce, and ledger I/O failure**

Expected: replay/stale/future are BLOCKED; uncertain ledger publication is BLOCKED and never PASS.

- [ ] **Step 5: Commit durable replay protection**

```powershell
git add scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): persist native attestation replay state"
```

### Task 3: Bind Resolution To The Original Detection

**Files:**
- Modify: `ai/schemas/native-bypass-attempt.schema.json`
- Modify: `scripts/ai/tests/test_workflow_helper.py:7030-7145`
- Modify: `scripts/ai/workflow_helper.py:5884-6009`
- Modify: `ai/native-runtime-adapters.md`
- Modify: `ai/verification-gates.md`
- Modify: `docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md`

**Interfaces:**
- A RESOLVED event requires `detectionEventId`, `detectionGateInvocationId`, and `detectionEventSha256`.
- Produces: `native_detection_digest(detection: dict) -> str`.

- [ ] **Step 1: Add failing unrelated-resolution tests**

Create a valid detection and a later resolution that shares only `deduplicationKey` but points to a different event ID, task, original gate, or digest. Each case must return `NATIVE_BYPASS_RESOLUTION_INVALID` or a precise binding error.

- [ ] **Step 2: Run resolution tests and confirm RED**

Expected: at least the unrelated event-ID case is accepted by baseline grouping logic.

- [ ] **Step 3: Extend the closed resolution schema**

For `lifecycle: DETECTED`, all detection binding fields are null. For `RESOLVED`, require non-null values matching identifier and digest bounds:

```json
{
  "detectionEventId": "event-original",
  "detectionGateInvocationId": "gate-original",
  "detectionEventSha256": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
}
```

- [ ] **Step 4: Validate the exact original event**

```python
def native_detection_digest(detection):
    payload = {key: value for key, value in detection.items() if key not in {
        "resolvedAt", "resolutionReason", "detectionEventId",
        "detectionGateInvocationId", "detectionEventSha256",
    }}
    return hashlib.sha256(json.dumps(
        payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
    ).encode("utf-8")).hexdigest()
```

In each resolution group, locate exactly one prior DETECTED event whose event ID, task key, gate invocation ID, deduplication key, and digest match the resolution. Reject absent, multiple, later, or mismatched detections before signed `resolutionEventIds` comparison.

- [ ] **Step 5: Run Phase 3A regression suite and shell contract**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase3ANativeRuntimeAdapterTests -v
& 'C:\Program Files\Git\bin\bash.exe' -n scripts/ai/tests/native-adapter-gate.sh
git diff --check
```

Expected: exit 0; current host remains UNSUPPORTED; no repository `.ai-runs` exists.

- [ ] **Step 6: Update Phase 3A documentation and commit**

Document external host authority, public CLI limitation, durable ledger, and original detection binding without claiming current native enforcement.

```powershell
git add ai/schemas/native-bypass-attempt.schema.json ai/native-runtime-adapters.md ai/verification-gates.md docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py scripts/ai/tests/native-adapter-gate.sh
git commit -m "fix(ai): bind native bypass resolutions"
```
