# AI Workflow Tool-Call Policy

## Human Policy Notes

This policy constrains broad searches, repeated reads, command rediscovery, and duplicate external tool calls. JSON is canonical where a structured cache or context record exists. Markdown is not parsed as executable state.

Product commands remain NOT RUN unless a later approved gateway execution explicitly allows them. Phase 2A does not evaluate verification completeness.

## Repository-Only Boundary

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Phase 2A can record policy, cache keys, and review evidence; it cannot prevent all direct shell, editor, MCP, browser, or host-runtime actions.

Phase 3A declares the current host `UNSUPPORTED` for native `COMMAND`, `FILE_READ`, `SEARCH`, and `TOOL_CALL` interception. The internal native adapter check reports that state to Phase 2C as `NOT_APPLICABLE` with `HOST_UNSUPPORTED`; it does not turn repository policy into host-wide enforcement.

## Limits

- Prefer `rg` or targeted file reads over broad tree scans.
- Reuse the current route and handoff before rediscovering document routes. Load `ai/context-map.json` and its policy only when route selection, phase escalation, cache freshness, or workflow rediscovery is actually in scope.
- Apply the selected phase's typed `includePaths` scopes to ordinary searches. Every read document must be covered by an include scope and must not remain deferred. Search a `deferredPaths` area only after its matching typed `optInPaths` trigger is recorded in handoff `activatedTriggers`, then materialize only the exact paths actually selected; READY and PARTIAL record those exact paths in `readDocuments`. Work-log access additionally requires a non-null `activeIssue`; narrow it to the exact summary and listed role refs, read those refs for READY or PARTIAL, and do not widen it through reusable, foreign, unlisted, subtree, direct-children, descendant, or excluded scopes.
- Never search or opt into canonical `excludedPaths`.
- Reuse `ai/project-state.json` and `ai/command-registry.json` before rediscovering stack, ports, commands, and verification capabilities.
- Record why rediscovery was necessary when a cache entry is `STALE`, `UNCERTAIN`, missing, or mapped to changed inputs.
- Do not treat human manual command results as AI workflow verification evidence.

## Completion Impact

Detected bypasses and unexplained repeated discovery can block later review or completion claims. Phase 2A itself does not claim host-wide enforcement.

`scripts/ai/command-runner.sh` is the only supported product-command path. Native adapters may observe, classify, or block host operations but never execute product commands, and verification accepts no precomputed adapter result. Supported-host adapter faults remain completion-blocking. CI installation, remote-runner guarantees, durable native evidence, and cross-host parity are deferred to Phase 3B.
