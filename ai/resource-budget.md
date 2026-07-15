# AI Workflow Resource Budget

## Human Policy Notes

This file defines Phase 2A default budgets for repository discovery and cache reuse. JSON is canonical where a structured cache record exists. Markdown is not parsed as executable state.

Product commands remain NOT RUN. Phase 2A does not evaluate verification completeness.

## Default Budgets

| Activity | Default Limit | Exception Record |
|---|---:|---|
| Broad repository searches per task before using context map | 2 | Record route and why cached context was insufficient |
| Full tree file listings per task | 1 | Record stale or missing context-map reason |
| Re-reading unchanged policy files | 1 per file per task phase | Record digest or route change |
| Command capability rediscovery | 0 unless intake invalidation applies | Record affected registry IDs |
| External tool calls for the same fact | 1 | Record why prior evidence was stale or inconclusive |

Budgets apply per selected route phase. Reading a deferred document after its declared trigger is required work, not a budget exception. Expanding into a deferred path requires the matching opt-in trigger; expanding into an excluded path is prohibited rather than budgeted.

## Phase 2A Boundary

Repository scripts cannot intercept every host file read, search, or external tool call before Phase 3. These budgets are enforced through policy, work logs, cache records, and review gates in Phase 2A.

## Exceptions

Exceptions must name the route ID, changed input, stale cache entry, or blocker that required extra discovery. They do not authorize product command execution.
