# AI 워크플로 강제 적용 Phase 1B 문서화 명세

## 상태

- 명세 상태: 승인된 구현 기준선, 2026-07-10에 독립 재검토 PASS
- 소유 기능: none
- 기준선: `docs/superpowers/specs/2026-07-10-ai-workflow-enforcement-design.md`
- 상태 계약: `docs/superpowers/specs/2026-07-10-ai-workflow-phase-1a-spec.md`
- 범위: Phase 1B-1, Phase 1B-2 및 Phase 1B-3만
- 첫 구현 slice: Phase 1B-1

## 목표

schema에 유효한 registry ID만 해석하고, shell 해석 없이 argv를 구성하며, 구조화된 증거를 기록하고, 지원되지 않는 완료 주장을 차단하는 지원 명령 경로를 구현한다. Phase 1B는 저장소 gateway 강제 적용이다. 직접 호스트 shell, MCP, file-read 또는 다른 외부 도구 호출을 가로챈다고 주장하지 않는다.

## 확정된 결정

1. 정식 JSON은 기준 문서로 유지한다. Markdown은 사람 정책과 생성 요약으로 유지한다.
2. helper runtime 대상은 Python 3이다. validator는 `Draft202012Validator` 및 `FormatChecker`를 사용하는 Python `jsonschema`이다.
3. 유일한 schemaVersion 1 실행 profile은 `./gradlew`로 시작한다. 네이티브 `gradlew.bat` 및 다른 실행 profile은 계속 지원하지 않는다.
4. 명령은 `shell=False` 상태에서 argv 배열로 실행한다. `eval`, 명령 문자열, shell interpolation, shell expansion 또는 검사되지 않은 token 추가는 허용하지 않는다.
5. Bash 파일은 얇은 사람 대상 진입점이다. JSON 파싱, schema 및 의미 검증, hashing, 원자적 쓰기, 구조화된 process 실행, redaction 및 증거 생성은 Python이 담당한다.
6. 지원되는 gateway 호출마다 runtime preflight가 필요하다. cache된 project-state 주장은 실패한 현재 preflight를 절대 재정의하지 않는다.
7. 승인 JSON은 감사 기록일 뿐이다. 로컬에서 만든 기록은 권한을 만들 수 없다.
8. Phase 1B는 파괴적, production, deployment, secret 변경, migration, seed 또는 대량 mutation 명령을 절대 실행하지 않는다.
9. 실행별 원시 증거는 `.ai-runs/<run-id>/` 아래 로컬에 있고 Git이 무시한다. 영속적인 요약은 반드시 정제해야 한다.
10. 완성된 `command-runner.sh` supported path 외에는 제품 명령을 AI 에이전트가 사용할 수 없다.
11. Phase 1B에는 신뢰할 수 있는 host approval adapter가 없으므로 모든 `RISKY` 및 `DESTRUCTIVE` 명령을 차단한다. 승인 파일은 실행을 절대 해제하지 않는다.
12. 초기 runtime capability probe는 좁은 bootstrap 예외다. 정식 runtime 확인 전에는 runtime ID 및 validator capability만 보고할 수 있으며 command registry를 읽거나 제품 명령을 계획/실행할 수 없다.

## 단계 경계

### Phase 1B-1: registry 해석 및 매개변수 검증

helper-runtime preflight, schema 검증, registry 의미 검증, ID lookup, 폐쇄형 parameter 검증, whole-token placeholder 치환, classification 검사 및 prerequisite 검사를 구현한다. 이 slice는 해석된 프로젝트 argv를 실행해서는 안 된다.

### Phase 1B-2: 명령 실행 및 증거

command runner 및 workflow gate를 추가하고, 이미 승인된 resolution을 `shell=False`로 실행하며, 정제된 로그를 수집하고, schema에 유효한 실행별 증거를 영속화하며, 정책 및 승인 감사 이벤트를 기록한다.

### Phase 1B-3: 완료 게이트 및 계약 테스트

done-claim gate, leaf-result aggregation, stale-summary 검사 및 모든 fail-closed 동작에 대한 계약 test를 추가한다.

## 파일 계약

### Phase 1B-1 Files

| 경로 | 책임 |
|---|---|
| `scripts/ai/runtime-preflight.sh` | 승인된 Python 3 후보를 찾고 shell 평가 없이 helper preflight를 호출하는 얇은 POSIX 진입점 |
| `scripts/ai/run-helper-tests.sh` | 같은 고정 runtime 후보 정책을 사용하고 승인된 helper unittest module만 실행하는 인수 없는 test launcher |
| `scripts/ai/workflow_helper.py` | preflight, Draft 2020-12 검증, 의미 registry 검증 및 command resolution용 Python helper |
| `scripts/ai/tests/test_workflow_helper.py` | Phase 1B-1 동작을 위한 Python 표준 라이브러리 test |
| `ai/fixtures/phase-1b/` | runtime, registry, parameter, classification 및 prerequisite 계약 fixture |
| `ai/schemas/gateway-result.schema.json` | 구조화된 preflight, resolution 및 후속 leaf-gate 제어 결과 |
| `ai/schemas/helper-runtime-evidence.schema.json` | 영속적인 정제 LOCAL helper-runtime capability 증거 |
| `ai/evidence/local-helper-runtime.json` | 현재 환경 로컬의 정제된 preflight 증거. 실행 파일 경로, hostname 또는 secret 데이터 없음 |
| `ai/project-state.json` and `ai/project-state.md` | 성공적 preflight 기록 후 원자적인 LOCAL runtime 상태 및 generated-summary 전이 |
| `.gitignore` | 일시적인 `ai/.workflow-state-txn/` 복구 상태 무시 |

### Phase 1B-2 Files

| Path | Responsibility |
|---|---|
| `scripts/ai/command-runner.sh` | 지원 명령 진입점: `run <command-id>` 및 구조화된 옵션 |
| `scripts/ai/workflow-gate.sh` | PRE_COMMAND 및 POST_COMMAND leaf gate |
| `scripts/ai/workflow_helper.py` | 구조화된 실행, hashing, redaction, 원자적 증거 쓰기 및 run-index 갱신 |
| `ai/schemas/run-session.schema.json` | 정확한 CAS run 제어 상태 및 보존된 finalized projection receipt |
| `ai/schemas/process-attempt.schema.json` | redaction-failure 실행 결과를 포함하는 secret-free child-attempt 사실 |
| `ai/schemas/artifact-manifest.schema.json` | SHA-256 digest 및 크기를 포함한 정확한 불변 artifact closure |

### Phase 1B-3 Files

| Path | Responsibility |
|---|---|
| `scripts/ai/done-claim-check.sh` | PRE_DONE_CLAIM final gate |
| `scripts/ai/tests/run-contract-tests.sh` | helper 및 shell contract test를 위한 얇은 test 진입점 |
| `scripts/ai/tests/test_workflow_helper.py` | fixture 및 final aggregation test |

Phase 1B는 제품 source, 제품 test, Gradle configuration, 애플리케이션 configuration, migration, seed, Docker, API 또는 database 파일을 수정하지 않는다.

## 공통 종료 계약

| 종료 | 구조화된 결과 | 의미 |
|---:|---|---|
| 0 | `PASS` | 요청된 supported-path 작업이 완료됨 |
| 1 | `FAIL` | child process가 실행되어 0이 아닌 값을 반환했거나 실행된 gate가 실패함 |
| 2 | `BLOCKED` | 정책상 현재 충족되지 않는 증거나 권한이 필요함 |
| 3 | `NOT_CONFIGURED` | 필요한 runtime 또는 capability를 사용할 수 없음 |
| 4 | `POLICY_VIOLATION` | 호출자 요청이 유효한 폐쇄형 정책을 위반함 |
| 5 | `INVALID_STATE` | 정식 JSON, schema, 의미 계약 또는 증거 graph가 잘못됨 |
| 6 | `NOT_APPLICABLE` | leaf 검사가 분류된 작업과 무관함 |
| 7 | `SKIPPED_WITH_REASON` | 정책이 문서화된 skip을 명시적으로 허용함 |

child process exit code는 `processExitCode`로만 저장한다. 0이 아닌 child exit는 워크플로 `FAIL` 및 script exit `1`에 매핑된다.

## helper runtime 사전 점검

### 후보 선택

`runtime-preflight.sh`는 `PATH`에서 고정 command-name allowlist `python3`, 그다음 `python`을 probe한다. `python` 후보는 helper가 major version 3임을 증명한 후에만 허용한다. `py`, Node.js, Java, `jq` 또는 환경에서 선택한 실행 파일은 사용하지 않는다. 다른 실행 파일 경로에는 미래에 승인된 configuration field가 필요하다.

스크립트는 literal allowlist 이름 및 인용된 argv 호출과 함께 `command -v`를 사용한다. `eval`, `sh -c`, command string, alias, 환경에서 선택한 실행 파일 또는 동적 인수 결합은 사용하지 않는다. helper가 Python major version 3을 확인하고 `Draft202012Validator` 및 `FormatChecker` import에 성공한 경우에만 후보를 허용한다.

### 사전 점검 결과

성공한 preflight는 `operation: PREFLIGHT`, `result: PASS`, `reason: null`, 비어 있는 `errors` 배열 및 다음 `data`를 포함하는 하나의 gateway-result envelope를 출력한다.

- `runtimeCommand`: 선택된 allowlist 명령 이름, `python3` 또는 `python`;
- `runtimeExecutableHash`: 경로를 기록하지 않는 선택 interpreter file의 SHA-256;
- `pythonVersion`: 전체 Python 버전;
- `jsonschemaVersion`: 설치된 library 버전;
- `validator`: 정확히 `Draft202012Validator`;
- `formatChecker`: 정확히 `true`.

Python 3 누락, `jsonschema` 누락, 지원하지 않는 major version 또는 import 실패는 `NOT_CONFIGURED` 및 exit `3`을 반환한다. ad hoc parsing으로 fallback하지 않는다.

Python 또는 `jsonschema`를 사용할 수 없으면 schema 검증은 불가능하다. 이는 모든 script 결과가 schema 검증된다는 규칙의 유일한 bootstrap-output 예외다. shell 진입점은 `operation: PREFLIGHT`, `result: NOT_CONFIGURED`, `reason: helper runtime unavailable`, 비어 있는 `errors` 및 `data: null`을 갖는 고정 최소 JSON 객체를 출력한 뒤 `3`으로 종료한다. 호출자가 제어하는 텍스트는 포함하지 않는다. preflight가 성공하면 helper는 전체 결과를 `gateway-result.schema.json`으로 검증한다.

### gateway 결과 스키마

`gateway-result.schema.json`은 허용된 모든 operation/result 쌍에 대한 정확한 `oneOf` branch 및 다음 공통 field를 갖는 폐쇄형 Draft 2020-12 schema다.

- `$schema`, `$id` 및 `schemaVersion: 1`;
- `operation`: `PREFLIGHT`, `RESOLVE`, `RUN_START`, `PRE_COMMAND`, `POST_COMMAND` 또는 `PRE_DONE_CLAIM`;
- `result`: Script Control Outcome enum;
- `reason`: PASS일 때만 null이고, 그 외에는 비어 있지 않은 string;
- `errors`: 안정된 `code`, JSON `instancePath`, `schemaPath` 및 정제된 `message`를 포함하는 결정적인 폐쇄형 object;
- `data`: PASS용 operation별 폐쇄형 object, RESOLVE/BLOCKED용 변경되지 않은 폐쇄형 prerequisite 전용 object, POST_COMMAND/FAIL 및 POST_COMMAND/BLOCKED용 정확한 폐쇄형 POST object 또는 RUN_START와 PRE_COMMAND의 non-PASS branch 및 POST_COMMAND/NOT_CONFIGURED, POST_COMMAND/POLICY_VIOLATION, POST_COMMAND/INVALID_STATE용 `null`.

PREFLIGHT PASS data는 위에 나열한 정확한 중첩 형태를 사용한다. RESOLVE PASS data에는 command ID, classification, 저장소 상대 작업 디렉터리, 최종 argv 배열 및 결정적인 prerequisite ID가 있다. 비어 있지 않은 prerequisite로 인한 RESOLVE/BLOCKED에는 `data: { "prerequisiteIds": [...] }`가 있고 argv나 작업 디렉터리는 포함하지 않는다. 이 예외는 변경되지 않는다. RUN_START, PRE_COMMAND, POST_COMMAND 및 PRE_DONE_CLAIM branch는 해당 구현 phase에서만 추가하고 폐쇄형 operation별 data를 정의한다. RUN_START는 구조화된 시작 결과 게시에 필요한 유일한 추가 Phase 1B-2 operation이다. RUN_START/PASS data에는 정확히 `runId`, `taskKey`, `sessionRef`가 있고, 모든 non-PASS RUN_START branch는 `data: null`이며 공통 exit 계약을 사용한다. PRE_COMMAND non-PASS data는 null이다. POST_COMMAND/FAIL 및 POST_COMMAND/BLOCKED는 Phase 1B-2 outcome matrix가 정의한 정확한 폐쇄형 POST data object를 사용한다. POST_COMMAND/NOT_CONFIGURED, POST_COMMAND/POLICY_VIOLATION 및 POST_COMMAND/INVALID_STATE는 `data: null`을 사용한다. 이 추가는 기존 operation 의미를 바꾸지 않고 이전에 빠진 구조화 시작 결과를 보완한다. lock recovery는 gateway operation이 아니다. non-PASS 결과에는 실행 가능한 argv가 없다. helper는 게시 전에 결과를 검증하고 재구성된 shell string을 절대 출력하지 않는다.

### 정식 runtime 상태

bootstrap probe는 자체 runtime/version/import capability만 검사할 수 있다. 성공한 probe 후 Phase 1B-1은 정제된 환경 로컬 capability 사실이 있는 `ai/evidence/local-helper-runtime.json`을 쓰고, 이를 `helper-runtime-evidence.schema.json`으로 검증한 후 `ai/project-state.json`의 LOCAL helper-runtime 항목과 일치하는 LOCAL 환경 참고를 원자적으로 갱신한다. 상위 설계의 "state CONFIRMED" 표현은 null이 아닌 runtime/version과 영속적인 정제 증거 파일을 가리키는 `RUNTIME_COMMAND` 증거를 갖는 schema 구성 상태 `VERIFIED`에 매핑된다. CI는 `NOT_CONFIGURED`로 유지된다.

증거 파일은 allowlist 명령 이름 및 interpreter SHA-256은 기록하지만 절대 실행 파일 경로, hostname, username, 환경 값 또는 secret은 기록하지 않는다. 이는 명시적으로 환경 로컬이다. 모든 gateway 호출은 preflight를 다시 실행한다. 증거 누락, 일치하지 않는 executable hash/runtime/version/capability 보고 또는 실패한 현재 probe는 해당 호출의 cache된 runtime 상태를 `STALE`로 만들고 child 실행을 차단한다. 여러 머신의 consumer는 이 파일만으로 현재 가용성을 절대 판단하지 않는다. 동일한 현재 보고서는 읽기 전용이고 timestamp, 증거, 정식 JSON 또는 Markdown을 다시 쓰지 않는다.

증거, 정식 JSON 및 generated-summary 갱신은 같은 디렉터리의 임시 파일, 지원되는 경우 fsync 및 교체 전 검증을 사용한다. 세 파일은 하나의 작업으로 원자적 rename할 수 없으므로 helper는 이전 digest, backup 경로, 의도한 새 digest 및 transaction stage를 포함하는 lock된 `ai/.workflow-state-txn/` journal을 사용한다. 모든 preflight는 정식 상태를 읽기 전에 중단된 transaction을 먼저 복구하거나 rollback한다. 성공하면 journal과 backup을 삭제한다. 쓰기 또는 검증 실패는 모든 이전 파일을 복원하고 `INVALID_STATE`를 보고한다. 동기화를 주장하지 않는다. Python 또는 `jsonschema`가 없으면 정식 LOCAL 상태를 변경하지 않고 `NOT_CONFIGURED`를 반환한다.

## 스키마 검증

1. schema와 instance를 중복 key 탐지와 함께 UTF-8 JSON으로 load한다. 일반 JSON parser가 마지막 값을 유지하더라도 중복 object key는 `INVALID_STATE`이다.
2. `NaN`, `Infinity`, `-Infinity` 같은 JSON 이외의 numeric constant를 거부한다.
3. schema `$schema`가 Draft 2020-12이고 schema `$id`가 파일에 저장된 승인된 project URN과 일치하도록 요구한다.
4. 내부 저장소 상대 allowlist에서 schema를 선택한다. instance 제어 경로 또는 URI가 임의 schema 읽기나 네트워크 resolution을 일으키지 않는다.
5. instance 검증 전에 `Draft202012Validator.check_schema`를 실행한다.
6. `Draft202012Validator` 및 `FormatChecker`로 검증한다.
7. JSON path 및 schema path로 검증 오류를 결정적으로 정렬한다. 사람이 읽는 stderr는 이를 요약할 수 있으나 구조화된 JSON 결과가 정식이다.
8. 지원하지 않는 `schemaVersion` 및 알 수 없는 instance `$schema` 값을 `INVALID_STATE`로 거부한다.
9. 모든 저장소 상대 경로를 저장소 root에 대해 resolve하고, 이미 존재해야 하는 파일의 symlink escape를 포함해 정규화 후 escape를 거부한다.

네트워크 schema fetch는 허용하지 않는다.

## registry 의미 검증

schema에 유효한 registry JSON도 구조적 의미 규칙을 위반하면 `INVALID_STATE`이다. 아래 명시적인 missing-wrapper stale-configuration 규칙은 유일한 `BLOCKED` 예외다.

1. Command ID는 전역적으로 고유하다.
2. null이 아닌 모든 argv는 정확히 `./gradlew`로 시작한다.
3. 실행 가능한 명령은 `CONFIGURED_UNVERIFIED` 또는 `VERIFIED`를 사용하고 `UNAVAILABLE`이 아니며 schema가 요구하는 정적 또는 runtime 증거가 있다.
4. 실행 불가능한 상태는 `argv: null`, classification `UNAVAILABLE`을 가지며 실행을 위해 해석할 수 없다.
5. parameter schema의 `required` 이름은 `properties` key와 정확히 같다.
6. parameter pattern은 `^`와 `$`로 anchor하고 성공적으로 compile하며 schemaVersion 1 safe-regex subset, 즉 character class, escaped literal, plain literal, `.`, 선형 quantifier `?`, `*`, `+`를 사용한다. 괄호, alternation, counted quantifier, backreference, lookaround, inline flag, conditional 및 nested quantification은 거부한다.
7. `{` 또는 `}`가 있는 모든 argv token은 정확히 `{{parameterName}}`에 일치하는 whole-token placeholder다.
8. parameter가 비활성화되면 placeholder는 금지된다.
9. parameter가 활성화되면 고유 placeholder 이름은 parameter-schema property 이름과 정확히 같다. 같은 선언된 whole-token placeholder의 반복은 허용된다.
10. 모든 prerequisite ID는 존재하고 소유 command ID와 다르며 directed prerequisite graph는 acyclic이다.
11. prerequisite에는 결정적인 topological order가 있다.
12. 구성된 모든 실행 가능 working directory는 존재하고 repository root 내부로 resolve되며 directory다.
13. 구성된 `./gradlew` 경로는 존재하고 저장소 내부로 resolve되며 directory가 아니다. 이전 정적 증거 후 경로가 없으면 stale configuration으로 `BLOCKED`이고, symlink escape는 `INVALID_STATE`다.
14. 실행 profile은 parsing 후 의미적으로 다시 검사한다. schema 검증만으로 실행 allowlist로 취급하지 않는다.

## 해석 인터페이스

내부 helper 인터페이스는 다음과 같다.

```text
workflow_helper.py resolve
  --repository-root <absolute-path>
  --registry ai/command-registry.json
  --command-id <registry-id>
  [--parameters-file <repository-relative-json-path>]
  --output <path-or-stdout-marker>
```

미래의 public shell 진입점은 다음과 같다.

```text
scripts/ai/command-runner.sh run <command-id>
  [--parameters-file <repository-relative-json-path>]
  [--run-id <identifier>]
  [--rerun-reason-file <repository-relative-text-path>]
  [--approval-ref <repository-relative-json-path>]
```

inline JSON, `key=value` 추가, 여분의 trailing argv 및 원시 command string은 거부한다.

`resolve`는 discovery/planning 작업이다. 잘 구성되었으나 없는 ID는 `NOT_CONFIGURED`를 반환하고 이벤트를 만들지 않는다. Phase 1B-2는 실행 의도를 위한 별도의 `pre-command` helper 작업을 추가한다. 없는 ID는 `POLICY_VIOLATION`을 반환한다. active run이 있으면 `UNREGISTERED_COMMAND`를 추가하고, active run이 없으면 이벤트가 영속화되었다고 가장하지 않고 같은 구조화된 위반을 반환한다.

### 해석 순서

resolution은 다음 검사를 순서대로 수행하고 첫 결과에서 멈춘다.

1. 현재 helper preflight;
2. 정식 project-state 및 command-registry schema 검증;
3. registry 의미 검증;
4. 정확한 command-ID lookup;
5. command configuration 상태 및 classification;
6. 폐쇄형 parameter-file parsing 및 검증;
7. whole-token placeholder 치환;
8. prerequisite graph 검증 및 순서 지정;
9. prerequisite가 비어 있지 않으면 Phase 1B-1은 아직 active-run 증거를 허용하지 않으므로 `BLOCKED` 반환;
10. 최종 argv 및 working-directory containment 검사;
11. 구조화된 resolution 출력.

Phase 1B-1 resolver는 child project process를 생성하지 않는다.

## 실행 전 결과 매핑

| 조건 | 결과 |
|---|---|
| Python 3 또는 `jsonschema`를 사용할 수 없음 | `NOT_CONFIGURED` |
| 정식 JSON parse, schema, format, duplicate-key 또는 의미 오류 | `INVALID_STATE` |
| discovery/resolution 중 잘 구성되었으나 없는 command ID | `NOT_CONFIGURED` |
| Phase 1B-2 실행 진입점에 제출된 없는 command ID | `POLICY_VIOLATION` 및 `UNREGISTERED_COMMAND` 이벤트 |
| Command 상태 `NOT_CONFIGURED` | `NOT_CONFIGURED` |
| Command 상태 `UNKNOWN`, `STALE` 또는 `UNCERTAIN` | `BLOCKED` |
| Classification `UNAVAILABLE` | `NOT_CONFIGURED` |
| Classification `SAFE` | 계속 |
| 호출자가 작성한 승인 기록의 유무와 관계없는 classification `RISKY` | `BLOCKED` |
| Classification `DESTRUCTIVE` | Phase 1B에서는 `BLOCKED`, 실행 시도에는 `DESTRUCTIVE_WITHOUT_APPROVAL` 이벤트 |
| 비활성화 상태에서 제공된 parameter | `POLICY_VIOLATION` |
| 누락, 알 수 없음, 잘못된 type 또는 pattern이 유효하지 않은 parameter | run이 있으면 `POLICY_VIOLATION` 및 `UNSAFE_PARAMETER` 이벤트 |
| Placeholder 또는 parameter-schema 불일치 | `INVALID_STATE` |
| 알 수 없거나 cyclic이거나 잘못된 prerequisite graph | `INVALID_STATE` |
| Phase 1B-1 pure resolver의 모든 prerequisite | 순서가 있는 prerequisite ID와 함께 `BLOCKED` |
| Phase 1B-2 active-run prerequisite PASS 증거 없음 | `BLOCKED` |
| Phase 1B-2 증거 reference가 잘못되었거나, run 밖이거나, 잘못된 command이거나, PASS가 아님 | `INVALID_STATE` |

## 매개변수 해석

1. parameter file은 duplicate-key 탐지와 최대 encoded size 65536 bytes를 갖는 UTF-8 JSON object다.
2. 정규화한 real path는 repository root 안에 유지되어야 하고 secret file이거나 `.git/`에 있으면 안 된다. `.ai-runs/` 아래 경로는 현재 run 디렉터리 내부에서만 허용된다.
3. 모든 parameter 값은 최대 1024 Unicode scalar value이고 C0 control character, DEL, line separator 또는 paragraph separator를 포함하지 않는다.
4. parameter object는 Draft 2020-12 검증으로 command의 폐쇄형 schema에 대해 검증한다. pattern 검사는 `$` end-position 동작에 의존하지 않고 safe-regex body에 `re.fullmatch`를 사용한다.
5. 각 placeholder는 하나의 완전한 argv token을 차지한다. 검증된 string은 해당 token을 하나의 argv 요소로 대체한다.
6. parameter 값은 절대 재parse하거나 whitespace로 분리하거나 glob 또는 variable로 확장하거나 shell syntax로 해석하지 않는다.
7. 치환 후 남아 있는 모든 placeholder marker는 `INVALID_STATE`이다.
8. 해석된 argv는 Phase 1B-2를 위해 메모리에 보관하며 실행 가능한 shell command로 절대 직렬화하지 않는다.

## 분류 및 승인

- `SAFE` command은 다른 모든 검사 후 진행할 수 있다.
- 신뢰할 수 있는 approval adapter가 없으므로 `RISKY` command은 Phase 1B 전체에서 차단한다. 후속 native adapter는 새로 승인된 specification을 통해서만 이를 변경할 수 있다.
- `DESTRUCTIVE` command은 Phase 1B에서 차단한다. 여기에는 database reset/drop/truncate, migration, seed, deployment, production mutation, secret 변경 및 대량 파괴 작업이 포함된다.
- `UNAVAILABLE` command은 절대 실행하지 않는다.
- approval record는 검증되고 현재 run 및 scope와 일치하며 비어 있지 않은 외부 reference를 포함해야 한다. 이 검사는 감사 일관성만 확립한다.

## 사전 조건 강제 적용

prerequisite는 자동 실행하지 않는다. Phase 1B-1은 graph를 검증하고 순서 지정한 후 active-run 증거가 아직 없으므로 prerequisite가 있는 모든 command에 `BLOCKED`를 반환한다. Phase 1B-2는 active run의 schema에 유효한 command-result reference가 일치하는 `commandId`와 결과 `PASS`를 가질 때만 resolution을 계속할 수 있다. 과거 registry `VERIFIED` 상태는 service 또는 일시적인 prerequisite가 현재 사용 가능함을 증명하지 않는다.

Phase 1B-2 PRE_COMMAND 작업은 참조된 command-result 파일이 다음을 만족하는지 검증한다.

- 현재 schema에 유효한 active `run-session.json`에 나열됨;
- 현재 `.ai-runs/<run-id>/` 디렉터리 안에서 resolve됨;
- 같은 `runId`와 일치함;
- `command-result.schema.json`에 대해 검증됨; 그리고
- 필요한 command ID에 `PASS`를 보고함.

증거 누락은 `BLOCKED`다. 모순되거나 잘못된 증거는 `INVALID_STATE`다.

## Phase 1B-2 실행 계약

1. `command-runner.sh start --run-id <id> --task-key <key>`는 command 실행 전에 lock된 schema에 유효한 OPEN run session을 만든다. `run`에는 해당 명시적 active run ID가 필요하다.
2. PRE_COMMAND는 execution-intent 작업, 현재 preflight, Phase 1B-1 검증, active-run prerequisite 증거, rerun 검사 및 무조건적인 RISKY/DESTRUCTIVE 차단을 사용한다.
3. child launch 전에 session은 불변 attempt reservation을 원자적으로 추가한다. reservation은 append-only이며 `RESERVED`에서 정확히 하나의 terminal state로 단조롭게 이동한다. 실패를 숨기기 위해 제거하거나 다시 쓰지 않는다.
4. helper는 `subprocess` list argument, `shell=False`, 저장소 내부 working directory, allowlist 환경, 닫힌 stdin 및 상속한 secret-file 콘텐츠 없이 해석된 argv를 launch한다.
5. stdout과 stderr는 disk 게시 전 경계가 있는 streaming scrubber를 통해 별도로 capture한다. 경계 없는 in-memory capture는 금지된다.
6. scrubber는 authorization header, cookie, token/password/secret assignment, runner가 제공한 민감한 환경 값 및 구성된 literal secret을 마스킹한다. secret file은 capture를 위해 절대 읽지 않는다.
7. launch한 모든 process는 run/command/attempt ID, timestamp, hash, 사용 가능한 경우 native process exit code 및 redaction 상태를 포함하는 schema에 유효한 secret-free `process-attempt` artifact를 만든다. process output 또는 환경 값은 절대 포함하지 않는다.
8. redaction 실패 시 임시 log를 삭제하고 PASS/FAIL command-result를 만들지 않는다. 실행/log field가 null인 schema에 유효한 BLOCKED command-result가 이유를 기록하고 process-attempt는 child 사실을 보존하며 차단하는 `UNSCRUBBED_EVIDENCE` 이벤트를 append한다.
9. redaction 성공 시 command result와 log를 exclusive creation 및 제한적 permission이 있는 같은 디렉터리 임시 path에 쓰고 검증·flush·원자적 rename한 뒤 지원되는 경우 read-only로 만든다.
10. approval 및 policy-violation record는 ID별 하나의 불변 schema에 유효한 파일이다. 공유 session 작업은 소유자 ID, run ID, PID 및 획득 시각을 포함하는 폐쇄형 `owner.json`과 배타적인 `.state/lock/` 디렉터리로 직렬화한다. 획득에는 원자적 디렉터리 생성을 사용하고, release는 제거 전에 완전한 owner record를 비교한다. 살아 있거나 최근의 owner는 차단한다. owner가 dead이면서 expired일 때만 recovery를 허용한다. 변경되지 않은 stale owner를 다시 읽은 뒤 recovery는 stale lock 디렉터리를 recovery-ID quarantine path로 원자적 rename하고 대체 `.state/lock/`을 원자적으로 만들며 대체 owner를 배타적으로 쓴다. 모든 collision은 차단한다. 대체 owner는 불변 폐쇄형 `lockRecovery` 항목을 run-session history에 append하고 quarantine된 owner를 다시 검증하며 quarantine을 제거한 다음에야 대체 lock을 compare-and-release한다. lock recovery는 gateway operation이 아니다.
11. 성공한 정확한 argv는 PASS command 증거를 만든다. registry `VERIFIED` 전이에는 영속적인 정제 저장소 work-log 요약 또는 외부 CI artifact가 추가로 필요하다. 무시된 로컬 증거만으로는 registry가 `CONFIGURED_UNVERIFIED`로 유지된다.
12. 0이 아닌 child exit는 정확한 `processExitCode`가 있는 FAIL을 만든다. 워크플로 제어 exit가 되지는 않는다.

## 재실행 계약

같은 command ID, argv hash, input fingerprint 및 environment fingerprint는 허용된 rerun 이유 없이 한 run에서 두 번 실행할 수 없다. Phase 1B-2에서는 이전 PASS attempt의 중복만 rerun할 수 있고, 그마저도 정규화한 real path가 저장소 내부인 경계가 있는 한 줄 UTF-8 이유 파일이 있을 때만 가능하다. reservation에는 원시 이유가 아니라 `rerunReasonHash`와 `rerunOfAttemptId`를 저장한다. 이유가 없으면 `POLICY_VIOLATION`을 반환하고 `MISSING_RERUN_REASON`을 append한다. Phase 1B-2에는 승인된 failure-triage artifact 또는 권한이 없으므로 이전 FAIL 또는 BLOCKED attempt의 모든 중복은 `BLOCKED`다. approval record와 policy event를 triage 권한으로 과적하지 않는다. 자동 retry 및 실패 attempt rerun은 계속 보류한다.

### Phase 1B-2 보수적 실행 명확화

- command-result 및 process-attempt reference는 정확히 `.ai-runs/<run-id>/commands/<command-id>/<attempt-id>.json` 및 `.ai-runs/<run-id>/process-attempts/<command-id>/<attempt-id>.json`다. 각 artifact `$id`는 해당 reference와 같고, 내장 run/command/attempt ID는 path와 일치하며, reference는 session array와 reservation 전체에서 고유하다. Phase 1A version-1 command-result fixture는 계속 유효하다. `attemptId` 및 `processAttemptRef`는 추가적인 optional schema field이고, Phase 1B-2 의미 검증은 새로 영속화된 command result에 이를 요구한다.
- fingerprint는 명시적인 UTF-8 length-prefixed frame에 대한 SHA-256이다. argv frame은 token 순서를 보존한다. Phase 1B-2에서 각 `inputPaths` 항목은 glob metacharacter가 없는 저장소 상대 literal regular-file path이거나 정확히 `/**`로 끝나는 저장소 상대 directory prefix다. 그 밖의 모든 `*`, `?`, `[`, `]`, `{`, `}`, 빈 prefix, traversal, 절대 path, URI 및 backslash는 `INVALID_STATE`로 거부한다. literal은 존재하는 regular file이어야 한다. directory prefix는 symlink를 따르지 않고 재귀적으로 순회한다. 만나는 모든 symlink는 `INVALID_STATE`이고, directory entry는 무시하며 정규화한 POSIX 저장소 상대 path의 UTF-8 byte-order로 포함된 regular file만 포함한다. 누락되었거나 file이 비어 있는 `dir/**`는 결정적인 `NO_MATCH`를 기여한다. read/stat error는 reservation 전에 차단하거나 `INVALID_STATE`를 반환한다. input fingerprint는 command ID, 정규화 working directory, 선언 순서의 pattern 및 결과 path·byte size·SHA-256을 포괄한다. environment fingerprint는 key로 정렬한 정확한 child 환경 map을 포괄한다.
- schemaVersion 1의 실행은 POSIX 전용이다. child 환경은 존재하고 string 값이며 non-secret일 때 `PATH`, `JAVA_HOME`, `GRADLE_USER_HOME`, `HOME`, `TMPDIR`, `LANG`, `LC_ALL`만 복사할 수 있고 secret 이름 key는 금지된다. production 실행에는 비어 있지 않은 allowlist `PATH` 값 및 정확한 절대 `/bin/sh` path가 실행 가능한 regular file로 존재해야 한다. 그렇지 않으면 실행은 launch 전에 `NOT_CONFIGURED`를 반환한다. 무해한 fake wrapper는 정확한 shebang `#!/bin/sh` 및 shell builtin만 사용한다. caller input에서 interpreter path 또는 lookup을 허용하지 않는다. non-POSIX host는 launch 전에 `NOT_CONFIGURED`를 반환한다. POSIX launch는 새 process session을 만들고, 이후 timeout/resource cleanup은 process group에 SIGTERM 다음으로 경계가 있는 SIGKILL을 보낸다.
- redaction은 엄격한 incremental UTF-8을 사용하는 경계 있는 byte-stream 작업이다. 유효하지 않거나 불완전한 UTF-8은 `UNSCRUBBED_EVIDENCE`다. 읽기는 64 KiB chunk를 사용하고, 각 stream은 1 MiB, 결합 출력은 2 MiB, 구성 literal/pattern width는 4096 byte로 제한하며 scrubber는 8192 byte의 carry를 보존한다. 출력 cap에 도달하면 차단하고 잘린 log는 게시하지 않는다. 필수 pattern은 authorization header, cookie/set-cookie header, bearer token 및 token/password/secret assignment를 포함한다. 승인된 non-secret configuration source가 존재할 때까지 public configured-literal set는 비어 있다. contract test는 내부적으로 경계 있는 literal을 주입할 수 있다. secret file은 절대 읽지 않는다.
- spawn failure, timeout/resource limit, redaction 불확실성, evidence-write 불확실성 및 post-launch 게시 실패는 절대 PASS가 되지 않는다. stale RESERVED reservation에 유효하게 존재하는 process-attempt는 안전한 경우 획득한 replacement lock 아래에서 BLOCKED command result/reservation으로 단조롭게 복구한다. 그렇지 않으면 reservation은 blocked 상태를 유지하고 자동으로 재launch하지 않는다.

## 증거 레이아웃

```text
.ai-runs/<run-id>/
  .state/
    run-session.json
    finalization-journals/
      <journal-id>.json
  run.json
  approvals/
    <approval-id>.json
  policy-violations/
    <event-id>.json
  commands/
    <command-id>/
      <attempt-id>.json
  process-attempts/
    <command-id>/
      <attempt-id>.json
  logs/
    <command-id>/
      <attempt-id>.stdout.log
      <attempt-id>.stderr.log
  gate-results/
    <stage>-<event-id>.json
  artifact-manifest.json
  done-claim.json
  done-claim.md
```

`.state/run-session.json`은 OPEN, FINALIZING 및 FINALIZED를 거쳐 영속된다. 폐쇄형 `finalizationJournalIdentity`는 OPEN에서는 null이고 FINALIZING에서는 정확한 attempt별 journal path/UUID/digest ID이며 FINALIZED receipt의 `journalIdentity`와 계속 같다. FINALIZED 형식은 정식 finalization receipt로 read-only 보존하고 artifact manifest에서 제외한다. `run.json`은 finalization 게시 후에만 존재한다. 모든 `.state/finalization-journals/<journal-id>.json`은 journal UUID, 정확한 source OPEN session, 정확한 의도 FINALIZING session, claim-input reference 및 예상 lock-recovery prefix를 포함하는 독립적 폐쇄형 제어 권한이다. journal은 manifest에서 제외하고 visibility 전에 read-only로 만들며 게시 후 절대 삭제하지 않는다. 비활성 보존 journal은 감사 이력이고 후속 attempt는 항상 새 UUID path를 만든다. 고정 legacy `.state/finalization-journal.json` marker는 허용하지 않으며 명시적 fail-closed recovery가 필요하다. 반복 command attempt는 JSON 내부 `commandId`를 보존하면서 attempt identifier를 포함하는 collision-free result 및 log 이름을 사용한다. 모든 schema-versioned immutable/session/evidence artifact `$id`는 저장소 상대 forward-slash reference와 같다. 일시적인 `.state/lock/owner.json`은 폐쇄형 embedded-schema 제어 JSON이며 artifact나 reference가 아니고 artifact `$id` 동등성 요구가 없다.

이 ID별/attempt별 레이아웃은 상위 설계의 예시적인 flat command path와 `approvals.json`을 명시적으로 대체한다. 승인된 approval schema가 하나의 record를 표현하고 append-only rerun 증거는 flat file을 안전하게 overwrite할 수 없으므로 이 개선이 필요하다.

### 실행 확정 수명 주기

1. `start`는 OPEN `.state/run-session.json`을 만든다. `run.json`은 존재하지 않는다.
2. 모든 reservation 및 terminal artifact reference는 run lock 아래에 단조롭게 append한다.
3. `done-claim-check.sh prepare <run-id> --claim <path>`는 새 UUID를 만들고 `.state/finalization-journals/<journal-id>.json`을 배타적으로 게시한다. journal에는 정확한 OPEN source와 의도한 FINALIZING projection을 내장한다. identity digest는 내장 FINALIZING identity의 `canonicalSha256`만 64 ASCII zero로 바꾼 뒤 compact canonical JSON에 적용한 SHA-256이다. 이 단일 정규화는 순환 self-reference를 끊으며 모든 validator는 같은 규칙을 적용한다.
4. 첫 session compare-and-swap은 `finalizationJournalIdentity`를 포함한 정확한 journal source OPEN session을 journal의 정확한 FINALIZING session으로 바꾼다. 이 전이 후에는 새 command, approval 또는 다른 일반 OPEN 작업을 허용하지 않는다. 비활성 고유 audit journal은 OPEN을 차단하지 않는다. null이 아닌 active identity나 고정 legacy marker가 있는 OPEN session에는 recovery가 필요하다.
5. PRE_DONE_CLAIM은 FINALIZING session, 모든 reservation, 발견한 모든 artifact, policy event 및 제안된 done claim을 검증한 뒤 완전한 gate 결과와 후보 `run.json`을 메모리에서 도출한다.
6. final artifact를 게시하기 전에 finalizer는 폐쇄형 `finalizationReceipt`가 있는 정확한 FINALIZING session을 FINALIZED로 compare-and-swap한다. receipt는 schema가 정의한 모든 `run.json` field, 정식 done-claim 및 gate digest와 outcome, 정확한 manifest ID/run ID, 최상위 session identity와 같은 journal identity 및 완전한 예상 artifact path/kind identity 집합을 보존한다.
7. finalizer는 done claim과 gate를 게시하고 정확한 증거 closure를 요구하며, 보존된 `.state`, manifest 및 최종 `run.json` 자체를 제외한 모든 불변 artifact의 저장소 상대 path, SHA-256 digest, byte size를 갖는 `artifact-manifest.json`을 쓴다.
8. 모든 불변 최종 JSON은 같은 디렉터리 임시 파일에 완전히 encode하고 file-fsync하며 read-only로 바꾸고 mode를 검증한 뒤 배타적 link가 이를 visible하게 한다. 이후 포함 디렉터리를 fsync한다. finalizer는 receipt의 정확한 `runProjection`을 마지막에 `run.json`으로 게시하고 성공 전에 정확한 claim, gate, manifest, run, FINALIZED session 및 active journal에 read-only mode를 다시 적용하고 검증한다. read-only `verify-finalized` 작업은 directory closure 및 digest를 다시 계산하고, 보존된 receipt와 독립 journal을 권한으로 load하며, 결과를 run 외부에 출력한다. finalized run에는 증거를 절대 append하지 않는다.

step 8 전 in-process 검증 또는 게시 예외는 같은 검증된 run-lock owner를 여전히 보유한 상태에서 경계가 있는 rollback을 호출한다. 임시 파일 chmod 후 또는 배타적 link 후 실패를 포함한 게시 불확실성은 visible할 수 있는 read-only artifact, active journal 및 현재 session을 기준으로 조정하며 schema에 유효한 구조화 결과만 반환한다. traceback이 외부로 빠져나가지 않는다. rollback은 먼저 `run.json`이 없음을 증명하고 active 독립 journal을 검증하며 `.state/run-session.json`이 허용된 lock-recovery suffix만 더한 정확한 FINALIZING 또는 receipt-bearing FINALIZED projection과 계속 같음을 증명한다. 귀속된 `done-claim.json`, PRE_DONE_CLAIM gate 결과 및 artifact manifest만 제거한 뒤, journal의 정확한 OPEN source를 허용된 suffix와 compare-and-swap한다. 해당 OPEN CAS는 `finalizationJournalIdentity`를 지운다. 이후 journal unlink나 cleanup은 transaction의 일부가 아니다. 불변 journal은 read-only 감사 이력으로 유지되고, 일반 OPEN 작업은 비활성 고유 journal을 무시하며 다음 finalization attempt는 별도 journal을 만든다. OPEN CAS 후 applied-error는 정확한 session을 다시 읽어 조정한다. FINALIZING recovery는 cleanup 또는 OPEN normalization 전에 최상위 journal identity를 검증한다. 고정 legacy marker, 변경된 journal ID/reference/digest, 변경된 lock owner, 변경된 sealed session, 안전하지 않은 cleanup target, cleanup 실패 또는 `run.json`의 모든 출현은 rollback을 막고 정확한 recovery 상태를 보존하면서 `FINALIZATION_RECOVERY_REQUIRED`와 함께 `BLOCKED`를 반환한다. 성공적인 resume 및 `ALREADY_FINALIZED` recovery는 claim, gate, manifest, run, session 및 active journal에 read-only mode를 다시 적용하고 검증한다. 원시 FINALIZED 상태를 관찰하는 실패한 모든 recovery도 lock을 release하기 전에 session과 안전하게 식별한 journal을 복구한다. `run.json` 게시 후 검증은 보존된 FINALIZED receipt, journal 및 manifest digest에 고정되며 게시된 `run.json`은 절대 rollback하지 않는다. 어떤 PRE_DONE_CLAIM 작업도 권한을 구성하기 위해 finalized `run.json`을 읽지 않으므로 finalization에는 순환 trust dependency가 없다.

## Phase 1B-3 완료 계약

Phase 1B-3은 무결성 gate이며 task-applicability 또는 verification-completeness 권한이 아니다. machine-readable change classification, required-check 선택, 허용된 N/A/skip 정책 및 제한 없는 완료 gating은 Phase 2C가 담당한다. 그러므로 Phase 1B-3은 caller가 작성한 requirements manifest를 도입하거나 생략된 검사가 허용되었다고 주장해서는 안 된다. Phase 2C가 존재하기 전까지 모든 `NOT_APPLICABLE` 또는 `SKIPPED_WITH_REASON` 검사는 Phase 1B-3 무결성 gate를 `BLOCKED`로 만든다. 기록된 이유는 필요하지만 충분한 권한은 아니다.

finalization 중 `done-claim-check.sh prepare`는 FINALIZING run session, 모든 reservation과 발견된 artifact, command result, process attempt, approval, policy violation, gate result, evidence reference, artifact digest 및 제안된 done claim을 검증한다. gateway 결과에는 `completenessEvaluated: false` 및 `scope: INTEGRITY_ONLY`가 포함된다.

모든 check-level `evidenceRefs` 항목은 active session이 소유한 증거로 resolve되어야 하며 claim의 top-level evidence closure에도 나타나야 한다. claim은 PASS check, 실행된 command 또는 완료된 capability를 not run으로 선언할 수 없다. 게시 후 `verify-finalized`는 보존된 FINALIZED session, done claim, manifest 및 PRE_DONE_CLAIM 결과를 schema 검증하고, manifest-kind reference를 재구성하며, 정식 claim/gate identity를 다시 계산하고, 오래되었거나 변경된 `run.json` field, manifest identity, outcome 또는 artifact identity를 거부한다.

전체 `PASS`에는 다음이 필요하다.

- `implementationStatus: PASS`;
- 영속적인 정제 증거가 있는 적용 가능한 check가 최소 하나;
- 모든 check 결과가 정확히 `PASS`; Phase 1B-3은 이를 승인할 수 없으므로 N/A와 skip을 거부함;
- 실제 존재하는 모든 command/evidence artifact가 check 또는 명시적 `notRunItems`에 일관되게 표현됨;
- 차단하는 policy violation 없음;
- 해결되지 않은 unexpected 500 또는 unhandled exception requirement 없음;
- blocker 없음;
- 정식 state가 변경되었을 때 오래된 generated summary 없음.

claim에 명시된 check 안에서 `NOT_CONFIGURED`를 조용히 PASS로 변환할 수 없다. child `FAIL`, 유효하지 않은 증거, 숨겨졌거나 manifest에 없는 실패, 증거 없는 완료 또는 해결되지 않은 차단 policy violation은 무결성 gate를 통과할 수 없다.

상세 제어 우선순위는 다음과 같다. 유효하지 않은 artifact 또는 graph -> `INVALID_STATE`; 차단 policy violation -> `POLICY_VIOLATION`; 실행된 child 실패 -> `FAIL`; blocked, not-configured, N/A 또는 skipped leaf -> `BLOCKED`; 그 외 내부적으로 일관된 모든 PASS claim 증거 -> 무결성 `PASS`. `run.json` 및 done-claim 워크플로 결과에는 `INVALID_STATE` 또는 `POLICY_VIOLATION`이 포함되지 않으므로, gate-result artifact가 상세 제어 outcome을 보존하는 동안 영속된 전체 결과는 `BLOCKED`다.

무결성 PASS는 제한 없는 전체 DONE을 뒷받침하거나, 적용 가능한 모든 검증이 실행되었음을 증명하거나, N/A/skip이 승인되었음을 증명할 수 없다. Phase 2C가 권위 있는 applicability 정책을 제공할 때까지 보고서는 `Phase 1B integrity PASS; verification completeness NOT EVALUATED`를 명시해야 한다.

## 계약 테스트 매트릭스

Phase 1B test는 최소한 다음을 포함해야 한다.

- runtime 부재, Python 2, `jsonschema` 누락, bootstrap-output 고정 형태 및 성공적인 영속 runtime-state 기록/rollback;
- 중복 JSON key 및 유효하지 않은 calendar date;
- 알 수 없는 schema URI/version 및 schema path escape;
- 중복 command ID 및 required/property 불일치;
- 지원하지 않는 executable, shell token, raw command 및 해석되지 않은 placeholder;
- 과도하게 큰 parameter file/value, control character, 알 수 없거나 누락되었거나 추가되었거나 잘못된 type의 value, 안전하지 않은 regex 구성, catastrophic-pattern 시도 및 full-string 불일치;
- space와 shell metacharacter가 있는 parameter value가 하나의 inert argv element로 유지됨;
- 알 수 없는 command 및 unavailable/stale command;
- caller가 작성한 approval file이 있어도 모든 risky 및 destructive command 차단;
- 알 수 없는 prerequisite, cycle, Phase 1B-1의 비어 있지 않은 prerequisite 차단, Phase 1B-2의 PASS 증거 누락, 잘못된 run 증거 및 유효한 same-run PASS;
- 이유 없는 반복 실행 시도;
- child 0이 아닌 exit가 workflow exit와 분리되어 보존됨;
- 필요한 각 secret class의 redaction, process-attempt 보존, temporary-log 삭제 및 scrub 실패 시 차단;
- 잘못되었거나 누락되었거나 모순된 command 증거;
- 단조로운 reservation 전이, stale-lock recovery, 정확한 directory closure, artifact digest 불일치, 증거 없는 PASS done claim 및 숨겨진 실패 leaf 결과;
- finalization crash 지점, final 이후 append 없음 및 read-only finalized 검증;
- `completenessEvaluated: false`를 명시적으로 보고하는 integrity PASS;
- 오래된 generated command-registry 및 project-state 요약;
- supported-path 경계 문구 및 direct-tool bypass event 동작.

test에는 임시 디렉터리와 무해한 fixture executable만 사용한다. Gradle, 제품 server, Docker, database, migration, seed 또는 HTTP API를 호출하지 않는다.

## 강제 적용 경계

Phase 1B는 저장소 script를 통해 routing된 호출만 강제한다. 알려진 bypass를 탐지하고 기록할 수 있으며, done-claim 검토는 탐지된 bypass 후 완료를 차단할 수 있다. 모든 직접 host shell, MCP, editor, file-read, search 또는 외부 도구 호출을 방지하거나 관찰할 수는 없다. native runtime adapter 및 CI 강제 적용은 후속 범위로 유지된다.

## 수용 기준

### Phase 1B-1

- 현재 runtime preflight는 fail closed하며 Python 또는 `jsonschema`를 절대 가정하지 않는다.
- 성공한 bootstrap은 검증된 정제 LOCAL runtime 증거를 기록하고 recovery-journal test와 함께 정식 JSON 및 generated summary를 transactionally 동기화한다. 실패한 bootstrap은 정식 상태를 변경하지 않는다.
- Phase 1A의 일곱 schema는 FormatChecker가 있는 allowlist Draft 2020-12 validator로 검증한다.
- registry 의미상 유효하지 않은 case는 lookup 전에 거부한다.
- parameter 입력은 폐쇄형이고 whole-token 전용이며 raw argv를 추가할 수 없다.
- SAFE classification 및 Phase 1B-1 prerequisite 차단은 지정된 결과를 생성하고 RISKY와 DESTRUCTIVE는 항상 차단한다.
- resolver test는 project process가 생성되지 않음을 보여 준다.

### Phase 1B-2

- 해석된 project argv는 `command-runner.sh`만 실행한다.
- 실행에는 list argv 및 `shell=False`를 사용한다.
- schema에 유효한 session, reservation, process attempt, result, 정제된 log, hash, approval 및 violation은 단조 및 append-only 규칙으로 영속화한다. artifact-manifest schema 및 fixture는 Phase 1B-2에 추가하고 manifest 게시와 directory closure는 Phase 1B-3으로 유지한다.
- failure, rerun, approval 및 redaction 동작은 fail closed다.

### Phase 1B-3

- done claim은 실패, blocked, manifest에 없음, stale, digest 불일치 또는 정제되지 않은 증거를 숨길 수 없다.
- final aggregation은 공통 결과 매핑을 따른다.
- contract fixture는 유효하고 유효하지 않은 gateway 동작을 포괄한다.
- 문서는 supported-path 강제 적용 한계를 명시적으로 보고한다.
- gate는 무결성만 보고하고 Phase 2C 전에는 verification completeness를 절대 주장하지 않는다.

## Phase 1B-1 검증 경계

Phase 1B-1 구현은 helper-runtime preflight, 영속적인 정제 state-record 작업 및 gateway 자체를 검증하는 데 필요한 helper contract test만 실행할 수 있다. Gradle, 제품 test, application server, Docker Compose, HTTP/API, database, migration, seed 및 infrastructure 명령은 Phase 1B-2 command 실행 및 증거 기록이 완료될 때까지 `NOT RUN`으로 유지된다.

## 남은 후속 범위

- Phase 1B-1이 검토를 통과한 후의 Phase 1B-2 command 실행 및 증거 영속화.
- Phase 1B-2가 검토를 통과한 후의 Phase 1B-3 done-claim gate 및 전체 contract suite.
- Phase 2 재사용 가능한 skill, 권위 있는 task/change classification, verification applicability/completeness 정책, verification-level orchestration, context cache, API smoke runner 및 문서 통합.
- Phase 3 CI gate, native host adapter 및 지원되는 곳의 더 광범위한 interception.
- Native Windows `gradlew.bat` executable profile.
