# AI Workflow Tool-Call Policy

## 사람용 정책 참고 사항

이 정책은 광범위한 검색, 반복 읽기, 명령 재탐색, 중복 외부 도구 호출을 제한한다. 구조화된 cache 또는 컨텍스트 레코드가 있으면 JSON이 기준 문서다. Markdown은 실행 가능한 상태로 파싱하지 않는다.

이후 승인된 gateway 실행이 명시적으로 허용하지 않는 한 제품 명령은 NOT RUN으로 유지한다. Phase 2A는 검증 완전성을 평가하지 않는다.

## 저장소 전용 경계

저장소 script는 Phase 3 이전에 모든 host 파일 읽기, 검색, 외부 도구 호출을 intercept할 수 없다. Phase 2A는 정책, cache key, 검토 증거를 기록할 수 있지만 모든 직접 shell, editor, MCP, browser, host-runtime 동작을 막을 수는 없다.

Phase 3A는 현재 host를 네이티브 `COMMAND`, `FILE_READ`, `SEARCH`, `TOOL_CALL` interception에 대해 `UNSUPPORTED`로 선언한다. 내부 네이티브 adapter 검사는 그 상태를 `HOST_UNSUPPORTED`와 함께 `NOT_APPLICABLE`로 Phase 2C에 보고한다. 이는 저장소 정책을 host 전체 강제 적용으로 바꾸지 않는다.

## 제한

- 광범위한 tree scan보다 `rg` 또는 대상 파일 읽기를 우선한다.
- 문서 경로를 재탐색하기 전에 현재 route와 handoff를 재사용한다. route 선택, phase 확장, cache 최신성 또는 워크플로 재탐색이 실제 범위에 있을 때만 `ai/context-map.json`과 정책을 불러온다.
- 선택된 phase의 typed `includePaths` scope를 일반 검색에 적용한다. 읽는 모든 문서는 include scope에 포함되어야 하며 deferred 상태로 남아서는 안 된다. `deferredPaths` 영역은 일치하는 typed `optInPaths` trigger가 handoff `activatedTriggers`에 기록된 후에만 검색하고, 실제로 선택한 정확한 path만 materialize한다. READY와 PARTIAL은 그 정확한 path를 `readDocuments`에 기록한다. Work-log 접근에는 null이 아닌 `activeIssue`도 필요하다. 이를 정확한 summary와 나열된 role ref로 좁히고 READY 또는 PARTIAL에서는 해당 ref를 읽으며, reusable, foreign, unlisted, subtree, direct-children, descendant 또는 excluded scope를 통해 넓히지 않는다.
- 기준 `excludedPaths`를 검색하거나 opt-in하지 않는다.
- stack, port, 명령, 검증 capability를 재탐색하기 전에 `ai/project-state.json`, `ai/command-registry.json`을 재사용한다.
- cache 항목이 `STALE`, `UNCERTAIN`, 누락 또는 변경 입력에 매핑되었으면 재탐색이 필요했던 이유를 기록한다.
- 사람 수동 명령 결과를 AI 워크플로 검증 증거로 취급하지 않는다.

## 완료에 미치는 영향

감지된 우회와 설명되지 않은 반복 탐색은 이후 검토 또는 완료 주장을 차단할 수 있다. Phase 2A 자체는 host 전체 강제 적용을 주장하지 않는다.

`scripts/ai/command-runner.sh`는 유일하게 지원되는 product-command 경로다. Native adapter는 host 작업을 관찰·분류·차단할 수 있지만 product command를 실행하지 않으며, 검증은 사전 계산된 adapter 결과를 수락하지 않는다. Supported-host adapter fault는 완료 차단으로 유지한다. CI 설치, remote-runner 보장, 내구성 native 증거, cross-host parity는 Phase 3B로 미룬다.
