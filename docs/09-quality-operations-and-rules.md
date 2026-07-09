# 09. Quality, Operations, and Rules

## Testing Strategy

Testing rules are also governed by `ai/verification-levels.md` and `ai/qa-gate.md`.

### Unit Test

Write unit tests for:

- domain rules
- point balance validation
- order creation rules
- request validation helpers
- ranking policy

### Integration Test

Write integration tests for:

- repository behavior
- MySQL transaction behavior
- API controller behavior
- Outbox event persistence
- Redis ranking update

### Real API Verification

Any API behavior change requires real HTTP request verification against a running server unless blocked by missing project setup. If blocked, report `BLOCKED` with the reason.

### Concurrency Test

Write concurrency tests for:

- same user multiple orders
- same user charge and order at the same time
- lock timeout behavior

## Security Rules

- Do not log secrets, tokens, passwords, or sensitive personal data.
- Validate all user input on the server.
- Do not trust userId from request in real production auth contexts without principal verification.
- Do not expose stack traces in API responses.

## Logging Rules

- Log important business events with structured fields.
- Log order/payment failure reasons.
- Log Outbox publish failures and retry counts.
- Log unexpected exceptions.
- Do not log full sensitive payloads.

## Release Rules

TODO: Confirm actual branch and release workflow after repository setup.

Suggested rules:

- Do not merge without QA Gate evidence.
- PR description should include changed requirements and verification evidence.
- Breaking changes require documentation update.

## Migration Rules

- DB migration must be reviewed before deployment.
- Migration rollback or mitigation plan must be documented.
- API changes that depend on migration must state deployment order.

## Definition of Done

A feature is done only when:

1. Relevant spec acceptance criteria are satisfied.
2. Required verification level is met.
3. Tests were actually run or explicitly reported as not run.
4. API changes have real API verification evidence when applicable.
5. Unexpected 500 responses were checked.
6. Server logs were reviewed when real server verification was required.
7. Docs/specs/adr were updated if behavior changed.
8. Done claim follows `ai/done-claim-template.md`.

## Open Questions

- Open Question: What exact Gradle tasks should be used for integration and real API verification beyond `test`?
- Open Question: Will Testcontainers be required for MySQL, Redis, and Kafka integration tests?
