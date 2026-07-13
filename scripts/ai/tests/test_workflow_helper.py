import ast
import base64
import contextlib
from concurrent.futures import ThreadPoolExecutor
import datetime as dt
import hashlib
import importlib.util
import io
from itertools import product
import json
import os
from pathlib import Path
import re
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
from types import SimpleNamespace
import unittest
from unittest import mock
import uuid as uuid_module

from jsonschema import Draft202012Validator, FormatChecker

try:
    from cryptography.exceptions import UnsupportedAlgorithm
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
except ImportError:
    UnsupportedAlgorithm = None
    Ed25519PrivateKey = None
    Encoding = None
    PublicFormat = None


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
HELPER_PATH = REPOSITORY_ROOT / "scripts" / "ai" / "workflow_helper.py"
GATEWAY_SCHEMA_PATH = REPOSITORY_ROOT / "ai" / "schemas" / "gateway-result.schema.json"
GATEWAY_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1b" / "gateway-result"
PHASE_1B_GATEWAY_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1b" / "gateway"
PHASE_1A_VALID_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1a" / "valid"
PHASE_1A_INVALID_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1a" / "invalid"
STRICT_JSON_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1b" / "json"
REGISTRY_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1b" / "registry"
PARAMETER_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1b" / "parameters"
PREREQUISITE_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1b" / "prerequisites"
EXECUTION_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1b" / "execution"
PHASE_1A_SEMANTIC_INVALID_FIXTURES_PATH = REPOSITORY_ROOT / "ai" / "fixtures" / "phase-1a" / "semantic-invalid"


def load_helper():
    specification = importlib.util.spec_from_file_location("workflow_helper_under_test", HELPER_PATH)
    module = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(module)
    return module


def preflight_pass():
    return {
        "$schema": "ai/schemas/gateway-result.schema.json",
        "$id": "ai/gateway-result.json",
        "schemaVersion": 1,
        "operation": "PREFLIGHT",
        "result": "PASS",
        "reason": None,
        "errors": [],
        "data": {
            "runtimeCommand": "python3",
            "runtimeExecutableHash": "a" * 64,
            "pythonVersion": "3.13.0",
            "jsonschemaVersion": "4.25.0",
            "validator": "Draft202012Validator",
            "formatChecker": True,
        },
    }


def resolve_pass():
    return {
        "$schema": "ai/schemas/gateway-result.schema.json",
        "$id": "ai/gateway-result.json",
        "schemaVersion": 1,
        "operation": "RESOLVE",
        "result": "PASS",
        "reason": None,
        "errors": [],
        "data": {
            "commandId": "test-unit",
            "classification": "SAFE",
            "workingDirectory": ".",
            "argv": ["./gradlew", "test"],
            "prerequisiteIds": [],
        },
    }


def gateway_result(operation, result, reason, data):
    return {
        "$schema": "ai/schemas/gateway-result.schema.json",
        "$id": "ai/gateway-result.json",
        "schemaVersion": 1,
        "operation": operation,
        "result": result,
        "reason": reason,
        "errors": [] if result == "PASS" else [{
            "code": "FIXTURE",
            "instancePath": "",
            "schemaPath": "",
            "message": "fixture failure",
        }],
        "data": data,
    }


def run_start_pass():
    return gateway_result("RUN_START", "PASS", None, {
        "runId": "run-1",
        "taskKey": "phase-1b-2-task-1",
        "sessionRef": ".ai-runs/run-1/.state/run-session.json",
    })


def pre_command_pass():
    return gateway_result("PRE_COMMAND", "PASS", None, {
        "runId": "run-1",
        "commandId": "verify.unit",
        "attemptId": "attempt-1",
        "argvHash": "a" * 64,
        "inputFingerprint": "b" * 64,
        "environmentFingerprint": "c" * 64,
        "workingDirectory": ".",
        "argv": ["./gradlew", "test"],
    })


def post_command_result(result, process_exit_code):
    return gateway_result("POST_COMMAND", result, None if result == "PASS" else "child did not complete cleanly", {
        "runId": "run-1",
        "commandId": "verify.unit",
        "attemptId": "attempt-1",
        "processExitCode": process_exit_code,
        "processAttemptRef": ".ai-runs/run-1/process-attempts/verify.unit/attempt-1.json",
        "commandResultRef": ".ai-runs/run-1/commands/verify.unit/attempt-1.json",
    })


def pre_done_claim_pass():
    return gateway_result("PRE_DONE_CLAIM", "PASS", None, {
        "runId": "run-1",
        "taskKey": "phase-1b-3",
        "doneClaimRef": ".ai-runs/run-1/done-claim.json",
        "manifestRef": ".ai-runs/run-1/artifact-manifest.json",
        "runRef": ".ai-runs/run-1/run.json",
        "gateResultRef": ".ai-runs/run-1/gate-results/pre-done-claim.json",
        "completenessEvaluated": False,
        "scope": "INTEGRITY_ONLY",
    })


class GatewayResultSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with GATEWAY_SCHEMA_PATH.open(encoding="utf-8") as handle:
            cls.schema = json.load(handle)
        Draft202012Validator.check_schema(cls.schema)
        cls.validator = Draft202012Validator(cls.schema, format_checker=FormatChecker())

    def assert_valid(self, result):
        self.assertEqual(list(self.validator.iter_errors(result)), [])

    def assert_invalid(self, result):
        self.assertNotEqual(list(self.validator.iter_errors(result)), [])

    def test_preflight_pass_uses_the_closed_runtime_shape(self):
        self.assert_valid(preflight_pass())

    def test_non_pass_requires_a_reason_and_never_allows_executable_argv(self):
        missing_reason = preflight_pass()
        missing_reason.update({"result": "NOT_CONFIGURED", "reason": "", "data": None})
        self.assert_invalid(missing_reason)

        executable_data = preflight_pass()
        executable_data.update({"result": "BLOCKED", "reason": "runtime blocked", "data": {"argv": ["./gradlew", "test"]}})
        self.assert_invalid(executable_data)

    def test_resolve_pass_requires_the_complete_planning_data(self):
        self.assert_valid(resolve_pass())
        for required_key in ("commandId", "classification", "workingDirectory", "argv", "prerequisiteIds"):
            with self.subTest(required_key=required_key):
                result = resolve_pass()
                del result["data"][required_key]
                self.assert_invalid(result)

    def test_resolve_blocked_only_contains_non_empty_prerequisite_ids(self):
        result = resolve_pass()
        result.update({
            "result": "BLOCKED",
            "reason": "prerequisites are incomplete",
            "data": {"prerequisiteIds": ["compile-main", "compile-test"]},
        })
        self.assert_valid(result)

        result["data"]["argv"] = ["./gradlew", "test"]
        self.assert_invalid(result)

    def test_resolve_blocked_without_prerequisites_requires_null_data(self):
        result = resolve_pass()
        result.update({
            "result": "BLOCKED",
            "reason": "configuration or classification is blocked",
            "data": None,
        })
        self.assert_valid(result)

        result["data"] = {"prerequisiteIds": []}
        self.assert_invalid(result)

    def test_unknown_operation_result_and_extra_fields_are_rejected(self):
        unknown_operation = preflight_pass()
        unknown_operation["operation"] = "EXECUTE"
        self.assert_invalid(unknown_operation)

        unknown_result = preflight_pass()
        unknown_result["result"] = "EXECUTED"
        self.assert_invalid(unknown_result)

        extra_field = preflight_pass()
        extra_field["unexpected"] = True
        self.assert_invalid(extra_field)

    def test_pre_done_claim_pass_reports_integrity_only_shape(self):
        instance = pre_done_claim_pass()
        self.assert_valid(instance)
        self.assertEqual(instance["data"]["completenessEvaluated"], False)
        self.assertEqual(instance["data"]["scope"], "INTEGRITY_ONLY")
        for required_key in (
            "runId", "taskKey", "doneClaimRef", "manifestRef", "runRef",
            "gateResultRef", "completenessEvaluated", "scope",
        ):
            with self.subTest(required_key=required_key):
                invalid = pre_done_claim_pass()
                del invalid["data"][required_key]
                self.assert_invalid(invalid)
        invalid = pre_done_claim_pass()
        invalid["data"]["completenessEvaluated"] = True
        self.assert_invalid(invalid)
        invalid = pre_done_claim_pass()
        invalid["data"]["scope"] = "COMPLETENESS"
        self.assert_invalid(invalid)

    def test_pre_done_claim_non_pass_branches_have_null_data(self):
        for result in ("FAIL", "BLOCKED", "NOT_CONFIGURED", "POLICY_VIOLATION", "INVALID_STATE"):
            with self.subTest(result=result):
                instance = gateway_result("PRE_DONE_CLAIM", result, "integrity gate blocked", None)
                self.assert_valid(instance)
                invalid = gateway_result("PRE_DONE_CLAIM", result, "integrity gate blocked", {"argv": ["./gradlew", "test"]})
                self.assert_invalid(invalid)

    def test_committed_gateway_result_fixtures_validate_with_expected_branch_data(self):
        expected_branches = {
            "preflight-pass.json": ("PREFLIGHT", "PASS"),
            "resolve-pass.json": ("RESOLVE", "PASS"),
            "resolve-blocked-prerequisites.json": ("RESOLVE", "BLOCKED"),
        }
        fixture_paths = sorted(GATEWAY_FIXTURES_PATH.glob("*.json"))
        self.assertEqual({path.name for path in fixture_paths}, set(expected_branches))

        for fixture_path in fixture_paths:
            with self.subTest(fixture=fixture_path.name):
                with fixture_path.open(encoding="utf-8") as handle:
                    result = json.load(handle)
                self.assert_valid(result)
                self.assertEqual(
                    (result["operation"], result["result"]),
                    expected_branches[fixture_path.name],
                )

                if fixture_path.name == "preflight-pass.json":
                    self.assertIsNone(result["reason"])
                    self.assertEqual(result["errors"], [])
                    self.assertEqual(
                        set(result["data"]),
                        {"runtimeCommand", "runtimeExecutableHash", "pythonVersion", "jsonschemaVersion", "validator", "formatChecker"},
                    )
                elif fixture_path.name == "resolve-pass.json":
                    self.assertIsNone(result["reason"])
                    self.assertEqual(result["errors"], [])
                    self.assertEqual(
                        set(result["data"]),
                        {"commandId", "classification", "workingDirectory", "argv", "prerequisiteIds"},
                    )
                    self.assertTrue(result["data"]["argv"])
                    self.assertEqual(result["data"]["prerequisiteIds"], [])
                else:
                    self.assertTrue(result["reason"])
                    self.assertEqual(set(result["data"]), {"prerequisiteIds"})
                    self.assertTrue(result["data"]["prerequisiteIds"])


class Phase1B2Task1SchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.helper = load_helper()
        cls.schemas = {}
        for name in ("gateway-result", "command-result", "run-session", "process-attempt", "artifact-manifest"):
            with (REPOSITORY_ROOT / "ai" / "schemas" / f"{name}.schema.json").open(encoding="utf-8") as handle:
                cls.schemas[name] = json.load(handle)
            Draft202012Validator.check_schema(cls.schemas[name])
        cls.validators = {
            name: Draft202012Validator(schema, format_checker=FormatChecker())
            for name, schema in cls.schemas.items()
        }

    def assert_schema_valid(self, schema_name, instance):
        self.assertEqual(list(self.validators[schema_name].iter_errors(instance)), [])

    def assert_schema_invalid(self, schema_name, instance):
        self.assertNotEqual(list(self.validators[schema_name].iter_errors(instance)), [])

    def assert_helper_invalid(self, schema_name, instance):
        with self.assertRaises(self.helper.InvalidStateError):
            self.helper.validate(REPOSITORY_ROOT, instance, f"ai/schemas/{schema_name}.schema.json")

    def helper_errors(self, schema_name, instance):
        with self.assertRaises(self.helper.InvalidStateError) as raised:
            self.helper.validate(REPOSITORY_ROOT, instance, f"ai/schemas/{schema_name}.schema.json")
        return raised.exception.errors

    def fixture(self, name):
        with (PHASE_1B_GATEWAY_FIXTURES_PATH / name).open(encoding="utf-8") as handle:
            return json.load(handle)

    def test_phase_1b2_and_phase_2_schema_names_are_allowlisted(self):
        additions = {"run-session", "process-attempt", "artifact-manifest"}
        self.assertTrue(additions.issubset(self.helper.SCHEMA_NAMES))
        phase_2a = {"context-map", "workflow-cache", "repo-intake-result"}
        self.assertTrue(phase_2a.issubset(self.helper.SCHEMA_NAMES))
        phase_2b = {"agent-handoff", "skill-catalog"}
        self.assertTrue(phase_2b.issubset(self.helper.SCHEMA_NAMES))
        phase_2c = {"verification-policy", "verification-gate-result"}
        self.assertTrue(phase_2c.issubset(self.helper.SCHEMA_NAMES))
        phase_3a = {
            "native-adapter-result",
            "native-bypass-attempt",
            "native-runtime-adapters",
            "native-runtime-snapshot",
        }
        self.assertTrue(phase_3a.issubset(self.helper.SCHEMA_NAMES))
        self.assertEqual(len(self.helper.SCHEMA_NAMES), 25)
        self.assertEqual(
            {name for name in self.helper.SCHEMA_NAMES if name in additions},
            additions,
        )

    def test_gateway_operation_matrix_has_exact_closed_data_shapes(self):
        valid_cases = (
            ("RUN_START", "PASS", run_start_pass()),
            ("RUN_START", "BLOCKED", gateway_result("RUN_START", "BLOCKED", "run is locked", None)),
            ("RUN_START", "NOT_CONFIGURED", gateway_result("RUN_START", "NOT_CONFIGURED", "runtime unavailable", None)),
            ("RUN_START", "POLICY_VIOLATION", gateway_result("RUN_START", "POLICY_VIOLATION", "bad request", None)),
            ("RUN_START", "INVALID_STATE", gateway_result("RUN_START", "INVALID_STATE", "bad state", None)),
            ("PRE_COMMAND", "PASS", pre_command_pass()),
            ("PRE_COMMAND", "BLOCKED", gateway_result("PRE_COMMAND", "BLOCKED", "prerequisite missing", None)),
            ("PRE_COMMAND", "NOT_CONFIGURED", gateway_result("PRE_COMMAND", "NOT_CONFIGURED", "runtime unavailable", None)),
            ("PRE_COMMAND", "POLICY_VIOLATION", gateway_result("PRE_COMMAND", "POLICY_VIOLATION", "bad request", None)),
            ("PRE_COMMAND", "INVALID_STATE", gateway_result("PRE_COMMAND", "INVALID_STATE", "bad state", None)),
            ("POST_COMMAND", "PASS", post_command_result("PASS", 0)),
            ("POST_COMMAND", "FAIL", post_command_result("FAIL", 7)),
            ("POST_COMMAND", "BLOCKED", post_command_result("BLOCKED", None)),
            ("POST_COMMAND", "NOT_CONFIGURED", gateway_result("POST_COMMAND", "NOT_CONFIGURED", "runtime unavailable", None)),
            ("POST_COMMAND", "POLICY_VIOLATION", gateway_result("POST_COMMAND", "POLICY_VIOLATION", "bad request", None)),
            ("POST_COMMAND", "INVALID_STATE", gateway_result("POST_COMMAND", "INVALID_STATE", "bad state", None)),
        )
        for operation, result, instance in valid_cases:
            with self.subTest(operation=operation, result=result):
                self.assert_schema_valid("gateway-result", instance)

        for factory, expected_keys in (
            (run_start_pass, {"runId", "taskKey", "sessionRef"}),
            (pre_command_pass, {"runId", "commandId", "attemptId", "argvHash", "inputFingerprint", "environmentFingerprint", "workingDirectory", "argv"}),
            (lambda: post_command_result("FAIL", 7), {"runId", "commandId", "attemptId", "processExitCode", "processAttemptRef", "commandResultRef"}),
        ):
            with self.subTest(expected_keys=expected_keys):
                instance = factory()
                self.assertEqual(set(instance["data"]), expected_keys)
                instance["data"]["unexpected"] = True
                self.assert_schema_invalid("gateway-result", instance)

        invalid = run_start_pass()
        invalid["data"] = {"runId": "run-1", "taskKey": "phase-1b-2-task-1"}
        self.assert_schema_invalid("gateway-result", invalid)
        invalid = post_command_result("FAIL", 0)
        self.assert_schema_invalid("gateway-result", invalid)
        invalid = gateway_result("POST_COMMAND", "BLOCKED", "blocked", None)
        self.assert_schema_invalid("gateway-result", invalid)

    def test_new_gateway_pass_and_non_pass_reason_boundaries_are_exact(self):
        for instance in (run_start_pass(), pre_command_pass(), post_command_result("PASS", 0)):
            with self.subTest(operation=instance["operation"], case="pass-null-reason"):
                self.assert_schema_valid("gateway-result", instance)
                invalid = json.loads(json.dumps(instance))
                invalid["reason"] = ""
                self.assert_schema_invalid("gateway-result", invalid)

        for operation in ("RUN_START", "PRE_COMMAND", "POST_COMMAND"):
            with self.subTest(operation=operation, case="non-pass-empty-reason"):
                invalid = gateway_result(operation, "INVALID_STATE", "", None)
                self.assert_schema_invalid("gateway-result", invalid)
            with self.subTest(operation=operation, case="non-pass-null-reason"):
                invalid = gateway_result(operation, "INVALID_STATE", None, None)
                self.assert_schema_invalid("gateway-result", invalid)

    def test_run_start_and_pre_command_non_pass_branches_forbid_all_data_and_argv(self):
        for operation in ("RUN_START", "PRE_COMMAND"):
            for result in ("BLOCKED", "NOT_CONFIGURED", "POLICY_VIOLATION", "INVALID_STATE"):
                with self.subTest(operation=operation, result=result, case="object-data"):
                    invalid = gateway_result(operation, result, "blocked", {"unexpected": True})
                    self.assert_schema_invalid("gateway-result", invalid)
                with self.subTest(operation=operation, result=result, case="argv-data"):
                    invalid = gateway_result(operation, result, "blocked", {"argv": ["./gradlew", "test"]})
                    self.assert_schema_invalid("gateway-result", invalid)

    def test_post_command_branches_require_exact_data_and_exclude_argv(self):
        for result, process_exit_code in (("PASS", 0), ("FAIL", 7), ("BLOCKED", None)):
            with self.subTest(result=result, case="exact-data"):
                instance = post_command_result(result, process_exit_code)
                self.assert_schema_valid("gateway-result", instance)
            with self.subTest(result=result, case="missing-key"):
                invalid = post_command_result(result, process_exit_code)
                del invalid["data"]["processAttemptRef"]
                self.assert_schema_invalid("gateway-result", invalid)
            with self.subTest(result=result, case="argv"):
                invalid = post_command_result(result, process_exit_code)
                invalid["data"]["argv"] = ["./gradlew", "test"]
                self.assert_schema_invalid("gateway-result", invalid)

        for result in ("NOT_CONFIGURED", "POLICY_VIOLATION", "INVALID_STATE"):
            with self.subTest(result=result, case="null-data"):
                instance = gateway_result("POST_COMMAND", result, "blocked", None)
                self.assert_schema_valid("gateway-result", instance)
            with self.subTest(result=result, case="argv-data"):
                invalid = gateway_result("POST_COMMAND", result, "blocked", {"argv": ["./gradlew", "test"]})
                self.assert_schema_invalid("gateway-result", invalid)

    def test_task1_gateway_fixtures_validate_and_cover_closed_branches(self):
        expected = {
            "run-start-pass.json": ("gateway-result", "RUN_START", "PASS"),
            "run-start-blocked.json": ("gateway-result", "RUN_START", "BLOCKED"),
            "pre-command-pass.json": ("gateway-result", "PRE_COMMAND", "PASS"),
            "post-command-fail.json": ("gateway-result", "POST_COMMAND", "FAIL"),
        }
        fixture_paths = sorted(PHASE_1B_GATEWAY_FIXTURES_PATH.glob("*.json"))
        self.assertTrue({
            "run-session-open.json",
            "run-session-invalid-lock-recovery.json",
            "process-attempt-exited.json",
            "process-attempt-spawn-failed.json",
            "artifact-manifest-empty-logs.json",
            "artifact-manifest-negative-size.json",
            *expected,
        }.issubset({path.name for path in fixture_paths}))
        for filename, (schema_name, operation, result) in expected.items():
            with self.subTest(fixture=filename):
                instance = self.fixture(filename)
                self.assert_schema_valid(schema_name, instance)
                self.assertEqual((instance["operation"], instance["result"]), (operation, result))

    def test_run_session_schema_and_thin_reference_validator_are_closed(self):
        instance = self.fixture("run-session-open.json")
        self.assert_schema_valid("run-session", instance)
        self.helper.validate(REPOSITORY_ROOT, instance, "ai/schemas/run-session.schema.json")
        self.assertEqual(instance["state"], "OPEN")
        self.assertFalse(instance["lockRecoveries"])

        finalizing = json.loads(json.dumps(instance))
        finalizing["state"] = "FINALIZING"
        self.assert_schema_valid("run-session", finalizing)
        self.assertNotIn("FINALIZING", {self.fixture("run-session-open.json")["state"]})

        for mutate in (
            lambda value: value.update({"$id": ".ai-runs/other/.state/run-session.json"}),
            lambda value: value["commandResultRefs"].append(value["processAttemptRefs"][0]),
            lambda value: value["reservations"][0].update({
                "processAttemptRef": ".ai-runs/run-1/process-attempts/verify.unit/other-attempt.json",
            }),
        ):
            with self.subTest(mutate=mutate):
                invalid = json.loads(json.dumps(instance))
                mutate(invalid)
                self.assert_helper_invalid("run-session", invalid)

        self.assert_schema_invalid("run-session", self.fixture("run-session-invalid-lock-recovery.json"))

    def test_terminal_reservations_require_both_exact_artifact_refs_and_reserved_has_none(self):
        baseline = self.fixture("run-session-open.json")
        for state in ("PASS", "FAIL", "BLOCKED"):
            with self.subTest(state=state, case="valid"):
                instance = json.loads(json.dumps(baseline))
                instance["reservations"][0]["state"] = state
                self.assert_schema_valid("run-session", instance)
                self.helper.validate(REPOSITORY_ROOT, instance, "ai/schemas/run-session.schema.json")
            for field in ("commandResultRef", "processAttemptRef"):
                with self.subTest(state=state, missing=field):
                    instance = json.loads(json.dumps(baseline))
                    instance["reservations"][0]["state"] = state
                    instance["reservations"][0][field] = None
                    self.assert_schema_invalid("run-session", instance)

        reserved = json.loads(json.dumps(baseline))
        reserved["commandResultRefs"] = []
        reserved["processAttemptRefs"] = []
        reservation = reserved["reservations"][0]
        reservation.update({
            "state": "RESERVED",
            "commandResultRef": None,
            "processAttemptRef": None,
            "terminalAt": None,
        })
        self.assert_schema_valid("run-session", reserved)
        self.helper.validate(REPOSITORY_ROOT, reserved, "ai/schemas/run-session.schema.json")

    def test_run_session_has_a_dedicated_semantic_validator(self):
        self.assertTrue(hasattr(self.helper, "validate_run_session"))

    def test_rerun_correlation_fields_are_jointly_null_or_jointly_present(self):
        baseline = self.fixture("run-session-open.json")
        reservation = baseline["reservations"][0]
        self.assert_schema_valid("run-session", baseline)

        rerun = json.loads(json.dumps(baseline))
        rerun["reservations"][0].update({
            "rerunReasonHash": "d" * 64,
            "rerunOfAttemptId": "attempt-0",
        })
        self.assert_schema_valid("run-session", rerun)

        for field, value in (("rerunReasonHash", "d" * 64), ("rerunOfAttemptId", "attempt-0")):
            with self.subTest(only=field):
                invalid = json.loads(json.dumps(baseline))
                invalid["reservations"][0][field] = value
                self.assert_schema_invalid("run-session", invalid)

        self.assertIsNone(reservation["rerunReasonHash"])
        self.assertIsNone(reservation["rerunOfAttemptId"])

    def test_run_session_semantics_bind_recoveries_uniqueness_and_exact_paths(self):
        baseline = self.fixture("run-session-open.json")
        recovery = {
            "recoveryId": "recovery-1",
            "runId": "run-1",
            "recoveredOwnerId": "owner-1",
            "replacementOwnerId": "owner-2",
            "previousPid": 123,
            "previousAcquiredAt": "2026-07-11T02:00:00Z",
            "recoveredAt": "2026-07-11T03:00:00Z",
            "reason": "DEAD_AND_EXPIRED",
        }
        valid = json.loads(json.dumps(baseline))
        valid["lockRecoveries"] = [recovery]
        self.helper.validate(REPOSITORY_ROOT, valid, "ai/schemas/run-session.schema.json")

        cases = []
        wrong_run = json.loads(json.dumps(valid))
        wrong_run["lockRecoveries"][0]["runId"] = "other-run"
        cases.append((wrong_run, "LOCK_RECOVERY_RUN_MISMATCH", "/lockRecoveries/0/runId"))

        duplicate_recovery = json.loads(json.dumps(valid))
        duplicate_recovery["lockRecoveries"].append(json.loads(json.dumps(recovery)))
        duplicate_recovery["lockRecoveries"][1]["replacementOwnerId"] = "owner-3"
        cases.append((duplicate_recovery, "DUPLICATE_LOCK_RECOVERY_ID", "/lockRecoveries/1/recoveryId"))

        duplicate_reservation = json.loads(json.dumps(baseline))
        duplicate_reservation["reservations"].append(json.loads(json.dumps(duplicate_reservation["reservations"][0])))
        cases.append((duplicate_reservation, "DUPLICATE_RESERVATION_TUPLE", "/reservations/1"))

        duplicate_attempt = json.loads(json.dumps(baseline))
        second = json.loads(json.dumps(duplicate_attempt["reservations"][0]))
        second["commandId"] = "verify.integration"
        second["commandResultRef"] = ".ai-runs/run-1/commands/verify.integration/attempt-1.json"
        second["processAttemptRef"] = ".ai-runs/run-1/process-attempts/verify.integration/attempt-1.json"
        duplicate_attempt["commandResultRefs"].append(second["commandResultRef"])
        duplicate_attempt["processAttemptRefs"].append(second["processAttemptRef"])
        duplicate_attempt["reservations"].append(second)
        cases.append((duplicate_attempt, "DUPLICATE_ATTEMPT_ID", "/reservations/1/attemptId"))

        wrong_command_ref = json.loads(json.dumps(baseline))
        wrong_command_ref["reservations"][0]["commandResultRef"] = "commands/verify.unit/attempt-1.json"
        wrong_command_ref["commandResultRefs"] = ["commands/verify.unit/attempt-1.json"]
        cases.append((wrong_command_ref, "COMMAND_RESULT_REFERENCE_MISMATCH", "/reservations/0/commandResultRef"))

        wrong_process_ref = json.loads(json.dumps(baseline))
        wrong_process_ref["reservations"][0]["processAttemptRef"] = "process-attempts/verify.unit/attempt-1.json"
        wrong_process_ref["processAttemptRefs"] = ["process-attempts/verify.unit/attempt-1.json"]
        cases.append((wrong_process_ref, "PROCESS_ATTEMPT_REFERENCE_MISMATCH", "/reservations/0/processAttemptRef"))

        for instance, code, path in cases:
            with self.subTest(code=code):
                errors = self.helper_errors("run-session", instance)
                self.assertEqual((errors[0]["code"], errors[0]["instancePath"]), (code, path))

    def test_process_attempt_contract_is_exhaustive_and_secret_free(self):
        exited = self.fixture("process-attempt-exited.json")
        spawned = self.fixture("process-attempt-spawn-failed.json")
        valid_cases = [
            exited,
            spawned,
        ]
        for termination, redaction_status in (
            ("TIMED_OUT", "SCRUBBED"),
            ("TIMED_OUT", "NOT_APPLIED"),
            ("RESOURCE_LIMIT", "NOT_APPLIED"),
        ):
            instance = json.loads(json.dumps(exited))
            instance.update({
                "termination": termination,
                "processExitCode": None,
                "redactionStatus": redaction_status,
                "reason": termination.lower(),
            })
            valid_cases.append(instance)
        unscrubbed = json.loads(json.dumps(exited))
        unscrubbed.update({"redactionStatus": "UNSCRUBBED", "reason": "invalid UTF-8"})
        valid_cases.append(unscrubbed)

        for index, instance in enumerate(valid_cases):
            with self.subTest(valid=index):
                self.assert_schema_valid("process-attempt", instance)
        self.helper.validate(REPOSITORY_ROOT, exited, "ai/schemas/process-attempt.schema.json")

        for field in ("argv", "stdout", "stderr", "environment", "secret"):
            with self.subTest(field=field):
                invalid = json.loads(json.dumps(exited))
                invalid[field] = "forbidden"
                self.assert_schema_invalid("process-attempt", invalid)

        invalid_cases = []
        for field, value in (
            ("startedAt", exited["startedAt"]),
            ("processExitCode", 1),
            ("termination", "EXITED"),
            ("redactionStatus", "SCRUBBED"),
            ("reason", None),
            ("reason", ""),
        ):
            invalid = json.loads(json.dumps(spawned))
            invalid[field] = value
            invalid_cases.append((f"spawn-{field}-{value}", invalid))

        for name, changes in (
            ("launched-spawn-termination", {"termination": "SPAWN_FAILED"}),
            ("exited-null-exit", {"processExitCode": None}),
            ("exited-not-applied", {"redactionStatus": "NOT_APPLIED", "reason": "not applied"}),
            ("exited-scrubbed-reason", {"reason": "unexpected"}),
            ("exited-unscrubbed-null-reason", {"redactionStatus": "UNSCRUBBED", "reason": None}),
            ("exited-unscrubbed-empty-reason", {"redactionStatus": "UNSCRUBBED", "reason": ""}),
            ("timeout-not-applied-null-reason", {"termination": "TIMED_OUT", "processExitCode": None, "redactionStatus": "NOT_APPLIED", "reason": None}),
            ("resource-scrubbed-null-reason", {"termination": "RESOURCE_LIMIT", "processExitCode": None, "redactionStatus": "SCRUBBED", "reason": None}),
        ):
            invalid = json.loads(json.dumps(exited))
            invalid.update(changes)
            invalid_cases.append((name, invalid))

        for name, instance in invalid_cases:
            with self.subTest(invalid=name):
                self.assert_schema_invalid("process-attempt", instance)

        invalid = json.loads(json.dumps(exited))
        invalid["$id"] = ".ai-runs/run-1/process-attempts/verify.unit/other-attempt.json"
        self.assert_helper_invalid("process-attempt", invalid)

    def test_process_attempt_finite_matrix_accepts_exactly_the_approved_combinations(self):
        valid_combinations = {
            ("SPAWN_FAILED", "SPAWN_FAILED", None, "NOT_APPLIED", "NONEMPTY"),
            ("LAUNCHED", "EXITED", 0, "SCRUBBED", "NULL"),
            ("LAUNCHED", "EXITED", 7, "SCRUBBED", "NULL"),
            ("LAUNCHED", "EXITED", 0, "UNSCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "EXITED", 7, "UNSCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "TIMED_OUT", None, "SCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "TIMED_OUT", 0, "SCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "TIMED_OUT", 7, "SCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "TIMED_OUT", None, "NOT_APPLIED", "NONEMPTY"),
            ("LAUNCHED", "TIMED_OUT", 0, "NOT_APPLIED", "NONEMPTY"),
            ("LAUNCHED", "TIMED_OUT", 7, "NOT_APPLIED", "NONEMPTY"),
            ("LAUNCHED", "RESOURCE_LIMIT", None, "SCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "RESOURCE_LIMIT", 0, "SCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "RESOURCE_LIMIT", 7, "SCRUBBED", "NONEMPTY"),
            ("LAUNCHED", "RESOURCE_LIMIT", None, "NOT_APPLIED", "NONEMPTY"),
            ("LAUNCHED", "RESOURCE_LIMIT", 0, "NOT_APPLIED", "NONEMPTY"),
            ("LAUNCHED", "RESOURCE_LIMIT", 7, "NOT_APPLIED", "NONEMPTY"),
        }
        accepted = set()
        baseline = self.fixture("process-attempt-exited.json")
        dimensions = product(
            ("LAUNCHED", "SPAWN_FAILED"),
            ("EXITED", "TIMED_OUT", "RESOURCE_LIMIT", "SPAWN_FAILED"),
            (None, 0, 7),
            ("SCRUBBED", "UNSCRUBBED", "NOT_APPLIED"),
            ("NULL", "NONEMPTY"),
        )
        for combination in dimensions:
            launch_status, termination, process_exit_code, redaction_status, reason_kind = combination
            instance = json.loads(json.dumps(baseline))
            instance.update({
                "launchStatus": launch_status,
                "startedAt": None if launch_status == "SPAWN_FAILED" else baseline["startedAt"],
                "termination": termination,
                "processExitCode": process_exit_code,
                "redactionStatus": redaction_status,
                "reason": None if reason_kind == "NULL" else "matrix reason",
            })
            errors = list(self.validators["process-attempt"].iter_errors(instance))
            if not errors:
                accepted.add(combination)
            else:
                with self.subTest(rejected=combination):
                    self.assertNotIn(combination, valid_combinations)
                    self.assertTrue(
                        {error.validator for error in errors}.intersection({"const", "enum", "type", "minLength"}),
                        "forbidden matrix combination must have a conditional rejection reason",
                    )

        self.assertEqual(accepted, valid_combinations)

    def test_manifest_accepts_zero_byte_logs_and_rejects_negative_or_duplicate_paths(self):
        manifest = self.fixture("artifact-manifest-empty-logs.json")
        self.assert_schema_valid("artifact-manifest", manifest)
        self.helper.validate(REPOSITORY_ROOT, manifest, "ai/schemas/artifact-manifest.schema.json")
        self.assertEqual([item["size"] for item in manifest["artifacts"]], [0, 0])
        self.assert_schema_invalid("artifact-manifest", self.fixture("artifact-manifest-negative-size.json"))

        duplicate = json.loads(json.dumps(manifest))
        duplicate["artifacts"].append({
            "path": duplicate["artifacts"][0]["path"],
            "sha256": "f" * 64,
            "size": 1,
            "kind": "COMMAND_RESULT",
        })
        self.assert_helper_invalid("artifact-manifest", duplicate)

    def test_command_result_compatibility_is_additive_and_phase_1a_fixtures_remain_valid(self):
        for fixture_path in sorted(PHASE_1A_VALID_FIXTURES_PATH.glob("*.json")):
            with self.subTest(fixture=fixture_path.name):
                self.helper.validate_repository_instance(REPOSITORY_ROOT, fixture_path)

        with (PHASE_1A_VALID_FIXTURES_PATH / "command-result.json").open(encoding="utf-8") as handle:
            result = json.load(handle)
        self.assertNotIn("attemptId", result)
        self.assertNotIn("processAttemptRef", result)
        self.assert_schema_valid("command-result", result)

        result["attemptId"] = "attempt-1"
        result["$id"] = ".ai-runs/fixture-run-001/commands/verify.unit/attempt-1.json"
        result["processAttemptRef"] = ".ai-runs/fixture-run-001/process-attempts/verify.unit/attempt-1.json"
        self.assert_schema_valid("command-result", result)
        self.helper.validate_phase_1b2_command_result(result)

        for missing in ("attemptId", "processAttemptRef"):
            with self.subTest(partial=missing):
                partial = json.loads(json.dumps(result))
                partial.pop(missing)
                with self.assertRaises(self.helper.InvalidStateError):
                    self.helper.validate_phase_1b2_command_result(partial)

    def test_b2_command_result_requires_exact_command_and_process_tuple_paths(self):
        with (PHASE_1A_VALID_FIXTURES_PATH / "command-result.json").open(encoding="utf-8") as handle:
            result = json.load(handle)
        result.update({
            "$id": ".ai-runs/fixture-run-001/commands/verify.unit/attempt-1.json",
            "attemptId": "attempt-1",
            "processAttemptRef": ".ai-runs/fixture-run-001/process-attempts/verify.unit/attempt-1.json",
        })
        self.helper.validate(REPOSITORY_ROOT, result, "ai/schemas/command-result.schema.json")

        cases = (
            ("$id", ".ai-runs/other-run/commands/verify.unit/attempt-1.json", "COMMAND_RESULT_REFERENCE_MISMATCH"),
            ("$id", ".ai-runs/fixture-run-001/commands/verify.integration/attempt-1.json", "COMMAND_RESULT_REFERENCE_MISMATCH"),
            ("$id", ".ai-runs/fixture-run-001/commands/verify.unit/attempt-2.json", "COMMAND_RESULT_REFERENCE_MISMATCH"),
            ("processAttemptRef", ".ai-runs/other-run/process-attempts/verify.unit/attempt-1.json", "PROCESS_ATTEMPT_REFERENCE_MISMATCH"),
            ("processAttemptRef", ".ai-runs/fixture-run-001/process-attempts/verify.integration/attempt-1.json", "PROCESS_ATTEMPT_REFERENCE_MISMATCH"),
            ("processAttemptRef", ".ai-runs/fixture-run-001/process-attempts/verify.unit/attempt-2.json", "PROCESS_ATTEMPT_REFERENCE_MISMATCH"),
        )
        for field, value, code in cases:
            with self.subTest(field=field, value=value):
                invalid = json.loads(json.dumps(result))
                invalid[field] = value
                errors = self.helper_errors("command-result", invalid)
                self.assertEqual((errors[0]["code"], errors[0]["instancePath"]), (code, f"/{field}"))

    def test_gateway_semantics_require_exact_run_start_and_post_tuple_refs(self):
        run_start = run_start_pass()
        self.helper.validate(REPOSITORY_ROOT, run_start, "ai/schemas/gateway-result.schema.json")
        invalid = json.loads(json.dumps(run_start))
        invalid["data"]["sessionRef"] = ".ai-runs/other-run/.state/run-session.json"
        errors = self.helper_errors("gateway-result", invalid)
        self.assertEqual(
            (errors[0]["code"], errors[0]["instancePath"]),
            ("RUN_START_SESSION_REFERENCE_MISMATCH", "/data/sessionRef"),
        )

        for result_name, exit_code in (("PASS", 0), ("FAIL", 7), ("BLOCKED", None)):
            baseline = post_command_result(result_name, exit_code)
            self.helper.validate(REPOSITORY_ROOT, baseline, "ai/schemas/gateway-result.schema.json")
            cases = (
                ("commandResultRef", ".ai-runs/other-run/commands/verify.unit/attempt-1.json", "POST_COMMAND_RESULT_REFERENCE_MISMATCH"),
                ("commandResultRef", ".ai-runs/run-1/commands/verify.integration/attempt-1.json", "POST_COMMAND_RESULT_REFERENCE_MISMATCH"),
                ("commandResultRef", ".ai-runs/run-1/commands/verify.unit/attempt-2.json", "POST_COMMAND_RESULT_REFERENCE_MISMATCH"),
                ("processAttemptRef", ".ai-runs/other-run/process-attempts/verify.unit/attempt-1.json", "POST_PROCESS_ATTEMPT_REFERENCE_MISMATCH"),
                ("processAttemptRef", ".ai-runs/run-1/process-attempts/verify.integration/attempt-1.json", "POST_PROCESS_ATTEMPT_REFERENCE_MISMATCH"),
                ("processAttemptRef", ".ai-runs/run-1/process-attempts/verify.unit/attempt-2.json", "POST_PROCESS_ATTEMPT_REFERENCE_MISMATCH"),
            )
            for field, value, code in cases:
                with self.subTest(result=result_name, field=field, value=value):
                    invalid = json.loads(json.dumps(baseline))
                    invalid["data"][field] = value
                    errors = self.helper_errors("gateway-result", invalid)
                    self.assertEqual(
                        (errors[0]["code"], errors[0]["instancePath"]),
                        (code, f"/data/{field}"),
                    )


class WorkflowHelperPreflightTests(unittest.TestCase):
    def assert_invalid_publication_preserves_operation(self, operation):
        helper = load_helper()
        malformed = helper.gateway_result(
            "PASS",
            None,
            {"unexpected": "shape"},
            operation=operation,
        )

        result, status = helper.publish_result(REPOSITORY_ROOT, malformed, 0)

        self.assertEqual((result["operation"], result["result"], status), (operation, "INVALID_STATE", 5))
        self.assertEqual(result["reason"], "GATEWAY_RESULT_SCHEMA_INVALID")
        self.assertIsNone(result["data"])
        helper.validate(REPOSITORY_ROOT, result, "ai/schemas/gateway-result.schema.json")

    def test_publication_fallback_preserves_run_start(self):
        self.assert_invalid_publication_preserves_operation("RUN_START")

    def test_publication_fallback_preserves_pre_command(self):
        self.assert_invalid_publication_preserves_operation("PRE_COMMAND")

    def test_publication_fallback_preserves_post_command(self):
        self.assert_invalid_publication_preserves_operation("POST_COMMAND")

    def test_module_contract_describes_the_closed_phase_1b2_gateway(self):
        helper = load_helper()

        self.assertEqual(
            helper.__doc__,
            "Phase 1B helper owns closed gateway validation and POSIX-only command orchestration.",
        )

    def test_preflight_reports_validated_python_and_validator_capabilities_without_an_executable_path(self):
        helper = load_helper()
        result, status = helper.run_preflight(SimpleNamespace(
            repository_root=str(REPOSITORY_ROOT),
            runtime_command="python3",
            record=False,
        ))

        self.assertEqual(status, 0)
        self.assertEqual(result["operation"], "PREFLIGHT")
        self.assertEqual(result["result"], "PASS")
        self.assertTrue(result["data"]["pythonVersion"].startswith("3"))
        self.assertTrue(result["data"]["jsonschemaVersion"])
        self.assertEqual(result["data"]["validator"], "Draft202012Validator")
        self.assertIs(result["data"]["formatChecker"], True)
        self.assertNotIn(str(helper.sys.executable), json.dumps(result, sort_keys=True))

        with GATEWAY_SCHEMA_PATH.open(encoding="utf-8") as handle:
            schema = json.load(handle)
        self.assertEqual(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(result)), [])

    def test_malformed_result_is_replaced_with_invalid_state_before_publication(self):
        helper = load_helper()
        malformed = helper.gateway_result("PASS", None, {"unexpected": "data"})

        result, status = helper.publish_result(REPOSITORY_ROOT, malformed, 0)

        self.assertEqual(status, 5)
        self.assertEqual(result["operation"], "PREFLIGHT")
        self.assertEqual(result["result"], "INVALID_STATE")
        self.assertEqual(result["reason"], "GATEWAY_RESULT_SCHEMA_INVALID")

    def test_publication_fallback_does_not_depend_on_a_monkeypatched_result_factory(self):
        helper = load_helper()
        original = helper.gateway_result

        def malformed_factory(result, reason, data=None):
            if reason == "TRIGGER_MALFORMED_RESULT":
                return {"result": result, "reason": reason}
            return original(result, reason, data)

        helper.gateway_result = malformed_factory
        malformed = helper.gateway_result("NOT_CONFIGURED", "TRIGGER_MALFORMED_RESULT")

        result, status = helper.publish_result(REPOSITORY_ROOT, malformed, 3)

        self.assertEqual((result["result"], result["reason"], status), (
            "INVALID_STATE",
            "GATEWAY_RESULT_SCHEMA_INVALID",
            5,
        ))

    def test_publication_fails_closed_when_the_approved_gateway_schema_identity_is_tampered(self):
        helper = load_helper()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shutil.copytree(REPOSITORY_ROOT / "ai" / "schemas", root / "ai" / "schemas")
            schema_path = root / "ai" / "schemas" / "gateway-result.schema.json"
            with schema_path.open(encoding="utf-8") as handle:
                schema = json.load(handle)
            schema["$id"] = "urn:caller-selected:gateway-result:v1"
            schema_path.write_text(json.dumps(schema), encoding="utf-8")

            result, status = helper.publish_result(root, preflight_pass(), 0)

        self.assertEqual(status, 5)
        self.assertEqual(result["result"], "INVALID_STATE")
        self.assertEqual(result["reason"], "GATEWAY_RESULT_SCHEMA_INVALID")


class StrictJsonAndSchemaValidationTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def temporary_repository(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "ai").mkdir()
        shutil.copytree(REPOSITORY_ROOT / "ai" / "schemas", root / "ai" / "schemas")
        self.addCleanup(temporary.cleanup)
        return root

    def write_json(self, root, relative_path, value):
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def write_valid_registry_instance(self, root):
        destination = root / "instance.json"
        shutil.copyfile(PHASE_1A_VALID_FIXTURES_PATH / "command-registry.json", destination)
        return destination

    def mutate_approved_schema(self, root, mutate):
        path = root / "ai" / "schemas" / "command-registry.schema.json"
        with path.open(encoding="utf-8") as handle:
            schema = json.load(handle)
        mutate(schema)
        path.write_text(json.dumps(schema), encoding="utf-8")
        return path

    def assert_invalid_state(self, path, expected_code=None, root=REPOSITORY_ROOT):
        with self.assertRaises(self.helper.InvalidStateError) as raised:
            self.helper.validate_repository_instance(root, path)
        self.assertEqual(raised.exception.result, "INVALID_STATE")
        self.assertTrue(raised.exception.errors)
        if expected_code is not None:
            self.assertEqual(raised.exception.errors[0]["code"], expected_code)
        return raised.exception.errors

    def test_duplicate_object_keys_are_rejected_by_the_strict_loader(self):
        errors = self.assert_invalid_state(
            STRICT_JSON_FIXTURES_PATH / "duplicate-key.json",
            "DUPLICATE_JSON_KEY",
        )
        self.assertEqual(errors[0]["instancePath"], "")
        self.assertEqual(errors[0]["schemaPath"], "")
        self.assertNotIn("schemaVersion", errors[0]["message"])

    def test_every_non_finite_json_constant_is_rejected(self):
        self.assert_invalid_state(
            STRICT_JSON_FIXTURES_PATH / "non-finite.json",
            "NON_FINITE_JSON_NUMBER",
        )

        for constant in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(constant=constant):
                root = self.temporary_repository()
                path = root / "constant.json"
                path.write_text('{"value": ' + constant + "}", encoding="utf-8")
                self.assert_invalid_state(path, "NON_FINITE_JSON_NUMBER", root)

    def test_format_checker_rejects_an_invalid_calendar_timestamp(self):
        path = PHASE_1A_INVALID_FIXTURES_PATH / "project-state-malformed-utc-timestamp.json"
        errors = self.assert_invalid_state(path)

        self.assertIn("SCHEMA_VALIDATION_ERROR", {error["code"] for error in errors})
        self.assertIn("/updatedAt", {error["instancePath"] for error in errors})

    def test_unsupported_instance_schema_and_version_fail_closed(self):
        root = self.temporary_repository()
        unsupported_schema = self.write_json(root, "instance.json", {
            "$schema": "ai/schemas/caller-selected.schema.json",
            "$id": "ai/instance.json",
            "schemaVersion": 1,
        })
        self.assert_invalid_state(unsupported_schema, "UNSUPPORTED_INSTANCE_SCHEMA", root)

        unsupported_version = PHASE_1A_INVALID_FIXTURES_PATH / "command-registry-unknown-version.json"
        self.assert_invalid_state(unsupported_version, "UNSUPPORTED_SCHEMA_VERSION")

    def test_schema_selection_uses_only_the_internal_allowlist(self):
        root = self.temporary_repository()
        caller_schema = root / "caller-selected.schema.json"
        caller_schema.write_text(json.dumps({}), encoding="utf-8")
        instance = self.write_json(root, "instance.json", {
            "$schema": "caller-selected.schema.json",
            "$id": "ai/instance.json",
            "schemaVersion": 1,
        })

        errors = self.assert_invalid_state(instance, "UNSUPPORTED_INSTANCE_SCHEMA", root)
        self.assertEqual(errors[0]["instancePath"], "/$schema")

    def test_internal_validation_rejects_an_arbitrary_caller_schema_path(self):
        root = self.temporary_repository()
        caller_schema = self.write_json(root, "caller-selected.schema.json", {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:caller-selected:v1",
            "schemaVersion": 1,
            "type": "object",
        })

        with self.assertRaises(self.helper.InvalidStateError) as raised:
            self.helper.validate(root, {}, caller_schema.relative_to(root).as_posix())

        self.assertEqual(raised.exception.errors[0]["code"], "UNAPPROVED_SCHEMA_PATH")

    def test_approved_schema_metadata_must_match_draft_urn_and_version(self):
        cases = (
            ("$schema", "https://json-schema.org/draft/2019-09/schema", "SCHEMA_DRAFT_MISMATCH", "/$schema"),
            ("$id", "urn:sparta-ch6-advanced:ai-workflow:schema:other:v1", "SCHEMA_ID_MISMATCH", "/$id"),
            ("schemaVersion", 2, "SCHEMA_VERSION_MISMATCH", "/schemaVersion"),
        )
        for field, value, expected_code, expected_path in cases:
            with self.subTest(field=field):
                root = self.temporary_repository()
                self.mutate_approved_schema(root, lambda schema, field=field, value=value: schema.__setitem__(field, value))
                instance = self.write_valid_registry_instance(root)

                errors = self.assert_invalid_state(instance, expected_code, root)
                self.assertEqual(errors[0]["schemaPath"], expected_path)

    def test_external_schema_references_are_rejected_with_the_full_nested_pointer(self):
        cases = (
            ("$ref", "file:///tmp/caller-selected.schema.json"),
            ("$ref", "https://example.invalid/caller-selected.schema.json"),
            ("$dynamicRef", "../caller-selected.schema.json"),
            ("$dynamicRef", "https://example.invalid/dynamic.schema.json"),
        )
        for keyword, reference in cases:
            with self.subTest(keyword=keyword, reference=reference):
                root = self.temporary_repository()

                def add_external_reference(schema, keyword=keyword, reference=reference):
                    schema["properties"]["value"] = {keyword: reference}

                self.mutate_approved_schema(root, add_external_reference)
                instance = self.write_valid_registry_instance(root)

                errors = self.assert_invalid_state(instance, "EXTERNAL_SCHEMA_REFERENCE", root)
                self.assertEqual(errors[0]["schemaPath"], f"/properties/value/{keyword}")

    def test_schema_self_check_failure_is_invalid_state(self):
        root = self.temporary_repository()
        schema_path = root / "ai" / "schemas" / "command-registry.schema.json"
        schema_path.write_text(json.dumps({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "urn:sparta-ch6-advanced:ai-workflow:schema:command-registry:v1",
            "schemaVersion": 1,
            "type": "not-a-json-schema-type",
        }), encoding="utf-8")
        instance = self.write_json(root, "instance.json", {
            "$schema": "ai/schemas/command-registry.schema.json",
            "$id": "ai/command-registry.json",
            "schemaVersion": 1,
            "updatedAt": "2026-07-11T00:00:00Z",
            "commands": [],
        })

        self.assert_invalid_state(instance, "SCHEMA_SELF_CHECK_FAILED", root)

    def test_validation_errors_are_stable_and_deterministically_ordered(self):
        root = self.temporary_repository()
        with (PHASE_1A_VALID_FIXTURES_PATH / "command-registry.json").open(encoding="utf-8") as handle:
            instance = json.load(handle)
        instance["commands"][0]["configurationStatus"] = "BROKEN_STATUS"
        instance["commands"][0]["classification"] = "BROKEN_CLASSIFICATION"
        path = self.write_json(root, "invalid-registry.json", instance)

        first = self.assert_invalid_state(path, root=root)
        second = self.assert_invalid_state(path, root=root)

        self.assertEqual(first, second)
        self.assertEqual(
            first,
            sorted(first, key=lambda error: (
                error["instancePath"],
                error["schemaPath"],
                error["code"],
                error["message"],
            )),
        )
        self.assertEqual({error["code"] for error in first}, {"SCHEMA_VALIDATION_ERROR"})
        self.assertEqual(
            {error["instancePath"] for error in first},
            {"/commands/0/classification", "/commands/0/configurationStatus"},
        )

    def test_all_phase_1a_valid_fixtures_validate(self):
        fixture_paths = sorted(PHASE_1A_VALID_FIXTURES_PATH.glob("*.json"))
        self.assertEqual(len(fixture_paths), 9)

        for fixture_path in fixture_paths:
            with self.subTest(fixture=fixture_path.name):
                instance = self.helper.validate_repository_instance(REPOSITORY_ROOT, fixture_path)
                self.assertEqual(instance["schemaVersion"], 1)

    def test_all_phase_1a_invalid_fixtures_fail_as_invalid_state(self):
        fixture_paths = sorted(PHASE_1A_INVALID_FIXTURES_PATH.glob("*.json"))
        self.assertEqual(len(fixture_paths), 24)

        for fixture_path in fixture_paths:
            with self.subTest(fixture=fixture_path.name):
                self.assert_invalid_state(fixture_path)


class RegistrySemanticValidationTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def temporary_repository(self):
        temporary = tempfile.TemporaryDirectory()
        root = Path(temporary.name)
        (root / "ai").mkdir()
        shutil.copytree(REPOSITORY_ROOT / "ai" / "schemas", root / "ai" / "schemas")
        (root / "gradlew").write_text("fixture wrapper\n", encoding="utf-8")
        self.addCleanup(temporary.cleanup)
        return root

    def registry(self):
        with (REGISTRY_FIXTURES_PATH / "valid-parameterized.json").open(encoding="utf-8") as handle:
            return json.load(handle)

    def command(self, registry, command_id="verify.unit-class"):
        return next(item for item in registry["commands"] if item["id"] == command_id)

    def write_registry(self, root, registry):
        path = root / "registry.json"
        path.write_text(json.dumps(registry), encoding="utf-8")
        return path

    def assert_semantic_invalid(self, root, registry, expected_code, expected_path):
        with self.assertRaises(self.helper.InvalidStateError) as raised:
            self.helper.validate_registry_semantics(root, registry)
        self.assertEqual(raised.exception.result, "INVALID_STATE")
        self.assertEqual(raised.exception.errors[0]["code"], expected_code)
        self.assertEqual(raised.exception.errors[0]["instancePath"], expected_path)
        self.assertEqual(
            raised.exception.errors,
            sorted(raised.exception.errors, key=lambda error: (
                error["instancePath"], error["schemaPath"], error["code"], error["message"],
            )),
        )

    def test_phase_1a_semantic_invalid_fixtures_are_rejected_with_stable_paths(self):
        cases = (
            ("command-registry-duplicate-id.json", "DUPLICATE_COMMAND_ID", "/commands/1/id"),
            ("command-registry-parameter-required-mismatch.json", "PARAMETER_KEYS_MISMATCH", "/commands/0/parameters/schema"),
        )
        for fixture_name, expected_code, expected_path in cases:
            with self.subTest(fixture=fixture_name):
                root = self.temporary_repository()
                fixture = PHASE_1A_SEMANTIC_INVALID_FIXTURES_PATH / fixture_name
                registry = self.helper.validate_repository_instance(REPOSITORY_ROOT, fixture)
                self.assert_semantic_invalid(root, registry, expected_code, expected_path)

    def test_placeholder_tokens_must_be_closed_declared_and_enabled(self):
        cases = (
            ("partial", "test-{{testClass}}", "INVALID_PLACEHOLDER", "/commands/0/argv/3"),
            ("malformed", "{{}}", "INVALID_PLACEHOLDER", "/commands/0/argv/3"),
            ("undeclared", "{{missingClass}}", "PLACEHOLDER_PARAMETER_MISMATCH", "/commands/0/parameters/schema"),
            ("disabled", "{{testClass}}", "PLACEHOLDER_PARAMETERS_DISABLED", "/commands/0/argv/3"),
            ("unresolved", "{{testClass", "INVALID_PLACEHOLDER", "/commands/0/argv/3"),
        )
        for name, token, expected_code, expected_path in cases:
            with self.subTest(case=name):
                root = self.temporary_repository()
                registry = self.registry()
                command = self.command(registry)
                command["argv"][3] = token
                if name == "disabled":
                    command["parameters"] = {"allowed": False, "schema": None}
                self.assert_semantic_invalid(root, registry, expected_code, expected_path)

        root = self.temporary_repository()
        registry = self.registry()
        command = self.command(registry)
        command["argv"].append("{{testClass}}")
        self.assertEqual(self.helper.validate_registry_semantics(root, registry)["verify.unit-class"], [])

    def test_parameter_patterns_use_only_the_anchored_safe_subset(self):
        cases = (
            ("unanchored", "[A-Za-z]+", "PARAMETER_PATTERN_UNANCHORED"),
            ("non-compiling", "^[A-Za-z+$", "PARAMETER_PATTERN_INVALID"),
            ("raw-internal-start-anchor", "^a^b$", "UNSAFE_PARAMETER_PATTERN"),
            ("raw-internal-end-anchor", "^a$b$", "UNSAFE_PARAMETER_PATTERN"),
            ("parentheses", "^(a)+$", "UNSAFE_PARAMETER_PATTERN"),
            ("alternation", "^a|b$", "UNSAFE_PARAMETER_PATTERN"),
            ("counted", "^a{1,2}$", "UNSAFE_PARAMETER_PATTERN"),
            ("backreference", "^(a)\\1$", "UNSAFE_PARAMETER_PATTERN"),
            ("lookaround", "^(?=a)a$", "UNSAFE_PARAMETER_PATTERN"),
            ("flags", "(?i)^a$", "PARAMETER_PATTERN_UNANCHORED"),
            ("conditional", "^(?(1)a|b)$", "UNSAFE_PARAMETER_PATTERN"),
            ("nested", "^a++$", "UNSAFE_PARAMETER_PATTERN"),
            ("catastrophic", "^(a*)+$", "UNSAFE_PARAMETER_PATTERN"),
        )
        for name, pattern, expected_code in cases:
            with self.subTest(case=name):
                root = self.temporary_repository()
                registry = self.registry()
                self.command(registry)["parameters"]["schema"]["properties"]["testClass"]["pattern"] = pattern
                self.assert_semantic_invalid(
                    root,
                    registry,
                    expected_code,
                    "/commands/0/parameters/schema/properties/testClass/pattern",
                )

    def test_semantic_executable_allowlist_rejects_gradlew_bat_and_other_argv_zero(self):
        for executable in ("./gradlew.bat", "gradlew.bat", "./mvnw"):
            with self.subTest(executable=executable):
                root = self.temporary_repository()
                registry = self.registry()
                self.command(registry)["argv"][0] = executable
                self.assert_semantic_invalid(root, registry, "UNSUPPORTED_EXECUTABLE", "/commands/0/argv/0")

    def test_prerequisites_reject_unknown_self_and_cycles_and_have_a_stable_topological_order(self):
        cases = (
            ("unknown", ["verify.missing"], "UNKNOWN_PREREQUISITE", "/commands/0/prerequisites/0"),
            ("self", ["verify.unit-class"], "SELF_PREREQUISITE", "/commands/0/prerequisites/0"),
        )
        for name, prerequisites, expected_code, expected_path in cases:
            with self.subTest(case=name):
                root = self.temporary_repository()
                registry = self.registry()
                self.command(registry)["prerequisites"] = prerequisites
                self.assert_semantic_invalid(root, registry, expected_code, expected_path)

        root = self.temporary_repository()
        registry = self.registry()
        second = json.loads(json.dumps(self.command(registry)))
        second["id"] = "verify.compile"
        second["prerequisites"] = ["verify.unit-class"]
        registry["commands"].append(second)
        self.command(registry)["prerequisites"] = ["verify.compile"]
        self.assert_semantic_invalid(root, registry, "CYCLIC_PREREQUISITE", "/commands/0/prerequisites")

        root = self.temporary_repository()
        registry = self.registry()
        assets = json.loads(json.dumps(self.command(registry)))
        assets["id"] = "verify.assets"
        assets["prerequisites"] = []
        compile_command = json.loads(json.dumps(self.command(registry)))
        compile_command["id"] = "verify.compile"
        compile_command["prerequisites"] = ["verify.assets"]
        self.command(registry)["prerequisites"] = ["verify.compile", "verify.assets"]
        registry["commands"].extend((assets, compile_command))
        order = self.helper.validate_registry_semantics(root, registry)["verify.unit-class"]
        self.assertEqual(order, ["verify.assets", "verify.compile"])

    def test_configured_non_symlink_working_directory_and_wrapper_pass(self):
        root = self.temporary_repository()
        registry = self.registry()
        (root / "work").mkdir()
        (root / "work" / "gradlew").write_text("fixture wrapper\n", encoding="utf-8")
        self.command(registry)["workingDirectory"] = "work"
        self.assertEqual(self.helper.validate_registry_semantics(root, registry)["verify.unit-class"], [])

    def test_missing_working_directory_is_invalid_state(self):
        root = self.temporary_repository()
        registry = self.registry()
        self.command(registry)["workingDirectory"] = "missing"
        self.assert_semantic_invalid(root, registry, "WORKING_DIRECTORY_MISSING", "/commands/0/workingDirectory")

    def test_missing_non_root_wrapper_is_blocked_when_static_evidence_matches(self):
        root = self.temporary_repository()
        registry = self.registry()
        (root / "work").mkdir()
        command = self.command(registry)
        command["workingDirectory"] = "work"
        command["evidence"][0]["path"] = "work/gradlew"
        with self.assertRaises(self.helper.RegistryBlockedError) as raised:
            self.helper.validate_registry_semantics(root, registry)
        self.assertEqual(raised.exception.result, "BLOCKED")
        self.assertEqual(raised.exception.errors[0]["code"], "WRAPPER_STATIC_EVIDENCE_MISSING")
        self.assertEqual(raised.exception.errors[0]["instancePath"], "/commands/0/argv/0")

    def test_missing_non_root_wrapper_is_invalid_when_static_evidence_targets_root_wrapper(self):
        root = self.temporary_repository()
        registry = self.registry()
        (root / "work").mkdir()
        command = self.command(registry)
        command["workingDirectory"] = "work"
        command["evidence"][0]["path"] = "gradlew"
        self.assert_semantic_invalid(root, registry, "WRAPPER_MISSING", "/commands/0/argv/0")

    def test_working_directory_symlink_escape_is_invalid_state_where_supported(self):
        root = self.temporary_repository()
        registry = self.registry()
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        try:
            (root / "escaped").symlink_to(outside, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("directory symlinks are unavailable in this test environment")
        self.command(registry)["workingDirectory"] = "escaped"
        self.assert_semantic_invalid(root, registry, "WORKING_DIRECTORY_OUTSIDE_REPOSITORY", "/commands/0/workingDirectory")

    def test_wrapper_symlink_escape_is_invalid_state_where_supported(self):
        root = self.temporary_repository()
        registry = self.registry()
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        external_wrapper = outside / "gradlew"
        external_wrapper.write_text("external fixture wrapper\n", encoding="utf-8")
        try:
            (root / "gradlew").unlink()
            (root / "gradlew").symlink_to(external_wrapper)
        except (NotImplementedError, OSError):
            self.skipTest("file symlinks are unavailable in this test environment")
        self.assert_semantic_invalid(root, registry, "WRAPPER_OUTSIDE_REPOSITORY", "/commands/0/argv/0")

    def test_schema_and_semantic_validation_complete_before_lookup(self):
        root = self.temporary_repository()
        fixture = PHASE_1A_SEMANTIC_INVALID_FIXTURES_PATH / "command-registry-duplicate-id.json"
        registry_path = self.write_registry(root, json.loads(fixture.read_text(encoding="utf-8")))

        with self.assertRaises(self.helper.InvalidStateError) as raised:
            self.helper.find_registry_command(root, registry_path, "verify.missing")

        self.assertEqual(raised.exception.errors[0]["code"], "DUPLICATE_COMMAND_ID")


class ProjectStateSummaryTests(unittest.TestCase):
    def test_full_generated_summary_is_deterministic_and_derived_from_canonical_state(self):
        helper = load_helper()
        existing = """# AI Workflow Project State

## Human Policy Notes

Human-authored fixture policy remains untouched.

<!-- GENERATED:START source=ai/project-state.json -->
stale generated content
<!-- GENERATED:END source=ai/project-state.json -->
"""
        state = {
            "$schema": "./schemas/project-state.schema.json",
            "$id": "ai/project-state.json",
            "schemaVersion": 1,
            "updatedAt": "2026-07-11T01:02:03Z",
            "project": {
                "name": "fixture-project",
                "productType": "fixture product",
                "mainLanguage": "FixtureLang 1",
                "framework": "Fixture Framework",
                "buildSystem": "Fixture Build",
            },
            "facts": [{
                "id": "fixture.fact",
                "value": "fixture value",
                "confidence": "CONFIRMED",
                "evidence": [{"kind": "STATIC_FILE", "path": "fixture.txt", "claim": "fixture fact source"}],
                "observedAt": "2026-07-10T00:00:00Z",
            }],
            "importantPaths": [{"purpose": "Fixture sources", "path": "src/fixture"}],
            "ports": [{
                "service": "application",
                "value": 8080,
                "confidence": "INFERRED",
                "evidence": [{"kind": "STATIC_FILE", "path": "application.yml", "claim": "default port"}],
            }],
            "environments": [
                {"kind": "LOCAL", "configurationStatus": "VERIFIED", "notes": ["fixture local note"]},
                {"kind": "CI", "configurationStatus": "NOT_CONFIGURED", "notes": []},
            ],
            "helperRuntimes": [
                {
                    "environment": "LOCAL",
                    "targetRuntime": "Python 3",
                    "detectedRuntime": "Python 3",
                    "configurationStatus": "VERIFIED",
                    "version": "3.fixture",
                    "evidence": [{
                        "kind": "RUNTIME_COMMAND",
                        "path": "ai/evidence/local-helper-runtime.json",
                        "claim": "recorded fixture runtime",
                    }],
                },
                {
                    "environment": "CI",
                    "targetRuntime": "Python 3",
                    "detectedRuntime": None,
                    "configurationStatus": "NOT_CONFIGURED",
                    "version": None,
                    "evidence": [],
                },
            ],
            "commandRegistryRef": "ai/command-registry.json",
            "cacheInvalidationInputs": ["build.gradle", ".github/**"],
        }
        expected = """# AI Workflow Project State

## Human Policy Notes

Human-authored fixture policy remains untouched.

<!-- GENERATED:START source=ai/project-state.json -->
## Generated State Summary

Canonical source: `ai/project-state.json`
Schema version: `1`
Updated at: `2026-07-11T01:02:03Z`

This section was manually bootstrapped from canonical JSON during Phase 1A.
Automatic generation and stale-state validation begin in Phase 1B or later.
This section cannot be changed independently of its canonical JSON source.

### Project Summary

| Field | Value |
|---|---|
| Name | fixture-project |
| Product Type | fixture product |
| Main Language | FixtureLang 1 |
| Framework | Fixture Framework |
| Build System | Fixture Build |

#### Facts

| ID | Value | Confidence | Observed At | Evidence |
|---|---|---|---|---|
| fixture.fact | fixture value | CONFIRMED | 2026-07-10T00:00:00Z | STATIC_FILE: fixture.txt (fixture fact source) |

### Important Paths

| Purpose | Path |
|---|---|
| Fixture sources | src/fixture |

### Known Ports

| Service | Port | Evidence |
|---|---|---|
| application | 8080 (INFERRED) | STATIC_FILE: application.yml (default port) |

### Environment State

| Environment | Configuration Status | Notes |
|---|---|---|
| LOCAL | VERIFIED | fixture local note |
| CI | NOT_CONFIGURED | N/A |

### Helper Runtime State

| Environment | Target | Detected | Configuration Status | Version | Evidence |
|---|---|---|---|---|---|
| LOCAL | Python 3 | Python 3 | VERIFIED | 3.fixture | RUNTIME_COMMAND: ai/evidence/local-helper-runtime.json (recorded fixture runtime) |
| CI | Python 3 | N/A | NOT_CONFIGURED | N/A | N/A |

### Command Registry Reference

- `ai/command-registry.json`

### Cache Invalidation Inputs

- `build.gradle`
- `.github/**`
<!-- GENERATED:END source=ai/project-state.json -->
"""

        actual = helper.summary_for(existing, state)

        self.assertEqual(actual, expected)
        for heading in (
            "### Project Summary",
            "### Important Paths",
            "### Known Ports",
            "### Environment State",
            "### Helper Runtime State",
            "### Command Registry Reference",
            "### Cache Invalidation Inputs",
        ):
            self.assertEqual(actual.count(heading), 1)


class PureResolutionTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        temporary = tempfile.TemporaryDirectory()
        self.root = Path(temporary.name)
        self.addCleanup(temporary.cleanup)
        shutil.copytree(REPOSITORY_ROOT / "ai" / "schemas", self.root / "ai" / "schemas")
        (self.root / "gradlew").write_text("fixture wrapper\n", encoding="utf-8")
        self.state = json.loads((REPOSITORY_ROOT / "ai" / "project-state.json").read_text(encoding="utf-8"))
        self.runtime_evidence = self.helper.current_evidence(
            "python",
            self.helper.sys.version,
            self.helper.package_version("jsonschema"),
            self.helper.digest(Path(self.helper.sys.executable)),
        )
        local_runtime = next(item for item in self.state["helperRuntimes"] if item["environment"] == "LOCAL")
        local_runtime.update({
            "targetRuntime": self.runtime_evidence["targetRuntime"],
            "detectedRuntime": self.runtime_evidence["detectedRuntime"],
            "configurationStatus": "VERIFIED",
            "version": self.runtime_evidence["version"],
            "evidence": [{
                "kind": "RUNTIME_COMMAND",
                "path": "ai/evidence/local-helper-runtime.json",
                "claim": "fixture current helper runtime evidence",
            }],
        })
        local_environment = next(item for item in self.state["environments"] if item["kind"] == "LOCAL")
        local_environment.update({"configurationStatus": "VERIFIED", "notes": ["fixture recorded preflight"]})
        self.state_path = self.write_json("ai/project-state.json", self.state)
        self.evidence_path = self.write_json(
            "ai/evidence/local-helper-runtime.json",
            self.runtime_evidence,
        )
        self.registry = json.loads((REPOSITORY_ROOT / "ai" / "command-registry.json").read_text(encoding="utf-8"))
        self.registry_path = self.write_json("ai/command-registry.json", self.registry)

    def write_json(self, relative_path, value):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def command(self, command_id="verify.unit"):
        return next(command for command in self.registry["commands"] if command["id"] == command_id)

    def save_registry(self):
        self.registry_path.write_text(json.dumps(self.registry), encoding="utf-8")

    def save_state(self):
        self.state_path.write_text(json.dumps(self.state), encoding="utf-8")

    def save_evidence(self):
        self.evidence_path.write_text(json.dumps(self.runtime_evidence), encoding="utf-8")

    def current_preflight(self):
        result, status = self.helper.run_current_preflight(self.root)
        self.helper.validate(self.root, result, "ai/schemas/gateway-result.schema.json")
        return result, status

    def resolve(self, command_id="verify.unit", parameters_path=None):
        result, status = self.helper.resolve_command(
            self.root,
            self.state_path,
            self.registry_path,
            command_id,
            parameters_path,
        )
        self.helper.validate(self.root, result, "ai/schemas/gateway-result.schema.json")
        return result, status

    def enable_parameters(self, pattern="^.+$"):
        command = self.command()
        command["argv"] = ["./gradlew", "test", "--tests", "{{testClass}}"]
        command["parameters"] = {
            "allowed": True,
            "schema": {
                "type": "object",
                "additionalProperties": False,
                "required": ["testClass"],
                "properties": {"testClass": {"type": "string", "pattern": pattern}},
            },
        }
        self.save_registry()

    def parameter_fixture(self, name):
        destination = self.root / "parameters" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(PARAMETER_FIXTURES_PATH / name, destination)
        return destination.relative_to(self.root).as_posix()

    def invoke_resolve_cli(self, output, root=None):
        root = self.root if root is None else root
        arguments = [
            "workflow_helper.py", "resolve", "--repository-root", str(root),
            "--registry", "ai/command-registry.json", "--command-id", "verify.unit", "--output", output,
        ]
        stdout = io.StringIO()
        previous_argv = sys.argv
        try:
            sys.argv = arguments
            with contextlib.redirect_stdout(stdout):
                status = self.helper.main()
        finally:
            sys.argv = previous_argv
        return stdout.getvalue(), status

    def test_canonical_safe_command_resolves_to_an_argv_list(self):
        result, status = self.resolve()

        self.assertEqual(status, 0)
        self.assertEqual(result["result"], "PASS")
        self.assertEqual(result["data"]["argv"], ["./gradlew", "test"])
        self.assertIsInstance(result["data"]["argv"], list)

    def test_public_resolve_preflight_matches_durable_state_without_hardcoded_runtime_identity(self):
        before = tuple(path.read_bytes() for path in (self.evidence_path, self.state_path))

        result, status = self.current_preflight()

        self.assertEqual((result["operation"], result["result"], status), ("PREFLIGHT", "PASS", 0))
        self.assertEqual(result["data"]["runtimeCommand"], "python")
        self.assertEqual(result["data"]["runtimeExecutableHash"], self.runtime_evidence["interpreterSha256"])
        self.assertEqual(tuple(path.read_bytes() for path in (self.evidence_path, self.state_path)), before)

    def test_public_resolve_preflight_blocks_missing_evidence_or_state_claim_without_mutation(self):
        before_state = self.state_path.read_bytes()
        self.evidence_path.unlink()

        result, status = self.current_preflight()

        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(self.state_path.read_bytes(), before_state)

        self.save_evidence()
        self.state["helperRuntimes"] = [
            item for item in self.state["helperRuntimes"] if item["environment"] != "LOCAL"
        ]
        self.save_state()
        before = tuple(path.read_bytes() for path in (self.evidence_path, self.state_path))

        result, status = self.current_preflight()

        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(tuple(path.read_bytes() for path in (self.evidence_path, self.state_path)), before)

    def test_public_resolve_preflight_blocks_schema_valid_current_capability_mismatches(self):
        baseline = json.loads(json.dumps(self.runtime_evidence))
        cases = (
            ("interpreterSha256", "0" * 64),
            ("version", "3.99 fixture mismatch"),
            ("jsonschemaVersion", "99.0.0-fixture"),
        )
        for field, value in cases:
            with self.subTest(field=field):
                self.runtime_evidence = json.loads(json.dumps(baseline))
                self.runtime_evidence[field] = value
                self.save_evidence()
                before = tuple(path.read_bytes() for path in (self.evidence_path, self.state_path))

                result, status = self.current_preflight()

                self.assertEqual((result["result"], status), ("BLOCKED", 2))
                self.assertEqual(tuple(path.read_bytes() for path in (self.evidence_path, self.state_path)), before)

    def test_public_resolve_preflight_blocks_schema_valid_state_status_version_and_reference_mismatches(self):
        baseline = json.loads(json.dumps(self.state))

        def stale_environment(state):
            next(item for item in state["environments"] if item["kind"] == "LOCAL")["configurationStatus"] = "STALE"

        def stale_runtime_version(state):
            next(item for item in state["helperRuntimes"] if item["environment"] == "LOCAL")["version"] = "3.99 fixture mismatch"

        def missing_runtime_reference(state):
            runtime = next(item for item in state["helperRuntimes"] if item["environment"] == "LOCAL")
            runtime.update({
                "configurationStatus": "CONFIGURED_UNVERIFIED",
                "evidence": [{"kind": "STATIC_FILE", "path": "AGENTS.md", "claim": "fixture only"}],
            })

        for name, mutate in (
            ("environment-status", stale_environment),
            ("runtime-version", stale_runtime_version),
            ("evidence-reference", missing_runtime_reference),
        ):
            with self.subTest(case=name):
                self.state = json.loads(json.dumps(baseline))
                mutate(self.state)
                self.save_state()
                before = tuple(path.read_bytes() for path in (self.evidence_path, self.state_path))

                result, status = self.current_preflight()

                self.assertEqual((result["result"], status), ("BLOCKED", 2))
                self.assertEqual(tuple(path.read_bytes() for path in (self.evidence_path, self.state_path)), before)

    def test_public_resolve_preflight_rejects_malformed_evidence_and_state(self):
        self.evidence_path.write_text('{"environment":"LOCAL"}', encoding="utf-8")
        before_state = self.state_path.read_bytes()

        result, status = self.current_preflight()

        self.assertEqual((result["result"], status), ("INVALID_STATE", 5))
        self.assertEqual(self.state_path.read_bytes(), before_state)

        self.save_evidence()
        self.state["schemaVersion"] = 2
        self.save_state()
        before = tuple(path.read_bytes() for path in (self.evidence_path, self.state_path))

        result, status = self.current_preflight()

        self.assertEqual((result["result"], status), ("INVALID_STATE", 5))
        self.assertEqual(tuple(path.read_bytes() for path in (self.evidence_path, self.state_path)), before)

    def test_command_id_and_configuration_status_mapping(self):
        result, status = self.resolve("verify.unknown")
        self.assertEqual((result["result"], status), ("NOT_CONFIGURED", 3))

        result, status = self.resolve("not a command id")
        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

        for configuration_status, expected_result, expected_status in (
            ("NOT_CONFIGURED", "NOT_CONFIGURED", 3),
            ("UNKNOWN", "BLOCKED", 2),
            ("STALE", "BLOCKED", 2),
            ("UNCERTAIN", "BLOCKED", 2),
        ):
            with self.subTest(configuration_status=configuration_status):
                command = self.command()
                command["configurationStatus"] = configuration_status
                command["classification"] = "UNAVAILABLE"
                command["argv"] = None
                self.save_registry()
                result, status = self.resolve()
                self.assertEqual((result["result"], status), (expected_result, expected_status))
                if expected_result == "BLOCKED":
                    self.assertIsNone(result["data"])
                self.registry = json.loads((REPOSITORY_ROOT / "ai" / "command-registry.json").read_text(encoding="utf-8"))

    def test_resolution_validates_canonical_state_before_command_id_policy(self):
        self.registry["commands"].append(json.loads(json.dumps(self.command())))
        self.save_registry()

        result, status = self.resolve("not a command id")

        self.assertEqual((result["result"], status), ("INVALID_STATE", 5))
        self.assertEqual(result["reason"], "SCHEMA_VALIDATION_ERROR")

    def test_classification_blocks_risky_and_destructive_commands(self):
        for classification in ("RISKY", "DESTRUCTIVE"):
            with self.subTest(classification=classification):
                self.command()["classification"] = classification
                self.save_registry()
                result, status = self.resolve()
                self.assertEqual((result["result"], status), ("BLOCKED", 2))
                self.assertIsNone(result["data"])
                self.registry = json.loads((REPOSITORY_ROOT / "ai" / "command-registry.json").read_text(encoding="utf-8"))

    def test_missing_statically_evidenced_wrapper_is_schema_valid_blocked_with_null_data(self):
        (self.root / "gradlew").unlink()

        result, status = self.resolve()

        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(result["reason"], "WRAPPER_STATIC_EVIDENCE_MISSING")
        self.assertIsNone(result["data"])

    def test_disabled_parameters_are_a_policy_violation_even_when_empty(self):
        parameters_path = self.write_json("parameters/empty.json", {})

        result, status = self.resolve(parameters_path.relative_to(self.root).as_posix())

        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

    def test_enabled_parameters_reject_closed_schema_and_input_limits(self):
        self.enable_parameters("^[A-Za-z]+$")
        cases = (
            ("missing.json", {}, "missing"),
            ("extra.json", {"testClass": "Valid", "extra": "no"}, "extra"),
            ("wrong-type.json", {"testClass": 7}, "wrong-type"),
            ("pattern.json", {"testClass": "not valid"}, "pattern-invalid"),
            ("too-many-scalars.json", {"testClass": "a" * 1025}, "too-many-scalars"),
        )
        for filename, parameters, name in cases:
            with self.subTest(case=name):
                path = self.write_json(f"parameters/{filename}", parameters)
                result, status = self.resolve(parameters_path=path.relative_to(self.root).as_posix())
                self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

        for character, name in (("\u0000", "c0"), ("\u007f", "del"), ("\u2028", "line-separator"), ("\u2029", "paragraph-separator")):
            with self.subTest(case=name):
                path = self.write_json("parameters/control.json", {"testClass": "Bad" + character + "Value"})
                result, status = self.resolve(parameters_path=path.relative_to(self.root).as_posix())
                self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

        oversized = self.root / "parameters" / "oversized.json"
        oversized.write_bytes(b"{" + b" " * 65536 + b"}")
        result, status = self.resolve(parameters_path=oversized.relative_to(self.root).as_posix())
        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

    def test_parameter_json_is_strict_and_shell_text_is_one_inert_argv_element(self):
        self.enable_parameters()
        duplicate = self.parameter_fixture("duplicate-key.json")
        result, status = self.resolve(parameters_path=duplicate)
        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

        malformed = self.root / "parameters" / "malformed-utf8.json"
        malformed.write_bytes(b"\xff")
        result, status = self.resolve(parameters_path=malformed.relative_to(self.root).as_posix())
        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

        object_required = self.write_json("parameters/not-object.json", ["testClass"])
        result, status = self.resolve(parameters_path=object_required.relative_to(self.root).as_posix())
        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

        value = "Example Class;$(not-executed)"
        path = self.write_json("parameters/inert-shell-text.json", {"testClass": value})
        result, status = self.resolve(parameters_path=path.relative_to(self.root).as_posix())
        self.assertEqual((result["result"], status), ("PASS", 0))
        self.assertEqual(result["data"]["argv"], ["./gradlew", "test", "--tests", value])

        with self.assertRaises(self.helper.InvalidStateError):
            self.helper.resolved_argv({"argv": ["{{testClass}}"]}, {"testClass": "{{remaining}}"})

    def test_parameter_paths_reject_escapes_secret_git_and_all_phase_1b_run_inputs(self):
        self.enable_parameters()
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        (outside / "parameters.json").write_text('{"testClass":"Valid"}', encoding="utf-8")
        for relative_path, setup in (
            ("../parameters.json", None),
            (".git/parameters.json", lambda: self.write_json(".git/parameters.json", {"testClass": "Valid"})),
            ("secrets/parameters.json", lambda: self.write_json("secrets/parameters.json", {"testClass": "Valid"})),
            (".ai-runs/run-1/parameters.json", lambda: self.write_json(".ai-runs/run-1/parameters.json", {"testClass": "Valid"})),
        ):
            with self.subTest(path=relative_path):
                if setup is not None:
                    setup()
                result, status = self.resolve(parameters_path=relative_path)
                self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

    def test_parameter_path_symlink_escape_is_a_policy_violation_where_supported(self):
        self.enable_parameters()
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        external = outside / "parameters.json"
        external.write_text('{"testClass":"Valid"}', encoding="utf-8")
        escaped = self.root / "parameters" / "escaped.json"
        escaped.parent.mkdir(parents=True, exist_ok=True)
        try:
            escaped.symlink_to(external)
        except (NotImplementedError, OSError):
            self.skipTest("file symlinks are unavailable in this test environment")

        result, status = self.resolve(parameters_path=escaped.relative_to(self.root).as_posix())

        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

    def test_parameter_realpath_aliases_into_control_and_secret_paths_are_rejected_where_supported(self):
        self.enable_parameters()
        targets = (
            ".git/parameters.json",
            ".ai-runs/run-1/parameters.json",
            "secrets/parameters.json",
        )
        for index, target_name in enumerate(targets):
            with self.subTest(target=target_name):
                target = self.write_json(target_name, {"testClass": "Valid"})
                alias = self.root / "parameters" / f"alias-{index}.json"
                alias.parent.mkdir(parents=True, exist_ok=True)
                try:
                    alias.symlink_to(target)
                except (NotImplementedError, OSError):
                    self.skipTest("file symlinks are unavailable in this test environment")

                result, status = self.resolve(parameters_path=alias.relative_to(self.root).as_posix())

                self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))

    def test_prerequisites_are_deterministically_ordered_and_blocked(self):
        assets = json.loads(json.dumps(self.command()))
        assets["id"] = "verify.assets"
        assets["prerequisites"] = []
        compile_command = json.loads(json.dumps(self.command()))
        compile_command["id"] = "verify.compile"
        compile_command["prerequisites"] = ["verify.assets"]
        self.command()["prerequisites"] = ["verify.compile", "verify.assets"]
        self.registry["commands"].extend((assets, compile_command))
        self.save_registry()

        expected = json.loads((PREREQUISITE_FIXTURES_PATH / "ordered.json").read_text(encoding="utf-8"))
        result, status = self.resolve()

        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(result["data"], expected)

    def test_resolver_does_not_create_runs_or_use_subprocess_and_cli_publishes_stdout(self):
        result, status = self.resolve()
        self.assertEqual((result["result"], status), ("PASS", 0))
        self.assertFalse((self.root / ".ai-runs").exists())
        tree = ast.parse(HELPER_PATH.read_text(encoding="utf-8"))
        for function_name in ("resolve_command", "run_resolve"):
            function = next(
                node for node in tree.body
                if isinstance(node, ast.FunctionDef) and node.name == function_name
            )
            names = {node.id for node in ast.walk(function) if isinstance(node, ast.Name)}
            attributes = {
                node.attr for node in ast.walk(function) if isinstance(node, ast.Attribute)
            }
            self.assertNotIn("subprocess", names)
            self.assertNotIn("Popen", attributes)
            self.assertNotIn("launch_reserved", names)

        arguments = [
            "workflow_helper.py", "resolve", "--repository-root", str(self.root),
            "--registry", "ai/command-registry.json", "--command-id", "verify.unit", "--output", "-",
        ]
        stdout = io.StringIO()
        previous_argv = sys.argv
        try:
            sys.argv = arguments
            with contextlib.redirect_stdout(stdout):
                status = self.helper.main()
        finally:
            sys.argv = previous_argv
        published = json.loads(stdout.getvalue())
        self.helper.validate(self.root, published, "ai/schemas/gateway-result.schema.json")
        self.assertEqual((published["result"], status), ("PASS", 0))

        arguments[-1] = "resolution.json"
        stdout = io.StringIO()
        try:
            sys.argv = arguments
            with contextlib.redirect_stdout(stdout):
                status = self.helper.main()
        finally:
            sys.argv = previous_argv
        self.assertEqual((stdout.getvalue(), status), ("", 0))
        file_output = json.loads((self.root / "resolution.json").read_text(encoding="utf-8"))
        self.helper.validate(self.root, file_output, "ai/schemas/gateway-result.schema.json")

    def test_resolve_cli_rejects_control_nested_hidden_non_json_and_existing_outputs_without_changes(self):
        self.write_json("scripts/ai/workflow_helper.py", {"fixture": "helper"})
        (self.root / "build.gradle").write_bytes(b"build fixture\n")
        (self.root / "existing.json").write_bytes(b"existing result\n")
        (self.root / "gradle").mkdir()
        (self.root / "nested").mkdir()
        cases = (
            "ai/project-state.json",
            "ai/command-registry.json",
            "ai/schemas/gateway-result.schema.json",
            "scripts/ai/workflow_helper.py",
            "gradlew",
            "build.gradle",
            "existing.json",
            "ai/result.json",
            "scripts/result.json",
            "gradle/result.json",
            "nested/result.json",
            ".hidden.json",
            "not-json.txt",
        )
        for relative_path in cases:
            with self.subTest(output=relative_path), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary) / "repository"
                shutil.copytree(self.root, root)
                target = root / relative_path
                before = target.read_bytes() if target.exists() else None

                stdout, status = self.invoke_resolve_cli(relative_path, root)

                self.assertEqual(status, 4)
                result = json.loads(stdout)
                self.helper.validate(root, result, "ai/schemas/gateway-result.schema.json")
                self.assertEqual(result["result"], "POLICY_VIOLATION")
                self.assertEqual(target.read_bytes() if target.exists() else None, before)

    def test_resolve_cli_rejects_destination_and_parent_symlinks_without_mutation_where_supported(self):
        outside = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, outside)
        external_file = outside / "external.json"
        external_file.write_bytes(b"external bytes\n")
        destination = self.root / "result.json"
        try:
            destination.symlink_to(external_file)
        except (NotImplementedError, OSError):
            self.skipTest("file symlinks are unavailable in this test environment")

        stdout, status = self.invoke_resolve_cli("result.json")

        self.assertEqual(status, 4)
        self.assertEqual(json.loads(stdout)["result"], "POLICY_VIOLATION")
        self.assertTrue(destination.is_symlink())
        self.assertEqual(external_file.read_bytes(), b"external bytes\n")

        outside_directory = outside / "directory"
        outside_directory.mkdir()
        parent_alias = self.root / "alias"
        try:
            parent_alias.symlink_to(outside_directory, target_is_directory=True)
        except (NotImplementedError, OSError):
            self.skipTest("directory symlinks are unavailable in this test environment")

        stdout, status = self.invoke_resolve_cli("alias/result.json")

        self.assertEqual(status, 4)
        self.assertEqual(json.loads(stdout)["result"], "POLICY_VIOLATION")
        self.assertFalse((outside_directory / "result.json").exists())

    def test_resolve_output_is_published_before_a_new_root_json_file_is_written(self):
        malformed = self.helper.gateway_result(
            "PASS",
            None,
            {"unexpected": "shape"},
            operation="RESOLVE",
        )

        result, status, output_status = self.helper.publish_resolve_output(
            self.root,
            "resolution.json",
            malformed,
            0,
        )

        self.assertEqual((result["result"], status, output_status), ("INVALID_STATE", 5, 0))
        written = json.loads((self.root / "resolution.json").read_text(encoding="utf-8"))
        self.assertEqual(written, result)
        self.helper.validate(self.root, written, "ai/schemas/gateway-result.schema.json")

    def test_resolve_cli_maps_extra_arguments_to_a_structured_policy_violation(self):
        arguments = [
            "workflow_helper.py", "resolve", "--repository-root", str(self.root),
            "--registry", "ai/command-registry.json", "--command-id", "verify.unit", "--output", "-",
            "--inline-json", "{}",
        ]
        stdout = io.StringIO()
        previous_argv = sys.argv
        try:
            sys.argv = arguments
            with contextlib.redirect_stdout(stdout):
                status = self.helper.main()
        finally:
            sys.argv = previous_argv

        result = json.loads(stdout.getvalue())
        self.helper.validate(self.root, result, "ai/schemas/gateway-result.schema.json")
        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))


class RunLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        temporary = tempfile.TemporaryDirectory()
        self.root = Path(temporary.name) / "repository"
        self.addCleanup(temporary.cleanup)
        shutil.copytree(REPOSITORY_ROOT / "ai" / "schemas", self.root / "ai" / "schemas")
        state = json.loads((REPOSITORY_ROOT / "ai" / "project-state.json").read_text(encoding="utf-8"))
        evidence = self.helper.current_evidence(
            "python",
            self.helper.sys.version,
            self.helper.package_version("jsonschema"),
            self.helper.digest(Path(self.helper.sys.executable)),
        )
        runtime = next(item for item in state["helperRuntimes"] if item["environment"] == "LOCAL")
        runtime.update({
            "targetRuntime": evidence["targetRuntime"],
            "detectedRuntime": evidence["detectedRuntime"],
            "configurationStatus": "VERIFIED",
            "version": evidence["version"],
            "evidence": [{
                "kind": "RUNTIME_COMMAND",
                "path": "ai/evidence/local-helper-runtime.json",
                "claim": "fixture current helper runtime evidence",
            }],
        })
        environment = next(item for item in state["environments"] if item["kind"] == "LOCAL")
        environment.update({"configurationStatus": "VERIFIED", "notes": ["fixture recorded preflight"]})
        self.write_json("ai/project-state.json", state)
        self.write_json("ai/evidence/local-helper-runtime.json", evidence)

    def write_json(self, relative_path, value):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def start(self):
        result, status = self.helper.start_run(self.root, "run-1", "phase-1b-2-task-2")
        self.assertEqual((result["result"], status), ("PASS", 0))
        return self.root / ".ai-runs" / "run-1"

    def owner_fixture(self, name, **changes):
        owner = json.loads((EXECUTION_FIXTURES_PATH / name).read_text(encoding="utf-8"))
        owner.update(changes)
        return owner

    def reserved_fixture(self):
        return json.loads((EXECUTION_FIXTURES_PATH / "reserved-with-process-attempt.json").read_text(encoding="utf-8"))

    def prepare_reserved_attempt(self, *, process=True, process_changes=None):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        fixture = self.reserved_fixture()
        session["reservations"] = [fixture["reservation"]]
        self.write_json(session_path.relative_to(self.root).as_posix(), session)
        process_path = run / "process-attempts" / "verify.unit" / "attempt-1.json"
        if process:
            process_attempt = fixture["processAttempt"]
            if process_changes:
                process_attempt.update(process_changes)
            self.write_json(process_path.relative_to(self.root).as_posix(), process_attempt)
        return run, session_path, session, process_path

    def expected_repair_result(self, ended_at="2026-07-11T03:00:04Z"):
        return {
            "$schema": "ai/schemas/command-result.schema.json",
            "$id": ".ai-runs/run-1/commands/verify.unit/attempt-1.json",
            "schemaVersion": 1,
            "runId": "run-1",
            "commandId": "verify.unit",
            "attemptId": "attempt-1",
            "processAttemptRef": ".ai-runs/run-1/process-attempts/verify.unit/attempt-1.json",
            "startedAt": "2026-07-11T03:00:02Z",
            "endedAt": ended_at,
            "result": "BLOCKED",
            "processExitCode": None,
            "argvHash": None,
            "inputFingerprint": None,
            "environmentFingerprint": None,
            "stdoutPath": None,
            "stderrPath": None,
            "redactionApplied": False,
            "reason": "STALE_RESERVED_REPAIRED",
        }

    def write_lock_owner(self, run, fixture_name="lock-owner-dead-expired.json", **changes):
        lock = run / ".state" / "lock"
        lock.mkdir(exist_ok=True)
        owner = self.owner_fixture(fixture_name, **changes)
        self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), owner)
        return lock, owner

    def repair(self, session):
        acquired = self.helper.acquire_run_lock(self.root, session["runId"])
        try:
            return self.helper.repair_reserved_attempts(self.root, session, acquired)
        finally:
            self.helper.release_run_lock(acquired)

    def age_control_owner(self, directory):
        owner_path = directory / "owner.json"
        owner = json.loads(owner_path.read_text(encoding="utf-8"))
        owner.update({"pid": 99999999, "acquiredAt": "2000-01-01T00:00:00Z"})
        self.write_json(owner_path.relative_to(self.root).as_posix(), owner)
        return owner

    def leave_replacement_recovery_partial(self, fault_hook):
        run = self.start()
        self.write_lock_owner(run)
        observed = {}

        def hook(name, **context):
            if name == "recover.after_quarantine_rename":
                observed["quarantine"] = context["quarantine"]
            if name == fault_hook:
                raise OSError(f"injected {fault_hook} failure")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(OSError):
                self.helper.recover_run_lock(self.root, "run-1")
        claim = run / ".state" / "lock-recovery-claim"
        replacement = run / ".state" / "lock"
        self.assertTrue(observed["quarantine"].is_dir())
        self.assertTrue(claim.is_dir())
        self.assertTrue(replacement.is_dir())
        self.age_control_owner(claim)
        replacement_owner = self.age_control_owner(replacement)
        return run, observed["quarantine"], replacement, replacement_owner

    def leave_ownerless_replacement_partial(self):
        run = self.start()
        self.write_lock_owner(run)
        observed = {}

        class SimulatedCrash(BaseException):
            pass

        def hook(name, **context):
            if name == "recover.after_quarantine_rename":
                observed["quarantine"] = context["quarantine"]
            if name == "acquire.after_mkdir" and context.get("purpose") == "recovery":
                raise SimulatedCrash()

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(SimulatedCrash):
                self.helper.recover_run_lock(self.root, "run-1")
        state = run / ".state"
        claim = state / "lock-recovery-claim"
        replacement = state / "lock"
        self.assertTrue(observed["quarantine"].is_dir())
        self.assertEqual(list(replacement.iterdir()), [])
        self.age_control_owner(claim)
        return run, observed["quarantine"], replacement, claim

    def test_start_run_publishes_only_an_open_session_after_current_preflight(self):
        result, status = self.helper.start_run(self.root, "run-1", "phase-1b-2-task-2")

        self.assertEqual((result["operation"], result["result"], result["reason"], status), ("RUN_START", "PASS", None, 0))
        self.assertEqual(result["data"], {
            "runId": "run-1",
            "taskKey": "phase-1b-2-task-2",
            "sessionRef": ".ai-runs/run-1/.state/run-session.json",
        })
        session_path = self.root / ".ai-runs" / "run-1" / ".state" / "run-session.json"
        self.assertTrue(session_path.is_file())
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "run.json").exists())
        session = json.loads(session_path.read_text(encoding="utf-8"))
        self.helper.validate(self.root, session, "ai/schemas/run-session.schema.json")
        self.assertEqual((session["runId"], session["taskKey"], session["state"]), ("run-1", "phase-1b-2-task-2", "OPEN"))
        self.assertEqual(session["reservations"], [])
        if os.name != "nt":
            self.assertEqual(session_path.stat().st_mode & 0o777, 0o600)
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())


class PreCommandFingerprintTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        temporary = tempfile.TemporaryDirectory()
        self.root = Path(temporary.name) / "repository"
        self.root.mkdir()
        self.addCleanup(temporary.cleanup)

    def command(self, input_paths=None, working_directory="."):
        return {
            "id": "verify.unit",
            "workingDirectory": working_directory,
            "inputPaths": ["build.gradle"] if input_paths is None else input_paths,
        }

    def write_bytes(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def assert_invalid_input(self, input_path):
        with self.assertRaises(self.helper.InvalidStateError):
            self.helper.input_fingerprint(self.root, self.command([input_path]))

    def test_length_prefixed_frames_and_argv_hash_match_known_vectors(self):
        vectors = json.loads((EXECUTION_FIXTURES_PATH / "fingerprint-pattern-vectors.json").read_text(encoding="utf-8"))
        self.assertEqual(
            hashlib.sha256(self.helper.length_prefixed_frame("", "")).hexdigest(),
            vectors["frameEmptySha256"],
        )
        self.assertEqual(
            hashlib.sha256(self.helper.length_prefixed_frame("\ud55c\uae00", "\uac12")).hexdigest(),
            vectors["frameUtf8Sha256"],
        )
        self.assertEqual(
            self.helper.argv_hash(["./gradlew", "test"]),
            vectors["argvOrderedSha256"],
        )
        self.assertEqual(
            self.helper.argv_hash(["test", "./gradlew"]),
            "36be4e3e8ecc776a400e57eba36e8bfc69ab54a29a6375d88ae801079820f012",
        )

    def test_input_fingerprint_matches_literal_tree_no_match_and_utf8_order_vector(self):
        vectors = json.loads((EXECUTION_FIXTURES_PATH / "fingerprint-pattern-vectors.json").read_text(encoding="utf-8"))
        self.write_bytes("build.gradle", b"build\n")
        self.write_bytes("tree/a.txt", b"A")
        self.write_bytes("tree/empty.txt", b"")
        self.write_bytes("tree/nested/z.txt", b"Z")
        self.write_bytes("tree/\ud55c.txt", b"K")
        command = self.command(["build.gradle", "tree/**", "missing/**"])

        self.assertEqual(
            self.helper.input_fingerprint(self.root, command),
            vectors["inputTreeSha256"],
        )
        command["inputPaths"].reverse()
        self.assertEqual(
            self.helper.input_fingerprint(self.root, command),
            "49b079237d68323841290bf1bc0bb26239d986a80483f784c362c339aa7b29bb",
        )

    def test_input_fingerprint_normalizes_working_directory_and_empty_tree(self):
        self.write_bytes("nested/input.txt", b"input")
        (self.root / "empty-tree").mkdir()
        first = self.command(["nested/input.txt", "empty-tree/**", "missing/**"], "nested")
        second = self.command(["nested/input.txt", "empty-tree/**", "missing/**"], "nested/.")
        self.assertEqual(
            self.helper.input_fingerprint(self.root, first),
            self.helper.input_fingerprint(self.root, second),
        )

    def test_input_path_grammar_is_closed(self):
        invalid = (
            "*", "file*", "*file", "fi*le", "file?", "[x]", "{x}",
            "dir/**/more", "dir/*", "/**", "//", "dir//file", "../file",
            "/absolute", "C:/absolute", "https://example.test/file", "dir\\file",
        )
        for value in invalid:
            with self.subTest(value=value):
                self.assert_invalid_input(value)

    def test_literal_paths_must_be_existing_regular_non_links(self):
        self.assert_invalid_input("missing.txt")
        (self.root / "directory").mkdir()
        self.assert_invalid_input("directory")
        target = self.write_bytes("target.txt", b"target")
        alias = self.root / "alias.txt"
        try:
            alias.symlink_to(target)
        except (NotImplementedError, OSError):
            pass
        else:
            self.assert_invalid_input("alias.txt")

    def test_tree_walk_rejects_file_links_at_every_file_depth_where_supported(self):
        target = self.write_bytes("outside.txt", b"outside")
        for relative in ("tree/link.txt", "tree/nested/link.txt"):
            shutil.rmtree(self.root / "tree", ignore_errors=True)
            (self.root / "tree" / "nested").mkdir(parents=True)
            alias = self.root / relative
            try:
                alias.symlink_to(target)
            except (NotImplementedError, OSError):
                self.skipTest("file symlinks are unavailable in this test environment")
            self.assert_invalid_input("tree/**")

    def test_tree_walk_rejects_directory_links_at_each_walked_depth_where_supported(self):
        target = self.root / "directory-link-target"
        target.mkdir()
        self.write_bytes("directory-link-target/input.txt", b"outside")
        cases = (
            ("prefix", "prefix/tree", "prefix/tree/**"),
            ("child", "child/tree/link", "child/tree/**"),
            ("nested", "nested/tree/level/link", "nested/tree/**"),
        )
        for name, relative, pattern in cases:
            with self.subTest(depth=name):
                alias = self.root / relative
                alias.parent.mkdir(parents=True, exist_ok=True)
                try:
                    alias.symlink_to(target, target_is_directory=True)
                except (NotImplementedError, OSError):
                    self.skipTest("directory symlinks are unavailable in this test environment")
                self.assert_invalid_input(pattern)

    def test_tree_walk_mock_contract_rejects_directory_links_at_each_walked_depth(self):
        cases = (
            ("prefix", "prefix/tree", "prefix/tree/**"),
            ("child", "child/tree/link", "child/tree/**"),
            ("nested", "nested/tree/level/link", "nested/tree/**"),
        )
        original_lstat = Path.lstat
        link_mode = self.helper.stat.S_IFLNK | 0o777
        for name, relative, pattern in cases:
            with self.subTest(depth=name):
                mocked_link = self.root / relative
                mocked_link.mkdir(parents=True)

                def link_lstat(candidate, *args, **kwargs):
                    metadata = original_lstat(candidate, *args, **kwargs)
                    if candidate == mocked_link:
                        return SimpleNamespace(st_mode=link_mode, st_file_attributes=0)
                    return metadata

                with mock.patch.object(Path, "lstat", link_lstat):
                    self.assert_invalid_input(pattern)

    def test_tree_walk_rejects_mocked_recursive_non_regular_entry_mode(self):
        special = self.write_bytes("tree/special", b"not really special")
        original_lstat = Path.lstat

        def non_regular_lstat(candidate, *args, **kwargs):
            metadata = original_lstat(candidate, *args, **kwargs)
            if candidate == special:
                return SimpleNamespace(
                    st_mode=self.helper.stat.S_IFIFO | 0o600,
                    st_file_attributes=0,
                )
            return metadata

        with mock.patch.object(Path, "lstat", non_regular_lstat):
            self.assert_invalid_input("tree/**")

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "mkfifo"), "safe POSIX FIFO coverage")
    def test_tree_walk_rejects_real_posix_fifo_without_opening_it(self):
        tree = self.root / "tree"
        tree.mkdir()
        os.mkfifo(tree / "named-pipe", 0o600)
        self.assert_invalid_input("tree/**")

    def test_lstat_errors_fail_closed_at_literal_and_recursive_walk_boundaries(self):
        literal = self.write_bytes("input.txt", b"input")
        recursive = self.write_bytes("tree/input.txt", b"tree")
        original_lstat = Path.lstat
        cases = (
            ("literal-containment", literal, 1, "input.txt"),
            ("literal-before-read", literal, 2, "input.txt"),
            ("literal-after-read", literal, 3, "input.txt"),
            ("recursive-prefix", recursive.parent, 2, "tree/**"),
            ("recursive-entry", recursive, 1, "tree/**"),
        )
        for name, failed_path, failed_call, pattern in cases:
            with self.subTest(boundary=name):
                calls = 0

                def fail_lstat(candidate, *args, **kwargs):
                    nonlocal calls
                    if candidate == failed_path:
                        calls += 1
                        if calls == failed_call:
                            raise OSError(f"injected {name} lstat failure")
                    return original_lstat(candidate, *args, **kwargs)

                with mock.patch.object(Path, "lstat", fail_lstat):
                    self.assert_invalid_input(pattern)

    def test_read_and_stat_uncertainty_fail_before_a_fingerprint(self):
        path = self.write_bytes("input.txt", b"input")
        original_open = Path.open

        def fail_open(candidate, *args, **kwargs):
            if candidate == path:
                raise OSError("injected read failure")
            return original_open(candidate, *args, **kwargs)

        with mock.patch.object(Path, "open", fail_open):
            self.assert_invalid_input("input.txt")

    def test_child_environment_and_fingerprint_use_only_the_exact_sorted_allowlist(self):
        vectors = json.loads((EXECUTION_FIXTURES_PATH / "fingerprint-pattern-vectors.json").read_text(encoding="utf-8"))
        source = {
            "PATH": "/bin", "LANG": "ko_KR.UTF-8", "HOME": "/home/test",
            "TOKEN": "ignored", "SHELL": "/bin/bash",
        }
        environment = self.helper.child_environment(source)
        self.assertEqual(environment, {"PATH": "/bin", "HOME": "/home/test", "LANG": "ko_KR.UTF-8"})
        self.assertEqual(
            self.helper.environment_fingerprint({"LANG": "ko_KR.UTF-8", "PATH": "/bin"}),
            vectors["environmentSha256"],
        )
        for value in ("bad\x00value", "bad\nvalue", 1):
            with self.subTest(value=value), self.assertRaises(self.helper.InvalidStateError):
                self.helper.child_environment({"PATH": value})


class PreCommandTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        temporary = tempfile.TemporaryDirectory()
        self.root = Path(temporary.name) / "repository"
        self.addCleanup(temporary.cleanup)
        shutil.copytree(REPOSITORY_ROOT / "ai" / "schemas", self.root / "ai" / "schemas")
        state = json.loads((REPOSITORY_ROOT / "ai" / "project-state.json").read_text(encoding="utf-8"))
        evidence = self.helper.current_evidence(
            "python", self.helper.sys.version, self.helper.package_version("jsonschema"),
            self.helper.digest(Path(self.helper.sys.executable)),
        )
        runtime = next(item for item in state["helperRuntimes"] if item["environment"] == "LOCAL")
        runtime.update({
            "targetRuntime": evidence["targetRuntime"], "detectedRuntime": evidence["detectedRuntime"],
            "configurationStatus": "VERIFIED", "version": evidence["version"],
            "evidence": [{"kind": "RUNTIME_COMMAND", "path": "ai/evidence/local-helper-runtime.json", "claim": "fixture"}],
        })
        next(item for item in state["environments"] if item["kind"] == "LOCAL").update({
            "configurationStatus": "VERIFIED", "notes": ["fixture"],
        })
        self.write_json("ai/project-state.json", state)
        self.write_json("ai/evidence/local-helper-runtime.json", evidence)
        self.write_bytes("gradlew", b"#!/bin/sh\n")
        self.write_bytes("build.gradle", b"build fixture\n")
        self.write_bytes("settings.gradle", b"settings fixture\n")
        self.write_bytes("gradle/wrapper.properties", b"wrapper fixture\n")
        self.registry = self.base_registry()
        self.save_registry()
        result, status = self.helper.start_run(self.root, "run-1", "phase-1b-2-task-3")
        self.assertEqual((result["result"], status), ("PASS", 0))

    def write_bytes(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return path

    def write_json(self, relative_path, value):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value), encoding="utf-8")
        return path

    def base_registry(self):
        registry = json.loads((REPOSITORY_ROOT / "ai" / "command-registry.json").read_text(encoding="utf-8"))
        registry["commands"] = [next(item for item in registry["commands"] if item["id"] == "verify.unit")]
        registry["commands"][0]["inputPaths"] = ["build.gradle", "settings.gradle", "gradle/**"]
        return registry

    def save_registry(self):
        self.write_json("ai/command-registry.json", self.registry)

    def session_path(self):
        return self.root / ".ai-runs" / "run-1" / ".state" / "run-session.json"

    def session(self):
        return json.loads(self.session_path().read_text(encoding="utf-8"))

    def pre(self, command_id="verify.unit", **kwargs):
        source_environment = kwargs.pop("source_environment", {"PATH": "/bin", "LANG": "C"})
        return self.helper.pre_command(
            self.root, "run-1", command_id, source_environment=source_environment, **kwargs,
        )

    def event_files(self):
        directory = self.root / ".ai-runs" / "run-1" / "policy-violations"
        return sorted(directory.glob("*.json")) if directory.exists() else []

    def process_for_reservation(self, reservation):
        process = json.loads(
            (EXECUTION_FIXTURES_PATH / "reserved-with-process-attempt.json").read_text(encoding="utf-8")
        )["processAttempt"]
        process.update({
            "$id": f".ai-runs/run-1/process-attempts/{reservation['commandId']}/{reservation['attemptId']}.json",
            "commandId": reservation["commandId"],
            "attemptId": reservation["attemptId"],
            "reservedAt": reservation["reservedAt"],
            "argvHash": reservation["argvHash"],
            "inputFingerprint": reservation["inputFingerprint"],
            "environmentFingerprint": reservation["environmentFingerprint"],
        })
        return process

    def resume_pending_publications(self):
        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        try:
            session = self.helper.active_open_session(self.root, "run-1")
            return self.helper.resume_immutable_publications(self.root, session, acquired)
        finally:
            self.helper.release_run_lock(acquired)

    def terminal_reservation(self, state):
        result, status = self.pre()
        self.assertEqual((result["result"], status), ("PASS", 0))
        session = self.session()
        reservation = session["reservations"][0]
        attempt_id = reservation["attemptId"]
        reservation.update({
            "state": state,
            "commandResultRef": f".ai-runs/run-1/commands/verify.unit/{attempt_id}.json",
            "processAttemptRef": f".ai-runs/run-1/process-attempts/verify.unit/{attempt_id}.json",
            "terminalAt": "2026-07-11T03:00:03Z",
        })
        session["commandResultRefs"] = [reservation["commandResultRef"]]
        session["processAttemptRefs"] = [reservation["processAttemptRef"]]
        self.write_json(self.session_path().relative_to(self.root).as_posix(), session)
        return reservation

    def test_pre_command_always_runs_current_preflight_before_artifacts(self):
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(
            self.helper.gateway_result("NOT_CONFIGURED", "RUNTIME_UNAVAILABLE"), 3,
        )) as preflight:
            result, status = self.pre()
        self.assertEqual((result["result"], status), ("NOT_CONFIGURED", 3))
        preflight.assert_called_once_with(self.root.resolve())
        self.assertEqual(self.session()["reservations"], [])

    def test_execute_capability_failure_runs_real_policy_without_reservation_or_launch(self):
        cases = (
            ("verify.unit", "SAFE", "NOT_CONFIGURED", "POSIX_EXECUTION_NOT_CONFIGURED", None),
            ("verify.missing", None, "POLICY_VIOLATION", "COMMAND_NOT_REGISTERED", "UNREGISTERED_COMMAND"),
            ("verify.unit", "RISKY", "BLOCKED", "COMMAND_CLASSIFICATION_BLOCKED", None),
            ("verify.unit", "DESTRUCTIVE", "BLOCKED", "COMMAND_CLASSIFICATION_BLOCKED", "DESTRUCTIVE_WITHOUT_APPROVAL"),
        )
        for command_id, classification, expected_result, reason, event_type in cases:
            with self.subTest(command_id=command_id, classification=classification):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(remove_readonly_tree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                if classification is not None:
                    registry = json.loads((root_copy / "ai/command-registry.json").read_text(encoding="utf-8"))
                    registry["commands"][0]["classification"] = classification
                    (root_copy / "ai/command-registry.json").write_text(json.dumps(registry), encoding="utf-8")
                with contextlib.ExitStack() as stack:
                    stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=False))
                    popen = stack.enter_context(mock.patch.object(self.helper.subprocess, "Popen"))
                    result, status, process = self.helper.execute_command(
                        root_copy, {"runId": "run-1", "commandId": command_id},
                    )
                self.assertEqual((result["result"], result["reason"], process), (
                    expected_result, reason, None,
                ))
                self.assertNotEqual(status, 0)
                session = json.loads((root_copy / self.session_path().relative_to(self.root)).read_text(encoding="utf-8"))
                self.assertEqual(session["reservations"], [])
                events_dir = root_copy / ".ai-runs/run-1/policy-violations"
                events = list(events_dir.glob("*.json")) if events_dir.exists() else []
                self.assertEqual(len(events), 1 if event_type else 0)
                if event_type:
                    self.assertEqual(json.loads(events[0].read_text(encoding="utf-8"))["type"], event_type)
                popen.assert_not_called()

    def test_public_execute_concurrency_repairs_crash_residue_and_never_relaunches(self):
        first, first_status = self.pre()
        self.assertEqual((first["result"], first_status), ("PASS", 0))
        reservation = self.session()["reservations"][0]
        process = self.process_for_reservation(reservation)
        self.write_json(process["$id"], process)
        lock = self.root / ".ai-runs/run-1/.state/lock"
        lock.mkdir()
        owner = json.loads((EXECUTION_FIXTURES_PATH / "lock-owner-dead-expired.json").read_text(encoding="utf-8"))
        self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), owner)

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
            stack.enter_context(mock.patch.dict(self.helper.os.environ, {"PATH": "/bin", "LANG": "C"}, clear=True))
            launch = stack.enter_context(mock.patch.object(self.helper, "launch_reserved"))
            with ThreadPoolExecutor(max_workers=2) as executor:
                futures = [executor.submit(
                    self.helper.execute_command,
                    self.root,
                    {"runId": "run-1", "commandId": "verify.unit"},
                ) for _ in range(2)]
                outcomes = [future.result(timeout=10) for future in futures]

        self.assertTrue(all(len(outcome) == 3 for outcome in outcomes), outcomes)
        self.assertTrue(all(status != 0 and child is None for _result, status, child in outcomes), outcomes)
        launch.assert_not_called()
        recovered = self.session()
        self.assertEqual(recovered["reservations"][0]["state"], "BLOCKED")
        self.assertEqual(len(recovered["lockRecoveries"]), 1)

    def test_unrepairable_reserved_attempt_blocks_new_work_with_a_different_fingerprint(self):
        first, first_status = self.pre()
        self.assertEqual((first["result"], first_status), ("PASS", 0))

        blocked, blocked_status = self.pre(source_environment={"PATH": "/different", "LANG": "C"})

        self.assertEqual((blocked["result"], blocked["reason"], blocked_status), (
            "BLOCKED", "RESERVATION_PENDING", 2,
        ))
        self.assertEqual(len(self.session()["reservations"]), 1)

    def test_pre_command_lstat_failure_is_invalid_state_without_artifact_mutation(self):
        run = self.root / ".ai-runs" / "run-1"
        before = {
            path.relative_to(run).as_posix(): path.read_bytes()
            for path in run.rglob("*")
            if path.is_file()
        }
        input_path = self.root / "build.gradle"
        original_lstat = Path.lstat
        calls = 0

        def fail_after_read(candidate, *args, **kwargs):
            nonlocal calls
            if candidate == input_path:
                calls += 1
                if calls == 3:
                    raise OSError("injected post-read lstat failure")
            return original_lstat(candidate, *args, **kwargs)

        with mock.patch.object(Path, "lstat", fail_after_read):
            result, status = self.pre()

        after = {
            path.relative_to(run).as_posix(): path.read_bytes()
            for path in run.rglob("*")
            if path.is_file()
        }
        self.assertEqual(
            (result["operation"], result["result"], result["reason"], status),
            ("PRE_COMMAND", "INVALID_STATE", "INPUT_PATH_READ_FAILED", 5),
        )
        self.assertEqual(after, before)
        self.assertEqual(self.session()["reservations"], [])

    def test_pre_command_requires_a_schema_valid_open_run_and_no_finalized_run(self):
        missing, missing_status = self.helper.pre_command(
            self.root, "missing-run", "verify.unit", source_environment={"PATH": "/bin"},
        )
        self.assertEqual((missing["result"], missing_status), ("INVALID_STATE", 5))
        self.assertFalse((self.root / ".ai-runs" / "missing-run").exists())

        session = self.session()
        session["state"] = "FINALIZING"
        self.write_json(self.session_path().relative_to(self.root).as_posix(), session)
        result, status = self.pre()
        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(self.session()["reservations"], [])

    def test_pre_command_first_attempt_publishes_one_schema_valid_reserved_entry_under_lock(self):
        observed = []
        original_replace = self.helper.replace_run_session

        def checked_replace(root, path, session, acquired, expected_session=None):
            self.helper.validate_held_run_lock(root, "run-1", acquired)
            observed.append(acquired.owner["ownerId"])
            return original_replace(root, path, session, acquired, expected_session)

        with mock.patch.object(self.helper, "replace_run_session", side_effect=checked_replace):
            result, status = self.pre()
        self.assertEqual((result["result"], status), ("PASS", 0))
        self.assertEqual(set(result["data"]), {
            "runId", "commandId", "attemptId", "argvHash", "inputFingerprint",
            "environmentFingerprint", "workingDirectory", "argv",
        })
        session = self.session()
        self.helper.validate(self.root, session, "ai/schemas/run-session.schema.json")
        self.assertEqual(len(session["reservations"]), 1)
        self.assertEqual(session["reservations"][0]["state"], "RESERVED")
        self.assertEqual(observed, [observed[0]])
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "process-attempts").exists())

    def test_unregistered_and_unsafe_commands_record_events_only_for_valid_runs(self):
        result, status = self.pre("verify.unknown")
        self.assertEqual((result["result"], status), ("POLICY_VIOLATION", 4))
        event = json.loads(self.event_files()[0].read_text(encoding="utf-8"))
        self.helper.validate(self.root, event, "ai/schemas/policy-violation.schema.json")
        self.assertEqual(event["type"], "UNREGISTERED_COMMAND")
        self.assertIn(event["$id"], self.session()["policyViolationRefs"])

        command = self.registry["commands"][0]
        command["parameters"] = {
            "allowed": True,
            "schema": {
                "type": "object", "additionalProperties": False, "required": ["testClass"],
                "properties": {"testClass": {"type": "string", "pattern": "^[A-Za-z]+$"}},
            },
        }
        command["argv"].append("{{testClass}}")
        self.save_registry()
        self.write_json("unsafe.json", {"testClass": "bad value"})
        unsafe, unsafe_status = self.pre(parameters_path="unsafe.json")
        self.assertEqual((unsafe["result"], unsafe_status), ("POLICY_VIOLATION", 4))
        self.assertEqual({json.loads(path.read_text(encoding="utf-8"))["type"] for path in self.event_files()}, {
            "UNREGISTERED_COMMAND", "UNSAFE_PARAMETER",
        })

        no_run, no_run_status = self.helper.pre_command(
            self.root, "absent", "verify.unknown", source_environment={"PATH": "/bin"},
        )
        self.assertEqual(
            (no_run["operation"], no_run["result"], no_run["reason"], no_run["data"], no_run_status),
            ("PRE_COMMAND", "POLICY_VIOLATION", "COMMAND_NOT_REGISTERED", None, 4),
        )
        self.assertFalse((self.root / ".ai-runs" / "absent").exists())

    def test_risky_and_destructive_commands_block_even_with_valid_approval_audit(self):
        approval = json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / "approval-audit-valid.json").read_text(encoding="utf-8"))
        for index, classification in enumerate(("RISKY", "DESTRUCTIVE"), start=1):
            with self.subTest(classification=classification):
                current = json.loads(json.dumps(approval))
                current["approvalId"] = f"approval-{index}"
                current["$id"] = f".ai-runs/run-1/approvals/approval-{index}.json"
                current["type"] = f"{classification}_COMMAND"
                self.write_json(f"approval-{index}.json", current)
                self.registry["commands"][0]["classification"] = classification
                self.save_registry()
                result, status = self.pre(approval_ref=f"approval-{index}.json")
                self.assertEqual((result["result"], status), ("BLOCKED", 2))
                self.assertEqual(self.session()["reservations"], [])
        self.assertTrue(self.session()["approvalRefs"])

    def test_risky_and_destructive_classification_precedes_missing_and_unsafe_parameters(self):
        for classification in ("RISKY", "DESTRUCTIVE"):
            for case, parameters_path in (("missing", None), ("unsafe", "unsafe.json")):
                with self.subTest(classification=classification, case=case):
                    root_copy = Path(tempfile.mkdtemp()) / "repository"
                    self.addCleanup(shutil.rmtree, root_copy.parent)
                    shutil.copytree(self.root, root_copy)
                    registry_path = root_copy / "ai" / "command-registry.json"
                    registry = json.loads(registry_path.read_text(encoding="utf-8"))
                    command = registry["commands"][0]
                    command["classification"] = classification
                    command["parameters"] = {
                        "allowed": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "required": ["testClass"],
                            "properties": {"testClass": {"type": "string", "pattern": "^[A-Za-z]+$"}},
                        },
                    }
                    command["argv"].append("{{testClass}}")
                    registry_path.write_text(json.dumps(registry), encoding="utf-8")
                    if parameters_path is not None:
                        (root_copy / parameters_path).write_text(
                            json.dumps({"testClass": "bad value"}), encoding="utf-8",
                        )

                    result, status = self.helper.pre_command(
                        root_copy,
                        "run-1",
                        "verify.unit",
                        parameters_path=parameters_path,
                        source_environment={"PATH": "/bin"},
                    )

                    self.assertEqual((result["result"], result["reason"], status), (
                        "BLOCKED", "COMMAND_CLASSIFICATION_BLOCKED", 2,
                    ))
                    session = json.loads((
                        root_copy / ".ai-runs" / "run-1" / ".state" / "run-session.json"
                    ).read_text(encoding="utf-8"))
                    event_types = {
                        json.loads(path.read_text(encoding="utf-8"))["type"]
                        for path in (root_copy / ".ai-runs" / "run-1" / "policy-violations").glob("*.json")
                    } if (root_copy / ".ai-runs" / "run-1" / "policy-violations").exists() else set()
                    self.assertNotIn("UNSAFE_PARAMETER", event_types)
                    self.assertEqual(session["reservations"], [])
                    if classification == "DESTRUCTIVE":
                        self.assertEqual(event_types, {"DESTRUCTIVE_WITHOUT_APPROVAL"})
                    else:
                        self.assertEqual(event_types, set())

    def test_policy_event_publication_resumes_after_fault_without_unreferenced_artifact(self):
        failed = {"done": False}

        def hook(name, **_context):
            if name == "immutable.after_artifact" and not failed["done"]:
                failed["done"] = True
                raise OSError("injected publication fault")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            result, status = self.pre("verify.unknown")

        self.assertEqual((result["result"], status), ("INVALID_STATE", 5))
        stranded = self.event_files()
        self.assertEqual(len(stranded), 1)
        self.assertNotIn(json.loads(stranded[0].read_text(encoding="utf-8"))["$id"], self.session()["policyViolationRefs"])

        resumed = self.resume_pending_publications()

        reference = json.loads(stranded[0].read_text(encoding="utf-8"))["$id"]
        self.assertIn(reference, resumed["policyViolationRefs"])
        self.assertEqual(self.session(), resumed)
        self.assertFalse((self.root / ".ai-runs" / "run-1" / ".state" / "immutable-publications").exists())

    def test_approval_publication_resumes_after_session_cas_failure(self):
        approval = json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / "approval-audit-valid.json").read_text(encoding="utf-8"))
        self.write_json("approval.json", approval)
        self.registry["commands"][0]["classification"] = "RISKY"
        self.save_registry()
        session_path = self.session_path()
        concurrent_ref = ".ai-runs/run-1/policy-violations/concurrent.json"
        failed = {"done": False}

        def hook(name, **context):
            replacement = context.get("replacement", {})
            if (
                name == "session.before_replace"
                and replacement.get("approvalRefs")
                and not failed["done"]
            ):
                failed["done"] = True
                current = json.loads(session_path.read_text(encoding="utf-8"))
                current["policyViolationRefs"].append(concurrent_ref)
                self.write_json(session_path.relative_to(self.root).as_posix(), current)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            result, status = self.pre(approval_ref="approval.json")

        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        approval_path = self.root / approval["$id"]
        winner_bytes = approval_path.read_bytes()
        self.assertNotIn(approval["$id"], self.session()["approvalRefs"])

        resumed = self.resume_pending_publications()

        self.assertEqual(approval_path.read_bytes(), winner_bytes)
        self.assertEqual(resumed["approvalRefs"], [approval["$id"]])
        self.assertEqual(resumed["policyViolationRefs"], [concurrent_ref])

    def test_immutable_publication_collision_preserves_winner_and_pending_evidence(self):
        winner = {"written": False, "bytes": None}

        def hook(name, **context):
            if name == "immutable.before_artifact" and not winner["written"]:
                artifact = json.loads(json.dumps(context["artifact"]))
                artifact["description"] = "collision winner"
                path = self.root / artifact["$id"]
                self.write_json(path.relative_to(self.root).as_posix(), artifact)
                winner["written"] = True
                winner["bytes"] = path.read_bytes()

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            result, status = self.pre("verify.unknown")

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "POLICY_EVENT_COLLISION", 2,
        ))
        event = self.event_files()[0]
        self.assertEqual(event.read_bytes(), winner["bytes"])
        self.assertEqual(self.session()["policyViolationRefs"], [])
        pending = self.root / ".ai-runs" / "run-1" / ".state" / "immutable-publications"
        self.assertEqual(len(list(pending.glob("*.json"))), 1)

    def test_same_run_pass_prerequisite_is_required_and_wrong_evidence_is_invalid(self):
        prerequisite = json.loads(json.dumps(self.registry["commands"][0]))
        prerequisite["id"] = "verify.prepare"
        prerequisite["prerequisites"] = []
        self.registry["commands"][0]["prerequisites"] = ["verify.prepare"]
        self.registry["commands"].append(prerequisite)
        self.save_registry()

        missing, missing_status = self.pre()
        self.assertEqual((missing["result"], missing_status), ("BLOCKED", 2))
        self.assertEqual(self.session()["reservations"], [])

        fixture = json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / "prerequisite-pass-same-run.json").read_text(encoding="utf-8"))
        self.write_json(fixture["$id"], fixture)
        session = self.session()
        session["commandResultRefs"] = [fixture["$id"]]
        self.write_json(self.session_path().relative_to(self.root).as_posix(), session)
        passed, passed_status = self.pre()
        self.assertEqual((passed["result"], passed_status), ("PASS", 0))

        for name in ("prerequisite-wrong-run.json",):
            wrong = json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / name).read_text(encoding="utf-8"))
            self.write_json(wrong["$id"], wrong)
            session = self.session()
            session["reservations"] = []
            session["commandResultRefs"] = [wrong["$id"]]
            self.write_json(self.session_path().relative_to(self.root).as_posix(), session)
            invalid, invalid_status = self.pre()
            self.assertEqual((invalid["result"], invalid_status), ("INVALID_STATE", 5))

    def test_task3_gateway_fixtures_are_schema_valid_and_closed(self):
        fixtures = {
            "approval-audit-valid.json": "approval-record",
            "policy-unregistered-command.json": "policy-violation",
            "prerequisite-pass-same-run.json": "command-result",
            "prerequisite-wrong-run.json": "command-result",
        }
        for filename, schema_name in fixtures.items():
            with self.subTest(filename=filename):
                instance = json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / filename).read_text(encoding="utf-8"))
                schema = json.loads((REPOSITORY_ROOT / "ai" / "schemas" / f"{schema_name}.schema.json").read_text(encoding="utf-8"))
                errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))
                self.assertEqual(errors, [])

        self.assertEqual((EXECUTION_FIXTURES_PATH / "fingerprint-tree" / "empty.txt").read_bytes(), b"")
        self.assertEqual(
            (EXECUTION_FIXTURES_PATH / "rerun-reason.txt").read_text(encoding="utf-8").strip(),
            "confirm deterministic rerun",
        )

    def test_prerequisite_wrong_command_tuple_and_non_pass_result_are_invalid(self):
        prerequisite = json.loads(json.dumps(self.registry["commands"][0]))
        prerequisite["id"] = "verify.prepare"
        prerequisite["prerequisites"] = []
        self.registry["commands"][0]["prerequisites"] = ["verify.prepare"]
        self.registry["commands"].append(prerequisite)
        self.save_registry()
        base = json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / "prerequisite-pass-same-run.json").read_text(encoding="utf-8"))

        cases = []
        wrong_tuple = json.loads(json.dumps(base))
        wrong_tuple["commandId"] = "verify.other"
        cases.append(wrong_tuple)
        non_pass = json.loads(json.dumps(base))
        non_pass.update({"result": "FAIL", "processExitCode": 7, "reason": "fixture failure"})
        cases.append(non_pass)
        for index, fixture in enumerate(cases):
            with self.subTest(index=index):
                self.write_json(base["$id"], fixture)
                session = self.session()
                session["commandResultRefs"] = [base["$id"]]
                self.write_json(self.session_path().relative_to(self.root).as_posix(), session)
                result, status = self.pre()
                self.assertEqual((result["result"], status), ("INVALID_STATE", 5))

    def test_prior_pass_requires_bounded_one_line_reason_and_links_hash(self):
        prior = self.terminal_reservation("PASS")
        missing, missing_status = self.pre()
        self.assertEqual((missing["result"], missing_status), ("POLICY_VIOLATION", 4))
        self.assertEqual(len(self.session()["reservations"]), 1)
        self.assertEqual(json.loads(self.event_files()[0].read_text(encoding="utf-8"))["type"], "MISSING_RERUN_REASON")

        for content in (b"", b"line one\nline two", b"x" * 4097):
            with self.subTest(length=len(content)):
                self.write_bytes("invalid-reason.txt", content)
                invalid, invalid_status = self.pre(rerun_reason_path="invalid-reason.txt")
                self.assertEqual((invalid["result"], invalid_status), ("POLICY_VIOLATION", 4))

        reason = self.write_bytes("rerun-reason.txt", (EXECUTION_FIXTURES_PATH / "rerun-reason.txt").read_bytes())
        result, status = self.pre(rerun_reason_path=reason.relative_to(self.root).as_posix())
        self.assertEqual((result["result"], status), ("PASS", 0))
        rerun = self.session()["reservations"][-1]
        self.assertEqual(rerun["rerunOfAttemptId"], prior["attemptId"])
        self.assertEqual(rerun["rerunReasonHash"], hashlib.sha256(b"confirm deterministic rerun").hexdigest())

    def test_prior_fail_blocked_and_reserved_duplicates_have_no_triage_surrogate(self):
        for terminal in ("FAIL", "BLOCKED"):
            with self.subTest(terminal=terminal):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(shutil.rmtree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                session_path = root_copy / ".ai-runs" / "run-1" / ".state" / "run-session.json"
                session = json.loads(session_path.read_text(encoding="utf-8"))
                result, status = self.helper.pre_command(
                    root_copy, "run-1", "verify.unit", source_environment={"PATH": "/bin"},
                )
                self.assertEqual((result["result"], status), ("PASS", 0))
                session = json.loads(session_path.read_text(encoding="utf-8"))
                reservation = session["reservations"][0]
                attempt_id = reservation["attemptId"]
                reservation.update({
                    "state": terminal,
                    "commandResultRef": f".ai-runs/run-1/commands/verify.unit/{attempt_id}.json",
                    "processAttemptRef": f".ai-runs/run-1/process-attempts/verify.unit/{attempt_id}.json",
                    "terminalAt": "2026-07-11T03:00:03Z",
                })
                session["commandResultRefs"] = [reservation["commandResultRef"]]
                session["processAttemptRefs"] = [reservation["processAttemptRef"]]
                session_path.write_text(json.dumps(session), encoding="utf-8")
                blocked, blocked_status = self.helper.pre_command(
                    root_copy, "run-1", "verify.unit", rerun_reason_path="rerun-reason.txt",
                    source_environment={"PATH": "/bin"},
                )
                self.assertEqual((blocked["result"], blocked_status), ("BLOCKED", 2))
                self.assertEqual(len(json.loads(session_path.read_text(encoding="utf-8"))["reservations"]), 1)
                self.assertFalse((root_copy / ".ai-runs" / "run-1" / "approvals").exists())
                self.assertFalse((root_copy / ".ai-runs" / "run-1" / "policy-violations").exists())

        reserved, reserved_status = self.pre()
        self.assertEqual((reserved["result"], reserved_status), ("PASS", 0))
        duplicate, duplicate_status = self.pre(rerun_reason_path="rerun-reason.txt")
        self.assertEqual((duplicate["result"], duplicate_status), ("BLOCKED", 2))
        self.assertEqual(len(self.session()["reservations"]), 1)

    def test_pre_command_never_launches_or_creates_phase_1b3_artifacts(self):
        with mock.patch.object(self.helper.subprocess, "Popen") as popen:
            result, status = self.pre()
        self.assertEqual((result["result"], status), ("PASS", 0))
        popen.assert_not_called()
        run = self.root / ".ai-runs" / "run-1"
        self.assertFalse((run / "run.json").exists())
        self.assertFalse((run / "artifact-manifest.json").exists())
        self.assertFalse((run / "process-attempts").exists())

class RunLifecycleContinuationTests(unittest.TestCase):
    setUp = RunLifecycleTests.setUp
    write_json = RunLifecycleTests.write_json
    start = RunLifecycleTests.start
    owner_fixture = RunLifecycleTests.owner_fixture
    reserved_fixture = RunLifecycleTests.reserved_fixture
    prepare_reserved_attempt = RunLifecycleTests.prepare_reserved_attempt
    expected_repair_result = RunLifecycleTests.expected_repair_result
    write_lock_owner = RunLifecycleTests.write_lock_owner
    repair = RunLifecycleTests.repair
    age_control_owner = RunLifecycleTests.age_control_owner
    leave_replacement_recovery_partial = RunLifecycleTests.leave_replacement_recovery_partial
    leave_ownerless_replacement_partial = RunLifecycleTests.leave_ownerless_replacement_partial

    def test_public_acquisition_recovers_dead_expired_lock_and_repairs_reserved_attempt(self):
        run, session_path, _session, _process_path = self.prepare_reserved_attempt()
        self.write_lock_owner(run)

        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        try:
            recovered = json.loads(session_path.read_text(encoding="utf-8"))
            self.assertEqual(recovered["reservations"][0]["state"], "BLOCKED")
            self.assertEqual(len(recovered["lockRecoveries"]), 1)
            self.assertEqual(recovered["lockRecoveries"][0]["reason"], "DEAD_AND_EXPIRED")
        finally:
            self.helper.release_run_lock(acquired)

    def test_every_public_acquisition_repairs_reserved_attempt_without_a_stale_lock(self):
        _run, session_path, _session, _process_path = self.prepare_reserved_attempt()

        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        try:
            repaired = json.loads(session_path.read_text(encoding="utf-8"))
            self.assertEqual(repaired["reservations"][0]["state"], "BLOCKED")
            self.assertEqual(repaired["lockRecoveries"], [])
        finally:
            self.helper.release_run_lock(acquired)

    def test_start_run_maps_current_preflight_block_to_run_start_without_mutation(self):
        (self.root / "ai" / "evidence" / "local-helper-runtime.json").unlink()

        result, status = self.helper.start_run(self.root, "run-1", "phase-1b-2-task-2")

        self.assertEqual(
            (result["operation"], result["result"], result["reason"], result["data"], status),
            ("RUN_START", "BLOCKED", "HELPER_RUNTIME_STATE_MISSING", None, 2),
        )
        self.assertFalse((self.root / ".ai-runs").exists())
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())

    def test_lock_directory_is_exclusive_and_release_compares_the_complete_owner_record(self):
        run = self.start()
        acquired = self.helper.acquire_run_lock(self.root, "run-1")

        self.assertEqual(acquired.path, run / ".state" / "lock")
        self.assertEqual(json.loads((acquired.path / "owner.json").read_text(encoding="utf-8")), acquired.owner)
        parsed_owner = uuid_module.UUID(acquired.owner["ownerId"])
        self.assertEqual((parsed_owner.version, parsed_owner.variant), (4, uuid_module.RFC_4122))
        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.acquire_run_lock(self.root, "run-1")
        mutated = dict(acquired.owner)
        mutated["ownerId"] = "55555555-5555-4555-8555-555555555555"
        self.write_json((acquired.path / "owner.json").relative_to(self.root).as_posix(), mutated)
        self.assertFalse(self.helper.release_run_lock(acquired))
        self.assertTrue(acquired.path.exists())
        self.assertEqual(json.loads((acquired.path / "owner.json").read_text(encoding="utf-8")), mutated)

    def test_lock_recovery_blocks_live_or_recent_owner_and_recovers_only_dead_and_expired_owner(self):
        run = self.start()
        lock, live_owner = self.write_lock_owner(
            run, "lock-owner-live.json", pid=os.getpid(), acquiredAt=self.helper.utc_now(),
        )

        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.recover_run_lock(self.root, "run-1")
        self.assertEqual(json.loads((lock / "owner.json").read_text(encoding="utf-8")), live_owner)

        (lock / "owner.json").unlink()
        recent_dead = self.owner_fixture("lock-owner-dead-recent.json", acquiredAt=self.helper.utc_now())
        self.write_json(lock.relative_to(self.root).as_posix() + "/owner.json", recent_dead)
        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.recover_run_lock(self.root, "run-1")
        self.assertEqual(json.loads((lock / "owner.json").read_text(encoding="utf-8")), recent_dead)

        (lock / "owner.json").unlink()
        stale_owner = self.owner_fixture("lock-owner-dead-expired.json")
        self.write_json(lock.relative_to(self.root).as_posix() + "/owner.json", stale_owner)
        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))
        self.assertFalse(lock.exists())
        session_path = run / ".state" / "run-session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        self.helper.validate(self.root, session, "ai/schemas/run-session.schema.json")
        self.assertEqual(len(session["lockRecoveries"]), 1)
        recovery = session["lockRecoveries"][0]
        self.assertEqual(
            (recovery["runId"], recovery["recoveredOwnerId"], recovery["replacementOwnerId"], recovery["reason"]),
            ("run-1", stale_owner["ownerId"], recovery["replacementOwnerId"], "DEAD_AND_EXPIRED"),
        )
        replacement_id = uuid_module.UUID(recovery["replacementOwnerId"])
        self.assertEqual(replacement_id.version, 4)
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())

    def test_lock_owner_ids_are_internal_unique_uuid4_values(self):
        self.start()
        first = self.helper.acquire_run_lock(self.root, "run-1")
        self.assertTrue(self.helper.release_run_lock(first))
        second = self.helper.acquire_run_lock(self.root, "run-1")
        self.assertNotEqual(first.owner["ownerId"], second.owner["ownerId"])
        self.assertEqual(uuid_module.UUID(first.owner["ownerId"]).version, 4)
        self.assertEqual(uuid_module.UUID(second.owner["ownerId"]).version, 4)
        self.assertTrue(self.helper.release_run_lock(second))

    def test_owner_mutation_during_compare_release_preserves_lock(self):
        self.start()
        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        mutated = dict(acquired.owner)
        mutated["ownerId"] = "77777777-7777-4777-8777-777777777777"

        def hook(name, **_context):
            if name == "release.before_unlink":
                self.write_json((acquired.path / "owner.json").relative_to(self.root).as_posix(), mutated)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            self.assertFalse(self.helper.release_run_lock(acquired))
        self.assertTrue(acquired.path.exists())
        self.assertEqual(json.loads((acquired.path / "owner.json").read_text(encoding="utf-8")), mutated)

    def test_session_mutation_requires_exact_held_run_lock(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        current = json.loads(session_path.read_text(encoding="utf-8"))
        replacement = json.loads(json.dumps(current))
        replacement["approvalRefs"].append(".ai-runs/run-1/approvals/one.json")

        with self.assertRaises(self.helper.InvalidStateError):
            self.helper.replace_run_session(
                self.root, session_path, replacement, None, expected_session=current,
            )
        self.assertEqual(json.loads(session_path.read_text(encoding="utf-8")), current)

    def test_repair_rejects_missing_lock_before_immutable_result_publication(self):
        run, _session_path, session, _process_path = self.prepare_reserved_attempt()

        with self.assertRaises(self.helper.InvalidStateError):
            self.helper.repair_reserved_attempts(self.root, session, None)

        self.assertFalse((run / "commands" / "verify.unit" / "attempt-1.json").exists())

    def test_session_compare_barrier_blocks_second_writer_and_preserves_sequential_updates(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        first_lock = self.helper.acquire_run_lock(self.root, "run-1")
        current = json.loads(session_path.read_text(encoding="utf-8"))
        first_update = json.loads(json.dumps(current))
        first_update["approvalRefs"].append(".ai-runs/run-1/approvals/one.json")
        compared = threading.Event()
        release = threading.Event()

        def hook(name, **_context):
            if name == "session.after_compare":
                compared.set()
                if not release.wait(5):
                    raise RuntimeError("session comparison barrier timed out")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            with ThreadPoolExecutor(max_workers=1) as executor:
                writer = executor.submit(
                    self.helper.replace_run_session,
                    self.root,
                    session_path,
                    first_update,
                    first_lock,
                    current,
                )
                self.assertTrue(compared.wait(2))
                with self.assertRaises(self.helper.RegistryBlockedError):
                    self.helper.acquire_run_lock(self.root, "run-1")
                release.set()
                writer.result(timeout=5)
        self.assertTrue(self.helper.release_run_lock(first_lock))

        second_lock = self.helper.acquire_run_lock(self.root, "run-1")
        second_current = json.loads(session_path.read_text(encoding="utf-8"))
        second_update = json.loads(json.dumps(second_current))
        second_update["approvalRefs"].append(".ai-runs/run-1/approvals/two.json")
        self.helper.replace_run_session(
            self.root, session_path, second_update, second_lock, expected_session=second_current,
        )
        self.assertTrue(self.helper.release_run_lock(second_lock))
        persisted = json.loads(session_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["approvalRefs"], [
            ".ai-runs/run-1/approvals/one.json",
            ".ai-runs/run-1/approvals/two.json",
        ])

    def test_session_owner_mutation_before_replace_aborts_without_lost_update(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        current = json.loads(session_path.read_text(encoding="utf-8"))
        replacement = json.loads(json.dumps(current))
        replacement["approvalRefs"].append(".ai-runs/run-1/approvals/one.json")
        mutated_owner = dict(acquired.owner)
        mutated_owner["ownerId"] = "88888888-8888-4888-8888-888888888888"

        def hook(name, **_context):
            if name == "session.before_os_replace":
                self.write_json((acquired.path / "owner.json").relative_to(self.root).as_posix(), mutated_owner)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            with self.assertRaises(self.helper.RegistryBlockedError):
                self.helper.replace_run_session(
                    self.root, session_path, replacement, acquired, expected_session=current,
                )
        self.assertEqual(json.loads(session_path.read_text(encoding="utf-8")), current)
        self.assertTrue(acquired.path.exists())

    def test_concurrent_lock_acquire_has_one_owner_and_one_blocked_contender(self):
        self.start()
        entered = threading.Event()
        release = threading.Event()

        def hook(name, **context):
            if name == "acquire.after_mkdir" and context.get("purpose") == "normal":
                entered.set()
                if not release.wait(5):
                    raise RuntimeError("acquire barrier timed out")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with ThreadPoolExecutor(max_workers=1) as executor:
                winner = executor.submit(self.helper.acquire_run_lock, self.root, "run-1")
                self.assertTrue(entered.wait(2))
                with self.assertRaises(self.helper.RegistryBlockedError):
                    self.helper.acquire_run_lock(self.root, "run-1")
                release.set()
                acquired = winner.result(timeout=5)
        self.assertEqual(json.loads((acquired.path / "owner.json").read_text(encoding="utf-8")), acquired.owner)
        self.assertTrue(self.helper.release_run_lock(acquired))

    def test_stale_owner_mutation_between_recovery_reads_blocks_and_preserves_lock(self):
        run = self.start()
        lock, _owner = self.write_lock_owner(run)
        replacement = self.owner_fixture("lock-owner-dead-expired.json", ownerId="66666666-6666-4666-8666-666666666666")

        def hook(name, **_context):
            if name == "recover.after_initial_owner_read":
                self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), replacement)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(self.helper.RegistryBlockedError):
                self.helper.recover_run_lock(self.root, "run-1")
        self.assertEqual(json.loads((lock / "owner.json").read_text(encoding="utf-8")), replacement)
        self.assertFalse((run / ".state" / "lock-recovery-claim").exists())

    def test_pid_permission_and_reuse_are_conservative_recovery_blocks(self):
        for name, effect in (("permission", PermissionError()), ("reused", None)):
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary) / "repository"
                try:
                    shutil.copytree(original_root / "ai", self.root / "ai")
                    run = self.start()
                    lock, owner = self.write_lock_owner(run)
                    patcher = mock.patch.object(self.helper.os, "kill", side_effect=effect) if effect else mock.patch.object(self.helper.os, "kill", return_value=None)
                    with patcher, self.assertRaises(self.helper.RegistryBlockedError):
                        self.helper.recover_run_lock(self.root, "run-1")
                    self.assertEqual(json.loads((lock / "owner.json").read_text(encoding="utf-8")), owner)
                finally:
                    self.root = original_root

    def test_recovery_quarantine_and_replacement_collisions_fail_closed(self):
        scenarios = ("quarantine", "replacement-mkdir", "replacement-write")
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary) / "repository"
                try:
                    shutil.copytree(original_root / "ai", self.root / "ai")
                    run = self.start()
                    lock, _owner = self.write_lock_owner(run)

                    def hook(name, **context):
                        if scenario == "quarantine" and name == "recover.before_quarantine_rename":
                            context["quarantine"].mkdir()
                        if scenario == "replacement-mkdir" and name == "recover.after_quarantine_rename":
                            lock.mkdir()
                            self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), self.owner_fixture("lock-owner-live.json", pid=os.getpid(), acquiredAt=self.helper.utc_now()))
                        if scenario == "replacement-write" and name == "acquire.after_mkdir" and context.get("purpose") == "recovery":
                            self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), self.owner_fixture("lock-owner-live.json", pid=os.getpid(), acquiredAt=self.helper.utc_now()))

                    with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
                        with self.assertRaises((self.helper.RegistryBlockedError, self.helper.InvalidStateError)):
                            self.helper.recover_run_lock(self.root, "run-1")
                    self.assertTrue(lock.exists())
                    claim = run / ".state" / "lock-recovery-claim"
                    self.assertEqual(claim.exists(), scenario != "quarantine")
                finally:
                    self.root = original_root

    def test_pre_quarantine_recovery_faults_release_still_owned_claim(self):
        scenarios = ("after-claim", "rename-error")
        for scenario in scenarios:
            with self.subTest(scenario=scenario), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary) / "repository"
                try:
                    shutil.copytree(original_root / "ai", self.root / "ai")
                    run = self.start()
                    lock, stale_owner = self.write_lock_owner(run)
                    original_rename = self.helper.os.rename

                    def hook(name, **_context):
                        if scenario == "after-claim" and name == "recover.after_claim":
                            raise OSError("injected after claim")

                    def rename(source, destination):
                        if scenario == "rename-error" and Path(source) == lock:
                            raise OSError("injected quarantine rename failure")
                        return original_rename(source, destination)

                    with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook), mock.patch.object(self.helper.os, "rename", side_effect=rename):
                        with self.assertRaises((OSError, self.helper.RegistryBlockedError)):
                            self.helper.recover_run_lock(self.root, "run-1")
                    self.assertFalse((run / ".state" / "lock-recovery-claim").exists())
                    self.assertEqual(json.loads((lock / "owner.json").read_text(encoding="utf-8")), stale_owner)
                finally:
                    self.root = original_root

    def test_claim_owner_mutation_prevents_cleanup_and_preserves_mutated_claim(self):
        run = self.start()
        self.write_lock_owner(run)
        claim_path = run / ".state" / "lock-recovery-claim"
        mutated = self.owner_fixture(
            "lock-owner-live.json",
            ownerId="99999999-9999-4999-8999-999999999999",
            pid=os.getpid(),
            acquiredAt=self.helper.utc_now(),
        )

        def hook(name, **_context):
            if name == "recover.after_claim":
                self.write_json((claim_path / "owner.json").relative_to(self.root).as_posix(), mutated)
                raise OSError("injected claim-owner mutation")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            with self.assertRaises(OSError):
                self.helper.recover_run_lock(self.root, "run-1")
        self.assertTrue(claim_path.exists())
        self.assertEqual(json.loads((claim_path / "owner.json").read_text(encoding="utf-8")), mutated)

    def test_existing_recovery_claim_live_or_recent_blocks_but_dead_and_expired_is_reacquired(self):
        cases = ("live", "recent", "expired")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary) / "repository"
                try:
                    shutil.copytree(original_root / "ai", self.root / "ai")
                    run = self.start()
                    self.write_lock_owner(run)
                    claim = run / ".state" / "lock-recovery-claim"
                    claim.mkdir()
                    if case == "live":
                        owner = self.owner_fixture("lock-owner-live.json", pid=os.getpid(), acquiredAt=self.helper.utc_now())
                    elif case == "recent":
                        owner = self.owner_fixture("lock-owner-dead-recent.json", acquiredAt=self.helper.utc_now())
                    else:
                        owner = self.owner_fixture("lock-owner-dead-expired.json")
                    self.write_json((claim / "owner.json").relative_to(self.root).as_posix(), owner)

                    if case == "expired":
                        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))
                        self.assertFalse(claim.exists())
                    else:
                        with self.assertRaises(self.helper.RegistryBlockedError):
                            self.helper.recover_run_lock(self.root, "run-1")
                        self.assertEqual(json.loads((claim / "owner.json").read_text(encoding="utf-8")), owner)
                finally:
                    self.root = original_root

    def test_recovery_resumes_exact_single_quarantine_after_crash_before_replacement(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        _lock, stale_owner = self.write_lock_owner(run)
        seen = []

        def hook(name, **context):
            if name == "recover.after_quarantine_rename":
                seen.append(context["quarantine"])
                raise OSError("injected crash after quarantine")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            with self.assertRaises(OSError):
                self.helper.recover_run_lock(self.root, "run-1")
        quarantine = seen[0]
        claim = run / ".state" / "lock-recovery-claim"
        stale_claim_owner = self.owner_fixture("lock-owner-dead-expired.json")
        self.write_json((claim / "owner.json").relative_to(self.root).as_posix(), stale_claim_owner)
        self.assertFalse((run / ".state" / "lock").exists())

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        self.assertFalse(quarantine.exists())
        self.assertFalse(claim.exists())
        session = json.loads(session_path.read_text(encoding="utf-8"))
        self.assertEqual(len(session["lockRecoveries"]), 1)
        self.assertEqual(session["lockRecoveries"][0]["recoveredOwnerId"], stale_owner["ownerId"])

    def test_multiple_or_contradictory_recovery_quarantines_are_preserved(self):
        for case in ("multiple", "contradictory"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary) / "repository"
                try:
                    shutil.copytree(original_root / "ai", self.root / "ai")
                    run = self.start()
                    state = run / ".state"
                    if case == "multiple":
                        names = (
                            "lock-recovery-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
                            "lock-recovery-bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
                        )
                    else:
                        names = ("lock-recovery-aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",)
                    for name in names:
                        quarantine = state / name
                        quarantine.mkdir()
                        self.write_json((quarantine / "owner.json").relative_to(self.root).as_posix(), self.owner_fixture("lock-owner-dead-expired.json"))
                    if case == "contradictory":
                        (state / names[0] / "unexpected").write_text("preserve", encoding="utf-8")

                    with self.assertRaises((self.helper.InvalidStateError, self.helper.RegistryBlockedError)):
                        self.helper.recover_run_lock(self.root, "run-1")
                    for name in names:
                        self.assertTrue((state / name).exists())
                finally:
                    self.root = original_root

    def test_owner_publication_oserror_cleans_only_owned_empty_initialization_directory(self):
        run = self.start()
        state = run / ".state"
        fsynced = []
        original_fsync = self.helper.fsync_directory

        def fsync(path):
            fsynced.append(Path(path))
            return original_fsync(path)

        with mock.patch.object(self.helper, "exclusive_write", side_effect=OSError("injected owner write failure")), mock.patch.object(self.helper, "fsync_directory", side_effect=fsync):
            with self.assertRaises(OSError):
                self.helper.acquire_run_lock(self.root, "run-1")
        self.assertFalse((state / "lock").exists())
        self.assertIn(state, fsynced)

    def test_crash_after_lock_mkdir_leaves_recent_ownerless_initialization_blocked(self):
        run = self.start()
        lock = run / ".state" / "lock"

        class SimulatedCrash(BaseException):
            pass

        def hook(name, **_context):
            if name == "acquire.after_mkdir":
                raise SimulatedCrash()

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            with self.assertRaises(SimulatedCrash):
                self.helper.acquire_run_lock(self.root, "run-1")
        self.assertTrue(lock.is_dir())
        self.assertEqual(list(lock.iterdir()), [])
        with self.assertRaises(self.helper.RegistryBlockedError) as blocked:
            self.helper.acquire_run_lock(self.root, "run-1")
        self.assertEqual(blocked.exception.errors[0]["code"], "RUN_LOCK_INITIALIZING")

    def test_expired_empty_ownerless_lock_is_quarantined_removed_and_retryable(self):
        run = self.start()
        lock = run / ".state" / "lock"
        lock.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        self.assertFalse(lock.exists())
        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        self.assertTrue(self.helper.release_run_lock(acquired))

    def test_ownerless_main_cleanup_resumes_after_initialization_quarantine_crash(self):
        run = self.start()
        state = run / ".state"
        lock = state / "lock"
        lock.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))
        observed = {}

        class SimulatedCrash(BaseException):
            pass

        def hook(name, **context):
            if name == "recover.ownerless_after_quarantine_rename":
                observed["quarantine"] = context["quarantine"]
                raise SimulatedCrash()

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(SimulatedCrash):
                self.helper.recover_run_lock(self.root, "run-1")
        claim = state / "lock-recovery-claim"
        self.assertEqual(list(observed["quarantine"].iterdir()), [])
        self.age_control_owner(claim)

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        self.assertFalse(lock.exists())
        self.assertFalse(observed["quarantine"].exists())
        self.assertFalse(claim.exists())

    def test_normal_acquisition_blocks_during_stale_claim_replacement_gap(self):
        run = self.start()
        state = run / ".state"
        lock = state / "lock"
        lock.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))
        observed = {}

        class SimulatedCrash(BaseException):
            pass

        def crash_after_initialization_quarantine(name, **context):
            if name == "recover.ownerless_after_quarantine_rename":
                observed["quarantine"] = context["quarantine"]
                raise SimulatedCrash()

        with mock.patch.object(
            self.helper, "run_lifecycle_hook", side_effect=crash_after_initialization_quarantine, create=True,
        ):
            with self.assertRaises(SimulatedCrash):
                self.helper.recover_run_lock(self.root, "run-1")

        claim = state / "lock-recovery-claim"
        self.age_control_owner(claim)
        gap_open = threading.Event()
        continue_recovery = threading.Event()
        original_create = self.helper.create_recovery_claim

        def create_with_replacement_barrier(path, run_id):
            if Path(path) == claim and not claim.exists():
                gap_open.set()
                if not continue_recovery.wait(timeout=5):
                    raise AssertionError("stale-claim replacement barrier timed out")
            return original_create(path, run_id)

        normal_lock = None
        normal_error = None
        with mock.patch.object(self.helper, "create_recovery_claim", side_effect=create_with_replacement_barrier):
            with ThreadPoolExecutor(max_workers=1) as executor:
                recovery = executor.submit(self.helper.recover_run_lock, self.root, "run-1")
                self.assertTrue(gap_open.wait(timeout=5), "recovery did not enter the claim replacement gap")
                self.assertFalse(claim.exists())
                self.assertTrue(observed["quarantine"].exists())
                try:
                    normal_lock = self.helper.acquire_run_lock(self.root, "run-1")
                except Exception as error:
                    normal_error = error
                finally:
                    if normal_lock is not None:
                        self.helper.release_run_lock(normal_lock)
                    continue_recovery.set()
                self.assertTrue(recovery.result(timeout=5))

        self.assertIsInstance(normal_error, self.helper.RegistryBlockedError)
        self.assertFalse(observed["quarantine"].exists())
        self.assertFalse(claim.exists())

    def test_ownerless_main_cleanup_resumes_after_quarantine_removal_crash(self):
        run = self.start()
        state = run / ".state"
        lock = state / "lock"
        lock.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))

        class SimulatedCrash(BaseException):
            pass

        def hook(name, **_context):
            if name == "recover.ownerless_after_quarantine_removal":
                raise SimulatedCrash()

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(SimulatedCrash):
                self.helper.recover_run_lock(self.root, "run-1")
        claim = state / "lock-recovery-claim"
        self.assertTrue(claim.is_dir())
        self.assertFalse(lock.exists())
        self.assertFalse(any(item.name.startswith("lock-initialization-quarantine-") for item in state.iterdir()))
        self.age_control_owner(claim)

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        self.assertFalse(claim.exists())
        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        self.assertTrue(self.helper.release_run_lock(acquired))

    def test_expired_nonempty_ownerless_lock_is_preserved_and_refused(self):
        run = self.start()
        lock = run / ".state" / "lock"
        lock.mkdir()
        (lock / "unexpected").write_text("preserve", encoding="utf-8")
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))

        with self.assertRaises((self.helper.InvalidStateError, self.helper.RegistryBlockedError)):
            self.helper.recover_run_lock(self.root, "run-1")

        self.assertTrue((lock / "unexpected").is_file())
        self.assertFalse((run / ".state" / "lock-recovery-claim").exists())

    def test_concurrent_ownerless_recovery_has_one_cleanup_winner(self):
        run = self.start()
        lock = run / ".state" / "lock"
        lock.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))
        barrier = threading.Barrier(2)

        def hook(name, **_context):
            if name == "recover.before_claim":
                barrier.wait(timeout=5)

        def recover():
            try:
                return self.helper.recover_run_lock(self.root, "run-1")
            except (self.helper.InvalidStateError, self.helper.RegistryBlockedError):
                return False

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(lambda _index: recover(), range(2)))
        self.assertEqual(outcomes.count(True), 1)
        self.assertFalse(lock.exists())

    def test_failed_recovery_history_write_preserves_quarantine_replacement_lock_and_session(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        before_session = session_path.read_bytes()
        lock, _owner = self.write_lock_owner(run)
        quarantine_seen = []

        def hook(name, **context):
            if name == "recover.after_quarantine_rename":
                quarantine_seen.append(context["quarantine"])
            if name == "recover.before_history_write":
                raise OSError("injected history write failure")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(OSError):
                self.helper.recover_run_lock(self.root, "run-1")
        self.assertTrue(lock.exists())
        self.assertTrue(quarantine_seen[0].exists())
        self.assertEqual(session_path.read_bytes(), before_session)

    def test_failed_recovery_session_write_preserves_quarantine_replacement_lock_and_session(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        before_session = session_path.read_bytes()
        lock, _owner = self.write_lock_owner(run)
        quarantine_seen = []

        def hook(name, **context):
            if name == "recover.after_quarantine_rename":
                quarantine_seen.append(context["quarantine"])
            if name == "session.before_replace":
                raise OSError("injected recovery session write failure")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook):
            with self.assertRaises(OSError):
                self.helper.recover_run_lock(self.root, "run-1")
        self.assertTrue(lock.exists())
        self.assertTrue(quarantine_seen[0].exists())
        self.assertEqual(session_path.read_bytes(), before_session)

    def test_concurrent_recovery_allows_one_replacement_and_one_fail_closed_contender(self):
        run = self.start()
        self.write_lock_owner(run)
        barrier = threading.Barrier(2)

        def hook(name, **_context):
            if name == "recover.after_initial_owner_read":
                barrier.wait(timeout=5)

        def recover():
            try:
                return self.helper.recover_run_lock(self.root, "run-1")
            except (self.helper.RegistryBlockedError, self.helper.InvalidStateError) as error:
                return type(error).__name__ + ":" + str(error)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(lambda _index: recover(), range(2)))
        self.assertEqual(outcomes.count(True), 1, outcomes)
        self.assertEqual(len([outcome for outcome in outcomes if outcome is not True]), 1)
        session = json.loads((run / ".state" / "run-session.json").read_text(encoding="utf-8"))
        self.assertEqual(len(session["lockRecoveries"]), 1)

    def test_start_run_cleans_its_new_run_when_session_publication_crashes(self):
        original = self.helper.exclusive_publish_json

        def fail_before_publication(*_args):
            raise OSError("simulated publication failure")

        self.helper.exclusive_publish_json = fail_before_publication
        try:
            result, status = self.helper.start_run(self.root, "run-1", "phase-1b-2-task-2")
        finally:
            self.helper.exclusive_publish_json = original

        self.assertEqual((result["operation"], result["result"], result["reason"], result["data"], status), (
            "RUN_START", "INVALID_STATE", "RUN_SESSION_PUBLICATION_FAILED", None, 5,
        ))
        self.assertFalse((self.root / ".ai-runs" / "run-1").exists())
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())

    def test_reserved_attempt_with_exact_process_evidence_is_repaired_only_to_blocked(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        reservation = {
            "attemptId": "attempt-1",
            "commandId": "verify.unit",
            "argvHash": "a" * 64,
            "inputFingerprint": "b" * 64,
            "environmentFingerprint": "c" * 64,
            "reservedAt": "2026-07-11T03:00:01Z",
            "state": "RESERVED",
            "commandResultRef": None,
            "processAttemptRef": None,
            "terminalAt": None,
            "rerunReasonHash": None,
            "rerunOfAttemptId": None,
        }
        session["reservations"] = [reservation]
        self.write_json(session_path.relative_to(self.root).as_posix(), session)
        process = json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / "process-attempt-exited.json").read_text(encoding="utf-8"))
        process.update({
            "argvHash": reservation["argvHash"],
            "inputFingerprint": reservation["inputFingerprint"],
            "environmentFingerprint": reservation["environmentFingerprint"],
        })
        process_path = run / "process-attempts" / "verify.unit" / "attempt-1.json"
        self.write_json(process_path.relative_to(self.root).as_posix(), process)

        repaired = self.repair(session)

        repaired_reservation = repaired["reservations"][0]
        command_path = run / "commands" / "verify.unit" / "attempt-1.json"
        self.assertEqual(repaired_reservation["state"], "BLOCKED")
        self.assertTrue(command_path.is_file())
        self.assertEqual(repaired_reservation["commandResultRef"], ".ai-runs/run-1/commands/verify.unit/attempt-1.json")
        self.assertEqual(repaired_reservation["processAttemptRef"], ".ai-runs/run-1/process-attempts/verify.unit/attempt-1.json")
        repaired_result = json.loads(command_path.read_text(encoding="utf-8"))
        self.helper.validate(self.root, repaired_result, "ai/schemas/command-result.schema.json")
        self.assertEqual((repaired_result["result"], repaired_result["reason"], repaired_result["processExitCode"]), (
            "BLOCKED", "STALE_RESERVED_REPAIRED", None,
        ))
        persisted = json.loads(session_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted, repaired)
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())

    def test_reserved_attempt_with_malformed_process_evidence_remains_reserved(self):
        run = self.start()
        session_path = run / ".state" / "run-session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["reservations"] = [{
            "attemptId": "attempt-1", "commandId": "verify.unit", "argvHash": "a" * 64,
            "inputFingerprint": "b" * 64, "environmentFingerprint": "c" * 64,
            "reservedAt": "2026-07-11T03:00:01Z", "state": "RESERVED", "commandResultRef": None,
            "processAttemptRef": None, "terminalAt": None, "rerunReasonHash": None, "rerunOfAttemptId": None,
        }]
        self.write_json(session_path.relative_to(self.root).as_posix(), session)
        malformed = {"runId": "run-1"}
        process_path = run / "process-attempts" / "verify.unit" / "attempt-1.json"
        self.write_json(process_path.relative_to(self.root).as_posix(), malformed)

        repaired = self.repair(session)

        self.assertEqual(repaired["reservations"][0]["state"], "RESERVED")
        self.assertFalse((run / "commands" / "verify.unit" / "attempt-1.json").exists())
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())

    def test_repair_rejects_process_attempts_read_through_an_ancestor_symlink_where_supported(self):
        run, _session_path, session, _process_path = self.prepare_reserved_attempt(process=False)
        with tempfile.TemporaryDirectory() as temporary:
            external = Path(temporary) / "process-attempts"
            target = external / "verify.unit" / "attempt-1.json"
            target.parent.mkdir(parents=True)
            target.write_text(json.dumps(self.reserved_fixture()["processAttempt"]), encoding="utf-8")
            try:
                (run / "process-attempts").symlink_to(external, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("directory symlinks are unavailable in this test environment")

            repaired = self.repair(session)

            self.assertEqual(repaired["reservations"][0]["state"], "RESERVED")
            self.assertFalse((run / "commands").exists())

    def test_repair_rejects_command_result_write_through_an_ancestor_symlink_where_supported(self):
        run, _session_path, session, _process_path = self.prepare_reserved_attempt()
        with tempfile.TemporaryDirectory() as temporary:
            external = Path(temporary) / "commands"
            external.mkdir()
            try:
                (run / "commands").symlink_to(external, target_is_directory=True)
            except (NotImplementedError, OSError):
                self.skipTest("directory symlinks are unavailable in this test environment")

            repaired = self.repair(session)

            self.assertEqual(repaired["reservations"][0]["state"], "RESERVED")
            self.assertFalse((external / "verify.unit" / "attempt-1.json").exists())

    def test_stranded_valid_repair_result_completes_reserved_session_transition(self):
        run, session_path, session, _process_path = self.prepare_reserved_attempt()
        command_path = run / "commands" / "verify.unit" / "attempt-1.json"
        stranded = self.expected_repair_result()
        self.write_json(command_path.relative_to(self.root).as_posix(), stranded)
        before = command_path.read_bytes()

        repaired = self.repair(session)

        self.assertEqual(repaired["reservations"][0]["state"], "BLOCKED")
        self.assertEqual(command_path.read_bytes(), before)
        self.assertEqual(json.loads(session_path.read_text(encoding="utf-8")), repaired)

    def test_malformed_or_contradictory_existing_repair_result_never_mutates_session_or_artifact(self):
        run, session_path, session, _process_path = self.prepare_reserved_attempt()
        command_path = run / "commands" / "verify.unit" / "attempt-1.json"
        contradictory = self.expected_repair_result()
        contradictory["reason"] = "contradictory"
        self.write_json(command_path.relative_to(self.root).as_posix(), contradictory)
        before_session = session_path.read_bytes()
        before_result = command_path.read_bytes()

        repaired = self.repair(session)

        self.assertEqual(repaired["reservations"][0]["state"], "RESERVED")
        self.assertEqual(session_path.read_bytes(), before_session)
        self.assertEqual(command_path.read_bytes(), before_result)

    def test_session_write_failure_after_repair_publication_resumes_without_overwrite(self):
        run, session_path, session, _process_path = self.prepare_reserved_attempt()
        command_path = run / "commands" / "verify.unit" / "attempt-1.json"
        failed = {"done": False}

        def hook(name, **_context):
            if name == "session.before_replace" and not failed["done"]:
                failed["done"] = True
                raise OSError("injected session write failure")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(OSError):
                self.repair(session)

        stranded_bytes = command_path.read_bytes()
        self.assertEqual(json.loads(session_path.read_text(encoding="utf-8"))["reservations"][0]["state"], "RESERVED")
        resumed = self.repair(json.loads(session_path.read_text(encoding="utf-8")))
        self.assertEqual(resumed["reservations"][0]["state"], "BLOCKED")
        self.assertEqual(command_path.read_bytes(), stranded_bytes)

    def test_repair_publication_collision_validates_winner_and_never_overwrites(self):
        run, session_path, session, _process_path = self.prepare_reserved_attempt()
        command_path = run / "commands" / "verify.unit" / "attempt-1.json"
        winner = self.expected_repair_result()

        def hook(name, **context):
            if name == "repair.before_publish" and not command_path.exists():
                self.write_json(command_path.relative_to(self.root).as_posix(), winner)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            repaired = self.repair(session)

        self.assertEqual(repaired["reservations"][0]["state"], "BLOCKED")
        self.assertEqual(json.loads(command_path.read_text(encoding="utf-8")), winner)
        self.assertEqual(json.loads(session_path.read_text(encoding="utf-8")), repaired)

    def test_repair_requires_launched_process_and_blocks_missing_or_mismatched_attempts(self):
        cases = (
            ("missing", None),
            ("spawn-failed", json.loads((PHASE_1B_GATEWAY_FIXTURES_PATH / "process-attempt-spawn-failed.json").read_text(encoding="utf-8"))),
            ("tuple-mismatch", {**self.reserved_fixture()["processAttempt"], "attemptId": "other-attempt"}),
        )
        for name, process in cases:
            with self.subTest(case=name), tempfile.TemporaryDirectory() as temporary:
                original_root = self.root
                self.root = Path(temporary) / "repository"
                try:
                    shutil.copytree(original_root / "ai", self.root / "ai")
                    run, session_path, session, process_path = self.prepare_reserved_attempt(process=False)
                    if process is not None:
                        self.write_json(process_path.relative_to(self.root).as_posix(), process)
                    before_session = session_path.read_bytes()

                    repaired = self.repair(session)

                    self.assertEqual(repaired["reservations"][0]["state"], "RESERVED")
                    self.assertEqual(session_path.read_bytes(), before_session)
                    self.assertFalse((run / "commands" / "verify.unit" / "attempt-1.json").exists())
                finally:
                    self.root = original_root

    def test_repair_session_compare_and_swap_preserves_concurrent_session_update(self):
        run, session_path, session, _process_path = self.prepare_reserved_attempt()
        concurrent_ref = ".ai-runs/run-1/approvals/concurrent.json"

        def hook(name, **_context):
            if name == "session.before_replace":
                current = json.loads(session_path.read_text(encoding="utf-8"))
                if concurrent_ref not in current["approvalRefs"]:
                    current["approvalRefs"].append(concurrent_ref)
                    self.write_json(session_path.relative_to(self.root).as_posix(), current)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(self.helper.RegistryBlockedError):
                self.repair(session)

        persisted = json.loads(session_path.read_text(encoding="utf-8"))
        self.assertEqual(persisted["approvalRefs"], [concurrent_ref])
        self.assertEqual(persisted["reservations"][0]["state"], "RESERVED")
        self.assertTrue((run / "commands" / "verify.unit" / "attempt-1.json").is_file())

    def test_recovery_resumes_replacement_lock_failure_before_history_without_duplicate(self):
        run, quarantine, replacement, replacement_owner = self.leave_replacement_recovery_partial(
            "recover.before_history_write",
        )
        recovery_uuid = quarantine.name.removeprefix("lock-recovery-")
        self.assertEqual(replacement_owner["ownerId"], recovery_uuid)

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        session = json.loads((run / ".state" / "run-session.json").read_text(encoding="utf-8"))
        self.assertEqual(len(session["lockRecoveries"]), 1)
        history = session["lockRecoveries"][0]
        self.assertEqual(history["recoveryId"], quarantine.name)
        self.assertEqual(history["replacementOwnerId"], replacement_owner["ownerId"])
        self.assertFalse(quarantine.exists())
        self.assertFalse(replacement.exists())

    def test_recovery_resumes_ownerless_replacement_after_mkdir_crash(self):
        run, quarantine, replacement, claim = self.leave_ownerless_replacement_partial()

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        session = json.loads((run / ".state" / "run-session.json").read_text(encoding="utf-8"))
        self.assertEqual(len(session["lockRecoveries"]), 1)
        self.assertEqual((session["lockRecoveries"][0]["recoveryId"], session["lockRecoveries"][0]["replacementOwnerId"]), (
            quarantine.name, quarantine.name.removeprefix("lock-recovery-"),
        ))
        self.assertFalse(replacement.exists())
        self.assertFalse(quarantine.exists())
        self.assertFalse(claim.exists())

    def test_ownerless_replacement_resume_aborts_when_held_claim_owner_changes(self):
        _run, quarantine, replacement, claim = self.leave_ownerless_replacement_partial()
        mutated = self.helper.new_run_lock_owner("run-1")

        def hook(name, **_context):
            if name == "recover.replacement_before_owner_publication":
                self.write_json((claim / "owner.json").relative_to(self.root).as_posix(), mutated)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(self.helper.RegistryBlockedError):
                self.helper.recover_run_lock(self.root, "run-1")

        self.assertEqual(list(replacement.iterdir()), [])
        self.assertTrue(quarantine.exists())
        self.assertEqual(self.helper.read_run_lock_owner(claim / "owner.json", "run-1"), mutated)

    def test_recovery_rejects_mismatched_replacement_uuid_without_history(self):
        run, quarantine, replacement, _replacement_owner = self.leave_replacement_recovery_partial(
            "recover.before_history_write",
        )
        mismatched_owner = self.age_control_owner(replacement)
        mismatched_owner["ownerId"] = str(uuid_module.uuid4())
        while mismatched_owner["ownerId"] == quarantine.name.removeprefix("lock-recovery-"):
            mismatched_owner["ownerId"] = str(uuid_module.uuid4())
        self.write_json((replacement / "owner.json").relative_to(self.root).as_posix(), mismatched_owner)

        with self.assertRaises(self.helper.InvalidStateError):
            self.helper.recover_run_lock(self.root, "run-1")

        self.assertTrue(quarantine.exists())
        self.assertTrue(replacement.exists())
        session = json.loads((run / ".state" / "run-session.json").read_text(encoding="utf-8"))
        self.assertEqual(session["lockRecoveries"], [])

    def test_normal_lock_acquire_blocks_active_recovery_claim_before_lock_creation(self):
        run = self.start()
        state = run / ".state"
        claim = self.helper.create_recovery_claim(state / "lock-recovery-claim", "run-1")

        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.acquire_run_lock(self.root, "run-1")

        self.assertFalse((state / "lock").exists())
        self.assertTrue(self.helper.release_run_lock(claim))

    def test_normal_lock_acquire_blocks_recovery_quarantine_before_lock_creation(self):
        run = self.start()
        state = run / ".state"
        recovery_uuid = str(uuid_module.uuid4())
        quarantine = state / f"lock-recovery-{recovery_uuid}"
        quarantine.mkdir()
        owner = self.owner_fixture("lock-owner-dead-expired.json")
        self.write_json((quarantine / "owner.json").relative_to(self.root).as_posix(), owner)

        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.acquire_run_lock(self.root, "run-1")

        self.assertFalse((state / "lock").exists())
        self.assertEqual(self.helper.read_run_lock_owner(quarantine / "owner.json", "run-1"), owner)

    def test_recovery_resumes_replacement_lock_failure_during_history_publication(self):
        run, quarantine, replacement, replacement_owner = self.leave_replacement_recovery_partial(
            "session.before_os_replace",
        )

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        history = json.loads((run / ".state" / "run-session.json").read_text(encoding="utf-8"))["lockRecoveries"]
        self.assertEqual(len(history), 1)
        self.assertEqual((history[0]["recoveryId"], history[0]["replacementOwnerId"]), (
            quarantine.name, replacement_owner["ownerId"],
        ))
        self.assertFalse(replacement.exists())

    def test_recovery_resumes_after_history_publication_without_duplicate_history(self):
        run, quarantine, replacement, replacement_owner = self.leave_replacement_recovery_partial(
            "recover.after_history_publication",
        )
        before = json.loads((run / ".state" / "run-session.json").read_text(encoding="utf-8"))
        self.assertEqual(len(before["lockRecoveries"]), 1)

        self.assertTrue(self.helper.recover_run_lock(self.root, "run-1"))

        after = json.loads((run / ".state" / "run-session.json").read_text(encoding="utf-8"))
        self.assertEqual(after["lockRecoveries"], before["lockRecoveries"])
        self.assertEqual(after["lockRecoveries"][0]["replacementOwnerId"], replacement_owner["ownerId"])
        self.assertFalse(quarantine.exists())
        self.assertFalse(replacement.exists())

    def test_recovery_preserves_live_replacement_and_history_mismatch(self):
        run, quarantine, replacement, _replacement_owner = self.leave_replacement_recovery_partial(
            "recover.after_history_publication",
        )
        live_owner = self.helper.new_run_lock_owner("run-1")
        self.write_json((replacement / "owner.json").relative_to(self.root).as_posix(), live_owner)

        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.recover_run_lock(self.root, "run-1")
        self.assertTrue(quarantine.exists())
        self.assertTrue(replacement.exists())

        self.age_control_owner(replacement)
        session_path = run / ".state" / "run-session.json"
        session = json.loads(session_path.read_text(encoding="utf-8"))
        session["lockRecoveries"][0]["replacementOwnerId"] = str(uuid_module.uuid4())
        self.write_json(session_path.relative_to(self.root).as_posix(), session)
        with self.assertRaises(self.helper.InvalidStateError):
            self.helper.recover_run_lock(self.root, "run-1")
        self.assertTrue(quarantine.exists())
        self.assertTrue(replacement.exists())

    def test_recovery_claim_crash_after_mkdir_leaves_recent_initialization_blocked(self):
        run = self.start()
        state = run / ".state"
        claim = state / "lock-recovery-claim"

        def crash(name, **_context):
            if name == "recover.claim_after_mkdir":
                raise RuntimeError("injected process death")

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=crash, create=True):
            with self.assertRaises(RuntimeError):
                self.helper.acquire_recovery_claim(state, "run-1")
        self.assertEqual(list(claim.iterdir()), [])
        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.acquire_recovery_claim(state, "run-1")
        self.assertTrue(claim.is_dir())

    def test_expired_empty_ownerless_recovery_claim_is_replaced(self):
        run = self.start()
        state = run / ".state"
        claim = state / "lock-recovery-claim"
        claim.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(claim, (expired, expired))

        acquired = self.helper.acquire_recovery_claim(state, "run-1")

        self.assertEqual(acquired.path, claim)
        self.assertTrue((claim / "owner.json").is_file())
        self.assertTrue(self.helper.release_run_lock(acquired))

    def test_ownerless_recovery_claim_publication_error_cleans_exact_empty_directory(self):
        run = self.start()
        state = run / ".state"
        claim = state / "lock-recovery-claim"
        original = self.helper.exclusive_write

        def fail(path, content, mode=0o600):
            if path == claim / "owner.json":
                raise OSError("injected claim owner publication failure")
            return original(path, content, mode)

        with mock.patch.object(self.helper, "exclusive_write", side_effect=fail):
            with self.assertRaises(OSError):
                self.helper.acquire_recovery_claim(state, "run-1")
        self.assertFalse(claim.exists())

    def test_concurrent_expired_ownerless_claim_recovery_has_one_winner(self):
        run = self.start()
        state = run / ".state"
        claim = state / "lock-recovery-claim"
        claim.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(claim, (expired, expired))
        barrier = threading.Barrier(2)

        def hook(name, **_context):
            if name == "recover.claim_before_ownerless_quarantine":
                barrier.wait(timeout=5)

        def acquire():
            try:
                return self.helper.acquire_recovery_claim(state, "run-1")
            except (self.helper.RegistryBlockedError, self.helper.InvalidStateError):
                return None

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with ThreadPoolExecutor(max_workers=2) as executor:
                outcomes = list(executor.map(lambda _index: acquire(), range(2)))
        winners = [item for item in outcomes if item is not None]
        self.assertEqual(len(winners), 1)
        self.assertTrue(self.helper.release_run_lock(winners[0]))

    def test_late_owner_on_ownerless_recovery_claim_is_restored_and_blocks(self):
        run = self.start()
        state = run / ".state"
        claim = state / "lock-recovery-claim"
        claim.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(claim, (expired, expired))
        late_owner = self.helper.new_run_lock_owner("run-1")

        def hook(name, **_context):
            if name == "recover.claim_before_ownerless_quarantine":
                self.write_json((claim / "owner.json").relative_to(self.root).as_posix(), late_owner)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(self.helper.RegistryBlockedError):
                self.helper.acquire_recovery_claim(state, "run-1")

        self.assertEqual(self.helper.read_run_lock_owner(claim / "owner.json", "run-1"), late_owner)
        self.assertFalse(any(item.name.startswith("lock-recovery-claim-initialization-") for item in state.iterdir()))

    def test_late_claim_owner_quarantine_is_preserved_when_fixed_path_is_taken(self):
        run = self.start()
        state = run / ".state"
        claim = state / "lock-recovery-claim"
        claim.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(claim, (expired, expired))
        late_owner = self.helper.new_run_lock_owner("run-1")
        competing_owner = self.helper.new_run_lock_owner("run-1")

        def hook(name, **_context):
            if name == "recover.claim_before_ownerless_quarantine":
                self.write_json((claim / "owner.json").relative_to(self.root).as_posix(), late_owner)
            if name == "recover.claim_after_ownerless_quarantine_rename":
                claim.mkdir()
                self.write_json((claim / "owner.json").relative_to(self.root).as_posix(), competing_owner)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(self.helper.InvalidStateError):
                self.helper.acquire_recovery_claim(state, "run-1")

        quarantines = [
            item for item in state.iterdir() if item.name.startswith("lock-recovery-claim-initialization-")
        ]
        self.assertEqual(len(quarantines), 1)
        self.assertEqual(self.helper.read_run_lock_owner(quarantines[0] / "owner.json", "run-1"), late_owner)
        self.assertEqual(self.helper.read_run_lock_owner(claim / "owner.json", "run-1"), competing_owner)

    def test_late_owner_on_ownerless_lock_is_restored_and_blocks_second_owner(self):
        run = self.start()
        lock = run / ".state" / "lock"
        lock.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))
        late_owner = self.helper.new_run_lock_owner("run-1")

        def hook(name, **_context):
            if name == "recover.ownerless_after_age_check":
                self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), late_owner)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(self.helper.RegistryBlockedError):
                self.helper.recover_run_lock(self.root, "run-1")
        self.assertEqual(self.helper.read_run_lock_owner(lock / "owner.json", "run-1"), late_owner)
        self.assertFalse(any(item.name.startswith("lock-initialization-quarantine-") for item in lock.parent.iterdir()))
        with self.assertRaises(self.helper.RegistryBlockedError):
            self.helper.acquire_run_lock(self.root, "run-1")

    def test_late_owner_quarantine_is_preserved_when_original_lock_path_is_taken(self):
        run = self.start()
        state = run / ".state"
        lock = state / "lock"
        lock.mkdir()
        expired = time.time() - self.helper.RUN_LOCK_MAX_RECENT_SECONDS - 10
        os.utime(lock, (expired, expired))
        late_owner = self.helper.new_run_lock_owner("run-1")
        competing_owner = self.helper.new_run_lock_owner("run-1")

        def hook(name, **_context):
            if name == "recover.ownerless_after_age_check":
                self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), late_owner)
            if name == "recover.ownerless_after_quarantine_rename":
                lock.mkdir()
                self.write_json((lock / "owner.json").relative_to(self.root).as_posix(), competing_owner)

        with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=hook, create=True):
            with self.assertRaises(self.helper.InvalidStateError):
                self.helper.recover_run_lock(self.root, "run-1")
        quarantines = [item for item in state.iterdir() if item.name.startswith("lock-initialization-quarantine-")]
        self.assertEqual(len(quarantines), 1)
        self.assertEqual(self.helper.read_run_lock_owner(quarantines[0] / "owner.json", "run-1"), late_owner)
        self.assertEqual(self.helper.read_run_lock_owner(lock / "owner.json", "run-1"), competing_owner)

    def test_start_run_rejects_invalid_existing_symlinked_and_unsafe_run_paths(self):
        invalid, invalid_status = self.helper.start_run(self.root, "../run", "phase-1b-2-task-2")
        self.assertEqual((invalid["result"], invalid_status), ("POLICY_VIOLATION", 4))
        invalid_task, invalid_task_status = self.helper.start_run(self.root, "other-run", "../task")
        self.assertEqual((invalid_task["result"], invalid_task_status), ("POLICY_VIOLATION", 4))

        self.start()
        existing, existing_status = self.helper.start_run(self.root, "run-1", "phase-1b-2-task-2")
        self.assertEqual((existing["result"], existing_status), ("BLOCKED", 2))

        with tempfile.TemporaryDirectory() as temporary:
            external = Path(temporary) / "runs"
            external.mkdir()
            symlink_root = Path(temporary) / "repository"
            shutil.copytree(self.root / "ai", symlink_root / "ai")
            try:
                (symlink_root / ".ai-runs").symlink_to(external, target_is_directory=True)
            except (NotImplementedError, OSError):
                pass
            else:
                symlinked, symlinked_status = self.helper.start_run(symlink_root, "other-run", "phase-1b-2-task-2")
                self.assertEqual((symlinked["result"], symlinked_status), ("INVALID_STATE", 5))
                self.assertFalse((external / "other-run").exists())

        unsafe_root = Path(tempfile.mkdtemp()) / "repository"
        self.addCleanup(shutil.rmtree, unsafe_root.parent)
        shutil.copytree(self.root / "ai", unsafe_root / "ai")
        unsafe_runs = unsafe_root / ".ai-runs"
        unsafe_runs.mkdir()
        unsafe_runs.chmod(0o777)
        with mock.patch.object(self.helper, "permission_checks_supported", return_value=True):
            unsafe, unsafe_status = self.helper.start_run(unsafe_root, "unsafe-run", "phase-1b-2-task-2")
        self.assertEqual((unsafe["result"], unsafe_status), ("INVALID_STATE", 5))
        self.assertFalse((unsafe_runs / "unsafe-run").exists())
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())


class PosixLaunchTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name) / "repository"
        (self.root / "work").mkdir(parents=True)
        self.environment = {"PATH": "/usr/bin:/bin", "LANG": "C", "TOKEN": "not-copied"}
        self.pre_data = {
            "runId": "run-1",
            "commandId": "verify.unit",
            "attemptId": "11111111-1111-4111-8111-111111111111",
            "argvHash": "a" * 64,
            "inputFingerprint": "b" * 64,
            "environmentFingerprint": "c" * 64,
            "workingDirectory": "work",
            "reservedAt": "2026-07-11T03:00:01Z",
            "argv": ["./gradlew", "value with spaces;$(printf unsafe)*?"],
        }

    def request(self, **overrides):
        request = {"runId": "run-1", "commandId": "verify.unit"}
        request.update(overrides)
        return request

    def pre_pass(self, *_args, **_kwargs):
        return self.helper.pre_command_result("PASS", None, 0, data=self.pre_data)

    def execute_with_capabilities(self, request=None):
        process = mock.Mock(pid=4321)
        process.wait.return_value = 0
        captured = SimpleNamespace(stdout=b"scrubbed-out", stderr=b"scrubbed-err")
        terminal = ({"operation": "POST_COMMAND", "result": "PASS"}, 0)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "pre_command", side_effect=self.pre_pass))
            stack.enter_context(mock.patch.dict(self.helper.os.environ, self.environment, clear=True))
            popen = stack.enter_context(mock.patch.object(self.helper.subprocess, "Popen", return_value=process))
            which = stack.enter_context(mock.patch.object(self.helper.shutil, "which"))
            capture = stack.enter_context(mock.patch.object(self.helper, "capture_and_scrub", return_value=captured))
            post = stack.enter_context(mock.patch.object(self.helper, "post_command", return_value=terminal))
            result = self.helper.execute_command(self.root, request or self.request())
        return result, process, popen, which, capture, post

    def test_non_posix_and_missing_launch_capabilities_are_not_configured_before_reservation(self):
        cases = (
            (False, {"PATH": "/bin"}, True, "POSIX_EXECUTION_NOT_CONFIGURED"),
            (True, {}, True, "CHILD_PATH_NOT_CONFIGURED"),
            (True, {"PATH": ""}, True, "CHILD_PATH_NOT_CONFIGURED"),
            (True, {"PATH": "/bin"}, False, "POSIX_SHELL_NOT_CONFIGURED"),
        )
        for is_posix, environment, shell_available, reason in cases:
            with self.subTest(reason=reason, environment=environment), contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=is_posix))
                stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=shell_available))
                pre_command = stack.enter_context(mock.patch.object(
                    self.helper, "pre_command", side_effect=self.pre_pass,
                ))
                stack.enter_context(mock.patch.dict(self.helper.os.environ, environment, clear=True))
                popen = stack.enter_context(mock.patch.object(self.helper.subprocess, "Popen"))
                result, status, process = self.helper.execute_command(self.root, self.request())
            self.assertEqual((result["operation"], result["result"], result["reason"], status, process), (
                "PRE_COMMAND", "NOT_CONFIGURED", reason, 3, None,
            ))
            pre_command.assert_called_once()
            self.assertIs(pre_command.call_args.kwargs["reserve"], False)
            popen.assert_not_called()

    def test_exact_bin_sh_must_be_an_executable_regular_file(self):
        regular = SimpleNamespace(st_mode=stat.S_IFREG | 0o755)
        directory = SimpleNamespace(st_mode=stat.S_IFDIR | 0o755)
        cases = (
            (FileNotFoundError(), True, False),
            (directory, True, False),
            (regular, False, False),
            (regular, True, True),
        )
        for stat_result, executable, expected in cases:
            with self.subTest(stat_result=stat_result, executable=executable), contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(
                    self.helper.Path, "stat",
                    side_effect=stat_result if isinstance(stat_result, Exception) else None,
                    return_value=None if isinstance(stat_result, Exception) else stat_result,
                ))
                access = stack.enter_context(mock.patch.object(self.helper.os, "access", return_value=executable))
                self.assertIs(self.helper.posix_shell_available(), expected)
            if not isinstance(stat_result, Exception) and stat.S_ISREG(stat_result.st_mode):
                access.assert_called_once_with(Path("/bin/sh"), os.X_OK)

    def test_execute_command_uses_exact_closed_popen_contract_and_no_interpreter_lookup(self):
        terminal, process, popen, which, capture, post = self.execute_with_capabilities()

        self.assertEqual(terminal, ({"operation": "POST_COMMAND", "result": "PASS"}, 0))
        popen.assert_called_once_with(
            self.pre_data["argv"],
            cwd=(self.root / "work").resolve(),
            env={"PATH": "/usr/bin:/bin", "LANG": "C"},
            shell=False,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            start_new_session=True,
        )
        which.assert_not_called()
        capture.assert_called_once()
        self.assertIs(capture.call_args.args[0], process)
        self.assertIsInstance(capture.call_args.kwargs["lifecycle_deadline"], float)
        self.assertEqual(post.call_count, 1)
        self.assertIs(post.call_args.args[2], capture.return_value)

    def test_launch_preserves_the_new_session_pgid_independently_of_leader_liveness(self):
        process = mock.Mock(pid=4321)
        with mock.patch.object(self.helper.subprocess, "Popen", return_value=process):
            launched = self.helper.launch_reserved(["./gradlew"], self.root, {"PATH": "/bin"})
        self.assertIs(launched, process)
        self.assertEqual(launched._workflow_pgid, 4321)

    def test_execute_command_owns_capture_and_terminal_publication(self):
        captured = SimpleNamespace(stdout=b"scrubbed-out", stderr=b"scrubbed-err")
        terminal = ({"operation": "POST_COMMAND", "result": "PASS"}, 0)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "pre_command", side_effect=self.pre_pass))
            stack.enter_context(mock.patch.dict(self.helper.os.environ, self.environment, clear=True))
            process = mock.Mock(pid=4321)
            process.wait.return_value = 0
            stack.enter_context(mock.patch.object(self.helper, "launch_reserved", return_value=process))
            capture = stack.enter_context(mock.patch.object(
                self.helper, "capture_and_scrub", return_value=captured,
            ))
            post = stack.enter_context(mock.patch.object(self.helper, "post_command", return_value=terminal))
            actual = self.helper.execute_command(self.root, self.request())

        self.assertEqual(actual, terminal)
        capture.assert_called_once()
        self.assertIs(capture.call_args.args[0], process)
        self.assertIsInstance(capture.call_args.kwargs["lifecycle_deadline"], float)
        post.assert_called_once()
        posted_process, posted_capture = post.call_args.args[1:]
        self.assertEqual(posted_process["redactionStatus"], "SCRUBBED")
        self.assertIs(posted_capture, captured)

    def test_execute_maps_timeout_and_output_caps_to_exact_non_log_process_attempts(self):
        cases = (
            (self.helper.ExecutionLifecycleTimeout("timeout"), "TIMED_OUT"),
            (self.helper.CaptureResourceLimit("output cap"), "RESOURCE_LIMIT"),
        )
        for failure, termination in cases:
            with self.subTest(termination=termination), contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
                stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
                stack.enter_context(mock.patch.object(self.helper, "pre_command", side_effect=self.pre_pass))
                stack.enter_context(mock.patch.dict(self.helper.os.environ, self.environment, clear=True))
                process = mock.Mock(pid=4321)
                process.poll.return_value = None
                stack.enter_context(mock.patch.object(self.helper, "launch_reserved", return_value=process))
                stack.enter_context(mock.patch.object(self.helper, "capture_and_scrub", side_effect=failure))
                post = stack.enter_context(mock.patch.object(
                    self.helper, "post_command", return_value=({"result": "BLOCKED"}, 2),
                ))
                actual = self.helper.execute_command(self.root, self.request())
            self.assertEqual(actual, ({"result": "BLOCKED"}, 2))
            posted = post.call_args.args[1]
            self.assertEqual(posted["termination"], termination)
            self.assertEqual(posted["redactionStatus"], "NOT_APPLIED")
            self.assertIsNone(posted["processExitCode"])
            self.assertEqual(len(post.call_args.args), 2)

    def test_execute_child_closes_pipes_but_stays_alive_through_deadline_posts_timed_out(self):
        process = mock.Mock(pid=4321)
        process.wait.side_effect = subprocess.TimeoutExpired("fake", 0.01)
        process.poll.return_value = None
        captured = self.helper.ScrubbedEvidence(b"scrubbed-out", b"scrubbed-err", self.helper._CAPTURE_SEAL)
        terminal = ({"operation": "POST_COMMAND", "result": "BLOCKED"}, 2)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "pre_command", side_effect=self.pre_pass))
            stack.enter_context(mock.patch.dict(self.helper.os.environ, self.environment, clear=True))
            stack.enter_context(mock.patch.object(self.helper, "EXECUTION_TIMEOUT_SECONDS", 0.01))
            stack.enter_context(mock.patch.object(self.helper, "launch_reserved", return_value=process))
            capture = stack.enter_context(mock.patch.object(
                self.helper, "capture_and_scrub", return_value=captured,
            ))
            terminate = stack.enter_context(mock.patch.object(self.helper, "terminate_process_group"))
            post = stack.enter_context(mock.patch.object(self.helper, "post_command", return_value=terminal))
            actual = self.helper.execute_command(self.root, self.request())

        self.assertEqual(actual, terminal)
        lifecycle_deadline = capture.call_args.kwargs["lifecycle_deadline"]
        self.assertIsInstance(lifecycle_deadline, float)
        self.assertLessEqual(process.wait.call_args.kwargs["timeout"], 0.011)
        terminate.assert_called_once_with(process, 5)
        posted = post.call_args.args[1]
        self.assertEqual((posted["termination"], posted["redactionStatus"], posted["processExitCode"]), (
            "TIMED_OUT", "NOT_APPLIED", None,
        ))
        self.assertEqual(len(post.call_args.args), 2)

    def test_execute_reap_failure_still_posts_blocked_process_facts(self):
        process = mock.Mock(pid=4321)
        process.wait.side_effect = subprocess.TimeoutExpired("fake", 0.01)
        process.poll.return_value = None
        terminal = ({"operation": "POST_COMMAND", "result": "BLOCKED"}, 2)
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "pre_command", side_effect=self.pre_pass))
            stack.enter_context(mock.patch.dict(self.helper.os.environ, self.environment, clear=True))
            stack.enter_context(mock.patch.object(self.helper, "EXECUTION_TIMEOUT_SECONDS", 0.01))
            stack.enter_context(mock.patch.object(self.helper, "launch_reserved", return_value=process))
            stack.enter_context(mock.patch.object(
                self.helper, "capture_and_scrub",
                return_value=self.helper.ScrubbedEvidence(b"out", b"err", self.helper._CAPTURE_SEAL),
            ))
            stack.enter_context(mock.patch.object(
                self.helper, "terminate_process_group",
                side_effect=self.helper.ProcessGroupError("process group could not be reaped"),
            ))
            post = stack.enter_context(mock.patch.object(self.helper, "post_command", return_value=terminal))
            actual = self.helper.execute_command(self.root, self.request())

        self.assertEqual(actual, terminal)
        posted = post.call_args.args[1]
        self.assertEqual((posted["termination"], posted["redactionStatus"], posted["processExitCode"]), (
            "TIMED_OUT", "NOT_APPLIED", None,
        ))
        self.assertIn("reaped", posted["reason"])

    def test_execute_request_is_closed_and_working_directory_must_remain_contained(self):
        for request in (
            self.request(interpreter="/tmp/caller-sh"),
            self.request(sourceEnvironment={"PATH": "/tmp"}),
            ["run-1", "verify.unit"],
        ):
            with self.subTest(request=request), contextlib.ExitStack() as stack:
                preflight = stack.enter_context(mock.patch.object(
                    self.helper, "run_current_preflight", return_value=(preflight_pass(), 0),
                ))
                popen = stack.enter_context(mock.patch.object(self.helper.subprocess, "Popen"))
                result, status, process = self.helper.execute_command(self.root, request)
            self.assertEqual((result["result"], result["reason"], status, process), (
                "POLICY_VIOLATION", "EXECUTE_COMMAND_REQUEST_INVALID", 4, None,
            ))
            preflight.assert_called_once_with(self.root.resolve())
            popen.assert_not_called()

        outside = self.root.parent / "outside"
        outside.mkdir()
        self.pre_data["workingDirectory"] = "../outside"
        (result, status, process), _expected, popen, _which, _capture, _post = self.execute_with_capabilities()
        self.assertEqual((result["result"], result["reason"], status, process), (
            "INVALID_STATE", "EXECUTION_WORKING_DIRECTORY_INVALID", 5, None,
        ))
        popen.assert_not_called()

    def test_invalid_allowlisted_environment_values_fail_closed_without_launch(self):
        for value in ("bad\x00value", "bad\nvalue", 1):
            with self.subTest(value=value), contextlib.ExitStack() as stack:
                stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
                stack.enter_context(mock.patch.object(self.helper.os, "environ", {"PATH": value}))
                pre_command = stack.enter_context(mock.patch.object(
                    self.helper, "pre_command", side_effect=self.pre_pass,
                ))
                popen = stack.enter_context(mock.patch.object(self.helper.subprocess, "Popen"))
                result, status, process = self.helper.execute_command(self.root, self.request())
            self.assertEqual((result["result"], result["reason"], status, process), (
                "INVALID_STATE", "CHILD_ENVIRONMENT_INVALID", 5, None,
            ))
            pre_command.assert_called_once()
            self.assertIs(pre_command.call_args.kwargs["reserve"], False)
            popen.assert_not_called()

    def test_terminate_process_group_uses_term_then_bounded_kill_and_reap(self):
        process = mock.Mock(pid=4321)
        process._workflow_pgid = 4321
        process.poll.return_value = None
        process.wait.return_value = 9
        with contextlib.ExitStack() as stack:
            exists = stack.enter_context(mock.patch.object(self.helper, "process_group_exists", return_value=True))
            disappearance = stack.enter_context(mock.patch.object(
                self.helper, "wait_for_process_group_disappearance", side_effect=(False, True),
            ))
            killpg = stack.enter_context(mock.patch.object(self.helper.os, "killpg", create=True))
            self.helper.terminate_process_group(process, 5)
        exists.assert_called_once_with(4321)
        self.assertEqual(disappearance.call_args_list, [mock.call(4321, 5), mock.call(4321, 5)])
        self.assertEqual(killpg.call_args_list, [
            mock.call(4321, signal.SIGTERM), mock.call(4321, getattr(signal, "SIGKILL", 9)),
        ])
        process.wait.assert_called_once_with(timeout=5)

    def test_terminate_process_group_never_signals_an_unrelated_group(self):
        process = mock.Mock(pid=4321)
        process.poll.return_value = None
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper.os, "getpgid", return_value=9999, create=True))
            killpg = stack.enter_context(mock.patch.object(self.helper.os, "killpg", create=True))
            with self.assertRaises(self.helper.ProcessGroupError):
                self.helper.terminate_process_group(process, 5)
        killpg.assert_not_called()
        process.wait.assert_not_called()

    def test_terminate_process_group_bounds_reap_and_wraps_signal_errors(self):
        process = mock.Mock(pid=4321)
        process._workflow_pgid = 4321
        process.poll.return_value = None
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "process_group_exists", return_value=True))
            stack.enter_context(mock.patch.object(
                self.helper, "wait_for_process_group_disappearance", side_effect=(False, False),
            ))
            killpg = stack.enter_context(mock.patch.object(self.helper.os, "killpg", create=True))
            with self.assertRaises(self.helper.ProcessGroupError):
                self.helper.terminate_process_group(process, 1)
        self.assertEqual(killpg.call_args_list, [
            mock.call(4321, signal.SIGTERM), mock.call(4321, getattr(signal, "SIGKILL", 9)),
        ])
        process.wait.assert_not_called()

        process.reset_mock()
        process._workflow_pgid = 4321
        process.poll.return_value = None
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "process_group_exists", return_value=True))
            stack.enter_context(mock.patch.object(
                self.helper.os, "killpg", side_effect=PermissionError("denied"), create=True,
            ))
            with self.assertRaises(self.helper.ProcessGroupError):
                self.helper.terminate_process_group(process, 1)

    def test_disappeared_preserved_group_is_never_signalled_as_a_reused_group(self):
        process = mock.Mock(pid=4321)
        process._workflow_pgid = 4321
        process.poll.return_value = 0
        process.wait.return_value = 0
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "process_group_exists", return_value=False))
            killpg = stack.enter_context(mock.patch.object(self.helper.os, "killpg", create=True))
            self.helper.terminate_process_group(process, 1)
        killpg.assert_not_called()
        process.wait.assert_called_once_with(timeout=1)

    def test_exited_group_leader_does_not_short_circuit_descendant_cleanup(self):
        process = mock.Mock(pid=4321)
        process._workflow_pgid = 4321
        process.poll.return_value = 0
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(
                self.helper, "process_group_exists", side_effect=(True, False), create=True,
            ))
            killpg = stack.enter_context(mock.patch.object(self.helper.os, "killpg", create=True))
            self.helper.terminate_process_group(process, 5)
        self.assertIn(mock.call(4321, signal.SIGTERM), killpg.call_args_list)
        process.wait.assert_called()

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "fork"), "complete process-group regression requires POSIX fork")
    def test_real_posix_exited_leader_descendant_ignores_term_and_holds_pipes_until_kill(self):
        process = self.helper.launch_reserved(
            [sys.executable, "-c", (
                "import os,signal,sys,time; child=os.fork(); "
                "(signal.signal(signal.SIGTERM, signal.SIG_IGN), print(os.getpid(), flush=True), time.sleep(30)) "
                "if child == 0 else os._exit(0)"
            )],
            self.root,
            {"PATH": os.environ.get("PATH", "")},
        )
        descendant_pid = int(process.stdout.readline().decode("ascii").strip())
        process.wait(timeout=2)
        self.assertEqual(process.poll(), 0)
        try:
            self.helper.terminate_process_group(process, 1)
            with self.assertRaises(ProcessLookupError):
                os.kill(descendant_pid, 0)
        finally:
            try:
                os.kill(descendant_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

    def test_popen_reachability_is_closed_to_execute_command(self):
        tree = ast.parse(HELPER_PATH.read_text(encoding="utf-8"))
        popen_owners = []
        launch_callers = []
        for node in (item for item in ast.walk(tree) if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))):
            for child in ast.walk(node):
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Attribute):
                    if isinstance(child.func.value, ast.Name) and (child.func.value.id, child.func.attr) == ("subprocess", "Popen"):
                        popen_owners.append(node.name)
                if isinstance(child, ast.Call) and isinstance(child.func, ast.Name) and child.func.id == "launch_reserved":
                    launch_callers.append(node.name)
        self.assertEqual(popen_owners, ["launch_reserved"])
        self.assertEqual(launch_callers, ["execute_command"])
        for standalone in ("start_run", "pre_command"):
            function = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == standalone)
            names = {child.id for child in ast.walk(function) if isinstance(child, ast.Name)}
            self.assertNotIn("launch_reserved", names)
            self.assertNotIn("Popen", names)

    def test_fake_gradlew_is_exact_posix_builtin_fixture(self):
        content = (EXECUTION_FIXTURES_PATH / "fake-gradlew").read_bytes()
        self.assertTrue(content.startswith(b"#!/bin/sh\n"))
        self.assertEqual(content, (
            b"#!/bin/sh\n"
            b"printf '%s\\n' \"$#\"\n"
            b"for argument do\n"
            b"  printf '<%s>\\n' \"$argument\"\n"
            b"done\n"
        ))

    @unittest.skipUnless(os.name == "posix", "real launch requires a POSIX host")
    def test_real_posix_launch_preserves_spaces_and_metacharacters_as_one_argument(self):
        shell = Path("/bin/sh")
        self.assertTrue(shell.is_absolute())
        self.assertTrue(shell.is_file())
        self.assertTrue(os.access(shell, os.X_OK))
        wrapper = self.root / "gradlew"
        shutil.copyfile(EXECUTION_FIXTURES_PATH / "fake-gradlew", wrapper)
        wrapper.chmod(0o755)
        token = "value with spaces;$(printf unsafe)*?"
        process = self.helper.launch_reserved(
            ["./gradlew", token], self.root, {"PATH": "/usr/bin:/bin", "LANG": "C"},
        )
        stdout, stderr = process.communicate(timeout=5)
        self.assertEqual(process.returncode, 0)
        self.assertEqual(stdout, f"1\n<{token}>\n".encode("utf-8"))
        self.assertEqual(stderr, b"")


class RecordingChunkStream:
    def __init__(self, chunks, barrier=None):
        self.chunks = list(chunks)
        self.read_sizes = []
        self.barrier = barrier

    def read(self, size=-1):
        self.read_sizes.append(size)
        if self.barrier is not None:
            barrier, self.barrier = self.barrier, None
            barrier.wait(timeout=5)
        if not self.chunks:
            return b""
        return self.chunks.pop(0)

class BlockingCloseStream:
    def __init__(self):
        self.closed = threading.Event()
        self.read_sizes = []

    def read(self, size=-1):
        self.read_sizes.append(size)
        self.closed.wait(timeout=5)
        return b""

    def close(self):
        self.closed.set()


def remove_readonly_tree(path):
    path = Path(path)
    if not path.exists():
        return
    for item in sorted(path.rglob("*"), key=lambda candidate: len(candidate.parts), reverse=True):
        try:
            item.chmod(0o700 if item.is_dir() else 0o600)
        except OSError:
            pass
    shutil.rmtree(path)


class BoundedRedactionTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        self.limits = {
            "readBytes": 65536,
            "carryBytes": 8192,
            "streamBytes": 1048576,
            "combinedBytes": 2097152,
            "candidateBytes": 4096,
        }

    def process(self, stdout, stderr=b"", barrier=None):
        return SimpleNamespace(
            stdout=RecordingChunkStream(stdout if isinstance(stdout, list) else [stdout], barrier),
            stderr=RecordingChunkStream(stderr if isinstance(stderr, list) else [stderr], barrier),
        )

    def scrub_in_splits(self, payload):
        expected = None
        for split in range(len(payload) + 1):
            scrubber = self.helper.BoundedStreamScrubber()
            first = scrubber.feed(payload[:split])
            second = scrubber.feed(payload[split:])
            actual = first + second + scrubber.finish()
            expected = actual if expected is None else expected
            self.assertEqual(actual, expected, split)
        return expected

    def test_reads_are_concurrent_and_never_request_more_than_65536_bytes(self):
        barrier = threading.Barrier(2)
        process = self.process(b"stdout", b"stderr", barrier)
        captured = self.helper.capture_and_scrub(process, self.limits)
        self.assertEqual(captured, {"stdout": b"stdout", "stderr": b"stderr"})
        self.assertTrue(process.stdout.read_sizes)
        self.assertTrue(process.stderr.read_sizes)
        self.assertTrue(all(size == 65536 for size in process.stdout.read_sizes))
        self.assertTrue(all(size == 65536 for size in process.stderr.read_sizes))


    def test_exact_65536_read_and_8192_carry_boundaries_are_real(self):
        scrubber = self.helper.BoundedStreamScrubber()
        emitted = scrubber.feed(b"a" * 65536)
        self.assertEqual(len(emitted), 65536 - 8192)
        self.assertEqual(len(scrubber.pending.encode("utf-8")), 8192)
        self.assertEqual(emitted + scrubber.finish(), b"a" * 65536)
    def test_capture_limits_must_equal_every_approved_constant(self):
        for field in self.limits:
            for delta in (-1, 1):
                with self.subTest(field=field, delta=delta), self.assertRaises(self.helper.RedactionUncertainty):
                    self.helper.capture_and_scrub(
                        self.process(b"safe"), dict(self.limits, **{field: self.limits[field] + delta}),
                    )

    def test_lifecycle_timeout_closes_descendant_pipes_and_bounds_termination_failure(self):
        process = SimpleNamespace(
            pid=4321, stdout=BlockingCloseStream(), stderr=BlockingCloseStream(),
            poll=mock.Mock(return_value=None),
        )
        self.assertEqual(self.helper.EXECUTION_TIMEOUT_SECONDS, 3600)
        started = time.monotonic()
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "EXECUTION_TIMEOUT_SECONDS", 0.01))
            terminate = stack.enter_context(mock.patch.object(
                self.helper, "terminate_process_group",
                side_effect=self.helper.ProcessGroupError("injected termination failure"),
            ))
            with self.assertRaises(self.helper.RedactionUncertainty):
                self.helper.capture_and_scrub(process, self.limits)
        self.assertLess(time.monotonic() - started, 1)
        terminate.assert_called_once_with(process, 5)
        self.assertTrue(process.stdout.closed.is_set())
        self.assertTrue(process.stderr.closed.is_set())

    def test_scrubber_streams_before_eof_and_retains_exactly_bounded_carry(self):
        scrubber = self.helper.BoundedStreamScrubber()
        emitted = scrubber.feed(b"safe-line\n" * 7000)
        self.assertTrue(emitted)
        self.assertLessEqual(len(scrubber.pending.encode("utf-8")), 8192)
        self.assertEqual(emitted + scrubber.finish(), b"safe-line\n" * 7000)

    def test_retained_scrubbed_bytes_use_bounded_sinks_at_exact_stream_and_combined_limits(self):
        budget = self.helper._ScrubbedByteBudget(2097152)
        stdout = self.helper._BoundedScrubbedSink(1048576, budget)
        stderr = self.helper._BoundedScrubbedSink(1048576, budget)
        stdout.append(b"a" * 1048576)
        stderr.append(b"b" * 1048576)

        self.assertEqual((stdout.retained_bytes, stderr.retained_bytes, budget.retained_bytes), (
            1048576, 1048576, 2097152,
        ))
        self.assertIsInstance(stdout._buffer, bytearray)
        self.assertIsInstance(stderr._buffer, bytearray)
        for sink in (stdout, stderr):
            with self.assertRaises(self.helper.CaptureResourceLimit):
                sink.append(b"x")
        self.assertEqual((stdout.retained_bytes, stderr.retained_bytes, budget.retained_bytes), (
            1048576, 1048576, 2097152,
        ))

    def test_redaction_expansion_over_cap_stops_without_returning_oversized_evidence(self):
        payload = b"x" * 1048576
        with self.assertRaises(self.helper.CaptureResourceLimit):
            self.helper.capture_and_scrub(self.process(payload), self.limits, injected_literals=("x",))

    def test_pending_sensitive_candidate_overflow_fails_at_the_carry_boundary(self):
        scrubber = self.helper.BoundedStreamScrubber()
        scrubber.feed(b"safe\n" * 900)
        scrubber.feed(b"access_token=" + b"x" * 4096)
        with self.assertRaises(self.helper.RedactionUncertainty):
            scrubber.feed(b"x")

    def test_exact_stream_and_combined_caps_succeed_and_one_byte_over_fails_closed(self):
        mib = 1048576
        exact = self.helper.capture_and_scrub(self.process(b"a" * mib, b"b" * mib), self.limits)
        self.assertEqual((len(exact["stdout"]), len(exact["stderr"])), (mib, mib))
        for stdout, stderr in ((b"a" * (mib + 1), b""), (b"", b"b" * (mib + 1))):
            with self.subTest(stdout=len(stdout), stderr=len(stderr)):
                with self.assertRaises(self.helper.RedactionUncertainty):
                    self.helper.capture_and_scrub(self.process(stdout, stderr), self.limits)

        with self.assertRaises(self.helper.RedactionUncertainty):
            self.helper.capture_and_scrub(self.process(b"a" * 1048576, b"b" * 1048577), self.limits)
        for field, value in (("streamBytes", mib + 1), ("combinedBytes", 2097153)):
            with self.subTest(field=field), self.assertRaises(self.helper.RedactionUncertainty):
                self.helper.capture_and_scrub(self.process(b""), dict(self.limits, **{field: value}))

    def test_capture_uncertainty_requests_one_bounded_process_group_termination(self):
        process = self.process(b"x" * 1048577)
        process.pid = 4321
        process.poll = mock.Mock(return_value=None)
        with mock.patch.object(self.helper, "terminate_process_group") as terminate:
            with self.assertRaises(self.helper.RedactionUncertainty):
                self.helper.capture_and_scrub(process, self.limits)
        terminate.assert_called_once_with(process, 5)

    def test_strict_incremental_utf8_accepts_every_valid_split_and_rejects_invalid_or_incomplete(self):
        text = "prefix \ud55c\uae00 suffix".encode("utf-8")
        for split in range(len(text) + 1):
            with self.subTest(split=split):
                chunks = [chunk for chunk in (text[:split], text[split:]) if chunk]
                captured = self.helper.capture_and_scrub(self.process(chunks), self.limits)
                self.assertEqual(captured["stdout"], text)

        invalid = (EXECUTION_FIXTURES_PATH / "invalid-utf8.bin").read_bytes()
        for payload in (invalid, b"incomplete\xe2\x82"):
            with self.subTest(payload=payload), self.assertRaises(self.helper.RedactionUncertainty):
                self.helper.capture_and_scrub(self.process([payload[:2], payload[2:]]), self.limits)

    def test_every_fixed_redaction_class_survives_all_chunk_boundaries(self):
        vectors = json.loads((EXECUTION_FIXTURES_PATH / "redaction-classes.json").read_text(encoding="utf-8"))
        payloads = [
            vectors["authorization"], vectors["cookie"], vectors["setCookie"], vectors["bearer"],
            *vectors["assignments"],
        ]
        for text in payloads:
            payload = (text + "\n").encode("utf-8")
            with self.subTest(text=text):
                scrubbed = self.scrub_in_splits(payload).decode("utf-8")
                self.assertIn("[REDACTED]", scrubbed)
                candidate = text
                for separator in (":", "="):
                    if separator in candidate:
                        candidate = candidate.split(separator, 1)[1]
                        break
                self.assertNotIn(candidate.strip().strip("\"'"), scrubbed)

        assignment_names = {
            text.split("=", 1)[0].split(":", 1)[0].strip()
            for text in vectors["assignments"]
        }
        self.assertEqual(assignment_names, {
            "token", "access_token", "refresh_token", "password", "passwd", "secret",
            "api_key", "private_key", "credential",
        })

    def test_assignment_quotes_are_retained_and_sensitive_value_bounds_are_exact(self):
        cases = {
            b'token=value\n': b'token=[REDACTED]\n',
            b'password="value"\n': b'password="[REDACTED]"\n',
            b"api_key='value'\n": b"api_key='[REDACTED]'\n",
        }
        for payload, expected in cases.items():
            with self.subTest(payload=payload):
                self.assertEqual(self.scrub_in_splits(payload), expected)

        accepted = b"token=" + b"x" * 4096 + b"\n"
        self.assertEqual(self.scrub_in_splits(accepted), b"token=[REDACTED]\n")
        for size in (4097, 8192):
            with self.subTest(size=size), self.assertRaises(self.helper.RedactionUncertainty):
                scrubber = self.helper.BoundedStreamScrubber()
                scrubber.feed(b"token=" + b"x" * size)
                scrubber.finish()
        for payload in (b"token=\n", b'password=""\n', b"api_key=''\n"):
            with self.subTest(payload=payload), self.assertRaises(self.helper.RedactionUncertainty):
                scrubber = self.helper.BoundedStreamScrubber()
                scrubber.feed(payload)
                scrubber.finish()

    def test_public_literals_are_empty_internal_literals_are_bounded_and_no_secret_path_is_opened(self):
        process = self.process(b"literal-secret remains ordinary text")
        with mock.patch("builtins.open", side_effect=AssertionError("secret file path opened")):
            public = self.helper.capture_and_scrub(process, self.limits)
        self.assertEqual(public["stdout"], b"literal-secret remains ordinary text")

        for size, accepted in ((4096, True), (4097, False)):
            literal = "x" * size
            process = self.process(("before " + literal + " after").encode("utf-8"))
            with self.subTest(size=size):
                if accepted:
                    captured = self.helper.capture_and_scrub(process, self.limits, injected_literals=(literal,))
                    self.assertEqual(captured["stdout"], b"before [REDACTED] after")
                else:
                    with self.assertRaises(self.helper.RedactionUncertainty):
                        self.helper.capture_and_scrub(process, self.limits, injected_literals=(literal,))

        with self.assertRaises(self.helper.RedactionUncertainty):
            self.helper.capture_and_scrub(self.process(b"anything"), self.limits, injected_literals=("",))

    @unittest.skipUnless(os.name == "posix" and hasattr(os, "fork"), "real pipe regression requires POSIX fork")
    def test_real_posix_descendant_held_pipe_fds_are_bounded_without_thread_close(self):
        stdout_read, stdout_write = os.pipe()
        stderr_read, stderr_write = os.pipe()
        holder = subprocess.Popen(
            [sys.executable, "-c", (
                "import os,time; child=os.fork(); "
                "os._exit(0) if child else time.sleep(2)"
            )],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            pass_fds=(stdout_write, stderr_write),
            start_new_session=True,
        )
        os.close(stdout_write)
        os.close(stderr_write)
        holder.wait(timeout=1)
        process = SimpleNamespace(
            stdout=os.fdopen(stdout_read, "rb", buffering=0),
            stderr=os.fdopen(stderr_read, "rb", buffering=0),
        )
        started = time.monotonic()
        try:
            with mock.patch.object(self.helper, "EXECUTION_TIMEOUT_SECONDS", 0.05):
                with self.assertRaises(self.helper.ExecutionLifecycleTimeout):
                    self.helper.capture_and_scrub(process, self.limits)
            self.assertLess(time.monotonic() - started, 1)
        finally:
            for stream in (process.stdout, process.stderr):
                try:
                    stream.close()
                except OSError:
                    pass
            try:
                os.killpg(holder.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass


class PostCommandPersistenceTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(remove_readonly_tree, temporary)
        self.root = temporary / "repository"
        shutil.copytree(REPOSITORY_ROOT / "ai", self.root / "ai")
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.start_run(self.root, "run-1", "phase-1b-2-task-5")
        self.assertEqual((result["result"], status), ("PASS", 0))
        self.session_path = self.root / ".ai-runs" / "run-1" / ".state" / "run-session.json"
        session = self.session()
        session["reservations"] = [{
            "attemptId": "attempt-1", "commandId": "verify.unit", "argvHash": "a" * 64,
            "inputFingerprint": "b" * 64, "environmentFingerprint": "c" * 64,
            "reservedAt": "2026-07-11T03:00:01Z", "state": "RESERVED",
            "commandResultRef": None, "processAttemptRef": None, "terminalAt": None,
            "rerunReasonHash": None, "rerunOfAttemptId": None,
        }]
        self.session_path.write_text(json.dumps(session), encoding="utf-8")

    def session(self):
        return json.loads(self.session_path.read_text(encoding="utf-8"))

    def process_attempt(self, *, exit_code=0, termination="EXITED", redaction="SCRUBBED", launch="LAUNCHED", reason=None):
        return {
            "$schema": "ai/schemas/process-attempt.schema.json",
            "$id": ".ai-runs/run-1/process-attempts/verify.unit/attempt-1.json",
            "schemaVersion": 1, "runId": "run-1", "commandId": "verify.unit", "attemptId": "attempt-1",
            "reservedAt": "2026-07-11T03:00:01Z",
            "startedAt": None if launch == "SPAWN_FAILED" else "2026-07-11T03:00:02Z",
            "endedAt": "2026-07-11T03:00:03Z", "argvHash": "a" * 64,
            "inputFingerprint": "b" * 64, "environmentFingerprint": "c" * 64,
            "workingDirectory": ".", "launchStatus": launch, "processExitCode": exit_code,
            "termination": termination, "redactionStatus": redaction, "reason": reason,
        }

    def artifact(self, kind):
        return self.root / ".ai-runs" / "run-1" / kind / "verify.unit" / "attempt-1.json"


    def scrubbed(self, stdout=b"out", stderr=b"err"):
        limits = {
            "readBytes": 65536, "carryBytes": 8192, "streamBytes": 1048576,
            "combinedBytes": 2097152, "candidateBytes": 4096,
        }
        process = SimpleNamespace(
            stdout=RecordingChunkStream([stdout]), stderr=RecordingChunkStream([stderr]),
        )
        return self.helper.capture_and_scrub(process, limits)

    def policy_events(self, root):
        directory = root / ".ai-runs" / "run-1" / "policy-violations"
        return list(directory.glob("*.json")) if directory.exists() else []

    def task5_publication_transactions(self, root):
        run = root / ".ai-runs" / "run-1"
        return sorted(
            path.relative_to(run).as_posix()
            for path in run.rglob("*")
            if path.is_file() and (
                path.name.startswith(".attempt-1.")
                or path.name.endswith(".terminal-publication.json")
                or "immutable-publications" in path.parts
            )
        )

    def execute_final_wait_failure(self, wait_error, *, poll_exit=None, deadline_boundary=False):
        process = mock.Mock(pid=4321)
        process.wait.side_effect = wait_error
        process.poll.return_value = poll_exit
        captured = self.helper.ScrubbedEvidence(b"captured-out", b"captured-err", self.helper._CAPTURE_SEAL)
        pre_data = {
            "runId": "run-1", "commandId": "verify.unit", "attemptId": "attempt-1",
            "argvHash": "a" * 64, "inputFingerprint": "b" * 64,
            "environmentFingerprint": "c" * 64, "workingDirectory": ".",
            "reservedAt": "2026-07-11T03:00:01Z", "argv": ["/bin/true"],
        }
        real_monotonic = time.monotonic
        monotonic_calls = 0

        def boundary_clock():
            nonlocal monotonic_calls
            monotonic_calls += 1
            if monotonic_calls == 1:
                return 100.0
            if monotonic_calls == 2:
                return 100.0 + self.helper.EXECUTION_TIMEOUT_SECONDS
            return real_monotonic()

        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
            stack.enter_context(mock.patch.object(
                self.helper, "pre_command",
                return_value=self.helper.pre_command_result("PASS", None, 0, data=pre_data),
            ))
            stack.enter_context(mock.patch.dict(self.helper.os.environ, {"PATH": "/usr/bin:/bin"}, clear=True))
            stack.enter_context(mock.patch.object(self.helper, "launch_reserved", return_value=process))
            capture = stack.enter_context(mock.patch.object(
                self.helper, "capture_and_scrub", return_value=captured,
            ))
            terminate = stack.enter_context(mock.patch.object(self.helper, "terminate_process_group"))
            post = stack.enter_context(mock.patch.object(
                self.helper, "post_command", wraps=self.helper.post_command,
            ))
            if deadline_boundary:
                stack.enter_context(mock.patch.object(self.helper.time, "monotonic", side_effect=boundary_clock))
            actual = self.helper.execute_command(self.root, {"runId": "run-1", "commandId": "verify.unit"})

        process_path = self.artifact("process-attempts")
        command_path = self.artifact("commands")
        process_attempt = json.loads(process_path.read_text(encoding="utf-8"))
        command_result = json.loads(command_path.read_text(encoding="utf-8"))
        reservation = self.session()["reservations"][0]
        self.assertEqual((actual[0]["operation"], actual[0]["result"], actual[1]), (
            "POST_COMMAND", "BLOCKED", 2,
        ))
        self.assertEqual(post.call_count, 1)
        self.assertEqual(reservation["state"], "BLOCKED")
        self.assertEqual(sum(
            item["state"] == "BLOCKED" for item in self.session()["reservations"]
        ), 1)
        self.assertEqual((process_attempt["termination"], process_attempt["redactionStatus"]), (
            "TIMED_OUT", "NOT_APPLIED",
        ))
        self.assertEqual(process_attempt["processExitCode"], poll_exit)
        self.assertEqual((command_result["result"], command_result["processExitCode"]), ("BLOCKED", None))
        self.assertEqual((command_result["stdoutPath"], command_result["stderrPath"]), (None, None))
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "logs").exists())
        self.assertEqual(len(post.call_args.args), 2)
        capture.assert_called_once()
        return process, terminate

    def test_capture_succeeds_at_deadline_boundary_while_child_alive_posts_once_and_blocks_once(self):
        process, terminate = self.execute_final_wait_failure(
            subprocess.TimeoutExpired("unused", 0), deadline_boundary=True,
        )
        process.wait.assert_not_called()
        terminate.assert_called_once_with(process, 5)

    def test_final_wait_oserror_while_child_alive_posts_once_and_blocks_once(self):
        process, terminate = self.execute_final_wait_failure(OSError("direct reap failure"))
        process.wait.assert_called_once()
        terminate.assert_called_once_with(process, 5)

    def test_final_wait_exception_preserves_authoritative_exit_without_false_pass(self):
        process, terminate = self.execute_final_wait_failure(RuntimeError("unexpected reap failure"), poll_exit=9)
        process.wait.assert_called_once()
        terminate.assert_not_called()

    def test_redaction_cleanup_failure_never_fabricates_exit_or_exited_process_facts(self):
        process = mock.Mock(pid=4321)
        process._workflow_pgid = 4321
        process.poll.return_value = None
        pre_data = {
            "runId": "run-1", "commandId": "verify.unit", "attemptId": "attempt-1",
            "argvHash": "a" * 64, "inputFingerprint": "b" * 64,
            "environmentFingerprint": "c" * 64, "workingDirectory": ".",
            "reservedAt": "2026-07-11T03:00:01Z", "argv": ["/bin/true"],
        }
        with contextlib.ExitStack() as stack:
            stack.enter_context(mock.patch.object(self.helper, "host_is_posix", return_value=True))
            stack.enter_context(mock.patch.object(self.helper, "posix_shell_available", return_value=True))
            stack.enter_context(mock.patch.object(
                self.helper, "pre_command",
                return_value=self.helper.pre_command_result("PASS", None, 0, data=pre_data),
            ))
            stack.enter_context(mock.patch.dict(self.helper.os.environ, {"PATH": "/usr/bin:/bin"}, clear=True))
            stack.enter_context(mock.patch.object(self.helper, "launch_reserved", return_value=process))
            stack.enter_context(mock.patch.object(
                self.helper, "capture_and_scrub", side_effect=self.helper.RedactionUncertainty("invalid UTF-8"),
            ))
            stack.enter_context(mock.patch.object(
                self.helper, "terminate_process_group",
                side_effect=self.helper.ProcessGroupError("process group did not disappear"),
            ))
            actual = self.helper.execute_command(self.root, {"runId": "run-1", "commandId": "verify.unit"})

        self.assertEqual((actual[0]["operation"], actual[0]["result"], actual[0]["reason"], actual[1]), (
            "POST_COMMAND", "BLOCKED", "UNSCRUBBED_EVIDENCE", 2,
        ))
        attempt = json.loads(self.artifact("process-attempts").read_text(encoding="utf-8"))
        self.helper.validate(self.root, attempt, "ai/schemas/process-attempt.schema.json")
        self.assertEqual((attempt["processExitCode"], attempt["termination"], attempt["redactionStatus"]), (
            None, "TIMED_OUT", "NOT_APPLIED",
        ))
        self.assertIn("REDACTION_UNCERTAINTY", attempt["reason"])
        self.assertIn("PROCESS_GROUP_TERMINATION_FAILED", attempt["reason"])
        command = json.loads(self.artifact("commands").read_text(encoding="utf-8"))
        self.assertEqual((command["result"], command["processExitCode"], command["reason"]), (
            "BLOCKED", None, "UNSCRUBBED_EVIDENCE",
        ))
        events = self.policy_events(self.root)
        self.assertEqual(len(events), 1)
        self.assertEqual(json.loads(events[0].read_text(encoding="utf-8"))["type"], "UNSCRUBBED_EVIDENCE")

    def test_exact_execution_outcome_table_is_parameterized(self):
        rows = (
            ("spawn", self.process_attempt(exit_code=None, termination="SPAWN_FAILED", redaction="NOT_APPLIED", launch="SPAWN_FAILED", reason="spawn failed"), None, None, "BLOCKED", 2, "BLOCKED", None, 0),
            ("pass", self.process_attempt(), b"out", b"err", "PASS", 0, "PASS", 0, 0),
            ("fail", self.process_attempt(exit_code=17), b"out", b"err", "FAIL", 1, "FAIL", 17, 0),
            ("timeout", self.process_attempt(exit_code=None, termination="TIMED_OUT", redaction="NOT_APPLIED", reason="timeout"), None, None, "BLOCKED", 2, "BLOCKED", None, 0),
            ("resource", self.process_attempt(exit_code=None, termination="RESOURCE_LIMIT", redaction="NOT_APPLIED", reason="output cap"), None, None, "BLOCKED", 2, "BLOCKED", None, 0),
            ("unscrubbed", self.process_attempt(redaction="UNSCRUBBED", reason="invalid UTF-8"), None, None, "BLOCKED", 2, "BLOCKED", 0, 1),
        )
        for name, process, stdout, stderr, expected, status, reservation_state, expected_exit, event_count in rows:
            with self.subTest(name=name):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(remove_readonly_tree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                with mock.patch.object(self.helper.subprocess, "Popen") as popen:
                    evidence = self.scrubbed(stdout, stderr) if stdout is not None else None
                    result, actual_status = self.helper.post_command(root_copy, process, evidence)
                self.assertEqual((result["operation"], result["result"], actual_status), ("POST_COMMAND", expected, status))
                self.assertEqual(result["data"]["processExitCode"], expected_exit)
                persisted = json.loads((root_copy / self.session_path.relative_to(self.root)).read_text(encoding="utf-8"))
                self.assertEqual(persisted["reservations"][0]["state"], reservation_state)
                command = json.loads((root_copy / self.artifact("commands").relative_to(self.root)).read_text(encoding="utf-8"))
                self.helper.validate(root_copy, command, "ai/schemas/command-result.schema.json")
                if expected == "BLOCKED":
                    self.assertEqual((command["processExitCode"], command["stdoutPath"], command["stderrPath"]), (None, None, None))
                else:
                    self.assertEqual(command["processExitCode"], process["processExitCode"])
                    self.assertEqual((root_copy / command["stdoutPath"]).read_bytes(), stdout)
                    self.assertEqual((root_copy / command["stderrPath"]).read_bytes(), stderr)
                events = list((root_copy / ".ai-runs" / "run-1" / "policy-violations").glob("*.json")) if (root_copy / ".ai-runs" / "run-1" / "policy-violations").exists() else []
                self.assertEqual(len(events), event_count)
                if events:
                    self.assertEqual(json.loads(events[0].read_text(encoding="utf-8"))["type"], "UNSCRUBBED_EVIDENCE")
                popen.assert_not_called()

    def test_process_attempt_is_published_first_and_later_failure_leaves_reserved(self):
        process = self.process_attempt()
        with mock.patch.object(self.helper, "publish_command_result", side_effect=OSError("injected failure")):
            result, status = self.helper.post_command(self.root, process, self.scrubbed())
        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertTrue(self.artifact("process-attempts").is_file())
        self.assertFalse(self.artifact("commands").exists())
        session = self.session()
        self.assertEqual(session["reservations"][0]["state"], "RESERVED")
        self.assertIn(process["$id"], session["processAttemptRefs"])
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "policy-violations").exists())
        self.assertFalse(any(path.name != ".state" for path in (self.root / ".ai-runs" / "run-1").rglob(".*")))

        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        try:
            repaired = self.helper.repair_reserved_attempts(self.root, self.session(), acquired)
        finally:
            self.helper.release_run_lock(acquired)
        self.assertEqual(repaired["reservations"][0]["state"], "BLOCKED")
        self.assertEqual(repaired["processAttemptRefs"], [process["$id"]])

    def test_write_uncertainty_emits_unscrubbed_event_but_generic_collision_does_not(self):
        for error, expected_events in ((self.helper.EvidenceWriteUncertainty("uncertain"), 1), (FileExistsError("collision"), 0)):
            with self.subTest(error=type(error).__name__):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(remove_readonly_tree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                with mock.patch.object(self.helper, "publish_command_result", side_effect=error):
                    result, status = self.helper.post_command(root_copy, self.process_attempt(), self.scrubbed())
                self.assertEqual((result["result"], status), ("BLOCKED", 2))
                events_dir = root_copy / ".ai-runs" / "run-1" / "policy-violations"
                events = list(events_dir.glob("*.json")) if events_dir.exists() else []
                self.assertEqual(len(events), expected_events)

    def test_collision_race_and_second_terminal_transition_are_rejected_without_false_pass(self):
        pristine = Path(tempfile.mkdtemp()) / "repository"
        self.addCleanup(remove_readonly_tree, pristine.parent)
        shutil.copytree(self.root, pristine)
        first, first_status = self.helper.post_command(self.root, self.process_attempt(), self.scrubbed())
        before = self.session_path.read_bytes()
        contradictory = self.process_attempt(exit_code=7)
        second, second_status = self.helper.post_command(self.root, contradictory, self.scrubbed())
        self.assertEqual((first["result"], first_status), ("PASS", 0))
        self.assertEqual((second["result"], second_status), ("BLOCKED", 2))
        self.assertEqual(second["data"]["processExitCode"], 0)
        self.assertEqual(self.session_path.read_bytes(), before)

        root_copy = Path(tempfile.mkdtemp()) / "repository"
        self.addCleanup(remove_readonly_tree, root_copy.parent)
        shutil.copytree(pristine, root_copy)
        process = self.process_attempt()
        process["reason"] = None
        destination = root_copy / process["$id"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        winner = dict(process, processExitCode=9)
        destination.write_text(json.dumps(winner), encoding="utf-8")
        raced, raced_status = self.helper.post_command(root_copy, process, self.scrubbed())
        self.assertEqual((raced["result"], raced_status), ("BLOCKED", 2))
        self.assertEqual(raced["data"]["processExitCode"], 9)
        self.assertEqual(json.loads(destination.read_text(encoding="utf-8"))["processExitCode"], 9)
        self.assertEqual(self.task5_publication_transactions(root_copy), [])

        unproven_root = Path(tempfile.mkdtemp()) / "repository"
        self.addCleanup(remove_readonly_tree, unproven_root.parent)
        shutil.copytree(pristine, unproven_root)
        unproven_destination = unproven_root / process["$id"]
        unproven_destination.parent.mkdir(parents=True, exist_ok=True)
        unproven_destination.write_text("{}", encoding="utf-8")
        unproven, unproven_status = self.helper.post_command(
            unproven_root, self.process_attempt(exit_code=23), self.scrubbed(),
        )
        self.assertEqual((unproven["result"], unproven_status), ("BLOCKED", 2))
        self.assertIsNone(unproven["data"]["processExitCode"])

    def test_standalone_post_rejects_raw_or_oversized_forged_pass_logs_before_process_publication(self):
        for forged in (b"token=unredacted-secret", b"x" * 1048577):
            with self.subTest(size=len(forged)):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(remove_readonly_tree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                result, status = self.helper.post_command(root_copy, self.process_attempt(), forged)
                self.assertEqual((result["result"], status), ("INVALID_STATE", 5))
                self.assertFalse((root_copy / self.process_attempt()["$id"]).exists())
                self.assertFalse((root_copy / ".ai-runs" / "run-1" / "commands").exists())

    def test_process_publication_faults_emit_once_and_resume_for_launched_and_spawn_failed(self):
        hooks = (
            "post.process.after_temp", "post.process.after_chmod",
            "post.process.after_rename", "post.process.after_session",
        )
        for launch, hook in product(("LAUNCHED", "SPAWN_FAILED"), hooks):
            with self.subTest(launch=launch, hook=hook):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(remove_readonly_tree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                process = self.process_attempt() if launch == "LAUNCHED" else self.process_attempt(
                    exit_code=None, termination="SPAWN_FAILED", redaction="NOT_APPLIED",
                    launch="SPAWN_FAILED", reason="spawn failed",
                )
                raised = False

                def inject(event, **_kwargs):
                    nonlocal raised
                    if event == hook and not raised:
                        raised = True
                        raise self.helper.EvidenceWriteUncertainty("injected process publication fault")

                evidence = self.scrubbed() if launch == "LAUNCHED" else None
                with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=inject):
                    first, first_status = self.helper.post_command(root_copy, process, evidence)
                self.assertEqual((first["result"], first_status), ("BLOCKED", 2))
                self.assertEqual(len(self.policy_events(root_copy)), 1)

                resumed, resumed_status = self.helper.post_command(root_copy, process, evidence)
                expected = ("PASS", 0) if launch == "LAUNCHED" else ("BLOCKED", 2)
                self.assertEqual((resumed["result"], resumed_status), expected)
                persisted = json.loads((
                    root_copy / self.session_path.relative_to(self.root)
                ).read_text(encoding="utf-8"))
                self.assertNotEqual(persisted["reservations"][0]["state"], "RESERVED")
                self.assertEqual(self.task5_publication_transactions(root_copy), [])

    def test_terminal_publication_faults_leave_no_partial_finals_and_resume_from_journal(self):
        hooks = (
            "post.command.after_stdout", "post.command.after_stderr",
            "post.command.after_result", "post.command.after_chmod",
            "post.command.before_session",
        )
        for hook in hooks:
            with self.subTest(hook=hook):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(remove_readonly_tree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                process = self.process_attempt()
                evidence = self.scrubbed()
                raised = False

                def inject(event, **_kwargs):
                    nonlocal raised
                    if event == hook and not raised:
                        raised = True
                        raise self.helper.EvidenceWriteUncertainty("injected terminal publication fault")

                with mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=inject):
                    first, first_status = self.helper.post_command(root_copy, process, evidence)
                self.assertEqual((first["result"], first_status), ("BLOCKED", 2))
                for path in (
                    root_copy / ".ai-runs/run-1/logs/verify.unit/attempt-1.stdout.log",
                    root_copy / ".ai-runs/run-1/logs/verify.unit/attempt-1.stderr.log",
                    root_copy / ".ai-runs/run-1/commands/verify.unit/attempt-1.json",
                ):
                    self.assertFalse(path.exists(), (hook, path))
                journals = list((root_copy / ".ai-runs/run-1/.state").rglob("*terminal-publication*.json"))
                self.assertEqual(len(journals), 1)
                resumed, resumed_status = self.helper.post_command(root_copy, process, evidence)
                self.assertEqual((resumed["result"], resumed_status), ("PASS", 0))
                persisted = json.loads((
                    root_copy / self.session_path.relative_to(self.root)
                ).read_text(encoding="utf-8"))
                self.assertEqual(persisted["reservations"][0]["state"], "PASS")
                self.assertEqual(self.task5_publication_transactions(root_copy), [])


    def test_post_session_faults_preserve_committed_terminal_finals_and_result(self):
        for fault in ("after_session", "journal_cleanup"):
            with self.subTest(fault=fault):
                root_copy = Path(tempfile.mkdtemp()) / "repository"
                self.addCleanup(remove_readonly_tree, root_copy.parent)
                shutil.copytree(self.root, root_copy)
                process = self.process_attempt()
                evidence = self.scrubbed()
                with contextlib.ExitStack() as stack:
                    if fault == "after_session":
                        def inject(event, **_kwargs):
                            if event == "post.command.after_session":
                                raise self.helper.EvidenceWriteUncertainty("injected post-session fault")
                        stack.enter_context(mock.patch.object(self.helper, "run_lifecycle_hook", side_effect=inject))
                    else:
                        stack.enter_context(mock.patch.object(
                            self.helper, "complete_terminal_publication",
                            side_effect=OSError("injected journal cleanup failure"),
                        ))
                    result, status = self.helper.post_command(root_copy, process, evidence)

                self.assertEqual((result["result"], status), ("PASS", 0))
                persisted = json.loads((
                    root_copy / self.session_path.relative_to(self.root)
                ).read_text(encoding="utf-8"))
                self.assertEqual(persisted["reservations"][0]["state"], "PASS")
                finals = (
                    root_copy / ".ai-runs/run-1/logs/verify.unit/attempt-1.stdout.log",
                    root_copy / ".ai-runs/run-1/logs/verify.unit/attempt-1.stderr.log",
                    root_copy / ".ai-runs/run-1/commands/verify.unit/attempt-1.json",
                )
                for path in finals:
                    self.assertTrue(path.is_file(), (fault, path))
                    self.assertEqual(path.stat().st_mode & stat.S_IWUSR, 0)
                final_bytes = {path: path.read_bytes() for path in finals}
                session_bytes = (
                    root_copy / self.session_path.relative_to(self.root)
                ).read_bytes()
                journals = list((root_copy / ".ai-runs/run-1/.state").rglob("*terminal-publication*.json"))
                self.assertEqual(len(journals), 1)
                retry, retry_status = self.helper.post_command(root_copy, process, evidence)
                self.assertEqual((retry["result"], retry_status), ("BLOCKED", 2))
                self.assertEqual(retry["data"]["processExitCode"], 0)
                self.assertEqual(
                    (root_copy / self.session_path.relative_to(self.root)).read_bytes(),
                    session_bytes,
                )
                self.assertEqual({path: path.read_bytes() for path in finals}, final_bytes)
                self.assertEqual(self.task5_publication_transactions(root_copy), [])

    def test_terminal_journal_collision_preserves_winner_finals_and_session(self):
        process = self.process_attempt()
        evidence = self.scrubbed()
        with mock.patch.object(
            self.helper, "complete_terminal_publication",
            side_effect=OSError("injected journal cleanup failure"),
        ):
            result, status = self.helper.post_command(self.root, process, evidence)
        self.assertEqual((result["result"], status), ("PASS", 0))

        finals = (
            self.root / ".ai-runs/run-1/logs/verify.unit/attempt-1.stdout.log",
            self.root / ".ai-runs/run-1/logs/verify.unit/attempt-1.stderr.log",
            self.root / ".ai-runs/run-1/commands/verify.unit/attempt-1.json",
        )
        final_bytes = {path: path.read_bytes() for path in finals}
        session_bytes = self.session_path.read_bytes()
        journal = next((
            self.root / ".ai-runs/run-1/.state"
        ).glob("*terminal-publication*.json"))
        winner = b'{"collision":"winner"}\n'
        journal.write_bytes(winner)

        retry, retry_status = self.helper.post_command(self.root, process, evidence)

        self.assertEqual((retry["result"], retry_status), ("BLOCKED", 2))
        self.assertEqual(retry["reason"], "TERMINAL_PUBLICATION_COLLISION")
        self.assertEqual(journal.read_bytes(), winner)
        self.assertEqual({path: path.read_bytes() for path in finals}, final_bytes)
        self.assertEqual(self.session_path.read_bytes(), session_bytes)


class Phase1B3DoneClaimGateTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        temporary = Path(tempfile.mkdtemp())
        self.addCleanup(remove_readonly_tree, temporary)
        self.root = temporary / "repository"
        shutil.copytree(REPOSITORY_ROOT / "ai", self.root / "ai")
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.start_run(self.root, "run-1", "phase-1b-3")
        self.assertEqual((result["result"], status), ("PASS", 0))
        self.session_path = self.root / ".ai-runs" / "run-1" / ".state" / "run-session.json"
        session = self.session()
        session["reservations"] = [{
            "attemptId": "attempt-1", "commandId": "verify.unit", "argvHash": "a" * 64,
            "inputFingerprint": "b" * 64, "environmentFingerprint": "c" * 64,
            "reservedAt": "2026-07-12T03:00:01Z", "state": "RESERVED",
            "commandResultRef": None, "processAttemptRef": None, "terminalAt": None,
            "rerunReasonHash": None, "rerunOfAttemptId": None,
        }]
        self.session_path.write_text(json.dumps(session), encoding="utf-8")

    def session(self):
        return json.loads(self.session_path.read_text(encoding="utf-8"))

    def process_attempt(self, exit_code=0):
        return {
            "$schema": "ai/schemas/process-attempt.schema.json",
            "$id": ".ai-runs/run-1/process-attempts/verify.unit/attempt-1.json",
            "schemaVersion": 1, "runId": "run-1", "commandId": "verify.unit", "attemptId": "attempt-1",
            "reservedAt": "2026-07-12T03:00:01Z", "startedAt": "2026-07-12T03:00:02Z",
            "endedAt": "2026-07-12T03:00:03Z", "argvHash": "a" * 64,
            "inputFingerprint": "b" * 64, "environmentFingerprint": "c" * 64,
            "workingDirectory": ".", "launchStatus": "LAUNCHED", "processExitCode": exit_code,
            "termination": "EXITED", "redactionStatus": "SCRUBBED", "reason": None,
        }

    def artifact(self, kind):
        return self.root / ".ai-runs" / "run-1" / kind / "verify.unit" / "attempt-1.json"

    def scrubbed(self, stdout=b"out", stderr=b"err"):
        return self.helper.ScrubbedEvidence(stdout, stderr, self.helper._CAPTURE_SEAL)

    def publish_command_result(self, exit_code=0):
        stdout = b"phase-1b-3 stdout\n"
        stderr = b""
        result, status = self.helper.post_command(
            self.root,
            self.process_attempt(exit_code=exit_code),
            self.helper.ScrubbedEvidence(stdout, stderr, self.helper._CAPTURE_SEAL),
        )
        self.assertEqual(result["operation"], "POST_COMMAND")
        return result, status

    def publish_policy_violation(self):
        acquired = self.helper.acquire_run_lock(self.root, "run-1")
        try:
            session = self.helper.active_open_session(self.root, "run-1")
            self.helper.immutable_policy_event(
                self.root,
                session,
                acquired,
                "COMPLETION_WITHOUT_EVIDENCE",
                "verify.unit",
                "done claim attempted without evidence",
                operation="PRE_DONE_CLAIM",
            )
        finally:
            self.helper.release_run_lock(acquired)

    def done_claim(self, *, overall="PASS", checks=None, blockers=None):
        if checks is None:
            checks = [{
                "id": "verify.unit",
                "result": "PASS",
                "evidenceRefs": [".ai-runs/run-1/commands/verify.unit/attempt-1.json"],
                "reason": None,
            }]
        return {
            "$schema": "ai/schemas/done-claim.schema.json",
            "$id": ".ai-runs/run-1/done-claim.json",
            "schemaVersion": 1,
            "runId": "run-1",
            "taskKey": "phase-1b-3",
            "generatedAt": "2026-07-12T03:10:00Z",
            "implementationStatus": "PASS",
            "overallResult": overall,
            "checks": checks,
            "notRunItems": [],
            "evidenceRefs": [reference for check in checks for reference in check["evidenceRefs"]],
            "unexpected500Status": "PASS",
            "unhandledExceptionStatus": "PASS",
            "blockers": [] if blockers is None else blockers,
            "remainingRisks": ["Phase 2C verification completeness is not evaluated by Phase 1B-3."],
        }

    def write_claim(self, claim):
        path = self.root / ".ai-runs" / "run-1" / "claim-input.json"
        path.write_text(json.dumps(claim), encoding="utf-8")
        return ".ai-runs/run-1/claim-input.json"

    def partial_finalization_paths(self):
        run = self.root / ".ai-runs" / "run-1"
        return (
            run / "done-claim.json",
            run / "gate-results" / "pre-done-claim.json",
            run / "artifact-manifest.json",
        )

    def inject_partial_finalization_failure(self, error, *, mutate_session=False):
        for path in self.partial_finalization_paths():
            path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            path.write_text("{}\n", encoding="utf-8")
        if mutate_session:
            session = self.session()
            session["startedAt"] = "2026-07-12T00:00:00Z"
            self.session_path.write_text(json.dumps(session), encoding="utf-8")
        raise error

    def assert_partial_finalization_absent(self):
        for path in self.partial_finalization_paths():
            self.assertFalse(path.exists(), path)

    def test_valid_all_pass_claim_finalizes_integrity_only_run(self):
        self.publish_command_result(exit_code=0)
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(self.done_claim()),
            )
        self.assertEqual((result["operation"], result["result"], status), ("PRE_DONE_CLAIM", "PASS", 0))
        self.assertEqual(result["data"]["completenessEvaluated"], False)
        self.assertEqual(result["data"]["scope"], "INTEGRITY_ONLY")
        run = self.root / ".ai-runs" / "run-1"
        self.assertTrue((run / "artifact-manifest.json").is_file())
        self.assertTrue((run / "run.json").is_file())
        self.assertFalse((run / ".state").exists())
        verified, verify_status = self.helper.verify_finalized_run(self.root, "run-1")
        self.assertEqual((verified["operation"], verified["result"], verify_status), ("PRE_DONE_CLAIM", "PASS", 0))
        self.assertFalse((run / ".state").exists())

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

    def test_unreferenced_process_attempt_blocks_finalization(self):
        self.publish_command_result(exit_code=0)
        extra = self.process_attempt(exit_code=0)
        extra["attemptId"] = "attempt-extra"
        extra["$id"] = ".ai-runs/run-1/process-attempts/verify.unit/attempt-extra.json"
        extra_path = self.root / ".ai-runs" / "run-1" / "process-attempts" / "verify.unit" / "attempt-extra.json"
        extra_path.write_text(json.dumps(extra), encoding="utf-8")
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(self.done_claim()),
            )
        self.assertEqual((result["operation"], result["result"], status), ("PRE_DONE_CLAIM", "INVALID_STATE", 5))
        self.assertEqual(result["reason"], "UNREFERENCED_FINAL_ARTIFACT")

    def test_missing_process_attempt_reference_blocks_finalization(self):
        self.publish_command_result(exit_code=0)
        process_path = self.root / ".ai-runs" / "run-1" / "process-attempts" / "verify.unit" / "attempt-1.json"
        process_path.chmod(0o600)
        process_path.unlink()
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(self.done_claim()),
            )
        self.assertEqual((result["operation"], result["result"], status), ("PRE_DONE_CLAIM", "INVALID_STATE", 5))
        self.assertIn(result["reason"], {"PROCESS_ATTEMPT_REFERENCE_MISSING", "MISSING_FINAL_ARTIFACT"})

    def test_verify_finalized_detects_digest_mismatch_read_only(self):
        self.publish_command_result(exit_code=0)
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(self.done_claim()),
            )
        self.assertEqual((result["result"], status), ("PASS", 0))
        log_path = self.root / ".ai-runs" / "run-1" / "logs" / "verify.unit" / "attempt-1.stdout.log"
        before = sorted(path.relative_to(self.root).as_posix() for path in (self.root / ".ai-runs" / "run-1").rglob("*"))
        log_path.chmod(0o600)
        log_path.write_text("tampered\n", encoding="utf-8")
        verified, verify_status = self.helper.verify_finalized_run(self.root, "run-1")
        after = sorted(path.relative_to(self.root).as_posix() for path in (self.root / ".ai-runs" / "run-1").rglob("*"))
        self.assertEqual((verified["operation"], verified["result"], verify_status), ("PRE_DONE_CLAIM", "INVALID_STATE", 5))
        self.assertEqual(verified["reason"], "ARTIFACT_DIGEST_MISMATCH")
        self.assertEqual(before, after)

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

    def test_verify_finalized_rejects_stale_run_result(self):
        self.publish_command_result(exit_code=0)
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(self.done_claim()),
            )
        self.assertEqual((result["result"], status), ("PASS", 0))
        path = self.root / ".ai-runs" / "run-1" / "run.json"
        path.chmod(0o600)
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["result"] = "BLOCKED"
        path.write_text(json.dumps(payload), encoding="utf-8")
        verified, verify_status = self.helper.verify_finalized_run(self.root, "run-1")
        self.assertEqual((verified["result"], verify_status), ("INVALID_STATE", 5))
        self.assertEqual(verified["reason"], "FINAL_RUN_PROJECTION_MISMATCH")

    def test_evidence_free_pass_claim_is_blocked(self):
        claim = self.done_claim(checks=[])
        claim["evidenceRefs"] = []
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(claim),
            )
        self.assertEqual((result["operation"], result["result"], status), ("PRE_DONE_CLAIM", "BLOCKED", 2))
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "run.json").exists())

    def test_hidden_failed_leaf_result_cannot_pass(self):
        self.publish_command_result(exit_code=9)
        claim = self.done_claim(checks=[{
            "id": "verify.unit",
            "result": "PASS",
            "evidenceRefs": [".ai-runs/run-1/commands/verify.unit/attempt-1.json"],
            "reason": None,
        }])
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(claim),
            )
        self.assertEqual((result["operation"], result["result"], status), ("PRE_DONE_CLAIM", "FAIL", 1))
        run_index = json.loads((self.root / ".ai-runs" / "run-1" / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(run_index["result"], "FAIL")

    def test_blocking_policy_violation_precedes_integrity_pass(self):
        self.publish_command_result(exit_code=0)
        self.publish_policy_violation()
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(self.done_claim()),
            )
        self.assertEqual((result["operation"], result["result"], status), ("PRE_DONE_CLAIM", "POLICY_VIOLATION", 4))
        run_index = json.loads((self.root / ".ai-runs" / "run-1" / "run.json").read_text(encoding="utf-8"))
        self.assertEqual(run_index["result"], "BLOCKED")

    def test_stale_generated_summary_blocks_finalization(self):
        self.publish_command_result(exit_code=0)
        summary = self.root / "ai" / "project-state.md"
        summary.write_text(
            summary.read_text(encoding="utf-8").replace("Updated at: `2026-07-10T14:17:27Z`", "Updated at: `1999-01-01T00:00:00Z`"),
            encoding="utf-8",
        )
        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            result, status = self.helper.prepare_done_claim(
                self.root, "run-1", self.write_claim(self.done_claim()),
            )
        self.assertEqual((result["operation"], result["result"], status), ("PRE_DONE_CLAIM", "INVALID_STATE", 5))
        self.assertEqual(result["reason"], "PROJECT_STATE_SUMMARY_STALE")
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "run.json").exists())

    def test_validation_failure_before_run_publication_rolls_back_and_retries(self):
        self.publish_command_result(exit_code=0)
        claim_ref = self.write_claim(self.done_claim())
        failure = self.helper.InvalidStateError([self.helper.validation_error(
            "INJECTED_FINALIZATION_FAILURE", message="injected finalization validation failure",
        )])
        with (
            mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)),
            mock.patch.object(
                self.helper,
                "publish_done_gate_manifest_run",
                side_effect=lambda *args: self.inject_partial_finalization_failure(failure),
            ),
        ):
            result, status = self.helper.prepare_done_claim(self.root, "run-1", claim_ref)
        self.assertEqual((result["result"], result["reason"], status), (
            "INVALID_STATE", "INJECTED_FINALIZATION_FAILURE", 5,
        ))
        self.assertEqual(self.session()["state"], "OPEN")
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "run.json").exists())
        self.assert_partial_finalization_absent()

        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            retry, retry_status = self.helper.prepare_done_claim(self.root, "run-1", claim_ref)
        self.assertEqual((retry["result"], retry_status), ("PASS", 0))

    def test_io_failure_before_run_publication_rolls_back_and_retries(self):
        self.publish_command_result(exit_code=0)
        claim_ref = self.write_claim(self.done_claim())
        failure = OSError("injected finalization I/O failure")
        with (
            mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)),
            mock.patch.object(
                self.helper,
                "publish_done_gate_manifest_run",
                side_effect=lambda *args: self.inject_partial_finalization_failure(failure),
            ),
        ):
            result, status = self.helper.prepare_done_claim(self.root, "run-1", claim_ref)
        self.assertEqual((result["result"], result["reason"], status), (
            "INVALID_STATE", "PRE_DONE_CLAIM_FAILED", 5,
        ))
        self.assertEqual(self.session()["state"], "OPEN")
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "run.json").exists())
        self.assert_partial_finalization_absent()

        with mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)):
            retry, retry_status = self.helper.prepare_done_claim(self.root, "run-1", claim_ref)
        self.assertEqual((retry["result"], retry_status), ("PASS", 0))

    def test_mutated_finalizing_session_requires_explicit_recovery(self):
        self.publish_command_result(exit_code=0)
        claim_ref = self.write_claim(self.done_claim())
        failure = self.helper.InvalidStateError([self.helper.validation_error(
            "INJECTED_FINALIZATION_FAILURE", message="injected finalization validation failure",
        )])
        with (
            mock.patch.object(self.helper, "run_current_preflight", return_value=(preflight_pass(), 0)),
            mock.patch.object(
                self.helper,
                "publish_done_gate_manifest_run",
                side_effect=lambda *args: self.inject_partial_finalization_failure(
                    failure, mutate_session=True,
                ),
            ),
        ):
            result, status = self.helper.prepare_done_claim(self.root, "run-1", claim_ref)
        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "FINALIZATION_RECOVERY_REQUIRED", 2,
        ))
        self.assertEqual(self.session()["state"], "FINALIZING")
        self.assertFalse((self.root / ".ai-runs" / "run-1" / "run.json").exists())
        for path in self.partial_finalization_paths():
            self.assertTrue(path.exists(), path)


class Phase1B2Task7RepositoryBoundaryTests(unittest.TestCase):
    def read_repository_text(self, relative_path):
        return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")

    def test_agents_declares_the_closed_phase_1b2_repository_boundary(self):
        agents = self.read_repository_text("AGENTS.md")
        required_contracts = (
            "`scripts/ai/command-runner.sh` is the only supported project-command path after Phase 1B-2.",
            "Direct project-command execution remains prohibited.",
            "`RISKY` and `DESTRUCTIVE` commands remain prohibited; approval records are audit-only and never grant execution authority.",
            "Non-POSIX project-command execution remains `NOT_CONFIGURED` and prohibited.",
            "Standalone `workflow-gate.sh` stages never launch project commands.",
            "Phase 1B-3 adds integrity-only finalization, artifact manifests, finalized `run.json`, and done-claim checks for supported-path run evidence.",
            "Phase 1B-3 reports `completenessEvaluated: false` and `scope: INTEGRITY_ONLY`; it does not prove verification completeness, registry `VERIFIED`, reconciliation-complete, issue-backed closure, or unqualified overall `DONE` claims.",
        )
        for contract in required_contracts:
            with self.subTest(contract=contract):
                self.assertIn(contract, agents)
        self.assertIn("JSON is canonical. Markdown summaries must not override or contradict JSON.", agents)
        self.assertNotIn("The Phase 1B-2 execution gateway is still absent.", agents)

    def test_work_logs_preserve_history_and_approved_task7_review_state(self):
        summary = self.read_repository_text(
            "ai/work-logs/issue-4/README.md"
        )
        index = self.read_repository_text("ai/work-logs/index.md")
        log_root = "ai/work-logs/issue-4"
        final_review = self.read_repository_text(f"{log_root}/phase-1b-2-reviewer.md")
        log_directory = REPOSITORY_ROOT / log_root
        role_logs = tuple(sorted(
            path.name for path in log_directory.glob("*.md")
            if path.name.endswith(("-agent.md", "-reviewer.md", "-rereviewer.md", "-verifier.md"))
        ))
        self.assertEqual(37, len(role_logs))
        required_fields = (
            "issue", "issue_url", "agent", "tracking_status", "status", "owning_feature",
            "current_owner", "started_at", "ended_at", "last_updated", "branch", "related_files",
            "changed_files", "commands_run", "tests_run", "blockers", "reconciliation_required",
            "issue_creation_attempted_at", "issue_creation_failure_reason", "expected_issue_scope",
            "migration_history",
        )
        canonical_statuses = {"planned", "in_progress", "handoff_needed", "blocked", "in_review", "done"}
        exact_attempt = "issue_creation_attempted_at: 2026-07-10T12:37:12Z"
        exact_reason = 'issue_creation_failure_reason: "authorization failure: GitHub API 403 Resource not accessible by integration"'
        exact_scope = 'expected_issue_scope: "Specify, implement, and contract-verify AI Workflow Enforcement Phase 1B command gateway without product behavior changes."'
        for role_log in role_logs:
            with self.subTest(role_log=role_log):
                text = self.read_repository_text(f"{log_root}/{role_log}")
                self.assertTrue(text.startswith("---\n"))
                frontmatter = text.split("---", 2)[1]
                for field in required_fields:
                    self.assertRegex(frontmatter, rf"(?m)^{field}:")
                self.assertRegex(frontmatter, r"(?m)^issue: 4$")
                self.assertRegex(frontmatter, r"(?m)^issue_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4$")
                self.assertRegex(frontmatter, r"(?m)^agent: \S+$")
                self.assertIn("tracking_status: issue_backed", frontmatter)
                status = re.search(r"(?m)^status: (\S+)$", frontmatter).group(1)
                self.assertIn(status, canonical_statuses)
                self.assertRegex(frontmatter, r'(?m)^owning_feature: "none"$')
                self.assertRegex(frontmatter, r"(?m)^current_owner: \S+$")
                self.assertRegex(frontmatter, r"(?m)^started_at: \S+$")
                self.assertRegex(frontmatter, r"(?m)^last_updated: \S+$")
                self.assertRegex(frontmatter, r"(?m)^branch: main$")
                self.assertIn("reconciliation_required: false", frontmatter)
                self.assertIn("comment_url: https://github.com/116Lv/sparta-ch6-advanced/issues/4#issuecomment-", frontmatter)
                self.assertIn(exact_attempt, frontmatter)
                self.assertIn(exact_reason, frontmatter)
                self.assertIn(exact_scope, frontmatter)
                self.assertIn("from: ai/work-logs/no-issue/phase-1b-command-gateway", frontmatter)
                self.assertIn("to: ai/work-logs/issue-4", frontmatter)
                self.assertIn(f"]({role_log})", summary)
        summary_updated = re.search(r"(?m)^last_updated: (\S+)$", summary).group(1)
        index_row = next(line for line in index.splitlines() if "issue-4/README.md" in line)
        self.assertIn(f"| {summary_updated} |", index_row)
        summary_frontmatter = summary.split("---", 2)[1]
        final_review_frontmatter = final_review.split("---", 2)[1]
        for frontmatter in (summary_frontmatter, final_review_frontmatter):
            self.assertRegex(frontmatter, r"(?m)^tracking_status: issue_backed$")
            self.assertRegex(frontmatter, r"(?m)^status: done$")
            self.assertRegex(frontmatter, r"(?m)^reconciliation_required: false$")
            self.assertIn(exact_reason, frontmatter)
        self.assertIn("Phase 1B-1", summary)
        self.assertIn("PASS / APPROVED", summary)
        for task in range(1, 8):
            self.assertIn(f"Phase 1B-2 Task {task}: `PASS`", summary)
        self.assertIn(
            "Phase 1B-3 integrity-only finalization and done-claim gate implementation is technically PASS",
            summary,
        )
        self.assertIn("[Phase 1B-3 Implementation Agent](phase-1b-3-implementation-agent.md): `done`", summary)
        self.assertIn("[Phase 1B-3 Reviewer](phase-1b-3-reviewer.md): `done`", summary)
        self.assertIn(
            "**PASS / APPROVED. Status: DONE. Findings: Critical 0, Important 0, Minor 0.**",
            final_review,
        )
        self.assertIn(
            "| #4 | issue_backed | done | none | phase-1b-3-reviewer |",
            index_row,
        )
        self.assertIn(
            "Phase 1B-3 remains integrity-only and this record does not claim verification completeness, "
            "Issue closure, or unqualified overall DONE.",
            summary,
        )
        self.assertIn(
            "This review makes no issue-backed, reconciliation-complete, registry-VERIFIED, "
            "verification-complete, Phase 1B-3, or unqualified overall DONE claim.",
            final_review,
        )
        combined = summary + "\n" + final_review
        for unqualified_claim in (
            r"(?mi)^overall(?: workflow)? status:\s*done\b",
            r"(?mi)^issue-backed(?: status| claim)?:\s*(?:done|complete|pass)\b",
            r"(?mi)^reconciliation(?: status)?:\s*(?:done|complete|pass)\b",
        ):
            with self.subTest(unqualified_claim=unqualified_claim):
                self.assertNotRegex(combined, unqualified_claim)

    def test_reconciled_work_log_local_markdown_links_resolve(self):
        markdown_link = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
        for issue_number in range(4, 9):
            log_directory = REPOSITORY_ROOT / f"ai/work-logs/issue-{issue_number}"
            for log_path in sorted(log_directory.glob("*.md")):
                text = log_path.read_text(encoding="utf-8")
                for raw_target in markdown_link.findall(text):
                    target = raw_target.strip().strip("<>").split("#", 1)[0]
                    if not target or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
                        continue
                    with self.subTest(issue=issue_number, log=log_path.name, target=target):
                        self.assertTrue((log_path.parent / target).resolve().exists())

    def test_phase_1b3_repository_artifacts_remain_absent(self):
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())
        self.assertEqual(list(REPOSITORY_ROOT.rglob("artifact-manifest.json")), [])
        self.assertEqual(list((REPOSITORY_ROOT / ".ai-runs").rglob("run.json")), [])


class Phase2AContextCacheTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()

    def read_repository_text(self, relative_path):
        return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")

    def test_phase_2a_policy_documents_exist_and_are_linked(self):
        required = (
            "ai/context-map.md",
            "ai/cache-policy.md",
            "ai/tool-call-policy.md",
            "ai/resource-budget.md",
            "ai/workflow-cache.md",
        )
        for relative in required:
            with self.subTest(relative=relative):
                self.assertTrue((REPOSITORY_ROOT / relative).is_file(), relative)

        agents = self.read_repository_text("AGENTS.md")
        index = self.read_repository_text("docs/00-index.md")
        routing = self.read_repository_text("ai/document-routing.md")
        for relative in required:
            with self.subTest(link=relative):
                self.assertIn(relative, agents + "\n" + index + "\n" + routing)

    def test_context_map_and_workflow_cache_validate_through_allowlist(self):
        self.assertIn("context-map", self.helper.SCHEMA_NAMES)
        self.assertIn("workflow-cache", self.helper.SCHEMA_NAMES)
        self.assertIn("repo-intake-result", self.helper.SCHEMA_NAMES)
        context = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/context-map.json")
        cache = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/workflow-cache.json")
        self.assertEqual(context["schemaVersion"], 1)
        self.assertEqual(cache["schemaVersion"], 1)
        self.assertTrue(context["routes"])
        self.assertIsInstance(cache["entries"], list)

    def test_phase_2a_policy_text_preserves_repository_boundary(self):
        combined = "\n".join(self.read_repository_text(path) for path in (
            "ai/context-map.md",
            "ai/cache-policy.md",
            "ai/tool-call-policy.md",
            "ai/resource-budget.md",
            "ai/workflow-cache.md",
        ))
        required = (
            "JSON is canonical",
            "Markdown is not parsed as executable state",
            "repository scripts cannot intercept every host file read, search, or external tool call before Phase 3",
            "Product commands remain NOT RUN",
            "Phase 2A does not evaluate verification completeness",
        )
        for phrase in required:
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)


class Phase2ARepoIntakeTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        self.root = Path(tempfile.mkdtemp()) / "repository"
        self.addCleanup(remove_readonly_tree, self.root.parent)
        shutil.copytree(REPOSITORY_ROOT, self.root, ignore=shutil.ignore_patterns(".git", ".ai-runs", "__pycache__"))

    def test_repo_intake_passes_with_schema_backed_proposals_and_no_ai_runs(self):
        result, status = self.helper.repo_intake(self.root)
        self.assertEqual((result["operation"], result["result"], status), ("REPO_INTAKE", "PASS", 0))
        self.helper.validate(self.root, result, "ai/schemas/repo-intake-result.schema.json")
        self.assertEqual(result["data"]["contextMapRef"], "ai/context-map.json")
        self.assertEqual(result["data"]["workflowCacheRef"], "ai/workflow-cache.json")
        self.assertEqual(result["data"]["createdAiRuns"], False)
        self.assertFalse((self.root / ".ai-runs").exists())
        self.assertTrue(result["data"]["projectStateRefresh"])
        self.assertTrue(result["data"]["commandDiscoveryUpdates"])
        self.assertFalse(any(item.get("proposedStatus") == "VERIFIED" for item in result["data"]["commandDiscoveryUpdates"]))

    def test_repo_intake_rejects_context_route_escape(self):
        context_path = self.root / "ai" / "context-map.json"
        context = json.loads(context_path.read_text(encoding="utf-8"))
        context["routes"][0]["requiredDocuments"].append("../outside.md")
        context_path.write_text(json.dumps(context), encoding="utf-8")
        result, status = self.helper.repo_intake(self.root)
        self.assertEqual((result["operation"], result["result"], status), ("REPO_INTAKE", "INVALID_STATE", 5))
        self.assertIn(result["reason"], ("CONTEXT_MAP_PATH_INVALID", "SCHEMA_VALIDATION_ERROR"))

    def test_repo_intake_reports_stale_and_uncertain_cache_entries(self):
        cache_path = self.root / "ai" / "workflow-cache.json"
        stale_digest = "0" * 64
        cache = {
            "$schema": "./schemas/workflow-cache.schema.json",
            "$id": "ai/workflow-cache.json",
            "schemaVersion": 1,
            "updatedAt": "2026-07-12T00:00:00Z",
            "entries": [
                {
                    "id": "read-agents",
                    "kind": "FILE_DISCOVERY",
                    "status": "FRESH",
                    "key": {
                        "paths": [{"path": "AGENTS.md", "sha256": stale_digest}],
                        "environmentFingerprint": None
                    },
                    "summary": "stale digest fixture",
                    "evidenceRefs": ["AGENTS.md"],
                    "createdAt": "2026-07-12T00:00:00Z"
                },
                {
                    "id": "unmapped",
                    "kind": "FILE_DISCOVERY",
                    "status": "FRESH",
                    "key": {
                        "paths": [{"path": "docs/does-not-exist.md", "sha256": stale_digest}],
                        "environmentFingerprint": None
                    },
                    "summary": "uncertain missing path fixture",
                    "evidenceRefs": [],
                    "createdAt": "2026-07-12T00:00:00Z"
                }
            ],
            "handoffNotes": [],
            "invalidationEvents": []
        }
        cache_path.write_text(json.dumps(cache), encoding="utf-8")
        result, status = self.helper.repo_intake(self.root)
        self.assertEqual((result["result"], status), ("PASS", 0))
        invalidation = {item["entryId"]: item["status"] for item in result["data"]["cacheInvalidation"]}
        self.assertEqual(invalidation["read-agents"], "STALE")
        self.assertEqual(invalidation["unmapped"], "UNCERTAIN")


class Phase2BSkillsHandoffTests(unittest.TestCase):
    REQUIRED_SKILLS = (
        "repo-intake",
        "command-runner",
        "verification-runner",
        "api-smoke-verifier",
        "failure-triage",
        "docs-sync",
        "review-gate",
    )
    PROJECT_COMMAND_TOKENS = (
        "gradlew",
        "gradlew.bat",
        "docker",
        "docker-compose",
        "curl",
        "wget",
        "mysql",
        "psql",
        "java -jar",
        "bootRun",
        "migration",
        "seed",
        "scripts/ai/command-runner.sh run",
    )

    def setUp(self):
        self.helper = load_helper()

    def read_repository_text(self, relative_path):
        return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")

    def test_phase_2b_skill_catalog_and_documents_are_complete(self):
        self.assertIn("skill-catalog", self.helper.SCHEMA_NAMES)
        catalog = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/skill-catalog.json")
        self.assertEqual(catalog["schemaVersion"], 1)
        self.assertEqual({entry["id"] for entry in catalog["skills"]}, set(self.REQUIRED_SKILLS))

        for entry in catalog["skills"]:
            with self.subTest(skill=entry["id"]):
                document_path = REPOSITORY_ROOT / entry["document"]
                self.assertTrue(document_path.is_file(), entry["document"])
                document = document_path.read_text(encoding="utf-8")
                for heading in (
                    "## Purpose",
                    "## Required Inputs",
                    "## Allowed Operations",
                    "## Prohibited Operations",
                    "## Evidence Outputs",
                    "## Handoff And Reuse",
                    "## Phase 2B Boundary",
                ):
                    self.assertIn(heading, document)
                self.assertIn("Product commands remain NOT RUN in Phase 2B", document)
                self.assertIn(entry["routeId"], ("repo-wide-ai-workflow",))
                self.assertIn("notRunProjectCommands", entry["handoffFields"])
                self.assertFalse(any(output.startswith(".ai-runs/") for output in entry["evidenceOutputs"]))

        api_smoke = (REPOSITORY_ROOT / "ai/skills/api-smoke-verifier.md").read_text(encoding="utf-8")
        self.assertIn("NOT_CONFIGURED", api_smoke)
        self.assertIn("BLOCKED", api_smoke)
        self.assertIn("must not run HTTP, curl, or API calls in Phase 2B", api_smoke)

    def test_agent_handoff_and_workflow_cache_reuse_validate(self):
        self.assertIn("agent-handoff", self.helper.SCHEMA_NAMES)
        handoff = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/agent-handoff.json")
        cache = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/workflow-cache.json")
        self.assertEqual(handoff["routeId"], "repo-wide-ai-workflow")
        self.assertEqual(handoff["owningFeature"], "none")
        self.assertEqual(handoff["githubIssue"]["trackingStatus"], "issue_backed")
        self.assertEqual(handoff["githubIssue"]["issueNumber"], 7)
        self.assertFalse(handoff["githubIssue"]["reconciliationRequired"])
        self.assertIn("issues/7#issuecomment-", handoff["githubIssue"]["reconciliationCommentUrl"])
        self.assertEqual(
            handoff["githubIssue"]["previousReconciliationError"],
            "authorization failure: GitHub API 403 Resource not accessible by integration",
        )
        self.assertEqual(handoff["phase3AIssue"], {
            "issueNumber": 10,
            "issueUrl": "https://github.com/116Lv/sparta-ch6-advanced/issues/10",
            "trackingStatus": "issue_backed",
        })
        self.assertEqual(set(handoff["skillIds"]), set(self.REQUIRED_SKILLS))
        self.assertIn("ai/work-logs/issue-5/README.md", handoff["reusableContextRefs"])
        self.assertIn("ai/work-logs/issue-6/README.md", handoff["workLogRefs"])
        for not_run in (
            "Gradle",
            "build",
            "product/unit project tests",
            "application server",
            "Docker Compose",
            "HTTP/curl/API",
            "database",
            "migration",
            "seed",
            "infrastructure commands",
        ):
            self.assertIn(not_run, handoff["notRunProjectCommands"])

        handoff_entries = [entry for entry in cache["entries"] if entry["kind"] == "HANDOFF_CONTEXT"]
        self.assertTrue(handoff_entries)
        refs = set()
        for entry in handoff_entries:
            refs.update(entry["evidenceRefs"])
            if entry["status"] == "FRESH":
                for path_entry in entry["key"]["paths"]:
                    current_digest = hashlib.sha256(
                        (REPOSITORY_ROOT / path_entry["path"]).read_bytes()
                    ).hexdigest()
                    self.assertEqual(current_digest, path_entry["sha256"], path_entry["path"])
        self.assertIn("ai/agent-handoff.json", refs)
        self.assertIn("ai/work-logs/issue-5/README.md", refs)
        self.assertIn("ai/work-logs/issue-6/README.md", refs)
        self.assertFalse(any(ref.startswith(".ai-runs/") for ref in refs))
        self.assertTrue(any(note["id"] == "phase-2b-skills-handoff" for note in cache["handoffNotes"]))

    def test_work_log_and_routing_docs_link_phase_2b_reuse_contracts(self):
        combined_routing = "\n".join(self.read_repository_text(path) for path in (
            "AGENTS.md",
            "docs/00-index.md",
            "ai/document-routing.md",
        ))
        for link in ("ai/skills/README.md", "ai/agent-handoff.md", "ai/agent-handoff.json", "ai/skill-catalog.json"):
            with self.subTest(link=link):
                self.assertIn(link, combined_routing)

        combined_work_logs = "\n".join(self.read_repository_text(path) for path in (
            "ai/subagent-workflow.md",
            "ai/work-log-template.md",
            "ai/work-logs/README.md",
        ))
        for field in (
            "skill_ids",
            "handoff_state_ref",
            "reusable_context_refs",
            "not_run_project_commands",
            "github_reconciliation_status",
        ):
            with self.subTest(field=field):
                self.assertIn(field, combined_work_logs)

        index = self.read_repository_text("ai/work-logs/index.md")
        self.assertIn("| #5 | issue_backed | done | none | orchestrator |", index)
        self.assertIn("[Phase 2A context intake and cache control](issue-5/README.md)", index)
        self.assertIn("| #6 | issue_backed | done | none | orchestrator |", index)
        self.assertIn("[Phase 2B skills and handoff reuse](issue-6/README.md)", index)

        phase_2b_summary = self.read_repository_text("ai/work-logs/issue-6/README.md")
        self.assertIn("authorization failure: GitHub API 403 Resource not accessible by integration", phase_2b_summary)
        self.assertIn("does not authorize product command execution, Issue closure, or unqualified overall DONE", phase_2b_summary)

    def test_phase_2b_static_boundary_guards_do_not_expose_product_command_paths(self):
        for relative_path in (
            "scripts/ai/runtime-preflight.sh",
            "scripts/ai/repo-intake.sh",
            "scripts/ai/workflow_helper.py",
        ):
            source = self.read_repository_text(relative_path)
            executable_lines = [
                line.strip()
                for line in source.splitlines()
                if line.lstrip().startswith(("subprocess.", "os.system", "os.exec", "Popen(", "run_process(", "exec "))
                or "command-runner.sh run" in line
            ]
            with self.subTest(relative_path=relative_path):
                joined = "\n".join(executable_lines)
                for token in self.PROJECT_COMMAND_TOKENS:
                    self.assertNotIn(token, joined)

    def test_phase_2b_repository_artifacts_remain_absent(self):
        bad = []
        for path in REPOSITORY_ROOT.rglob("*"):
            if ".git" in path.parts:
                continue
            normalized = str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")
            if normalized.startswith("ai/fixtures/"):
                continue
            if normalized.startswith(".ai-runs/") or path.name in {"artifact-manifest.json", "run.json"}:
                bad.append(normalized)
        self.assertEqual(bad, [])


class Phase2CVerificationGateTests(unittest.TestCase):
    ENTRY_POINTS = (
        "verification-level",
        "api-smoke",
        "failure-triage",
        "review",
        "done-claim",
    )
    CHANGE_TYPES = (
        "documentation-only",
        "static-workflow",
        "domain-logic",
        "db-api",
        "auth-permission",
        "critical-data",
        "user-flow",
    )

    def setUp(self):
        self.helper = load_helper()
        self.root = Path(tempfile.mkdtemp()) / "repository"
        self.addCleanup(remove_readonly_tree, self.root.parent)
        shutil.copytree(REPOSITORY_ROOT, self.root, ignore=shutil.ignore_patterns(".git", ".ai-runs", "__pycache__"))

    def read_repository_text(self, relative_path):
        return (REPOSITORY_ROOT / relative_path).read_text(encoding="utf-8")

    def write_leaf_results(self, results):
        path = self.root / "ai" / "fixtures" / "phase-2c-leaf-results.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"results": results}), encoding="utf-8")
        return "ai/fixtures/phase-2c-leaf-results.json"

    def write_json_fixture(self, name, payload):
        path = self.root / "ai" / "fixtures" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path.relative_to(self.root).as_posix()

    def test_verification_policy_and_result_schemas_are_allowlisted(self):
        self.assertIn("verification-policy", self.helper.SCHEMA_NAMES)
        self.assertIn("verification-gate-result", self.helper.SCHEMA_NAMES)
        policy = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/verification-policy.json")
        self.assertEqual(policy["schemaVersion"], 1)
        self.assertEqual({entry["id"] for entry in policy["entryPoints"]}, set(self.ENTRY_POINTS))
        self.assertEqual({item["id"] for item in policy["changeTypes"]}, set(self.CHANGE_TYPES))

        by_change = {item["id"]: item for item in policy["changeTypes"]}
        self.assertEqual(by_change["documentation-only"]["minimumVerificationLevel"], 0)
        self.assertIn("verify.api-smoke", by_change["db-api"]["requiredChecks"])
        self.assertIn("verify.api-smoke", by_change["auth-permission"]["requiredChecks"])
        self.assertIn("verify.e2e", by_change["critical-data"]["requiredChecks"])
        self.assertIn("failure-triage", by_change["static-workflow"]["entryPoints"])

    def test_verification_gate_maps_leaf_results_by_change_type(self):
        not_configured = self.write_leaf_results([
            {"checkId": "review-gate", "result": "PASS", "evidenceRef": "ai/work-logs/issue-7/reviewer.md", "reason": "Independent static review evidence is present."},
            {"checkId": "done-claim-gate", "result": "PASS", "evidenceRef": "ai/work-logs/issue-7/README.md", "reason": "Completion claim checklist evidence is present."},
            {"checkId": "verify.api-smoke", "result": "NOT_CONFIGURED", "evidenceRef": None, "reason": "No API smoke runner is configured."},
        ])
        doc_result, doc_status = self.helper.verification_gate(
            self.root, "documentation-only", "verification-level", not_configured,
            task_key="issue-10", gate_invocation_id="gate-doc",
        )
        self.assertEqual((doc_result["result"], doc_status), ("PASS", 0))
        doc_checks = {item["checkId"]: item for item in doc_result["data"]["checks"]}
        self.assertEqual(doc_checks["verify.api-smoke"]["mappedResult"], "NOT_APPLICABLE")
        self.assertEqual(doc_result["data"]["completenessEvaluated"], True)

        not_applicable_result, not_applicable_status = self.helper.verification_gate(
            self.root, "documentation-only", "api-smoke", not_configured,
            task_key="issue-10", gate_invocation_id="gate-na",
        )
        self.assertEqual((not_applicable_result["result"], not_applicable_status), ("NOT_APPLICABLE", 6))
        self.assertEqual(not_applicable_result["data"]["entryPoint"], "api-smoke")

        api_result, api_status = self.helper.verification_gate(
            self.root, "db-api", "api-smoke", not_configured,
            task_key="issue-10", gate_invocation_id="gate-api",
        )
        self.assertEqual((api_result["result"], api_status), ("BLOCKED", 2))
        api_checks = {item["checkId"]: item for item in api_result["data"]["checks"]}
        self.assertEqual(api_checks["verify.api-smoke"]["mappedResult"], "BLOCKED")

        failed = self.write_leaf_results([
            {"checkId": "verify.unit", "result": "FAIL", "evidenceRef": "ai/fixtures/fake-unit-result.json", "reason": "Fixture failure."},
        ])
        logic_result, logic_status = self.helper.verification_gate(
            self.root, "domain-logic", "verification-level", failed,
            task_key="issue-10", gate_invocation_id="gate-logic",
        )
        self.assertEqual((logic_result["result"], logic_status), ("FAIL", 1))
        logic_checks = {item["checkId"]: item for item in logic_result["data"]["checks"]}
        self.assertEqual(logic_checks["verify.unit"]["mappedResult"], "FAIL")

    def test_review_and_done_claim_gates_require_explicit_leaf_evidence(self):
        review_result, review_status = self.helper.verification_gate(
            self.root, "documentation-only", "review",
            task_key="issue-10", gate_invocation_id="gate-review",
        )
        self.assertEqual((review_result["result"], review_status), ("BLOCKED", 2))
        review_checks = {item["checkId"]: item for item in review_result["data"]["checks"]}
        self.assertEqual(review_checks["review-gate"]["rawResult"], "NOT_CONFIGURED")
        self.assertEqual(review_checks["review-gate"]["mappedResult"], "BLOCKED")

        done_result, done_status = self.helper.verification_gate(
            self.root, "documentation-only", "done-claim",
            task_key="issue-10", gate_invocation_id="gate-done",
        )
        self.assertEqual((done_result["result"], done_status), ("BLOCKED", 2))
        done_checks = {item["checkId"]: item for item in done_result["data"]["checks"]}
        self.assertEqual(done_checks["done-claim-gate"]["rawResult"], "NOT_CONFIGURED")
        self.assertEqual(done_checks["done-claim-gate"]["mappedResult"], "BLOCKED")

        explicit = self.write_leaf_results([
            {"checkId": "review-gate", "result": "PASS", "evidenceRef": "ai/work-logs/issue-7/reviewer.md", "reason": "Independent static review evidence is present."},
            {"checkId": "done-claim-gate", "result": "PASS", "evidenceRef": "ai/work-logs/issue-7/README.md", "reason": "Completion claim checklist evidence is present."},
        ])
        passed_result, passed_status = self.helper.verification_gate(
            self.root, "documentation-only", "review", explicit,
            task_key="issue-10", gate_invocation_id="gate-review-pass",
        )
        self.assertEqual((passed_result["result"], passed_status), ("PASS", 0))

    def test_verification_gate_shell_entrypoint_is_static_and_creates_no_ai_runs(self):
        shell = REPOSITORY_ROOT / "scripts" / "ai" / "verification-gate.sh"
        self.assertTrue(shell.is_file())
        bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if not bash.is_file():
            bash = Path("bash")
        command = [
            str(bash),
            str(shell),
            "--change-type",
            "documentation-only",
            "--entry-point",
            "verification-level",
            "--task-key",
            "issue-10",
            "--gate-invocation-id",
            "gate-shell",
            "--leaf-results-file",
            str(self.write_leaf_results([
                {"checkId": "review-gate", "result": "PASS", "evidenceRef": "ai/work-logs/issue-7/reviewer.md", "reason": "Independent static review evidence is present."},
                {"checkId": "done-claim-gate", "result": "PASS", "evidenceRef": "ai/work-logs/issue-7/README.md", "reason": "Completion claim checklist evidence is present."},
            ])),
            "--runtime-snapshot",
            self.write_json_fixture("runtime-snapshot.json", {"producerId": "fixture", "surfaces": []}),
            "--bypass-attempts",
            self.write_json_fixture("bypass-attempts.json", {"attempts": []}),
            "--output",
            "-",
        ]
        completed = subprocess.run(
            command,
            cwd=str(self.root),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr + completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual((result["operation"], result["result"]), ("VERIFICATION_GATE", "PASS"))
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())

        not_applicable = subprocess.run(
            [
                str(bash),
                str(shell),
                "--change-type",
                "documentation-only",
                "--entry-point",
                "api-smoke",
                "--task-key",
                "issue-10",
                "--gate-invocation-id",
                "gate-shell-na",
                "--output",
                "-",
            ],
            cwd=str(REPOSITORY_ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(not_applicable.returncode, 6, not_applicable.stderr + not_applicable.stdout)
        not_applicable_result = json.loads(not_applicable.stdout)
        self.assertEqual(not_applicable_result["result"], "NOT_APPLICABLE")

    def test_phase_2c_documents_link_executable_gates_and_preserve_boundaries(self):
        for relative in (
            "ai/verification-gates.md",
            "ai/verification-policy.json",
            "scripts/ai/verification-gate.sh",
        ):
            with self.subTest(relative=relative):
                self.assertTrue((REPOSITORY_ROOT / relative).is_file(), relative)

        combined = "\n".join(self.read_repository_text(path) for path in (
            "AGENTS.md",
            "docs/00-index.md",
            "ai/document-routing.md",
            "ai/skills/README.md",
            "ai/skills/verification-runner.md",
            "ai/skills/api-smoke-verifier.md",
            "ai/skills/failure-triage.md",
            "ai/skills/review-gate.md",
            "ai/verification-levels.md",
            "ai/qa-gate.md",
            "ai/done-claim-template.md",
            "ai/issue-completion-checklist.md",
            "ai/subagent-workflow.md",
            "ai/work-log-template.md",
            "ai/work-logs/README.md",
            "ai/agent-handoff.md",
            "ai/workflow-cache.md",
            "specs/_template/spec.md",
            "specs/_template/plan.md",
            "specs/_template/tasks.md",
            "specs/_template/checklist.md",
            "specs/_template/decisions.md",
        ))
        for phrase in (
            "ai/verification-gates.md",
            "ai/verification-policy.json",
            "scripts/ai/verification-gate.sh",
            "verification completeness",
            "task/change applicability",
            "NOT_CONFIGURED",
            "NOT_APPLICABLE",
            "BLOCKED",
            "FAIL",
            "Product commands remain NOT RUN",
            "pending_issue",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, combined)

        catalog = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/skill-catalog.json")
        gate_entry_points = {entry["id"]: entry["allowedEntryPoint"] for entry in catalog["skills"]}
        self.assertIn("scripts/ai/verification-gate.sh", gate_entry_points["verification-runner"])
        self.assertIn("scripts/ai/verification-gate.sh", gate_entry_points["api-smoke-verifier"])
        self.assertIn("scripts/ai/verification-gate.sh", gate_entry_points["failure-triage"])
        self.assertIn("scripts/ai/verification-gate.sh", gate_entry_points["review-gate"])

    def test_catalog_verification_gate_commands_include_required_wrapper_correlation_arguments(self):
        catalog = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/skill-catalog.json")
        entry_points = {entry["id"]: entry["allowedEntryPoint"] for entry in catalog["skills"]}
        expected_entry_points = {
            "verification-runner": "verification-level",
            "api-smoke-verifier": "api-smoke",
            "failure-triage": "failure-triage",
            "review-gate": "review",
        }

        for skill_id, entry_point in expected_entry_points.items():
            with self.subTest(skill_id=skill_id):
                self.assertEqual(entry_points[skill_id].split(), [
                    "scripts/ai/verification-gate.sh",
                    "--change-type", "<type>",
                    "--entry-point", entry_point,
                    "--task-key", "<task-key>",
                    "--gate-invocation-id", "<gate-invocation-id>",
                    "--output", "-",
                ])

    def test_phase_2c_repository_artifacts_and_registry_verified_remain_absent(self):
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())
        bad = []
        for path in REPOSITORY_ROOT.rglob("*"):
            if ".git" in path.parts:
                continue
            normalized = str(path.relative_to(REPOSITORY_ROOT)).replace("\\", "/")
            if normalized.startswith("ai/fixtures/"):
                continue
            if normalized.startswith(".ai-runs/") or path.name in {"artifact-manifest.json", "run.json"}:
                bad.append(normalized)
        self.assertEqual(bad, [])
        registry = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/command-registry.json")
        self.assertFalse(any(command["configurationStatus"] == "VERIFIED" for command in registry["commands"]))
        summary = self.read_repository_text("ai/work-logs/issue-7/README.md")
        self.assertIn("authorization failure: GitHub API 403 Resource not accessible by integration", summary)


class Phase3ANativeRuntimeAdapterTests(unittest.TestCase):
    SCHEMA_PATHS = {
        "native-runtime-adapters": "ai/schemas/native-runtime-adapters.schema.json",
        "native-bypass-attempt": "ai/schemas/native-bypass-attempt.schema.json",
        "native-runtime-snapshot": "ai/schemas/native-runtime-snapshot.schema.json",
        "native-adapter-result": "ai/schemas/native-adapter-result.schema.json",
    }

    @classmethod
    def setUpClass(cls):
        cls.helper = load_helper()

    def setUp(self):
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        shutil.copytree(REPOSITORY_ROOT / "ai" / "schemas", self.root / "ai" / "schemas")
        shutil.copyfile(
            REPOSITORY_ROOT / "ai" / "native-runtime-adapters.json",
            self.root / "ai" / "native-runtime-adapters.json",
        )
        shutil.copyfile(
            REPOSITORY_ROOT / "ai" / "verification-policy.json",
            self.root / "ai" / "verification-policy.json",
        )
        (self.root / "ai" / "fixtures").mkdir()
        if hasattr(self.helper, "NATIVE_CONSUMED_CHALLENGES"):
            self.helper.NATIVE_CONSUMED_CHALLENGES.clear()

    def tearDown(self):
        self.temporary_directory.cleanup()

    def write_fixture(self, name, value):
        path = self.root / "ai" / "fixtures" / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return path.relative_to(self.root).as_posix()

    def write_verification_leaf_results(self, results, name="phase-3a-leaf-results.json"):
        return self.write_fixture(name, {"results": results})

    def copy_repository_fixture(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        root = Path(directory.name) / "repository"
        shutil.copytree(self.root, root)
        return root

    @staticmethod
    def native_check(result):
        return next(
            check for check in result["data"]["checks"]
            if check["checkId"] == "native-runtime-adapter"
        )

    def write_temp_snapshot(self, snapshot):
        return self.write_fixture("runtime-snapshot.json", snapshot)

    def write_attempts(self, attempts):
        return self.write_fixture("bypass-attempts.json", {"attempts": attempts})

    def write_supported_policy(self, public_key_fingerprint="a" * 64):
        policy = self.supported_host_policy()
        policy["supportedHosts"][0].update({
            "hostId": "codex-desktop",
            "minimumHostVersion": "1.0.0",
            "ed25519PublicKeyFingerprint": public_key_fingerprint,
        })
        return self.write_fixture("supported-native-runtime-adapters.json", policy)

    def valid_attempt(self, **overrides):
        attempt = self.bypass_attempt()
        attempt.update(overrides)
        return attempt

    def validator(self, schema_name):
        with (REPOSITORY_ROOT / self.SCHEMA_PATHS[schema_name]).open(encoding="utf-8") as handle:
            schema = json.load(handle)
        Draft202012Validator.check_schema(schema)
        return Draft202012Validator(schema, format_checker=FormatChecker())

    def assert_valid(self, schema_name, instance):
        self.assertEqual(list(self.validator(schema_name).iter_errors(instance)), [])

    def assert_invalid(self, schema_name, instance):
        self.assertNotEqual(list(self.validator(schema_name).iter_errors(instance)), [])

    def test_invalid_native_adapter_cli_result_is_schema_valid_and_fail_closed(self):
        result, status = self.helper.invalid_cli_result("native-adapter-gate")

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS", 2,
        ))
        self.assert_valid("native-adapter-result", result)

    def run_native_adapter_cli_subprocess(self, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts" / "ai" / "workflow_helper.py"),
                "native-adapter-gate",
                *arguments,
            ],
            cwd=str(REPOSITORY_ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def run_verification_gate_cli_subprocess(self, *arguments):
        return subprocess.run(
            [
                sys.executable,
                str(REPOSITORY_ROOT / "scripts" / "ai" / "workflow_helper.py"),
                "verification-gate",
                *arguments,
            ],
            cwd=str(REPOSITORY_ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

    def test_native_adapter_cli_missing_required_argument_returns_structured_result(self):
        completed = self.run_native_adapter_cli_subprocess(
            "--task-key", "issue-10",
            "--gate-invocation-id", "gate-1",
            "--output", "-",
        )

        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("Traceback", completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual((result["result"], result["reason"]), (
            "BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS",
        ))
        self.assert_valid("native-adapter-result", result)

    def test_native_adapter_cli_unknown_option_returns_structured_result(self):
        completed = self.run_native_adapter_cli_subprocess(
            "--repository-root", str(REPOSITORY_ROOT),
            "--task-key", "issue-10",
            "--gate-invocation-id", "gate-1",
            "--output", "-",
            "--unknown-option",
        )

        self.assertEqual(completed.returncode, 2)
        self.assertNotIn("Traceback", completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual((result["result"], result["reason"]), (
            "BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS",
        ))
        self.assert_valid("native-adapter-result", result)

    def supported_host_policy(self):
        return {
            "$schema": "ai/schemas/native-runtime-adapters.schema.json",
            "$id": "ai/native-runtime-adapters.json",
            "schemaVersion": 1,
            "updatedAt": "2026-07-13T01:00:00Z",
            "supportedHosts": [{
                "hostId": "supported-host",
                "minimumHostVersion": "1.2.3",
                "adapterVersionRange": ">=1.0.0 <2.0.0",
                "producerId": "example.native.adapter",
                "ed25519PublicKeyFingerprint": "a" * 64,
                "surfaces": self.supported_surfaces(),
            }],
            "currentHost": {
                "hostId": "codex-desktop",
                "hostVersion": "1.0.0",
                "versionProvenance": "PROBED",
                "probeRefs": ["ai/native-runtime-adapters.md"],
                "surfaces": self.unsupported_surfaces(),
            },
            "completionPolicy": {
                "phase2cCheckId": "native-runtime-adapter",
                "unsupportedLeafResult": "NOT_APPLICABLE",
                "supportedHostFailureResult": "BLOCKED",
            },
        }

    @staticmethod
    def supported_surfaces():
        return [
            {"surface": surface, "status": "NOT_CONFIGURED", "reasonCode": "ADAPTER_CONFIGURATION_REQUIRED"}
            for surface in ("COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL")
        ]

    @staticmethod
    def unsupported_surfaces():
        return [
            {"surface": surface, "status": "UNSUPPORTED", "reasonCode": "HOST_NOT_SUPPORTED"}
            for surface in ("COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL")
        ]

    @staticmethod
    def bypass_attempt():
        return {
            "$schema": "ai/schemas/native-bypass-attempt.schema.json",
            "$id": "ai/native-bypass-attempt.json",
            "schemaVersion": 1,
            "attemptId": "attempt-1",
            "eventId": "event-1",
            "observedAt": "2026-07-13T01:00:00Z",
            "hostId": "supported-host",
            "hostVersion": "1.2.3",
            "adapterVersion": "1.0.0",
            "surface": "COMMAND",
            "operationType": "FILE_READ",
            "commandIntent": "FILE_READ",
            "statusAtObservation": "ENFORCED",
            "decision": "BLOCKED",
            "reasonCode": "DIRECT_TOOL_BYPASS",
            "repositoryGatewayExpected": True,
            "taskKey": "issue-10",
            "gateInvocationId": "gate-1",
            "runId": None,
            "deduplicationKey": "dedupe-1",
            "lifecycle": "DETECTED",
            "resolvedAt": None,
            "resolutionReason": None,
            "summary": {
                "target": {
                    "classification": "REPOSITORY_PATH",
                    "repositoryPath": "docs/00-index.md",
                },
                "argumentSummary": {
                    "classification": "STRUCTURAL_PLACEHOLDERS",
                    "count": 1,
                    "sha256": "a" * 64,
                },
                "querySummary": {"classification": "NONE"},
                "toolPayloadSummary": {"classification": "NONE"},
            },
        }

    @staticmethod
    def adapter_result():
        return {
            "$schema": "ai/schemas/native-adapter-result.schema.json",
            "$id": "ai/native-adapter-result.json",
            "schemaVersion": 1,
            "operation": "NATIVE_ADAPTER_GATE",
            "result": "UNSUPPORTED",
            "phase2cLeafResult": "NOT_APPLICABLE",
            "reason": "The current host has no supported native adapter.",
            "data": {
                "hostId": "codex-desktop",
                "hostVersion": None,
                "versionProvenance": "UNPROBED",
                "claimedSurfaces": Phase3ANativeRuntimeAdapterTests.unsupported_surfaces(),
                "trustedSurfaces": Phase3ANativeRuntimeAdapterTests.unsupported_surfaces(),
                "bypassAttemptRefs": [],
                "repositoryOnlyQualification": True,
                "phase2CLeafResult": "NOT_APPLICABLE",
            },
        }

    @staticmethod
    def canonical_snapshot_bytes(snapshot):
        payload = {key: value for key, value in snapshot.items() if key != "signature"}
        return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")

    def signed_snapshot(self, gate_invocation_id="gate-signed", observed_at=None,
                        producer_id="example.native.adapter", host_id="codex-desktop",
                        host_version="1.0.0", callback_result="BLOCKED",
                        resolution_event_ids=None, task_key="issue-10",
                        bypass_attempts=None):
        if Ed25519PrivateKey is None:
            self.skipTest("cryptography is unavailable for the valid Ed25519 vector")
        private_key = Ed25519PrivateKey.generate()
        public_key_bytes = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
        fingerprint = hashlib.sha256(public_key_bytes).hexdigest()
        if observed_at is None:
            observed_at = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        bypass_attempts = [] if bypass_attempts is None else bypass_attempts
        event_set_bytes = json.dumps(
            sorted(bypass_attempts, key=lambda attempt: attempt["eventId"]),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        snapshot = {
            "$schema": "ai/schemas/native-runtime-snapshot.schema.json",
            "$id": "ai/native-runtime-snapshot.json",
            "schemaVersion": 1,
            "producerId": producer_id,
            "hostId": host_id,
            "hostVersion": host_version,
            "adapterVersion": "1.0.0",
            "observedAt": observed_at,
            "taskKey": task_key,
            "gateInvocationId": gate_invocation_id,
            "bypassEventCount": len(bypass_attempts),
            "bypassEventSetSha256": hashlib.sha256(event_set_bytes).hexdigest(),
            "resolutionEventIds": [] if resolution_event_ids is None else resolution_event_ids,
            "surfaces": [
                {
                    "surface": surface,
                    "status": "ENFORCED",
                    "reasonCode": "SIGNED_CALLBACK_PROOF",
                    "callbackProof": {
                        "gateInvocationId": gate_invocation_id,
                        "observedBeforeOperation": True,
                        "challengeResult": callback_result,
                    },
                }
                for surface in ("COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL")
            ],
            "publicKey": {
                "algorithm": "Ed25519",
                "encoding": "RAW_BASE64",
                "fingerprintSha256": fingerprint,
                "value": base64.b64encode(public_key_bytes).decode("ascii"),
            },
            "signature": {
                "algorithm": "Ed25519",
                "encoding": "BASE64",
                "value": "",
            },
        }
        snapshot["signature"]["value"] = base64.b64encode(
            private_key.sign(self.canonical_snapshot_bytes(snapshot))
        ).decode("ascii")
        return snapshot, fingerprint, private_key

    def resolved_transition_attempts(self, gate_invocation_id="gate-resolution"):
        prior_detection = self.valid_attempt(
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T00:59:00Z",
        )
        current_resolution = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-resolution-2",
            gateInvocationId=gate_invocation_id,
            observedAt="2026-07-13T01:00:00Z",
            lifecycle="RESOLVED",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
        )
        return [prior_detection, current_resolution]

    def resign_snapshot(self, snapshot, private_key):
        snapshot["signature"]["value"] = base64.b64encode(
            private_key.sign(self.canonical_snapshot_bytes(snapshot))
        ).decode("ascii")
        return snapshot

    def assert_trusted_not_enforced(self, result):
        self.assertEqual(
            {surface["status"] for surface in result["data"]["trustedSurfaces"]},
            {"NOT_CONFIGURED"},
        )

    def supported_policy_with_fingerprint(self, fingerprint):
        policy = self.supported_host_policy()
        policy["supportedHosts"][0].update({
            "hostId": "codex-desktop",
            "minimumHostVersion": "1.0.0",
            "ed25519PublicKeyFingerprint": fingerprint,
        })
        return policy

    def test_runtime_snapshot_schema_and_canonicalizer_are_available(self):
        self.assertIn("native-runtime-snapshot", self.helper.SCHEMA_NAMES)
        self.assertTrue((REPOSITORY_ROOT / self.SCHEMA_PATHS["native-runtime-snapshot"]).is_file())
        snapshot, _, _ = self.signed_snapshot()
        self.assert_valid("native-runtime-snapshot", snapshot)

    def test_resolution_event_ids_are_required_unique_and_bounded_in_signed_snapshot(self):
        snapshot, _, private_key = self.signed_snapshot(
            resolution_event_ids=["event-resolution-2"],
        )
        self.assert_valid("native-runtime-snapshot", snapshot)
        self.assertIn(b'"resolutionEventIds":["event-resolution-2"]',
                      self.helper.native_snapshot_canonical_bytes(snapshot))

        invalid_cases = {}
        missing = dict(snapshot)
        missing.pop("resolutionEventIds")
        invalid_cases["missing"] = missing
        duplicate = dict(snapshot)
        duplicate["resolutionEventIds"] = ["event-resolution-2", "event-resolution-2"]
        invalid_cases["duplicate"] = self.resign_snapshot(duplicate, private_key)
        too_many = dict(snapshot)
        too_many["resolutionEventIds"] = [f"event-{index}" for index in range(65)]
        invalid_cases["too-many"] = self.resign_snapshot(too_many, private_key)
        too_long = dict(snapshot)
        too_long["resolutionEventIds"] = ["e" * 129]
        invalid_cases["too-long"] = self.resign_snapshot(too_long, private_key)

        for name, invalid in invalid_cases.items():
            with self.subTest(name=name):
                self.assert_invalid("native-runtime-snapshot", invalid)

    def test_signed_snapshot_binds_task_and_complete_bypass_event_set(self):
        attempts = self.resolved_transition_attempts("gate-event-set")
        snapshot, fingerprint, private_key = self.signed_snapshot(
            gate_invocation_id="gate-event-set",
            resolution_event_ids=["event-resolution-2"],
            bypass_attempts=attempts,
        )
        self.assert_valid("native-runtime-snapshot", snapshot)
        canonical = self.helper.native_snapshot_canonical_bytes(snapshot)
        self.assertIn(b'"taskKey":"issue-10"', canonical)
        self.assertIn(b'"bypassEventCount":2', canonical)
        self.assertIn(b'"bypassEventSetSha256":', canonical)

        altered = json.loads(json.dumps(attempts))
        for attempt in altered:
            attempt["deduplicationKey"] = "grafted-group"
        altered_result, altered_status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-event-set",
            runtime_snapshot_ref=self.write_fixture("snapshot-event-set.json", snapshot),
            bypass_attempts_ref=self.write_fixture("attempts-event-set.json", {"attempts": altered}),
            policy_ref=self.write_fixture(
                "policy-event-set.json", self.supported_policy_with_fingerprint(fingerprint),
            ),
        )
        self.assertEqual((altered_result["result"], altered_result["reason"], altered_status), (
            "BLOCKED", "NATIVE_BYPASS_EVENT_SET_MISMATCH", 2,
        ))

        wrong_task = dict(snapshot)
        wrong_task["taskKey"] = "other-task"
        self.resign_snapshot(wrong_task, private_key)
        task_result, task_status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-event-set",
            runtime_snapshot_ref=self.write_fixture("snapshot-wrong-task.json", wrong_task),
            bypass_attempts_ref=self.write_fixture("attempts-wrong-task.json", {"attempts": attempts}),
            policy_ref=self.write_fixture(
                "policy-wrong-task.json", self.supported_policy_with_fingerprint(fingerprint),
            ),
        )
        self.assertEqual((task_result["result"], task_result["reason"], task_status), (
            "BLOCKED", "NATIVE_ADAPTER_TASK_MISMATCH", 2,
        ))

    def test_bypass_surface_operation_semantics_are_closed(self):
        valid_cases = (
            self.valid_attempt(surface="COMMAND", operationType="COMMAND", commandIntent="COMMAND"),
            self.valid_attempt(surface="COMMAND", operationType="FILE_READ", commandIntent="FILE_READ"),
            self.valid_attempt(surface="FILE_READ", operationType="FILE_READ", commandIntent=None),
            self.valid_attempt(surface="SEARCH", operationType="SEARCH", commandIntent=None),
            self.valid_attempt(surface="TOOL_CALL", operationType="TOOL_CALL", commandIntent=None),
        )
        for attempt in valid_cases:
            if attempt.get("commandIntent") is None:
                attempt.pop("commandIntent", None)
            self.assert_valid("native-bypass-attempt", attempt)

        invalid_cases = (
            self.valid_attempt(surface="COMMAND", operationType="COMMAND", commandIntent=None),
            self.valid_attempt(surface="FILE_READ", operationType="COMMAND", commandIntent="FILE_READ"),
            self.valid_attempt(surface="COMMAND", operationType="SEARCH", commandIntent="FILE_READ"),
            self.valid_attempt(surface="SEARCH", operationType="SEARCH", commandIntent="SEARCH"),
        )
        for attempt in invalid_cases:
            if attempt.get("commandIntent") is None:
                attempt.pop("commandIntent", None)
            self.assert_invalid("native-bypass-attempt", attempt)

    def test_ed25519_backend_unavailable_is_structured_and_fail_closed(self):
        if UnsupportedAlgorithm is None:
            self.skipTest("cryptography exception type is unavailable")
        snapshot, fingerprint, _ = self.signed_snapshot()

        class UnsupportedEd25519:
            @staticmethod
            def from_public_bytes(_value):
                raise UnsupportedAlgorithm("Ed25519 is unavailable")

        with mock.patch.object(self.helper, "Ed25519PublicKey", UnsupportedEd25519):
            result, status = self.helper.native_adapter_gate(
                self.root,
                "issue-10",
                "gate-signed",
                runtime_snapshot_ref=self.write_temp_snapshot(snapshot),
                policy_ref=self.write_supported_policy(fingerprint),
            )
        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "NATIVE_ADAPTER_CRYPTO_UNAVAILABLE", 2,
        ))

    def test_native_snapshot_canonical_bytes_match_restricted_rfc8785_vector(self):
        canonicalizer = getattr(self.helper, "native_snapshot_canonical_bytes", None)
        self.assertIsNotNone(canonicalizer)
        vector = {
            "z": ["ASCII", True, None, 7],
            "signature": {"algorithm": "Ed25519", "encoding": "BASE64", "value": "excluded"},
            "a": {"k": "v"},
        }
        self.assertEqual(canonicalizer(vector), b'{"a":{"k":"v"},"z":["ASCII",true,null,7]}')
        for invalid in (
            {"value": 1.5, "signature": {}},
            {"value": "non-ascii-\u00e9", "signature": {}},
            {"non-ascii-\u00e9": "value", "signature": {}},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    canonicalizer(invalid)

    def test_temporary_supported_policy_accepts_real_signed_enforced_snapshot(self):
        snapshot, fingerprint, _ = self.signed_snapshot()
        policy_ref = self.write_supported_policy(fingerprint)
        missing, missing_status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-missing",
            policy_ref=policy_ref,
        )
        self.assertEqual((missing["result"], missing_status), ("NOT_CONFIGURED", 3))
        self.assert_trusted_not_enforced(missing)

        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-signed",
            runtime_snapshot_ref=self.write_temp_snapshot(snapshot),
            policy_ref=policy_ref,
        )
        self.assertEqual((result["result"], result["reason"], status), ("PASS", None, 0))
        self.assertEqual({surface["status"] for surface in result["data"]["claimedSurfaces"]}, {"ENFORCED"})
        self.assertEqual({surface["status"] for surface in result["data"]["trustedSurfaces"]}, {"ENFORCED"})
        self.assertFalse(result["data"]["repositoryOnlyQualification"])
        self.assertFalse((self.root / ".ai-runs").exists())

    def test_valid_signed_bound_resolution_clears_lifecycle_and_passes(self):
        attempts = self.resolved_transition_attempts()
        snapshot, fingerprint, _ = self.signed_snapshot(
            gate_invocation_id="gate-resolution",
            resolution_event_ids=["event-resolution-2"],
            bypass_attempts=attempts,
        )
        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-resolution",
            runtime_snapshot_ref=self.write_temp_snapshot(snapshot),
            bypass_attempts_ref=self.write_attempts(attempts),
            policy_ref=self.write_supported_policy(fingerprint),
        )

        self.assertEqual((result["result"], result["reason"], status), ("PASS", None, 0))
        self.assertEqual(
            {surface["status"] for surface in result["data"]["trustedSurfaces"]},
            {"ENFORCED"},
        )

    def test_signed_resolution_binding_missing_mismatched_or_extra_blocks_precisely(self):
        cases = (
            ("missing", [], "NATIVE_BYPASS_RESOLUTION_BINDING_MISSING"),
            ("mismatched", ["event-wrong"], "NATIVE_BYPASS_RESOLUTION_BINDING_MISMATCH"),
            (
                "extra",
                ["event-resolution-2", "event-extra"],
                "NATIVE_BYPASS_RESOLUTION_BINDING_EXTRA",
            ),
        )
        for name, resolution_event_ids, expected_reason in cases:
            with self.subTest(name=name):
                gate_invocation_id = f"gate-binding-{name}"
                attempts = self.resolved_transition_attempts(gate_invocation_id)
                snapshot, fingerprint, _ = self.signed_snapshot(
                    gate_invocation_id=gate_invocation_id,
                    resolution_event_ids=resolution_event_ids,
                    bypass_attempts=attempts,
                )
                result, status = self.helper.native_adapter_gate(
                    self.root,
                    "issue-10",
                    gate_invocation_id,
                    runtime_snapshot_ref=self.write_fixture(f"snapshot-{name}.json", snapshot),
                    bypass_attempts_ref=self.write_fixture(
                        f"attempts-{name}.json",
                        {"attempts": attempts},
                    ),
                    policy_ref=self.write_fixture(
                        f"policy-binding-{name}.json",
                        self.supported_policy_with_fingerprint(fingerprint),
                    ),
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "BLOCKED", expected_reason, 2,
                ))

    def test_stale_or_bad_signature_cannot_authorize_bound_resolution(self):
        stale_time = (
            dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=301)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        cases = []

        stale, stale_fingerprint, _ = self.signed_snapshot(
            gate_invocation_id="gate-resolution-stale",
            observed_at=stale_time,
            resolution_event_ids=["event-resolution-2"],
        )
        cases.append((
            "stale", stale, stale_fingerprint, "gate-resolution-stale",
            "NATIVE_ADAPTER_SNAPSHOT_STALE",
        ))

        bad_signature, signature_fingerprint, _ = self.signed_snapshot(
            gate_invocation_id="gate-resolution-signature",
            resolution_event_ids=["event-resolution-2"],
        )
        signature = bytearray(base64.b64decode(bad_signature["signature"]["value"]))
        signature[-1] ^= 1
        bad_signature["signature"]["value"] = base64.b64encode(bytes(signature)).decode("ascii")
        cases.append((
            "signature", bad_signature, signature_fingerprint, "gate-resolution-signature",
            "NATIVE_ADAPTER_SIGNATURE_UNTRUSTED",
        ))

        for name, snapshot, fingerprint, gate_invocation_id, expected_reason in cases:
            with self.subTest(name=name):
                result, status = self.helper.native_adapter_gate(
                    self.root,
                    "issue-10",
                    gate_invocation_id,
                    runtime_snapshot_ref=self.write_fixture(f"resolution-{name}.json", snapshot),
                    bypass_attempts_ref=self.write_fixture(
                        f"resolution-attempts-{name}.json",
                        {"attempts": self.resolved_transition_attempts(gate_invocation_id)},
                    ),
                    policy_ref=self.write_fixture(
                        f"resolution-policy-{name}.json",
                        self.supported_policy_with_fingerprint(fingerprint),
                    ),
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "BLOCKED", expected_reason, 2,
                ))

    def test_resolution_claims_block_without_supported_host_or_snapshot(self):
        attempts_ref = self.write_attempts(self.resolved_transition_attempts())
        unsupported, unsupported_status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-resolution",
            bypass_attempts_ref=attempts_ref,
        )
        self.assertEqual((unsupported["result"], unsupported["reason"], unsupported_status), (
            "BLOCKED", "NATIVE_BYPASS_RESOLUTION_HOST_UNSUPPORTED", 2,
        ))

        no_snapshot, no_snapshot_status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-resolution",
            bypass_attempts_ref=attempts_ref,
            policy_ref=self.write_supported_policy(),
        )
        self.assertEqual((no_snapshot["result"], no_snapshot["reason"], no_snapshot_status), (
            "BLOCKED", "NATIVE_BYPASS_RESOLUTION_SNAPSHOT_REQUIRED", 2,
        ))

        unprobed_policy = self.supported_policy_with_fingerprint("a" * 64)
        unprobed_policy["currentHost"].update({
            "hostVersion": None,
            "versionProvenance": "UNPROBED",
        })
        unprobed, unprobed_status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-resolution",
            bypass_attempts_ref=attempts_ref,
            policy_ref=self.write_fixture("resolution-unprobed-policy.json", unprobed_policy),
        )
        self.assertEqual((unprobed["result"], unprobed["reason"], unprobed_status), (
            "BLOCKED", "NATIVE_BYPASS_RESOLUTION_HOST_UNSUPPORTED", 2,
        ))

    def test_ordinary_unresolved_detection_blocks_before_snapshot_trust(self):
        snapshot, fingerprint, _ = self.signed_snapshot(gate_invocation_id="gate-unresolved")
        unresolved = self.valid_attempt(gateInvocationId="gate-unresolved")
        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-unresolved",
            runtime_snapshot_ref=self.write_temp_snapshot(snapshot),
            bypass_attempts_ref=self.write_attempts([unresolved]),
            policy_ref=self.write_supported_policy(fingerprint),
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "NATIVE_BYPASS_UNRESOLVED", 2,
        ))
        self.assertEqual(self.helper.NATIVE_CONSUMED_CHALLENGES, set())

    def test_untrusted_snapshot_claims_never_promote_trusted_surfaces(self):
        stale_time = (
            dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=301)
        ).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        cases = {}

        snapshot, fingerprint, private_key = self.signed_snapshot(gate_invocation_id="gate-bad-producer")
        snapshot["producerId"] = "untrusted.producer"
        cases["producer"] = (
            self.resign_snapshot(snapshot, private_key), fingerprint, "gate-bad-producer",
            "NATIVE_ADAPTER_PRODUCER_UNTRUSTED",
        )

        snapshot, fingerprint, _ = self.signed_snapshot(gate_invocation_id="gate-bad-key")
        cases["key"] = (snapshot, "f" * 64, "gate-bad-key", "NATIVE_ADAPTER_KEY_UNTRUSTED")

        snapshot, fingerprint, _ = self.signed_snapshot(gate_invocation_id="gate-bad-signature")
        signature = bytearray(base64.b64decode(snapshot["signature"]["value"]))
        signature[0] ^= 1
        snapshot["signature"]["value"] = base64.b64encode(bytes(signature)).decode("ascii")
        cases["signature"] = (
            snapshot, fingerprint, "gate-bad-signature", "NATIVE_ADAPTER_SIGNATURE_UNTRUSTED",
        )

        snapshot, fingerprint, _ = self.signed_snapshot(
            gate_invocation_id="gate-stale", observed_at=stale_time,
        )
        cases["stale"] = (snapshot, fingerprint, "gate-stale", "NATIVE_ADAPTER_SNAPSHOT_STALE")

        snapshot, fingerprint, _ = self.signed_snapshot(gate_invocation_id="signed-other-gate")
        cases["challenge"] = (
            snapshot, fingerprint, "gate-challenge", "NATIVE_ADAPTER_CHALLENGE_MISMATCH",
        )

        snapshot, fingerprint, _ = self.signed_snapshot(
            gate_invocation_id="gate-callback", callback_result="FAILED",
        )
        cases["callback"] = (
            snapshot, fingerprint, "gate-callback", "NATIVE_ADAPTER_CALLBACK_FAILED",
        )

        snapshot, fingerprint, private_key = self.signed_snapshot(gate_invocation_id="gate-host")
        snapshot["hostVersion"] = "1.0.1"
        cases["host-version"] = (
            self.resign_snapshot(snapshot, private_key), fingerprint, "gate-host",
            "NATIVE_ADAPTER_HOST_MISMATCH",
        )

        for name, (snapshot, policy_fingerprint, gate_invocation_id, expected_reason) in cases.items():
            with self.subTest(name=name):
                result, status = self.helper.native_adapter_gate(
                    self.root,
                    "issue-10",
                    gate_invocation_id,
                    runtime_snapshot_ref=self.write_fixture(f"runtime-{name}.json", snapshot),
                    policy_ref=self.write_fixture(
                        f"policy-{name}.json",
                        self.supported_policy_with_fingerprint(policy_fingerprint),
                    ),
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "BLOCKED", expected_reason, 2,
                ))
                self.assertEqual(
                    {surface["status"] for surface in result["data"]["claimedSurfaces"]},
                    {"ENFORCED"},
                )
                self.assert_trusted_not_enforced(result)

    def test_replayed_challenge_and_missing_crypto_block_without_trusted_enforcement(self):
        snapshot, fingerprint, _ = self.signed_snapshot(gate_invocation_id="gate-one-use")
        snapshot_ref = self.write_temp_snapshot(snapshot)
        policy_ref = self.write_supported_policy(fingerprint)
        first, first_status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-one-use", snapshot_ref, policy_ref=policy_ref,
        )
        self.assertEqual((first["result"], first_status), ("PASS", 0))

        replay, replay_status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-one-use", snapshot_ref, policy_ref=policy_ref,
        )
        self.assertEqual((replay["result"], replay["reason"], replay_status), (
            "BLOCKED", "NATIVE_ADAPTER_CHALLENGE_REPLAYED", 2,
        ))
        self.assert_trusted_not_enforced(replay)

        crypto_snapshot, crypto_fingerprint, _ = self.signed_snapshot(gate_invocation_id="gate-no-crypto")
        with mock.patch.object(self.helper, "Ed25519PublicKey", None, create=True):
            unavailable, unavailable_status = self.helper.native_adapter_gate(
                self.root,
                "issue-10",
                "gate-no-crypto",
                runtime_snapshot_ref=self.write_fixture("runtime-no-crypto.json", crypto_snapshot),
                policy_ref=self.write_fixture(
                    "policy-no-crypto.json", self.supported_policy_with_fingerprint(crypto_fingerprint),
                ),
            )
        self.assertEqual((unavailable["result"], unavailable["reason"], unavailable_status), (
            "BLOCKED", "NATIVE_ADAPTER_CRYPTO_UNAVAILABLE", 2,
        ))
        self.assert_trusted_not_enforced(unavailable)

    def test_version_provenance_conditionals_and_supported_matching_require_probe(self):
        canonical = json.loads(
            (REPOSITORY_ROOT / "ai/native-runtime-adapters.json").read_text(encoding="utf-8")
        )
        self.assertIsNone(canonical["currentHost"]["hostVersion"])
        self.assertEqual(canonical["currentHost"]["versionProvenance"], "UNPROBED")
        self.assert_valid("native-runtime-adapters", canonical)

        for provenance, version in (("UNPROBED", "1.0.0"), ("PROBED", None)):
            with self.subTest(provenance=provenance, version=version):
                policy = self.supported_host_policy()
                policy["currentHost"].update({"versionProvenance": provenance, "hostVersion": version})
                self.assert_invalid("native-runtime-adapters", policy)

        result = self.adapter_result()
        result["data"].update({"versionProvenance": "PROBED", "hostVersion": None})
        self.assert_invalid("native-adapter-result", result)

        unprobed = self.supported_policy_with_fingerprint("a" * 64)
        unprobed["currentHost"].update({"versionProvenance": "UNPROBED", "hostVersion": None})
        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-unprobed",
            policy_ref=self.write_fixture("policy-unprobed.json", unprobed),
        )
        self.assertEqual((result["result"], result["reason"], status), (
            "UNSUPPORTED", "HOST_UNSUPPORTED", 6,
        ))

    def test_repository_supported_host_policy_cannot_declare_runtime_enforcement(self):
        policy = self.supported_host_policy()
        self.assert_valid("native-runtime-adapters", policy)
        policy["supportedHosts"][0]["surfaces"][0]["status"] = "ENFORCED"
        self.assert_invalid("native-runtime-adapters", policy)

    def test_phase_3a_schemas_are_allowlisted_and_work_log_is_issue_backed(self):
        self.assertIn("native-runtime-adapters", self.helper.SCHEMA_NAMES)
        self.assertIn("native-bypass-attempt", self.helper.SCHEMA_NAMES)
        self.assertIn("native-adapter-result", self.helper.SCHEMA_NAMES)
        summary = (REPOSITORY_ROOT / "ai/work-logs/issue-10/README.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/116Lv/sparta-ch6-advanced/issues/10", summary)

    def test_issue_10_logs_cover_actual_phase_3a_files_and_use_tracked_references(self):
        expected_changed_files = {
            ".gitattributes",
            "AGENTS.md",
            "ai/agent-handoff.json",
            "ai/agent-handoff.md",
            "ai/cache-policy.md",
            "ai/document-routing.md",
            "ai/native-runtime-adapters.json",
            "ai/native-runtime-adapters.md",
            "ai/schemas/native-adapter-result.schema.json",
            "ai/schemas/agent-handoff.schema.json",
            "ai/schemas/native-bypass-attempt.schema.json",
            "ai/schemas/native-runtime-adapters.schema.json",
            "ai/schemas/native-runtime-snapshot.schema.json",
            "ai/schemas/verification-policy.schema.json",
            "ai/skill-catalog.json",
            "ai/tool-call-policy.md",
            "ai/verification-gates.md",
            "ai/verification-policy.json",
            "ai/work-logs/index.md",
            "ai/work-logs/issue-10/README.md",
            "ai/work-logs/issue-10/implementation-agent.md",
            "ai/work-logs/issue-10/plan-reviewer.md",
            "ai/work-logs/issue-10/reviewer.md",
            "ai/workflow-cache.json",
            "ai/workflow-cache.md",
            "docs/superpowers/plans/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-implementation.md",
            "docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md",
            "scripts/ai/native-adapter-gate.sh",
            "scripts/ai/tests/test_workflow_helper.py",
            "scripts/ai/verification-gate.sh",
            "scripts/ai/workflow_helper.py",
        }
        log_paths = (
            "ai/work-logs/issue-10/README.md",
            "ai/work-logs/issue-10/implementation-agent.md",
            "ai/work-logs/issue-10/plan-reviewer.md",
            "ai/work-logs/issue-10/reviewer.md",
        )
        for path in log_paths:
            with self.subTest(path=path):
                text = (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
                frontmatter = text.split("---", 2)[1]
                match = re.search(r"(?m)^changed_files:\n((?:  - [^\n]+\n)+)", frontmatter)
                self.assertIsNotNone(match)
                changed_files = {
                    line.removeprefix("  - ")
                    for line in match.group(1).splitlines()
                }
                self.assertEqual(changed_files, expected_changed_files)
                self.assertNotIn(".superpowers/sdd", text)

        summary = (REPOSITORY_ROOT / log_paths[0]).read_text(encoding="utf-8")
        last_updated = re.search(r"(?m)^last_updated: (\S+)$", summary).group(1)
        index = (REPOSITORY_ROOT / "ai/work-logs/index.md").read_text(encoding="utf-8")
        issue_10_row = next(line for line in index.splitlines() if line.startswith("| #10 |"))
        self.assertIn(last_updated, issue_10_row)

    def test_current_host_is_explicitly_unsupported_on_all_native_surfaces(self):
        policy_path = REPOSITORY_ROOT / "ai/native-runtime-adapters.json"
        self.assertTrue(policy_path.is_file())
        policy = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/native-runtime-adapters.json")

        self.assertEqual(policy["supportedHosts"], [])
        self.assertEqual(policy["currentHost"]["hostId"], "codex-desktop")
        self.assertEqual(
            {surface["surface"] for surface in policy["currentHost"]["surfaces"]},
            {"COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL"},
        )
        self.assertEqual({surface["status"] for surface in policy["currentHost"]["surfaces"]}, {"UNSUPPORTED"})

    def test_current_host_support_document_matches_canonical_policy(self):
        document_path = REPOSITORY_ROOT / "ai/native-runtime-adapters.md"
        self.assertTrue(document_path.is_file())

        policy = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/native-runtime-adapters.json")
        document = document_path.read_text(encoding="utf-8")

        self.assertIn("ai/native-runtime-adapters.json", document)
        self.assertIn("supportedHosts: []", document)
        self.assertIn(policy["currentHost"]["hostId"], document)
        for surface in policy["currentHost"]["surfaces"]:
            with self.subTest(surface=surface["surface"]):
                self.assertIn(surface["surface"], document)
                self.assertIn(surface["status"], document)
                self.assertIn(surface["reasonCode"], document)

    def test_closed_native_adapter_schemas_accept_complete_supported_host_vectors(self):
        self.assert_valid("native-runtime-adapters", self.supported_host_policy())
        self.assert_valid("native-bypass-attempt", self.bypass_attempt())
        self.assert_valid("native-adapter-result", self.adapter_result())

    def test_native_bypass_summary_accepts_only_closed_classifications_and_digests(self):
        attempt = self.bypass_attempt()
        attempt["summary"].update({
            "target": {
                "classification": "EXTERNAL_TARGET",
                "redactedCategory": "OUTSIDE_REPOSITORY_PATH",
                "sha256": "d" * 64,
            },
            "argumentSummary": {
                "classification": "ALLOWLISTED_LITERALS",
                "count": 2,
                "sha256": "a" * 64,
            },
            "querySummary": {
                "classification": "TEXT_QUERY",
                "sha256": "b" * 64,
            },
            "toolPayloadSummary": {
                "classification": "STRUCTURED_PAYLOAD",
                "sha256": "c" * 64,
            },
        })
        self.assert_valid("native-bypass-attempt", attempt)

        invalid_summaries = {
            "raw-query-string": {"querySummary": "alice@example.com"},
            "raw-query-content": {"querySummary": {
                "classification": "TEXT_QUERY",
                "sha256": "b" * 64,
                "content": "alice@example.com",
            }},
            "raw-tool-json": {"toolPayloadSummary": {
                "classification": "STRUCTURED_PAYLOAD",
                "sha256": "c" * 64,
                "content": '{"email":"alice@example.com"}',
            }},
            "none-query-digest": {"querySummary": {
                "classification": "NONE",
                "sha256": "b" * 64,
            }},
            "none-tool-content": {"toolPayloadSummary": {
                "classification": "NONE",
                "content": "{}",
            }},
            "raw-arguments": {"argumentSummary": {
                "classification": "ALLOWLISTED_LITERALS",
                "count": 1,
                "sha256": "a" * 64,
                "argv": ["--token", "opaque"],
            }},
            "unbounded-argument-count": {"argumentSummary": {
                "classification": "STRUCTURAL_PLACEHOLDERS",
                "count": 65,
                "sha256": "a" * 64,
            }},
            "absolute-repository-path": {"target": {
                "classification": "REPOSITORY_PATH",
                "repositoryPath": "C:/Users/alice/secret.json",
            }},
            "raw-external-target": {"target": {
                "classification": "EXTERNAL_TARGET",
                "redactedCategory": "OUTSIDE_REPOSITORY_PATH",
                "sha256": "d" * 64,
                "absolutePath": "C:/Users/alice/secret.json",
            }},
        }
        for name, summary_update in invalid_summaries.items():
            with self.subTest(name=name):
                invalid_attempt = self.bypass_attempt()
                invalid_attempt["summary"].update(summary_update)
                self.assert_invalid("native-bypass-attempt", invalid_attempt)

    def test_native_adapter_version_schemas_require_strict_semver_2(self):
        valid_version = "1.0.0-rc.1+build.5"
        invalid_versions = (
            "01.0.0", "1.01.0", "1.0.01", "1.0.0-01", "1.0.0-rc..1", "1.0.0-", "1.0.0\n",
        )
        vectors = (
            ("native-runtime-adapters", self.supported_host_policy, ("currentHost", "hostVersion")),
            ("native-runtime-adapters", self.supported_host_policy, ("supportedHosts", 0, "minimumHostVersion")),
            ("native-bypass-attempt", self.bypass_attempt, ("hostVersion",)),
            ("native-bypass-attempt", self.bypass_attempt, ("adapterVersion",)),
            ("native-adapter-result", self.adapter_result, ("data", "hostVersion")),
        )

        for schema_name, factory, path in vectors:
            with self.subTest(schema_name=schema_name, path=path, version=valid_version):
                instance = factory()
                if schema_name == "native-adapter-result" and path == ("data", "hostVersion"):
                    instance["data"]["versionProvenance"] = "PROBED"
                target = instance
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = valid_version
                self.assert_valid(schema_name, instance)
            for invalid_version in invalid_versions:
                with self.subTest(schema_name=schema_name, path=path, version=invalid_version):
                    instance = factory()
                    if schema_name == "native-adapter-result" and path == ("data", "hostVersion"):
                        instance["data"]["versionProvenance"] = "PROBED"
                    target = instance
                    for segment in path[:-1]:
                        target = target[segment]
                    target[path[-1]] = invalid_version
                    self.assert_invalid(schema_name, instance)

    def test_native_adapter_schema_patterns_use_portable_exact_end_and_reject_terminal_newlines(self):
        vectors = (
            ("native-runtime-adapters", self.supported_host_policy, ("updatedAt",), "2026-07-13T01:00:00Z"),
            ("native-runtime-adapters", self.supported_host_policy, ("supportedHosts", 0, "producerId"), "example.native.adapter"),
            ("native-runtime-adapters", self.supported_host_policy, ("supportedHosts", 0, "ed25519PublicKeyFingerprint"), "a" * 64),
            ("native-runtime-adapters", self.supported_host_policy, ("currentHost", "probeRefs", 0), "ai/native-runtime-adapters.md"),
            ("native-bypass-attempt", self.bypass_attempt, ("eventId",), "event-1"),
            ("native-bypass-attempt", self.bypass_attempt, ("observedAt",), "2026-07-13T01:00:00Z"),
            ("native-bypass-attempt", self.bypass_attempt, ("summary", "argumentSummary", "sha256"), "a" * 64),
            ("native-bypass-attempt", self.bypass_attempt, ("summary", "target", "repositoryPath"), "docs/00-index.md"),
            ("native-adapter-result", self.adapter_result, ("data", "hostVersion"), "1.0.0"),
        )
        for schema_name, factory, path, value in vectors:
            with self.subTest(schema_name=schema_name, path=path, value="valid"):
                instance = factory()
                if schema_name == "native-adapter-result" and path == ("data", "hostVersion"):
                    instance["data"]["versionProvenance"] = "PROBED"
                target = instance
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = value
                self.assert_valid(schema_name, instance)
            with self.subTest(schema_name=schema_name, path=path, value="terminal-newline"):
                instance = factory()
                if schema_name == "native-adapter-result" and path == ("data", "hostVersion"):
                    instance["data"]["versionProvenance"] = "PROBED"
                target = instance
                for segment in path[:-1]:
                    target = target[segment]
                target[path[-1]] = value + "\n"
                self.assert_invalid(schema_name, instance)

        result = self.adapter_result()
        result["data"]["bypassAttemptRefs"] = ["ai/native-bypass-attempts.json"]
        self.assert_valid("native-adapter-result", result)
        result["data"]["bypassAttemptRefs"] = ["ai/native-bypass-attempts.json\n"]
        self.assert_invalid("native-adapter-result", result)

        for schema_name in (
            "native-runtime-adapters",
            "native-bypass-attempt",
            "native-adapter-result",
        ):
            schema = json.loads((REPOSITORY_ROOT / "ai" / "schemas" / f"{schema_name}.schema.json").read_text(encoding="utf-8"))
            patterns = []
            pending = [schema]
            while pending:
                value = pending.pop()
                if isinstance(value, dict):
                    if "pattern" in value:
                        patterns.append(value["pattern"])
                    pending.extend(value.values())
                elif isinstance(value, list):
                    pending.extend(value)
            self.assertTrue(patterns)
            for pattern in patterns:
                self.assertNotIn("$", pattern)
                self.assertNotIn(r"\Z", pattern)
                self.assertIn(r"(?![\s\S])", pattern)

    def test_closed_native_adapter_schemas_reject_unknown_values_and_secret_bearing_fields(self):
        policy = self.supported_host_policy()
        policy["unexpected"] = True
        self.assert_invalid("native-runtime-adapters", policy)

        policy = self.supported_host_policy()
        policy["currentHost"]["surfaces"][0]["status"] = "PARTIALLY_ENFORCED"
        self.assert_invalid("native-runtime-adapters", policy)

        attempt = self.bypass_attempt()
        attempt["summary"]["target"] = "x" * 513
        self.assert_invalid("native-bypass-attempt", attempt)
        for raw_field in ("environment", "payload", "query", "argv"):
            with self.subTest(raw_field=raw_field):
                attempt = self.bypass_attempt()
                attempt[raw_field] = "secret"
                self.assert_invalid("native-bypass-attempt", attempt)

        result = self.adapter_result()
        result["result"] = "AUDIT_ONLY"
        self.assert_invalid("native-adapter-result", result)
        result = self.adapter_result()
        result["phase2cLeafResult"] = "UNSUPPORTED"
        self.assert_invalid("native-adapter-result", result)
        result = self.adapter_result()
        del result["data"]["phase2CLeafResult"]
        self.assert_invalid("native-adapter-result", result)
        result = self.adapter_result()
        result["data"]["phase2CLeafResult"] = "PASS"
        self.assert_invalid("native-adapter-result", result)

    def test_native_bypass_identifier_fields_preserve_their_length_limits(self):
        for field, maximum_length in (("taskKey", 128), ("runId", 128), ("deduplicationKey", 256)):
            with self.subTest(field=field):
                attempt = self.bypass_attempt()
                attempt[field] = "a" * (maximum_length + 1)
                self.assert_invalid("native-bypass-attempt", attempt)

    def test_bypass_lifecycle_requires_consistent_resolution_and_correlation(self):
        attempt = self.bypass_attempt()
        attempt.update({
            "lifecycle": "RESOLVED",
            "resolvedAt": None,
            "resolutionReason": "FALSE_POSITIVE",
        })
        self.assert_invalid("native-bypass-attempt", attempt)

        attempt = self.bypass_attempt()
        attempt["resolvedAt"] = "2026-07-13T01:01:00Z"
        self.assert_invalid("native-bypass-attempt", attempt)

        attempt = self.bypass_attempt()
        attempt.update({
            "lifecycle": "RESOLVED",
            "resolvedAt": "2026-07-13T01:01:00Z",
            "resolutionReason": "UNREVIEWED_REASON",
        })
        self.assert_invalid("native-bypass-attempt", attempt)

        for correlation_field in ("taskKey", "gateInvocationId", "deduplicationKey"):
            with self.subTest(correlation_field=correlation_field):
                attempt = self.bypass_attempt()
                del attempt[correlation_field]
                self.assert_invalid("native-bypass-attempt", attempt)

    def test_repository_helper_rejects_native_bypass_resolution_before_observation(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            schema_path = root / "ai/schemas/native-bypass-attempt.schema.json"
            attempt_path = root / "ai/native-bypass-attempt.json"
            schema_path.parent.mkdir(parents=True)
            shutil.copyfile(REPOSITORY_ROOT / self.SCHEMA_PATHS["native-bypass-attempt"], schema_path)

            valid_attempt = self.bypass_attempt()
            valid_attempt.update({
                "lifecycle": "RESOLVED",
                "resolvedAt": "2026-07-13T01:00:01Z",
                "resolutionReason": "REMEDIATED",
            })
            attempt_path.write_text(json.dumps(valid_attempt), encoding="utf-8")
            self.helper.validate_repository_instance(root, "ai/native-bypass-attempt.json")

            invalid_attempt = self.bypass_attempt()
            invalid_attempt.update({
                "lifecycle": "RESOLVED",
                "resolvedAt": "2026-07-13T00:59:59Z",
                "resolutionReason": "REMEDIATED",
            })
            attempt_path.write_text(json.dumps(invalid_attempt), encoding="utf-8")
            with self.assertRaises(self.helper.InvalidStateError):
                self.helper.validate_repository_instance(root, "ai/native-bypass-attempt.json")

    def test_native_adapter_leaf_is_required_for_every_change_type(self):
        policy = self.helper.validate_repository_instance(REPOSITORY_ROOT, "ai/verification-policy.json")
        for change in policy["changeTypes"]:
            with self.subTest(change_type=change["id"]):
                self.assertIn("native-runtime-adapter", change["requiredChecks"])

    def test_every_change_type_aggregates_explicit_native_adapter_state(self):
        supported_root = self.copy_repository_fixture()
        supported_policy = self.supported_host_policy()
        supported_policy["supportedHosts"][0].update({
            "hostId": "codex-desktop",
            "minimumHostVersion": "1.0.0",
        })
        (supported_root / "ai" / "native-runtime-adapters.json").write_text(
            json.dumps(supported_policy), encoding="utf-8",
        )
        policy = self.helper.validate_repository_instance(self.root, "ai/verification-policy.json")
        for change in policy["changeTypes"]:
            change_type = change["id"]
            with self.subTest(change_type=change_type, host="unsupported"):
                result, _ = self.helper.verification_gate(
                    self.root,
                    change_type,
                    "verification-level",
                    task_key="issue-10",
                    gate_invocation_id=f"gate-u-{change_type}",
                )
                native = self.native_check(result)
                self.assertEqual((native["rawResult"], native["mappedResult"], native["reason"]), (
                    "NOT_APPLICABLE", "NOT_APPLICABLE", "HOST_UNSUPPORTED",
                ))
            with self.subTest(change_type=change_type, host="supported"):
                blocked_result, blocked_status = self.helper.verification_gate(
                    supported_root,
                    change_type,
                    "verification-level",
                    task_key="issue-10",
                    gate_invocation_id=f"gate-b-{change_type}",
                )
                self.assertEqual((blocked_result["result"], blocked_status), ("BLOCKED", 2))
                self.assertEqual(self.native_check(blocked_result)["rawResult"], "NOT_CONFIGURED")

    def test_unsupported_host_pass_is_explicitly_repository_qualified(self):
        explicit = self.write_verification_leaf_results([
            {"checkId": "review-gate", "result": "PASS"},
            {"checkId": "done-claim-gate", "result": "PASS"},
        ])
        result, status = self.helper.verification_gate(
            self.root,
            "documentation-only",
            "verification-level",
            explicit,
            task_key="issue-10",
            gate_invocation_id="gate-qualified",
        )
        self.assertEqual((result["result"], result["reason"], status), (
            "PASS", "REPOSITORY_ONLY_HOST_UNSUPPORTED", 0,
        ))

    def test_external_native_adapter_leaf_is_rejected_before_leaf_lookup(self):
        supported_root = self.copy_repository_fixture()
        supported_policy = self.supported_host_policy()
        supported_policy["supportedHosts"][0].update({
            "hostId": "codex-desktop",
            "minimumHostVersion": "1.0.0",
        })
        (supported_root / "ai" / "native-runtime-adapters.json").write_text(
            json.dumps(supported_policy), encoding="utf-8",
        )
        variants = {
            "plain-pass": {"checkId": "native-runtime-adapter", "result": "PASS"},
            "repository-result-ref": {
                "checkId": "native-runtime-adapter",
                "result": "PASS",
                "adapterResultRef": "ai/fixtures/fake-native-adapter-result.json",
            },
            "correlation-mismatch": {
                "checkId": "native-runtime-adapter",
                "result": "PASS",
                "taskKey": "other-task",
                "gateInvocationId": "other-gate",
            },
            "policy-digest-mismatch": {
                "checkId": "native-runtime-adapter",
                "result": "PASS",
                "policySha256": "0" * 64,
            },
            "fixture-pass-empty-supported-hosts": {
                "checkId": "native-runtime-adapter",
                "result": "PASS",
                "reason": "fixture claimed PASS",
            },
        }
        for root_name, root in (("canonical", self.root), ("supported", supported_root)):
            for name, forged in variants.items():
                with self.subTest(root=root_name, variant=name):
                    ref = self.write_fixture(f"forged-{root_name}-{name}.json", {"results": [forged]})
                    if root != self.root:
                        destination = root / ref
                        destination.write_bytes((self.root / ref).read_bytes())
                    result, status = self.helper.verification_gate(
                        root,
                        "documentation-only",
                        "verification-level",
                        ref,
                        task_key="issue-10",
                        gate_invocation_id=f"gate-forged-{name}",
                    )
                    self.assertEqual((result["result"], result["reason"], status), (
                        "INVALID_STATE", "NATIVE_ADAPTER_LEAF_FORGED", 5,
                    ))

    def test_forged_native_adapter_leaf_precedes_correlation_and_applicability_returns(self):
        forged = self.write_verification_leaf_results([
            {"checkId": "native-runtime-adapter", "result": "PASS"},
        ])
        cases = (
            ("invalid-correlation", "verification-level", None, "gate-forged-correlation"),
            ("inapplicable-entry-point", "api-smoke", "issue-10", "gate-forged-inapplicable"),
        )

        for case, entry_point, task_key, gate_invocation_id in cases:
            with self.subTest(case=case):
                result, status = self.helper.verification_gate(
                    self.root,
                    "documentation-only",
                    entry_point,
                    forged,
                    task_key=task_key,
                    gate_invocation_id=gate_invocation_id,
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "INVALID_STATE", "NATIVE_ADAPTER_LEAF_FORGED", 5,
                ))

    def test_forged_native_adapter_leaf_precedes_earlier_malformed_leaf_result(self):
        forged = self.write_verification_leaf_results([
            {"checkId": 1, "result": "PASS"},
            {"checkId": "native-runtime-adapter", "result": "PASS"},
        ])

        result, status = self.helper.verification_gate(
            self.root,
            "documentation-only",
            "verification-level",
            forged,
            task_key="issue-10",
            gate_invocation_id="gate-forged-after-malformed",
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "INVALID_STATE", "NATIVE_ADAPTER_LEAF_FORGED", 5,
        ))

    def test_early_native_fail_preserves_failure_for_correlation_and_applicability_returns(self):
        malformed_bypass = self.write_fixture("malformed-bypass-attempts.json", {
            "attempts": [{"eventId": "missing-required-fields"}],
        })
        cases = (
            ("invalid-correlation", "verification-level", None, "gate-bypass-correlation"),
            ("inapplicable-entry-point", "api-smoke", "issue-10", "gate-bypass-inapplicable"),
        )

        for case, entry_point, task_key, gate_invocation_id in cases:
            with self.subTest(case=case):
                result, status = self.helper.verification_gate(
                    self.root,
                    "documentation-only",
                    entry_point,
                    task_key=task_key,
                    gate_invocation_id=gate_invocation_id,
                    bypass_attempts_ref=malformed_bypass,
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "FAIL", "VERIFICATION_GATE_FAIL", 1,
                ))
                native = self.native_check(result)
                self.assertEqual((native["rawResult"], native["mappedResult"], native["reason"]), (
                    "FAIL", "FAIL", "NATIVE_BYPASS_CONTRACT_INVALID",
                ))

    def test_early_native_blocked_preserves_blocking_for_correlation_and_applicability_returns(self):
        malformed_snapshot = self.write_temp_snapshot([])
        cases = (
            ("invalid-correlation", "verification-level", None, "gate-snapshot-correlation"),
            ("inapplicable-entry-point", "api-smoke", "issue-10", "gate-snapshot-inapplicable"),
        )

        for case, entry_point, task_key, gate_invocation_id in cases:
            with self.subTest(case=case):
                result, status = self.helper.verification_gate(
                    self.root,
                    "documentation-only",
                    entry_point,
                    task_key=task_key,
                    gate_invocation_id=gate_invocation_id,
                    runtime_snapshot_ref=malformed_snapshot,
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "BLOCKED", "VERIFICATION_GATE_BLOCKED", 2,
                ))
                self.assertEqual(self.native_check(result)["reason"], "NATIVE_ADAPTER_EVALUATION_INVALID")

    def test_early_native_not_configured_preserves_blocking_for_inapplicable_entry_point(self):
        supported_root = self.copy_repository_fixture()
        supported_policy = self.supported_host_policy()
        supported_policy["supportedHosts"][0].update({
            "hostId": "codex-desktop",
            "minimumHostVersion": "1.0.0",
        })
        (supported_root / "ai" / "native-runtime-adapters.json").write_text(
            json.dumps(supported_policy), encoding="utf-8",
        )
        bypass_ref = "ai/fixtures/empty-bypass-attempts.json"
        (supported_root / bypass_ref).write_text(json.dumps({"attempts": []}), encoding="utf-8")

        result, status = self.helper.verification_gate(
            supported_root,
            "documentation-only",
            "api-smoke",
            task_key="issue-10",
            gate_invocation_id="gate-not-configured",
            bypass_attempts_ref=bypass_ref,
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "VERIFICATION_GATE_BLOCKED", 2,
        ))
        native = self.native_check(result)
        self.assertEqual((native["rawResult"], native["mappedResult"]), (
            "NOT_CONFIGURED", "BLOCKED",
        ))

    def test_early_native_not_applicable_preserves_inapplicable_entry_point_result(self):
        snapshot_ref = self.write_temp_snapshot({
            "producerId": "codex-native-adapter",
            "surfaces": [],
        })

        result, status = self.helper.verification_gate(
            self.root,
            "documentation-only",
            "api-smoke",
            task_key="issue-10",
            gate_invocation_id="gate-unsupported",
            runtime_snapshot_ref=snapshot_ref,
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "NOT_APPLICABLE", "ENTRY_POINT_NOT_APPLICABLE", 6,
        ))

    def test_verification_gate_evaluates_explicit_native_inputs_once_before_check_loop(self):
        snapshot_ref = self.write_temp_snapshot({
            "producerId": "codex-native-adapter",
            "surfaces": [],
        })
        bypass_ref = self.write_attempts([])
        original_leaf = self.helper.native_adapter_phase2c_leaf
        calls = []

        def counted_leaf(*args, **kwargs):
            calls.append((args[3:], kwargs))
            return original_leaf(*args, **kwargs)

        self.helper.native_adapter_phase2c_leaf = counted_leaf
        self.addCleanup(setattr, self.helper, "native_adapter_phase2c_leaf", original_leaf)

        result, status = self.helper.verification_gate(
            self.root,
            "documentation-only",
            "verification-level",
            task_key="issue-10",
            gate_invocation_id="gate-read-once",
            runtime_snapshot_ref=snapshot_ref,
            bypass_attempts_ref=bypass_ref,
        )

        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(calls, [((snapshot_ref, bypass_ref), {})])

    def test_verification_gate_evaluates_native_leaf_once_without_optional_inputs_before_inapplicability(self):
        supported_root = self.copy_repository_fixture()
        supported_policy = self.supported_host_policy()
        supported_policy["supportedHosts"][0].update({
            "hostId": "codex-desktop",
            "minimumHostVersion": "1.0.0",
        })
        (supported_root / "ai" / "native-runtime-adapters.json").write_text(
            json.dumps(supported_policy), encoding="utf-8",
        )
        original_leaf = self.helper.native_adapter_phase2c_leaf
        calls = []

        def counted_leaf(*args, **kwargs):
            calls.append((args[0], args[3:], kwargs))
            return original_leaf(*args, **kwargs)

        self.helper.native_adapter_phase2c_leaf = counted_leaf
        self.addCleanup(setattr, self.helper, "native_adapter_phase2c_leaf", original_leaf)

        ordinary_result, ordinary_status = self.helper.verification_gate(
            self.root,
            "documentation-only",
            "verification-level",
            task_key="issue-10",
            gate_invocation_id="gate-unconditional-normal",
        )
        self.assertEqual((ordinary_result["result"], ordinary_status), ("BLOCKED", 2))

        unsupported_result, unsupported_status = self.helper.verification_gate(
            self.root,
            "documentation-only",
            "api-smoke",
            task_key="issue-10",
            gate_invocation_id="gate-unconditional-unsupported",
        )
        self.assertEqual((unsupported_result["result"], unsupported_result["reason"], unsupported_status), (
            "NOT_APPLICABLE", "ENTRY_POINT_NOT_APPLICABLE", 6,
        ))
        self.assertEqual(self.native_check(unsupported_result)["reason"], "HOST_UNSUPPORTED")

        blocked_result, blocked_status = self.helper.verification_gate(
            supported_root,
            "documentation-only",
            "api-smoke",
            task_key="issue-10",
            gate_invocation_id="gate-unconditional-supported",
        )
        self.assertEqual((blocked_result["result"], blocked_result["reason"], blocked_status), (
            "BLOCKED", "VERIFICATION_GATE_BLOCKED", 2,
        ))
        self.assertEqual(self.native_check(blocked_result)["reason"], "NATIVE_ADAPTER_NOT_CONFIGURED")
        self.assertEqual(calls, [
            (self.root, (None, None), {}),
            (self.root, (None, None), {}),
            (supported_root, (None, None), {}),
        ])

    def test_native_adapter_phase2c_leaf_validates_correlation_fail_closed(self):
        invalid_vectors = ((None, "gate-1"), ("issue-10", None), ("", "gate-1"), ("issue-10", ""))
        for task_key, gate_invocation_id in invalid_vectors:
            with self.subTest(task_key=task_key, gate_invocation_id=gate_invocation_id):
                leaf = self.helper.native_adapter_phase2c_leaf(
                    self.root, task_key, gate_invocation_id,
                )
                self.assertEqual((leaf["checkId"], leaf["result"], leaf["reason"]), (
                    "native-runtime-adapter", "BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS",
                ))

                gate_result, gate_status = self.helper.verification_gate(
                    self.root,
                    "documentation-only",
                    "api-smoke",
                    task_key=task_key,
                    gate_invocation_id=gate_invocation_id,
                )
                self.assertEqual((gate_result["result"], gate_result["reason"], gate_status), (
                    "BLOCKED", "VERIFICATION_GATE_BLOCKED", 2,
                ))
                self.assertEqual(self.native_check(gate_result)["reason"], "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS")

    def test_verification_cli_accepts_only_live_native_adapter_inputs(self):
        completed = self.run_verification_gate_cli_subprocess(
            "--repository-root", str(REPOSITORY_ROOT),
            "--change-type", "documentation-only",
            "--entry-point", "verification-level",
            "--task-key", "issue-10",
            "--gate-invocation-id", "gate-cli",
            "--native-adapter-result", "ai/fixtures/fake-native-adapter-result.json",
            "--output", "-",
        )
        self.assertEqual(completed.returncode, 4, completed.stderr + completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual((result["result"], result["reason"]), (
            "POLICY_VIOLATION", "INVALID_VERIFICATION_GATE_ARGUMENTS",
        ))

    def test_repository_and_native_boundaries_are_documented(self):
        policy_docs = (
            "AGENTS.md",
            "ai/document-routing.md",
            "ai/verification-gates.md",
            "ai/cache-policy.md",
            "ai/tool-call-policy.md",
            "ai/agent-handoff.md",
        )
        text = "\n".join(
            (REPOSITORY_ROOT / path).read_text(encoding="utf-8")
            for path in policy_docs
        )
        for phrase in (
            "only supported product-command path",
            "UNSUPPORTED",
            "Phase 3B",
            "INTEGRITY_ONLY",
            "unqualified overall DONE",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, text)

    def test_native_policy_docs_define_signed_trust_and_bypass_lifecycle(self):
        document = (REPOSITORY_ROOT / "ai/native-runtime-adapters.md").read_text(encoding="utf-8")
        for phrase in (
            "hostVersion: null",
            "versionProvenance: UNPROBED",
            "Claimed And Trusted Status",
            "ai/schemas/native-runtime-snapshot.schema.json",
            "RFC 8785-compatible restricted subset",
            '{"a":{"k":"v"},"z":["ASCII",true,null,7]}',
            "cryptography.hazmat",
            "300 seconds",
            "gateInvocationId",
            "resolutionEventIds",
            "DETECTED",
            "RESOLVED",
            "scripts/ai/command-runner.sh",
            "ai/verification-gates.md",
            "Phase 3B",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, document)

    def test_unsupported_host_maps_to_explicit_not_applicable_leaf(self):
        result, status = self.helper.native_adapter_gate(self.root, "issue-10", "gate-1")
        self.assertEqual((result["result"], status), ("UNSUPPORTED", 6))
        self.assertEqual(result["data"]["phase2CLeafResult"], "NOT_APPLICABLE")
        self.assertFalse((self.root / ".ai-runs").exists())

    def test_canonical_empty_supported_hosts_ignores_snapshot_promotion(self):
        snapshot = self.write_temp_snapshot({
            "producerId": "fixture",
            "surfaces": [],
        })
        result, status = self.helper.native_adapter_gate(self.root, "issue-10", "gate-2", snapshot)
        self.assertEqual((result["result"], status), ("UNSUPPORTED", 6))
        self.assertEqual((result["reason"], result["phase2cLeafResult"]), (
            "HOST_UNSUPPORTED", "NOT_APPLICABLE",
        ))

    def test_canonical_empty_supported_hosts_accepts_unsigned_minimum_snapshot_without_promotion(self):
        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            self.write_temp_snapshot({"producerId": "fixture", "surfaces": []}),
        )
        self.assertEqual((result["result"], result["reason"], status), ("UNSUPPORTED", "HOST_UNSUPPORTED", 6))
        self.assertEqual(result["phase2cLeafResult"], "NOT_APPLICABLE")

    def test_canonical_empty_supported_hosts_block_malformed_unsigned_snapshot(self):
        invalid_snapshots = (
            {},
            {"producerId": "", "surfaces": []},
            {"producerId": "fixture"},
            {"producerId": [], "surfaces": []},
            {"producerId": "fixture", "surfaces": {}},
            {"producerId": "fixture", "surfaces": [None]},
            {"producerId": "fixture", "surfaces": ["COMMAND"]},
            {"producerId": "fixture", "surfaces": [], "fresh": False},
        )
        for snapshot in invalid_snapshots:
            with self.subTest(snapshot=snapshot):
                result, status = self.helper.native_adapter_gate(
                    self.root, "issue-10", "gate-1", self.write_temp_snapshot(snapshot),
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "BLOCKED", "NATIVE_ADAPTER_SNAPSHOT_INVALID", 2,
                ))

    def test_invalid_runtime_snapshot_reference_blocks_before_unsupported_host_fallback(self):
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", runtime_snapshot_ref="ai/runtime-snapshot.json",
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))

        malformed = self.write_fixture("runtime-snapshot.json", [])
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", runtime_snapshot_ref=malformed,
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))

    def test_native_adapter_gate_rejects_empty_contract_identifiers(self):
        for task_key, gate_invocation_id in (("", "gate-1"), ("issue-10", "")):
            with self.subTest(task_key=task_key, gate_invocation_id=gate_invocation_id):
                result, status = self.helper.native_adapter_gate(self.root, task_key, gate_invocation_id)
                self.assertEqual((result["result"], result["reason"], status), (
                    "BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS", 2,
                ))

    def test_enforced_bypass_allowed_for_audit_is_a_failure_before_unsupported_host_fallback(self):
        attempt = self.valid_attempt(decision="ALLOWED_AUDIT_ONLY")
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=self.write_attempts([attempt]),
        )
        self.assertEqual((result["result"], status), ("FAIL", 1))

    def test_unresolved_bypass_and_redaction_uncertainty_block_completion(self):
        attempts = self.write_attempts([self.valid_attempt(lifecycle="DETECTED", gateInvocationId="gate-3")])
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-3", bypass_attempts_ref=attempts,
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))

        uncertain = self.valid_attempt(
            lifecycle="RESOLVED",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
            reasonCode="REDACTION_UNCERTAIN",
            gateInvocationId="gate-3",
        )
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-3", bypass_attempts_ref=self.write_attempts([uncertain]),
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))

    def test_bypass_attempts_fail_closed_for_invalid_correlation_and_redaction_contracts(self):
        cases = {
            "wrong-task": self.valid_attempt(taskKey="issue-else"),
            "wrong-gate": self.valid_attempt(
                gateInvocationId="different-gate",
                lifecycle="RESOLVED",
                resolvedAt="2026-07-13T01:01:00Z",
                resolutionReason="REMEDIATED",
            ),
            "malformed": {"eventId": "missing-required-fields"},
            "raw-secret": dict(self.valid_attempt(), payload="secret"),
            "byte-bound": self.valid_attempt(summary={
                "target": {
                    "classification": "REPOSITORY_PATH",
                    "repositoryPath": "\uac00" * 200,
                },
                "argumentSummary": {
                    "classification": "NONE",
                    "count": 0,
                    "sha256": "a" * 64,
                },
                "querySummary": {"classification": "NONE"},
                "toolPayloadSummary": {"classification": "NONE"},
            }),
            "scalar-bound": self.valid_attempt(summary={
                "target": {
                    "classification": "REPOSITORY_PATH",
                    "repositoryPath": "a" * 513,
                },
                "argumentSummary": {
                    "classification": "NONE",
                    "count": 0,
                    "sha256": "a" * 64,
                },
                "querySummary": {"classification": "NONE"},
                "toolPayloadSummary": {"classification": "NONE"},
            }),
        }
        for name, attempt in cases.items():
            with self.subTest(name=name):
                result, status = self.helper.native_adapter_gate(
                    self.root, "issue-10", "gate-1", bypass_attempts_ref=self.write_attempts([attempt]),
                )
                self.assertEqual((result["result"], status), ("FAIL", 1))

    def test_bypass_attempts_reject_secret_markers_in_all_user_controlled_string_fields(self):
        cases = (
            ("attemptId", "Authorization", "issue-10", "gate-1"),
            ("eventId", "Cookie", "issue-10", "gate-1"),
            ("hostId", "Authorization", "issue-10", "gate-1"),
            ("reasonCode", "Cookie", "issue-10", "gate-1"),
            ("taskKey", "Authorization", "Authorization", "gate-1"),
            ("gateInvocationId", "Cookie", "issue-10", "Cookie"),
            ("runId", "Authorization: Bearer opaque", "issue-10", "gate-1"),
            ("deduplicationKey", "Cookie: session=opaque", "issue-10", "gate-1"),
        )
        for field, value, task_key, gate_invocation_id in cases:
            with self.subTest(field=field):
                attempt = self.valid_attempt(**{field: value})
                result, status = self.helper.native_adapter_gate(
                    self.root,
                    task_key,
                    gate_invocation_id,
                    bypass_attempts_ref=self.write_attempts([attempt]),
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "FAIL", "NATIVE_BYPASS_CONTRACT_INVALID", 1,
                ))

        attempt = self.valid_attempt(summary={
            "target": {
                "classification": "REPOSITORY_PATH",
                "repositoryPath": "docs/Cookie/session.txt",
            },
            "argumentSummary": {
                "classification": "STRUCTURAL_PLACEHOLDERS",
                "count": 1,
                "sha256": "a" * 64,
            },
            "querySummary": {"classification": "NONE"},
            "toolPayloadSummary": {"classification": "NONE"},
        })
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=self.write_attempts([attempt]),
        )
        self.assertEqual((result["result"], result["reason"], status), (
            "FAIL", "NATIVE_BYPASS_CONTRACT_INVALID", 1,
        ))

    def test_bypass_summary_rejects_secret_bearing_strings(self):
        secret_summaries = (
            "Authorization: Bearer abc",
            "Cookie: session=abc",
            "cookie=session=abc",
            "cookies=session=abc",
            "password=abc",
            "password: abc",
            "secret: abc",
            "token: abc",
            "api_key: abc",
            "credential: abc",
            "Authorization: Basic dXNlcjpwYXNz",
            "Basic dXNlcjpwYXNz",
            "Basic YWxpY2U6cA==",
            "Basic YWxpY2U6cA",
            "Bearer ya29.a0AfH6SMB-credential",
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signature",
            "-----BEGIN PRIVATE KEY-----",
            "raw request body: {\"password\": \"abc\"}",
            "request body: {\"password\": \"abc\"}",
            "raw auth: alice:abc",
            "raw authorization value",
            "raw cookie value",
            "raw cookies value",
            "raw body: {\"password\": \"abc\"}",
            "raw bodies: [{\"password\": \"abc\"}]",
            "raw payload: token=abc",
            "raw credentials: alice:abc",
            "raw query: key=value",
            "raw argv: --flag value",
            "raw env: NAME=value",
        )
        for summary in secret_summaries:
            with self.subTest(summary=summary):
                self.assertTrue(self.helper.native_summary_has_secret(summary))

    def test_bypass_summary_rejects_review_raw_content_label_examples(self):
        review_examples = (
            '{"authorization":"Bearer opaque"}',
            '"authorization" : "Bearer opaque"',
            '"cookie" = "session=opaque"',
            '"cookies"\t"session=opaque"',
            "authorization\topaque",
            "cookie opaque",
            "cookies\nopaque",
        )

        for summary in review_examples:
            with self.subTest(summary=summary):
                self.assertTrue(self.helper.native_summary_has_secret(summary))

    def test_bypass_summary_rejects_any_authorization_header_marker_or_assignment(self):
        for summary in (
            "Authorization: Digest abc123",
            "authorization: Basic",
            "AUTHORIZATION: Bearer",
            "Authorization: Arbitrary opaque-value",
            "authorization=opaque-value",
            "Authorization = bearer token documentation",
        ):
            with self.subTest(summary=summary):
                self.assertTrue(self.helper.native_summary_has_secret(summary))

    def test_bypass_summary_rejects_bearer_credentials_regardless_of_trailing_non_whitespace(self):
        for suffix in ("", ".", ")", "]", ":", "!", "?", ",", ";", '"', "'", "}", "/"):
            with self.subTest(suffix=suffix):
                self.assertTrue(self.helper.native_summary_has_secret(f"Bearer opaqueToken{suffix}"))

    def test_bypass_summary_rejects_bearer_credentials_with_regex_whitespace(self):
        for separator in ("\u00a0", "\n", "\r\n"):
            with self.subTest(separator=repr(separator)):
                self.assertTrue(self.helper.native_summary_has_secret(f"Bearer{separator}opaqueToken"))

    def test_bypass_summary_allows_bearer_token_documentation(self):
        self.assertFalse(self.helper.native_summary_has_secret("bearer token documentation"))
        self.assertTrue(self.helper.native_summary_has_secret("bearer token documentation extra"))
        self.assertTrue(self.helper.native_summary_has_secret("Authorization: bearer token documentation"))

    def test_bypass_summary_allows_only_normalized_ascii_bearer_token_documentation(self):
        self.assertFalse(self.helper.native_summary_has_secret("Bearer Token Documentation"))
        for summary in ("bearer\ntoken documentation", "bearer\u00a0token documentation"):
            with self.subTest(summary=repr(summary)):
                self.assertTrue(self.helper.native_summary_has_secret(summary))

    def test_bypass_summary_rejects_basic_credentials_regardless_of_trailing_non_whitespace(self):
        for punctuation in (".", ")", "]", ":", "!", "?", ",", ";", '"', "'", "}", "/"):
            for credential in ("dXNlcjpwYXNz", "YWxpY2U6cA=="):
                with self.subTest(punctuation=punctuation, credential=credential):
                    self.assertTrue(self.helper.native_summary_has_secret(f"Basic {credential}{punctuation}"))

        for credential in ("dXNlcjpwYXNz", "YWxpY2U6cA=="):
            with self.subTest(credential=credential):
                self.assertTrue(self.helper.native_summary_has_secret(f"Basic {credential}"))
                self.assertTrue(self.helper.native_summary_has_secret(f"Basic {credential} followed"))

    def test_bypass_summary_rejects_basic_credentials_with_regex_whitespace(self):
        for separator in ("\n", "\r\n"):
            with self.subTest(separator=repr(separator)):
                self.assertTrue(self.helper.native_summary_has_secret(f"Basic{separator}dXNlcjpwYXNz"))

    def test_bypass_summary_allows_closed_non_secret_classifications(self):
        attempt = self.valid_attempt(
            lifecycle="RESOLVED",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
            summary={
                "target": {
                    "classification": "EXTERNAL_TARGET",
                    "redactedCategory": "OTHER_EXTERNAL_TARGET",
                    "sha256": "d" * 64,
                },
                "argumentSummary": {
                    "classification": "ALLOWLISTED_LITERALS",
                    "count": 2,
                    "sha256": "a" * 64,
                },
                "querySummary": {
                    "classification": "STRUCTURED_QUERY",
                    "sha256": "b" * 64,
                },
                "toolPayloadSummary": {
                    "classification": "OPAQUE_PAYLOAD",
                    "sha256": "c" * 64,
                },
            },
        )
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=self.write_attempts([attempt]),
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(result["reason"], "NATIVE_BYPASS_RESOLUTION_INVALID")

    def test_bypass_resolution_requires_prior_detection_and_blocks_without_signed_snapshot(self):
        prior_detected = self.valid_attempt(
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T00:59:00Z",
        )
        current_resolved = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-2",
            gateInvocationId="gate-1",
            lifecycle="RESOLVED",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
        )
        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            bypass_attempts_ref=self.write_attempts([prior_detected, current_resolved]),
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))

    def test_bypass_detection_from_the_same_gate_invocation_remains_unresolved(self):
        same_invocation_detection = self.valid_attempt(
            gateInvocationId="gate-1",
            observedAt="2026-07-13T00:59:00Z",
        )
        current_resolution = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-2",
            gateInvocationId="gate-1",
            lifecycle="RESOLVED",
            observedAt="2026-07-13T01:00:00Z",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
        )

        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            bypass_attempts_ref=self.write_attempts([same_invocation_detection, current_resolution]),
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "NATIVE_BYPASS_UNRESOLVED", 2,
        ))

    def test_mixed_resolution_times_in_one_deduplication_group_are_invalid(self):
        prior_detected = self.valid_attempt(
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T00:59:00Z",
        )
        valid_resolution = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-2",
            lifecycle="RESOLVED",
            observedAt="2026-07-13T01:01:00Z",
            resolvedAt="2026-07-13T01:01:01Z",
            resolutionReason="REMEDIATED",
        )
        invalid_resolution = self.valid_attempt(
            attemptId="attempt-3",
            eventId="event-3",
            lifecycle="RESOLVED",
            observedAt="2026-07-13T00:58:00Z",
            resolvedAt="2026-07-13T00:58:01Z",
            resolutionReason="REMEDIATED",
        )

        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            bypass_attempts_ref=self.write_attempts([prior_detected, valid_resolution, invalid_resolution]),
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "NATIVE_BYPASS_RESOLUTION_INVALID", 2,
        ))

    def test_later_unresolved_detection_wins_over_prior_resolution(self):
        prior_detected = self.valid_attempt(
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T00:59:00Z",
        )
        resolved = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-2",
            lifecycle="RESOLVED",
            observedAt="2026-07-13T01:01:00Z",
            resolvedAt="2026-07-13T01:01:01Z",
            resolutionReason="REMEDIATED",
        )
        later_detected = self.valid_attempt(
            attemptId="attempt-3",
            eventId="event-3",
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T01:02:00Z",
        )

        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            bypass_attempts_ref=self.write_attempts([prior_detected, resolved, later_detected]),
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "NATIVE_BYPASS_UNRESOLVED", 2,
        ))

    def test_current_detection_wins_over_resolution_in_the_same_deduplication_group(self):
        prior_detected = self.valid_attempt(
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T00:59:00Z",
        )
        current_resolved = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-2",
            lifecycle="RESOLVED",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
        )
        current_detected = self.valid_attempt(
            attemptId="attempt-3",
            eventId="event-3",
            observedAt="2026-07-13T01:02:00Z",
        )
        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            bypass_attempts_ref=self.write_attempts([prior_detected, current_resolved, current_detected]),
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(result["reason"], "NATIVE_BYPASS_UNRESOLVED")

        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=self.write_attempts([current_resolved]),
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))

        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=self.write_attempts([prior_detected]),
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))

    def test_current_detection_remains_unresolved_when_current_resolution_follows_it(self):
        prior_detected = self.valid_attempt(
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T00:58:00Z",
        )
        current_detected = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-2",
            observedAt="2026-07-13T00:59:00Z",
        )
        current_resolved = self.valid_attempt(
            attemptId="attempt-3",
            eventId="event-3",
            lifecycle="RESOLVED",
            observedAt="2026-07-13T01:00:00Z",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
        )

        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            bypass_attempts_ref=self.write_attempts([prior_detected, current_detected, current_resolved]),
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "NATIVE_BYPASS_UNRESOLVED", 2,
        ))

    def test_repeated_events_are_idempotent_and_dedup_groups_preserve_every_event(self):
        resolved = self.valid_attempt(
            lifecycle="RESOLVED",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
        )
        duplicate = dict(resolved)
        second = dict(resolved)
        second.update({"attemptId": "attempt-2", "eventId": "event-2"})
        attempts_ref = self.write_attempts([resolved, duplicate, second])
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=attempts_ref,
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        self.assertEqual(len(result["data"]["bypassAttemptRefs"]), 2)
        attempts = json.loads((self.root / attempts_ref).read_text(encoding="utf-8"))["attempts"]
        self.assertEqual([attempt["eventId"] for attempt in attempts], ["event-1", "event-1", "event-2"])
        self.assertEqual({attempt["deduplicationKey"] for attempt in attempts}, {"dedupe-1"})

    def test_command_file_read_intent_retains_command_surface(self):
        attempt = self.valid_attempt(
            lifecycle="RESOLVED",
            resolvedAt="2026-07-13T01:01:00Z",
            resolutionReason="REMEDIATED",
            commandIntent="FILE_READ",
            surface="COMMAND",
            operationType="FILE_READ",
        )
        attempts_ref = self.write_attempts([attempt])
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=attempts_ref,
        )
        self.assertEqual((result["result"], status), ("BLOCKED", 2))
        evaluated = json.loads((self.root / attempts_ref).read_text(encoding="utf-8"))["attempts"][0]
        self.assertEqual((evaluated["surface"], evaluated["commandIntent"]), ("COMMAND", "FILE_READ"))

    def test_supported_host_fixture_states_are_completion_blocking_and_never_pass(self):
        policy_ref = self.write_supported_policy()
        states = {
            "missing": None,
            "stale": {"fresh": False, "surfaces": self.supported_surfaces()},
            "bad-signature": {"signatureValid": False, "surfaces": self.supported_surfaces()},
            "callback-failure": {"signatureValid": True, "callbackStatus": "FAILED", "surfaces": self.supported_surfaces()},
            "audit-only": {"signatureValid": True, "callbackStatus": "OK", "fresh": True, "surfaces": [
                {"surface": surface, "status": "AUDIT_ONLY", "reasonCode": "AUDIT_ONLY_FIXTURE"}
                for surface in ("COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL")
            ]},
            "enforced-fixture": {"signatureValid": True, "callbackStatus": "OK", "fresh": True, "surfaces": [
                {"surface": surface, "status": "ENFORCED", "reasonCode": "FIXTURE_ONLY"}
                for surface in ("COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL")
            ]},
        }
        for name, snapshot in states.items():
            with self.subTest(name=name):
                result, status = self.helper.native_adapter_gate(
                    self.root,
                    "issue-10",
                    "gate-1",
                    self.write_temp_snapshot(snapshot) if snapshot is not None else None,
                    policy_ref=policy_ref,
                )
                self.assertIn((result["result"], status), (("NOT_CONFIGURED", 3), ("BLOCKED", 2)))
                self.assertNotEqual(result["result"], "PASS")

    def test_prerelease_host_version_does_not_satisfy_release_minimum(self):
        policy = self.supported_host_policy()
        policy["currentHost"]["hostVersion"] = "1.0.0-beta"
        policy["supportedHosts"][0]["hostId"] = "codex-desktop"
        policy["supportedHosts"][0]["minimumHostVersion"] = "1.0.0"
        policy_ref = self.write_fixture("prerelease-native-runtime-adapters.json", policy)
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", policy_ref=policy_ref,
        )
        self.assertEqual((result["result"], status), ("UNSUPPORTED", 6))

    def test_native_semver_comparator_rejects_malformed_inputs_and_accepts_prerelease_build(self):
        self.assertEqual(
            self.helper.native_semver_key("1.0.0-rc.1+build.5"),
            ((1, 0, 0), 0, ((1, "rc"), (0, 1))),
        )
        for version in ("01.0.0", "1.01.0", "1.0.01", "1.0.0-01", "1.0.0-rc..1", "1.0.0-", "1.0.0\n"):
            with self.subTest(version=version):
                with self.assertRaises(ValueError):
                    self.helper.native_semver_key(version)

    def test_malformed_policy_versions_block_before_not_configured_evaluation(self):
        invalid_versions = ("01.0.0", "1.01.0", "1.0.01", "1.0.0-01", "1.0.0-rc..1", "1.0.0-")
        for path in (("currentHost", "hostVersion"), ("supportedHosts", 0, "minimumHostVersion")):
            for version in invalid_versions:
                with self.subTest(path=path, version=version):
                    policy = self.supported_host_policy()
                    policy["supportedHosts"][0]["hostId"] = policy["currentHost"]["hostId"]
                    target = policy
                    for segment in path[:-1]:
                        target = target[segment]
                    target[path[-1]] = version
                    result, status = self.helper.native_adapter_gate(
                        self.root,
                        "issue-10",
                        "gate-1",
                        policy_ref=self.write_fixture("malformed-native-runtime-adapters.json", policy),
                    )
                    self.assertEqual((result["result"], result["reason"], status), (
                        "BLOCKED", "NATIVE_ADAPTER_EVALUATION_INVALID", 2,
                    ))

    def test_native_adapter_gate_shell_wrapper_is_static_and_fixed_argument(self):
        shell = REPOSITORY_ROOT / "scripts" / "ai" / "native-adapter-gate.sh"
        bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if not bash.is_file():
            bash = Path("bash")
        completed = subprocess.run(
            [
                str(bash), str(shell), "--task-key", "issue-10", "--gate-invocation-id", "gate-1", "--output", "-",
            ],
            cwd=str(REPOSITORY_ROOT),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(completed.returncode, 6, completed.stderr + completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual((result["operation"], result["result"]), ("NATIVE_ADAPTER_GATE", "UNSUPPORTED"))
        self.assertFalse((REPOSITORY_ROOT / ".ai-runs").exists())

    def test_native_adapter_shell_fallback_envelopes_match_result_schema(self):
        shell = (REPOSITORY_ROOT / "scripts/ai/native-adapter-gate.sh").read_text(encoding="utf-8")
        payloads = re.findall(r"^\s*printf '%s\\n' '(\{.*\})'$", shell, flags=re.MULTILINE)
        self.assertEqual(len(payloads), 2)
        for payload in payloads:
            with self.subTest(payload=payload):
                self.assert_valid("native-adapter-result", json.loads(payload))

    def test_native_adapter_shell_wrapper_anchors_repository_from_another_directory(self):
        shell = REPOSITORY_ROOT / "scripts" / "ai" / "native-adapter-gate.sh"
        bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if not bash.is_file():
            bash = Path("bash")
        other_repository = self.root / "other-repository"
        other_repository.mkdir()

        completed = subprocess.run(
            [
                str(bash), str(shell), "--task-key", "issue-10", "--gate-invocation-id", "gate-1", "--output", "-",
            ],
            cwd=str(other_repository),
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )

        self.assertEqual(completed.returncode, 6, completed.stderr + completed.stdout)
        result = json.loads(completed.stdout)
        self.assertEqual((result["operation"], result["result"]), ("NATIVE_ADAPTER_GATE", "UNSUPPORTED"))
        self.assertFalse((other_repository / ".ai-runs").exists())

    def test_native_adapter_cli_semantic_arguments_and_invalid_output_are_structured(self):
        invalid_cases = (
            ("--repository-root", ""),
            ("--task-key", ""),
            ("--gate-invocation-id", ""),
            ("--runtime-snapshot", ""),
            ("--bypass-attempts", ""),
            ("--output", ""),
            ("--output", "nested/result.json"),
        )
        for option, value in invalid_cases:
            with self.subTest(option=option):
                arguments = [
                    "--repository-root", str(REPOSITORY_ROOT),
                    "--task-key", "issue-10",
                    "--gate-invocation-id", "gate-1",
                    "--output", "-",
                ]
                if option in arguments:
                    arguments[arguments.index(option) + 1] = value
                else:
                    arguments.extend([option, value])
                completed = self.run_native_adapter_cli_subprocess(*arguments)
                self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
                self.assertNotIn("Traceback", completed.stderr)
                result = json.loads(completed.stdout)
                expected_reason = (
                    "NATIVE_ADAPTER_OUTPUT_PATH_INVALID"
                    if option == "--output" else "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS"
                )
                self.assertEqual((result["result"], result["reason"]), ("BLOCKED", expected_reason))

    def test_native_adapter_cli_rejects_empty_repository_root_before_resolving_from_repo_cwd(self):
        completed = self.run_native_adapter_cli_subprocess(
            "--repository-root", "",
            "--task-key", "issue-10",
            "--gate-invocation-id", "gate-1",
            "--output", "-",
        )

        self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
        self.assertNotIn("Traceback", completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual((result["result"], result["reason"]), (
            "BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS",
        ))
        self.assert_valid("native-adapter-result", result)

    def test_bypass_reference_faults_block_before_loaded_record_validation(self):
        invalid_json_ref = "ai/fixtures/invalid-bypass-attempts.json"
        (self.root / invalid_json_ref).write_text("{", encoding="utf-8")
        unreadable_ref = "ai/fixtures/unreadable-bypass-attempts.json"
        (self.root / unreadable_ref).mkdir()
        references = ("", "ai/fixtures/missing-bypass-attempts.json", "../outside.json", invalid_json_ref, unreadable_ref)

        for reference in references:
            with self.subTest(reference=reference):
                result, status = self.helper.native_adapter_gate(
                    self.root, "issue-10", "gate-1", bypass_attempts_ref=reference,
                )
                self.assertEqual((result["result"], result["reason"], status), (
                    "BLOCKED", "NATIVE_BYPASS_REFERENCE_INVALID", 2,
                ))

    def test_malformed_loaded_bypass_records_remain_contract_failures(self):
        result, status = self.helper.native_adapter_gate(
            self.root, "issue-10", "gate-1", bypass_attempts_ref=self.write_attempts([{"eventId": "missing-fields"}]),
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "FAIL", "NATIVE_BYPASS_CONTRACT_INVALID", 1,
        ))

    def test_bypass_lifecycle_compares_equivalent_fractional_second_instants_as_equal(self):
        prior_detected = self.valid_attempt(
            gateInvocationId="gate-prior",
            observedAt="2026-07-13T01:00:00.100Z",
        )
        current_resolved = self.valid_attempt(
            attemptId="attempt-2",
            eventId="event-2",
            lifecycle="RESOLVED",
            observedAt="2026-07-13T01:00:00.1Z",
            resolvedAt="2026-07-13T01:00:01Z",
            resolutionReason="REMEDIATED",
        )

        result, status = self.helper.native_adapter_gate(
            self.root,
            "issue-10",
            "gate-1",
            bypass_attempts_ref=self.write_attempts([prior_detected, current_resolved]),
        )

        self.assertEqual((result["result"], result["reason"], status), (
            "BLOCKED", "NATIVE_BYPASS_RESOLUTION_INVALID", 2,
        ))

    def test_native_adapter_shell_wrapper_preserves_explicit_empty_optional_arguments(self):
        shell = REPOSITORY_ROOT / "scripts" / "ai" / "native-adapter-gate.sh"
        bash = Path(r"C:\Program Files\Git\bin\bash.exe")
        if not bash.is_file():
            bash = Path("bash")
        for option in ("--runtime-snapshot", "--bypass-attempts"):
            with self.subTest(option=option):
                completed = subprocess.run(
                    [
                        str(bash), str(shell), "--task-key", "issue-10", "--gate-invocation-id", "gate-1",
                        option, "", "--output", "-",
                    ],
                    cwd=str(REPOSITORY_ROOT),
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                self.assertEqual(completed.returncode, 2, completed.stderr + completed.stdout)
                result = json.loads(completed.stdout)
                self.assertEqual((result["result"], result["reason"]), (
                    "BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS",
                ))


if __name__ == "__main__":
    unittest.main()


class Phase3BCIGatesDurableEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.helper = load_helper()
        self.root = REPOSITORY_ROOT

    def test_phase_3b_schemas_policy_and_work_log_are_issue_backed(self):
        self.assertIn("ci-capability-status", self.helper.SCHEMA_NAMES)
        self.assertIn("ci-gate-result", self.helper.SCHEMA_NAMES)
        status = self.helper.validate_repository_instance(self.root, "ai/ci-capability-status.json")
        self.assertEqual(status["phase"], "3B")
        self.assertEqual(status["issue"]["number"], 12)
        self.assertEqual(status["pullRequest"]["phase3AMerged"], True)
        self.assertEqual(status["currentCi"]["provider"], "github-actions")
        self.assertEqual(status["currentCi"]["nativeAdapterInstallation"]["status"], "NOT_CONFIGURED")
        self.assertEqual(status["currentCi"]["durableEvidence"]["status"], "NOT_CONFIGURED")
        self.assertEqual(status["currentCi"]["remoteRunner"]["completionBlocking"], True)
        self.assertEqual(status["phase2cLink"]["nativeAdapterCheckId"], "native-runtime-adapter")
        summary = (self.root / "ai/work-logs/issue-12/README.md").read_text(encoding="utf-8")
        self.assertIn("https://github.com/116Lv/sparta-ch6-advanced/issues/12", summary)

    def test_ci_gate_is_fail_closed_without_durable_github_actions_evidence(self):
        result, status = self.helper.ci_evidence_gate(self.root, "issue-12", "gate-ci")
        self.assertEqual((result["result"], result["phase2cLeafResult"], status), ("NOT_CONFIGURED", "BLOCKED", 3))
        self.assertEqual(result["reason"], "CI_EVIDENCE_NOT_AVAILABLE")
        self.assertEqual(result["data"]["requiredCheck"], "phase-3b-ci-gates")
        self.assertEqual(result["data"]["durableEvidence"]["retentionDays"], 90)
        self.assertEqual(result["data"]["nativeAdapterLeaf"]["currentHostResult"], "UNSUPPORTED")
        self.assertFalse((self.root / ".ai-runs").exists())

    def test_ci_evidence_available_requires_retained_artifact_identity(self):
        status = self.helper.validate_repository_instance(self.root, "ai/ci-capability-status.json")
        status["currentCi"]["nativeAdapterInstallation"] = {
            "status": "INSTALLED",
            "reasonCode": "REMOTE_NATIVE_ADAPTER_INSTALLED",
        }
        status["currentCi"]["durableEvidence"]["status"] = "AVAILABLE"
        status["currentCi"]["durableEvidence"]["reasonCode"] = "DURABLE_EVIDENCE_AVAILABLE"
        status["currentCi"]["remoteRunner"] = {
            "status": "PASS",
            "completionBlocking": False,
            "reasonCode": "REMOTE_RUNNER_ATTESTED",
        }
        status_path = self.root / "phase3b-ci-status-underbound.tmp.json"
        try:
            status_path.write_text(json.dumps(status, sort_keys=True), encoding="utf-8")
            result, exit_status = self.helper.ci_evidence_gate(
                self.root, "issue-12", "gate-available", "phase3b-ci-status-underbound.tmp.json",
            )
            self.assertEqual((result["result"], result["reason"], exit_status), (
                "BLOCKED", "CI_EVIDENCE_EVALUATION_INVALID", 2,
            ))
        finally:
            status_path.unlink(missing_ok=True)
    def test_ci_evidence_available_requires_retained_artifact_file(self):
        status = self.helper.validate_repository_instance(self.root, "ai/ci-capability-status.json")
        status["currentCi"]["nativeAdapterInstallation"] = {
            "status": "INSTALLED",
            "reasonCode": "REMOTE_NATIVE_ADAPTER_INSTALLED",
        }
        status["currentCi"]["durableEvidence"].update({
            "status": "AVAILABLE",
            "reasonCode": "DURABLE_EVIDENCE_AVAILABLE",
            "artifactRefs": ["ai/evidence/missing-phase3b-ci-artifact.json"],
            "retainedRun": {
                "repository": "116Lv/sparta-ch6-advanced",
                "commitSha": "400c00f35f9d21cbeec44b0f40f49dac564a4bb6",
                "workflowRunId": 1,
                "jobId": 1,
                "attempt": 1,
                "taskKey": "issue-12",
                "gateInvocationId": "gate-available",
                "nativeAdapterStatusDigest": "0000000000000000000000000000000000000000000000000000000000000000",
                "bypassEventSetSha256": "0000000000000000000000000000000000000000000000000000000000000000",
                "resolutionEventIds": [],
            },
        })
        status["currentCi"]["remoteRunner"] = {
            "status": "PASS",
            "completionBlocking": False,
            "reasonCode": "REMOTE_RUNNER_ATTESTED",
        }
        status_path = self.root / "phase3b-ci-status-missing-artifact.tmp.json"
        try:
            status_path.write_text(json.dumps(status, sort_keys=True), encoding="utf-8")
            result, exit_status = self.helper.ci_evidence_gate(
                self.root, "issue-12", "gate-available", "phase3b-ci-status-missing-artifact.tmp.json",
            )
            self.assertEqual((result["result"], result["reason"], exit_status), (
                "BLOCKED", "CI_DURABLE_EVIDENCE_ARTIFACT_MISSING", 2,
            ))
        finally:
            status_path.unlink(missing_ok=True)
    def test_ci_workflow_and_policy_docs_preserve_product_command_boundary(self):
        workflow = self.root / ".github/workflows/phase-3b-ci-gates.yml"
        self.assertTrue(workflow.is_file())
        workflow_text = workflow.read_text(encoding="utf-8")
        self.assertIn("scripts/ai/ci-evidence-gate.sh", workflow_text)
        self.assertNotIn("gradle", workflow_text.lower())
        self.assertNotIn("docker compose", workflow_text.lower())
        doc_text = "\n".join(
            (self.root / path).read_text(encoding="utf-8")
            for path in (
                "ai/ci-gates.md",
                "docs/superpowers/specs/2026-07-13-ai-workflow-phase-3b-ci-gates-durable-evidence-design.md",
            )
        )
        self.assertIn("repository gateway", doc_text)
        self.assertIn("cross-process challenge", doc_text)
        self.assertIn("bypass event", doc_text)
        self.assertIn("registry `VERIFIED`", doc_text)

    def test_ci_workflow_provisions_contract_runtime_and_retains_failure_evidence(self):
        workflow_text = (
            self.root / ".github/workflows/phase-3b-ci-gates.yml"
        ).read_text(encoding="utf-8")
        packages = "jsonschema==4.25.1 cryptography==45.0.5"
        setup_install = f"python -m pip install {packages}"
        contract_install_command = (
            f"/usr/bin/python3 -m pip install --break-system-packages {packages}"
        )
        self.assertIn(setup_install, workflow_text)
        self.assertIn(contract_install_command, workflow_text)
        self.assertEqual(
            workflow_text.count("assert version('jsonschema') == '4.25.1'"), 2,
        )
        self.assertEqual(
            workflow_text.count("assert version('cryptography') == '45.0.5'"), 2,
        )
        contract_install = workflow_text.index(contract_install_command)
        contract_run = workflow_text.index("bash scripts/ai/tests/run-contract-tests.sh")
        self.assertLess(contract_install, contract_run)
        self.assertIn("> phase3b-ci-gate-fallback.json", workflow_text)
        self.assertIn("if: ${{ !cancelled() }}\n        shell: bash", workflow_text)
        self.assertIn("hashFiles('phase3b-ci-gate-result.json') != ''", workflow_text)
        self.assertIn("hashFiles('ai/ci-capability-status.json') != ''", workflow_text)
        self.assertIn("if-no-files-found: error", workflow_text)
