# AI Workflow Context Map

## Human Policy Notes

`ai/context-map.json` is the canonical source for Phase 2A repository context routes. This Markdown file explains how agents should use those routes during review and handoff. JSON is canonical. Markdown is not parsed as executable state.

Phase 2A records reusable context and route IDs only. Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness, does not mark registry entries `VERIFIED`, and does not claim host-wide interception.

repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. Until native adapters exist, detected bypasses are audit/review inputs and may block later completion claims, but this file does not claim prevention.

## Route IDs

| Route ID | Purpose | Minimum Documents |
|---|---|---|
| `repo-wide-ai-workflow` | Repository-wide AI workflow policy, gates, evidence, and cache work | `AGENTS.md`, `ai/document-routing.md`, `ai/context-map.md`, relevant `ai/*` policy |
| `product-feature` | Product feature requirements, implementation, and verification | `AGENTS.md`, `ai/document-routing.md`, owning `specs/{feature}/spec.md` |
| `documentation-only` | Non-normative wording, index, or report updates | Directly affected document after ownership routing |

## Repository Surfaces

- Product source: `src/main/**`
- Product tests: `src/test/**`
- Feature specs: `specs/**`
- Project docs: `docs/**`
- Architecture decisions: `adr/**`
- AI workflow policy: `ai/**`
- Workflow scripts: `scripts/ai/**`

## Generated And Excluded Paths

- Local raw evidence: `.ai-runs/**` is ignored and must not be committed.
- Python caches: `**/__pycache__/**` are generated local artifacts.
- Generated summary sections between `<!-- GENERATED:START ... -->` and `<!-- GENERATED:END ... -->` cannot be edited independently of canonical JSON.

## Phase 2A Boundary

Use this map to avoid rediscovering repository structure. If the route or surface mapping is stale, repo intake reports proposal-only refresh records. It does not rewrite project state automatically in Phase 2A.
