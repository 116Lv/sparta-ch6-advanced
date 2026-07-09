# Implementation Guardrails

## Architecture Guardrails

- 문서에 정의된 레이어 구조를 따른다.
- Controller/API route에 비즈니스 로직을 몰아넣지 않는다.
- UI 컴포넌트에 비즈니스 규칙을 직접 넣지 않는다.
- domain layer는 framework에 의존하지 않는다.
- project-wide decision은 ADR 없이 바꾸지 않는다.

## Error Handling Guardrails

- 예외를 catch하고 무시하지 않는다.
- 예상 가능한 에러는 명시적 에러 코드로 반환한다.
- 예상하지 못한 500은 실패로 본다.
- 에러 응답 포맷은 `docs/07-data-and-api-contracts.md#error-format`을 따른다.
- validation 실패가 500으로 터지면 완료가 아니다.

## Testing Guardrails

- mock 테스트만으로 API 검증을 완료했다고 주장하지 않는다.
- 권한/인증/validation 실패 케이스를 포함한다.
- 테스트를 통과시키기 위해 요구사항을 바꾸지 않는다.
- 결제/포인트/주문 로직은 동시성 테스트를 포함한다.

## Code Quality Guardrails

- `any`로 타입 에러를 덮지 않는다.
- 사용하지 않는 코드를 남기지 않는다.
- 의미 없는 주석을 남기지 않는다.
- 임시 fallback을 production 코드처럼 남기지 않는다.
- `console.log` 또는 임시 debug log를 남기지 않는다.
- TODO를 남길 경우 이유와 후속 작업을 문서화한다.

## Data Consistency Guardrails

- MySQL 기준 데이터와 Redis/Kafka 보조 데이터를 혼동하지 않는다.
- 주문/결제와 Outbox 저장의 트랜잭션 경계를 깨지 않는다.
- 포인트 잔액 변경은 사용자 단위 동시성 제어를 적용한다.

