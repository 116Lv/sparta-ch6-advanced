# Work Log Index

The Orchestrator maintains this index. Each row links the active recovery record for one dispatchable unit. `pending_issue` rows must be reconciled to an `issue-{number}` directory when GitHub Issue creation becomes available. A `done` workflow status records only that work-log lifecycle; it does not claim Issue closure, a registry `VERIFIED` transition, or unqualified overall DONE.

| Issue | Tracking Status | Workflow Status | Owning Feature | Current Owner | Last Updated | Work Log | Reconciliation |
|---|---|---|---|---|---|---|---|
| #4 | issue_backed | done | none | phase-1b-3-reviewer | 2026-07-13T09:32:29+09:00 | [Phase 1B command gateway](issue-4/README.md) | complete |
| #5 | issue_backed | done | none | orchestrator | 2026-07-13T09:32:29+09:00 | [Phase 2A context intake and cache control](issue-5/README.md) | complete |
| #6 | issue_backed | done | none | orchestrator | 2026-07-13T09:32:29+09:00 | [Phase 2B skills and handoff reuse](issue-6/README.md) | complete |
| #7 | issue_backed | done | none | implementation-agent | 2026-07-13T09:32:29+09:00 | [Phase 2C verification and document gates](issue-7/README.md) | complete |
| #8 | issue_backed | done | none | orchestrator | 2026-07-13T09:32:29+09:00 | [subagent workflow](issue-8/README.md) | complete |
| #10 | issue_backed | done | none | reviewer | 2026-07-13T22:21:36+09:00 | [Phase 3A native runtime adapters](issue-10/README.md) | reconciliation complete; Issue closed |
| [#12](https://github.com/116Lv/sparta-ch6-advanced/issues/12) | issue_backed | done | none | main-agent | 2026-07-20T14:05:00+09:00 | [Phase 3B CI gates and durable evidence](issue-12/README.md) | reconciliation complete; Issue closed |
| #14 | issue_backed | done | none | orchestrator | 2026-07-14T18:15:29+09:00 | [AI workflow trust-boundary hardening](issue-14/README.md) | reconciliation complete; Issue closed; PR #15 CI follow-up green |
| [#20](https://github.com/116Lv/sparta-ch6-advanced/issues/20) | issue_backed | done | none | repository-owner | 2026-07-20T14:05:00+09:00 | [Level 5 runtime verification](issue-20/README.md) | Implementation QA and refreshed CI PASS; Issue closed |
| [#22](https://github.com/116Lv/sparta-ch6-advanced/issues/22) | issue_backed | done | none | orchestrator | 2026-07-20T13:53:27+09:00 | [과제 제출 문서 한글화](issue-22/README.md) | 구현·검수 PASS; gh CLI reconciliation complete, Issue closed |
