# Phase 3B CI Provenance Hardening Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Separate repository contract success from native enforcement, reject locally self-certified CI evidence, bind future PASS to GitHub provenance, and run the complete helper regression suite in the contract entry point.

**Architecture:** Rename the existing green workflow as a repository contract check. Keep native enforcement NOT_CONFIGURED until an external GitHub verifier supplies authenticated run/job/workflow/artifact provenance; repository `retainedRun` remains a claim only.

**Tech Stack:** GitHub Actions YAML, Python 3.12 in CI, Python 3.9+ helper contracts, Draft 2020-12 JSON Schema, SHA-256, GitHub artifact attestations.

## Global Constraints

- A green repository contract check is not Phase 3 enforcement PASS.
- The native enforcement check must not be emitted green while its state is NOT_CONFIGURED or BLOCKED.
- `GITHUB_RUN_ID`, `GITHUB_RUN_ATTEMPT`, `GITHUB_JOB`, `GITHUB_WORKFLOW_REF`, `GITHUB_WORKFLOW_SHA`, and `GITHUB_SHA` are correlation inputs, not sufficient cryptographic authority by themselves.
- Artifact attestations must be cryptographically verified and signer identity validated before trusted use.
- Current branch work does not push, create a PR, modify branch protection, close Issues, or execute GitHub workflows.
- Product commands, servers, Docker, HTTP/API, databases, migrations, seeds, and deploys remain NOT RUN.

## File Map

- Create `ai/schemas/github-ci-provenance.schema.json`: externally verified GitHub run/job/workflow/artifact envelope.
- Modify `ai/schemas/ci-capability-status.schema.json` and `ai/ci-capability-status.json`: separate contract and enforcement state.
- Modify `ai/schemas/ci-gate-result.schema.json`: expose verified provenance identity.
- Modify `scripts/ai/workflow_helper.py`: provenance validation and local self-certification rejection.
- Modify `scripts/ai/tests/test_workflow_helper.py`: provenance negative matrix.
- Modify `.github/workflows/phase-3b-ci-gates.yml`: rename contract job and stop treating enforcement NOT_CONFIGURED as success.
- Modify `scripts/ai/tests/run-contract-tests.sh`: run complete Python helper suite.
- Modify `ai/project-state.json` and `ai/project-state.md`: workflow exists; native enforcement remains NOT_CONFIGURED.
- Modify `ai/ci-gates.md` and Phase 3B design: corrected semantics.

---

### Task 1: Separate Repository Contract And Native Enforcement Checks

**Files:**
- Modify: `.github/workflows/phase-3b-ci-gates.yml`
- Modify: `ai/schemas/ci-capability-status.schema.json`
- Modify: `ai/ci-capability-status.json`
- Modify: `ai/project-state.json`
- Modify: `ai/project-state.md`
- Modify: `scripts/ai/tests/test_workflow_helper.py:8896`

**Interfaces:**
- Contract check name: `phase-3b-repository-contract`
- Enforcement check identity: `phase-3b-native-enforcement`, state `NOT_CONFIGURED` until externally installed.

- [ ] **Step 1: Add failing workflow/state semantics tests**

Assert the workflow/job name is `phase-3b-repository-contract`, no step accepts exit 3 as enforcement success, capability status has separate `repositoryContract` and `nativeEnforcement` objects, and project state says CI workflow exists while native enforcement is NOT_CONFIGURED.

- [ ] **Step 2: Run the new Phase 3B tests and confirm RED**

Expected: baseline still names the green job `phase-3b-ci-gates`, accepts exit 3, and project state says no workflow exists.

- [ ] **Step 3: Split canonical status**

Use this semantic shape in `currentCi`:

```json
{
  "repositoryContract": {
    "checkName": "phase-3b-repository-contract",
    "workflowRef": ".github/workflows/phase-3b-ci-gates.yml",
    "configurationStatus": "CONFIGURED_UNVERIFIED"
  },
  "nativeEnforcement": {
    "checkName": "phase-3b-native-enforcement",
    "configurationStatus": "NOT_CONFIGURED",
    "requiredCheckConfigured": false,
    "reasonCode": "GITHUB_REQUIRED_CHECK_AND_NATIVE_ADAPTER_NOT_CONFIGURED"
  }
}
```

Remove the ambiguous single `requiredCheck` field. Keep remote runner and durable evidence completion-blocking.

- [ ] **Step 4: Rename and narrow the workflow**

Change workflow `name`, job ID, and job display name to repository contract terminology. Remove the step that runs `ci-evidence-gate.sh` and accepts status 3. The workflow runs helper/static contracts and uploads diagnostic test output only; it does not emit an enforcement result.

- [ ] **Step 5: Synchronize project state**

Set CI environment `configurationStatus` to `CONFIGURED_UNVERIFIED` with notes stating the repository contract workflow exists and native enforcement remains NOT_CONFIGURED. Update the generated Markdown section from canonical JSON without changing LOCAL runtime claims.

- [ ] **Step 6: Run workflow/static state tests and commit**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper.Phase3BCIGatesDurableEvidenceTests -v
git diff --check
```

Expected: exit 0.

```powershell
git add .github/workflows/phase-3b-ci-gates.yml ai/schemas/ci-capability-status.schema.json ai/ci-capability-status.json ai/project-state.json ai/project-state.md scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): separate ci contract and enforcement"
```

### Task 2: Require Authenticated GitHub Provenance For CI PASS

**Files:**
- Create: `ai/schemas/github-ci-provenance.schema.json`
- Modify: `ai/schemas/ci-gate-result.schema.json`
- Modify: `scripts/ai/tests/test_workflow_helper.py:8916-8988`
- Modify: `scripts/ai/workflow_helper.py:6392-6493`
- Modify: `ai/ci-gates.md`

**Interfaces:**
- Produces: immutable `GitHubCiProvenance` value loaded only by a future external verifier integration.
- Changes: `ci_evidence_gate(root, task_key, gate_invocation_id, ci_status_ref="ai/ci-capability-status.json", github_provenance=None)`.
- Public `ci-evidence-gate.sh` supplies `github_provenance=None` and therefore cannot self-certify PASS.

- [ ] **Step 1: Add the complete failing provenance matrix**

Tests must reject: fake `retainedRun`, wrong repository, head SHA, workflow ref/SHA, run ID, attempt, job ID, event name, artifact ID, artifact digest, member digest, native evidence digest, bypass event-set digest, resolution IDs, task, and gate. Also reject valid-looking evidence from a different run. A repository-local file with all correct strings must still return NOT_CONFIGURED without an externally verified provenance object.

- [ ] **Step 2: Run provenance tests and confirm RED**

Expected: baseline can PASS from `AVAILABLE` repository status plus local files after only task/gate checks.

- [ ] **Step 3: Add the closed provenance schema**

Require this shape:

```json
{
  "$schema": "ai/schemas/github-ci-provenance.schema.json",
  "schemaVersion": 1,
  "repository": "116Lv/sparta-ch6-advanced",
  "workflowRef": "116Lv/sparta-ch6-advanced/.github/workflows/phase-3b-ci-gates.yml@refs/heads/main",
  "workflowSha": "0123456789abcdef0123456789abcdef01234567",
  "headSha": "0123456789abcdef0123456789abcdef01234567",
  "eventName": "push",
  "runId": 123456789,
  "runAttempt": 1,
  "jobId": "phase-3b-repository-contract",
  "artifactId": 987654321,
  "artifactDigest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
  "members": [
    {"path": "phase3b-contract-results.json", "sha256": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"}
  ],
  "taskKey": "issue-12",
  "gateInvocationId": "github-actions",
  "nativeEvidenceSha256": "cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc",
  "bypassEventSetSha256": "dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd",
  "resolutionEventIds": [],
  "attestation": {
    "subjectDigest": "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "signerRepository": "116Lv/sparta-ch6-advanced",
    "verified": true
  }
}
```

The internal loader receives the object only after an external GitHub/Sigstore verifier has cryptographically validated the bundle and signer. Repository paths cannot supply this object to the public CLI.

- [ ] **Step 4: Implement exact binding**

```python
def validate_github_ci_provenance(provenance, expected, artifact_root):
    exact = {
        "repository": expected["repository"],
        "workflowRef": expected["workflowRef"],
        "workflowSha": expected["workflowSha"],
        "headSha": expected["headSha"],
        "runId": expected["runId"],
        "runAttempt": expected["runAttempt"],
        "jobId": expected["jobId"],
        "taskKey": expected["taskKey"],
        "gateInvocationId": expected["gateInvocationId"],
    }
    if any(provenance[key] != value for key, value in exact.items()):
        raise InvalidStateError([validation_error("CI_GITHUB_PROVENANCE_MISMATCH")])
    if not provenance["attestation"]["verified"]:
        raise InvalidStateError([validation_error("CI_ATTESTATION_UNVERIFIED")])
    if provenance["attestation"]["subjectDigest"] != provenance["artifactDigest"]:
        raise InvalidStateError([validation_error("CI_ARTIFACT_ATTESTATION_MISMATCH")])
    for member in provenance["members"]:
        path = secure_artifact_member(artifact_root, member["path"])
        if digest(path) != member["sha256"]:
            raise InvalidStateError([validation_error("CI_ARTIFACT_MEMBER_TAMPERED")])
```

`ci_evidence_gate` returns `NOT_CONFIGURED/CI_GITHUB_PROVENANCE_NOT_AVAILABLE` whenever `github_provenance is None`, regardless of `retainedRun`. Only the internal verified path may continue to native installation and remote-runner checks.

- [ ] **Step 5: Run all Phase 3B provenance tests**

Expected: every wrong binding is BLOCKED/INVALID_STATE as specified; repository-only retained state never PASSes; a completely matching externally verified object passes only in the lower-level test path.

- [ ] **Step 6: Commit provenance verification**

```powershell
git add ai/schemas/github-ci-provenance.schema.json ai/schemas/ci-gate-result.schema.json ai/ci-gates.md scripts/ai/workflow_helper.py scripts/ai/tests/test_workflow_helper.py
git commit -m "fix(ai): bind ci evidence to github provenance"
```

### Task 3: Run The Complete Helper Regression Suite From The Contract Entry Point

**Files:**
- Modify: `scripts/ai/tests/run-contract-tests.sh`
- Modify: `.github/workflows/phase-3b-ci-gates.yml`
- Modify: `scripts/ai/tests/test_workflow_helper.py:8988`
- Modify: `docs/superpowers/specs/2026-07-13-ai-workflow-phase-3b-ci-gates-durable-evidence-design.md`

**Interfaces:**
- Contract entry point runs the full Python helper module once, then both shell contract scripts.

- [ ] **Step 1: Add a failing contract-entry test**

Read `run-contract-tests.sh` and assert it invokes:

```text
python -m unittest scripts.ai.tests.test_workflow_helper -v
```

Assert the workflow calls `bash scripts/ai/tests/run-contract-tests.sh` and does not separately select only Phase 2C/3A/3B classes.

- [ ] **Step 2: Run the contract-entry test and confirm RED**

Expected: FAIL because the shell entry point currently runs only two shell scripts.

- [ ] **Step 3: Update the contract entry point**

```bash
#!/usr/bin/env bash
set -eu

PATH=/usr/bin:/bin:$PATH
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
REPOSITORY_ROOT=$(CDPATH= cd -- "$SCRIPT_DIR/../../.." && pwd)

cd "$REPOSITORY_ROOT"
python -m unittest scripts.ai.tests.test_workflow_helper -v
/usr/bin/bash "$SCRIPT_DIR/test-runtime-preflight.sh"
/usr/bin/bash "$SCRIPT_DIR/test-command-runner.sh"
```

The workflow provisions pinned helper dependencies, then invokes only this contract entry point for helper/shell regressions.

- [ ] **Step 4: Run permitted final verification**

```powershell
$env:PYTHONDONTWRITEBYTECODE='1'
python -m unittest scripts.ai.tests.test_workflow_helper -v
& 'C:\Program Files\Git\bin\bash.exe' -n scripts/ai/tests/run-contract-tests.sh
& 'C:\Program Files\Git\bin\bash.exe' -n scripts/ai/tests/test-runtime-preflight.sh
& 'C:\Program Files\Git\bin\bash.exe' -n scripts/ai/tests/test-command-runner.sh
git diff --check
```

Expected: every command exits 0. Then confirm `Get-ChildItem -Force .ai-runs` is absent, and search non-fixture files for unsupported `VERIFIED`/unqualified `DONE` outputs.

- [ ] **Step 5: Update Phase 3B design and commit**

Document the contract/enforcement split, external GitHub attestation requirement, current NOT_CONFIGURED enforcement state, and complete test entry point.

```powershell
git add scripts/ai/tests/run-contract-tests.sh .github/workflows/phase-3b-ci-gates.yml scripts/ai/tests/test_workflow_helper.py docs/superpowers/specs/2026-07-13-ai-workflow-phase-3b-ci-gates-durable-evidence-design.md
git commit -m "test(ai): run complete workflow contracts"
```

## External Configuration Remaining After This Plan

GitHub branch protection/rulesets must later require `phase-3b-native-enforcement` only after a trusted host integration can produce and verify GitHub artifact attestations and native adapter evidence. Until then, repository contract checks may be green while native enforcement remains NOT_CONFIGURED. Configuring the required check, downloading/verifying attestation bundles, and closing Issues #10 or #12 require separate GitHub authority and are not performed by this plan.

## Authoritative GitHub References

- GitHub Actions default variables and workflow identity: <https://docs.github.com/en/enterprise-cloud@latest/actions/reference/workflows-and-actions/variables>
- Artifact attestation provenance and verification: <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/use-artifact-attestations>
- Offline attestation verification: <https://docs.github.com/en/actions/how-tos/secure-your-work/use-artifact-attestations/verify-attestations-offline>
