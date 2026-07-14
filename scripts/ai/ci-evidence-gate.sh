#!/bin/bash
set -eu

task_key_set=0
gate_invocation_id_set=0
ci_status_set=0
output_set=0

while [ "$#" -gt 0 ]; do
  [ "$#" -ge 2 ] || break
  case "$1" in
    --task-key)
      [ "$task_key_set" -eq 0 ] || break
      task_key=$2
      task_key_set=1
      ;;
    --gate-invocation-id)
      [ "$gate_invocation_id_set" -eq 0 ] || break
      gate_invocation_id=$2
      gate_invocation_id_set=1
      ;;
    --ci-status)
      [ "$ci_status_set" -eq 0 ] || break
      ci_status=$2
      ci_status_set=1
      ;;
    --output)
      [ "$output_set" -eq 0 ] || break
      output=$2
      output_set=1
      ;;
    *) break ;;
  esac
  shift 2
done

if [ "$#" -ne 0 ] || [ "$task_key_set" -ne 1 ] || [ "$gate_invocation_id_set" -ne 1 ] || [ "$output_set" -ne 1 ]; then
  printf '%s\n' '{"$schema":"ai/schemas/ci-gate-result.schema.json","$id":"ai/ci-gate-result.json","schemaVersion":1,"operation":"CI_EVIDENCE_GATE","result":"BLOCKED","phase2cLeafResult":"BLOCKED","reason":"INVALID_CI_GATE_ARGUMENTS","data":{"taskKey":"invalid","gateInvocationId":"invalid","provider":"github-actions","repositoryContract":{"checkName":"phase-3b-repository-contract","workflowRef":".github/workflows/phase-3b-ci-gates.yml","configurationStatus":"CONFIGURED_UNVERIFIED"},"nativeEnforcement":{"checkName":"phase-3b-native-enforcement","configurationStatus":"NOT_CONFIGURED","requiredCheckConfigured":false,"reasonCode":"INVALID_CI_GATE_ARGUMENTS"},"durableEvidence":{"status":"NOT_CONFIGURED","reasonCode":"INVALID_CI_GATE_ARGUMENTS","retentionDays":90,"artifactRefs":[],"requiredBindings":["repository","workflowRef","workflowSha","commitSha","eventName","workflowRunId","attempt","jobId","artifactId","artifactDigest","artifactMembers","taskKey","gateInvocationId","nativeAdapterStatusDigest","bypassEventSetSha256","resolutionEventIds"],"retainedRun":null},"remoteRunner":{"status":"NOT_CONFIGURED","completionBlocking":true,"reasonCode":"INVALID_CI_GATE_ARGUMENTS"},"nativeAdapterLeaf":{"nativeAdapterCheckId":"native-runtime-adapter","currentHostResult":"UNSUPPORTED"},"cachePolicy":{"reuse":"FORBIDDEN_WITHOUT_MATCHING_RUN_ID","handoff":"SUMMARY_ONLY","retentionDays":90},"phase2CLeafResult":"BLOCKED"}}'
  exit 2
fi

if [ "$ci_status_set" -ne 1 ]; then
  ci_status=ai/ci-capability-status.json
fi

ROOT=$(git rev-parse --show-toplevel 2>/dev/null || pwd)
cd "$ROOT"
probe='import sys; from jsonschema import Draft202012Validator, FormatChecker; print(f"{sys.version_info.major}|{Draft202012Validator.__name__}|{FormatChecker.__name__}")'
for candidate_name in python3 python; do
  candidate=$(command -v "$candidate_name" 2>/dev/null || true)
  case "$candidate" in
    /*) ;;
    *) continue ;;
  esac
  [ -f "$candidate" ] && [ -x "$candidate" ] || continue
  result=$("$candidate" -c "$probe" 2>/dev/null || true)
  case "$result" in
    3\|Draft202012Validator\|FormatChecker)
      exec "$candidate" scripts/ai/workflow_helper.py ci-evidence-gate --repository-root "$ROOT" --task-key "$task_key" --gate-invocation-id "$gate_invocation_id" --ci-status "$ci_status" --output "$output"
      ;;
  esac
done
printf '%s\n' '{"$schema":"ai/schemas/ci-gate-result.schema.json","$id":"ai/ci-gate-result.json","schemaVersion":1,"operation":"CI_EVIDENCE_GATE","result":"NOT_CONFIGURED","phase2cLeafResult":"BLOCKED","reason":"HELPER_RUNTIME_UNAVAILABLE","data":{"taskKey":"runtime-unavailable","gateInvocationId":"runtime-unavailable","provider":"github-actions","repositoryContract":{"checkName":"phase-3b-repository-contract","workflowRef":".github/workflows/phase-3b-ci-gates.yml","configurationStatus":"CONFIGURED_UNVERIFIED"},"nativeEnforcement":{"checkName":"phase-3b-native-enforcement","configurationStatus":"NOT_CONFIGURED","requiredCheckConfigured":false,"reasonCode":"HELPER_RUNTIME_UNAVAILABLE"},"durableEvidence":{"status":"NOT_CONFIGURED","reasonCode":"HELPER_RUNTIME_UNAVAILABLE","retentionDays":90,"artifactRefs":[],"requiredBindings":["repository","workflowRef","workflowSha","commitSha","eventName","workflowRunId","attempt","jobId","artifactId","artifactDigest","artifactMembers","taskKey","gateInvocationId","nativeAdapterStatusDigest","bypassEventSetSha256","resolutionEventIds"],"retainedRun":null},"remoteRunner":{"status":"NOT_CONFIGURED","completionBlocking":true,"reasonCode":"HELPER_RUNTIME_UNAVAILABLE"},"nativeAdapterLeaf":{"nativeAdapterCheckId":"native-runtime-adapter","currentHostResult":"UNSUPPORTED"},"cachePolicy":{"reuse":"FORBIDDEN_WITHOUT_MATCHING_RUN_ID","handoff":"SUMMARY_ONLY","retentionDays":90},"phase2CLeafResult":"BLOCKED"}}'
exit 3
