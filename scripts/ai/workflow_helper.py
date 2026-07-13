#!/usr/bin/env python3
"""Phase 1B helper owns closed gateway validation and POSIX-only command orchestration."""

import argparse
import base64
import codecs
from collections.abc import Mapping, Sequence
import ctypes
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from dataclasses import dataclass
from decimal import Decimal
import datetime as dt
import errno
import hashlib
from importlib.metadata import version as package_version
import json
import os
from pathlib import Path
import re
import selectors
import shutil
import signal
import stat
import struct
import subprocess
import sys
import tempfile
import time
import traceback
from types import MappingProxyType
import uuid

try:
    import jsonschema
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError:
    jsonschema = None

try:
    from cryptography.exceptions import InvalidSignature as Ed25519InvalidSignature
    from cryptography.exceptions import UnsupportedAlgorithm as Ed25519UnsupportedAlgorithm
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
except ImportError:
    Ed25519InvalidSignature = None
    Ed25519UnsupportedAlgorithm = None
    Ed25519PublicKey = None


TRANSACTION_MAX_RECENT_SECONDS = 300
RUN_IDENTIFIER_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
RUN_TASK_KEY_MAX_LENGTH = 255
RUN_LOCK_MAX_RECENT_SECONDS = 300
CHILD_ENVIRONMENT_ALLOWLIST = (
    "PATH", "JAVA_HOME", "GRADLE_USER_HOME", "HOME", "TMPDIR", "LANG", "LC_ALL",
)
INPUT_GLOB_CHARACTERS = frozenset("*?[]{}")
RERUN_REASON_MAX_BYTES = 4096
RERUN_REASON_MAX_SCALARS = 1024
EXECUTION_TIMEOUT_SECONDS = 3600
PROCESS_GROUP_GRACE_SECONDS = 5
DRAIN_COMPLETION_SECONDS = 5
RECOVERY_QUARANTINE_PATTERN = re.compile(
    r"^lock-recovery-[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
)
INITIALIZATION_QUARANTINE_PATTERN = re.compile(
    r"^lock-initialization-quarantine-[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"
)
TRANSACTION_FILES = {
    "ai/evidence/local-helper-runtime.json": "local-helper-runtime.json.backup",
    "ai/project-state.json": "project-state.json.backup",
    "ai/project-state.md": "project-state.md.backup",
}
DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS = {
    errno.EINVAL,
    getattr(errno, "ENOTSUP", errno.EINVAL),
    getattr(errno, "EOPNOTSUPP", errno.EINVAL),
}
OWNER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["pid", "createdAt"],
    "properties": {
        "pid": {"type": "integer", "minimum": 1},
        "createdAt": {"type": "string", "format": "date-time"},
    },
}
RUN_LOCK_OWNER_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["ownerId", "runId", "pid", "acquiredAt"],
    "properties": {
        "ownerId": {"type": "string", "pattern": "^[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89ab][a-f0-9]{3}-[a-f0-9]{12}$"},
        "runId": {"type": "string", "pattern": "^[A-Za-z0-9][A-Za-z0-9._-]*$"},
        "pid": {"type": "integer", "minimum": 1},
        "acquiredAt": {
            "type": "string",
            "format": "date-time",
            "pattern": "^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\\.[0-9]+)?Z$",
        },
    },
}
DRAFT_2020_12_URI = "https://json-schema.org/draft/2020-12/schema"
GATEWAY_OPERATIONS = ("PREFLIGHT", "RESOLVE", "RUN_START", "PRE_COMMAND", "POST_COMMAND", "PRE_DONE_CLAIM")
SCHEMA_NAMES = (
    "agent-handoff",
    "approval-record",
    "artifact-manifest",
    "command-registry",
    "command-result",
    "ci-capability-status",
    "ci-gate-result",
    "context-map",
    "done-claim",
    "gateway-result",
    "helper-runtime-evidence",
    "host-native-trust",
    "native-adapter-result",
    "native-bypass-attempt",
    "native-runtime-adapters",
    "native-runtime-snapshot",
    "policy-violation",
    "project-state",
    "process-attempt",
    "repo-intake-result",
    "run",
    "run-session",
    "skill-catalog",
    "verification-gate-result",
    "verification-leaf-result",
    "verification-policy",
    "workflow-cache",
)
SCHEMA_ALLOWLIST = {
    instance_schema: {
        "path": f"ai/schemas/{schema_name}.schema.json",
        "id": f"urn:sparta-ch6-advanced:ai-workflow:schema:{schema_name}:v1",
    }
    for schema_name in SCHEMA_NAMES
    for instance_schema in (
        f"ai/schemas/{schema_name}.schema.json",
        f"./schemas/{schema_name}.schema.json",
    )
}
APPROVED_SCHEMA_PATHS = {
    profile["path"]: profile
    for profile in SCHEMA_ALLOWLIST.values()
}
JOURNAL_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": False,
    "required": ["version", "stage", "owner", "files"],
    "properties": {
        "version": {"const": 1},
        "stage": {"const": "PREPARED"},
        "owner": OWNER_SCHEMA,
        "files": {
            "type": "array",
            "minItems": 3,
            "maxItems": 3,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["target", "backup", "existed", "previousSha256", "intendedSha256"],
                "properties": {
                    "target": {"type": "string", "minLength": 1},
                    "backup": {"type": "string", "minLength": 1},
                    "existed": {"type": "boolean"},
                    "previousSha256": {
                        "type": ["string", "null"],
                        "pattern": "^[a-f0-9]{64}$",
                    },
                    "intendedSha256": {"type": "string", "pattern": "^[a-f0-9]{64}$"},
                },
            },
        },
    },
}


class TransactionBlocked(Exception):
    pass


class InvalidTransaction(Exception):
    pass


class InvalidStateError(ValueError):
    result = "INVALID_STATE"

    def __init__(self, errors):
        self.errors = errors
        super().__init__(errors[0]["message"] if errors else "invalid workflow state")


class RegistryBlockedError(ValueError):
    result = "BLOCKED"

    def __init__(self, errors):
        self.errors = errors
        super().__init__(errors[0]["message"] if errors else "registry resolution is blocked")


class VerificationNotConfiguredError(ValueError):
    result = "BLOCKED"

    def __init__(self, errors):
        self.errors = errors
        super().__init__(errors[0]["message"] if errors else "verification input is not configured")


class DuplicateJsonKey(ValueError):
    pass


class NonFiniteJsonNumber(ValueError):
    pass


class ProcessGroupError(RuntimeError):
    pass


class RedactionUncertainty(RuntimeError):
    pass



class ExecutionLifecycleTimeout(RedactionUncertainty):
    pass


class CaptureResourceLimit(RedactionUncertainty):
    pass

_CAPTURE_SEAL = object()


class _ScrubbedByteBudget:
    def __init__(self, maximum_bytes):
        self.maximum_bytes = maximum_bytes
        self.retained_bytes = 0
        self._lock = __import__("threading").Lock()


class _BoundedScrubbedSink:
    def __init__(self, maximum_bytes, budget):
        self.maximum_bytes = maximum_bytes
        self.budget = budget
        self._buffer = bytearray()

    @property
    def retained_bytes(self):
        return len(self._buffer)

    def append(self, scrubbed):
        if not isinstance(scrubbed, bytes):
            raise RedactionUncertainty("scrubbed capture must be bytes")
        with self.budget._lock:
            if (
                len(self._buffer) + len(scrubbed) > self.maximum_bytes
                or self.budget.retained_bytes + len(scrubbed) > self.budget.maximum_bytes
            ):
                raise CaptureResourceLimit("scrubbed output exceeded the capture bound")
            self._buffer.extend(scrubbed)
            self.budget.retained_bytes += len(scrubbed)

    def bytes(self):
        return bytes(self._buffer)


@dataclass(frozen=True, eq=False)
class ScrubbedEvidence:
    stdout: bytes
    stderr: bytes
    _seal: object

    def __getitem__(self, name):
        if name not in ("stdout", "stderr"):
            raise KeyError(name)
        return getattr(self, name)

    def values(self):
        return (self.stdout, self.stderr)

    def __eq__(self, other):
        if isinstance(other, dict):
            return other == {"stdout": self.stdout, "stderr": self.stderr}
        return self is other

    def is_authentic(self):
        return self._seal is _CAPTURE_SEAL
class EvidenceWriteUncertainty(RuntimeError):
    pass


@dataclass(frozen=True)
class AcquiredRunLock:
    path: Path
    owner: dict


REDACTION_READ_BYTES = 65536
REDACTION_CARRY_BYTES = 8192
REDACTION_STREAM_BYTES = 1048576
REDACTION_COMBINED_BYTES = 2097152
REDACTION_CANDIDATE_BYTES = 4096
REDACTION_REPLACEMENT = "[REDACTED]"
AUTHORIZATION_PATTERN = re.compile(r"(?im)^(Authorization:[ \t]*(?:Bearer[ \t]+)?)([^\r\n]+)$")
COOKIE_PATTERN = re.compile(r"(?im)^((?:Cookie|Set-Cookie):[ \t]*)([^\r\n]+)$")
BEARER_PATTERN = re.compile(r"(?i)\b(Bearer[ \t]+)([^\s\r\n]+)")
ASSIGNMENT_PATTERN = re.compile(
    r"(?i)\b((?:token|access_token|refresh_token|password|passwd|secret|api_key|private_key|credential)"
    r"[ \t]*[:=][ \t]*)(?:\"([^\"\r\n]*)\"|'([^'\r\n]*)'|([^\s\r\n]+))"
)
SENSITIVE_PREFIX_PATTERN = re.compile(
    r"(?im)(?:^(?:Authorization|Cookie|Set-Cookie):[ \t]*(?:Bearer[ \t]+)?|"
    r"\bBearer[ \t]+|\b(?:token|access_token|refresh_token|password|passwd|secret|api_key|"
    r"private_key|credential)[ \t]*[:=][ \t]*)"
)


class BoundedStreamScrubber:
    def __init__(self, injected_literals=(), *, carry_bytes=REDACTION_CARRY_BYTES,
                 candidate_bytes=REDACTION_CANDIDATE_BYTES):
        if not isinstance(carry_bytes, int) or not 0 < carry_bytes <= REDACTION_CARRY_BYTES:
            raise RedactionUncertainty("invalid redaction carry bound")
        if not isinstance(candidate_bytes, int) or not 0 < candidate_bytes <= REDACTION_CANDIDATE_BYTES:
            raise RedactionUncertainty("invalid redaction candidate bound")
        if not isinstance(injected_literals, (tuple, list)):
            raise RedactionUncertainty("injected literals must be a bounded sequence")
        self.carry_bytes = carry_bytes
        self.candidate_bytes = candidate_bytes
        self.decoder = codecs.getincrementaldecoder("utf-8")("strict")
        self.pending = ""
        self.literals = []
        for literal in injected_literals:
            if not isinstance(literal, str):
                raise RedactionUncertainty("injected literal must be text")
            encoded = literal.encode("utf-8")
            if not encoded or len(encoded) > candidate_bytes:
                raise RedactionUncertainty("injected literal exceeds the approved bound")
            self.literals.append(literal)

    def feed(self, chunk):
        if not isinstance(chunk, bytes):
            raise RedactionUncertainty("captured stream chunks must be bytes")
        try:
            self.pending += self.decoder.decode(chunk, final=False)
        except UnicodeDecodeError as error:
            raise RedactionUncertainty("captured stream is not strict UTF-8") from error
        pending_start = self._pending_sensitive_start(self.pending)
        if pending_start is not None:
            safe = self._scrub_text(self.pending[:pending_start])
            sensitive = self.pending[pending_start:]
            if len(sensitive.encode("utf-8")) > self.carry_bytes:
                raise RedactionUncertainty("pending sensitive value exceeds the carry bound")
            self.pending = sensitive
            return safe.encode("utf-8")
        scrubbed = self._scrub_text(self.pending)
        encoded = scrubbed.encode("utf-8")
        if len(encoded) <= self.carry_bytes:
            self.pending = scrubbed
            return b""
        split = len(encoded) - self.carry_bytes
        while split < len(encoded) and (encoded[split] & 0xC0) == 0x80:
            split += 1
        emitted = encoded[:split]
        self.pending = encoded[split:].decode("utf-8")
        return emitted

    def _pending_sensitive_start(self, text):
        for prefix in SENSITIVE_PREFIX_PATTERN.finditer(text):
            tail = text[prefix.end():]
            if any(tail.startswith(value) for value in (
                REDACTION_REPLACEMENT,
                f'"{REDACTION_REPLACEMENT}"',
                f"'{REDACTION_REPLACEMENT}'",
            )):
                continue
            prefix_text = prefix.group(0).lower()
            candidate = tail
            pending = False
            if tail.startswith(('"', "'")):
                quote = tail[0]
                closing = tail.find(quote, 1)
                if closing < 0:
                    candidate = tail[1:]
                    pending = True
            elif prefix_text.lstrip().startswith(("authorization", "cookie", "set-cookie")):
                pending = "\n" not in tail and "\r" not in tail
            else:
                delimiter = re.search(r"[\s\r\n]", tail)
                pending = delimiter is None
                candidate = tail if delimiter is None else tail[:delimiter.start()]
            if pending:
                if len(candidate.encode("utf-8")) > self.candidate_bytes:
                    raise RedactionUncertainty("sensitive value exceeds the approved bound")
                return prefix.start()
        return None

    def _bounded_value(self, value):
        size = len(value.encode("utf-8"))
        if not value or size > self.candidate_bytes:
            raise RedactionUncertainty("sensitive value exceeds the approved bound")
        return value

    def finish(self):
        try:
            self.pending += self.decoder.decode(b"", final=True)
        except UnicodeDecodeError as error:
            raise RedactionUncertainty("captured stream ends with incomplete UTF-8") from error
        return self._scrub_text(self.pending).encode("utf-8")

    def _scrub_text(self, text):

        def replace_pair(match):
            self._bounded_value(match.group(2))
            return match.group(1) + REDACTION_REPLACEMENT

        text = AUTHORIZATION_PATTERN.sub(replace_pair, text)
        text = COOKIE_PATTERN.sub(replace_pair, text)
        text = BEARER_PATTERN.sub(replace_pair, text)

        def replace_assignment(match):
            values = match.groups()[1:]
            index, value = next((index, value) for index, value in enumerate(values) if value is not None)
            self._bounded_value(value)
            quote = ('"', "'", "")[index]
            return match.group(1) + quote + REDACTION_REPLACEMENT + quote

        text = ASSIGNMENT_PATTERN.sub(replace_assignment, text)
        for literal in sorted(self.literals, key=lambda item: len(item.encode("utf-8")), reverse=True):
            text = text.replace(literal, REDACTION_REPLACEMENT)

        for prefix in SENSITIVE_PREFIX_PATTERN.finditer(text):
            tail = text[prefix.end():]
            if any(tail.startswith(value) for value in (
                REDACTION_REPLACEMENT,
                f'"{REDACTION_REPLACEMENT}"',
                f"'{REDACTION_REPLACEMENT}'",
            )):
                continue
            raise RedactionUncertainty("sensitive prefix is incomplete or exceeds the carry bound")
        return text


def capture_and_scrub(process, limits=None, injected_literals=(), lifecycle_deadline=None):
    approved = {
        "readBytes": REDACTION_READ_BYTES,
        "carryBytes": REDACTION_CARRY_BYTES,
        "streamBytes": REDACTION_STREAM_BYTES,
        "combinedBytes": REDACTION_COMBINED_BYTES,
        "candidateBytes": REDACTION_CANDIDATE_BYTES,
    }
    if limits is None:
        limits = dict(approved)
    required = set(approved)
    if not isinstance(limits, dict) or set(limits) != required or any(
        not isinstance(limits[name], int) or limits[name] <= 0 for name in required
    ):
        raise RedactionUncertainty("capture limits are invalid")
    if limits != approved:
        raise RedactionUncertainty("capture limits must equal the approved bounds")
    streams = {"stdout": getattr(process, "stdout", None), "stderr": getattr(process, "stderr", None)}
    if any(stream is None or not callable(getattr(stream, "read", None)) for stream in streams.values()):
        raise RedactionUncertainty("separate stdout and stderr pipes are required")
    if lifecycle_deadline is None:
        lifecycle_deadline = time.monotonic() + EXECUTION_TIMEOUT_SECONDS
    if (
        not isinstance(lifecycle_deadline, (int, float))
        or isinstance(lifecycle_deadline, bool)
        or not lifecycle_deadline > 0
    ):
        raise RedactionUncertainty("execution lifecycle deadline is invalid")

    combined = 0
    combined_lock = __import__("threading").Lock()
    termination_lock = __import__("threading").Lock()
    termination_requested = False
    uncertainty = []
    termination_errors = []
    retained_budget = _ScrubbedByteBudget(limits["combinedBytes"])
    states = {
        name: {
            "seen": 0,
            "scrubber": BoundedStreamScrubber(
                injected_literals,
                carry_bytes=limits["carryBytes"],
                candidate_bytes=limits["candidateBytes"],
            ),
            "sink": _BoundedScrubbedSink(limits["streamBytes"], retained_budget),
        }
        for name in streams
    }

    def terminate_once():
        nonlocal termination_requested
        with termination_lock:
            if termination_requested:
                return
            termination_requested = True
        if isinstance(getattr(process, "pid", None), int) and callable(getattr(process, "poll", None)):
            try:
                terminate_process_group(process, PROCESS_GROUP_GRACE_SECONDS)
            except ProcessGroupError as error:
                termination_errors.append(error)

    def accept_chunk(name, chunk):
        nonlocal combined
        state = states[name]
        if not isinstance(chunk, bytes):
            raise RedactionUncertainty(f"{name} returned non-byte output")
        state["seen"] += len(chunk)
        with combined_lock:
            combined += len(chunk)
            combined_over = combined > limits["combinedBytes"]
        if state["seen"] > limits["streamBytes"] or combined_over:
            raise CaptureResourceLimit(f"{name} exceeded the capture bound")
        state["sink"].append(state["scrubber"].feed(chunk))

    def finish_stream(name):
        state = states[name]
        state["sink"].append(state["scrubber"].finish())
        return state["sink"].bytes()

    def consume(name, stream):
        while True:
            chunk = stream.read(limits["readBytes"])
            if not isinstance(chunk, bytes):
                uncertainty.append(RedactionUncertainty(f"{name} returned non-byte output"))
                break
            if not chunk:
                break
            if not uncertainty:
                try:
                    accept_chunk(name, chunk)
                except RedactionUncertainty as error:
                    uncertainty.append(error)
                    terminate_once()
        if uncertainty:
            return None
        try:
            return finish_stream(name)
        except RedactionUncertainty:
            terminate_once()
            raise

    def close_streams():
        for stream in streams.values():
            close = getattr(stream, "close", None)
            if callable(close):
                try:
                    close()
                except OSError as error:
                    termination_errors.append(error)

    def posix_pipe_descriptors():
        if os.name != "posix":
            return None
        descriptors = {}
        try:
            for name, stream in streams.items():
                descriptor = stream.fileno()
                if not isinstance(descriptor, int) or descriptor < 0 or not stat.S_ISFIFO(os.fstat(descriptor).st_mode):
                    return None
                descriptors[name] = descriptor
        except (AttributeError, OSError, TypeError, ValueError):
            return None
        return descriptors

    descriptors = posix_pipe_descriptors()
    if descriptors is not None:
        selector = selectors.DefaultSelector()
        blocking = {}
        captured = {}
        try:
            for name, descriptor in descriptors.items():
                blocking[descriptor] = os.get_blocking(descriptor)
                os.set_blocking(descriptor, False)
                selector.register(descriptor, selectors.EVENT_READ, name)
            while selector.get_map():
                remaining = lifecycle_deadline - time.monotonic()
                if remaining <= 0:
                    raise ExecutionLifecycleTimeout("execution lifecycle timed out")
                events = selector.select(remaining)
                if not events:
                    raise ExecutionLifecycleTimeout("execution lifecycle timed out")
                for key, _mask in events:
                    try:
                        chunk = os.read(key.fd, limits["readBytes"])
                    except BlockingIOError:
                        continue
                    if chunk:
                        accept_chunk(key.data, chunk)
                    else:
                        selector.unregister(key.fd)
            for name in streams:
                captured[name] = finish_stream(name)
        except RedactionUncertainty as error:
            terminate_once()
            close_streams()
            if termination_errors:
                message = f"{error}; process-group termination could not be proven"
                raise type(error)(message) from termination_errors[0]
            raise
        finally:
            selector.close()
            for descriptor, was_blocking in blocking.items():
                try:
                    os.set_blocking(descriptor, was_blocking)
                except OSError:
                    pass
        return ScrubbedEvidence(captured["stdout"], captured["stderr"], _CAPTURE_SEAL)

    executor = ThreadPoolExecutor(max_workers=2)
    futures = {name: executor.submit(consume, name, stream) for name, stream in streams.items()}
    captured = {}
    timed_out = False
    try:
        for name, future in futures.items():
            remaining = lifecycle_deadline - time.monotonic()
            if remaining <= 0:
                raise FutureTimeoutError()
            captured[name] = future.result(timeout=remaining)
    except FutureTimeoutError:
        timed_out = True
        terminate_once()
        close_streams()
        drain_deadline = time.monotonic() + DRAIN_COMPLETION_SECONDS
        for future in futures.values():
            if future.done():
                continue
            try:
                future.result(timeout=max(0.001, drain_deadline - time.monotonic()))
            except (FutureTimeoutError, RedactionUncertainty):
                pass
    finally:
        executor.shutdown(wait=False)
    if timed_out:
        message = "execution lifecycle timed out"
        if termination_errors:
            message += "; process-group termination could not be proven"
            raise ExecutionLifecycleTimeout(message) from termination_errors[0]
        raise ExecutionLifecycleTimeout(message)
    if uncertainty or any(value is None for value in captured.values()):
        error = uncertainty[0] if uncertainty else RedactionUncertainty("captured output is uncertain")
        if termination_errors:
            message = f"{error}; process-group termination could not be proven"
            raise type(error)(message) from termination_errors[0]
        raise error
    if termination_errors:
        raise RedactionUncertainty("process-group termination could not be proven") from termination_errors[0]
    return ScrubbedEvidence(captured["stdout"], captured["stderr"], _CAPTURE_SEAL)


class ClosedArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        raise ValueError(message)


def compact(value):
    return json.dumps(value, separators=(",", ":"), sort_keys=True)


def gateway_result(result, reason, data=None, *, operation="PREFLIGHT", errors=None):
    return {
        "$schema": "ai/schemas/gateway-result.schema.json",
        "$id": "ai/gateway-result.json",
        "schemaVersion": 1,
        "operation": operation,
        "result": result,
        "reason": reason,
        "errors": [] if errors is None else errors,
        "data": data,
    }


def validation_error(code, instance_path="", schema_path="", message="invalid workflow state"):
    return {
        "code": code,
        "instancePath": instance_path,
        "schemaPath": schema_path,
        "message": message,
    }


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateJsonKey(key)
        result[key] = value
    return result


def reject_non_finite_number(value):
    raise NonFiniteJsonNumber(value)


def read_json(path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(
                handle,
                object_pairs_hook=reject_duplicate_keys,
                parse_constant=reject_non_finite_number,
            )
    except DuplicateJsonKey as error:
        raise InvalidStateError([
            validation_error(
                "DUPLICATE_JSON_KEY",
                message="duplicate JSON object key is forbidden",
            )
        ]) from error
    except NonFiniteJsonNumber as error:
        raise InvalidStateError([
            validation_error(
                "NON_FINITE_JSON_NUMBER",
                message=f"non-finite JSON number is forbidden: {error}",
            )
        ]) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidStateError([
            validation_error("MALFORMED_JSON", message="input is not valid UTF-8 JSON")
        ]) from error


def json_pointer(parts):
    if not parts:
        return ""
    return "/" + "/".join(str(part).replace("~", "~0").replace("/", "~1") for part in parts)


def normalized_schema_errors(errors):
    normalized = [
        validation_error(
            "SCHEMA_VALIDATION_ERROR",
            json_pointer(error.absolute_path),
            json_pointer(error.absolute_schema_path),
            f"instance does not satisfy schema constraint: {error.validator}",
        )
        for error in errors
    ]
    return sorted(
        normalized,
        key=lambda error: (
            error["instancePath"],
            error["schemaPath"],
            error["code"],
            error["message"],
        ),
    )


def resolve_repository_file(root, path):
    try:
        repository_root = Path(root).resolve(strict=True)
        candidate = Path(path)
        if not candidate.is_absolute():
            candidate = repository_root / candidate
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(repository_root)
    except (OSError, ValueError) as error:
        raise InvalidStateError([
            validation_error("PATH_OUTSIDE_REPOSITORY", message="path is unavailable or outside the repository")
        ]) from error
    if not resolved.is_file():
        raise InvalidStateError([
            validation_error("PATH_NOT_FILE", message="path is not a regular file")
        ])
    return resolved


def reject_external_schema_references(schema):
    pending = [(schema, ())]
    while pending:
        value, path = pending.pop()
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = path + (key,)
                if key in ("$ref", "$dynamicRef") and (
                    not isinstance(child, str) or not child.startswith("#")
                ):
                    raise InvalidStateError([
                        validation_error(
                            "EXTERNAL_SCHEMA_REFERENCE",
                            schema_path=json_pointer(child_path),
                            message="schema references must use local fragments",
                        )
                    ])
                pending.append((child, child_path))
        elif isinstance(value, list):
            pending.extend((child, path + (index,)) for index, child in enumerate(value))


def load_approved_schema(root, schema_path):
    profile = APPROVED_SCHEMA_PATHS.get(schema_path)
    if profile is None:
        raise InvalidStateError([
            validation_error(
                "UNAPPROVED_SCHEMA_PATH",
                message="schema path is not in the internal repository allowlist",
            )
        ])
    schema_file = resolve_repository_file(root, schema_path)
    schema = read_json(schema_file)
    if not isinstance(schema, dict):
        raise InvalidStateError([
            validation_error("INVALID_SCHEMA_ROOT", message="schema root must be an object")
        ])
    if schema.get("$schema") != DRAFT_2020_12_URI:
        raise InvalidStateError([
            validation_error("SCHEMA_DRAFT_MISMATCH", schema_path="/$schema", message="schema must use Draft 2020-12")
        ])
    if schema.get("$id") != profile["id"]:
        raise InvalidStateError([
            validation_error("SCHEMA_ID_MISMATCH", schema_path="/$id", message="schema ID does not match the approved project URN")
        ])
    if schema.get("schemaVersion") != 1:
        raise InvalidStateError([
            validation_error("SCHEMA_VERSION_MISMATCH", schema_path="/schemaVersion", message="schema must declare version 1")
        ])
    reject_external_schema_references(schema)
    try:
        Draft202012Validator.check_schema(schema)
    except Exception as error:
        raise InvalidStateError([
            validation_error("SCHEMA_SELF_CHECK_FAILED", message="approved schema failed Draft 2020-12 self-check")
        ]) from error
    return schema


def validate(root, instance, schema_path):
    schema = load_approved_schema(root, schema_path)
    errors = normalized_schema_errors(
        Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance)
    )
    if errors:
        raise InvalidStateError(errors)
    validate_phase_1b2_contract(instance, schema_path)
    if schema_path == "ai/schemas/native-bypass-attempt.schema.json":
        validate_native_bypass_attempt(instance)
    elif schema_path == "ai/schemas/native-runtime-adapters.schema.json":
        validate_native_runtime_adapters_semantics(instance)
    elif schema_path == "ai/schemas/host-native-trust.schema.json":
        validate_host_native_trust_descriptor(instance)


def parse_rfc3339_timestamp(value):
    timestamp, separator, fractional_seconds = value[:-1].partition(".")
    observed_at = dt.datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=dt.timezone.utc)
    return observed_at, Decimal("0" if not separator else f"0.{fractional_seconds}")


def validate_native_bypass_attempt(instance):
    if instance.get("lifecycle") != "RESOLVED":
        return

    observed_at = parse_rfc3339_timestamp(instance["observedAt"])
    resolved_at = parse_rfc3339_timestamp(instance["resolvedAt"])
    if resolved_at < observed_at:
        raise InvalidStateError([
            validation_error(
                "NATIVE_BYPASS_RESOLUTION_BEFORE_OBSERVATION",
                "/resolvedAt",
                message="resolvedAt must not be earlier than observedAt",
            )
        ])


def phase_1b2_error(code, instance_path, message):
    return validation_error(code, instance_path, message=message)


def validate_phase_1b2_command_result(instance):
    missing = [name for name in ("attemptId", "processAttemptRef") if name not in instance]
    if missing:
        raise InvalidStateError([
            phase_1b2_error(
                "PHASE_1B2_ATTEMPT_REFERENCE_MISSING",
                f"/{missing[0]}",
                "Phase 1B-2 command results require attemptId and processAttemptRef",
            )
        ])
    run_id = instance.get("runId")
    command_id = instance.get("commandId")
    attempt_id = instance.get("attemptId")
    expected_command = f".ai-runs/{run_id}/commands/{command_id}/{attempt_id}.json"
    expected_process = f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json"
    errors = []
    if instance.get("$id") != expected_command:
        errors.append(phase_1b2_error(
            "COMMAND_RESULT_REFERENCE_MISMATCH",
            "/$id",
            "command result ID must equal the run, command, and attempt tuple path",
        ))
    if instance.get("processAttemptRef") != expected_process:
        errors.append(phase_1b2_error(
            "PROCESS_ATTEMPT_REFERENCE_MISMATCH",
            "/processAttemptRef",
            "processAttemptRef must equal the run, command, and attempt tuple path",
        ))
    if errors:
        raise InvalidStateError(sorted(
            errors,
            key=lambda error: (error["instancePath"], error["code"], error["message"]),
        ))


def validate_gateway_result(instance):
    operation = instance.get("operation")
    result = instance.get("result")
    data = instance.get("data")
    errors = []
    if operation == "RUN_START" and result == "PASS":
        expected_session = f".ai-runs/{data.get('runId')}/.state/run-session.json"
        if data.get("sessionRef") != expected_session:
            errors.append(phase_1b2_error(
                "RUN_START_SESSION_REFERENCE_MISMATCH",
                "/data/sessionRef",
                "RUN_START sessionRef must equal the run session tuple path",
            ))
    elif operation == "POST_COMMAND" and result in ("PASS", "FAIL", "BLOCKED"):
        run_id = data.get("runId")
        command_id = data.get("commandId")
        attempt_id = data.get("attemptId")
        expected_command = f".ai-runs/{run_id}/commands/{command_id}/{attempt_id}.json"
        expected_process = f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json"
        if data.get("commandResultRef") != expected_command:
            errors.append(phase_1b2_error(
                "POST_COMMAND_RESULT_REFERENCE_MISMATCH",
                "/data/commandResultRef",
                "POST_COMMAND commandResultRef must equal the result tuple path",
            ))
        if data.get("processAttemptRef") != expected_process:
            errors.append(phase_1b2_error(
                "POST_PROCESS_ATTEMPT_REFERENCE_MISMATCH",
                "/data/processAttemptRef",
                "POST_COMMAND processAttemptRef must equal the process tuple path",
            ))
    elif operation == "PRE_DONE_CLAIM" and result == "PASS":
        run_id = data.get("runId")
        expected = {
            "doneClaimRef": f".ai-runs/{run_id}/done-claim.json",
            "manifestRef": f".ai-runs/{run_id}/artifact-manifest.json",
            "runRef": f".ai-runs/{run_id}/run.json",
            "gateResultRef": f".ai-runs/{run_id}/gate-results/pre-done-claim.json",
        }
        for key, value in expected.items():
            if data.get(key) != value:
                errors.append(phase_1b2_error(
                    "PRE_DONE_CLAIM_REFERENCE_MISMATCH",
                    f"/data/{key}",
                    "PRE_DONE_CLAIM references must equal the exact run artifact paths",
                ))
    if errors:
        raise InvalidStateError(sorted(
            errors,
            key=lambda error: (error["instancePath"], error["code"], error["message"]),
        ))


def validate_phase_1b2_contract(instance, schema_path):
    if schema_path == "ai/schemas/gateway-result.schema.json":
        validate_gateway_result(instance)
        return

    if schema_path == "ai/schemas/command-result.schema.json":
        if "attemptId" in instance or "processAttemptRef" in instance:
            validate_phase_1b2_command_result(instance)
        return

    if schema_path == "ai/schemas/process-attempt.schema.json":
        expected = ".ai-runs/{}/process-attempts/{}/{}.json".format(
            instance.get("runId"), instance.get("commandId"), instance.get("attemptId")
        )
        if instance.get("$id") != expected:
            raise InvalidStateError([
                phase_1b2_error(
                    "PROCESS_ATTEMPT_REFERENCE_MISMATCH",
                    "/$id",
                    "process attempt ID must equal the run, command, and attempt tuple path",
                )
            ])
        return

    if schema_path == "ai/schemas/artifact-manifest.schema.json":
        expected = ".ai-runs/{}/artifact-manifest.json".format(instance.get("runId"))
        if instance.get("$id") != expected:
            raise InvalidStateError([
                phase_1b2_error(
                    "ARTIFACT_MANIFEST_REFERENCE_MISMATCH",
                    "/$id",
                    "artifact manifest ID must equal its run path",
                )
            ])
        paths = [artifact["path"] for artifact in instance.get("artifacts", [])]
        if len(paths) != len(set(paths)):
            raise InvalidStateError([
                phase_1b2_error(
                    "DUPLICATE_ARTIFACT_PATH",
                    "/artifacts",
                    "artifact manifest paths must be unique",
                )
            ])
        return

    if schema_path == "ai/schemas/run-session.schema.json":
        validate_run_session(instance)


def validate_run_session(instance):
    errors = []

    run_id = instance.get("runId")
    expected_session = f".ai-runs/{run_id}/.state/run-session.json"
    if instance.get("$id") != expected_session:
        errors.append(phase_1b2_error(
            "RUN_SESSION_REFERENCE_MISMATCH",
            "/$id",
            "run session ID must equal its run path",
        ))

    reference_lists = (
        "commandResultRefs",
        "processAttemptRefs",
        "approvalRefs",
        "policyViolationRefs",
        "gateResultRefs",
    )
    references = [reference for name in reference_lists for reference in instance.get(name, [])]
    if len(references) != len(set(references)):
        errors.append(phase_1b2_error(
            "DUPLICATE_SESSION_REFERENCE",
            "",
            "session references must be unique across all reference arrays",
        ))

    recovery_ids = set()
    for index, recovery in enumerate(instance.get("lockRecoveries", [])):
        recovery_id = recovery.get("recoveryId")
        if recovery.get("runId") != run_id:
            errors.append(phase_1b2_error(
                "LOCK_RECOVERY_RUN_MISMATCH",
                f"/lockRecoveries/{index}/runId",
                "lock recovery runId must match the enclosing run session",
            ))
        if recovery_id in recovery_ids:
            errors.append(phase_1b2_error(
                "DUPLICATE_LOCK_RECOVERY_ID",
                f"/lockRecoveries/{index}/recoveryId",
                "lock recovery IDs must be unique within a run session",
            ))
        recovery_ids.add(recovery_id)

    command_refs = set(instance.get("commandResultRefs", []))
    process_refs = set(instance.get("processAttemptRefs", []))
    reservation_tuples = set()
    attempt_ids = set()
    for index, reservation in enumerate(instance.get("reservations", [])):
        attempt_id = reservation.get("attemptId")
        command_id = reservation.get("commandId")
        reservation_tuple = (command_id, attempt_id)
        expected_command = f".ai-runs/{run_id}/commands/{command_id}/{attempt_id}.json"
        expected_process = f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json"
        state = reservation.get("state")
        command_ref = reservation.get("commandResultRef")
        process_ref = reservation.get("processAttemptRef")
        prefix = f"/reservations/{index}"
        if reservation_tuple in reservation_tuples:
            errors.append(phase_1b2_error(
                "DUPLICATE_RESERVATION_TUPLE",
                prefix,
                "reservation commandId and attemptId tuples must be unique",
            ))
        if attempt_id in attempt_ids:
            errors.append(phase_1b2_error(
                "DUPLICATE_ATTEMPT_ID",
                prefix + "/attemptId",
                "reservation attempt IDs must be unique within a run session",
            ))
        reservation_tuples.add(reservation_tuple)
        attempt_ids.add(attempt_id)
        if state == "RESERVED":
            if command_ref is not None or process_ref is not None:
                errors.append(phase_1b2_error(
                    "RESERVED_TERMINAL_REFERENCE",
                    prefix,
                    "a RESERVED reservation cannot contain terminal references",
                ))
            continue
        if command_ref != expected_command or command_ref not in command_refs:
            errors.append(phase_1b2_error(
                "COMMAND_RESULT_REFERENCE_MISMATCH",
                prefix + "/commandResultRef",
                "terminal command result reference must match the reservation tuple and session",
            ))
        if process_ref != expected_process or process_ref not in process_refs:
            errors.append(phase_1b2_error(
                "PROCESS_ATTEMPT_REFERENCE_MISMATCH",
                prefix + "/processAttemptRef",
                "terminal process attempt reference must match the reservation tuple and session",
            ))

    if errors:
        raise InvalidStateError(sorted(
            errors,
            key=lambda error: (
                error["instancePath"],
                error["schemaPath"],
                error["code"],
                error["message"],
            ),
        ))


def validate_repository_instance(root, instance_path):
    instance_file = resolve_repository_file(root, instance_path)
    instance = read_json(instance_file)
    if not isinstance(instance, dict):
        raise InvalidStateError([
            validation_error("INVALID_INSTANCE_ROOT", message="workflow JSON root must be an object")
        ])

    instance_schema = instance.get("$schema")
    profile = SCHEMA_ALLOWLIST.get(instance_schema)
    if profile is None:
        raise InvalidStateError([
            validation_error(
                "UNSUPPORTED_INSTANCE_SCHEMA",
                "/$schema",
                message="instance schema is not in the internal allowlist",
            )
        ])
    if instance.get("schemaVersion") != 1:
        raise InvalidStateError([
            validation_error(
                "UNSUPPORTED_SCHEMA_VERSION",
                "/schemaVersion",
                "/properties/schemaVersion/const",
                "only schemaVersion 1 is supported",
            )
        ])

    validate(root, instance, profile["path"])
    return instance


PLACEHOLDER_TOKEN = re.compile(r"^\{\{([A-Za-z][A-Za-z0-9_]*)\}\}$")
PARAMETER_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")
COMMAND_ID = re.compile(r"^[a-z][a-z0-9-]*(?:\.[a-z][a-z0-9-]*)+$")
MAX_PARAMETER_FILE_BYTES = 65536
MAX_PARAMETER_VALUE_SCALARS = 1024
SECRET_PATH_TERMS = ("secret", "token", "password", "credential")


def ordered_errors(errors):
    return sorted(
        errors,
        key=lambda error: (
            error["instancePath"],
            error["schemaPath"],
            error["code"],
            error["message"],
        ),
    )


def safe_parameter_pattern(pattern):
    if not (pattern.startswith("^") and pattern.endswith("$")):
        return "PARAMETER_PATTERN_UNANCHORED"

    body = pattern[1:-1]
    inside_class = False
    escaped = False
    has_atom = False
    previous_was_quantifier = False
    for character in body:
        if escaped:
            if character.isalnum():
                return "UNSAFE_PARAMETER_PATTERN"
            escaped = False
            has_atom = True
            previous_was_quantifier = False
            continue
        if character == "\\":
            escaped = True
            continue
        if inside_class:
            if character == "]":
                inside_class = False
                has_atom = True
                previous_was_quantifier = False
            elif character == "[":
                return "UNSAFE_PARAMETER_PATTERN"
            continue
        if character == "[":
            inside_class = True
            has_atom = False
            previous_was_quantifier = False
            continue
        if character in "^$()|{}":
            return "UNSAFE_PARAMETER_PATTERN"
        if character in "?*+":
            if not has_atom or previous_was_quantifier:
                return "UNSAFE_PARAMETER_PATTERN"
            previous_was_quantifier = True
            continue
        has_atom = True
        previous_was_quantifier = False

    if escaped or inside_class:
        return "PARAMETER_PATTERN_INVALID"
    try:
        re.compile(pattern)
    except re.error:
        return "PARAMETER_PATTERN_INVALID"
    return None


def registry_error(code, instance_path, message):
    return validation_error(code, instance_path, "", message)


def is_static_wrapper_evidenced(command, wrapper_repository_path):
    expected_path = Path(wrapper_repository_path).as_posix()
    for evidence in command.get("evidence", []):
        if (
            evidence.get("kind") == "STATIC_FILE"
            and Path(evidence.get("path", "")).as_posix() == expected_path
        ):
            return True
    return False


def validate_registry_semantics(root, registry):
    """Validate schema-valid command registry invariants without executing project argv."""
    errors = []
    blocked_errors = []
    commands = registry.get("commands", [])
    commands_by_id = {}
    command_indexes = {}

    for index, command in enumerate(commands):
        command_id = command.get("id")
        if command_id in commands_by_id:
            errors.append(registry_error(
                "DUPLICATE_COMMAND_ID",
                f"/commands/{index}/id",
                "command IDs must be globally unique",
            ))
        else:
            commands_by_id[command_id] = command
            command_indexes[command_id] = index

    for index, command in enumerate(commands):
        argv = command.get("argv")
        parameters = command.get("parameters", {})
        placeholders = []

        if argv is not None:
            if not argv or argv[0] != "./gradlew":
                errors.append(registry_error(
                    "UNSUPPORTED_EXECUTABLE",
                    f"/commands/{index}/argv/0",
                    "schemaVersion 1 only supports ./gradlew",
                ))
            for argument_index, token in enumerate(argv):
                if "{" not in token and "}" not in token:
                    continue
                match = PLACEHOLDER_TOKEN.fullmatch(token)
                if match is None:
                    errors.append(registry_error(
                        "INVALID_PLACEHOLDER",
                        f"/commands/{index}/argv/{argument_index}",
                        "placeholders must occupy one complete argv token",
                    ))
                else:
                    placeholders.append(match.group(1))

        if parameters.get("allowed"):
            parameter_schema = parameters.get("schema") or {}
            properties = parameter_schema.get("properties", {})
            required = parameter_schema.get("required", [])
            if set(required) != set(properties):
                errors.append(registry_error(
                    "PARAMETER_KEYS_MISMATCH",
                    f"/commands/{index}/parameters/schema",
                    "parameter required names must exactly equal property names",
                ))
            if set(placeholders) != set(properties):
                errors.append(registry_error(
                    "PLACEHOLDER_PARAMETER_MISMATCH",
                    f"/commands/{index}/parameters/schema",
                    "placeholder names must exactly equal parameter property names",
                ))
            for name in sorted(properties):
                pattern = properties[name].get("pattern", "")
                pattern_code = safe_parameter_pattern(pattern)
                if pattern_code is not None:
                    errors.append(registry_error(
                        pattern_code,
                        f"/commands/{index}/parameters/schema/properties/{name}/pattern",
                        "parameter patterns must use the anchored safe-regex subset",
                    ))
        elif placeholders:
            first_placeholder_index = next(
                argument_index
                for argument_index, token in enumerate(argv or [])
                if PLACEHOLDER_TOKEN.fullmatch(token)
            )
            errors.append(registry_error(
                "PLACEHOLDER_PARAMETERS_DISABLED",
                f"/commands/{index}/argv/{first_placeholder_index}",
                "placeholders are forbidden when parameters are disabled",
            ))

        for prerequisite_index, prerequisite_id in enumerate(command.get("prerequisites", [])):
            prerequisite_path = f"/commands/{index}/prerequisites/{prerequisite_index}"
            if prerequisite_id not in commands_by_id:
                errors.append(registry_error(
                    "UNKNOWN_PREREQUISITE",
                    prerequisite_path,
                    "prerequisite command ID is not registered",
                ))
            elif prerequisite_id == command.get("id"):
                errors.append(registry_error(
                    "SELF_PREREQUISITE",
                    prerequisite_path,
                    "a command cannot require itself",
                ))

    graph = {
        command_id: sorted(
            prerequisite
            for prerequisite in command.get("prerequisites", [])
            if prerequisite in commands_by_id and prerequisite != command_id
        )
        for command_id, command in commands_by_id.items()
    }
    visiting = []
    visited = set()
    cycle_nodes = set()

    def visit(command_id):
        if command_id in visiting:
            cycle_nodes.update(visiting[visiting.index(command_id):])
            return
        if command_id in visited:
            return
        visiting.append(command_id)
        for prerequisite_id in graph[command_id]:
            visit(prerequisite_id)
        visiting.pop()
        visited.add(command_id)

    for command_id in sorted(commands_by_id):
        visit(command_id)
    if cycle_nodes:
        cycle_index = min(command_indexes[command_id] for command_id in cycle_nodes)
        errors.append(registry_error(
            "CYCLIC_PREREQUISITE",
            f"/commands/{cycle_index}/prerequisites",
            "prerequisite graph must be acyclic",
        ))

    try:
        repository_root = Path(root).resolve(strict=True)
    except (OSError, ValueError) as error:
        raise InvalidStateError([registry_error("REPOSITORY_ROOT_INVALID", "", "repository root is unavailable")]) from error

    for index, command in enumerate(commands):
        if command.get("argv") is None:
            continue
        working_directory_path = f"/commands/{index}/workingDirectory"
        working_directory = repository_root / command.get("workingDirectory", "")
        try:
            resolved_working_directory = working_directory.resolve(strict=True)
        except OSError:
            errors.append(registry_error(
                "WORKING_DIRECTORY_MISSING",
                working_directory_path,
                "configured working directory does not exist",
            ))
            continue
        try:
            resolved_working_directory.relative_to(repository_root)
        except ValueError:
            errors.append(registry_error(
                "WORKING_DIRECTORY_OUTSIDE_REPOSITORY",
                working_directory_path,
                "configured working directory escapes the repository",
            ))
            continue
        if not resolved_working_directory.is_dir():
            errors.append(registry_error(
                "WORKING_DIRECTORY_NOT_DIRECTORY",
                working_directory_path,
                "configured working directory is not a directory",
            ))
            continue

        wrapper_path = resolved_working_directory / "gradlew"
        try:
            resolved_wrapper = wrapper_path.resolve(strict=True)
        except OSError:
            resolved_wrapper = wrapper_path.resolve(strict=False)
            try:
                wrapper_repository_path = resolved_wrapper.relative_to(repository_root).as_posix()
            except ValueError:
                errors.append(registry_error(
                    "WRAPPER_OUTSIDE_REPOSITORY",
                    f"/commands/{index}/argv/0",
                    "configured Gradle wrapper escapes the repository",
                ))
                continue
            wrapper_is_evidenced = is_static_wrapper_evidenced(command, wrapper_repository_path)
            wrapper_error = registry_error(
                "WRAPPER_STATIC_EVIDENCE_MISSING" if wrapper_is_evidenced else "WRAPPER_MISSING",
                f"/commands/{index}/argv/0",
                "statically evidenced Gradle wrapper is missing" if wrapper_is_evidenced else "configured Gradle wrapper does not exist",
            )
            (blocked_errors if wrapper_is_evidenced else errors).append(wrapper_error)
            continue
        try:
            resolved_wrapper.relative_to(repository_root)
        except ValueError:
            errors.append(registry_error(
                "WRAPPER_OUTSIDE_REPOSITORY",
                f"/commands/{index}/argv/0",
                "configured Gradle wrapper escapes the repository",
            ))
            continue
        if not resolved_wrapper.is_file():
            errors.append(registry_error(
                "WRAPPER_NOT_FILE",
                f"/commands/{index}/argv/0",
                "configured Gradle wrapper is not a regular file",
            ))

    if errors:
        raise InvalidStateError(ordered_errors(errors))
    if blocked_errors:
        raise RegistryBlockedError(ordered_errors(blocked_errors))

    ordered_prerequisites = {}
    for command_id in sorted(commands_by_id):
        ordered = []
        seen = set()

        def add_prerequisites(current_id):
            for prerequisite_id in graph[current_id]:
                if prerequisite_id not in seen:
                    add_prerequisites(prerequisite_id)
                    seen.add(prerequisite_id)
                    ordered.append(prerequisite_id)

        add_prerequisites(command_id)
        ordered_prerequisites[command_id] = ordered
    return ordered_prerequisites


def find_registry_command(root, registry_path, command_id):
    """Load, schema-validate, and semantically validate a registry before lookup."""
    registry = validate_repository_instance(root, registry_path)
    validate_registry_semantics(root, registry)
    return next((command for command in registry["commands"] if command["id"] == command_id), None)


def resolve_result(result, reason, status, data=None, errors=None):
    return gateway_result(
        result,
        reason,
        data,
        operation="RESOLVE",
        errors=[] if errors is None else errors,
    ), status


def policy_violation(reason):
    return resolve_result("POLICY_VIOLATION", reason, 4)


def forbidden_parameter_path_parts(parts):
    lower_parts = tuple(part.lower() for part in parts)
    return (
        ".git" in lower_parts
        or ".ai-runs" in lower_parts
        or any(term in part for part in lower_parts for term in SECRET_PATH_TERMS)
        or (bool(lower_parts) and lower_parts[-1].startswith(".env"))
    )


def parameter_file_path(root, parameter_path):
    if not isinstance(parameter_path, str) or not parameter_path:
        raise ValueError("PARAMETER_FILE_PATH_INVALID")
    candidate = Path(parameter_path)
    if candidate.is_absolute():
        raise ValueError("PARAMETER_FILE_PATH_INVALID")
    parts = candidate.parts
    if any(part in ("", ".", "..") for part in parts):
        raise ValueError("PARAMETER_FILE_PATH_INVALID")
    if forbidden_parameter_path_parts(parts):
        raise ValueError("PARAMETER_FILE_PATH_FORBIDDEN")
    try:
        repository_root = Path(root).resolve(strict=True)
        resolved = (repository_root / candidate).resolve(strict=True)
        resolved_relative = resolved.relative_to(repository_root)
    except (OSError, ValueError) as error:
        raise ValueError("PARAMETER_FILE_PATH_INVALID") from error
    if forbidden_parameter_path_parts(resolved_relative.parts):
        raise ValueError("PARAMETER_FILE_PATH_FORBIDDEN")
    if not resolved.is_file():
        raise ValueError("PARAMETER_FILE_PATH_INVALID")
    return resolved


def read_parameter_object(root, parameter_path):
    try:
        parameter_file = parameter_file_path(root, parameter_path)
        encoded = parameter_file.read_bytes()
    except OSError as error:
        raise ValueError("PARAMETER_FILE_PATH_INVALID") from error
    if len(encoded) > MAX_PARAMETER_FILE_BYTES:
        raise ValueError("PARAMETER_FILE_TOO_LARGE")
    try:
        text = encoded.decode("utf-8", errors="strict")
        value = json.loads(
            text,
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_number,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, DuplicateJsonKey, NonFiniteJsonNumber) as error:
        raise ValueError("PARAMETER_FILE_INVALID_JSON") from error
    if not isinstance(value, dict):
        raise ValueError("PARAMETER_FILE_NOT_OBJECT")
    return value


def validate_parameter_values(parameter_schema, parameters):
    for value in parameters.values():
        if not isinstance(value, str):
            continue
        if len(value) > MAX_PARAMETER_VALUE_SCALARS:
            raise ValueError("PARAMETER_VALUE_TOO_LONG")
        for character in value:
            codepoint = ord(character)
            if (
                codepoint <= 0x1F
                or codepoint == 0x7F
                or codepoint in (0x2028, 0x2029)
                or 0xD800 <= codepoint <= 0xDFFF
            ):
                raise ValueError("PARAMETER_VALUE_FORBIDDEN_CHARACTER")
    validator = Draft202012Validator(parameter_schema, format_checker=FormatChecker())
    if list(validator.iter_errors(parameters)):
        raise ValueError("UNSAFE_PARAMETER")
    for name, definition in parameter_schema["properties"].items():
        pattern = definition["pattern"]
        if re.fullmatch(pattern[1:-1], parameters[name]) is None:
            raise ValueError("UNSAFE_PARAMETER")


def resolved_argv(command, parameters):
    argv = []
    for token in command["argv"]:
        placeholder = PLACEHOLDER_TOKEN.fullmatch(token)
        argv.append(parameters[placeholder.group(1)] if placeholder else token)
    if any("{{" in token or "}}" in token for token in argv):
        raise InvalidStateError([
            validation_error("UNRESOLVED_PLACEHOLDER", message="resolved argv contains a placeholder marker")
        ])
    return argv


def length_prefixed_frame(label, value):
    if not isinstance(label, str) or not isinstance(value, str):
        raise InvalidStateError([validation_error("FINGERPRINT_FRAME_INVALID", message="fingerprint frames require strings")])
    label_bytes = label.encode("utf-8")
    value_bytes = value.encode("utf-8")
    return struct.pack(">Q", len(label_bytes)) + label_bytes + struct.pack(">Q", len(value_bytes)) + value_bytes


def argv_hash(argv):
    if not isinstance(argv, list) or any(not isinstance(token, str) for token in argv):
        raise InvalidStateError([validation_error("ARGV_FINGERPRINT_INVALID", message="argv must be a string array")])
    framed = b"".join(length_prefixed_frame(f"argv[{index}]", token) for index, token in enumerate(argv))
    return hashlib.sha256(framed).hexdigest()


def normalized_relative_directory(root, value):
    if not isinstance(value, str) or not value or "\\" in value or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", value):
        raise InvalidStateError([validation_error("WORKING_DIRECTORY_INVALID", message="working directory is invalid")])
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise InvalidStateError([validation_error("WORKING_DIRECTORY_INVALID", message="working directory escapes repository")])
    repository_root = Path(root).resolve(strict=True)
    try:
        resolved = (repository_root / candidate).resolve(strict=True)
        relative = resolved.relative_to(repository_root)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error("WORKING_DIRECTORY_INVALID", message="working directory is unavailable")]) from error
    if not resolved.is_dir():
        raise InvalidStateError([validation_error("WORKING_DIRECTORY_INVALID", message="working directory is not a directory")])
    return "." if not relative.parts else relative.as_posix()


def validate_input_pattern(pattern):
    if not isinstance(pattern, str) or not pattern or "\\" in pattern:
        raise InvalidStateError([validation_error("INPUT_PATH_GRAMMAR_INVALID", message="input path grammar is invalid")])
    if pattern.startswith("/") or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", pattern):
        raise InvalidStateError([validation_error("INPUT_PATH_GRAMMAR_INVALID", message="input path must be repository relative")])
    parts = pattern.split("/")
    if any(part in ("", ".", "..") for part in parts):
        raise InvalidStateError([validation_error("INPUT_PATH_GRAMMAR_INVALID", message="input path contains an invalid component")])
    recursive = pattern.endswith("/**")
    prefix = pattern[:-3] if recursive else pattern
    if not prefix or any(character in prefix for character in INPUT_GLOB_CHARACTERS):
        raise InvalidStateError([validation_error("INPUT_PATH_GRAMMAR_INVALID", message="input path uses unsupported glob syntax")])
    if not recursive and any(character in pattern for character in INPUT_GLOB_CHARACTERS):
        raise InvalidStateError([validation_error("INPUT_PATH_GRAMMAR_INVALID", message="literal input path contains glob syntax")])
    return prefix, recursive


def stable_file_facts(root, path):
    try:
        before = path.lstat()
        if path_is_link_or_reparse(path, before) or not stat.S_ISREG(before.st_mode):
            raise InvalidStateError([validation_error("INPUT_PATH_NOT_REGULAR", message="input path is not a regular file")])
        with path.open("rb") as handle:
            content = handle.read()
        after = path.lstat()
    except InvalidStateError:
        raise
    except OSError as error:
        raise InvalidStateError([validation_error("INPUT_PATH_READ_FAILED", message="input path could not be read consistently")]) from error
    identity = lambda item: (
        item.st_size, getattr(item, "st_mtime_ns", None), getattr(item, "st_dev", None), getattr(item, "st_ino", None),
    )
    if identity(before) != identity(after) or len(content) != after.st_size:
        raise InvalidStateError([validation_error("INPUT_PATH_CHANGED", message="input path changed while fingerprinting")])
    relative = path.relative_to(Path(root).resolve(strict=True)).as_posix()
    return relative, len(content), hashlib.sha256(content).hexdigest()


def contained_input_path(root, relative):
    repository_root = Path(root).resolve(strict=True)
    candidate = repository_root / relative
    current = repository_root
    for part in Path(relative).parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return candidate, False
        except OSError as error:
            raise InvalidStateError([validation_error("INPUT_PATH_STAT_FAILED", message="input path cannot be inspected")]) from error
        if path_is_link_or_reparse(current, metadata):
            raise InvalidStateError([validation_error("INPUT_PATH_SYMLINK", message="input paths cannot contain links")])
    try:
        candidate.resolve(strict=True).relative_to(repository_root)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error("INPUT_PATH_ESCAPE", message="input path escapes repository")]) from error
    return candidate, True


def recursive_input_files(root, prefix):
    directory, exists = contained_input_path(root, prefix)
    if not exists:
        return []
    try:
        metadata = directory.lstat()
    except OSError as error:
        raise InvalidStateError([validation_error("INPUT_PATH_STAT_FAILED", message="input directory cannot be inspected")]) from error
    if not stat.S_ISDIR(metadata.st_mode):
        raise InvalidStateError([validation_error("INPUT_PATH_NOT_DIRECTORY", message="recursive input prefix is not a directory")])
    files = []
    try:
        for current, directories, names in os.walk(directory, topdown=True, followlinks=False):
            current_path = Path(current)
            for name in tuple(directories) + tuple(names):
                child = current_path / name
                child_metadata = child.lstat()
                if path_is_link_or_reparse(child, child_metadata):
                    raise InvalidStateError([validation_error("INPUT_PATH_SYMLINK", message="recursive input tree contains a link")])
            for name in names:
                child = current_path / name
                child_metadata = child.lstat()
                if not stat.S_ISREG(child_metadata.st_mode):
                    raise InvalidStateError([validation_error("INPUT_PATH_NOT_REGULAR", message="recursive input match is not regular")])
                files.append(child)
    except InvalidStateError:
        raise
    except OSError as error:
        raise InvalidStateError([validation_error("INPUT_PATH_STAT_FAILED", message="recursive input tree cannot be inspected")]) from error
    return sorted(files, key=lambda path: path.relative_to(Path(root).resolve(strict=True)).as_posix().encode("utf-8"))


def input_fingerprint(root, command):
    repository_root = Path(root).resolve(strict=True)
    working_directory = normalized_relative_directory(repository_root, command.get("workingDirectory"))
    frames = [
        length_prefixed_frame("commandId", command.get("id")),
        length_prefixed_frame("workingDirectory", working_directory),
    ]
    for index, pattern in enumerate(command.get("inputPaths", [])):
        prefix, recursive = validate_input_pattern(pattern)
        frames.append(length_prefixed_frame(f"inputPaths[{index}]", pattern))
        if recursive:
            matches = recursive_input_files(repository_root, prefix)
        else:
            literal, exists = contained_input_path(repository_root, prefix)
            if not exists:
                raise InvalidStateError([validation_error("INPUT_LITERAL_MISSING", message="literal input path does not exist")])
            matches = [literal]
        if not matches:
            frames.append(length_prefixed_frame("NO_MATCH", pattern))
        for path in matches:
            relative, size, sha256 = stable_file_facts(repository_root, path)
            frames.extend((
                length_prefixed_frame("path", relative),
                length_prefixed_frame("size", str(size)),
                length_prefixed_frame("sha256", sha256),
            ))
    return hashlib.sha256(b"".join(frames)).hexdigest()


def child_environment(source):
    if not hasattr(source, "get"):
        raise InvalidStateError([validation_error("CHILD_ENVIRONMENT_INVALID", message="environment source must be a mapping")])
    environment = {}
    for key in CHILD_ENVIRONMENT_ALLOWLIST:
        value = source.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or "\x00" in value or "\n" in value or "\r" in value:
            raise InvalidStateError([validation_error("CHILD_ENVIRONMENT_INVALID", message="allowlisted environment value is invalid")])
        environment[key] = value
    return environment


def environment_fingerprint(environment):
    if not isinstance(environment, dict) or any(not isinstance(key, str) or not isinstance(value, str) for key, value in environment.items()):
        raise InvalidStateError([validation_error("CHILD_ENVIRONMENT_INVALID", message="environment fingerprint requires a string map")])
    frames = [length_prefixed_frame(key, environment[key]) for key in sorted(environment)]
    return hashlib.sha256(b"".join(frames)).hexdigest()


def host_is_posix():
    return os.name == "posix"


def posix_shell_available():
    shell = Path("/bin/sh")
    try:
        metadata = shell.stat()
    except OSError:
        return False
    return stat.S_ISREG(metadata.st_mode) and os.access(shell, os.X_OK)


def launch_reserved(argv, cwd, env):
    process = subprocess.Popen(
        argv,
        cwd=cwd,
        env=env,
        shell=False,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    process._workflow_pgid = process.pid
    return process


def launched_process_group_id(process):
    pid = getattr(process, "pid", None)
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        raise ProcessGroupError("launched process PID is invalid")
    preserved = getattr(process, "_workflow_pgid", None)
    if isinstance(preserved, int) and not isinstance(preserved, bool):
        if preserved != pid or preserved <= 0:
            raise ProcessGroupError("preserved process group identity is invalid")
        return preserved
    if authoritative_process_exit(process) is not None:
        raise ProcessGroupError("process group identity was not preserved before leader exit")
    try:
        observed = os.getpgid(pid)
    except (AttributeError, OSError, TypeError) as error:
        raise ProcessGroupError("process group identity could not be verified") from error
    if observed != pid:
        raise ProcessGroupError("process no longer leads its launched process group")
    process._workflow_pgid = observed
    return observed


def process_group_exists(pgid):
    if not isinstance(pgid, int) or isinstance(pgid, bool) or pgid <= 0:
        raise ProcessGroupError("process group identity is invalid")
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise ProcessGroupError("process group existence could not be verified") from error


def wait_for_process_group_disappearance(pgid, timeout):
    deadline = time.monotonic() + timeout
    while process_group_exists(pgid):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(0.01, remaining))
    return True


def reap_process_group_leader(process, timeout):
    try:
        process.wait(timeout=timeout)
    except subprocess.TimeoutExpired as error:
        raise ProcessGroupError("process group leader could not be reaped") from error
    except (AttributeError, OSError, TypeError, ValueError) as error:
        if authoritative_process_exit(process) is None:
            raise ProcessGroupError("process group leader reap failed") from error


def terminate_process_group(process, grace_seconds):
    if not isinstance(grace_seconds, (int, float)) or isinstance(grace_seconds, bool) or grace_seconds <= 0:
        raise ProcessGroupError("process group grace period is invalid")
    try:
        pgid = launched_process_group_id(process)
        if not process_group_exists(pgid):
            reap_process_group_leader(process, grace_seconds)
            return
        os.killpg(pgid, signal.SIGTERM)
        if wait_for_process_group_disappearance(pgid, grace_seconds):
            reap_process_group_leader(process, grace_seconds)
            return
        os.killpg(pgid, getattr(signal, "SIGKILL", 9))
        if not wait_for_process_group_disappearance(pgid, grace_seconds):
            raise ProcessGroupError("process group did not disappear after SIGKILL")
        reap_process_group_leader(process, grace_seconds)
    except ProcessGroupError:
        raise
    except (AttributeError, OSError, TypeError, ValueError) as error:
        raise ProcessGroupError("process group termination failed") from error


def authoritative_process_exit(process):
    try:
        exit_code = process.poll()
    except Exception:
        exit_code = getattr(process, "returncode", None)
    return exit_code if isinstance(exit_code, int) and not isinstance(exit_code, bool) else None


def wait_for_process_exit(process, argv, lifecycle_deadline):
    remaining = lifecycle_deadline - time.monotonic()
    failure = None
    exit_code = None
    if remaining <= 0:
        failure = subprocess.TimeoutExpired(argv, EXECUTION_TIMEOUT_SECONDS)
    else:
        try:
            exit_code = process.wait(timeout=remaining)
        except Exception as error:
            failure = error
    if failure is None:
        if isinstance(exit_code, int) and not isinstance(exit_code, bool):
            return exit_code
        exit_code = authoritative_process_exit(process)
        if exit_code is not None:
            return exit_code
        failure = RuntimeError("process exit status is unavailable")

    reason = (
        "execution lifecycle timed out"
        if isinstance(failure, subprocess.TimeoutExpired)
        else "execution lifecycle final wait failed"
    )
    if authoritative_process_exit(process) is None:
        try:
            terminate_process_group(process, PROCESS_GROUP_GRACE_SECONDS)
        except ProcessGroupError as termination_error:
            reason += f"; {termination_error}"
    raise ExecutionLifecycleTimeout(reason) from failure


def execution_working_directory(root, relative):
    if not isinstance(relative, str) or not relative or "\\" in relative:
        raise InvalidStateError([validation_error(
            "EXECUTION_WORKING_DIRECTORY_INVALID", message="execution working directory is invalid",
        )])
    try:
        repository_root = Path(root).resolve(strict=True)
        working_directory = (repository_root / relative).resolve(strict=True)
        working_directory.relative_to(repository_root)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error(
            "EXECUTION_WORKING_DIRECTORY_INVALID", message="execution working directory escapes repository",
        )]) from error
    if not working_directory.is_dir():
        raise InvalidStateError([validation_error(
            "EXECUTION_WORKING_DIRECTORY_INVALID", message="execution working directory is not a directory",
        )])
    return working_directory


def execution_process_attempt(data, *, started_at, ended_at, launch_status, process_exit_code,
                              termination, redaction_status, reason):
    run_id = data["runId"]
    command_id = data["commandId"]
    attempt_id = data["attemptId"]
    return {
        "$schema": "ai/schemas/process-attempt.schema.json",
        "$id": f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json",
        "schemaVersion": 1,
        "runId": run_id,
        "commandId": command_id,
        "attemptId": attempt_id,
        "reservedAt": data["reservedAt"],
        "startedAt": started_at,
        "endedAt": ended_at,
        "argvHash": data["argvHash"],
        "inputFingerprint": data["inputFingerprint"],
        "environmentFingerprint": data["environmentFingerprint"],
        "workingDirectory": data["workingDirectory"],
        "launchStatus": launch_status,
        "processExitCode": process_exit_code,
        "termination": termination,
        "redactionStatus": redaction_status,
        "reason": reason,
    }


def execute_command(root, request):
    root = Path(root).resolve()
    required = {"runId", "commandId"}
    allowed = required | {"parametersPath", "rerunReasonPath", "approvalRef"}
    if not isinstance(request, dict) or not required.issubset(request) or not set(request).issubset(allowed):
        preflight, preflight_status = run_current_preflight(root)
        if preflight_status != 0:
            result = gateway_result(
                preflight["result"], preflight["reason"], operation="PRE_COMMAND", errors=preflight["errors"],
            )
            published, published_status = publish_result(root, result, preflight_status)
            return published, published_status, None
        result, status = pre_command_result("POLICY_VIOLATION", "EXECUTE_COMMAND_REQUEST_INVALID", 4)
        return result, status, None

    policy_result, policy_status = pre_command(
        root,
        request["runId"],
        request["commandId"],
        parameters_path=request.get("parametersPath"),
        rerun_reason_path=request.get("rerunReasonPath"),
        approval_ref=request.get("approvalRef"),
        source_environment=os.environ,
        reserve=False,
    )
    if (
        policy_status != 0
        or policy_result.get("operation") != "PRE_COMMAND"
        or policy_result.get("result") != "PASS"
    ):
        return policy_result, policy_status, None
    if not host_is_posix():
        result, status = pre_command_result("NOT_CONFIGURED", "POSIX_EXECUTION_NOT_CONFIGURED", 3)
        return result, status, None
    try:
        environment = child_environment(os.environ)
    except InvalidStateError:
        result, status = pre_command_result("INVALID_STATE", "CHILD_ENVIRONMENT_INVALID", 5)
        return result, status, None
    if not environment.get("PATH"):
        result, status = pre_command_result("NOT_CONFIGURED", "CHILD_PATH_NOT_CONFIGURED", 3)
        return result, status, None
    if not posix_shell_available():
        result, status = pre_command_result("NOT_CONFIGURED", "POSIX_SHELL_NOT_CONFIGURED", 3)
        return result, status, None

    result, status = pre_command(
        root,
        request["runId"],
        request["commandId"],
        parameters_path=request.get("parametersPath"),
        rerun_reason_path=request.get("rerunReasonPath"),
        approval_ref=request.get("approvalRef"),
        source_environment=environment,
    )
    if status != 0 or result.get("operation") != "PRE_COMMAND" or result.get("result") != "PASS":
        return result, status, None
    data = result.get("data")
    if isinstance(data, dict) and "reservedAt" not in data:
        try:
            session = active_open_session(root, data.get("runId"))
            matches = [item for item in session["reservations"] if (
                item["commandId"], item["attemptId"]
            ) == (data.get("commandId"), data.get("attemptId"))]
            if len(matches) != 1 or any(matches[0].get(name) != data.get(name) for name in (
                "argvHash", "inputFingerprint", "environmentFingerprint",
            )):
                raise InvalidStateError([validation_error(
                    "PROCESS_RESERVATION_MISMATCH", message="execution reservation could not be proven",
                )])
            data = dict(data, reservedAt=matches[0]["reservedAt"])
        except (InvalidStateError, OSError, TypeError, ValueError):
            invalid, invalid_status = pre_command_result("INVALID_STATE", "PROCESS_RESERVATION_MISMATCH", 5)
            return invalid, invalid_status, None
    argv = data.get("argv") if isinstance(data, dict) else None
    if not isinstance(argv, list) or not argv or any(not isinstance(token, str) or not token for token in argv):
        invalid, invalid_status = pre_command_result("INVALID_STATE", "EXECUTION_ARGV_INVALID", 5)
        return invalid, invalid_status, None
    try:
        working_directory = execution_working_directory(root, data.get("workingDirectory"))
    except InvalidStateError as error:
        invalid, invalid_status = pre_command_result(
            "INVALID_STATE", "EXECUTION_WORKING_DIRECTORY_INVALID", 5, errors=error.errors,
        )
        return invalid, invalid_status, None
    started_at = utc_now()
    try:
        process = launch_reserved(argv, working_directory, environment)
    except OSError:
        attempt = execution_process_attempt(
            data, started_at=None, ended_at=utc_now(), launch_status="SPAWN_FAILED",
            process_exit_code=None, termination="SPAWN_FAILED", redaction_status="NOT_APPLIED",
            reason="SPAWN_FAILED",
        )
        return post_command(root, attempt)
    lifecycle_deadline = time.monotonic() + EXECUTION_TIMEOUT_SECONDS
    try:
        captured = capture_and_scrub(process, lifecycle_deadline=lifecycle_deadline)
        exit_code = wait_for_process_exit(process, argv, lifecycle_deadline)
        attempt = execution_process_attempt(
            data, started_at=started_at, ended_at=utc_now(), launch_status="LAUNCHED",
            process_exit_code=exit_code, termination="EXITED", redaction_status="SCRUBBED", reason=None,
        )
        return post_command(root, attempt, captured)
    except (ExecutionLifecycleTimeout, CaptureResourceLimit) as error:
        termination = "TIMED_OUT" if isinstance(error, ExecutionLifecycleTimeout) else "RESOURCE_LIMIT"
        exit_code = authoritative_process_exit(process)
        attempt = execution_process_attempt(
            data, started_at=started_at, ended_at=utc_now(), launch_status="LAUNCHED",
            process_exit_code=exit_code, termination=termination, redaction_status="NOT_APPLIED",
            reason=str(error) or termination,
        )
        return post_command(root, attempt)
    except RedactionUncertainty as error:
        exit_code = authoritative_process_exit(process)
        termination_error = None
        if exit_code is None:
            try:
                terminate_process_group(process, PROCESS_GROUP_GRACE_SECONDS)
            except ProcessGroupError as cleanup_error:
                termination_error = cleanup_error
            exit_code = authoritative_process_exit(process)
        reason = f"REDACTION_UNCERTAINTY: {str(error) or 'captured evidence could not be scrubbed'}"
        if exit_code is None:
            termination = "TIMED_OUT"
            redaction_status = "NOT_APPLIED"
            if termination_error is None:
                reason += "; PROCESS_EXIT_UNAVAILABLE_AFTER_CLEANUP"
            else:
                reason += f"; PROCESS_GROUP_TERMINATION_FAILED: {termination_error}"
        else:
            termination = "EXITED"
            redaction_status = "UNSCRUBBED"
        attempt = execution_process_attempt(
            data, started_at=started_at, ended_at=utc_now(), launch_status="LAUNCHED",
            process_exit_code=exit_code, termination=termination, redaction_status=redaction_status,
            reason=reason,
        )
        return post_command(root, attempt)


def resolve_command(root, project_state_path, registry_path, command_id, parameters_path=None):
    """Resolve a registered command without preflight recording or project execution."""
    root = Path(root).resolve()
    try:
        validate_repository_instance(root, project_state_path)
        registry = validate_repository_instance(root, registry_path)
        prerequisite_order = validate_registry_semantics(root, registry)
    except RegistryBlockedError as error:
        return resolve_result("BLOCKED", error.errors[0]["code"], 2, errors=error.errors)
    except InvalidStateError as error:
        return resolve_result("INVALID_STATE", error.errors[0]["code"], 5, errors=error.errors)

    if not isinstance(command_id, str) or COMMAND_ID.fullmatch(command_id) is None:
        return policy_violation("MALFORMED_COMMAND_ID")
    command = next((item for item in registry["commands"] if item["id"] == command_id), None)
    if command is None:
        return resolve_result("NOT_CONFIGURED", "COMMAND_NOT_CONFIGURED", 3)

    configuration_status = command["configurationStatus"]
    if configuration_status in ("UNKNOWN", "STALE", "UNCERTAIN"):
        return resolve_result("BLOCKED", "COMMAND_CONFIGURATION_BLOCKED", 2)
    if configuration_status == "NOT_CONFIGURED" or command["classification"] == "UNAVAILABLE":
        return resolve_result("NOT_CONFIGURED", "COMMAND_NOT_CONFIGURED", 3)
    if command["classification"] in ("RISKY", "DESTRUCTIVE"):
        return resolve_result("BLOCKED", "COMMAND_CLASSIFICATION_BLOCKED", 2)

    parameter_specification = command["parameters"]
    if not parameter_specification["allowed"]:
        if parameters_path is not None:
            return policy_violation("PARAMETERS_NOT_ALLOWED")
        parameters = {}
    else:
        if parameters_path is None:
            return policy_violation("PARAMETERS_REQUIRED")
        try:
            parameters = read_parameter_object(root, parameters_path)
            validate_parameter_values(parameter_specification["schema"], parameters)
        except ValueError as error:
            return policy_violation(str(error))

    try:
        argv = resolved_argv(command, parameters)
    except InvalidStateError as error:
        return resolve_result("INVALID_STATE", error.errors[0]["code"], 5, errors=error.errors)

    prerequisites = prerequisite_order[command_id]
    if prerequisites:
        return resolve_result("BLOCKED", "PREREQUISITES_PENDING", 2, {"prerequisiteIds": prerequisites})

    try:
        repository_root = Path(root).resolve(strict=True)
        working_directory = (repository_root / command["workingDirectory"]).resolve(strict=True)
        working_directory.relative_to(repository_root)
        if not working_directory.is_dir():
            raise ValueError
    except (OSError, ValueError):
        return resolve_result("INVALID_STATE", "WORKING_DIRECTORY_OUTSIDE_REPOSITORY", 5)
    return resolve_result(
        "PASS",
        None,
        0,
        {
            "commandId": command["id"],
            "classification": command["classification"],
            "workingDirectory": command["workingDirectory"],
            "argv": argv,
            "prerequisiteIds": [],
        },
    )


def resolve_output_path(root, output):
    if not isinstance(output, str) or not output:
        raise ValueError("RESOLVE_OUTPUT_PATH_INVALID")
    candidate = Path(output)
    if candidate.is_absolute() or len(candidate.parts) != 1:
        raise ValueError("RESOLVE_OUTPUT_PATH_INVALID")
    name = candidate.name
    if name.startswith(".") or candidate.suffix != ".json":
        raise ValueError("RESOLVE_OUTPUT_PATH_FORBIDDEN")
    try:
        repository_root = Path(root).resolve(strict=True)
        destination = repository_root / name
    except (OSError, ValueError) as error:
        raise ValueError("RESOLVE_OUTPUT_PATH_INVALID") from error
    if destination.exists() or destination.is_symlink():
        raise ValueError("RESOLVE_OUTPUT_PATH_EXISTS")
    return destination


def exclusive_write(path, content):
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    created = True
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        fsync_directory(path.parent)
        created = False
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if created:
            try:
                path.unlink()
            except FileNotFoundError:
                pass


def write_resolve_output(root, output, result):
    if output == "-":
        print(compact(result))
        return 0
    try:
        destination = resolve_output_path(root, output)
        exclusive_write(destination, compact(result) + "\n")
    except (OSError, ValueError):
        return 4
    return 0


def publish_resolve_output(root, output, result, status):
    published, published_status = publish_result(root, result, status)
    output_status = write_resolve_output(root, output, published)
    return published, published_status, output_status


def publish_result(root, result, status):
    schema_path = "ai/schemas/gateway-result.schema.json"
    try:
        validate(root, result, schema_path)
        return result, status
    except Exception:
        operation = result.get("operation") if isinstance(result, dict) else None
        if operation not in GATEWAY_OPERATIONS:
            operation = "PREFLIGHT"
        fallback = {
            "$schema": "ai/schemas/gateway-result.schema.json",
            "$id": "ai/gateway-result.json",
            "schemaVersion": 1,
            "operation": operation,
            "result": "INVALID_STATE",
            "reason": "GATEWAY_RESULT_SCHEMA_INVALID",
            "errors": [],
            "data": None,
        }
        try:
            validate(root, fallback, schema_path)
        except Exception:
            # A malformed gateway schema cannot validate any structured outcome.
            # Do not preserve a lower-severity result when that control-plane state fails.
            pass
        return fallback, 5


def utc_now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def digest(path):
    hasher = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def fsync_directory(path):
    flags = os.O_RDONLY
    if hasattr(os, "O_DIRECTORY"):
        flags |= os.O_DIRECTORY
    try:
        descriptor = os.open(path, flags)
    except OSError as error:
        # Windows does not expose fsync-capable directory descriptors. EINVAL and
        # ENOTSUP/EOPNOTSUPP are the documented unsupported-operation fallbacks.
        if error.errno in DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS or (os.name == "nt" and error.errno in (errno.EACCES, errno.EPERM)):
            return
        raise
    try:
        os.fsync(descriptor)
    except OSError as error:
        if error.errno in DIRECTORY_FSYNC_UNSUPPORTED_ERRNOS:
            return
        raise
    finally:
        os.close(descriptor)


def atomic_write(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        fsync_directory(path.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.recovery.", dir=destination.parent)
    try:
        with source.open("rb") as input_handle, os.fdopen(descriptor, "wb") as output_handle:
            shutil.copyfileobj(input_handle, output_handle)
            output_handle.flush()
            os.fsync(output_handle.fileno())
        os.replace(temporary, destination)
        fsync_directory(destination.parent)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def copy_backup(source, destination):
    with source.open("rb") as input_handle, destination.open("wb") as output_handle:
        shutil.copyfileobj(input_handle, output_handle)
        output_handle.flush()
        os.fsync(output_handle.fileno())


def remove_transaction(transaction):
    shutil.rmtree(transaction)
    fsync_directory(transaction.parent)


def validate_embedded(instance, schema):
    Draft202012Validator.check_schema(schema)
    errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(instance))
    if errors:
        raise InvalidTransaction("transaction metadata failed schema validation")


def parse_created_at(value):
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise InvalidTransaction("invalid transaction owner timestamp") from error
    if parsed.tzinfo is None:
        raise InvalidTransaction("transaction owner timestamp lacks timezone")
    return parsed.astimezone(dt.timezone.utc)


def owner_is_recent(owner):
    age = (dt.datetime.now(dt.timezone.utc) - parse_created_at(owner["createdAt"])).total_seconds()
    return age < TRANSACTION_MAX_RECENT_SECONDS


def owner_is_alive(pid):
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def read_owner(path):
    try:
        owner = read_json(path)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise InvalidTransaction("invalid transaction owner metadata") from error
    validate_embedded(owner, OWNER_SCHEMA)
    return owner


def transaction_directory_is_recent(transaction):
    modified = dt.datetime.fromtimestamp(transaction.stat().st_mtime, tz=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - modified).total_seconds() < TRANSACTION_MAX_RECENT_SECONDS


def load_prepared_transaction(root):
    transaction = root / "ai" / ".workflow-state-txn"
    journal = transaction / "journal.json"
    owner_path = transaction / "owner.json"
    try:
        journal_data = read_json(journal)
    except (OSError, ValueError, json.JSONDecodeError) as error:
        raise InvalidTransaction("invalid recovery journal") from error
    validate_embedded(journal_data, JOURNAL_SCHEMA)
    owner = read_owner(owner_path)
    if journal_data["owner"] != owner:
        raise InvalidTransaction("journal owner does not match lock owner")
    manifest = {item["target"]: item for item in journal_data["files"]}
    if len(manifest) != len(TRANSACTION_FILES) or set(manifest) != set(TRANSACTION_FILES):
        raise InvalidTransaction("transaction manifest is incomplete")
    for target_name, backup_name in TRANSACTION_FILES.items():
        item = manifest[target_name]
        if item["backup"] != backup_name:
            raise InvalidTransaction("transaction backup path mismatch")
        backup = transaction / backup_name
        if item["existed"]:
            if item["previousSha256"] is None or not backup.is_file():
                raise InvalidTransaction("transaction backup is missing")
            if digest(backup) != item["previousSha256"]:
                raise InvalidTransaction("transaction backup digest mismatch")
        elif item["previousSha256"] is not None or backup.exists():
            raise InvalidTransaction("unexpected transaction backup")
    return transaction, owner, manifest


def restore_prepared_transaction(root, transaction, manifest):
    for target_name, backup_name in TRANSACTION_FILES.items():
        target = root / target_name
        item = manifest[target_name]
        if item["existed"]:
            backup = transaction / backup_name
            atomic_copy(backup, target)
        else:
            target.unlink(missing_ok=True)
            fsync_directory(target.parent)
    for target_name in TRANSACTION_FILES:
        item = manifest[target_name]
        target = root / target_name
        if item["existed"] and digest(target) != item["previousSha256"]:
            raise InvalidTransaction("restored target digest mismatch")
    remove_transaction(transaction)


def recovery(root):
    transaction = root / "ai" / ".workflow-state-txn"
    if not transaction.exists():
        return
    if not transaction.is_dir() or transaction.is_symlink():
        raise InvalidTransaction("transaction lock is not a directory")
    journal = transaction / "journal.json"
    owner_path = transaction / "owner.json"
    if not journal.is_file():
        if owner_path.is_file():
            owner = read_owner(owner_path)
            if owner_is_alive(owner["pid"]) or owner_is_recent(owner):
                raise TransactionBlocked("transaction owner is active")
        elif transaction_directory_is_recent(transaction):
            raise TransactionBlocked("transaction lock is being prepared")
        raise InvalidTransaction("transaction has no prepared journal")
    transaction, owner, manifest = load_prepared_transaction(root)
    if owner_is_alive(owner["pid"]) or owner_is_recent(owner):
        raise TransactionBlocked("transaction owner is active")
    restore_prepared_transaction(root, transaction, manifest)


def acquire_transaction(root):
    transaction = root / "ai" / ".workflow-state-txn"
    for _attempt in range(2):
        try:
            transaction.mkdir(parents=True, exist_ok=False)
            fsync_directory(transaction.parent)
            break
        except FileExistsError:
            recovery(root)
    else:
        raise TransactionBlocked("transaction lock could not be acquired")
    owner = {"pid": os.getpid(), "createdAt": utc_now()}
    try:
        atomic_write(transaction / "owner.json", compact(owner) + "\n")
    except Exception:
        remove_transaction(transaction)
        raise
    return transaction, owner


def rollback_owned_transaction(root, expected_owner):
    transaction, owner, manifest = load_prepared_transaction(root)
    if owner != expected_owner:
        raise InvalidTransaction("writer no longer owns transaction")
    restore_prepared_transaction(root, transaction, manifest)


def summary_value(value):
    if value is None or value == "NOT_APPLICABLE":
        return "N/A"
    return str(value).replace("|", "\\|").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def summary_evidence(items):
    if not items:
        return "N/A"
    return "<br>".join(
        f"{summary_value(item['kind'])}: {summary_value(item['path'])} ({summary_value(item['claim'])})"
        for item in items
    )


def summary_for(existing_summary, state):
    project = state["project"]
    lines = [
        "## Generated State Summary",
        "",
        "Canonical source: `ai/project-state.json`",
        f"Schema version: `{state['schemaVersion']}`",
        f"Updated at: `{summary_value(state['updatedAt'])}`",
        "",
        "This section was manually bootstrapped from canonical JSON during Phase 1A.",
        "Automatic generation and stale-state validation begin in Phase 1B or later.",
        "This section cannot be changed independently of its canonical JSON source.",
        "",
        "### Project Summary",
        "",
        "| Field | Value |",
        "|---|---|",
        f"| Name | {summary_value(project['name'])} |",
        f"| Product Type | {summary_value(project['productType'])} |",
        f"| Main Language | {summary_value(project['mainLanguage'])} |",
        f"| Framework | {summary_value(project['framework'])} |",
        f"| Build System | {summary_value(project['buildSystem'])} |",
        "",
        "#### Facts",
        "",
        "| ID | Value | Confidence | Observed At | Evidence |",
        "|---|---|---|---|---|",
    ]
    lines.extend(
        f"| {summary_value(fact['id'])} | {summary_value(fact['value'])} | {summary_value(fact['confidence'])} | "
        f"{summary_value(fact['observedAt'])} | {summary_evidence(fact['evidence'])} |"
        for fact in state["facts"]
    )
    lines.extend([
        "",
        "### Important Paths",
        "",
        "| Purpose | Path |",
        "|---|---|",
    ])
    lines.extend(
        f"| {summary_value(item['purpose'])} | {summary_value(item['path'])} |"
        for item in state["importantPaths"]
    )
    lines.extend([
        "",
        "### Known Ports",
        "",
        "| Service | Port | Evidence |",
        "|---|---|---|",
    ])
    lines.extend(
        f"| {summary_value(port['service'])} | {port['value']} ({summary_value(port['confidence'])}) | "
        f"{summary_evidence(port['evidence'])} |"
        for port in state["ports"]
    )
    lines.extend([
        "",
        "### Environment State",
        "",
        "| Environment | Configuration Status | Notes |",
        "|---|---|---|",
    ])
    lines.extend(
        f"| {summary_value(environment['kind'])} | {summary_value(environment['configurationStatus'])} | "
        f"{'<br>'.join(summary_value(note) for note in environment['notes']) if environment['notes'] else 'N/A'} |"
        for environment in state["environments"]
    )
    lines.extend([
        "",
        "### Helper Runtime State",
        "",
        "| Environment | Target | Detected | Configuration Status | Version | Evidence |",
        "|---|---|---|---|---|---|",
    ])
    lines.extend(
        f"| {summary_value(runtime['environment'])} | {summary_value(runtime['targetRuntime'])} | "
        f"{summary_value(runtime['detectedRuntime'])} | {summary_value(runtime['configurationStatus'])} | "
        f"{summary_value(runtime['version'])} | {summary_evidence(runtime['evidence'])} |"
        for runtime in state["helperRuntimes"]
    )
    lines.extend([
        "",
        "### Command Registry Reference",
        "",
        f"- `{state['commandRegistryRef']}`",
        "",
        "### Cache Invalidation Inputs",
        "",
    ])
    lines.extend(f"- `{path}`" for path in state["cacheInvalidationInputs"])
    generated = "\n".join(lines) + "\n"
    start = "<!-- GENERATED:START source=ai/project-state.json -->"
    end = "<!-- GENERATED:END source=ai/project-state.json -->"
    start_index = existing_summary.index(start) + len(start)
    end_index = existing_summary.index(end, start_index)
    return existing_summary[:start_index] + "\n" + generated + existing_summary[end_index:]


def current_evidence(runtime_command, version, jsonschema_version, interpreter_hash):
    return {
        "environment": "LOCAL",
        "targetRuntime": "Python 3",
        "detectedRuntime": "Python 3",
        "runtimeCommand": runtime_command,
        "version": version,
        "jsonschemaVersion": jsonschema_version,
        "validator": "Draft202012Validator",
        "formatChecker": True,
        "interpreterSha256": interpreter_hash,
        "observedAt": utc_now(),
    }


def evidence_matches(previous, candidate):
    keys = ("environment", "targetRuntime", "detectedRuntime", "runtimeCommand", "version", "jsonschemaVersion", "validator", "formatChecker", "interpreterSha256")
    return all(previous.get(key) == candidate.get(key) for key in keys)


def record(root, evidence):
    transaction, owner = acquire_transaction(root)
    try:
        evidence_path = root / "ai" / "evidence" / "local-helper-runtime.json"
        state_path = root / "ai" / "project-state.json"
        summary_path = root / "ai" / "project-state.md"
        project_schema = "ai/schemas/project-state.schema.json"
        evidence_schema = "ai/schemas/helper-runtime-evidence.schema.json"
        previous_evidence = read_json(evidence_path) if evidence_path.is_file() else None
        if previous_evidence is not None:
            validate(root, previous_evidence, evidence_schema)
            if evidence_matches(previous_evidence, evidence):
                evidence = previous_evidence
        state = read_json(state_path)
        existing_summary = summary_path.read_text(encoding="utf-8")
        local_runtime = next(item for item in state["helperRuntimes"] if item["environment"] == "LOCAL")
        local_runtime.update({
            "detectedRuntime": "Python 3",
            "configurationStatus": "VERIFIED",
            "version": evidence["version"],
            "evidence": [{"kind": "RUNTIME_COMMAND", "path": "ai/evidence/local-helper-runtime.json", "claim": "Local Python 3 helper runtime passed the Phase 1B preflight."}],
        })
        local_environment = next(item for item in state["environments"] if item["kind"] == "LOCAL")
        local_environment["configurationStatus"] = "VERIFIED"
        local_environment["notes"] = ["Local Python 3 helper runtime passed the recorded Phase 1B preflight."]
        state["updatedAt"] = evidence["observedAt"]
        validate(root, evidence, evidence_schema)
        validate(root, state, project_schema)
        summary = summary_for(existing_summary, state)
        targets = {
            evidence_path: transaction / "local-helper-runtime.json.backup",
            state_path: transaction / "project-state.json.backup",
            summary_path: transaction / "project-state.md.backup",
        }
        contents = {
            evidence_path: compact(evidence) + "\n",
            state_path: json.dumps(state, indent=2) + "\n",
            summary_path: summary,
        }
        if (
            not os.environ.get("AI_WORKFLOW_TEST_FAIL_AFTER_STAGE")
            and all(target.is_file() and target.read_text(encoding="utf-8") == content for target, content in contents.items())
        ):
            remove_transaction(transaction)
            return
        journal_data = {
            "version": 1,
            "stage": "PREPARED",
            "owner": owner,
            "files": [
                {
                    "target": target.relative_to(root).as_posix(),
                    "backup": backup.name,
                    "existed": target.is_file(),
                    "previousSha256": digest(target) if target.is_file() else None,
                    "intendedSha256": hashlib.sha256(contents[target].encode("utf-8")).hexdigest(),
                }
                for target, backup in targets.items()
            ],
        }
        validate_embedded(journal_data, JOURNAL_SCHEMA)
        for target, backup in targets.items():
            if target.is_file():
                copy_backup(target, backup)
        fsync_directory(transaction)
        atomic_write(transaction / "journal.json", compact(journal_data) + "\n")
        hold_path = os.environ.get("AI_WORKFLOW_TEST_HOLD_AFTER_PREPARED")
        if hold_path:
            deadline = time.monotonic() + 30
            while not Path(hold_path).is_file():
                if time.monotonic() >= deadline:
                    raise TimeoutError("test writer release timed out")
                time.sleep(0.05)
        atomic_write(evidence_path, contents[evidence_path])
        if os.environ.get("AI_WORKFLOW_TEST_FAIL_AFTER_STAGE") == "1":
            raise ValueError("test failure")
        atomic_write(state_path, contents[state_path])
        atomic_write(summary_path, contents[summary_path])
        manifest = {item["target"]: item for item in journal_data["files"]}
        for target_name, item in manifest.items():
            if digest(root / target_name) != item["intendedSha256"]:
                raise ValueError("transaction target digest mismatch")
        remove_transaction(transaction)
    except Exception as error:
        if (transaction / "journal.json").is_file():
            try:
                rollback_owned_transaction(root, owner)
            except Exception as rollback_error:
                raise InvalidTransaction("owned transaction could not be safely rolled back") from rollback_error
        else:
            try:
                current_owner = read_owner(transaction / "owner.json")
            except Exception as owner_error:
                raise InvalidTransaction("unprepared transaction ownership is invalid") from owner_error
            if current_owner != owner:
                raise InvalidTransaction("unprepared transaction ownership changed")
            remove_transaction(transaction)
        raise error


def run_preflight(arguments):
    root = Path(arguments.repository_root).resolve()
    if sys.version_info.major != 3 or jsonschema is None:
        return gateway_result("NOT_CONFIGURED", "helper runtime unavailable"), 3
    if getattr(arguments, "invalid_arguments", False):
        return publish_result(root, gateway_result("INVALID_STATE", "INVALID_PREFLIGHT_ARGUMENTS"), 5)
    interpreter = Path(sys.executable)
    if not interpreter.is_file():
        return publish_result(root, gateway_result("INVALID_STATE", "INVALID_INTERPRETER"), 5)
    try:
        jsonschema_version = package_version("jsonschema")
    except Exception:
        return publish_result(root, gateway_result("NOT_CONFIGURED", "JSONSCHEMA_METADATA_UNAVAILABLE"), 3)
    runtime = {
        "runtimeCommand": arguments.runtime_command,
        "runtimeExecutableHash": digest(interpreter),
        "pythonVersion": sys.version,
        "jsonschemaVersion": jsonschema_version,
        "validator": "Draft202012Validator",
        "formatChecker": True,
    }
    result = gateway_result("PASS", None, runtime)
    preflight_result, preflight_status = publish_result(root, result, 0)
    if preflight_status != 0:
        return preflight_result, preflight_status
    try:
        recovery(root)
        if arguments.record:
            record(root, current_evidence(arguments.runtime_command, sys.version, jsonschema_version, runtime["runtimeExecutableHash"]))
    except TransactionBlocked:
        return publish_result(root, gateway_result("BLOCKED", "STATE_TRANSACTION_ACTIVE"), 2)
    except InvalidTransaction:
        if os.environ.get("AI_WORKFLOW_TEST_DIAGNOSTIC") == "1":
            traceback.print_exc()
        return publish_result(root, gateway_result("INVALID_STATE", "INVALID_TRANSACTION_STATE"), 5)
    except Exception:
        if os.environ.get("AI_WORKFLOW_TEST_DIAGNOSTIC") == "1":
            traceback.print_exc()
        return publish_result(root, gateway_result("INVALID_STATE", "STATE_RECORDING_FAILED"), 5)
    return publish_result(root, result, 0)


def current_preflight_invalid(root, error):
    errors = error.errors if isinstance(error, InvalidStateError) else [
        validation_error("CURRENT_HELPER_RUNTIME_STATE_INVALID", message="current helper runtime state is malformed")
    ]
    return publish_result(
        root,
        gateway_result("INVALID_STATE", errors[0]["code"], errors=errors),
        5,
    )


def run_current_preflight(repository_root):
    root = Path(repository_root).resolve()
    if sys.version_info.major != 3 or jsonschema is None:
        return publish_result(root, gateway_result("NOT_CONFIGURED", "helper runtime unavailable"), 3)
    interpreter = Path(sys.executable)
    if not interpreter.is_file():
        return publish_result(root, gateway_result("INVALID_STATE", "INVALID_INTERPRETER"), 5)
    try:
        jsonschema_version = package_version("jsonschema")
        format_checker = FormatChecker()
    except Exception:
        return publish_result(root, gateway_result("NOT_CONFIGURED", "JSONSCHEMA_METADATA_UNAVAILABLE"), 3)
    current = {
        "environment": "LOCAL",
        "targetRuntime": "Python 3",
        "detectedRuntime": "Python 3",
        "version": sys.version,
        "jsonschemaVersion": jsonschema_version,
        "validator": Draft202012Validator.__name__,
        "formatChecker": isinstance(format_checker, FormatChecker),
        "interpreterSha256": digest(interpreter),
    }
    evidence_path = root / "ai" / "evidence" / "local-helper-runtime.json"
    state_path = root / "ai" / "project-state.json"
    try:
        recovery(root)
    except TransactionBlocked:
        return publish_result(root, gateway_result("BLOCKED", "STATE_TRANSACTION_ACTIVE"), 2)
    except InvalidTransaction as error:
        return current_preflight_invalid(root, error)
    if not evidence_path.is_file() or not state_path.is_file():
        return publish_result(root, gateway_result("BLOCKED", "HELPER_RUNTIME_STATE_MISSING"), 2)
    try:
        evidence_file = resolve_repository_file(root, evidence_path)
        evidence = read_json(evidence_file)
        validate(root, evidence, "ai/schemas/helper-runtime-evidence.schema.json")
        state = validate_repository_instance(root, state_path)
    except InvalidStateError as error:
        return current_preflight_invalid(root, error)
    except Exception as error:
        return current_preflight_invalid(root, error)

    local_environments = [item for item in state["environments"] if item["kind"] == "LOCAL"]
    local_runtimes = [item for item in state["helperRuntimes"] if item["environment"] == "LOCAL"]
    if len(local_environments) > 1 or len(local_runtimes) > 1:
        return current_preflight_invalid(root, ValueError("duplicate LOCAL runtime state"))
    if not local_environments or not local_runtimes:
        return publish_result(root, gateway_result("BLOCKED", "HELPER_RUNTIME_STATE_MISSING"), 2)
    local_environment = local_environments[0]
    local_runtime = local_runtimes[0]
    has_evidence_reference = any(
        item.get("kind") == "RUNTIME_COMMAND"
        and item.get("path") == "ai/evidence/local-helper-runtime.json"
        for item in local_runtime["evidence"]
    )
    state_matches = (
        state["schemaVersion"] == 1
        and state.get("$id") == "ai/project-state.json"
        and local_environment["configurationStatus"] == "VERIFIED"
        and local_runtime["configurationStatus"] == "VERIFIED"
        and local_runtime["targetRuntime"] == evidence["targetRuntime"]
        and local_runtime["detectedRuntime"] == evidence["detectedRuntime"]
        and local_runtime["version"] == evidence["version"]
        and has_evidence_reference
    )
    capability_matches = all(evidence[key] == current[key] for key in (
        "environment",
        "targetRuntime",
        "detectedRuntime",
        "version",
        "jsonschemaVersion",
        "validator",
        "formatChecker",
        "interpreterSha256",
    ))
    if not state_matches or not capability_matches:
        return publish_result(root, gateway_result("BLOCKED", "HELPER_RUNTIME_EVIDENCE_STALE"), 2)
    runtime = {
        "runtimeCommand": evidence["runtimeCommand"],
        "runtimeExecutableHash": current["interpreterSha256"],
        "pythonVersion": current["version"],
        "jsonschemaVersion": current["jsonschemaVersion"],
        "validator": current["validator"],
        "formatChecker": current["formatChecker"],
    }
    return publish_result(root, gateway_result("PASS", None, runtime), 0)


def validate_run_start_inputs(run_id, task_key):
    if not isinstance(run_id, str) or not RUN_IDENTIFIER_PATTERN.fullmatch(run_id):
        raise ValueError("RUN_ID_INVALID")
    if (
        not isinstance(task_key, str)
        or not task_key
        or len(task_key) > RUN_TASK_KEY_MAX_LENGTH
        or any(character in task_key for character in ("/", "\\", "\x00", "\r", "\n"))
    ):
        raise ValueError("TASK_KEY_INVALID")


def permission_checks_supported():
    return os.name != "nt"


def run_lifecycle_hook(_name, **_context):
    return None


def path_is_link_or_reparse(path, metadata=None):
    metadata = path.lstat() if metadata is None else metadata
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return stat.S_ISLNK(metadata.st_mode) or bool(getattr(metadata, "st_file_attributes", 0) & reparse_flag)


def secure_run_path(root, run_id):
    root = Path(root).resolve(strict=True)
    run = root / ".ai-runs" / run_id
    try:
        metadata = run.lstat()
    except OSError as error:
        raise InvalidStateError([validation_error("RUN_DIRECTORY_INVALID", message="run directory is unavailable")]) from error
    if path_is_link_or_reparse(run, metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise InvalidStateError([validation_error("RUN_DIRECTORY_INVALID", message="run directory is unsafe")])
    try:
        resolved_run = run.resolve(strict=True)
        resolved_run.relative_to(root)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error("RUN_PATH_ESCAPE", message="run directory escapes repository")]) from error
    return root, run, resolved_run


def secure_run_artifact_path(root, run_id, components, *, create_parents=False):
    root, run, resolved_run = secure_run_path(root, run_id)
    current = run
    for index, component in enumerate(components[:-1]):
        candidate = current / component
        try:
            metadata = candidate.lstat()
        except FileNotFoundError:
            if not create_parents:
                return root, candidate.joinpath(*components[index + 1:]), False
            try:
                os.mkdir(candidate, 0o700)
                fsync_directory(current)
            except FileExistsError:
                pass
            metadata = candidate.lstat()
            run_lifecycle_hook("artifact.after_directory_create", path=candidate)
            metadata = candidate.lstat()
        except OSError as error:
            raise InvalidStateError([validation_error("RUN_ARTIFACT_PATH_INVALID", message="artifact ancestor is unavailable")]) from error
        if path_is_link_or_reparse(candidate, metadata) or not stat.S_ISDIR(metadata.st_mode):
            raise InvalidStateError([validation_error("RUN_ARTIFACT_PATH_INVALID", message="artifact ancestor is unsafe")])
        try:
            candidate.resolve(strict=True).relative_to(resolved_run)
        except (OSError, ValueError) as error:
            raise InvalidStateError([validation_error("RUN_ARTIFACT_PATH_ESCAPE", message="artifact ancestor escapes run")]) from error
        current = candidate

    path = current / components[-1]
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        return root, path, False
    except OSError as error:
        raise InvalidStateError([validation_error("RUN_ARTIFACT_PATH_INVALID", message="artifact path is unavailable")]) from error
    if path_is_link_or_reparse(path, metadata) or not stat.S_ISREG(metadata.st_mode):
        raise InvalidStateError([validation_error("RUN_ARTIFACT_PATH_INVALID", message="artifact path is not an exact regular file")])
    try:
        path.resolve(strict=True).relative_to(resolved_run)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error("RUN_ARTIFACT_PATH_ESCAPE", message="artifact path escapes run")]) from error
    return root, path, True


def require_safe_directory(path, code):
    if path.is_symlink() or not path.is_dir():
        raise InvalidStateError([validation_error(code, message="run directory is unsafe")])
    if permission_checks_supported() and path.stat().st_mode & 0o022:
        raise InvalidStateError([validation_error(code, message="run directory permissions are unsafe")])


def run_directory(root, run_id):
    root = Path(root).resolve(strict=True)
    runs = root / ".ai-runs"
    if runs.exists():
        require_safe_directory(runs, "RUNS_DIRECTORY_INVALID")
    if not runs.exists():
        runs.mkdir(mode=0o700)
        require_safe_directory(runs, "RUNS_DIRECTORY_INVALID")
    run = runs / run_id
    if run.exists() or run.is_symlink():
        raise RegistryBlockedError([validation_error("RUN_ID_EXISTS", message="run ID already exists")])
    try:
        run.mkdir(mode=0o700)
    except FileExistsError as error:
        raise RegistryBlockedError([validation_error("RUN_ID_EXISTS", message="run ID already exists")]) from error
    require_safe_directory(run, "RUN_DIRECTORY_INVALID")
    if run.resolve(strict=True).parent != runs.resolve(strict=True):
        raise InvalidStateError([validation_error("RUN_PATH_ESCAPE", message="run directory escapes repository")])
    return run


def exclusive_publish_json(root, path, instance, schema_path):
    validate(root, instance, schema_path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(path)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        try:
            os.fchmod(descriptor, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = None
            handle.write(compact(instance) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(temporary, path)
        except OSError as error:
            if error.errno in (errno.EEXIST, errno.EACCES, errno.EPERM):
                raise FileExistsError(path) from error
            raise
        fsync_directory(path.parent)
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)


def start_run(root, run_id, task_key):
    root = Path(root).resolve()
    preflight_result, preflight_status = run_current_preflight(root)
    if preflight_status != 0:
        return publish_result(
            root,
            gateway_result(
                preflight_result["result"],
                preflight_result["reason"],
                operation="RUN_START",
                errors=preflight_result["errors"],
            ),
            preflight_status,
        )
    try:
        validate_run_start_inputs(run_id, task_key)
    except ValueError as error:
        return publish_result(root, gateway_result("POLICY_VIOLATION", str(error), operation="RUN_START"), 4)

    run = None
    acquired_lock = None
    try:
        run = run_directory(root, run_id)
        state_directory = run / ".state"
        state_directory.mkdir(mode=0o700)
        acquired_lock = acquire_run_lock(root, run_id, purpose="start")
        session = {
            "$schema": "ai/schemas/run-session.schema.json",
            "$id": f".ai-runs/{run_id}/.state/run-session.json",
            "schemaVersion": 1,
            "runId": run_id,
            "taskKey": task_key,
            "startedAt": utc_now(),
            "workingDirectory": ".",
            "environment": "LOCAL",
            "state": "OPEN",
            "commandResultRefs": [],
            "processAttemptRefs": [],
            "approvalRefs": [],
            "policyViolationRefs": [],
            "gateResultRefs": [],
            "reservations": [],
            "lockRecoveries": [],
            "redactionApplied": False,
        }
        session_path = state_directory / "run-session.json"
        exclusive_publish_json(root, session_path, session, "ai/schemas/run-session.schema.json")
    except RegistryBlockedError as error:
        return publish_result(root, gateway_result("BLOCKED", error.errors[0]["code"], operation="RUN_START", errors=error.errors), 2)
    except (InvalidStateError, OSError, ValueError) as error:
        if run is not None and not (run / ".state" / "run-session.json").exists():
            shutil.rmtree(run, ignore_errors=True)
        errors = error.errors if isinstance(error, InvalidStateError) else []
        return publish_result(root, gateway_result("INVALID_STATE", "RUN_SESSION_PUBLICATION_FAILED", operation="RUN_START", errors=errors), 5)
    finally:
        if acquired_lock is not None:
            release_run_lock(acquired_lock)

    return publish_result(
        root,
        gateway_result(
            "PASS",
            None,
            {"runId": run_id, "taskKey": task_key, "sessionRef": session["$id"]},
            operation="RUN_START",
        ),
        0,
    )


def run_lock_path(root, run_id):
    validate_run_start_inputs(run_id, "lock")
    root = Path(root).resolve(strict=True)
    run = root / ".ai-runs" / run_id
    state = run / ".state"
    if not run.is_dir() or run.is_symlink() or not state.is_dir() or state.is_symlink():
        raise InvalidStateError([validation_error("RUN_STATE_DIRECTORY_INVALID", message="run state directory is unsafe")])
    require_safe_directory(run, "RUN_DIRECTORY_INVALID")
    require_safe_directory(state, "RUN_STATE_DIRECTORY_INVALID")
    if state.resolve(strict=True) != (root / ".ai-runs" / run_id / ".state").resolve(strict=True):
        raise InvalidStateError([validation_error("RUN_STATE_PATH_ESCAPE", message="run state path escapes repository")])
    return state / "lock"


def validate_run_lock_owner(owner, run_id):
    try:
        validate_embedded(owner, RUN_LOCK_OWNER_SCHEMA)
    except Exception as error:
        raise InvalidStateError([validation_error("RUN_LOCK_OWNER_INVALID", message="run lock owner is malformed")]) from error
    if owner["runId"] != run_id:
        raise InvalidStateError([validation_error("RUN_LOCK_OWNER_RUN_MISMATCH", message="run lock owner run ID does not match")])
    return owner


def read_run_lock_owner(path, run_id):
    try:
        lock_metadata = path.parent.lstat()
        owner_metadata = path.lstat()
    except OSError as error:
        raise InvalidStateError([validation_error("RUN_LOCK_OWNER_INVALID", message="run lock owner is unavailable")]) from error
    if (
        path_is_link_or_reparse(path.parent, lock_metadata)
        or not stat.S_ISDIR(lock_metadata.st_mode)
        or path_is_link_or_reparse(path, owner_metadata)
        or not stat.S_ISREG(owner_metadata.st_mode)
    ):
        raise InvalidStateError([validation_error("RUN_LOCK_OWNER_INVALID", message="run lock owner is unsafe")])
    try:
        owner = read_json(path)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error("RUN_LOCK_OWNER_INVALID", message="run lock owner is malformed")]) from error
    return validate_run_lock_owner(owner, run_id)


def run_owner_is_recent(owner):
    try:
        acquired_at = dt.datetime.fromisoformat(owner["acquiredAt"].replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise InvalidStateError([validation_error("RUN_LOCK_OWNER_INVALID", message="run lock acquisition time is malformed")]) from error
    return (dt.datetime.now(dt.timezone.utc) - acquired_at.astimezone(dt.timezone.utc)).total_seconds() < RUN_LOCK_MAX_RECENT_SECONDS


def new_run_lock_owner(run_id):
    return validate_run_lock_owner({
        "ownerId": str(uuid.uuid4()),
        "runId": run_id,
        "pid": os.getpid(),
        "acquiredAt": utc_now(),
    }, run_id)


def exact_control_directory(path, code):
    try:
        metadata = path.lstat()
    except OSError as error:
        raise InvalidStateError([validation_error(code, message="control directory is unavailable")]) from error
    if path_is_link_or_reparse(path, metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise InvalidStateError([validation_error(code, message="control directory is unsafe")])
    return metadata


def control_directory_is_recent(path):
    metadata = exact_control_directory(path, "RUN_LOCK_PATH_INVALID")
    modified = dt.datetime.fromtimestamp(metadata.st_mtime, tz=dt.timezone.utc)
    return (dt.datetime.now(dt.timezone.utc) - modified).total_seconds() < RUN_LOCK_MAX_RECENT_SECONDS


def exact_control_entries(path):
    exact_control_directory(path, "RUN_LOCK_PATH_INVALID")
    try:
        return tuple(path.iterdir())
    except OSError as error:
        raise InvalidStateError([validation_error("RUN_LOCK_PATH_INVALID", message="control directory cannot be inspected")]) from error


def cleanup_owned_empty_initialization(path):
    try:
        if exact_control_entries(path):
            return False
        path.rmdir()
        fsync_directory(path.parent)
        return True
    except (OSError, InvalidStateError):
        return False


def run_recovery_marker_exists(state):
    claim = state / "lock-recovery-claim"
    if claim.exists() or claim.is_symlink():
        return True
    try:
        return any(
            RECOVERY_QUARANTINE_PATTERN.fullmatch(item.name)
            or INITIALIZATION_QUARANTINE_PATTERN.fullmatch(item.name)
            for item in state.iterdir()
        )
    except OSError as error:
        raise InvalidStateError([validation_error(
            "RUN_LOCK_RECOVERY_STATE_INVALID", message="run recovery state cannot be inspected",
        )]) from error


def _publish_run_lock(root, run_id, owner, *, purpose, block_recovery=False):
    lock = run_lock_path(root, run_id)
    if block_recovery and run_recovery_marker_exists(lock.parent):
        raise RegistryBlockedError([validation_error(
            "RUN_LOCK_RECOVERY_ACTIVE", message="run lock recovery evidence blocks normal acquisition",
        )])
    try:
        os.mkdir(lock, 0o700)
    except FileExistsError as error:
        exact_control_directory(lock, "RUN_LOCK_PATH_INVALID")
        try:
            (lock / "owner.json").lstat()
        except FileNotFoundError:
            if exact_control_entries(lock):
                raise InvalidStateError([validation_error("RUN_LOCK_INITIALIZATION_INVALID", message="ownerless run lock contains unexpected entries")]) from error
            raise RegistryBlockedError([validation_error("RUN_LOCK_INITIALIZING", message="run lock acquisition is in progress")]) from error
        read_run_lock_owner(lock / "owner.json", run_id)
        raise RegistryBlockedError([validation_error("RUN_LOCK_HELD", message="run lock is held")]) from error
    run_lifecycle_hook("acquire.after_mkdir", lock=lock, owner=owner, purpose=purpose)
    if block_recovery and run_recovery_marker_exists(lock.parent):
        cleanup_owned_empty_initialization(lock)
        raise RegistryBlockedError([validation_error(
            "RUN_LOCK_RECOVERY_ACTIVE", message="run lock recovery evidence appeared during normal acquisition",
        )])
    try:
        exclusive_write(lock / "owner.json", compact(owner) + "\n")
        fsync_directory(lock)
    except FileExistsError as error:
        raise RegistryBlockedError([validation_error("RUN_LOCK_OWNER_COLLISION", message="run lock owner publication collided")]) from error
    except OSError:
        cleanup_owned_empty_initialization(lock)
        raise
    return AcquiredRunLock(lock, owner)


def acquire_run_lock(root, run_id, *, purpose="normal", continuing_attempt=None):
    if purpose not in {"normal", "start"}:
        raise InvalidStateError([validation_error(
            "RUN_LOCK_PURPOSE_INVALID", message="only normal and start lock acquisition are public",
        )])
    owner = new_run_lock_owner(run_id)
    try:
        acquired = _publish_run_lock(root, run_id, owner, purpose=purpose, block_recovery=True)
    except RegistryBlockedError as error:
        if purpose != "normal" or error.errors[0]["code"] != "RUN_LOCK_HELD":
            raise
        recover_run_lock(root, run_id, continuing_attempt=continuing_attempt)
        acquired = _publish_run_lock(
            root, run_id, new_run_lock_owner(run_id), purpose=purpose, block_recovery=True,
        )
    if purpose == "normal":
        try:
            session = active_open_session(root, run_id)
            repair_reserved_attempts(root, session, acquired, continuing_attempt=continuing_attempt)
        except Exception:
            release_run_lock(acquired)
            raise
    return acquired


def recovery_uuid(recovery_id):
    if not RECOVERY_QUARANTINE_PATTERN.fullmatch(recovery_id):
        raise InvalidStateError([validation_error(
            "RUN_LOCK_RECOVERY_ID_INVALID", message="run lock recovery ID is malformed",
        )])
    return recovery_id.removeprefix("lock-recovery-")


def acquire_replacement_run_lock(root, run_id, quarantine):
    lock = run_lock_path(root, run_id)
    if quarantine.parent != lock.parent:
        raise InvalidStateError([validation_error(
            "RUN_LOCK_RECOVERY_ID_INVALID", message="recovery quarantine is outside the exact run state",
        )])
    exact_control_directory(quarantine, "RUN_LOCK_QUARANTINE_INVALID")
    recovery_id = quarantine.name
    owner = validate_run_lock_owner({
        "ownerId": recovery_uuid(recovery_id),
        "runId": run_id,
        "pid": os.getpid(),
        "acquiredAt": utc_now(),
    }, run_id)
    return _publish_run_lock(root, run_id, owner, purpose="recovery")


def validate_held_recovery_claim(state, run_id, claim):
    expected_path = state / "lock-recovery-claim"
    if not isinstance(claim, AcquiredRunLock) or claim.path != expected_path or claim.owner.get("runId") != run_id:
        raise InvalidStateError([validation_error(
            "RUN_LOCK_RECOVERY_CLAIM_MISMATCH", message="held recovery claim does not match the exact run state",
        )])
    if read_run_lock_owner(expected_path / "owner.json", run_id) != claim.owner:
        raise RegistryBlockedError([validation_error(
            "RUN_LOCK_RECOVERY_CLAIM_CHANGED", message="held recovery claim owner changed",
        )])
    if {item.name for item in exact_control_entries(expected_path)} != {"owner.json"}:
        raise InvalidStateError([validation_error(
            "RUN_LOCK_RECOVERY_CLAIM_INVALID", message="held recovery claim contains unexpected entries",
        )])
    return claim


def resume_ownerless_replacement_lock(root, run_id, claim, quarantine):
    lock = run_lock_path(root, run_id)
    if exact_control_entries(lock):
        raise InvalidStateError([validation_error(
            "RUN_LOCK_RECOVERY_CONTRADICTION", message="ownerless replacement lock contains unexpected entries",
        )])
    owner = validate_run_lock_owner({
        "ownerId": recovery_uuid(quarantine.name),
        "runId": run_id,
        "pid": os.getpid(),
        "acquiredAt": utc_now(),
    }, run_id)
    run_lifecycle_hook(
        "recover.replacement_before_owner_publication", claim=claim, quarantine=quarantine, lock=lock, owner=owner,
    )
    validate_held_recovery_claim(lock.parent, run_id, claim)
    try:
        exclusive_write(lock / "owner.json", compact(owner) + "\n")
        fsync_directory(lock)
    except FileExistsError as error:
        existing = read_run_lock_owner(lock / "owner.json", run_id)
        if existing["ownerId"] != owner["ownerId"]:
            raise InvalidStateError([validation_error(
                "RUN_LOCK_RECOVERY_CONTRADICTION", message="late replacement owner does not match quarantine",
            )]) from error
        raise RegistryBlockedError([validation_error(
            "RUN_LOCK_HELD", message="matching replacement owner publication raced",
        )]) from error
    return AcquiredRunLock(lock, owner)


def release_run_lock(acquired):
    if not isinstance(acquired, AcquiredRunLock):
        return False
    lock = acquired.path
    try:
        owner = read_run_lock_owner(lock / "owner.json", acquired.owner["runId"])
        if owner != acquired.owner:
            return False
        run_lifecycle_hook("release.before_unlink", lock=lock, expected=acquired.owner)
        if read_run_lock_owner(lock / "owner.json", acquired.owner["runId"]) != acquired.owner:
            return False
        (lock / "owner.json").unlink()
        fsync_directory(lock)
        lock.rmdir()
        fsync_directory(lock.parent)
    except (OSError, ValueError, InvalidStateError):
        return False
    return True


def read_exact_run_json(root, run_id, components, schema_path):
    root, path, exists = secure_run_artifact_path(root, run_id, components)
    if not exists:
        return path, None
    instance = read_json(path)
    validate(root, instance, schema_path)
    return path, instance


def validate_held_run_lock(root, run_id, acquired):
    if not isinstance(acquired, AcquiredRunLock):
        raise InvalidStateError([validation_error("RUN_LOCK_REQUIRED", message="session mutation requires a held run lock")])
    expected_path = run_lock_path(root, run_id)
    if acquired.path != expected_path or acquired.owner.get("runId") != run_id:
        raise InvalidStateError([validation_error("RUN_LOCK_MISMATCH", message="held run lock does not match session")])
    owner = read_run_lock_owner(acquired.path / "owner.json", run_id)
    if owner != acquired.owner:
        raise RegistryBlockedError([validation_error("RUN_LOCK_CHANGED", message="held run lock owner changed")])
    return acquired


def replace_run_session(root, session_path, session, acquired_lock, expected_session=None):
    root = Path(root).resolve(strict=True)
    validate(root, session, "ai/schemas/run-session.schema.json")
    run_id = session["runId"]
    expected_path = root / ".ai-runs" / run_id / ".state" / "run-session.json"
    if Path(session_path) != expected_path:
        raise InvalidStateError([validation_error("RUN_SESSION_REFERENCE_MISMATCH", message="session path is not exact")])
    validate_held_run_lock(root, run_id, acquired_lock)
    run_lifecycle_hook("session.before_replace", path=expected_path, expected=expected_session, replacement=session)
    _path, current = read_exact_run_json(
        root, run_id, (".state", "run-session.json"), "ai/schemas/run-session.schema.json",
    )
    if current == session:
        return current
    if expected_session is not None and current != expected_session:
        raise RegistryBlockedError([validation_error("RUN_SESSION_CHANGED", message="run session changed before publication")])
    run_lifecycle_hook("session.after_compare", path=expected_path, expected=current, replacement=session)
    run_lifecycle_hook("session.before_temp_publication", path=expected_path, replacement=session)
    validate_held_run_lock(root, run_id, acquired_lock)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{expected_path.name}.", dir=expected_path.parent)
    try:
        try:
            os.fchmod(descriptor, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as handle:
            descriptor = None
            handle.write(compact(session) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        run_lifecycle_hook("session.before_os_replace", path=expected_path, temporary=Path(temporary), replacement=session)
        validate_held_run_lock(root, run_id, acquired_lock)
        os.replace(temporary, expected_path)
        fsync_directory(expected_path.parent)
        try:
            os.chmod(expected_path, 0o600)
        except OSError:
            if os.name != "nt":
                raise
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if os.path.exists(temporary):
            os.unlink(temporary)
    return session


def valid_repair_result(result, reservation, process, command_ref, process_ref):
    return (
        result.get("$id") == command_ref
        and result.get("runId") == process.get("runId")
        and result.get("commandId") == reservation["commandId"]
        and result.get("attemptId") == reservation["attemptId"]
        and result.get("processAttemptRef") == process_ref
        and result.get("startedAt") == (process["startedAt"] or reservation["reservedAt"])
        and result.get("result") == "BLOCKED"
        and result.get("processExitCode") is None
        and result.get("argvHash") is None
        and result.get("inputFingerprint") is None
        and result.get("environmentFingerprint") is None
        and result.get("stdoutPath") is None
        and result.get("stderrPath") is None
        and result.get("redactionApplied") is False
        and result.get("reason") == "STALE_RESERVED_REPAIRED"
    )


def repair_reserved_attempts(root, session, acquired_lock, continuing_attempt=None):
    root = Path(root).resolve(strict=True)
    validate(root, session, "ai/schemas/run-session.schema.json")
    repaired = json.loads(json.dumps(session))
    run_id = repaired["runId"]
    validate_held_run_lock(root, run_id, acquired_lock)
    changed = False
    for reservation in repaired["reservations"]:
        if reservation["state"] != "RESERVED":
            continue
        command_id = reservation["commandId"]
        attempt_id = reservation["attemptId"]
        if continuing_attempt == (command_id, attempt_id):
            continue
        process_ref = f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json"
        command_ref = f".ai-runs/{run_id}/commands/{command_id}/{attempt_id}.json"
        try:
            _process_path, process = read_exact_run_json(
                root,
                run_id,
                ("process-attempts", command_id, f"{attempt_id}.json"),
                "ai/schemas/process-attempt.schema.json",
            )
            if process is None or process.get("launchStatus") != "LAUNCHED":
                continue
            if process.get("$id") != process_ref or process.get("runId") != run_id or any(
                process.get(name) != reservation[name]
                for name in ("commandId", "attemptId", "argvHash", "inputFingerprint", "environmentFingerprint")
            ):
                continue
        except (InvalidStateError, OSError, ValueError):
            continue

        published_new = False
        try:
            _root, command_path, command_exists = secure_run_artifact_path(
                root,
                run_id,
                ("commands", command_id, f"{attempt_id}.json"),
                create_parents=True,
            )
            command_result = None
            if command_exists:
                _command_path, command_result = read_exact_run_json(
                    root,
                    run_id,
                    ("commands", command_id, f"{attempt_id}.json"),
                    "ai/schemas/command-result.schema.json",
                )
                if not valid_repair_result(command_result, reservation, process, command_ref, process_ref):
                    continue
            else:
                terminal_at = utc_now()
                command_result = {
                    "$schema": "ai/schemas/command-result.schema.json",
                    "$id": command_ref,
                    "schemaVersion": 1,
                    "runId": run_id,
                    "commandId": command_id,
                    "attemptId": attempt_id,
                    "processAttemptRef": process_ref,
                    "startedAt": process["startedAt"] or reservation["reservedAt"],
                    "endedAt": terminal_at,
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
                run_lifecycle_hook("repair.before_publish", path=command_path, result=command_result)
                _root, command_path, command_exists = secure_run_artifact_path(
                    root,
                    run_id,
                    ("commands", command_id, f"{attempt_id}.json"),
                    create_parents=True,
                )
                if not command_exists:
                    try:
                        exclusive_publish_json(root, command_path, command_result, "ai/schemas/command-result.schema.json")
                        published_new = True
                    except FileExistsError:
                        pass
                _command_path, winner = read_exact_run_json(
                    root,
                    run_id,
                    ("commands", command_id, f"{attempt_id}.json"),
                    "ai/schemas/command-result.schema.json",
                )
                if winner is None or not valid_repair_result(winner, reservation, process, command_ref, process_ref):
                    continue
                command_result = winner
        except (InvalidStateError, OSError, ValueError):
            continue
        if published_new:
            run_lifecycle_hook("repair.after_publish", path=command_path, result=command_result)
        terminal_at = command_result["endedAt"]
        reservation.update({
            "state": "BLOCKED",
            "commandResultRef": command_ref,
            "processAttemptRef": process_ref,
            "terminalAt": terminal_at,
        })
        repaired["commandResultRefs"].append(command_ref)
        if process_ref not in repaired["processAttemptRefs"]:
            repaired["processAttemptRefs"].append(process_ref)
        changed = True

    if changed:
        session_path = root / repaired["$id"]
        replace_run_session(root, session_path, repaired, acquired_lock, expected_session=session)
    return repaired


def create_recovery_claim(path, run_id):
    owner = new_run_lock_owner(run_id)
    os.mkdir(path, 0o700)
    run_lifecycle_hook("recover.claim_after_mkdir", claim=path, owner=owner)
    try:
        exclusive_write(path / "owner.json", compact(owner) + "\n")
        fsync_directory(path)
    except OSError:
        cleanup_owned_empty_initialization(path)
        raise
    return AcquiredRunLock(path, owner)


def remove_exact_owned_control_directory(path, expected_owner):
    if read_run_lock_owner(path / "owner.json", expected_owner["runId"]) != expected_owner:
        return False
    entries = exact_control_entries(path)
    if {item.name for item in entries} != {"owner.json"}:
        return False
    (path / "owner.json").unlink()
    fsync_directory(path)
    path.rmdir()
    fsync_directory(path.parent)
    return True


def acquire_recovery_claim(state, run_id):
    claim_path = state / "lock-recovery-claim"
    try:
        return create_recovery_claim(claim_path, run_id)
    except FileExistsError as error:
        exact_control_directory(claim_path, "RUN_LOCK_RECOVERY_CLAIM_INVALID")
        entries = exact_control_entries(claim_path)
        if not entries:
            if control_directory_is_recent(claim_path):
                raise RegistryBlockedError([validation_error(
                    "RUN_LOCK_RECOVERY_INITIALIZING", message="recovery claim initialization is recent",
                )]) from error
            run_lifecycle_hook("recover.claim_before_ownerless_quarantine", claim=claim_path)
            stale_path = state / f"lock-recovery-claim-initialization-{uuid.uuid4()}"
            if stale_path.exists() or stale_path.is_symlink():
                raise RegistryBlockedError([validation_error(
                    "RUN_LOCK_RECOVERY_CLAIM_COLLISION", message="ownerless recovery claim quarantine exists",
                )])
            try:
                os.rename(claim_path, stale_path)
            except OSError as rename_error:
                raise RegistryBlockedError([validation_error(
                    "RUN_LOCK_RECOVERY_ACTIVE", message="ownerless recovery claim changed",
                )]) from rename_error
            run_lifecycle_hook(
                "recover.claim_after_ownerless_quarantine_rename", claim=claim_path, quarantine=stale_path,
            )
            stale_entries = exact_control_entries(stale_path)
            if stale_entries:
                if {item.name for item in stale_entries} != {"owner.json"}:
                    raise InvalidStateError([validation_error(
                        "RUN_LOCK_RECOVERY_CLAIM_INVALID", message="ownerless recovery claim changed after quarantine",
                    )])
                read_run_lock_owner(stale_path / "owner.json", run_id)
                if claim_path.exists() or claim_path.is_symlink():
                    raise InvalidStateError([validation_error(
                        "RUN_LOCK_RECOVERY_CLAIM_CONTRADICTION",
                        message="late recovery claim owner cannot be restored because the fixed path is occupied",
                    )])
                try:
                    os.rename(stale_path, claim_path)
                except OSError as restore_error:
                    raise RegistryBlockedError([validation_error(
                        "RUN_LOCK_RECOVERY_ACTIVE", message="late recovery claim owner restoration raced",
                    )]) from restore_error
                fsync_directory(state)
                raise RegistryBlockedError([validation_error(
                    "RUN_LOCK_RECOVERY_ACTIVE", message="late recovery claim owner was restored",
                )])
            try:
                stale_path.rmdir()
                fsync_directory(state)
                return create_recovery_claim(claim_path, run_id)
            except (FileExistsError, FileNotFoundError) as race_error:
                raise RegistryBlockedError([validation_error(
                    "RUN_LOCK_RECOVERY_ACTIVE", message="ownerless recovery claim replacement raced",
                )]) from race_error
        if {item.name for item in entries} != {"owner.json"}:
            raise InvalidStateError([validation_error(
                "RUN_LOCK_RECOVERY_CLAIM_INVALID", message="recovery claim contains unexpected entries",
            )]) from error
        try:
            owner = read_run_lock_owner(claim_path / "owner.json", run_id)
        except InvalidStateError:
            raise InvalidStateError([validation_error("RUN_LOCK_RECOVERY_CLAIM_INVALID", message="recovery claim owner is invalid")]) from error
        if owner_is_alive(owner["pid"]) or run_owner_is_recent(owner):
            raise RegistryBlockedError([validation_error("RUN_LOCK_RECOVERY_ACTIVE", message="run lock recovery is live or recent")]) from error
        if {item.name for item in exact_control_entries(claim_path)} != {"owner.json"}:
            raise InvalidStateError([validation_error("RUN_LOCK_RECOVERY_CLAIM_INVALID", message="recovery claim contains unexpected entries")])
        stale_path = state / f"lock-recovery-claim-stale-{uuid.uuid4()}"
        if stale_path.exists() or stale_path.is_symlink():
            raise RegistryBlockedError([validation_error("RUN_LOCK_RECOVERY_CLAIM_COLLISION", message="stale recovery claim path exists")])
        try:
            os.rename(claim_path, stale_path)
        except OSError as rename_error:
            raise RegistryBlockedError([validation_error("RUN_LOCK_RECOVERY_ACTIVE", message="stale recovery claim rename failed")]) from rename_error
        replacement = create_recovery_claim(claim_path, run_id)
        if not remove_exact_owned_control_directory(stale_path, owner):
            raise InvalidStateError([validation_error("RUN_LOCK_RECOVERY_CLAIM_INVALID", message="stale recovery claim changed")])
        return replacement


def recovery_quarantines(state, run_id):
    quarantines = []
    for candidate in state.iterdir():
        if not RECOVERY_QUARANTINE_PATTERN.fullmatch(candidate.name):
            continue
        exact_control_directory(candidate, "RUN_LOCK_QUARANTINE_INVALID")
        if {item.name for item in exact_control_entries(candidate)} != {"owner.json"}:
            raise InvalidStateError([validation_error("RUN_LOCK_QUARANTINE_INVALID", message="recovery quarantine contains unexpected entries")])
        owner = read_run_lock_owner(candidate / "owner.json", run_id)
        quarantines.append((candidate, owner))
    if len(quarantines) > 1:
        raise InvalidStateError([validation_error("MULTIPLE_RUN_LOCK_QUARANTINES", message="multiple recovery quarantines are contradictory")])
    return quarantines


def initialization_quarantines(state):
    quarantines = []
    for candidate in state.iterdir():
        if not INITIALIZATION_QUARANTINE_PATTERN.fullmatch(candidate.name):
            continue
        exact_control_directory(candidate, "RUN_LOCK_INITIALIZATION_INVALID")
        entries = exact_control_entries(candidate)
        if entries and {item.name for item in entries} != {"owner.json"}:
            raise InvalidStateError([validation_error(
                "RUN_LOCK_INITIALIZATION_INVALID", message="initialization quarantine contains unexpected entries",
            )])
        quarantines.append(candidate)
    if len(quarantines) > 1:
        raise InvalidStateError([validation_error(
            "MULTIPLE_RUN_LOCK_INITIALIZATION_QUARANTINES",
            message="multiple initialization quarantines are contradictory",
        )])
    return quarantines


def complete_ownerless_initialization_cleanup(state, run_id, claim, quarantine):
    lock = state / "lock"
    entries = exact_control_entries(quarantine)
    if entries:
        owner = read_run_lock_owner(quarantine / "owner.json", run_id)
        validate_held_recovery_claim(state, run_id, claim)
        if lock.exists() or lock.is_symlink():
            raise InvalidStateError([validation_error(
                "RUN_LOCK_INITIALIZATION_CONTRADICTION",
                message="late lock owner cannot be restored because the lock path is occupied",
            )])
        try:
            os.rename(quarantine, lock)
        except OSError as restore_error:
            raise RegistryBlockedError([validation_error(
                "RUN_LOCK_HELD", message="late run lock owner restoration raced",
            )]) from restore_error
        fsync_directory(state)
        if not release_run_lock(claim):
            raise InvalidStateError([validation_error(
                "RUN_LOCK_RELEASE_FAILED", message="recovery claim release failed",
            )])
        raise RegistryBlockedError([validation_error(
            "RUN_LOCK_HELD", message=f"late run lock owner {owner['ownerId']} was restored",
        )])
    run_lifecycle_hook(
        "recover.ownerless_before_quarantine_removal", claim=claim, quarantine=quarantine, lock=lock,
    )
    validate_held_recovery_claim(state, run_id, claim)
    try:
        quarantine.rmdir()
    except OSError as error:
        raise RegistryBlockedError([validation_error(
            "RUN_LOCK_INITIALIZATION_CHANGED", message="initialization quarantine cleanup raced",
        )]) from error
    fsync_directory(state)
    run_lifecycle_hook("recover.ownerless_after_quarantine_removal", claim=claim, quarantine=quarantine, lock=lock)
    validate_held_recovery_claim(state, run_id, claim)
    if not release_run_lock(claim):
        raise InvalidStateError([validation_error("RUN_LOCK_RELEASE_FAILED", message="recovery claim release failed")])
    return True


def complete_recovery(
    root, run_id, claim, quarantine, stale_owner, replacement_lock=None, continuing_attempt=None,
):
    recovery_id = quarantine.name
    if replacement_lock is None:
        replacement_lock = acquire_replacement_run_lock(root, run_id, quarantine)
    if replacement_lock.owner["ownerId"] != recovery_uuid(recovery_id):
        raise InvalidStateError([validation_error(
            "RUN_LOCK_REPLACEMENT_MISMATCH", message="replacement lock does not prove its recovery quarantine",
        )])
    session_path, session = read_exact_run_json(
        root, run_id, (".state", "run-session.json"), "ai/schemas/run-session.schema.json",
    )
    if session is None:
        raise InvalidStateError([validation_error("RUN_SESSION_MISSING", message="run session is missing")])
    matches = [item for item in session["lockRecoveries"] if item["recoveryId"] == recovery_id]
    if len(matches) > 1:
        raise InvalidStateError([validation_error("DUPLICATE_LOCK_RECOVERY_ID", message="recovery history is contradictory")])
    if matches:
        existing = matches[0]
        if (
            existing["runId"] != run_id
            or existing["recoveredOwnerId"] != stale_owner["ownerId"]
            or existing["replacementOwnerId"] != replacement_lock.owner["ownerId"]
            or existing["previousPid"] != stale_owner["pid"]
            or existing["previousAcquiredAt"] != stale_owner["acquiredAt"]
            or existing["reason"] != "DEAD_AND_EXPIRED"
        ):
            raise InvalidStateError([validation_error("LOCK_RECOVERY_HISTORY_MISMATCH", message="recovery history contradicts quarantine")])
    else:
        original_session = json.loads(json.dumps(session))
        session["lockRecoveries"].append({
            "recoveryId": recovery_id,
            "runId": run_id,
            "recoveredOwnerId": stale_owner["ownerId"],
            "replacementOwnerId": replacement_lock.owner["ownerId"],
            "previousPid": stale_owner["pid"],
            "previousAcquiredAt": stale_owner["acquiredAt"],
            "recoveredAt": utc_now(),
            "reason": "DEAD_AND_EXPIRED",
        })
        run_lifecycle_hook("recover.before_history_write", session=session, quarantine=quarantine, lock=replacement_lock.path)
        replace_run_session(root, session_path, session, replacement_lock, expected_session=original_session)
        run_lifecycle_hook(
            "recover.after_history_publication", session=session, quarantine=quarantine, lock=replacement_lock.path,
        )
    session = repair_reserved_attempts(
        root, session, replacement_lock, continuing_attempt=continuing_attempt,
    )
    unresolved = [
        (item["commandId"], item["attemptId"])
        for item in session["reservations"] if item["state"] == "RESERVED"
    ]
    if any(item != continuing_attempt for item in unresolved):
        raise RegistryBlockedError([validation_error("RESERVED_ATTEMPT_REPAIR_BLOCKED", message="reserved attempt recovery is unsafe")])
    validate_held_recovery_claim(replacement_lock.path.parent, run_id, claim)
    if read_run_lock_owner(quarantine / "owner.json", run_id) != stale_owner:
        raise InvalidStateError([validation_error("RUN_LOCK_CHANGED", message="quarantined lock owner changed")])
    if {item.name for item in exact_control_entries(quarantine)} != {"owner.json"}:
        raise InvalidStateError([validation_error("RUN_LOCK_QUARANTINE_INVALID", message="quarantined lock contains unexpected entries")])
    if not remove_exact_owned_control_directory(quarantine, stale_owner):
        raise InvalidStateError([validation_error("RUN_LOCK_QUARANTINE_INVALID", message="quarantined lock cleanup failed")])
    if not release_run_lock(replacement_lock):
        raise InvalidStateError([validation_error("RUN_LOCK_RELEASE_FAILED", message="replacement run lock release failed")])
    if not release_run_lock(claim):
        raise InvalidStateError([validation_error("RUN_LOCK_RELEASE_FAILED", message="recovery claim release failed")])
    return True


def recover_run_lock(root, run_id, *, continuing_attempt=None):
    lock = run_lock_path(root, run_id)
    state = lock.parent
    stale_owner = None
    lock_exists = False
    try:
        exact_control_directory(lock, "RUN_LOCK_PATH_INVALID")
        lock_exists = True
    except InvalidStateError:
        if lock.exists() or lock.is_symlink():
            raise
    if lock_exists:
        entries = exact_control_entries(lock)
        owner_entries = [item for item in entries if item.name == "owner.json"]
        if owner_entries:
            stale_owner = read_run_lock_owner(lock / "owner.json", run_id)
            if owner_is_alive(stale_owner["pid"]) or run_owner_is_recent(stale_owner):
                raise RegistryBlockedError([validation_error("RUN_LOCK_HELD", message="run lock owner is live or recent")])
            run_lifecycle_hook("recover.after_initial_owner_read", lock=lock, owner=stale_owner)
        elif entries:
            raise InvalidStateError([validation_error("RUN_LOCK_INITIALIZATION_INVALID", message="ownerless run lock contains unexpected entries")])
    run_lifecycle_hook("recover.before_claim", lock=lock, owner=stale_owner)
    claim_path = state / "lock-recovery-claim"
    claim_preexisted = claim_path.exists() or claim_path.is_symlink()
    claim = acquire_recovery_claim(state, run_id)
    quarantine_started = False
    try:
        run_lifecycle_hook("recover.after_claim", claim=claim, lock=lock, owner=stale_owner)
        quarantines = recovery_quarantines(state, run_id)
        ownerless_quarantines = initialization_quarantines(state)
        if stale_owner is not None:
            if ownerless_quarantines:
                raise InvalidStateError([validation_error(
                    "RUN_LOCK_RECOVERY_CONTRADICTION", message="owned lock and initialization quarantine both exist",
                )])
            if quarantines:
                if len(quarantines) != 1:
                    raise InvalidStateError([validation_error(
                        "RUN_LOCK_RECOVERY_CONTRADICTION", message="replacement lock recovery state is contradictory",
                    )])
                quarantine, quarantined_owner = quarantines[0]
                if owner_is_alive(quarantined_owner["pid"]) or run_owner_is_recent(quarantined_owner):
                    raise RegistryBlockedError([validation_error(
                        "RUN_LOCK_QUARANTINE_NOT_STALE", message="quarantined lock owner is live or recent",
                    )])
                if read_run_lock_owner(lock / "owner.json", run_id) != stale_owner:
                    raise RegistryBlockedError([validation_error(
                        "RUN_LOCK_CHANGED", message="replacement lock owner changed during recovery",
                    )])
                if {item.name for item in exact_control_entries(lock)} != {"owner.json"}:
                    raise InvalidStateError([validation_error(
                        "RUN_LOCK_PATH_INVALID", message="replacement lock contains unexpected entries",
                    )])
                if stale_owner["ownerId"] != recovery_uuid(quarantine.name):
                    raise InvalidStateError([validation_error(
                        "RUN_LOCK_RECOVERY_CONTRADICTION",
                        message="replacement lock owner does not match the recovery quarantine",
                    )])
                quarantine_started = True
                replacement_lock = AcquiredRunLock(lock, stale_owner)
                return complete_recovery(
                    root, run_id, claim, quarantine, quarantined_owner, replacement_lock=replacement_lock,
                    continuing_attempt=continuing_attempt,
                )
            if read_run_lock_owner(lock / "owner.json", run_id) != stale_owner:
                raise RegistryBlockedError([validation_error("RUN_LOCK_CHANGED", message="run lock owner changed during recovery")])
            recovery_id = f"lock-recovery-{uuid.uuid4()}"
            quarantine = state / recovery_id
            if quarantine.exists() or quarantine.is_symlink():
                raise RegistryBlockedError([validation_error("RUN_LOCK_RECOVERY_COLLISION", message="run lock recovery path exists")])
            run_lifecycle_hook("recover.before_quarantine_rename", lock=lock, quarantine=quarantine, owner=stale_owner)
            try:
                os.rename(lock, quarantine)
            except OSError as error:
                raise RegistryBlockedError([validation_error("RUN_LOCK_RECOVERY_COLLISION", message="run lock recovery rename failed")]) from error
            quarantine_started = True
            run_lifecycle_hook("recover.after_quarantine_rename", lock=lock, quarantine=quarantine, owner=stale_owner)
        elif lock_exists:
            if quarantines:
                if ownerless_quarantines or len(quarantines) != 1:
                    raise InvalidStateError([validation_error(
                        "RUN_LOCK_RECOVERY_CONTRADICTION", message="ownerless replacement recovery state is contradictory",
                    )])
                quarantine, quarantined_owner = quarantines[0]
                if owner_is_alive(quarantined_owner["pid"]) or run_owner_is_recent(quarantined_owner):
                    raise RegistryBlockedError([validation_error(
                        "RUN_LOCK_QUARANTINE_NOT_STALE", message="quarantined lock owner is live or recent",
                    )])
                quarantine_started = True
                replacement_lock = resume_ownerless_replacement_lock(root, run_id, claim, quarantine)
                return complete_recovery(
                    root, run_id, claim, quarantine, quarantined_owner, replacement_lock=replacement_lock,
                    continuing_attempt=continuing_attempt,
                )
            if ownerless_quarantines:
                raise InvalidStateError([validation_error(
                    "RUN_LOCK_RECOVERY_CONTRADICTION", message="ownerless lock and initialization quarantine both exist",
                )])
            if exact_control_entries(lock):
                raise InvalidStateError([validation_error("RUN_LOCK_INITIALIZATION_INVALID", message="ownerless run lock contains unexpected entries")])
            if control_directory_is_recent(lock):
                raise RegistryBlockedError([validation_error("RUN_LOCK_INITIALIZING", message="run lock initialization is recent")])
            run_lifecycle_hook("recover.ownerless_after_age_check", lock=lock)
            quarantine = state / f"lock-initialization-quarantine-{uuid.uuid4()}"
            if quarantine.exists() or quarantine.is_symlink():
                raise RegistryBlockedError([validation_error("RUN_LOCK_RECOVERY_COLLISION", message="initialization quarantine exists")])
            os.rename(lock, quarantine)
            quarantine_started = True
            run_lifecycle_hook("recover.ownerless_after_quarantine_rename", lock=lock, quarantine=quarantine)
            return complete_ownerless_initialization_cleanup(state, run_id, claim, quarantine)
        else:
            if quarantines and ownerless_quarantines:
                raise InvalidStateError([validation_error(
                    "RUN_LOCK_RECOVERY_CONTRADICTION", message="recovery and initialization quarantines both exist",
                )])
            if ownerless_quarantines:
                quarantine_started = True
                return complete_ownerless_initialization_cleanup(
                    state, run_id, claim, ownerless_quarantines[0],
                )
            if not quarantines and claim_preexisted:
                validate_held_recovery_claim(state, run_id, claim)
                if not release_run_lock(claim):
                    raise InvalidStateError([validation_error(
                        "RUN_LOCK_RELEASE_FAILED", message="recovery claim release failed",
                    )])
                claim = None
                return True
            if len(quarantines) != 1:
                raise InvalidStateError([validation_error("RUN_LOCK_QUARANTINE_MISSING", message="exactly one recovery quarantine is required")])
            quarantine, stale_owner = quarantines[0]
            quarantine_started = True
        return complete_recovery(
            root, run_id, claim, quarantine, stale_owner, continuing_attempt=continuing_attempt,
        )
    finally:
        if claim is not None and not quarantine_started:
            release_run_lock(claim)


def pre_command_result(result, reason, status, *, data=None, errors=None):
    return gateway_result(result, reason, data, operation="PRE_COMMAND", errors=errors), status


def require_no_reserved_attempts(session):
    if any(reservation["state"] == "RESERVED" for reservation in session["reservations"]):
        raise RegistryBlockedError([validation_error(
            "RESERVATION_PENDING", message="an unresolved reserved attempt blocks new work",
        )])


def active_open_session(root, run_id):
    try:
        validate_run_start_inputs(run_id, "pre-command")
        _path, session = read_exact_run_json(
            root, run_id, (".state", "run-session.json"), "ai/schemas/run-session.schema.json",
        )
    except ValueError as error:
        raise InvalidStateError([validation_error("RUN_ID_INVALID", message=str(error))]) from error
    if session is None:
        raise InvalidStateError([validation_error("ACTIVE_RUN_REQUIRED", message="PRE_COMMAND requires an active run")])
    if session["state"] != "OPEN":
        raise RegistryBlockedError([validation_error("RUN_NOT_OPEN", message="PRE_COMMAND requires an OPEN run")])
    _root, _run_json, finalized = secure_run_artifact_path(root, run_id, ("run.json",))
    if finalized:
        raise RegistryBlockedError([validation_error("RUN_FINALIZED", message="finalized runs cannot accept commands")])
    return session


def pending_publication_profile(root, session, journal, journal_path):
    if set(journal) != {"publicationId", "runId", "referenceField", "artifact"}:
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication is not closed")])
    publication_id = journal.get("publicationId")
    try:
        parsed_id = uuid.UUID(publication_id)
    except (AttributeError, TypeError, ValueError) as error:
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication ID is invalid")]) from error
    if parsed_id.version != 4 or str(parsed_id) != publication_id or journal_path.name != f"{publication_id}.json":
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication identity is invalid")])
    if journal.get("runId") != session["runId"]:
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication run does not match")])

    artifact = journal.get("artifact")
    profiles = {
        "approvalRefs": ("ai/schemas/approval-record.schema.json", "approvals", "approvalId", "APPROVAL_AUDIT_COLLISION"),
        "policyViolationRefs": ("ai/schemas/policy-violation.schema.json", "policy-violations", "violationId", "POLICY_EVENT_COLLISION"),
    }
    profile = profiles.get(journal.get("referenceField"))
    if profile is None or not isinstance(artifact, dict):
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication type is invalid")])
    schema_path, directory, identity_field, collision_code = profile
    validate(root, artifact, schema_path)
    identity = artifact.get(identity_field)
    reference = f".ai-runs/{session['runId']}/{directory}/{identity}.json"
    if artifact.get("$id") != reference or artifact.get("runId") != session["runId"]:
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication artifact tuple is invalid")])
    return artifact, reference, journal["referenceField"], schema_path, (directory, f"{identity}.json"), collision_code


def complete_immutable_publication(root, session, acquired, journal, journal_path):
    validate_held_run_lock(root, session["runId"], acquired)
    artifact, reference, reference_field, schema_path, components, collision_code = pending_publication_profile(
        root, session, journal, journal_path,
    )
    _root, destination, exists = secure_run_artifact_path(
        root, session["runId"], components, create_parents=True,
    )
    if exists:
        existing = read_json(destination)
        validate(root, existing, schema_path)
        if existing != artifact:
            raise RegistryBlockedError([validation_error(collision_code, message="immutable artifact publication collided")])
    else:
        run_lifecycle_hook("immutable.before_artifact", path=destination, artifact=artifact, journal=journal)
        try:
            exclusive_publish_json(root, destination, artifact, schema_path)
        except FileExistsError:
            existing = read_json(destination)
            validate(root, existing, schema_path)
            if existing != artifact:
                raise RegistryBlockedError([validation_error(collision_code, message="immutable artifact publication collided")])
    run_lifecycle_hook("immutable.after_artifact", path=destination, artifact=artifact, journal=journal)

    if reference not in session[reference_field]:
        replacement = json.loads(json.dumps(session))
        replacement[reference_field].append(reference)
        replace_run_session(
            root, Path(root).resolve(strict=True) / replacement["$id"], replacement, acquired,
            expected_session=session,
        )
        session = replacement
    run_lifecycle_hook("immutable.after_session", path=destination, artifact=artifact, journal=journal)
    journal_path.unlink()
    fsync_directory(journal_path.parent)
    try:
        journal_path.parent.rmdir()
        fsync_directory(journal_path.parent.parent)
    except OSError:
        pass
    return session


def resume_immutable_publications(root, session, acquired):
    validate_held_run_lock(root, session["runId"], acquired)
    _root, run, _resolved = secure_run_path(root, session["runId"])
    pending = run / ".state" / "immutable-publications"
    try:
        metadata = pending.lstat()
    except FileNotFoundError:
        return session
    except OSError as error:
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication directory is unavailable")]) from error
    if path_is_link_or_reparse(pending, metadata) or not stat.S_ISDIR(metadata.st_mode):
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication directory is unsafe")])
    try:
        entries = sorted(pending.iterdir(), key=lambda path: path.name.encode("utf-8"))
    except OSError as error:
        raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publications cannot be inspected")]) from error
    for journal_path in entries:
        try:
            entry_metadata = journal_path.lstat()
        except OSError as error:
            raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication is unavailable")]) from error
        if path_is_link_or_reparse(journal_path, entry_metadata) or not stat.S_ISREG(entry_metadata.st_mode) or journal_path.suffix != ".json":
            raise InvalidStateError([validation_error("IMMUTABLE_PUBLICATION_INVALID", message="pending publication entry is unsafe")])
        journal = read_json(journal_path)
        session = complete_immutable_publication(root, session, acquired, journal, journal_path)
    return session


def publish_immutable_artifact(root, session, acquired, artifact, reference_field):
    validate_held_run_lock(root, session["runId"], acquired)
    publication_id = str(uuid.uuid4())
    journal = {
        "publicationId": publication_id,
        "runId": session["runId"],
        "referenceField": reference_field,
        "artifact": artifact,
    }
    _root, journal_path, exists = secure_run_artifact_path(
        root, session["runId"], (".state", "immutable-publications", f"{publication_id}.json"),
        create_parents=True,
    )
    if exists:
        raise RegistryBlockedError([validation_error("IMMUTABLE_PUBLICATION_COLLISION", message="pending publication already exists")])
    pending_publication_profile(root, session, journal, journal_path)
    try:
        exclusive_write(journal_path, compact(journal) + "\n")
        fsync_directory(journal_path.parent)
    except FileExistsError as error:
        raise RegistryBlockedError([validation_error("IMMUTABLE_PUBLICATION_COLLISION", message="pending publication already exists")]) from error
    run_lifecycle_hook("immutable.after_journal", path=journal_path, artifact=artifact, journal=journal)
    return complete_immutable_publication(root, session, acquired, journal, journal_path)


def immutable_policy_event(root, session, acquired, event_type, command_id, description, operation="PRE_COMMAND"):
    run_id = session["runId"]
    event_id = str(uuid.uuid4())
    reference = f".ai-runs/{run_id}/policy-violations/{event_id}.json"
    event = {
        "$schema": "ai/schemas/policy-violation.schema.json",
        "$id": reference,
        "schemaVersion": 1,
        "violationId": event_id,
        "runId": run_id,
        "type": event_type,
        "description": description,
        "detectedAt": utc_now(),
        "blocking": True,
        "context": {"commandId": command_id, "toolName": None, "path": None, "operation": operation},
    }
    return publish_immutable_artifact(root, session, acquired, event, "policyViolationRefs")


def make_read_only(path):
    try:
        os.chmod(path, 0o400)
    except OSError as error:
        raise EvidenceWriteUncertainty("published evidence could not be made read-only") from error


def reservation_for_process(session, process_attempt):
    matches = [reservation for reservation in session["reservations"] if (
        reservation["commandId"] == process_attempt.get("commandId")
        and reservation["attemptId"] == process_attempt.get("attemptId")
    )]
    if len(matches) != 1:
        raise InvalidStateError([validation_error(
            "PROCESS_RESERVATION_MISMATCH", message="process attempt must match exactly one reservation",
        )])
    reservation = matches[0]
    if any(process_attempt.get(name) != reservation[name] for name in (
        "argvHash", "inputFingerprint", "environmentFingerprint", "reservedAt",
    )):
        raise InvalidStateError([validation_error(
            "PROCESS_RESERVATION_MISMATCH", message="process facts do not match the reservation",
        )])
    return reservation


def remove_owned_file(path):
    try:
        path.chmod(0o600)
    except OSError:
        pass
    try:
        path.unlink()
    except FileNotFoundError:
        pass


def stage_fsynced_file(destination, content):
    descriptor, temporary = tempfile.mkstemp(prefix=f".{destination.name}.", dir=destination.parent)
    temporary = Path(temporary)
    try:
        try:
            os.fchmod(descriptor, 0o600)
        except (AttributeError, OSError):
            pass
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        return temporary
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        remove_owned_file(temporary)
        raise


def atomic_rename_noreplace(temporary, destination):
    if destination.exists() or destination.is_symlink():
        raise FileExistsError(destination)
    try:
        if os.name == "posix":
            if not sys.platform.startswith("linux"):
                raise EvidenceWriteUncertainty("atomic no-replace rename is unsupported on this POSIX host")
            libc = ctypes.CDLL(None, use_errno=True)
            renameat2 = getattr(libc, "renameat2", None)
            if renameat2 is None:
                raise EvidenceWriteUncertainty("renameat2 is unavailable")
            result = renameat2(
                -100, os.fsencode(temporary), -100, os.fsencode(destination), 1,
            )
            if result != 0:
                error_number = ctypes.get_errno()
                if error_number == errno.EEXIST:
                    raise FileExistsError(destination)
                raise OSError(error_number, os.strerror(error_number))
        else:
            os.rename(temporary, destination)
    except (FileExistsError, EvidenceWriteUncertainty):
        raise
    except OSError as error:
        raise EvidenceWriteUncertainty("atomic evidence rename failed") from error
    fsync_directory(destination.parent)


def persisted_process_attempt(root, process_attempt):
    try:
        _path, persisted = read_exact_run_json(
            root, process_attempt["runId"],
            ("process-attempts", process_attempt["commandId"], f"{process_attempt['attemptId']}.json"),
            "ai/schemas/process-attempt.schema.json",
        )
        return persisted
    except (InvalidStateError, OSError, TypeError, ValueError):
        return None


def publish_process_attempt(root, session, acquired, process_attempt):
    root = Path(root).resolve(strict=True)
    validate_held_run_lock(root, session["runId"], acquired)
    validate(root, process_attempt, "ai/schemas/process-attempt.schema.json")
    reservation = reservation_for_process(session, process_attempt)
    if reservation["state"] != "RESERVED":
        raise RegistryBlockedError([validation_error(
            "RESERVATION_ALREADY_TERMINAL", message="reservation already has a terminal outcome",
        )])
    reference = process_attempt["$id"]
    _root, destination, exists = secure_run_artifact_path(
        root, session["runId"],
        ("process-attempts", process_attempt["commandId"], f"{process_attempt['attemptId']}.json"),
        create_parents=True,
    )
    if exists:
        winner = persisted_process_attempt(root, process_attempt)
        if winner != process_attempt:
            raise RegistryBlockedError([validation_error(
                "PROCESS_ATTEMPT_COLLISION", message="process attempt publication collided",
            )])
    else:
        temporary = None
        published = False
        try:
            content = (compact(process_attempt) + "\n").encode("utf-8")
            temporary = stage_fsynced_file(destination, content)
            run_lifecycle_hook("post.process.after_temp", path=temporary, artifact=process_attempt)
            make_read_only(temporary)
            run_lifecycle_hook("post.process.after_chmod", path=temporary, artifact=process_attempt)
            atomic_rename_noreplace(temporary, destination)
            temporary = None
            published = True
            run_lifecycle_hook("post.process.after_rename", path=destination, artifact=process_attempt)
        except Exception:
            if temporary is not None:
                remove_owned_file(temporary)
            if published:
                remove_owned_file(destination)
                fsync_directory(destination.parent)
            raise
    replacement = json.loads(json.dumps(session))
    if reference not in replacement["processAttemptRefs"]:
        replacement["processAttemptRefs"].append(reference)
        replace_run_session(root, root / replacement["$id"], replacement, acquired, expected_session=session)
    run_lifecycle_hook("post.process.after_session", path=destination, artifact=process_attempt)
    return replacement


def terminal_publication_profile(command_result, stdout, stderr):
    result_bytes = (compact(command_result) + "\n").encode("utf-8")
    contents = {"result": result_bytes}
    if command_result["result"] in ("PASS", "FAIL"):
        contents = {"stdout": stdout, "stderr": stderr, "result": result_bytes}
    return contents, {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}


def terminal_publication_paths(root, command_result):
    run = Path(root) / ".ai-runs" / command_result["runId"]
    command_id = command_result["commandId"]
    attempt_id = command_result["attemptId"]
    return {
        "stdout": run / "logs" / command_id / f"{attempt_id}.stdout.log",
        "stderr": run / "logs" / command_id / f"{attempt_id}.stderr.log",
        "result": run / "commands" / command_id / f"{attempt_id}.json",
        "journal": run / ".state" / f"{command_id}.{attempt_id}.terminal-publication.json",
    }


def ensure_terminal_journal(paths, profile):
    journal = {"schemaVersion": 1, "hashes": profile}
    if paths["journal"].exists():
        try:
            existing = json.loads(paths["journal"].read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise EvidenceWriteUncertainty("terminal publication journal is unreadable") from error
        if existing != journal:
            raise RegistryBlockedError([validation_error(
                "TERMINAL_PUBLICATION_COLLISION", message="terminal publication journal collided",
            )])
    else:
        exclusive_write(paths["journal"], compact(journal) + "\n")
    return paths["journal"]


def matching_publication_file(path, digest):
    try:
        return path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == digest
    except OSError:
        return False


def terminal_journal_bytes(profile):
    return (compact({"schemaVersion": 1, "hashes": profile}) + "\n").encode("utf-8")


def remove_exact_terminal_journal(root, command_result, profile):
    run_id = command_result["runId"]
    command_id = command_result["commandId"]
    attempt_id = command_result["attemptId"]
    _root, journal, exists = secure_run_artifact_path(
        root, run_id,
        (".state", f"{command_id}.{attempt_id}.terminal-publication.json"),
    )
    if not exists:
        return
    expected = terminal_journal_bytes(profile)
    try:
        before = journal.lstat()
        if journal.read_bytes() != expected:
            raise RegistryBlockedError([validation_error(
                "TERMINAL_PUBLICATION_COLLISION",
                message="terminal publication journal does not match committed evidence",
            )])
        _root, current, current_exists = secure_run_artifact_path(
            root, run_id,
            (".state", f"{command_id}.{attempt_id}.terminal-publication.json"),
        )
        after = current.lstat() if current_exists else None
        identity = lambda metadata: (
            metadata.st_dev, metadata.st_ino, metadata.st_size, metadata.st_mtime_ns,
        )
        if after is None or identity(before) != identity(after) or current.read_bytes() != expected:
            raise RegistryBlockedError([validation_error(
                "TERMINAL_PUBLICATION_COLLISION",
                message="terminal publication journal changed before cleanup",
            )])
        current.unlink()
        fsync_directory(current.parent)
    except RegistryBlockedError:
        raise
    except OSError as error:
        raise EvidenceWriteUncertainty("terminal publication journal cleanup failed") from error


def committed_terminal_result(root, session, reservation, acquired):
    validate_held_run_lock(root, session["runId"], acquired)
    run_id = session["runId"]
    command_id = reservation["commandId"]
    attempt_id = reservation["attemptId"]
    command_ref = f".ai-runs/{run_id}/commands/{command_id}/{attempt_id}.json"
    process_ref = f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json"
    if (
        reservation["state"] not in ("PASS", "FAIL", "BLOCKED")
        or reservation.get("commandResultRef") != command_ref
        or reservation.get("processAttemptRef") != process_ref
        or command_ref not in session["commandResultRefs"]
        or process_ref not in session["processAttemptRefs"]
    ):
        raise RegistryBlockedError([validation_error(
            "TERMINAL_PUBLICATION_STATE_INVALID",
            message="terminal publication cleanup requires an exact committed session tuple",
        )])
    _path, command_result = read_exact_run_json(
        root, run_id, ("commands", command_id, f"{attempt_id}.json"),
        "ai/schemas/command-result.schema.json",
    )
    if (
        command_result is None
        or command_result.get("$id") != command_ref
        or command_result.get("processAttemptRef") != process_ref
        or command_result.get("result") != reservation["state"]
        or command_result.get("endedAt") != reservation.get("terminalAt")
    ):
        raise RegistryBlockedError([validation_error(
            "TERMINAL_PUBLICATION_STATE_INVALID",
            message="terminal publication cleanup requires the committed command result",
        )])
    return command_result


def rollback_terminal_publication(root, command_result):
    paths = terminal_publication_paths(root, command_result)
    if not paths["journal"].is_file():
        return
    try:
        profile = json.loads(paths["journal"].read_text(encoding="utf-8"))["hashes"]
    except (KeyError, OSError, ValueError):
        return
    for name, digest in profile.items():
        path = paths[name]
        if matching_publication_file(path, digest):
            remove_owned_file(path)
            fsync_directory(path.parent)


def complete_terminal_publication(root, command_result):
    paths = terminal_publication_paths(root, command_result)
    result_bytes = (compact(command_result) + "\n").encode("utf-8")
    if not matching_publication_file(paths["result"], hashlib.sha256(result_bytes).hexdigest()):
        raise RegistryBlockedError([validation_error(
            "TERMINAL_PUBLICATION_COLLISION",
            message="committed command result does not match terminal publication",
        )])
    profile = {"result": hashlib.sha256(result_bytes).hexdigest()}
    if command_result["result"] in ("PASS", "FAIL"):
        expected_stdout = f".ai-runs/{command_result['runId']}/logs/{command_result['commandId']}/{command_result['attemptId']}.stdout.log"
        expected_stderr = f".ai-runs/{command_result['runId']}/logs/{command_result['commandId']}/{command_result['attemptId']}.stderr.log"
        if (
            command_result.get("stdoutPath") != expected_stdout
            or command_result.get("stderrPath") != expected_stderr
        ):
            raise RegistryBlockedError([validation_error(
                "TERMINAL_PUBLICATION_STATE_INVALID",
                message="committed command result log references are not exact",
            )])
        for name in ("stdout", "stderr"):
            path = paths[name]
            _root, exact_path, exists = secure_run_artifact_path(
                root, command_result["runId"],
                ("logs", command_result["commandId"], path.name),
            )
            if not exists:
                raise EvidenceWriteUncertainty("committed terminal log is unavailable")
            profile[name] = hashlib.sha256(exact_path.read_bytes()).hexdigest()
        profile = {name: profile[name] for name in ("stdout", "stderr", "result")}
    remove_exact_terminal_journal(root, command_result, profile)


def publish_command_result(root, session, acquired, command_result, stdout, stderr):
    root = Path(root).resolve(strict=True)
    validate_held_run_lock(root, session["runId"], acquired)
    validate(root, command_result, "ai/schemas/command-result.schema.json")
    matches = [item for item in session["reservations"] if (
        item["commandId"], item["attemptId"]
    ) == (command_result["commandId"], command_result["attemptId"])]
    if len(matches) != 1 or command_result["processAttemptRef"] not in session["processAttemptRefs"]:
        raise InvalidStateError([validation_error(
            "COMMAND_RESERVATION_MISMATCH", message="command result does not match the reserved process tuple",
        )])
    if matches[0]["state"] != "RESERVED":
        raise RegistryBlockedError([validation_error(
            "RESERVATION_ALREADY_TERMINAL", message="reservation already has a terminal outcome",
        )])
    if command_result["result"] in ("PASS", "FAIL"):
        if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
            raise EvidenceWriteUncertainty("terminal PASS or FAIL requires sealed scrubbed logs")
    elif stdout is not None or stderr is not None:
        raise EvidenceWriteUncertainty("blocked command results cannot publish logs")
    contents, profile = terminal_publication_profile(command_result, stdout, stderr)
    paths = terminal_publication_paths(root, command_result)
    paths["result"].parent.mkdir(parents=True, exist_ok=True)
    if "stdout" in contents:
        paths["stdout"].parent.mkdir(parents=True, exist_ok=True)
    ensure_terminal_journal(paths, profile)
    staged = {}
    published = []
    try:
        for name, content in contents.items():
            path = paths[name]
            if path.exists() or path.is_symlink():
                if not matching_publication_file(path, profile[name]):
                    raise FileExistsError(path)
                continue
            staged[name] = stage_fsynced_file(path, content)
        for temporary in staged.values():
            make_read_only(temporary)
        run_lifecycle_hook("post.command.after_chmod", journal=paths["journal"], artifact=command_result)
        for name in ("stdout", "stderr", "result"):
            if name not in contents or name not in staged:
                continue
            atomic_rename_noreplace(staged[name], paths[name])
            staged[name] = None
            published.append(paths[name])
            run_lifecycle_hook(f"post.command.after_{name}", path=paths[name], artifact=command_result)
    except Exception:
        for temporary in staged.values():
            if temporary is not None:
                remove_owned_file(temporary)
        for path in published:
            remove_owned_file(path)
            fsync_directory(path.parent)
        raise
    return paths["result"]



def post_command_data(process_attempt):
    run_id = process_attempt["runId"]
    command_id = process_attempt["commandId"]
    attempt_id = process_attempt["attemptId"]
    return {
        "runId": run_id,
        "commandId": command_id,
        "attemptId": attempt_id,
        "processExitCode": process_attempt["processExitCode"],
        "processAttemptRef": f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json",
        "commandResultRef": f".ai-runs/{run_id}/commands/{command_id}/{attempt_id}.json",
    }



def authoritative_post_data(root, data):
    if data is None:
        return None
    authoritative = dict(data, processExitCode=None)
    try:
        _path, persisted = read_exact_run_json(
            root, data["runId"],
            ("process-attempts", data["commandId"], f"{data['attemptId']}.json"),
            "ai/schemas/process-attempt.schema.json",
        )
        if persisted is not None:
            authoritative = post_command_data(persisted)
    except (InvalidStateError, OSError, TypeError, ValueError):
        pass
    return authoritative

def post_command(root, process_attempt, evidence=None):
    root = Path(root).resolve()
    acquired = None
    process_published = False
    data = post_command_data(process_attempt) if isinstance(process_attempt, dict) and all(
        name in process_attempt for name in ("runId", "commandId", "attemptId", "processExitCode")
    ) else None
    try:
        validate(root, process_attempt, "ai/schemas/process-attempt.schema.json")
        requires_logs = (
            process_attempt["termination"] == "EXITED"
            and process_attempt["redactionStatus"] == "SCRUBBED"
        )
        if requires_logs:
            if not isinstance(evidence, ScrubbedEvidence) or not evidence.is_authentic():
                raise InvalidStateError([validation_error(
                    "SCRUBBED_EVIDENCE_REQUIRED",
                    message="terminal PASS or FAIL requires evidence produced by the bounded scrubber",
                )])
            stdout, stderr = evidence.stdout, evidence.stderr
        elif evidence is not None:
            raise InvalidStateError([validation_error(
                "UNEXPECTED_CAPTURE_EVIDENCE", message="non-log outcomes cannot publish capture evidence",
            )])
        else:
            stdout, stderr = None, None
        run_id = process_attempt["runId"]
        acquired = acquire_run_lock(
            root, run_id,
            continuing_attempt=(process_attempt["commandId"], process_attempt["attemptId"]),
        )
        session = active_open_session(root, run_id)
        validate_held_run_lock(root, run_id, acquired)
        reservation = reservation_for_process(session, process_attempt)
        if reservation["state"] != "RESERVED":
            command_result = committed_terminal_result(root, session, reservation, acquired)
            complete_terminal_publication(root, command_result)
            raise RegistryBlockedError([validation_error(
                "RESERVATION_ALREADY_TERMINAL", message="reservation already has a terminal outcome",
            )])
        session = publish_process_attempt(root, session, acquired, process_attempt)
        process_published = True

        termination = process_attempt["termination"]
        redaction = process_attempt["redactionStatus"]
        exit_code = process_attempt["processExitCode"]
        redaction_uncertain = isinstance(process_attempt.get("reason"), str) and process_attempt["reason"].startswith(
            "REDACTION_UNCERTAINTY:"
        )
        if process_attempt["launchStatus"] == "SPAWN_FAILED":
            terminal, status, reason = "BLOCKED", 2, "SPAWN_FAILED"
        elif redaction == "UNSCRUBBED" or redaction_uncertain:
            terminal, status, reason = "BLOCKED", 2, "UNSCRUBBED_EVIDENCE"
            session = immutable_policy_event(
                root, session, acquired, "UNSCRUBBED_EVIDENCE", process_attempt["commandId"],
                "Captured process evidence could not be scrubbed with certainty", operation="POST_COMMAND",
            )
        elif termination in ("TIMED_OUT", "RESOURCE_LIMIT"):
            terminal, status, reason = "BLOCKED", 2, termination
        elif termination == "EXITED" and redaction == "SCRUBBED" and exit_code == 0:
            terminal, status, reason = "PASS", 0, None
        elif termination == "EXITED" and redaction == "SCRUBBED" and isinstance(exit_code, int):
            terminal, status, reason = "FAIL", 1, "CHILD_EXIT_NONZERO"
        else:
            raise InvalidStateError([validation_error(
                "PROCESS_OUTCOME_INVALID", message="process attempt does not map to an approved outcome",
            )])

        command_result = {
            "$schema": "ai/schemas/command-result.schema.json",
            "$id": data["commandResultRef"],
            "schemaVersion": 1,
            "runId": process_attempt["runId"],
            "commandId": process_attempt["commandId"],
            "attemptId": process_attempt["attemptId"],
            "processAttemptRef": data["processAttemptRef"],
            "startedAt": process_attempt["startedAt"] or process_attempt["reservedAt"],
            "endedAt": process_attempt["endedAt"],
            "result": terminal,
            "processExitCode": exit_code if terminal in ("PASS", "FAIL") else None,
            "argvHash": process_attempt["argvHash"] if terminal in ("PASS", "FAIL") else None,
            "inputFingerprint": process_attempt["inputFingerprint"] if terminal in ("PASS", "FAIL") else None,
            "environmentFingerprint": process_attempt["environmentFingerprint"] if terminal in ("PASS", "FAIL") else None,
            "stdoutPath": f".ai-runs/{run_id}/logs/{process_attempt['commandId']}/{process_attempt['attemptId']}.stdout.log" if terminal in ("PASS", "FAIL") else None,
            "stderrPath": f".ai-runs/{run_id}/logs/{process_attempt['commandId']}/{process_attempt['attemptId']}.stderr.log" if terminal in ("PASS", "FAIL") else None,
            "redactionApplied": terminal in ("PASS", "FAIL"),
            "reason": reason,
        }
        publish_command_result(root, session, acquired, command_result, stdout, stderr)
        replacement = json.loads(json.dumps(session))
        target = reservation_for_process(replacement, process_attempt)
        if target["state"] != "RESERVED":
            raise RegistryBlockedError([validation_error(
                "RESERVATION_ALREADY_TERMINAL", message="reservation terminal transition raced",
            )])
        target.update({
            "state": terminal,
            "commandResultRef": data["commandResultRef"],
            "processAttemptRef": data["processAttemptRef"],
            "terminalAt": process_attempt["endedAt"],
        })
        replacement["commandResultRefs"].append(data["commandResultRef"])
        run_lifecycle_hook("post.command.before_session", artifact=command_result)
        replace_run_session(root, root / replacement["$id"], replacement, acquired, expected_session=session)
        try:
            run_lifecycle_hook("post.command.after_session", artifact=command_result)
            complete_terminal_publication(root, command_result)
        except (EvidenceWriteUncertainty, OSError):
            pass
        result = gateway_result(terminal, reason, data, operation="POST_COMMAND")
        return publish_result(root, result, status)
    except EvidenceWriteUncertainty:
        if "command_result" in locals():
            rollback_terminal_publication(root, command_result)
        if acquired is not None:
            try:
                session = active_open_session(root, process_attempt["runId"])
                session = immutable_policy_event(
                    root, session, acquired, "UNSCRUBBED_EVIDENCE", process_attempt["commandId"],
                    "Evidence publication could not be proven complete", operation="POST_COMMAND",
                )
            except (InvalidStateError, RegistryBlockedError, OSError, ValueError):
                pass
        if data is not None:
            return publish_result(root, gateway_result(
                "BLOCKED", "EVIDENCE_WRITE_UNCERTAINTY", data, operation="POST_COMMAND",
            ), 2)
        return publish_result(root, gateway_result(
            "INVALID_STATE", "POST_COMMAND_INVALID", None, operation="POST_COMMAND",
        ), 5)
    except RegistryBlockedError as error:
        if data is not None:
            data = authoritative_post_data(root, data)
            return publish_result(root, gateway_result(
                "BLOCKED", error.errors[0]["code"], data, operation="POST_COMMAND", errors=error.errors,
            ), 2)
        return publish_result(root, gateway_result(
            "INVALID_STATE", "POST_COMMAND_INVALID", None, operation="POST_COMMAND",
        ), 5)
    except (FileExistsError, OSError):
        if "command_result" in locals():
            rollback_terminal_publication(root, command_result)
        if data is not None:
            data = authoritative_post_data(root, data)
            return publish_result(root, gateway_result(
                "BLOCKED", "TERMINAL_PUBLICATION_FAILED", data, operation="POST_COMMAND",
            ), 2)
        return publish_result(root, gateway_result(
            "INVALID_STATE", "POST_COMMAND_INVALID", None, operation="POST_COMMAND",
        ), 5)
    except (InvalidStateError, TypeError, ValueError) as error:
        errors = error.errors if isinstance(error, InvalidStateError) else None
        return publish_result(root, gateway_result(
            "INVALID_STATE", errors[0]["code"] if errors else "POST_COMMAND_INVALID", None,
            operation="POST_COMMAND", errors=errors,
        ), 5)
    finally:
        if acquired is not None:
            release_run_lock(acquired)


def approval_source_path(root, reference):
    if not isinstance(reference, str) or not reference:
        raise InvalidStateError([validation_error("APPROVAL_REFERENCE_INVALID", message="approval reference is invalid")])
    candidate = Path(reference)
    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
        raise InvalidStateError([validation_error("APPROVAL_REFERENCE_INVALID", message="approval reference must be repository relative")])
    if forbidden_parameter_path_parts(candidate.parts):
        raise InvalidStateError([validation_error("APPROVAL_REFERENCE_FORBIDDEN", message="approval reference is forbidden")])
    try:
        repository_root = Path(root).resolve(strict=True)
        path = (repository_root / candidate).resolve(strict=True)
        path.relative_to(repository_root)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error("APPROVAL_REFERENCE_INVALID", message="approval reference is unavailable")]) from error
    if path.is_symlink() or not path.is_file():
        raise InvalidStateError([validation_error("APPROVAL_REFERENCE_INVALID", message="approval reference is not a regular file")])
    return path


def done_claim_source_path(root, run_id, reference):
    if not isinstance(reference, str) or not reference:
        raise InvalidStateError([validation_error("DONE_CLAIM_REFERENCE_INVALID", message="done claim reference is invalid")])
    candidate = Path(reference)
    if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
        raise InvalidStateError([validation_error("DONE_CLAIM_REFERENCE_INVALID", message="done claim reference must be repository relative")])
    try:
        repository_root = Path(root).resolve(strict=True)
        path = (repository_root / candidate).resolve(strict=True)
        path.relative_to(repository_root)
        expected_run = (repository_root / ".ai-runs" / run_id).resolve(strict=True)
        path.relative_to(expected_run)
    except (OSError, ValueError) as error:
        raise InvalidStateError([validation_error("DONE_CLAIM_REFERENCE_INVALID", message="done claim reference is unavailable")]) from error
    if path.is_symlink() or not path.is_file():
        raise InvalidStateError([validation_error("DONE_CLAIM_REFERENCE_INVALID", message="done claim reference is not a regular file")])
    return path


def persist_approval_audit(root, session, acquired, approval_ref, command):
    source = approval_source_path(root, approval_ref)
    approval = read_json(source)
    validate(root, approval, "ai/schemas/approval-record.schema.json")
    expected_type = f"{command['classification']}_COMMAND"
    approval_id = approval.get("approvalId")
    expected_ref = f".ai-runs/{session['runId']}/approvals/{approval_id}.json"
    if (
        approval.get("runId") != session["runId"]
        or approval.get("scope") != command["id"]
        or approval.get("type") != expected_type
        or approval.get("$id") != expected_ref
        or not approval.get("externalReference")
    ):
        raise InvalidStateError([validation_error("APPROVAL_AUDIT_MISMATCH", message="approval audit does not match this run and command")])
    return publish_immutable_artifact(root, session, acquired, approval, "approvalRefs")


def prerequisite_evidence(root, session, prerequisite_ids):
    run_id = session["runId"]
    for prerequisite_id in prerequisite_ids:
        marker = f"/commands/{prerequisite_id}/"
        candidates = [reference for reference in session["commandResultRefs"] if marker in reference]
        if not candidates:
            raise RegistryBlockedError([validation_error("PREREQUISITE_PASS_MISSING", message="same-run prerequisite PASS evidence is missing")])
        for reference in candidates:
            prefix = f".ai-runs/{run_id}/commands/{prerequisite_id}/"
            suffix = reference[len(prefix):] if reference.startswith(prefix) else ""
            if not suffix.endswith(".json") or "/" in suffix or not suffix[:-5]:
                raise InvalidStateError([validation_error("PREREQUISITE_REFERENCE_INVALID", message="prerequisite reference is outside the current run or malformed")])
            attempt_id = suffix[:-5]
            _path, result = read_exact_run_json(
                root, run_id, ("commands", prerequisite_id, f"{attempt_id}.json"), "ai/schemas/command-result.schema.json",
            )
            if result is None:
                raise InvalidStateError([validation_error("PREREQUISITE_REFERENCE_MISSING", message="listed prerequisite evidence is missing")])
            if (
                result.get("$id") != reference
                or result.get("runId") != run_id
                or result.get("commandId") != prerequisite_id
                or result.get("attemptId") != attempt_id
                or result.get("result") != "PASS"
            ):
                raise InvalidStateError([validation_error("PREREQUISITE_EVIDENCE_INVALID", message="prerequisite evidence tuple must be same-run PASS")])


def normalized_rerun_reason(root, reference):
    path = approval_source_path(root, reference)
    try:
        encoded = path.read_bytes()
        text = encoded.decode("utf-8", errors="strict")
    except (OSError, UnicodeDecodeError) as error:
        raise ValueError("RERUN_REASON_INVALID") from error
    if text.endswith("\r\n"):
        text = text[:-2]
    elif text.endswith("\n"):
        text = text[:-1]
    normalized = text.encode("utf-8")
    if not text or "\r" in text or "\n" in text or len(text) > RERUN_REASON_MAX_SCALARS or len(normalized) > RERUN_REASON_MAX_BYTES:
        raise ValueError("RERUN_REASON_INVALID")
    return hashlib.sha256(normalized).hexdigest()


ARTIFACT_KINDS = (
    ("commands", "COMMAND_RESULT"),
    ("process-attempts", "PROCESS_ATTEMPT"),
    ("logs", None),
    ("approvals", "APPROVAL"),
    ("policy-violations", "POLICY_VIOLATION"),
    ("gate-results", "GATE_RESULT"),
)


def artifact_kind_for(path):
    parts = path.parts
    if "logs" in parts:
        if path.name.endswith(".stdout.log"):
            return "STDOUT_LOG"
        if path.name.endswith(".stderr.log"):
            return "STDERR_LOG"
    for directory, kind in ARTIFACT_KINDS:
        if directory in parts and kind is not None:
            return kind
    if path.name == "done-claim.json":
        return "DONE_CLAIM"
    return None


def run_relative_artifact_ref(root, path):
    return path.relative_to(Path(root).resolve(strict=True)).as_posix()


def read_run_reference(root, reference, schema_path):
    path = Path(root).resolve(strict=True) / reference
    instance = read_json(path)
    validate(root, instance, schema_path)
    return path, instance


def done_claim_exit_for(result):
    return {
        "PASS": 0,
        "FAIL": 1,
        "BLOCKED": 2,
        "NOT_CONFIGURED": 3,
        "POLICY_VIOLATION": 4,
        "INVALID_STATE": 5,
    }[result]


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


def done_claim_semantic_result(root, session, claim):
    if claim.get("$id") != f".ai-runs/{session['runId']}/done-claim.json":
        return "INVALID_STATE", "DONE_CLAIM_REFERENCE_MISMATCH"
    if claim.get("runId") != session["runId"] or claim.get("taskKey") != session["taskKey"]:
        return "INVALID_STATE", "DONE_CLAIM_RUN_MISMATCH"
    resolved_evidence = validated_done_claim_evidence(root, session, claim)
    validate_not_run_consistency(session, claim)
    if claim.get("implementationStatus") != "PASS" or claim.get("overallResult") != "PASS":
        return "BLOCKED", "DONE_CLAIM_NOT_PASS"
    if claim.get("blockers"):
        return "BLOCKED", "DONE_CLAIM_BLOCKERS_PRESENT"
    checks = claim.get("checks", [])
    if not checks:
        return "BLOCKED", "COMPLETION_WITHOUT_EVIDENCE"
    if claim.get("unexpected500Status") != "PASS" or claim.get("unhandledExceptionStatus") != "PASS":
        return "BLOCKED", "DONE_CLAIM_UNRESOLVED_RUNTIME_RISK"
    session_command_refs = set(session["commandResultRefs"])
    claimed_refs = set(claim.get("evidenceRefs", []))
    if not claimed_refs:
        return "BLOCKED", "COMPLETION_WITHOUT_EVIDENCE"
    for check in checks:
        result = check.get("result")
        if result == "FAIL":
            return "FAIL", "DONE_CLAIM_FAILED_CHECK"
        if result in ("BLOCKED", "NOT_CONFIGURED", "NOT_APPLICABLE", "SKIPPED_WITH_REASON"):
            return "BLOCKED", "DONE_CLAIM_CHECK_NOT_PASS"
        if result != "PASS":
            return "INVALID_STATE", "DONE_CLAIM_CHECK_INVALID"
        if not check.get("evidenceRefs"):
            return "BLOCKED", "COMPLETION_WITHOUT_EVIDENCE"
    for reference in claimed_refs:
        if reference not in session_command_refs:
            continue
        command_result = resolved_evidence[reference]
        if command_result.get("result") == "FAIL":
            return "FAIL", "DONE_CLAIM_HIDDEN_FAILED_LEAF"
        if command_result.get("result") != "PASS":
            return "BLOCKED", "DONE_CLAIM_LEAF_NOT_PASS"
    for reference in session_command_refs:
        command_result = resolved_evidence[reference]
        if command_result.get("result") == "FAIL":
            return "FAIL", "DONE_CLAIM_HIDDEN_FAILED_LEAF"
        if command_result.get("result") != "PASS":
            return "BLOCKED", "DONE_CLAIM_LEAF_NOT_PASS"
        if reference not in claimed_refs:
            return "INVALID_STATE", "DONE_CLAIM_UNMANIFESTED_COMMAND_RESULT"
    for reference in session["policyViolationRefs"]:
        _path, event = read_run_reference(root, reference, "ai/schemas/policy-violation.schema.json")
        if event.get("blocking"):
            return "POLICY_VIOLATION", "BLOCKING_POLICY_VIOLATION"
    return "PASS", None


def expected_terminal_artifacts(session):
    expected = set()
    run_id = session["runId"]
    for reservation in session["reservations"]:
        command_id = reservation["commandId"]
        attempt_id = reservation["attemptId"]
        command_ref = f".ai-runs/{run_id}/commands/{command_id}/{attempt_id}.json"
        process_ref = f".ai-runs/{run_id}/process-attempts/{command_id}/{attempt_id}.json"
        if reservation["state"] == "RESERVED":
            raise InvalidStateError([validation_error("RESERVATION_PENDING", message="reserved attempts cannot finalize")])
        if reservation.get("commandResultRef") != command_ref or reservation.get("processAttemptRef") != process_ref:
            raise InvalidStateError([validation_error("RESERVATION_ARTIFACT_MISMATCH", message="reservation terminal refs are inconsistent")])
        if command_ref not in session["commandResultRefs"] or process_ref not in session["processAttemptRefs"]:
            raise InvalidStateError([validation_error("RESERVATION_ARTIFACT_MISMATCH", message="reservation terminal refs are not listed in session")])
        _command_path, command_result = read_run_reference(session["_root"], command_ref, "ai/schemas/command-result.schema.json")
        _process_path, process_attempt = read_exact_run_json(
            session["_root"], run_id, ("process-attempts", command_id, f"{attempt_id}.json"),
            "ai/schemas/process-attempt.schema.json",
        )
        if process_attempt is None:
            raise InvalidStateError([validation_error("PROCESS_ATTEMPT_REFERENCE_MISSING", message="process attempt artifact is missing")])
        if command_result.get("processAttemptRef") != process_ref:
            raise InvalidStateError([validation_error("COMMAND_PROCESS_REF_MISMATCH", message="command result does not reference the process attempt")])
        if process_attempt.get("redactionStatus") not in ("SCRUBBED", "NOT_APPLIED"):
            raise InvalidStateError([validation_error("UNSCRUBBED_PROCESS_ATTEMPT", message="unscrubbed process attempt cannot finalize")])
        expected.update({command_ref, process_ref})
        if command_result["result"] in ("PASS", "FAIL"):
            for field in ("stdoutPath", "stderrPath"):
                if command_result.get(field) not in expected:
                    expected.add(command_result[field])
    expected.update(session["approvalRefs"])
    expected.update(session["policyViolationRefs"])
    expected.update(session["gateResultRefs"])
    return expected


def validate_evidence_closure(root, session, include_final_refs=()):
    session = json.loads(json.dumps(session))
    session["_root"] = root
    expected = expected_terminal_artifacts(session)
    expected.update(include_final_refs)
    root = Path(root).resolve(strict=True)
    run = root / ".ai-runs" / session["runId"]
    actual = set()
    for path in run.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(run).as_posix()
        if relative.startswith(".state/") or relative == "claim-input.json":
            continue
        actual.add(path.relative_to(root).as_posix())
    unexpected = actual - expected
    missing = expected - actual
    if unexpected:
        raise InvalidStateError([validation_error("UNREFERENCED_FINAL_ARTIFACT", message="run contains unreferenced final artifacts")])
    if missing:
        raise InvalidStateError([validation_error("MISSING_FINAL_ARTIFACT", message="referenced final artifacts are missing")])


def generated_section(text, source):
    start = f"<!-- GENERATED:START source={source} -->"
    end = f"<!-- GENERATED:END source={source} -->"
    if start not in text or end not in text:
        raise InvalidStateError([validation_error("GENERATED_SUMMARY_MARKERS_MISSING", message="generated summary markers are missing")])
    start_index = text.index(start)
    end_index = text.index(end, start_index) + len(end)
    return text[start_index:end_index]


def command_registry_summary_lines(registry):
    verified = sum(1 for command in registry["commands"] if command["configurationStatus"] == "VERIFIED")
    return (
        f"- Updated at: `{registry['updatedAt']}`",
        f"- Registered capability records: `{len(registry['commands'])}`",
        f"- Verified command records: `{verified}`",
    )


def require_generated_summaries_current(root):
    root = Path(root).resolve(strict=True)
    state = validate_repository_instance(root, root / "ai" / "project-state.json")
    project_summary_path = root / "ai" / "project-state.md"
    project_summary = project_summary_path.read_text(encoding="utf-8")
    if summary_for(project_summary, state) != project_summary:
        raise InvalidStateError([validation_error("PROJECT_STATE_SUMMARY_STALE", message="project-state generated summary is stale")])

    registry = validate_repository_instance(root, root / "ai" / "command-registry.json")
    registry_summary = (root / "ai" / "command-registry.md").read_text(encoding="utf-8")
    registry_section = generated_section(registry_summary, "ai/command-registry.json")
    missing = [line for line in command_registry_summary_lines(registry) if line not in registry_section]
    if missing:
        raise InvalidStateError([validation_error("COMMAND_REGISTRY_SUMMARY_STALE", message="command-registry generated summary is stale")])


def publish_final_json(root, path, instance, schema_path):
    exclusive_publish_json(root, path, instance, schema_path)
    make_read_only(path)


def gate_result_artifact(root, run_id, result, reason):
    data = None
    if result == "PASS":
        data = {
            "runId": run_id,
            "taskKey": None,
            "doneClaimRef": f".ai-runs/{run_id}/done-claim.json",
            "manifestRef": f".ai-runs/{run_id}/artifact-manifest.json",
            "runRef": f".ai-runs/{run_id}/run.json",
            "gateResultRef": f".ai-runs/{run_id}/gate-results/pre-done-claim.json",
            "completenessEvaluated": False,
            "scope": "INTEGRITY_ONLY",
        }
    return gateway_result(result, reason, data, operation="PRE_DONE_CLAIM")


def final_run_result_for(gate_result):
    if gate_result in ("INVALID_STATE", "POLICY_VIOLATION"):
        return "BLOCKED"
    return gate_result


def validate_final_run_projection(run_index, claim, gate, manifest):
    expected_evidence = [
        f".ai-runs/{run_index['runId']}/done-claim.json",
        f".ai-runs/{run_index['runId']}/artifact-manifest.json",
        f".ai-runs/{run_index['runId']}/gate-results/pre-done-claim.json",
    ]

    def manifest_references(kind):
        return sorted(
            artifact["path"] for artifact in manifest["artifacts"]
            if artifact["kind"] == kind
        )

    mismatched = (
        run_index["runId"] != claim["runId"]
        or run_index["taskKey"] != claim["taskKey"]
        or run_index["result"] != final_run_result_for(gate["result"])
        or run_index["evidenceRefs"] != expected_evidence
        or sorted(run_index["commandResultRefs"]) != manifest_references("COMMAND_RESULT")
        or sorted(run_index["approvalRefs"]) != manifest_references("APPROVAL")
        or sorted(run_index["policyViolationRefs"]) != manifest_references("POLICY_VIOLATION")
        or gate.get("data") is not None and gate["data"]["manifestRef"] != manifest["$id"]
    )
    if mismatched:
        raise InvalidStateError([validation_error(
            "FINAL_RUN_PROJECTION_MISMATCH",
            message="run.json does not match claim, gate, and manifest",
        )])


def publish_finalized_run(root, session, gate_result, reason):
    run_id = session["runId"]
    ended_at = utc_now()
    run_index = {
        "$schema": "ai/schemas/run.schema.json",
        "$id": f".ai-runs/{run_id}/run.json",
        "schemaVersion": 1,
        "runId": run_id,
        "taskKey": session["taskKey"],
        "startedAt": session["startedAt"],
        "endedAt": ended_at,
        "workingDirectory": session["workingDirectory"],
        "environment": session["environment"],
        "result": final_run_result_for(gate_result),
        "commandResultRefs": session["commandResultRefs"],
        "approvalRefs": session["approvalRefs"],
        "policyViolationRefs": session["policyViolationRefs"],
        "evidenceRefs": [
            ".ai-runs/{}/done-claim.json".format(run_id),
            ".ai-runs/{}/artifact-manifest.json".format(run_id),
            ".ai-runs/{}/gate-results/pre-done-claim.json".format(run_id),
        ],
        "redactionApplied": session["redactionApplied"],
        "reason": reason or "Phase 1B integrity PASS; verification completeness NOT EVALUATED",
    }
    run_destination = Path(root).resolve(strict=True) / ".ai-runs" / run_id / "run.json"
    publish_final_json(root, run_destination, run_index, "ai/schemas/run.schema.json")
    return run_index


def publish_done_gate_manifest_run(root, session, claim, gate_result_name, gate_reason):
    run_id = session["runId"]
    claim_destination = Path(root).resolve(strict=True) / ".ai-runs" / run_id / "done-claim.json"
    if not claim_destination.exists():
        publish_final_json(root, claim_destination, claim, "ai/schemas/done-claim.schema.json")
    gate = gate_result_artifact(root, run_id, gate_result_name, gate_reason)
    if gate_result_name == "PASS":
        gate["data"]["taskKey"] = session["taskKey"]
    gate_destination = Path(root).resolve(strict=True) / ".ai-runs" / run_id / "gate-results" / "pre-done-claim.json"
    gate_destination.parent.mkdir(mode=0o700, exist_ok=True)
    publish_final_json(root, gate_destination, gate, "ai/schemas/gateway-result.schema.json")
    validate_evidence_closure(root, session, include_final_refs={
        f".ai-runs/{run_id}/done-claim.json",
        f".ai-runs/{run_id}/gate-results/pre-done-claim.json",
    })
    manifest = final_artifact_manifest(root, run_id)
    manifest_destination = Path(root).resolve(strict=True) / ".ai-runs" / run_id / "artifact-manifest.json"
    publish_final_json(root, manifest_destination, manifest, "ai/schemas/artifact-manifest.schema.json")
    publish_finalized_run(root, session, gate_result_name, gate_reason)
    shutil.rmtree(Path(root).resolve(strict=True) / ".ai-runs" / run_id / ".state")
    return gate


def finalization_artifact_refs(run_id):
    return (
        f".ai-runs/{run_id}/done-claim.json",
        f".ai-runs/{run_id}/gate-results/pre-done-claim.json",
        f".ai-runs/{run_id}/artifact-manifest.json",
    )


def expected_finalizing_session(original_session):
    finalizing = json.loads(json.dumps(original_session))
    finalizing["state"] = "FINALIZING"
    return finalizing


def read_locked_run_session(root, run_id, acquired):
    validate_held_run_lock(root, run_id, acquired)
    _session_path, session = read_exact_run_json(
        root, run_id, (".state", "run-session.json"), "ai/schemas/run-session.schema.json",
    )
    validate_held_run_lock(root, run_id, acquired)
    return session


def rollback_finalization(root: Path, original_session: dict, final_refs: Sequence[str], acquired) -> None:
    root = Path(root).resolve(strict=True)
    validate(root, original_session, "ai/schemas/run-session.schema.json")
    if original_session["state"] != "OPEN":
        raise InvalidStateError([validation_error(
            "FINALIZATION_ORIGINAL_SESSION_INVALID", message="rollback requires the exact prior OPEN session",
        )])
    run_id = original_session["runId"]
    expected_refs = finalization_artifact_refs(run_id)
    if isinstance(final_refs, (str, bytes)) or tuple(final_refs) != expected_refs:
        raise InvalidStateError([validation_error(
            "FINALIZATION_ROLLBACK_REFS_INVALID", message="rollback references are not the exact finalization set",
        )])

    validate_held_run_lock(root, run_id, acquired)
    run = root / ".ai-runs" / run_id
    try:
        (run / "run.json").lstat()
    except FileNotFoundError:
        pass
    else:
        raise RegistryBlockedError([validation_error(
            "FINALIZATION_ALREADY_PUBLISHED", message="published run.json cannot be rolled back",
        )])

    expected_finalizing = expected_finalizing_session(original_session)
    current_session = read_locked_run_session(root, run_id, acquired)
    if current_session != expected_finalizing:
        raise RegistryBlockedError([validation_error(
            "FINALIZING_SESSION_CHANGED", message="FINALIZING session changed before rollback",
        )])

    for reference in final_refs:
        validate_held_run_lock(root, run_id, acquired)
        relative = reference.removeprefix(f".ai-runs/{run_id}/")
        _root, path, exists = secure_run_artifact_path(root, run_id, tuple(relative.split("/")))
        if not exists:
            continue
        path.chmod(0o600)
        path.unlink()
        fsync_directory(path.parent)

    try:
        replace_run_session(
            root,
            run / ".state" / "run-session.json",
            original_session,
            acquired,
            expected_session=expected_finalizing,
        )
    except Exception:
        if read_locked_run_session(root, run_id, acquired) == original_session:
            return
        raise


def final_artifact_manifest(root, run_id):
    root = Path(root).resolve(strict=True)
    run = root / ".ai-runs" / run_id
    artifacts = []
    for path in sorted(run.rglob("*"), key=lambda item: item.relative_to(root).as_posix().encode("utf-8")):
        if not path.is_file():
            continue
        relative = path.relative_to(run).as_posix()
        if relative.startswith(".state/") or relative in ("artifact-manifest.json", "run.json", "claim-input.json"):
            continue
        kind = artifact_kind_for(path)
        if kind is None:
            raise InvalidStateError([validation_error("UNKNOWN_FINAL_ARTIFACT", message="final artifact has no approved kind")])
        artifacts.append({
            "path": run_relative_artifact_ref(root, path),
            "sha256": digest(path),
            "size": path.stat().st_size,
            "kind": kind,
        })
    return {
        "$schema": "ai/schemas/artifact-manifest.schema.json",
        "$id": f".ai-runs/{run_id}/artifact-manifest.json",
        "schemaVersion": 1,
        "runId": run_id,
        "generatedAt": utc_now(),
        "algorithm": "SHA-256",
        "artifacts": artifacts,
    }


def verify_finalized_run(root, run_id):
    root = Path(root).resolve()
    try:
        validate_run_start_inputs(run_id, "verify-finalized")
        run = root / ".ai-runs" / run_id
        _path, run_index = read_exact_run_json(root, run_id, ("run.json",), "ai/schemas/run.schema.json")
        if run_index is None:
            raise InvalidStateError([validation_error("FINALIZED_RUN_MISSING", message="finalized run.json is missing")])
        _manifest_path, manifest = read_exact_run_json(root, run_id, ("artifact-manifest.json",), "ai/schemas/artifact-manifest.schema.json")
        if manifest is None:
            raise InvalidStateError([validation_error("ARTIFACT_MANIFEST_MISSING", message="artifact manifest is missing")])
        manifest_paths = {artifact["path"]: artifact for artifact in manifest["artifacts"]}
        for reference, artifact in manifest_paths.items():
            path = root / reference
            if not path.is_file():
                raise InvalidStateError([validation_error("MANIFEST_ARTIFACT_MISSING", message="manifest artifact is missing")])
            if digest(path) != artifact["sha256"] or path.stat().st_size != artifact["size"]:
                raise InvalidStateError([validation_error("ARTIFACT_DIGEST_MISMATCH", message="manifest digest or size mismatch")])
        actual = set()
        for path in run.rglob("*"):
            if not path.is_file():
                continue
            relative = path.relative_to(run).as_posix()
            if relative in ("artifact-manifest.json", "run.json", "claim-input.json"):
                continue
            actual.add(path.relative_to(root).as_posix())
        if set(manifest_paths) != actual:
            raise InvalidStateError([validation_error("FINALIZED_DIRECTORY_CLOSURE_MISMATCH", message="finalized directory closure mismatches manifest")])
        _claim_path, claim = read_exact_run_json(
            root, run_id, ("done-claim.json",), "ai/schemas/done-claim.schema.json",
        )
        if claim is None:
            raise InvalidStateError([validation_error("FINAL_DONE_CLAIM_MISSING", message="final done claim is missing")])
        _gate_path, gate = read_exact_run_json(
            root, run_id, ("gate-results", "pre-done-claim.json"), "ai/schemas/gateway-result.schema.json",
        )
        if gate is None:
            raise InvalidStateError([validation_error("FINAL_GATE_RESULT_MISSING", message="final gate result is missing")])
        validate_final_run_projection(run_index, claim, gate, manifest)
        data = {
            "runId": run_id,
            "taskKey": run_index["taskKey"],
            "doneClaimRef": f".ai-runs/{run_id}/done-claim.json",
            "manifestRef": f".ai-runs/{run_id}/artifact-manifest.json",
            "runRef": f".ai-runs/{run_id}/run.json",
            "gateResultRef": f".ai-runs/{run_id}/gate-results/pre-done-claim.json",
            "completenessEvaluated": False,
            "scope": "INTEGRITY_ONLY",
        }
        return publish_result(root, gateway_result("PASS", None, data, operation="PRE_DONE_CLAIM"), 0)
    except InvalidStateError as error:
        return publish_result(root, gateway_result(
            "INVALID_STATE", error.errors[0]["code"], operation="PRE_DONE_CLAIM", errors=error.errors,
        ), 5)
    except (OSError, ValueError):
        return publish_result(root, gateway_result("INVALID_STATE", "VERIFY_FINALIZED_FAILED", operation="PRE_DONE_CLAIM"), 5)


def prepare_done_claim(root, run_id, claim_ref):
    root = Path(root).resolve()
    preflight, preflight_status = run_current_preflight(root)
    if preflight_status != 0:
        return publish_result(root, gateway_result(
            preflight["result"], preflight["reason"], operation="PRE_DONE_CLAIM", errors=preflight["errors"],
        ), preflight_status)
    acquired = None
    original_session = None
    finalization_started = False

    def recovery_required_result():
        error = validation_error(
            "FINALIZATION_RECOVERY_REQUIRED",
            message="finalization state requires explicit recovery",
        )
        return publish_result(root, gateway_result(
            "BLOCKED", error["code"], operation="PRE_DONE_CLAIM", errors=[error],
        ), 2)

    def rollback_or_recovery_required():
        if not finalization_started:
            return None
        try:
            rollback_finalization(
                root, original_session, finalization_artifact_refs(run_id), acquired,
            )
        except Exception:
            return recovery_required_result()
        return None

    try:
        validate_run_start_inputs(run_id, "done-claim")
        session = active_open_session(root, run_id)
        acquired = acquire_run_lock(root, run_id)
        session = active_open_session(root, run_id)
        validate_held_run_lock(root, run_id, acquired)
        session = resume_immutable_publications(root, session, acquired)
        require_no_reserved_attempts(session)
        original_session = json.loads(json.dumps(session))
        replacement = expected_finalizing_session(original_session)
        try:
            replace_run_session(
                root, root / replacement["$id"], replacement, acquired, expected_session=original_session,
            )
        except Exception:
            try:
                current_session = read_locked_run_session(root, run_id, acquired)
            except Exception:
                return recovery_required_result()
            if current_session == replacement:
                finalization_started = True
            elif current_session != original_session:
                return recovery_required_result()
            raise
        finalization_started = True
        session = replacement

        source = done_claim_source_path(root, run_id, claim_ref)
        claim = read_json(source)
        validate(root, claim, "ai/schemas/done-claim.schema.json")
        require_generated_summaries_current(root)
        validate_evidence_closure(root, session)
        result, reason = done_claim_semantic_result(root, session, claim)
        status = done_claim_exit_for(result)
        gate = publish_done_gate_manifest_run(root, session, claim, result, reason)
        return publish_result(root, gate, status)
    except RegistryBlockedError as error:
        recovery = rollback_or_recovery_required()
        if recovery is not None:
            return recovery
        return publish_result(root, gateway_result(
            "BLOCKED", error.errors[0]["code"], operation="PRE_DONE_CLAIM", errors=error.errors,
        ), 2)
    except InvalidStateError as error:
        recovery = rollback_or_recovery_required()
        if recovery is not None:
            return recovery
        return publish_result(root, gateway_result(
            "INVALID_STATE", error.errors[0]["code"], operation="PRE_DONE_CLAIM", errors=error.errors,
        ), 5)
    except (OSError, TypeError, ValueError) as error:
        recovery = rollback_or_recovery_required()
        if recovery is not None:
            return recovery
        return publish_result(root, gateway_result(
            "INVALID_STATE", "PRE_DONE_CLAIM_FAILED", operation="PRE_DONE_CLAIM",
        ), 5)
    finally:
        if acquired is not None:
            release_run_lock(acquired)


def pre_command(
    root,
    run_id,
    command_id,
    parameters_path=None,
    rerun_reason_path=None,
    approval_ref=None,
    source_environment=None,
    reserve=True,
):
    root = Path(root).resolve()
    preflight, preflight_status = run_current_preflight(root)
    if preflight_status != 0:
        return publish_result(root, gateway_result(
            preflight["result"], preflight["reason"], operation="PRE_COMMAND", errors=preflight["errors"],
        ), preflight_status)
    acquired = None
    try:
        validate_repository_instance(root, root / "ai" / "project-state.json")
        registry = validate_repository_instance(root, root / "ai" / "command-registry.json")
        prerequisite_order = validate_registry_semantics(root, registry)

        if not isinstance(command_id, str) or COMMAND_ID.fullmatch(command_id) is None:
            if not (root / ".ai-runs" / str(run_id)).exists():
                return publish_result(root, pre_command_result("POLICY_VIOLATION", "MALFORMED_COMMAND_ID", 4)[0], 4)
            active_open_session(root, run_id)
            acquired = acquire_run_lock(root, run_id)
            session = active_open_session(root, run_id)
            validate_held_run_lock(root, run_id, acquired)
            session = resume_immutable_publications(root, session, acquired)
            require_no_reserved_attempts(session)
            session = immutable_policy_event(root, session, acquired, "UNREGISTERED_COMMAND", command_id, "Execution intent named an invalid command ID")
            return publish_result(root, pre_command_result("POLICY_VIOLATION", "MALFORMED_COMMAND_ID", 4)[0], 4)
        command = next((item for item in registry["commands"] if item["id"] == command_id), None)
        if command is None:
            if not (root / ".ai-runs" / run_id).exists():
                return publish_result(root, pre_command_result("POLICY_VIOLATION", "COMMAND_NOT_REGISTERED", 4)[0], 4)
            active_open_session(root, run_id)
            acquired = acquire_run_lock(root, run_id)
            session = active_open_session(root, run_id)
            validate_held_run_lock(root, run_id, acquired)
            session = resume_immutable_publications(root, session, acquired)
            require_no_reserved_attempts(session)
            session = immutable_policy_event(root, session, acquired, "UNREGISTERED_COMMAND", command_id, "Execution intent named an unregistered command")
            return publish_result(root, pre_command_result("POLICY_VIOLATION", "COMMAND_NOT_REGISTERED", 4)[0], 4)

        active_open_session(root, run_id)
        acquired = acquire_run_lock(root, run_id)
        session = active_open_session(root, run_id)
        validate_held_run_lock(root, run_id, acquired)
        session = resume_immutable_publications(root, session, acquired)
        require_no_reserved_attempts(session)

        status = command["configurationStatus"]
        if status in ("UNKNOWN", "STALE", "UNCERTAIN"):
            return publish_result(root, pre_command_result("BLOCKED", "COMMAND_CONFIGURATION_BLOCKED", 2)[0], 2)
        if status == "NOT_CONFIGURED" or command["classification"] == "UNAVAILABLE":
            return publish_result(root, pre_command_result("NOT_CONFIGURED", "COMMAND_NOT_CONFIGURED", 3)[0], 3)

        if approval_ref is not None:
            session = persist_approval_audit(root, session, acquired, approval_ref, command)
        if command["classification"] in ("RISKY", "DESTRUCTIVE"):
            if command["classification"] == "DESTRUCTIVE":
                session = immutable_policy_event(root, session, acquired, "DESTRUCTIVE_WITHOUT_APPROVAL", command_id, "Destructive commands remain blocked in Phase 1B-2")
            return publish_result(root, pre_command_result("BLOCKED", "COMMAND_CLASSIFICATION_BLOCKED", 2)[0], 2)

        parameter_specification = command["parameters"]
        try:
            if not parameter_specification["allowed"]:
                if parameters_path is not None:
                    raise ValueError("PARAMETERS_NOT_ALLOWED")
                parameters = {}
            else:
                if parameters_path is None:
                    raise ValueError("PARAMETERS_REQUIRED")
                parameters = read_parameter_object(root, parameters_path)
                validate_parameter_values(parameter_specification["schema"], parameters)
            argv = resolved_argv(command, parameters)
        except ValueError as error:
            session = immutable_policy_event(root, session, acquired, "UNSAFE_PARAMETER", command_id, "Command parameters violated the closed registry policy")
            return publish_result(root, pre_command_result("POLICY_VIOLATION", str(error), 4)[0], 4)

        prerequisite_evidence(root, session, prerequisite_order[command_id])
        working_directory = normalized_relative_directory(root, command["workingDirectory"])
        argv_digest = argv_hash(argv)
        input_digest = input_fingerprint(root, command)
        environment_digest = environment_fingerprint(child_environment(os.environ if source_environment is None else source_environment))
        duplicate = next((item for item in reversed(session["reservations"]) if (
            item["commandId"] == command_id
            and item["argvHash"] == argv_digest
            and item["inputFingerprint"] == input_digest
            and item["environmentFingerprint"] == environment_digest
        )), None)
        reason_hash = None
        rerun_of = None
        if duplicate is not None:
            if duplicate["state"] == "RESERVED":
                return publish_result(root, pre_command_result("BLOCKED", "RESERVATION_PENDING", 2)[0], 2)
            if duplicate["state"] in ("FAIL", "BLOCKED"):
                return publish_result(root, pre_command_result("BLOCKED", "FAILURE_TRIAGE_NOT_CONFIGURED", 2)[0], 2)
            try:
                if rerun_reason_path is None:
                    raise ValueError("MISSING_RERUN_REASON")
                reason_hash = normalized_rerun_reason(root, rerun_reason_path)
            except (ValueError, InvalidStateError):
                session = immutable_policy_event(root, session, acquired, "MISSING_RERUN_REASON", command_id, "Duplicate PASS requires a bounded rerun reason")
                return publish_result(root, pre_command_result("POLICY_VIOLATION", "MISSING_RERUN_REASON", 4)[0], 4)
            rerun_of = duplicate["attemptId"]
        elif rerun_reason_path is not None:
            return publish_result(root, pre_command_result("POLICY_VIOLATION", "RERUN_REASON_NOT_APPLICABLE", 4)[0], 4)

        attempt_id = str(uuid.uuid4())
        reservation = {
            "attemptId": attempt_id,
            "commandId": command_id,
            "argvHash": argv_digest,
            "inputFingerprint": input_digest,
            "environmentFingerprint": environment_digest,
            "reservedAt": utc_now(),
            "state": "RESERVED",
            "commandResultRef": None,
            "processAttemptRef": None,
            "terminalAt": None,
            "rerunReasonHash": reason_hash,
            "rerunOfAttemptId": rerun_of,
        }
        if reserve:
            replacement = json.loads(json.dumps(session))
            replacement["reservations"].append(reservation)
            replace_run_session(root, root / replacement["$id"], replacement, acquired, expected_session=session)
        data = {
            "runId": run_id,
            "commandId": command_id,
            "attemptId": attempt_id,
            "argvHash": argv_digest,
            "inputFingerprint": input_digest,
            "environmentFingerprint": environment_digest,
            "workingDirectory": working_directory,
            "argv": argv,
        }
        return publish_result(root, pre_command_result("PASS", None, 0, data=data)[0], 0)
    except RegistryBlockedError as error:
        return publish_result(root, pre_command_result("BLOCKED", error.errors[0]["code"], 2, errors=error.errors)[0], 2)
    except InvalidStateError as error:
        return publish_result(root, pre_command_result("INVALID_STATE", error.errors[0]["code"], 5, errors=error.errors)[0], 5)
    except (OSError, ValueError) as error:
        return publish_result(root, pre_command_result("INVALID_STATE", "PRE_COMMAND_FAILED", 5)[0], 5)
    finally:
        if acquired is not None:
            release_run_lock(acquired)


def run_resolve(arguments):
    root = Path(arguments.repository_root).resolve()
    preflight_result, preflight_status = run_current_preflight(root)
    if preflight_status != 0:
        return preflight_result, preflight_status
    return resolve_command(
        root,
        root / "ai" / "project-state.json",
        arguments.registry,
        arguments.command_id,
        arguments.parameters_file,
    )


def run_start_cli(arguments):
    return start_run(arguments.repository_root, arguments.run_id, arguments.task_key)


def run_pre_command_cli(arguments):
    return pre_command(
        arguments.repository_root,
        arguments.run_id,
        arguments.command_id,
        parameters_path=arguments.parameters_file,
        rerun_reason_path=arguments.rerun_reason_file,
        approval_ref=arguments.approval_ref,
    )


def run_execute_command_cli(arguments):
    request = {"runId": arguments.run_id, "commandId": arguments.command_id}
    for argument_name, request_name in (
        ("parameters_file", "parametersPath"),
        ("rerun_reason_file", "rerunReasonPath"),
        ("approval_ref", "approvalRef"),
    ):
        value = getattr(arguments, argument_name)
        if value is not None:
            request[request_name] = value
    outcome = execute_command(Path(arguments.repository_root).resolve(), request)
    return outcome[0], outcome[1]


def run_post_command_cli(arguments):
    root = Path(arguments.repository_root).resolve()
    preflight, preflight_status = run_current_preflight(root)
    if preflight_status != 0:
        return publish_result(root, gateway_result(
            preflight["result"], preflight["reason"], operation="POST_COMMAND", errors=preflight["errors"],
        ), preflight_status)
    try:
        session = active_open_session(root, arguments.run_id)
        matches = [
            reservation for reservation in session["reservations"]
            if reservation["attemptId"] == arguments.attempt_id
        ]
        if len(matches) != 1:
            raise InvalidStateError([validation_error(
                "PROCESS_ATTEMPT_NOT_FOUND", message="POST_COMMAND requires one reserved process attempt",
            )])
        reservation = matches[0]
        _path, process_attempt = read_exact_run_json(
            root,
            arguments.run_id,
            ("process-attempts", reservation["commandId"], f"{arguments.attempt_id}.json"),
            "ai/schemas/process-attempt.schema.json",
        )
        if process_attempt is None:
            raise InvalidStateError([validation_error(
                "PROCESS_ATTEMPT_NOT_FOUND", message="POST_COMMAND process attempt is unavailable",
            )])
    except (InvalidStateError, OSError, TypeError, ValueError) as error:
        errors = error.errors if isinstance(error, InvalidStateError) else None
        return publish_result(root, gateway_result(
            "INVALID_STATE", errors[0]["code"] if errors else "POST_COMMAND_INVALID", None,
            operation="POST_COMMAND", errors=errors,
        ), 5)
    return post_command(root, process_attempt)


def run_done_claim_prepare_cli(arguments):
    return prepare_done_claim(arguments.repository_root, arguments.run_id, arguments.claim)


def run_verify_finalized_cli(arguments):
    return verify_finalized_run(arguments.repository_root, arguments.run_id)


def add_command_arguments(parser):
    parser.add_argument("--repository-root", required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--command-id", required=True)
    parser.add_argument("--parameters-file")
    parser.add_argument("--rerun-reason-file")
    parser.add_argument("--approval-ref")


def invalid_cli_result(operation):
    profiles = {
        "run-start": ("RUN_START", "INVALID_RUN_START_ARGUMENTS"),
        "pre-command": ("PRE_COMMAND", "INVALID_PRE_COMMAND_ARGUMENTS"),
        "execute-command": ("PRE_COMMAND", "INVALID_EXECUTE_COMMAND_ARGUMENTS"),
        "post-command": ("POST_COMMAND", "INVALID_POST_COMMAND_ARGUMENTS"),
        "done-claim-prepare": ("PRE_DONE_CLAIM", "INVALID_DONE_CLAIM_ARGUMENTS"),
        "verify-finalized": ("PRE_DONE_CLAIM", "INVALID_VERIFY_FINALIZED_ARGUMENTS"),
        "verification-gate": ("VERIFICATION_GATE", "INVALID_VERIFICATION_GATE_ARGUMENTS"),
        "native-adapter-gate": ("NATIVE_ADAPTER_GATE", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS"),
    }
    gateway_operation, reason = profiles[operation]
    if operation == "verification-gate":
        return verification_gate_result("POLICY_VIOLATION", reason, None), 4
    if operation == "native-adapter-gate":
        return native_adapter_gate_result("BLOCKED", reason, native_adapter_fallback_data()), 2
    return gateway_result("POLICY_VIOLATION", reason, operation=gateway_operation), 4


def repo_intake_result(result, reason=None, data=None, errors=None):
    return {
        "$schema": "ai/schemas/repo-intake-result.schema.json",
        "$id": "ai/repo-intake-result.json",
        "schemaVersion": 1,
        "operation": "REPO_INTAKE",
        "result": result,
        "reason": reason,
        "errors": [] if errors is None and result == "PASS" else (errors or [{
            "code": reason or "REPO_INTAKE_FAILED",
            "instancePath": "",
            "schemaPath": "",
            "message": reason or "repo intake failed",
        }]),
        "data": data,
    }


def context_map_paths(context):
    for route_index, route in enumerate(context.get("routes", [])):
        for path_index, path in enumerate(route.get("requiredDocuments", [])):
            yield ("routes", route_index, "requiredDocuments", path_index), path
    for surface_index, surface in enumerate(context.get("surfaces", [])):
        for path_index, path in enumerate(surface.get("paths", [])):
            yield ("surfaces", surface_index, "paths", path_index), path
    for name in ("generatedPaths", "excludedPaths"):
        for index, path in enumerate(context.get(name, [])):
            yield (name, index), path


def validate_context_map_paths(root, context):
    repository_root = Path(root).resolve(strict=True)
    for pointer, relative in context_map_paths(context):
        try:
            candidate = Path(relative)
            if candidate.is_absolute() or any(part in ("", ".", "..") for part in candidate.parts):
                raise ValueError("invalid repository path")
            resolved = (repository_root / candidate).resolve(strict=False)
            resolved.relative_to(repository_root)
        except (OSError, ValueError) as error:
            raise InvalidStateError([validation_error(
                "CONTEXT_MAP_PATH_INVALID",
                instance_path=json_pointer(pointer),
                message="context-map path must remain repository relative",
            )]) from error


def project_state_refresh_proposals(project_state):
    proposals = []
    inputs = project_state.get("cacheInvalidationInputs", [])
    if inputs:
        proposals.append({
            "section": "cacheInvalidationInputs",
            "status": "CURRENT",
            "reason": "Phase 2A repo intake inspected configured invalidation inputs without rewriting project state.",
            "inputPaths": inputs,
        })
    for fact in project_state.get("facts", []):
        proposals.append({
            "section": f"facts.{fact['id']}",
            "status": "CURRENT",
            "reason": "Static fact remains proposal-only in Phase 2A; no runtime refresh was performed.",
            "inputPaths": [item["path"] for item in fact.get("evidence", [])],
        })
    return proposals


def command_discovery_update_proposals(registry):
    proposals = []
    for command in registry.get("commands", []):
        status = command["configurationStatus"]
        proposed = status if status in ("UNKNOWN", "CONFIGURED_UNVERIFIED", "NOT_CONFIGURED", "STALE", "UNCERTAIN") else "CONFIGURED_UNVERIFIED"
        proposals.append({
            "commandId": command["id"],
            "status": "CURRENT",
            "proposedStatus": proposed,
            "reason": "Phase 2A records command-discovery state as proposal-only and does not execute commands or mark VERIFIED.",
        })
    return proposals


REQUIRED_SKILL_IDS = {
    "repo-intake",
    "command-runner",
    "verification-runner",
    "api-smoke-verifier",
    "failure-triage",
    "docs-sync",
    "review-gate",
}


def cache_entry_identity(entry):
    key = entry["key"]
    if entry["kind"] == "VERIFICATION_DECISION":
        return (
            key["taskKey"],
            key["gateInvocationId"],
            key["commitSha"],
            key["changeType"],
            key["entryPoint"],
            key["policySha256"],
            tuple(sorted(key["producerIds"])),
            tuple(sorted((item["path"], item["sha256"]) for item in key["evidence"])),
            key["environmentFingerprint"],
            key["expiresAt"],
        )
    return (
        tuple(sorted((item["path"], item["sha256"]) for item in key["paths"])),
        key["environmentFingerprint"],
    )


def validate_skill_catalog_semantics(catalog):
    ids = [skill["id"] for skill in catalog["skills"]]
    if len(ids) != len(set(ids)) or set(ids) != REQUIRED_SKILL_IDS:
        raise InvalidStateError([validation_error(
            "SKILL_CATALOG_ID_SET_INVALID",
            message="skill catalog must contain every required skill ID exactly once",
        )])


def validate_handoff_skill_set(handoff, catalog):
    expected = {skill["id"] for skill in catalog["skills"]}
    actual = handoff["skillIds"]
    if len(actual) != len(set(actual)) or set(actual) != expected:
        raise InvalidStateError([validation_error(
            "HANDOFF_REQUIRED_SKILL_MISSING",
            message="handoff must contain every catalog skill ID exactly once",
        )])


def verification_cache_producers(policy, change_type, entry_point):
    changes = {item["id"]: item for item in policy.get("changeTypes", [])}
    checks = {item["id"]: item for item in policy.get("checks", [])}
    change = changes.get(change_type)
    if change is None or entry_point not in change.get("entryPoints", []):
        return None
    selected_ids = change.get("requiredChecks", []) + change.get("optionalChecks", [])
    selected = []
    for check_id in selected_ids:
        check = checks.get(check_id)
        if check is None:
            return None
        if check.get("entryPoint") == entry_point:
            selected.append(check["producerId"])
    return selected or None


def load_verification_cache_policy(root):
    policy_path = resolve_repository_file(root, "ai/verification-policy.json")
    encoded, policy = read_bounded_verification_json(
        policy_path,
        MAX_PARAMETER_FILE_BYTES,
        "VERIFICATION_CACHE_POLICY_TOO_LARGE",
        "verification cache policy exceeds the bounded read limit",
    )
    validate(root, policy, "ai/schemas/verification-policy.schema.json")
    return policy, hashlib.sha256(encoded).hexdigest()


def verification_cache_invalidation(root, entry, policy, policy_sha256, commit_sha):
    key = entry.get("key", {})
    stale_reasons = []
    uncertain_reasons = []
    if not all(
        isinstance(key.get(field), str)
        and NATIVE_ADAPTER_IDENTIFIER.fullmatch(key[field])
        for field in ("taskKey", "gateInvocationId")
    ):
        uncertain_reasons.append("Cache task or gate correlation is missing or unmapped.")

    expected_producers = (
        verification_cache_producers(policy, key.get("changeType"), key.get("entryPoint"))
        if policy is not None
        else None
    )
    if policy is None:
        uncertain_reasons.append("Current verification cache policy is unavailable.")
    elif expected_producers is None:
        uncertain_reasons.append("Cache change type or entry point is missing or unmapped.")
    else:
        producer_ids = key.get("producerIds", [])
        try:
            producer_mismatch = (
                len(producer_ids) != len(set(producer_ids))
                or set(producer_ids) != set(expected_producers)
            )
        except TypeError:
            producer_mismatch = True
        if producer_mismatch:
            stale_reasons.append("Cache producer set changed.")
    if key.get("environmentFingerprint") is not None:
        uncertain_reasons.append("Cache environment fingerprint has no authoritative current mapping.")
    if commit_sha is None:
        uncertain_reasons.append("Current repository commit is unavailable.")
    elif key.get("commitSha") != commit_sha:
        stale_reasons.append("Cache commit changed.")
    if policy_sha256 is None:
        if policy is not None:
            uncertain_reasons.append("Current verification policy digest is unavailable.")
    elif key.get("policySha256") != policy_sha256:
        stale_reasons.append("Cache verification policy digest changed.")

    repository_root = Path(root).resolve(strict=True)
    evidence = key.get("evidence", [])
    if not isinstance(evidence, list) or not evidence:
        uncertain_reasons.append("Cache evidence mapping is missing.")
        evidence = []
    for item in evidence:
        try:
            relative = item["path"]
            if (
                not isinstance(relative, str)
                or not VERIFICATION_REPOSITORY_PATH.fullmatch(relative)
            ):
                raise ValueError("cache evidence path is unsafe")
            path = (repository_root / relative).resolve(strict=True)
            path.relative_to(repository_root)
            if not path.is_file():
                raise OSError("cache evidence is not a regular file")
            evidence_sha256 = digest(path)
        except (KeyError, OSError, TypeError, ValueError):
            uncertain_reasons.append("Cache evidence path is missing, unmapped, or unavailable.")
            continue
        if evidence_sha256 != item.get("sha256"):
            stale_reasons.append("Cache evidence digest changed.")

    try:
        expires_at = parse_rfc3339_timestamp(key["expiresAt"])[0]
    except (KeyError, TypeError, ValueError):
        uncertain_reasons.append("Cache expiry is missing or unmapped.")
    else:
        if dt.datetime.now(dt.timezone.utc) > expires_at:
            stale_reasons.append("Cache decision expired.")

    if stale_reasons:
        return "STALE", " ".join(stale_reasons + uncertain_reasons)
    if uncertain_reasons:
        return "UNCERTAIN", " ".join(uncertain_reasons)
    return "FRESH", "All verification cache identity inputs match."


def cache_invalidation_report(root, workflow_cache):
    repository_root = Path(root).resolve(strict=True)
    report = []
    verification_entries = [
        entry for entry in workflow_cache.get("entries", [])
        if entry.get("kind") == "VERIFICATION_DECISION"
    ]
    policy = None
    policy_sha256 = None
    commit_sha = None
    if verification_entries:
        try:
            policy, policy_sha256 = load_verification_cache_policy(root)
        except (InvalidStateError, OSError, TypeError, ValueError):
            pass
        try:
            commit_sha = repository_commit_sha(root)
        except (InvalidStateError, VerificationNotConfiguredError, OSError, TypeError, ValueError):
            pass
    for entry in workflow_cache.get("entries", []):
        if entry.get("kind") == "VERIFICATION_DECISION":
            entry_status, reason = verification_cache_invalidation(
                root, entry, policy, policy_sha256, commit_sha,
            )
            report.append({
                "entryId": entry["id"],
                "status": entry_status,
                "reason": reason,
            })
            continue
        entry_status = "FRESH"
        reason = "All cache key paths match recorded digests."
        for item in entry.get("key", {}).get("paths", []):
            try:
                path = (repository_root / item["path"]).resolve(strict=True)
                path.relative_to(repository_root)
                if not path.is_file():
                    raise OSError("cache key path is not a regular file")
            except (OSError, ValueError):
                entry_status = "UNCERTAIN"
                reason = "Cache key path is missing, unmapped, or unavailable."
                break
            if digest(path) != item["sha256"]:
                entry_status = "STALE"
                reason = "Cache key path digest changed."
                break
        report.append({
            "entryId": entry["id"],
            "status": entry_status,
            "reason": reason,
        })
    return report


def publish_repo_intake_result(root, result, status):
    try:
        validate(root, result, "ai/schemas/repo-intake-result.schema.json")
    except InvalidStateError:
        fallback = repo_intake_result("INVALID_STATE", "REPO_INTAKE_RESULT_INVALID", None)
        validate(root, fallback, "ai/schemas/repo-intake-result.schema.json")
        return fallback, 5
    return result, status


def repo_intake(root):
    root = Path(root).resolve()
    try:
        context = validate_repository_instance(root, root / "ai" / "context-map.json")
        workflow_cache = validate_repository_instance(root, root / "ai" / "workflow-cache.json")
        project_state = validate_repository_instance(root, root / "ai" / "project-state.json")
        registry = validate_repository_instance(root, root / "ai" / "command-registry.json")
        skill_catalog = validate_repository_instance(root, root / "ai" / "skill-catalog.json")
        validate_skill_catalog_semantics(skill_catalog)
        handoff = validate_repository_instance(root, root / "ai" / "agent-handoff.json")
        validate_handoff_skill_set(handoff, skill_catalog)
        validate_context_map_paths(root, context)
        data = {
            "contextMapRef": "ai/context-map.json",
            "workflowCacheRef": "ai/workflow-cache.json",
            "projectStateRefresh": project_state_refresh_proposals(project_state),
            "commandDiscoveryUpdates": command_discovery_update_proposals(registry),
            "cacheInvalidation": cache_invalidation_report(root, workflow_cache),
            "createdAiRuns": False,
        }
        return publish_repo_intake_result(root, repo_intake_result("PASS", None, data), 0)
    except InvalidStateError as error:
        return publish_repo_intake_result(root, repo_intake_result(
            "INVALID_STATE", error.errors[0]["code"], None, errors=error.errors,
        ), 5)
    except (OSError, ValueError, TypeError):
        return publish_repo_intake_result(root, repo_intake_result(
            "INVALID_STATE", "REPO_INTAKE_FAILED", None,
        ), 5)


def run_repo_intake_cli(arguments):
    root = Path(arguments.repository_root).resolve()
    result, status = repo_intake(root)
    output_status = write_resolve_output(root, arguments.output, result)
    if output_status != 0:
        return publish_repo_intake_result(root, repo_intake_result(
            "POLICY_VIOLATION", "REPO_INTAKE_OUTPUT_PATH_INVALID", None,
        ), 4)
    return result, status


def verification_gate_result(result, reason=None, data=None, errors=None):
    return {
        "$schema": "ai/schemas/verification-gate-result.schema.json",
        "$id": "ai/verification-gate-result.json",
        "schemaVersion": 1,
        "operation": "VERIFICATION_GATE",
        "result": result,
        "reason": reason,
        "errors": [] if errors is None and result == "PASS" else (errors or ([{
            "code": reason or "VERIFICATION_GATE_FAILED",
            "instancePath": "",
            "schemaPath": "",
            "message": reason or "verification gate failed",
        }] if result != "PASS" else [])),
        "data": data,
    }


def verification_gate_exit(result):
    return {
        "PASS": 0,
        "FAIL": 1,
        "BLOCKED": 2,
        "NOT_CONFIGURED": 3,
        "POLICY_VIOLATION": 4,
        "INVALID_STATE": 5,
        "NOT_APPLICABLE": 6,
        "SKIPPED_WITH_REASON": 7,
    }[result]


def publish_verification_gate_result(root, result, status):
    try:
        validate(root, result, "ai/schemas/verification-gate-result.schema.json")
    except InvalidStateError:
        fallback = verification_gate_result("INVALID_STATE", "VERIFICATION_GATE_RESULT_INVALID", None)
        validate(root, fallback, "ai/schemas/verification-gate-result.schema.json")
        return fallback, 5
    return result, status


NATIVE_ADAPTER_CHECK_ID = "native-runtime-adapter"
VERIFICATION_LEAF_MAX_AGE = dt.timedelta(minutes=5)
MAX_VERIFICATION_LEAF_EVIDENCE_BYTES = MAX_PARAMETER_FILE_BYTES
VERIFICATION_REPOSITORY_PATH = re.compile(
    r"(?!/)(?![A-Za-z][A-Za-z0-9+.-]*:)(?![\s\S]*\\)(?![\s\S]*(?:^|/)\.\.(?:/|$)).+\Z"
)


def repository_commit_sha(root):
    try:
        completed = subprocess.run(
            ["git", "-C", str(Path(root).resolve()), "rev-parse", "HEAD"],
            shell=False,
            check=True,
            text=True,
            capture_output=True,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise VerificationNotConfiguredError([validation_error(
            "VERIFICATION_REPOSITORY_COMMIT_NOT_CONFIGURED",
            message="the checked-out repository commit is unavailable",
        )]) from error
    matched = (
        re.fullmatch(r"([a-f0-9]{40})(?:\r?\n)?", completed.stdout)
        if isinstance(completed.stdout, str)
        else None
    )
    if matched is None:
        raise VerificationNotConfiguredError([validation_error(
            "VERIFICATION_REPOSITORY_COMMIT_NOT_CONFIGURED",
            message="the checked-out repository commit is malformed",
        )])
    return matched.group(1)


def read_bounded_verification_json(path, max_bytes, too_large_code, too_large_message):
    with path.open("rb") as handle:
        encoded = handle.read(max_bytes + 1)
    if len(encoded) > max_bytes:
        raise InvalidStateError([validation_error(
            too_large_code,
            message=too_large_message,
        )])
    try:
        value = json.loads(
            encoded.decode("utf-8", errors="strict"),
            object_pairs_hook=reject_duplicate_keys,
            parse_constant=reject_non_finite_number,
        )
    except DuplicateJsonKey as error:
        raise InvalidStateError([validation_error(
            "DUPLICATE_JSON_KEY",
            message="duplicate JSON object key is forbidden",
        )]) from error
    except NonFiniteJsonNumber as error:
        raise InvalidStateError([validation_error(
            "NON_FINITE_JSON_NUMBER",
            message=f"non-finite JSON number is forbidden: {error}",
        )]) from error
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise InvalidStateError([validation_error(
            "MALFORMED_JSON", message="input is not valid UTF-8 JSON",
        )]) from error
    return encoded, value


def read_verification_leaf_evidence(path):
    return read_bounded_verification_json(
        path,
        MAX_VERIFICATION_LEAF_EVIDENCE_BYTES,
        "VERIFICATION_LEAF_EVIDENCE_TOO_LARGE",
        "verification leaf evidence exceeds the bounded read limit",
    )


def read_verification_leaf_result(path):
    return read_bounded_verification_json(
        path,
        MAX_VERIFICATION_LEAF_EVIDENCE_BYTES,
        "VERIFICATION_LEAF_RESULT_TOO_LARGE",
        "verification leaf result exceeds the bounded read limit",
    )


def verification_leaf_references(root, refs_file):
    try:
        payload = read_json(resolve_repository_file(root, refs_file))
        if not isinstance(payload, dict):
            raise ValueError("leaf result references must be an object")

        legacy_results = payload.get("results")
        if isinstance(legacy_results, list) and any(
            isinstance(item, dict) and item.get("checkId") == NATIVE_ADAPTER_CHECK_ID
            for item in legacy_results
        ):
            raise InvalidStateError([validation_error(
                "NATIVE_ADAPTER_LEAF_FORGED",
                message="native runtime adapter leaf results are internal-only",
            )])
        if set(payload) != {"leafResultRefs"}:
            raise ValueError("leaf result references have an invalid shape")

        references = payload["leafResultRefs"]
        if not isinstance(references, list) or len(references) != len(set(
            item for item in references if isinstance(item, str)
        )):
            raise ValueError("leaf result references must be a unique array")
        for reference in references:
            if (
                not isinstance(reference, str)
                or VERIFICATION_REPOSITORY_PATH.fullmatch(reference) is None
                or any(part in ("", ".", "..") for part in reference.split("/"))
            ):
                raise ValueError("invalid leaf result reference")

        loaded_leaves = []
        for reference in references:
            encoded, leaf = read_verification_leaf_result(
                resolve_repository_file(root, reference),
            )
            loaded_leaves.append({
                "reference": Path(reference).as_posix(),
                "encoded": encoded,
                "leaf": leaf,
            })
        if any(
            isinstance(item["leaf"], dict)
            and item["leaf"].get("checkId") == NATIVE_ADAPTER_CHECK_ID
            for item in loaded_leaves
        ):
            raise InvalidStateError([validation_error(
                "NATIVE_ADAPTER_LEAF_FORGED",
                message="native runtime adapter leaf results are internal-only",
            )])
        return loaded_leaves
    except InvalidStateError:
        raise
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        raise InvalidStateError([validation_error(
            "VERIFICATION_LEAF_RESULTS_INVALID",
            message="verification leaf results are invalid",
        )]) from error


def verified_leaf_result(root, loaded_leaf, expected, policy_sha256):
    reference = loaded_leaf["reference"]
    encoded = loaded_leaf["encoded"]
    leaf = loaded_leaf["leaf"]
    validate(root, leaf, "ai/schemas/verification-leaf-result.schema.json")
    if leaf["checkId"] == NATIVE_ADAPTER_CHECK_ID:
        raise InvalidStateError([validation_error(
            "NATIVE_ADAPTER_LEAF_FORGED",
            message="native runtime adapter leaf results are internal-only",
        )])
    if leaf["$id"] != Path(reference).as_posix():
        raise InvalidStateError([validation_error(
            "VERIFICATION_LEAF_ID_MISMATCH",
            message="verification leaf ID does not match its repository reference",
        )])
    if leaf["checkId"] != expected["checkId"]:
        raise InvalidStateError([validation_error(
            "VERIFICATION_LEAF_CORRELATION_MISMATCH",
            message="verification leaf check identity does not match canonical policy",
        )])
    for field in ("taskKey", "gateInvocationId", "commitSha"):
        if leaf[field] != expected[field]:
            raise InvalidStateError([validation_error(
                "VERIFICATION_LEAF_CORRELATION_MISMATCH",
                message="verification leaf correlation does not match the current gate",
            )])
    if leaf["policySha256"] != policy_sha256:
        raise InvalidStateError([validation_error(
            "VERIFICATION_LEAF_POLICY_MISMATCH",
            message="verification leaf policy digest does not match canonical policy",
        )])
    if leaf["producerId"] != expected["producerId"]:
        raise InvalidStateError([validation_error(
            "VERIFICATION_LEAF_PRODUCER_MISMATCH",
            message="verification leaf producer does not match canonical policy",
        )])

    produced = parse_rfc3339_timestamp(leaf["producedAt"])[0]
    expires = parse_rfc3339_timestamp(leaf["expiresAt"])[0]
    now = dt.datetime.now(dt.timezone.utc)
    if not produced <= now <= expires or expires - produced > VERIFICATION_LEAF_MAX_AGE:
        raise InvalidStateError([validation_error(
            "VERIFICATION_LEAF_STALE",
            message="verification leaf is outside its bounded freshness window",
        )])

    evidence = leaf["evidence"]
    if evidence is not None:
        if evidence["schema"] != expected["evidenceSchema"]:
            raise InvalidStateError([validation_error(
                "VERIFICATION_LEAF_EVIDENCE_SCHEMA_MISMATCH",
                message="verification leaf evidence schema does not match canonical policy",
            )])
        evidence_path = resolve_repository_file(root, evidence["ref"])
        evidence_bytes, evidence_value = read_verification_leaf_evidence(evidence_path)
        evidence_sha256 = hashlib.sha256(evidence_bytes).hexdigest()
        validate(root, evidence_value, evidence["schema"])
        if evidence_sha256 != evidence["sha256"]:
            raise InvalidStateError([validation_error(
                "VERIFICATION_LEAF_DIGEST_MISMATCH",
                message="verification leaf evidence digest does not match",
            )])
    verified = dict(leaf)
    verified["leafResultRef"] = reference
    verified["leafResultSha256"] = hashlib.sha256(encoded).hexdigest()
    return verified


def load_verified_leaf_results(root, loaded_leaves, task_key, gate_invocation_id, commit_sha, policy):
    policy_checks = {check["id"]: check for check in policy["checks"]}
    policy_sha256 = digest(resolve_repository_file(root, "ai/verification-policy.json"))
    by_id = {}
    for loaded_leaf in loaded_leaves:
        leaf = loaded_leaf["leaf"]
        check_id = leaf.get("checkId") if isinstance(leaf, dict) else None
        policy_check = policy_checks.get(check_id)
        if policy_check is None or check_id in by_id:
            raise InvalidStateError([validation_error(
                "VERIFICATION_LEAF_RESULTS_INVALID",
                message="verification leaf check identity is unknown or duplicated",
            )])
        expected = {
            "checkId": check_id,
            "taskKey": task_key,
            "gateInvocationId": gate_invocation_id,
            "commitSha": commit_sha,
            "producerId": policy_check["producerId"],
            "evidenceSchema": policy_check["evidenceSchema"],
        }
        by_id[check_id] = verified_leaf_result(
            root, loaded_leaf, expected, policy_sha256,
        )
    return by_id


def default_leaf_result_for_check(check_id, _policy_check):
    return {
        "checkId": check_id,
        "result": "NOT_CONFIGURED",
        "evidenceRef": None,
        "reason": "No verified leaf evidence was provided for this check.",
    }


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
    mapped_results = [item["mappedResult"] for item in mapped_checks]
    if "FAIL" in mapped_results:
        return "FAIL"
    if "BLOCKED" in mapped_results or "NOT_CONFIGURED" in mapped_results:
        return "BLOCKED"
    return "PASS"


def verification_check_result(check_id, required, raw, mapped_result):
    evidence = raw.get("evidence")
    evidence_ref = raw.get("evidenceRef")
    if evidence_ref is None and isinstance(evidence, dict):
        evidence_ref = evidence.get("ref")
    return {
        "checkId": check_id,
        "required": required,
        "rawResult": raw["result"],
        "mappedResult": mapped_result,
        "reason": raw.get("reason"),
        "evidenceRef": evidence_ref,
        "leafResultRef": raw.get("leafResultRef"),
        "leafResultSha256": raw.get("leafResultSha256"),
        "producerId": raw.get("producerId"),
        "commitSha": raw.get("commitSha"),
        "policySha256": raw.get("policySha256"),
    }


NATIVE_ADAPTER_SURFACES = ("COMMAND", "FILE_READ", "SEARCH", "TOOL_CALL")
NATIVE_SUMMARY_MAX_BYTES = 512
NATIVE_SNAPSHOT_MAX_AGE_SECONDS = 300
NATIVE_JSON_SAFE_INTEGER = 9007199254740991
NATIVE_CONSUMED_CHALLENGES = set()
NATIVE_ADAPTER_IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
NATIVE_KEY_FINGERPRINT = re.compile(r"[a-f0-9]{64}\Z")
NATIVE_SEMVER = re.compile(
    r"(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)"
    r"(?:-(?:(?:0|[1-9][0-9]*)|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*)"
    r"(?:\.(?:(?:0|[1-9][0-9]*)|[0-9A-Za-z-]*[A-Za-z-][0-9A-Za-z-]*))*)?"
    r"(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?\Z"
)
NATIVE_SECRET_BEARING_SUMMARY = re.compile(
    r"(?:\bauthorization\s*:\s*(?:bearer|basic)\s+\S+|\bcookies?\s*(?:=|:)|"
    r"\b(?:password|passwd|secret|token|api[-_]?key|credential)\s*(?:=|:)\s*\S+|"
    r"(?<![A-Za-z0-9_-])eyJ[A-Za-z0-9_-]*\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+(?![A-Za-z0-9_-])|"
    r"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----|"
    r"\b(?:request\s+body|raw\s+(?:auth(?:orization)?|cookies?|bod(?:y|ies)|credentials?|payload|query|argv|env(?:ironment)?)))",
    re.IGNORECASE,
)
NATIVE_BASIC_CREDENTIAL = re.compile(r"\bbasic\s+\S+", re.IGNORECASE)
NATIVE_BEARER_CREDENTIAL = re.compile(r"\bbearer\s+\S+", re.IGNORECASE)
NATIVE_FORBIDDEN_RAW_CONTENT_LABEL = re.compile(r"\b(?:authorization|cookies?)\b", re.IGNORECASE)
NATIVE_ALLOWED_BEARER_DOCUMENTATION = frozenset(("bearer token documentation",))
NATIVE_RFC3339_TIMESTAMP = re.compile(
    r"[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9](?:\.[0-9]+)?Z\Z"
)


def native_deep_freeze(value):
    if isinstance(value, Mapping):
        return MappingProxyType({
            key: native_deep_freeze(item)
            for key, item in value.items()
        })
    if isinstance(value, (list, tuple)):
        return tuple(native_deep_freeze(item) for item in value)
    return value


@dataclass(frozen=True)
class HostNativeTrust:
    descriptor: Mapping
    probe: Mapping
    ledger_root: Path

    def __post_init__(self):
        object.__setattr__(self, "descriptor", native_deep_freeze(self.descriptor))
        object.__setattr__(self, "probe", native_deep_freeze(self.probe))


class NativeBypassContractError(ValueError):
    pass


class NativeBypassReferenceError(ValueError):
    pass


class NativeReplayError(ValueError):
    pass


def native_summary_has_secret(value):
    if (
        NATIVE_SECRET_BEARING_SUMMARY.search(value)
        or NATIVE_BASIC_CREDENTIAL.search(value)
        or NATIVE_FORBIDDEN_RAW_CONTENT_LABEL.search(value)
    ):
        return True
    if (
        NATIVE_BEARER_CREDENTIAL.search(value)
        and value.casefold() not in NATIVE_ALLOWED_BEARER_DOCUMENTATION
    ):
        return True
    return False


def native_bypass_attempt_has_secret(value):
    if isinstance(value, str):
        return native_summary_has_secret(value)
    if isinstance(value, dict):
        return any(native_bypass_attempt_has_secret(item) for item in value.values())
    if isinstance(value, list):
        return any(native_bypass_attempt_has_secret(item) for item in value)
    return False


def native_summary_string_values(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from native_summary_string_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from native_summary_string_values(item)


def native_adapter_gate_result(result, reason, data):
    phase2c_leaf_result = {
        "PASS": "PASS",
        "FAIL": "FAIL",
        "BLOCKED": "BLOCKED",
        "NOT_CONFIGURED": "NOT_CONFIGURED",
        "UNSUPPORTED": "NOT_APPLICABLE",
    }[result]
    data = dict(data)
    data["phase2CLeafResult"] = phase2c_leaf_result
    return {
        "$schema": "ai/schemas/native-adapter-result.schema.json",
        "$id": "ai/native-adapter-result.json",
        "schemaVersion": 1,
        "operation": "NATIVE_ADAPTER_GATE",
        "result": result,
        "phase2cLeafResult": phase2c_leaf_result,
        "reason": reason,
        "data": data,
    }


def native_adapter_data(host, claimed_surfaces, trusted_surfaces, bypass_attempt_refs,
                        repository_only_qualification):
    return {
        "hostId": host["hostId"],
        "hostVersion": host["hostVersion"],
        "versionProvenance": host["versionProvenance"],
        "claimedSurfaces": claimed_surfaces,
        "trustedSurfaces": trusted_surfaces,
        "bypassAttemptRefs": bypass_attempt_refs,
        "repositoryOnlyQualification": repository_only_qualification,
    }


def native_adapter_fallback_data():
    return native_adapter_data(
        {"hostId": "unknown-host", "hostVersion": None, "versionProvenance": "UNPROBED"},
        [
            {"surface": surface, "status": "NOT_CONFIGURED", "reasonCode": "NATIVE_ADAPTER_EVALUATION_FAILED"}
            for surface in NATIVE_ADAPTER_SURFACES
        ],
        [
            {"surface": surface, "status": "NOT_CONFIGURED", "reasonCode": "NATIVE_ADAPTER_EVALUATION_FAILED"}
            for surface in NATIVE_ADAPTER_SURFACES
        ],
        [],
        True,
    )


def publish_native_adapter_gate_result(root, result, status):
    try:
        validate(root, result, "ai/schemas/native-adapter-result.schema.json")
    except InvalidStateError:
        fallback = native_adapter_gate_result(
            "BLOCKED", "NATIVE_ADAPTER_RESULT_INVALID", native_adapter_fallback_data(),
        )
        try:
            validate(root, fallback, "ai/schemas/native-adapter-result.schema.json")
        except InvalidStateError:
            pass
        return fallback, 2
    return result, status


def native_adapter_fixture_path(root, reference, *, canonical=False):
    if not isinstance(reference, str) or not reference:
        raise ValueError("native adapter fixture reference is required")
    path = Path(reference)
    if path.is_absolute() or any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("native adapter fixture reference is invalid")
    normalized = path.as_posix()
    if canonical:
        if normalized != "ai/native-runtime-adapters.json" and not normalized.startswith("ai/fixtures/"):
            raise ValueError("native adapter policy must be canonical or a temporary fixture")
    elif not normalized.startswith("ai/fixtures/"):
        raise ValueError("native adapter input must be a temporary fixture")
    return resolve_repository_file(root, normalized)


def native_semantic_error(code, instance_path, message):
    raise InvalidStateError([
        validation_error(code, instance_path=instance_path, message=message)
    ])


def validate_native_runtime_adapters_semantics(policy):
    if policy.get("supportedHosts") != []:
        native_semantic_error(
            "REPOSITORY_NATIVE_TRUST_FORBIDDEN",
            "/supportedHosts",
            "repository policy cannot declare a supported host",
        )
    surfaces = policy.get("currentHost", {}).get("surfaces")
    if (
        not isinstance(surfaces, list)
        or len(surfaces) != len(NATIVE_ADAPTER_SURFACES)
        or {surface.get("surface") for surface in surfaces if isinstance(surface, dict)}
        != set(NATIVE_ADAPTER_SURFACES)
        or any(
            not isinstance(surface, dict) or surface.get("status") != "UNSUPPORTED"
            for surface in surfaces
        )
    ):
        native_semantic_error(
            "REPOSITORY_NATIVE_SURFACE_BASELINE_INVALID",
            "/currentHost/surfaces",
            "repository policy must retain exactly four unsupported host surfaces",
        )


def native_adapter_version_range_bounds(version_range):
    match = re.fullmatch(r">=(\S+) <(\S+)", version_range) if isinstance(version_range, str) else None
    if match is None:
        raise ValueError("native adapter version range is invalid")
    minimum, maximum = (native_semver_key(item) for item in match.groups())
    if minimum >= maximum:
        raise ValueError("native adapter version range must be increasing")
    return minimum, maximum


def validate_host_native_trust_descriptor(descriptor):
    required = {
        "$schema",
        "schemaVersion",
        "producerId",
        "hostId",
        "minimumHostVersion",
        "adapterVersionRange",
        "ed25519PublicKeyFingerprint",
        "surfaces",
    }
    try:
        valid = (
            isinstance(descriptor, dict)
            and set(descriptor) == required
            and descriptor["$schema"] == "ai/schemas/host-native-trust.schema.json"
            and descriptor["schemaVersion"] == 1
            and all(
                isinstance(descriptor[field], str)
                and NATIVE_ADAPTER_IDENTIFIER.fullmatch(descriptor[field])
                for field in ("producerId", "hostId")
            )
            and NATIVE_KEY_FINGERPRINT.fullmatch(descriptor["ed25519PublicKeyFingerprint"])
            and isinstance(descriptor["surfaces"], list)
            and len(descriptor["surfaces"]) == len(NATIVE_ADAPTER_SURFACES)
            and set(descriptor["surfaces"]) == set(NATIVE_ADAPTER_SURFACES)
        )
        native_semver_key(descriptor["minimumHostVersion"])
        native_adapter_version_range_bounds(descriptor["adapterVersionRange"])
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        native_semantic_error(
            "HOST_NATIVE_TRUST_DESCRIPTOR_INVALID",
            "",
            "host-native trust descriptor violates the compiled trust contract",
        )


def validate_host_native_trust_probe(probe):
    required = {"hostId", "hostVersion", "versionProvenance", "producerId", "observedAt"}
    try:
        valid = (
            isinstance(probe, dict)
            and set(probe) == required
            and all(
                isinstance(probe[field], str)
                and NATIVE_ADAPTER_IDENTIFIER.fullmatch(probe[field])
                for field in ("hostId", "producerId")
            )
            and probe["versionProvenance"] == "PROBED"
            and isinstance(probe["observedAt"], str)
            and NATIVE_RFC3339_TIMESTAMP.fullmatch(probe["observedAt"])
        )
        native_semver_key(probe["hostVersion"])
        parse_rfc3339_timestamp(probe["observedAt"])
    except (KeyError, TypeError, ValueError):
        valid = False
    if not valid:
        native_semantic_error(
            "HOST_NATIVE_TRUST_PROBE_INVALID",
            "",
            "authoritative host probe violates the compiled trust contract",
        )


def resolve_external_host_trust_path(repository_root, path, *, directory):
    repository_root = Path(repository_root).resolve(strict=True)
    candidate = Path(os.path.abspath(os.fspath(path)))
    try:
        if any(item.is_symlink() for item in (candidate, *candidate.parents)):
            raise ValueError("host trust paths cannot contain symlinks")
        resolved = candidate.resolve(strict=True)
        try:
            resolved.relative_to(repository_root)
        except ValueError:
            pass
        else:
            raise ValueError("host trust paths must be outside the repository")
        if directory and not resolved.is_dir():
            raise ValueError("host trust ledger root must be a directory")
        if not directory and not resolved.is_file():
            raise ValueError("host trust document must be a regular file")
        return resolved
    except OSError as error:
        raise ValueError("host trust path is unavailable") from error


def native_safe_ledger_backend_supported():
    return (
        os.name == "posix"
        and hasattr(os, "O_DIRECTORY")
        and hasattr(os, "O_NOFOLLOW")
        and hasattr(os, "geteuid")
        and os.open in os.supports_dir_fd
        and os.unlink in os.supports_dir_fd
    )


def secure_host_ledger_directory(ledger_root, filename):
    if not isinstance(filename, str) or re.fullmatch(r"[a-f0-9]{64}\.json", filename) is None:
        raise ValueError("host ledger record name is invalid")
    candidate = Path(os.path.abspath(os.fspath(ledger_root)))
    try:
        if any(item.is_symlink() for item in (candidate, *candidate.parents)):
            raise ValueError("host ledger paths cannot contain symlinks")
        resolved_root = candidate.resolve(strict=True)
        if not resolved_root.is_dir():
            raise ValueError("host ledger root must be a directory")
        metadata = resolved_root.stat()
        if os.name != "nt":
            if metadata.st_uid != os.geteuid():
                raise PermissionError("host ledger root must be owned by the evaluator user")
            if stat.S_IMODE(metadata.st_mode) != 0o700:
                raise PermissionError("host ledger root permissions must be owner-only")
    except OSError as error:
        raise ValueError("host ledger root is unavailable") from error
    return resolved_root, metadata


def validate_pinned_native_ledger_directory(metadata, expected):
    if (
        not stat.S_ISDIR(metadata.st_mode)
        or metadata.st_dev != expected.st_dev
        or metadata.st_ino != expected.st_ino
    ):
        raise OSError("host ledger directory identity changed while it was being pinned")
    if os.name != "nt":
        if metadata.st_uid != os.geteuid():
            raise PermissionError("pinned host ledger directory owner is invalid")
        if stat.S_IMODE(metadata.st_mode) != 0o700:
            raise PermissionError("pinned host ledger directory permissions are invalid")


def validate_native_ledger_record(metadata):
    if not stat.S_ISREG(metadata.st_mode):
        raise OSError("native attestation ledger record is not a regular file")
    if os.name != "nt":
        if metadata.st_uid != os.geteuid():
            raise PermissionError("native attestation ledger record owner is invalid")
        if stat.S_IMODE(metadata.st_mode) != 0o600:
            raise PermissionError("native attestation ledger record permissions are invalid")


def cleanup_native_attestation_record(directory_descriptor, filename, record_descriptor):
    cleanup_errors = []
    if record_descriptor is not None:
        try:
            os.close(record_descriptor)
        except OSError as error:
            cleanup_errors.append(error)
    try:
        os.unlink(filename, dir_fd=directory_descriptor)
    except FileNotFoundError:
        pass
    except OSError as error:
        cleanup_errors.append(error)
    try:
        os.fsync(directory_descriptor)
    except OSError as error:
        cleanup_errors.append(error)
    if cleanup_errors:
        raise OSError("native attestation ledger cleanup is uncertain") from cleanup_errors[0]


def consume_native_attestation(ledger_root: Path, identity: dict) -> None:
    required = {
        "repositorySha256",
        "producerId",
        "taskKey",
        "gateInvocationId",
        "attestationId",
        "nonce",
        "eventSetSha256",
    }
    if (
        not isinstance(identity, dict)
        or set(identity) != required
        or any(not isinstance(value, str) or not value for value in identity.values())
        or NATIVE_KEY_FINGERPRINT.fullmatch(identity["repositorySha256"]) is None
        or NATIVE_KEY_FINGERPRINT.fullmatch(identity["eventSetSha256"]) is None
        or any(
            NATIVE_ADAPTER_IDENTIFIER.fullmatch(identity[field]) is None
            for field in ("producerId", "taskKey", "gateInvocationId", "nonce")
        )
    ):
        raise ValueError("native attestation ledger identity is invalid")
    canonical = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode("utf-8")
    key = hashlib.sha256(canonical).hexdigest()
    filename = f"{key}.json"
    if not native_safe_ledger_backend_supported():
        raise OSError(errno.ENOTSUP, "safe handle-relative host ledger backend is unavailable")
    directory, expected_metadata = secure_host_ledger_directory(ledger_root, filename)
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    directory_flags |= getattr(os, "O_CLOEXEC", 0)
    directory_descriptor = os.open(str(directory), directory_flags)
    record_descriptor = None
    created = False
    try:
        validate_pinned_native_ledger_directory(
            os.fstat(directory_descriptor), expected_metadata,
        )
        record_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
        record_flags |= getattr(os, "O_CLOEXEC", 0)
        try:
            record_descriptor = os.open(
                filename,
                record_flags,
                0o600,
                dir_fd=directory_descriptor,
            )
        except FileExistsError as error:
            raise NativeReplayError("NATIVE_ADAPTER_CHALLENGE_REPLAYED") from error
        created = True
        try:
            validate_native_ledger_record(os.fstat(record_descriptor))
            remaining = memoryview(canonical)
            while remaining:
                written = os.write(record_descriptor, remaining)
                if written <= 0:
                    raise OSError("native attestation ledger write made no progress")
                remaining = remaining[written:]
            os.fsync(record_descriptor)
            os.close(record_descriptor)
            record_descriptor = None
            os.fsync(directory_descriptor)
        except Exception:
            cleanup_native_attestation_record(
                directory_descriptor, filename, record_descriptor,
            )
            record_descriptor = None
            created = False
            raise
    finally:
        try:
            os.close(directory_descriptor)
        except OSError:
            if created:
                raise OSError("native attestation ledger directory close is uncertain")
            raise


def load_host_native_trust(repository_root, descriptor_path, probe_path, ledger_root) -> HostNativeTrust:
    descriptor_file = resolve_external_host_trust_path(
        repository_root, descriptor_path, directory=False,
    )
    probe_file = resolve_external_host_trust_path(
        repository_root, probe_path, directory=False,
    )
    resolved_ledger_root = resolve_external_host_trust_path(
        repository_root, ledger_root, directory=True,
    )
    descriptor = read_json(descriptor_file)
    probe = read_json(probe_file)
    validate(repository_root, descriptor, "ai/schemas/host-native-trust.schema.json")
    validate_host_native_trust_probe(probe)
    if (
        probe["producerId"] != descriptor["producerId"]
        or probe["hostId"] != descriptor["hostId"]
    ):
        native_semantic_error(
            "HOST_NATIVE_TRUST_IDENTITY_MISMATCH",
            "",
            "authoritative probe identity must match its host trust descriptor",
        )
    return HostNativeTrust(descriptor, probe, resolved_ledger_root)


def native_host_baseline_surfaces(descriptor):
    return [
        {
            "surface": surface,
            "status": "NOT_CONFIGURED",
            "reasonCode": "ADAPTER_CONFIGURATION_REQUIRED",
        }
        for surface in descriptor["surfaces"]
    ]


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


def native_semver_key(version):
    if not isinstance(version, str) or NATIVE_SEMVER.fullmatch(version) is None:
        raise ValueError("native adapter version is not SemVer 2.0.0")
    core_and_prerelease, _, _build = version.partition("+")
    core, separator, prerelease = core_and_prerelease.partition("-")
    release = tuple(int(part) for part in core.split("."))
    if not separator:
        return release, 1, ()
    prerelease_key = tuple(
        (0, int(part)) if part.isdigit() else (1, part)
        for part in prerelease.split(".")
    )
    return release, 0, prerelease_key


def load_native_bypass_attempts(root, bypass_attempts_ref, task_key, gate_invocation_id):
    if bypass_attempts_ref is None:
        return [], []
    try:
        path = native_adapter_fixture_path(root, bypass_attempts_ref)
        payload = read_json(path)
    except (InvalidStateError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise NativeBypassReferenceError("native bypass attempt reference is invalid") from error

    try:
        if not isinstance(payload, dict) or set(payload) != {"attempts"} or not isinstance(payload["attempts"], list):
            raise ValueError("native bypass attempts must be a closed attempts object")

        delivered_events = {}
        deduplication_groups = {}
        for attempt in payload["attempts"]:
            if not isinstance(attempt, dict):
                raise ValueError("native bypass attempt must be an object")
            validate(root, attempt, "ai/schemas/native-bypass-attempt.schema.json")
            if attempt["taskKey"] != task_key and attempt["lifecycle"] != "RESOLVED":
                raise ValueError("native bypass attempt task does not match this gate")
            if attempt["gateInvocationId"] != gate_invocation_id and attempt["lifecycle"] != "DETECTED":
                raise ValueError("native bypass attempt resolution does not match this gate")
            if native_bypass_attempt_has_secret(attempt):
                raise ValueError("native bypass attempt contains secret-bearing content")
            for value in native_summary_string_values(attempt["summary"]):
                if (len(value) > NATIVE_SUMMARY_MAX_BYTES
                        or len(value.encode("utf-8")) > NATIVE_SUMMARY_MAX_BYTES
                        or native_summary_has_secret(value)):
                    raise ValueError("native bypass summary is not safely redacted")
            event_id = attempt["eventId"]
            serialized = compact(attempt)
            existing = delivered_events.get(event_id)
            if existing is not None:
                if existing != serialized:
                    raise ValueError("native bypass event delivery conflicts with existing event")
                continue
            delivered_events[event_id] = serialized
            deduplication_groups.setdefault(attempt["deduplicationKey"], []).append(attempt)

        attempts = [json.loads(serialized) for serialized in delivered_events.values()]
        if len(attempts) > 256:
            raise ValueError("native bypass event set exceeds the signed snapshot bound")
        references = [
            f"{Path(bypass_attempts_ref).as_posix()}#{attempt['eventId']}"
            for attempts in deduplication_groups.values()
            for attempt in attempts
        ]
        return attempts, references
    except (InvalidStateError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError) as error:
        raise NativeBypassContractError("native bypass attempt contract is invalid") from error


def native_bypass_event_set_facts(attempts):
    canonical = json.dumps(
        sorted(attempts, key=lambda attempt: attempt["eventId"]),
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return len(attempts), hashlib.sha256(canonical).hexdigest()


def native_detection_digest(detection):
    payload = {
        key: value for key, value in detection.items()
        if key not in {
            "resolvedAt", "resolutionReason", "detectionEventId",
            "detectionGateInvocationId", "detectionEventSha256",
        }
    }
    return hashlib.sha256(json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")).hexdigest()


def native_bypass_lifecycle_state(attempts, gate_invocation_id):
    if any(
        attempt["lifecycle"] == "DETECTED"
        and attempt["gateInvocationId"] == gate_invocation_id
        for attempt in attempts
    ):
        return "UNRESOLVED", []

    groups = {}
    for attempt in attempts:
        groups.setdefault(attempt["deduplicationKey"], []).append(attempt)

    resolved_transition = False
    resolution_event_ids = []
    unresolved_detection = False
    for deduplication_key, attempts_in_group in groups.items():
        detections = [
            attempt for attempt in attempts_in_group
            if attempt["lifecycle"] == "DETECTED"
        ]
        if any(
            detection["gateInvocationId"] == gate_invocation_id
            for detection in detections
        ):
            return "UNRESOLVED", []
        current_resolutions = [
            attempt for attempt in attempts_in_group
            if attempt["lifecycle"] == "RESOLVED" and attempt["gateInvocationId"] == gate_invocation_id
        ]
        if current_resolutions:
            matched_detection_indexes = set()
            for resolution in current_resolutions:
                matching_indexes = [
                    index for index, detection in enumerate(detections)
                    if detection["eventId"] == resolution["detectionEventId"]
                    and detection["taskKey"] == resolution["taskKey"]
                    and detection["gateInvocationId"] == resolution["detectionGateInvocationId"]
                    and detection["deduplicationKey"] == deduplication_key
                    and native_detection_digest(detection) == resolution["detectionEventSha256"]
                    and parse_rfc3339_timestamp(detection["observedAt"])
                    < parse_rfc3339_timestamp(resolution["observedAt"])
                ]
                if len(matching_indexes) != 1:
                    return "INVALID_RESOLUTION", []
                matched_detection_indexes.add(matching_indexes[0])
            if len(matched_detection_indexes) != len(detections):
                unresolved_detection = True
            resolved_transition = True
            resolution_event_ids.extend(
                resolution["eventId"] for resolution in current_resolutions
            )
            continue
        if detections:
            unresolved_detection = True
    if unresolved_detection:
        return "UNRESOLVED", []
    return ("RESOLVED_TRANSITION" if resolved_transition else None), resolution_event_ids


def native_resolution_binding_reason(signed_event_ids, current_resolution_event_ids):
    signed = set(signed_event_ids)
    current = set(current_resolution_event_ids)
    missing = current - signed
    extra = signed - current
    if missing and extra:
        return "NATIVE_BYPASS_RESOLUTION_BINDING_MISMATCH"
    if missing:
        return "NATIVE_BYPASS_RESOLUTION_BINDING_MISSING"
    if extra:
        return "NATIVE_BYPASS_RESOLUTION_BINDING_EXTRA"
    return None


def validate_native_canonical_value(value):
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, int):
        if abs(value) > NATIVE_JSON_SAFE_INTEGER:
            raise ValueError("native signed integer exceeds the RFC 8785 restricted subset")
        return
    if isinstance(value, float):
        raise ValueError("native signed floats are not supported")
    if isinstance(value, str):
        try:
            value.encode("ascii")
        except UnicodeEncodeError as error:
            raise ValueError("native signed strings must be ASCII") from error
        return
    if isinstance(value, list):
        for item in value:
            validate_native_canonical_value(item)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise ValueError("native signed object keys must be strings")
            validate_native_canonical_value(key)
            validate_native_canonical_value(item)
        return
    raise ValueError("native signed data contains an unsupported JSON type")


def native_snapshot_canonical_bytes(snapshot):
    if not isinstance(snapshot, dict) or "signature" not in snapshot:
        raise ValueError("native runtime snapshot signature is required")
    payload = {key: value for key, value in snapshot.items() if key != "signature"}
    validate_native_canonical_value(payload)
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def native_snapshot_claimed_surfaces(snapshot):
    return [
        {
            "surface": surface["surface"],
            "status": surface["status"],
            "reasonCode": surface["reasonCode"],
        }
        for surface in snapshot["surfaces"]
    ]


def native_adapter_version_allowed(version_range, version):
    match = re.fullmatch(r">=(\S+) <(\S+)", version_range)
    if match is None:
        return False
    minimum, maximum = (native_semver_key(item) for item in match.groups())
    candidate = native_semver_key(version)
    return minimum <= candidate < maximum


def native_snapshot_freshness_reason(observed_at):
    observed, fractional_seconds = parse_rfc3339_timestamp(observed_at)
    now = dt.datetime.now(dt.timezone.utc)
    age_seconds = Decimal(str((now - observed).total_seconds())) - fractional_seconds
    if age_seconds < 0:
        return "NATIVE_ADAPTER_SNAPSHOT_FUTURE"
    if age_seconds > NATIVE_SNAPSHOT_MAX_AGE_SECONDS:
        return "NATIVE_ADAPTER_SNAPSHOT_STALE"
    return None


def native_runtime_snapshot_trust(root, snapshot, supported_host, current_host, task_key,
                                  gate_invocation_id, ledger_root):
    baseline_surfaces = native_host_baseline_surfaces(supported_host)
    try:
        validate(root, snapshot, "ai/schemas/native-runtime-snapshot.schema.json")
        native_snapshot_canonical_bytes(snapshot)
    except (InvalidStateError, TypeError, ValueError, KeyError):
        return baseline_surfaces, baseline_surfaces, "NATIVE_ADAPTER_SNAPSHOT_INVALID"

    claimed_surfaces = native_snapshot_claimed_surfaces(snapshot)
    if snapshot["producerId"] != supported_host["producerId"]:
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_PRODUCER_UNTRUSTED"
    if (
        snapshot["hostId"] != supported_host["hostId"]
        or snapshot["hostId"] != current_host["hostId"]
        or snapshot["hostVersion"] != current_host["hostVersion"]
    ):
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_HOST_MISMATCH"
    if not native_adapter_version_allowed(supported_host["adapterVersionRange"], snapshot["adapterVersion"]):
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_VERSION_UNTRUSTED"
    if snapshot["taskKey"] != task_key:
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_TASK_MISMATCH"
    if snapshot["gateInvocationId"] != gate_invocation_id:
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_CHALLENGE_MISMATCH"

    freshness_reason = native_snapshot_freshness_reason(snapshot["observedAt"])
    if freshness_reason is not None:
        return claimed_surfaces, baseline_surfaces, freshness_reason

    try:
        public_key_bytes = base64.b64decode(snapshot["publicKey"]["value"], validate=True)
        signature_bytes = base64.b64decode(snapshot["signature"]["value"], validate=True)
    except (ValueError, TypeError) as error:
        raise ValueError("native Ed25519 material is not valid base64") from error
    actual_fingerprint = hashlib.sha256(public_key_bytes).hexdigest()
    if (
        len(public_key_bytes) != 32
        or actual_fingerprint != snapshot["publicKey"]["fingerprintSha256"]
        or actual_fingerprint != supported_host["ed25519PublicKeyFingerprint"]
    ):
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_KEY_UNTRUSTED"
    if Ed25519PublicKey is None:
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_CRYPTO_UNAVAILABLE"
    try:
        Ed25519PublicKey.from_public_bytes(public_key_bytes).verify(
            signature_bytes,
            native_snapshot_canonical_bytes(snapshot),
        )
    except Ed25519UnsupportedAlgorithm:
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_CRYPTO_UNAVAILABLE"
    except (Ed25519InvalidSignature, ValueError, TypeError):
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_SIGNATURE_UNTRUSTED"

    if any(
        surface["status"] == "ENFORCED"
        and (
            surface["callbackProof"]["gateInvocationId"] != gate_invocation_id
            or surface["callbackProof"]["observedBeforeOperation"] is not True
            or surface["callbackProof"]["challengeResult"] != "BLOCKED"
        )
        for surface in snapshot["surfaces"]
    ):
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_CALLBACK_FAILED"

    challenge_key = (
        str(Path(root).resolve()),
        supported_host["producerId"],
        task_key,
        gate_invocation_id,
    )
    resolved_ledger_root = resolve_external_host_trust_path(
        root, ledger_root, directory=True,
    )
    repository_identity = os.path.normcase(str(Path(root).resolve(strict=True))).encode("utf-8")
    identity = {
        "repositorySha256": hashlib.sha256(repository_identity).hexdigest(),
        "producerId": snapshot["producerId"],
        "taskKey": snapshot["taskKey"],
        "gateInvocationId": snapshot["gateInvocationId"],
        "attestationId": snapshot["$id"],
        "nonce": snapshot["gateInvocationId"],
        "eventSetSha256": snapshot["bypassEventSetSha256"],
    }
    try:
        consume_native_attestation(resolved_ledger_root, identity)
    except NativeReplayError:
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_CHALLENGE_REPLAYED"
    if challenge_key in NATIVE_CONSUMED_CHALLENGES:
        return claimed_surfaces, baseline_surfaces, "NATIVE_ADAPTER_CHALLENGE_REPLAYED"
    NATIVE_CONSUMED_CHALLENGES.add(challenge_key)
    return claimed_surfaces, claimed_surfaces, None


def native_unsupported_runtime_snapshot_contract(snapshot):
    required_fields = {"producerId", "surfaces"}
    if not isinstance(snapshot, dict) or set(snapshot) != required_fields:
        return "NATIVE_ADAPTER_SNAPSHOT_INVALID"
    if not isinstance(snapshot["producerId"], str) or not snapshot["producerId"].strip():
        return "NATIVE_ADAPTER_SNAPSHOT_INVALID"
    if not isinstance(snapshot["surfaces"], list) or snapshot["surfaces"] != []:
        return "NATIVE_ADAPTER_SNAPSHOT_INVALID"
    return None


def native_adapter_gate(root, task_key, gate_invocation_id, runtime_snapshot_ref=None, bypass_attempts_ref=None,
                        policy_ref="ai/native-runtime-adapters.json",
                        host_trust: "HostNativeTrust | None" = None):
    root = Path(root).resolve()
    fallback_data = native_adapter_fallback_data()
    try:
        policy_path = native_adapter_fixture_path(root, policy_ref, canonical=True)
        policy = validate_repository_instance(root, policy_path)
        supported_host = native_adapter_supported_host(policy, host_trust)
        current_host = host_trust.probe if supported_host is not None else policy["currentHost"]
        repository_only_qualification = supported_host is None
        baseline_surfaces = (
            current_host["surfaces"]
            if supported_host is None
            else native_host_baseline_surfaces(supported_host)
        )
        fallback_data = native_adapter_data(
            current_host,
            baseline_surfaces,
            baseline_surfaces,
            [],
            repository_only_qualification,
        )
        attempts, attempt_refs = load_native_bypass_attempts(root, bypass_attempts_ref, task_key, gate_invocation_id)
        bypass_event_count, bypass_event_set_sha256 = native_bypass_event_set_facts(attempts)
        data = native_adapter_data(
            current_host,
            baseline_surfaces,
            baseline_surfaces,
            attempt_refs,
            repository_only_qualification,
        )
        if any(
            attempt["statusAtObservation"] == "ENFORCED" and attempt["decision"] == "ALLOWED_AUDIT_ONLY"
            for attempt in attempts
        ):
            return publish_native_adapter_gate_result(
                root, native_adapter_gate_result("FAIL", "NATIVE_BYPASS_ENFORCEMENT_BYPASSED", data), 1,
            )
        if any(attempt["reasonCode"] == "REDACTION_UNCERTAIN" for attempt in attempts):
            return publish_native_adapter_gate_result(
                root, native_adapter_gate_result("BLOCKED", "NATIVE_BYPASS_REDACTION_UNCERTAIN", data), 2,
            )

        contract_identifiers_valid = all(
            isinstance(value, str) and NATIVE_ADAPTER_IDENTIFIER.fullmatch(value)
            for value in (task_key, gate_invocation_id)
        )

        lifecycle_state, resolution_event_ids = native_bypass_lifecycle_state(
            attempts, gate_invocation_id,
        )
        if lifecycle_state == "UNRESOLVED":
            return publish_native_adapter_gate_result(
                root, native_adapter_gate_result("BLOCKED", "NATIVE_BYPASS_UNRESOLVED", data), 2,
            )
        if lifecycle_state == "INVALID_RESOLUTION":
            return publish_native_adapter_gate_result(
                root, native_adapter_gate_result("BLOCKED", "NATIVE_BYPASS_RESOLUTION_INVALID", data), 2,
            )
        if lifecycle_state == "RESOLVED_TRANSITION" and contract_identifiers_valid:
            if supported_host is None:
                return publish_native_adapter_gate_result(
                    root,
                    native_adapter_gate_result(
                        "BLOCKED", "NATIVE_BYPASS_RESOLUTION_HOST_UNSUPPORTED", data,
                    ),
                    2,
                )
            if runtime_snapshot_ref is None:
                return publish_native_adapter_gate_result(
                    root,
                    native_adapter_gate_result(
                        "BLOCKED", "NATIVE_BYPASS_RESOLUTION_SNAPSHOT_REQUIRED", data,
                    ),
                    2,
                )

        snapshot = None
        snapshot_claimed_surfaces = baseline_surfaces
        snapshot_trusted_surfaces = baseline_surfaces
        snapshot_data = data
        if runtime_snapshot_ref is not None:
            snapshot = read_json(native_adapter_fixture_path(root, runtime_snapshot_ref))
            if not isinstance(snapshot, dict):
                raise ValueError("native runtime snapshot must be a JSON object")
            if supported_host is not None:
                snapshot_claimed_surfaces, snapshot_trusted_surfaces, snapshot_error = native_runtime_snapshot_trust(
                    root,
                    snapshot,
                    supported_host,
                    current_host,
                    task_key,
                    gate_invocation_id,
                    host_trust.ledger_root,
                )
                snapshot_data = native_adapter_data(
                    current_host,
                    snapshot_claimed_surfaces,
                    snapshot_trusted_surfaces,
                    attempt_refs,
                    False,
                )
                if snapshot_error is not None:
                    return publish_native_adapter_gate_result(
                        root, native_adapter_gate_result("BLOCKED", snapshot_error, snapshot_data), 2,
                    )
            else:
                snapshot_error = native_unsupported_runtime_snapshot_contract(snapshot)
                if snapshot_error is not None:
                    return publish_native_adapter_gate_result(
                        root, native_adapter_gate_result("BLOCKED", snapshot_error, data), 2,
                    )

        if not contract_identifiers_valid:
            return publish_native_adapter_gate_result(
                root,
                native_adapter_gate_result("BLOCKED", "INVALID_NATIVE_ADAPTER_GATE_ARGUMENTS", data),
                2,
            )

        if supported_host is None:
            return publish_native_adapter_gate_result(
                root, native_adapter_gate_result("UNSUPPORTED", "HOST_UNSUPPORTED", data), 6,
            )
        if runtime_snapshot_ref is None:
            return publish_native_adapter_gate_result(
                root, native_adapter_gate_result("NOT_CONFIGURED", "NATIVE_ADAPTER_NOT_CONFIGURED", data), 3,
            )

        if any(surface["status"] != "ENFORCED" for surface in snapshot_trusted_surfaces):
            return publish_native_adapter_gate_result(
                root, native_adapter_gate_result("BLOCKED", "NATIVE_ADAPTER_ENFORCEMENT_INCOMPLETE", snapshot_data), 2,
            )
        if (
            snapshot["bypassEventCount"] != bypass_event_count
            or snapshot["bypassEventSetSha256"] != bypass_event_set_sha256
        ):
            return publish_native_adapter_gate_result(
                root,
                native_adapter_gate_result("BLOCKED", "NATIVE_BYPASS_EVENT_SET_MISMATCH", snapshot_data),
                2,
            )
        resolution_binding_reason = native_resolution_binding_reason(
            snapshot["resolutionEventIds"], resolution_event_ids,
        )
        if resolution_binding_reason is not None:
            return publish_native_adapter_gate_result(
                root,
                native_adapter_gate_result("BLOCKED", resolution_binding_reason, snapshot_data),
                2,
            )
        return publish_native_adapter_gate_result(
            root, native_adapter_gate_result("PASS", None, snapshot_data), 0,
        )
    except NativeBypassContractError:
        return publish_native_adapter_gate_result(
            root, native_adapter_gate_result("FAIL", "NATIVE_BYPASS_CONTRACT_INVALID", fallback_data), 1,
        )
    except NativeBypassReferenceError:
        return publish_native_adapter_gate_result(
            root, native_adapter_gate_result("BLOCKED", "NATIVE_BYPASS_REFERENCE_INVALID", fallback_data), 2,
        )
    except (InvalidStateError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
        return publish_native_adapter_gate_result(
            root, native_adapter_gate_result("BLOCKED", "NATIVE_ADAPTER_EVALUATION_INVALID", fallback_data), 2,
        )


def run_native_adapter_gate_cli(arguments):
    if not isinstance(arguments.repository_root, str) or not arguments.repository_root or not all(
        isinstance(value, str) and NATIVE_ADAPTER_IDENTIFIER.fullmatch(value)
        for value in (arguments.task_key, arguments.gate_invocation_id)
    ):
        result, status = invalid_cli_result("native-adapter-gate")
        print(compact(result))
        return result, status
    root = Path(arguments.repository_root).resolve()
    if not isinstance(arguments.output, str) or not arguments.output:
        result = native_adapter_gate_result(
            "BLOCKED", "NATIVE_ADAPTER_OUTPUT_PATH_INVALID", native_adapter_fallback_data(),
        )
        print(compact(result))
        return result, 2
    result, status = native_adapter_gate(
        root,
        arguments.task_key,
        arguments.gate_invocation_id,
        host_trust=None,
    )
    output_status = write_resolve_output(root, arguments.output, result)
    if output_status != 0:
        fallback, fallback_status = publish_native_adapter_gate_result(
            root,
            native_adapter_gate_result("BLOCKED", "NATIVE_ADAPTER_OUTPUT_PATH_INVALID", native_adapter_fallback_data()),
            2,
        )
        print(compact(fallback))
        return fallback, fallback_status
    return result, status


def native_adapter_phase2c_leaf(root, task_key, gate_invocation_id, runtime_snapshot_ref=None,
                                bypass_attempts_ref=None):
    adapter_result, _ = native_adapter_gate(
        root,
        task_key,
        gate_invocation_id,
        runtime_snapshot_ref,
        bypass_attempts_ref,
    )
    return {
        "checkId": NATIVE_ADAPTER_CHECK_ID,
        "result": adapter_result["phase2cLeafResult"],
        "evidenceRef": "ai/native-runtime-adapters.json",
        "leafResultRef": adapter_result["$id"],
        "leafResultSha256": hashlib.sha256(compact(adapter_result).encode("utf-8")).hexdigest(),
        "producerId": NATIVE_ADAPTER_CHECK_ID,
        "reason": adapter_result["reason"],
    }




CI_GATE_CHECK_ID = "phase-3b-ci-gates"


def ci_evidence_gate_result(result, reason, data):
    phase2c_leaf_result = {
        "PASS": "PASS",
        "FAIL": "FAIL",
        "BLOCKED": "BLOCKED",
        "NOT_CONFIGURED": "BLOCKED",
        "UNSUPPORTED": "NOT_APPLICABLE",
    }[result]
    payload = {
        "$schema": "ai/schemas/ci-gate-result.schema.json",
        "$id": "ai/ci-gate-result.json",
        "schemaVersion": 1,
        "operation": "CI_EVIDENCE_GATE",
        "result": result,
        "phase2cLeafResult": phase2c_leaf_result,
        "reason": reason,
        "data": data,
    }
    payload["data"]["phase2CLeafResult"] = phase2c_leaf_result
    return payload


def ci_evidence_gate_exit(result):
    return {
        "PASS": 0,
        "FAIL": 1,
        "BLOCKED": 2,
        "NOT_CONFIGURED": 3,
        "UNSUPPORTED": 6,
    }[result]


def ci_evidence_gate_data(status, task_key, gate_invocation_id):
    current_ci = status["currentCi"]
    return {
        "taskKey": task_key,
        "gateInvocationId": gate_invocation_id,
        "requiredCheck": current_ci["requiredCheck"],
        "provider": current_ci["provider"],
        "workflowRefs": current_ci["workflowRefs"],
        "nativeAdapterInstallation": current_ci["nativeAdapterInstallation"],
        "durableEvidence": current_ci["durableEvidence"],
        "remoteRunner": current_ci["remoteRunner"],
        "nativeAdapterLeaf": status["phase2cLink"],
        "cachePolicy": status["cachePolicy"],
        "phase2CLeafResult": "BLOCKED",
    }


def ci_evidence_gate(root, task_key, gate_invocation_id, ci_status_ref="ai/ci-capability-status.json"):
    root = Path(root).resolve()
    fallback_data = {
        "taskKey": task_key,
        "gateInvocationId": gate_invocation_id,
        "requiredCheck": CI_GATE_CHECK_ID,
        "provider": "github-actions",
        "workflowRefs": [],
        "nativeAdapterInstallation": {"status": "NOT_CONFIGURED", "reasonCode": "CI_STATUS_UNAVAILABLE"},
        "durableEvidence": {"status": "NOT_CONFIGURED", "retentionDays": 90, "artifactRefs": [], "retainedRun": None},
        "remoteRunner": {"status": "NOT_CONFIGURED", "completionBlocking": True, "reasonCode": "CI_STATUS_UNAVAILABLE"},
        "nativeAdapterLeaf": {"nativeAdapterCheckId": "native-runtime-adapter", "currentHostResult": "UNSUPPORTED"},
        "cachePolicy": {"reuse": "FORBIDDEN_WITHOUT_MATCHING_RUN_ID", "handoff": "SUMMARY_ONLY"},
        "phase2CLeafResult": "BLOCKED",
    }
    try:
        if not all(isinstance(value, str) and NATIVE_ADAPTER_IDENTIFIER.fullmatch(value) for value in (task_key, gate_invocation_id)):
            return ci_evidence_gate_result("BLOCKED", "INVALID_CI_GATE_ARGUMENTS", fallback_data), 2
        status = validate_repository_instance(root, ci_status_ref)
        data = ci_evidence_gate_data(status, task_key, gate_invocation_id)
        workflows_configured = all((root / ref).is_file() for ref in status["currentCi"]["workflowRefs"])
        evidence = status["currentCi"]["durableEvidence"]
        native_install = status["currentCi"]["nativeAdapterInstallation"]
        remote_runner = status["currentCi"]["remoteRunner"]
        if not workflows_configured:
            return ci_evidence_gate_result("NOT_CONFIGURED", "CI_WORKFLOW_NOT_CONFIGURED", data), 3
        if evidence["status"] != "AVAILABLE":
            return ci_evidence_gate_result("NOT_CONFIGURED", "CI_EVIDENCE_NOT_AVAILABLE", data), 3
        retained_run = evidence.get("retainedRun")
        artifact_refs = evidence.get("artifactRefs", [])
        expected_bindings = {
            "repository", "commitSha", "workflowRunId", "jobId", "attempt", "taskKey",
            "gateInvocationId", "nativeAdapterStatusDigest", "bypassEventSetSha256", "resolutionEventIds",
        }
        if (
            not isinstance(retained_run, dict)
            or set(evidence.get("requiredBindings", [])) != expected_bindings
            or not artifact_refs
            or retained_run.get("taskKey") != task_key
            or retained_run.get("gateInvocationId") != gate_invocation_id
        ):
            return ci_evidence_gate_result("BLOCKED", "CI_DURABLE_EVIDENCE_IDENTITY_MISSING", data), 2
        if any(not (root / ref).is_file() for ref in artifact_refs):
            return ci_evidence_gate_result("BLOCKED", "CI_DURABLE_EVIDENCE_ARTIFACT_MISSING", data), 2
        if native_install["status"] != "INSTALLED":
            return ci_evidence_gate_result("BLOCKED", "CI_NATIVE_ADAPTER_NOT_INSTALLED", data), 2
        if remote_runner["status"] != "PASS":
            return ci_evidence_gate_result("BLOCKED", "CI_REMOTE_RUNNER_NOT_PASSING", data), 2
        return ci_evidence_gate_result("PASS", None, data), 0
    except (InvalidStateError, OSError, TypeError, ValueError, KeyError, json.JSONDecodeError):
        return ci_evidence_gate_result("BLOCKED", "CI_EVIDENCE_EVALUATION_INVALID", fallback_data), 2


def run_ci_evidence_gate_cli(arguments):
    result, status = ci_evidence_gate(
        Path(arguments.repository_root).resolve(),
        arguments.task_key,
        arguments.gate_invocation_id,
        arguments.ci_status,
    )
    output_status = write_resolve_output(Path(arguments.repository_root).resolve(), arguments.output, result)
    if output_status != 0:
        fallback, fallback_status = ci_evidence_gate(
            Path(arguments.repository_root).resolve(), arguments.task_key, arguments.gate_invocation_id, arguments.ci_status,
        )
        fallback["result"] = "BLOCKED"
        fallback["phase2cLeafResult"] = "BLOCKED"
        fallback["reason"] = "CI_GATE_OUTPUT_PATH_INVALID"
        print(compact(fallback))
        return fallback, 2
    return result, status

def verification_gate(root, change_type, entry_point, leaf_results_ref=None, task_key=None,
                      gate_invocation_id=None, runtime_snapshot_ref=None, bypass_attempts_ref=None):
    root = Path(root).resolve()
    try:
        policy_path = root / "ai" / "verification-policy.json"
        policy = validate_repository_instance(root, policy_path)
        policy_sha256 = digest(policy_path)
        change_types = {item["id"]: item for item in policy["changeTypes"]}
        checks = {item["id"]: item for item in policy["checks"]}
        if change_type not in change_types:
            return publish_verification_gate_result(root, verification_gate_result(
                "POLICY_VIOLATION", "UNKNOWN_CHANGE_TYPE", None,
            ), 4)
        entry_ids = {item["id"] for item in policy["entryPoints"]}
        if entry_point not in entry_ids:
            return publish_verification_gate_result(root, verification_gate_result(
                "POLICY_VIOLATION", "UNKNOWN_ENTRY_POINT", None,
            ), 4)
        change = change_types[change_type]
        if leaf_results_ref is not None:
            loaded_leaves = verification_leaf_references(root, leaf_results_ref)
        commit_sha = repository_commit_sha(root)
        if leaf_results_ref is None:
            leaf_results = {}
        else:
            leaf_results = load_verified_leaf_results(
                root,
                loaded_leaves,
                task_key,
                gate_invocation_id,
                commit_sha,
                policy,
            )
        native_leaf = native_adapter_phase2c_leaf(
            root,
            task_key,
            gate_invocation_id,
            runtime_snapshot_ref,
            bypass_attempts_ref,
        )
        native_policy_check = checks.get(NATIVE_ADAPTER_CHECK_ID)
        if native_policy_check is None:
            raise InvalidStateError([validation_error(
                "VERIFICATION_POLICY_CHECK_INVALID",
                message="verification policy does not define the internal native check",
            )])
        native_leaf["producerId"] = native_policy_check["producerId"]
        native_leaf["commitSha"] = commit_sha
        native_leaf["policySha256"] = policy_sha256
        if not all(
            isinstance(value, str) and NATIVE_ADAPTER_IDENTIFIER.fullmatch(value)
            for value in (task_key, gate_invocation_id)
        ):
            raw = native_leaf
            mapped_result = map_verification_leaf(
                raw["result"], True, raw.get("reason") == "HOST_UNSUPPORTED",
            )
            data = {
                "changeType": change_type,
                "entryPoint": entry_point,
                "minimumVerificationLevel": change["minimumVerificationLevel"],
                "completenessEvaluated": True,
                "checks": [verification_check_result(
                    NATIVE_ADAPTER_CHECK_ID, True, raw, mapped_result,
                )],
                "createdAiRuns": False,
            }
            overall = aggregate_verification_gate(data["checks"])
            return publish_verification_gate_result(root, verification_gate_result(
                overall, None if overall == "PASS" else "VERIFICATION_GATE_" + overall, data,
            ), verification_gate_exit(overall))
        if entry_point not in change["entryPoints"]:
            native_check = verification_check_result(
                NATIVE_ADAPTER_CHECK_ID,
                True,
                native_leaf,
                map_verification_leaf(
                    native_leaf["result"], True,
                    native_leaf.get("reason") == "HOST_UNSUPPORTED",
                ),
            )
            entry_point_check = verification_check_result(entry_point, False, {
                "result": "NOT_APPLICABLE",
                "reason": "Entry point is not applicable to the selected change type.",
                "evidenceRef": "ai/verification-policy.json",
            }, "NOT_APPLICABLE")
            if native_check["mappedResult"] in {"BLOCKED", "FAIL"}:
                data = {
                    "changeType": change_type,
                    "entryPoint": entry_point,
                    "minimumVerificationLevel": change["minimumVerificationLevel"],
                    "completenessEvaluated": True,
                    "checks": [native_check, entry_point_check],
                    "createdAiRuns": False,
                }
                overall = aggregate_verification_gate(data["checks"])
                return publish_verification_gate_result(root, verification_gate_result(
                    overall, None if overall == "PASS" else "VERIFICATION_GATE_" + overall, data,
                ), verification_gate_exit(overall))
            data = {
                "changeType": change_type,
                "entryPoint": entry_point,
                "minimumVerificationLevel": change["minimumVerificationLevel"],
                "completenessEvaluated": True,
                "checks": [native_check, entry_point_check],
                "createdAiRuns": False,
            }
            return publish_verification_gate_result(root, verification_gate_result(
                "NOT_APPLICABLE", "ENTRY_POINT_NOT_APPLICABLE", data,
            ), 6)
        check_ids = list(dict.fromkeys(change["requiredChecks"] + change["optionalChecks"]))
        mapped_checks = []
        for check_id in check_ids:
            policy_check = checks.get(check_id)
            if policy_check is None:
                raise InvalidStateError([validation_error(
                    "VERIFICATION_POLICY_CHECK_INVALID",
                    message="verification policy references an unknown check",
                )])
            if check_id == NATIVE_ADAPTER_CHECK_ID:
                raw = native_leaf
            else:
                raw = leaf_results.get(check_id, default_leaf_result_for_check(check_id, policy_check))
            required = check_id in change["requiredChecks"]
            raw_result = raw["result"]
            mapped_checks.append(verification_check_result(
                check_id,
                required,
                raw,
                map_verification_leaf(
                    raw_result,
                    required,
                    (
                        check_id == NATIVE_ADAPTER_CHECK_ID
                        and raw.get("reason") == "HOST_UNSUPPORTED"
                    ) or change_type in policy_check["notApplicableFor"],
                ),
            ))
        overall = aggregate_verification_gate(mapped_checks)
        data = {
            "changeType": change_type,
            "entryPoint": entry_point,
            "minimumVerificationLevel": change["minimumVerificationLevel"],
            "completenessEvaluated": True,
            "checks": mapped_checks,
            "createdAiRuns": False,
        }
        native_check = next(
            (item for item in mapped_checks if item["checkId"] == NATIVE_ADAPTER_CHECK_ID),
            None,
        )
        if overall == "PASS" and native_check is not None and native_check["reason"] == "HOST_UNSUPPORTED":
            reason = "REPOSITORY_ONLY_HOST_UNSUPPORTED"
        else:
            reason = None if overall == "PASS" else "VERIFICATION_GATE_" + overall
        return publish_verification_gate_result(root, verification_gate_result(overall, reason, data), verification_gate_exit(overall))
    except VerificationNotConfiguredError as error:
        return publish_verification_gate_result(root, verification_gate_result(
            "BLOCKED", error.errors[0]["code"], None, errors=error.errors,
        ), 2)
    except InvalidStateError as error:
        return publish_verification_gate_result(root, verification_gate_result(
            "INVALID_STATE", error.errors[0]["code"], None, errors=error.errors,
        ), 5)
    except (OSError, ValueError, TypeError):
        return publish_verification_gate_result(root, verification_gate_result(
            "INVALID_STATE", "VERIFICATION_GATE_FAILED", None,
        ), 5)


def run_verification_gate_cli(arguments):
    root = Path(arguments.repository_root).resolve()
    result, status = verification_gate(
        root,
        arguments.change_type,
        arguments.entry_point,
        arguments.leaf_results_file,
        arguments.task_key,
        arguments.gate_invocation_id,
        arguments.runtime_snapshot,
        arguments.bypass_attempts,
    )
    output_status = write_resolve_output(root, arguments.output, result)
    if output_status != 0:
        return publish_verification_gate_result(root, verification_gate_result(
            "POLICY_VIOLATION", "VERIFICATION_GATE_OUTPUT_PATH_INVALID", None,
        ), 4)
    return result, status


def main():
    parser = ClosedArgumentParser(add_help=False)
    subparsers = parser.add_subparsers(dest="operation", required=True)
    preflight = subparsers.add_parser("preflight", add_help=False)
    preflight.add_argument("--repository-root", required=True)
    preflight.add_argument("--runtime-command", choices=("python3", "python"), required=True)
    preflight.add_argument("--record", action="store_true")
    preflight.add_argument("--invalid-arguments", action="store_true")
    resolve = subparsers.add_parser("resolve", add_help=False)
    resolve.add_argument("--repository-root", required=True)
    resolve.add_argument("--registry", required=True)
    resolve.add_argument("--command-id", required=True)
    resolve.add_argument("--parameters-file")
    resolve.add_argument("--output", required=True)
    run_start_parser = subparsers.add_parser("run-start", add_help=False)
    run_start_parser.add_argument("--repository-root", required=True)
    run_start_parser.add_argument("--run-id", required=True)
    run_start_parser.add_argument("--task-key", required=True)
    pre_command_parser = subparsers.add_parser("pre-command", add_help=False)
    add_command_arguments(pre_command_parser)
    execute_command_parser = subparsers.add_parser("execute-command", add_help=False)
    add_command_arguments(execute_command_parser)
    post_command_parser = subparsers.add_parser("post-command", add_help=False)
    post_command_parser.add_argument("--repository-root", required=True)
    post_command_parser.add_argument("--run-id", required=True)
    post_command_parser.add_argument("--attempt-id", required=True)
    done_claim_parser = subparsers.add_parser("done-claim-prepare", add_help=False)
    done_claim_parser.add_argument("--repository-root", required=True)
    done_claim_parser.add_argument("--run-id", required=True)
    done_claim_parser.add_argument("--claim", required=True)
    verify_finalized_parser = subparsers.add_parser("verify-finalized", add_help=False)
    verify_finalized_parser.add_argument("--repository-root", required=True)
    verify_finalized_parser.add_argument("--run-id", required=True)
    repo_intake_parser = subparsers.add_parser("repo-intake", add_help=False)
    repo_intake_parser.add_argument("--repository-root", required=True)
    repo_intake_parser.add_argument("--output", required=True)
    verification_gate_parser = subparsers.add_parser("verification-gate", add_help=False)
    verification_gate_parser.add_argument("--repository-root", required=True)
    verification_gate_parser.add_argument("--change-type", required=True)
    verification_gate_parser.add_argument("--entry-point", required=True)
    verification_gate_parser.add_argument("--leaf-results-file")
    verification_gate_parser.add_argument("--task-key", required=True)
    verification_gate_parser.add_argument("--gate-invocation-id", required=True)
    verification_gate_parser.add_argument("--runtime-snapshot")
    verification_gate_parser.add_argument("--bypass-attempts")
    verification_gate_parser.add_argument("--output", required=True)
    native_adapter_gate_parser = subparsers.add_parser("native-adapter-gate", add_help=False)
    native_adapter_gate_parser.add_argument("--repository-root", required=True)
    native_adapter_gate_parser.add_argument("--task-key", required=True)
    native_adapter_gate_parser.add_argument("--gate-invocation-id", required=True)
    native_adapter_gate_parser.add_argument("--output", required=True)
    ci_evidence_gate_parser = subparsers.add_parser("ci-evidence-gate", add_help=False)
    ci_evidence_gate_parser.add_argument("--repository-root", required=True)
    ci_evidence_gate_parser.add_argument("--task-key", required=True)
    ci_evidence_gate_parser.add_argument("--gate-invocation-id", required=True)
    ci_evidence_gate_parser.add_argument("--ci-status", default="ai/ci-capability-status.json")
    ci_evidence_gate_parser.add_argument("--output", required=True)
    try:
        arguments = parser.parse_args()
    except ValueError:
        if len(sys.argv) > 1 and sys.argv[1] in (
            "run-start", "pre-command", "execute-command", "post-command", "done-claim-prepare",
            "verify-finalized", "verification-gate", "native-adapter-gate", "ci-evidence-gate",
        ):
            result, status = invalid_cli_result(sys.argv[1])
            print(compact(result))
            return status
        if len(sys.argv) > 1 and sys.argv[1] == "resolve":
            result, status = policy_violation("INVALID_RESOLVE_ARGUMENTS")
        else:
            result, status = gateway_result("INVALID_STATE", "INVALID_PREFLIGHT_ARGUMENTS"), 5
        print(compact(result))
        return status
    if arguments.operation == "preflight":
        result, status = run_preflight(arguments)
        print(compact(result))
        return status
    if arguments.operation in (
        "run-start", "pre-command", "execute-command", "post-command", "done-claim-prepare",
        "verify-finalized",
    ):
        handlers = {
            "run-start": run_start_cli,
            "pre-command": run_pre_command_cli,
            "execute-command": run_execute_command_cli,
            "post-command": run_post_command_cli,
            "done-claim-prepare": run_done_claim_prepare_cli,
            "verify-finalized": run_verify_finalized_cli,
        }
        result, status = handlers[arguments.operation](arguments)
        print(compact(result))
        return status
    if arguments.operation == "repo-intake":
        result, status = run_repo_intake_cli(arguments)
        return status
    if arguments.operation == "verification-gate":
        result, status = run_verification_gate_cli(arguments)
        return status
    if arguments.operation == "native-adapter-gate":
        result, status = run_native_adapter_gate_cli(arguments)
        return status
    if arguments.operation == "ci-evidence-gate":
        result, status = run_ci_evidence_gate_cli(arguments)
        return status
    result, status = run_resolve(arguments)
    result, status, output_status = publish_resolve_output(
        arguments.repository_root,
        arguments.output,
        result,
        status,
    )
    if output_status != 0:
        result, status = policy_violation("RESOLVE_OUTPUT_PATH_INVALID")
        result, status = publish_result(arguments.repository_root, result, status)
        print(compact(result))
        return output_status
    return status


if __name__ == "__main__":
    raise SystemExit(main())
