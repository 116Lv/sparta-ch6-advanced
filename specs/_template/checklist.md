# Checklist: [Feature Name]

## Spec Quality

- [ ] 요구사항이 명확하다.
- [ ] acceptance criteria가 있다.
- [ ] out of scope가 명시되어 있다.
- [ ] 권한 조건이 명시되어 있다.
- [ ] edge case가 정리되어 있다.

## Implementation Quality

- [ ] architecture 문서의 레이어 규칙을 지켰다.
- [ ] domain rule이 UI에 직접 들어가지 않았다.
- [ ] API 에러 형식이 일관된다.
- [ ] database constraint가 반영되었다.
- [ ] permission check가 server-side에 있다.

## Verification Quality

- [ ] 필요한 verification level을 충족했다.
- [ ] typecheck를 실행했다.
- [ ] lint를 실행했다.
- [ ] unit/integration test를 실행했다.
- [ ] API 변경 시 실제 HTTP request를 실행했다.
- [ ] 예상하지 못한 500이 없었다.
- [ ] 서버 로그를 확인했다.

## Release Quality

- [ ] migration 위험이 검토되었다.
- [ ] rollback 방법이 있다.
- [ ] 문서가 업데이트되었다.

# Phase 2C Verification Gate

- [ ] `ai/verification-gates.md`, `ai/verification-policy.json`, and `scripts/ai/verification-gate.sh` are linked in the final verification evidence.
- [ ] Verification completeness and task/change applicability are recorded for the selected change type.
- [ ] `NOT_CONFIGURED`, `NOT_APPLICABLE`, `BLOCKED`, and `FAIL` mapping is recorded.
- [ ] Product commands remain NOT RUN unless supported evidence exists.
