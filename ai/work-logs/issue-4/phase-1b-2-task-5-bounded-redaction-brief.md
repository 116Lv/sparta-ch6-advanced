# Phase 1B-2 Task 5 Bounded Redaction Brief

## Routing

Owning feature: none. This is repository-wide AI workflow enforcement under the approved Phase 1B specification and Phase 1B-2 Task 5 plan.

## Scope

Implement only bounded concurrent stdout/stderr capture, strict UTF-8 redaction, immutable process-attempt-first publication, command-result/log publication, terminal reservation transition, and standalone POST_COMMAND persistence.

## Fixed Bounds

- Read at most 65536 bytes per stream read.
- Retain 8192 bytes of carry per stream.
- Accept exactly 1048576 bytes per stream and 2097152 bytes combined; one byte over blocks.
- Accept sensitive candidates and internally injected literals through 4096 UTF-8 bytes; 4097 bytes blocks.
- Keep the public configured-literal set empty and never read a secret-file path.

## Outcome Boundary

Preserve process-attempt evidence before terminal publication. PASS and FAIL require fully scrubbed immutable stdout/stderr logs. Spawn failure, timeout/resource/output limits, and redaction uncertainty become BLOCKED with null command-result execution/log fields. Only redaction or evidence-write uncertainty appends immutable `UNSCRUBBED_EVIDENCE`. A failure after process-attempt publication leaves the reservation visibly RESERVED for recovery.

## Explicit Deferrals

Do not add Task 6 shell entry points or Phase 1B-3 finalization, manifest publication, `run.json`, registry transitions, or done-claim behavior. Tests use fake/mock processes and temporary repositories only.
