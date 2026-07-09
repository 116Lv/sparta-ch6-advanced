# LazyCodex Runbook

## Purpose

AI가 게으르게 작업하거나 검증을 회피할 때 강제할 운영 매뉴얼이다.

## Warning Signs

- "아마 될 것입니다"라고 말한다.
- 테스트를 실행하지 않았는데 완료 분위기로 답한다.
- 실패 로그를 요약하지 않는다.
- 실제 API 검증 없이 controller 구현만 보고 완료한다.
- 문서 업데이트 필요 여부를 확인하지 않는다.
- Open Question을 임의로 결정한다.

## Required Correction

이런 징후가 보이면 다음을 요구한다.

1. 실행한 명령어 목록을 제시한다.
2. 실행하지 않은 명령어는 `NOT RUN`으로 표시한다.
3. 실패한 명령은 실패 원인을 요약한다.
4. API 변경이면 실제 request/response 증거를 제시한다.
5. 문서 업데이트 여부를 다시 확인한다.
6. Done Claim Template으로 다시 보고한다.

## Refusal Rule

AI가 검증 없이 완료를 주장하면 reviewer는 완료를 반려한다.

허용되는 상태:

- PASS
- FAIL
- BLOCKED
- PARTIAL

허용되지 않는 상태:

- "거의 완료"
- "테스트는 안 했지만 괜찮음"
- "코드상 문제 없어 보임"

