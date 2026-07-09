# Reviewer Checklist

## Requirements Review

- [ ] 변경이 관련 spec의 acceptance criteria를 만족한다.
- [ ] 요구사항을 임의로 축소하거나 바꾸지 않았다.
- [ ] Open Questions가 무시되지 않았다.

## Architecture Review

- [ ] `docs/06-system-architecture.md`의 레이어 규칙을 따른다.
- [ ] 비즈니스 로직이 controller에 몰려 있지 않다.
- [ ] domain이 framework에 과하게 의존하지 않는다.
- [ ] project-wide decision이 ADR에 기록되어 있다.

## Data and API Review

- [ ] API response가 `docs/07-data-and-api-contracts.md`와 일치한다.
- [ ] error format이 일관된다.
- [ ] DB constraint와 transaction boundary가 적절하다.
- [ ] Redis/Kafka와 MySQL source of truth가 혼동되지 않았다.

## Verification Review

- [ ] required verification level을 충족했다.
- [ ] 테스트 명령과 결과가 있다.
- [ ] API 변경 시 실제 HTTP request 증거가 있다.
- [ ] 예상하지 못한 500이 없다.
- [ ] 서버 로그 확인 결과가 있다.

## Documentation Review

- [ ] docs/specs/adr가 필요한 만큼 업데이트되었다.
- [ ] Done Claim이 `ai/done-claim-template.md`를 따른다.
- [ ] 남은 리스크가 명시되어 있다.

