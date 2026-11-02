# 기존 장부와 실제 검증을 연결하는 명령

Python 3.10+ 표준 라이브러리만 사용한다. 공식 과제 지시가 우선이다. 아래 명령은 형식 예시이며 실제로 받은 답변·실행·관찰만 기록한다. 준비 키트에는 문제별 요구나 통과 결과를 미리 넣지 않는다.

## 하나의 요구사항 장부

설치기는 기존 `.hackathon/REQUIREMENTS.md`, `docs/REQUIREMENTS.md`, 루트 `REQUIREMENTS.md` 및 소문자 이름을 찾아 하나를 재사용한다. 후보가 여러 개면 파일을 쓰기 전에 중단하므로 `install --requirements <기존경로>`로 정본을 지정한다. 설치 결과와 `.hackathon/install.json`에 실제 경로를 기록하고 AGENTS에 반영한다. 다른 이름의 문서도 명시적으로 지정할 수 있다. 기존 본문·ID·공식 README는 보존한다.

감사는 템플릿의 Markdown 표를 읽는다. 영문 대응 열은 `Requirement ID, Description, Status, Customer Evidence, Acceptance Criteria, Implementation Files, Verification Procedure, Actual Verification Result, Remaining Issues`다. Design Decision과 우선순위는 기존 표에 유지하되 자동으로 의미를 판단하지 않는다. 셀 안 `|`는 `\|`로 작성한다. 다른 문서 형식은 감사가 읽을 수 없다고 표시하며 별도 장부를 자동 생성하거나 상태를 바꾸지 않는다.

고객 원문 `.hackathon/private/INTERVIEWS.md`에는 실제 답변을 받은 뒤 `## Q1` 제목과 `질문:`, `답변:`으로 한 건씩 적는다. `### Q1 답변` 뒤의 실제 원문도 인식한다. 답변 대기 절·코드 블록의 형식 예시는 답변 근거로 인정하지 않는다. Q1은 번호 형식의 예시이며 실제 대화 없이 생성하지 않는다. 원문 진위 자체를 도구가 증명하지는 못한다.

## 실제 실행 기록

```sh
python3 .hackathon/tools/kit.py check --workspace . --id tests-01 --requirement R-001 --test-runner unittest -- python3 -m unittest discover -v
```

한 실행이 여러 요구를 검사하면 `--requirement`를 반복한다. 실제로 검증한 요구만 연결한다. 확인 대상은 코드뿐 아니라 등록 시점의 요구 설명·수락 조건·고객 근거와 해당 답변 내용의 지문이다. 장부에는 같은 R번호를 유지하고 **실제 결과** 셀에 `check:tests-01`과 관찰 요약을 적는다. 별도 Evidence DB를 만들지 않는다.

명령 실행 전후의 파일 지문·원래 종료 코드·실행 시각·테스트 요약·전체 로그 경로가 `.hackathon/checks/<id>.json`에 남는다. 전체 stdout/stderr는 `<id>.log`에 보존하고 JSON에는 마지막 각 32,000자와 잘림 여부를 저장한다. 기존 ID는 덮어쓰지 않는다. 실패를 고치면 같은 절차를 새 ID로 재실행한다.

실행 지문은 준비 키트·설치 manifest에 등록된 스킬·장부/로그용 `.hackathon/`·로컬 tracker·기존 요구사항 정본·`docs/DEFENSE.md` 색인·일반 의존성/빌드 캐시를 제외한다. 새로 작성한 제품 스킬을 포함한 제품 파일·테스트·설정·그 외 입력 자료는 포함한다. 제품 코드를 장부 전용 경로에 두지 않는다. 요구·수락 조건·참조 고객 답변은 별도 연결 지문으로 비교한다. 상태 칸·Defense 설명을 갱신하거나 관계없는 Q를 추가하는 것만으로 이전 검증을 무효화하지 않는다. 문답 지문은 Defense를 포함하므로 설명 갱신 뒤 생성 문답은 재검토한다. 제품 파일 내용이 바뀌거나 실행 중 변경되면 다시 검사한다. 동일 내용으로 되돌아온 경우·제외한 파일·외부 환경의 모든 변화까지 탐지하는 보증은 아니다.

| 결과 | 의미 |
| --- | --- |
| PASS | 명령 성공, 지문 안정, 지원 테스트면 유효 실행 있음 |
| FAIL | 원래 명령 실패/타임아웃 |
| NOT_RUN | 지원 테스트의 0건 또는 전부 skip |
| UNVERIFIED | 실행 중 소스 변경 또는 지원 runner 요약을 읽을 수 없음 |

unittest/pytest는 직접 명령과 `python -m` 호출에서 자동 인식한다. Node의 `node --test`도 인식하며 `--test-reporter=tap`의 요약을 읽는다. npm 등 wrapper는 `--test-runner node`를 명시하고 내부 runner에서 TAP을 출력한다. skip/todo/cancelled는 유효 실행에서 제외하며 실패/cancelled가 있으면 통과로 보지 않는다. wrapper가 실패를 출력하고 0을 반환해도 해당 기록은 FAIL이다. Node가 빈 파일 로드만 테스트 1건으로 집계할 수 있어 단순 import 성공은 기능 검증으로 삼지 않는다.

일반 CLI는 `none`으로 테스트 수를 추정하지 않는다. pytest 파서의 동작 검증은 자체 요약 fixture를 사용하며 시험 환경의 pytest 실행을 보장하지 않는다. 출력 요약은 실제 테스트의 의미나 전체 수락 조건 충족을 입증하지 않는다. 중간 검증 실행과 템플릿 사용은 [자동 검증 안내](../AUTOMATED_TESTING.md)를 따른다.

원래 명령이 비정상 종료하면 원래 종료 코드를 유지한다. 원래 0이지만 결과가 NOT_RUN/UNVERIFIED이거나 wrapper가 숨긴 FAIL이면 CLI는 2를 반환한다. Python 버전에 따라 unittest 0건의 원래 종료 코드가 0 또는 5일 수 있으며 그대로 보존한다.

## 실제 수동 관찰

참가자가 **현재 코드에서 실제 확인한 결과**를 전달한 뒤에만 사용한다. 아래 note를 그대로 실제 결과로 복사하지 않는다.

기본은 자동 회귀 검사 뒤의 최종 UI 목록에서 한 번에 확인받는 것이다. 기능마다 중간 클릭 검증을 요구하지 않는다. UI 확인 대기는 독립 구현을 막지 않으며 필요한 UI 수락 조건을 통과 처리하는 근거도 아니다.

```sh
python3 .hackathon/tools/kit.py manual-check --workspace . --id ui-01 --requirement R-001 --result PASS --note '참가자가 실제 확인한 입력·행동·관찰 결과'
```

결과는 PASS/FAIL/NOT_RUN이다. JSON에는 참가자 진술임을 명시하고 기록 시점의 소스/요구 지문을 연결한다. 오래전 관찰 뒤 코드가 바뀌었다면 현재 소스의 통과로 기록하지 말고 다시 확인한다. 장부 실제 결과 셀의 참조는 `manual:ui-01`이다. 브라우저 조작·캡처·자동 관찰은 하지 않는다. CLI는 각 결과에 0/1/2를 반환하며 실제 참가자 관찰의 진위는 검사하지 못한다.

## 읽기 전용 감사와 리뷰 범위

```sh
python3 .hackathon/tools/kit.py audit-requirements --workspace .
python3 .hackathon/tools/kit.py review-scope --workspace .
```

감사는 중복/잘못된 ID·상태·근거·실제 파일을 확인하고 Verified이면 연결된 성공 기록·소스·수락 조건·고객 답변 지문까지 대조한다. 누락·실패·대기·오래된 기록을 보고하며 상태를 자동 승격하거나 문서를 고치지 않는다. 출력의 `not_marked_verified`에는 아직 Verified가 아닌 ID가 남는다. **감사 PASS는 구조와 연결의 통과이며 모든 요구 구현 완료가 아니다.** 빈 장부는 NOT_RUN, 감사 오류는 FAIL이다. 종료 코드는 0/2/1이다.

`review-scope`는 설치 시 기준 커밋 이후와 현재의 커밋·staged·unstaged·미추적 파일을 모두 열거한다. Git이나 기준이 없으면 확인 가능한 범위를 표시하고 실제 파일을 직접 읽어 검토한다. 삭제 파일도 대상에 들어가며 파일명 목록은 코드 리뷰 결과가 아니다. Matt code-review의 요구 충족/품질 두 관점은 유지한다.

## 환경 조회

```sh
python3 .hackathon/tools/kit.py preflight --workspace .
python3 .hackathon/tools/kit.py preflight --workspace . --url http://127.0.0.1:3000/api/health
```

Python 버전·Git/Node/npm 존재·장부 위치를 읽기만 한다. 특정 CLI 부재를 모든 과제의 실패로 취급하지 않는다. URL은 실제 서버의 로컬 loopback 주소만 허용하며 응답 본문은 기록하지 않고 redirect도 따라가지 않는다. 포트 3000과 `/api/health`는 예시다. 서버를 켜거나 패키지/모델/권한/플랫폼을 변경하지 않는다. HTTP 성공은 화면 사용성·데이터 저장·제출 준비 완료를 뜻하지 않는다.
