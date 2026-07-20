# AI 워크플로 리소스 예산

## 사람용 정책 참고 사항

이 파일은 저장소 탐색과 cache 재사용을 위한 Phase 2A 기본 예산을 정의한다. 구조화된 cache record가 있는 경우 JSON이 canonical이다. Markdown은 실행 가능한 상태로 파싱하지 않는다.

제품 명령은 계속 NOT RUN이다. Phase 2A는 검증 완전성을 평가하지 않는다.

## 기본 예산

| 활동 | 기본 한도 | 예외 기록 |
|---|---:|---|
| context map 사용 전 task당 광범위 저장소 검색 | 2 | route와 cache된 context가 불충분했던 이유 기록 |
| task당 전체 트리 파일 목록 | 1 | stale 또는 누락된 context-map 사유 기록 |
| 변경되지 않은 policy file 재읽기 | task phase별 file당 1 | digest 또는 route 변경 기록 |
| command capability 재탐색 | intake invalidation이 적용되지 않는 한 0 | 영향받은 registry ID 기록 |
| 같은 사실에 대한 external tool call | 1 | 이전 evidence가 stale 또는 결론 불충분했던 이유 기록 |

예산은 선택된 route phase별로 적용된다. 선언된 trigger 후 deferred document를 읽는 것은 필수 작업이며 예산 예외가 아니다. deferred path로 확장하려면 일치하는 opt-in trigger가 필요하다. excluded path로 확장하는 것은 예산 적용이 아니라 금지다.

## Phase 2A 경계

저장소 script는 Phase 3 이전에 모든 host file read, search, external tool call을 가로챌 수 없다. 이 예산은 Phase 2A에서 policy, work log, cache record, review gate를 통해 강제된다.

## 예외

예외는 추가 탐색이 필요했던 route ID, changed input, stale cache entry 또는 blocker를 명시해야 한다. 이는 제품 명령 실행을 허가하지 않는다.
