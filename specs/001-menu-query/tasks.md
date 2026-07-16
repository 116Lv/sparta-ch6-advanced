# Tasks: Menu Query

## 2026-07-15 Static Audit Tracking

- [x] Menu domain, persistence, service, API, and focused contract tests inspected/authored.
- [ ] Product tests and real HTTP verification run through a supported VERIFIED command.

## Phase 1: Design Check

- [ ] `docs/05-functional-requirements.md`의 FR-001 확인
- [ ] `docs/03-domain-model.md`의 Menu 규칙 확인
- [ ] API 응답 필드 확인

## Phase 2: Domain

- [ ] `Menu` 엔티티 구현
- [ ] `MenuStatus` enum 구현
- [ ] 판매 가능 상태 판단 규칙 구현

## Phase 3: Application and Persistence

- [ ] `MenuRepository` 구현
- [ ] `MenuQueryService` 구현
- [ ] 메뉴 조회 integration test 작성

## Phase 4: API

- [ ] `MenuController` 구현
- [ ] `MenuResponse` 구현
- [ ] 빈 목록 응답 테스트 작성

## Phase 5: Verification

- [ ] 전체 테스트 실행
- [ ] checklist 갱신
- [ ] decisions 갱신
