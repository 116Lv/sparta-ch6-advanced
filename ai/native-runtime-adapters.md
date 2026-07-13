# Native Runtime Adapter Policy

`ai/native-runtime-adapters.json` is the canonical, schema-validated policy for
native runtime adapter support. This document records the same current-host
discovery result in a reviewable form; the JSON remains authoritative for
automation and status evaluation.

## Current Host Discovery

The canonical policy identifies the current host as `codex-desktop` version
`1.0.0`. `supportedHosts: []` means that Phase 3A declares no supported native
runtime adapter host or minimum supported host version.

The repository policy has no authoritative native registration manifest or
callable interceptor installation API for the current host. It therefore does
not infer native interception from repository shell, file-read, search, or
tool-call access. The policy source and its probe reference are
`ai/native-runtime-adapters.json` and
`docs/superpowers/specs/2026-07-13-ai-workflow-phase-3a-native-runtime-adapters-design.md`.

| Surface | Status | Reason code |
| --- | --- | --- |
| `COMMAND` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `FILE_READ` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `SEARCH` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |
| `TOOL_CALL` | `UNSUPPORTED` | `HOST_NOT_SUPPORTED` |

`UNSUPPORTED` is a current-host discovery result, not a claim that the
repository command gateway is unenforced. The native-adapter completion policy
maps this state to `NOT_APPLICABLE` with an explicit repository-only
qualification. It must not be represented as native enforcement.

## Future Support

A host can move from `UNSUPPORTED` only when `ai/native-runtime-adapters.json`
adds a supported-host declaration backed by an authoritative host version
probe, official hook-surface evidence, a trusted producer identity, and the
required surface configuration. Until then, all four current-host surfaces
remain `UNSUPPORTED` with `HOST_NOT_SUPPORTED`.
