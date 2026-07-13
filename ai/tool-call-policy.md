# AI Workflow Tool-Call Policy

## Human Policy Notes

This policy constrains broad searches, repeated reads, command rediscovery, and duplicate external tool calls. JSON is canonical where a structured cache or context record exists. Markdown is not parsed as executable state.

Product commands remain NOT RUN unless a later approved gateway execution explicitly allows them. Phase 2A does not evaluate verification completeness.

## Repository-Only Boundary

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Phase 2A can record policy, cache keys, and review evidence; it cannot prevent all direct shell, editor, MCP, browser, or host-runtime actions.

## Limits

- Prefer `rg` or targeted file reads over broad tree scans.
- Reuse `ai/context-map.md` and `ai/context-map.json` before rediscovering document routes.
- Reuse `ai/project-state.json` and `ai/command-registry.json` before rediscovering stack, ports, commands, and verification capabilities.
- Record why rediscovery was necessary when a cache entry is `STALE`, `UNCERTAIN`, missing, or mapped to changed inputs.
- Do not treat human manual command results as AI workflow verification evidence.

## Completion Impact

Detected bypasses and unexplained repeated discovery can block later review or completion claims. Phase 2A itself does not claim host-wide enforcement.
