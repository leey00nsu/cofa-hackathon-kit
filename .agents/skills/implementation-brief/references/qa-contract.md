# 구현 문답 생성 규약

`implementation-brief`로 문답을 작성·검사할 때만 읽는다.

현재 파일 이름은 이 준비물의 내부 관례다. 공식 필수 제출 파일·경로가 있으면 우선 작성하고 이 문서들이 그것을 대신한다고 주장하지 않는다.

## 입력과 명령

`prepare-qa`는 빈 스키마와 현재 소스 지문을 생성한다. 답변을 만들지는 않는다. Codex가 실제 구현과 기록으로 내용을 채운 후 `render-qa`가 검증된 JSON을 두 Markdown으로 렌더한다. `verify-qa`는 현재 소스와 렌더 결과까지 다시 대조한다.

```sh
python3 .hackathon/tools/kit.py prepare-qa --workspace .
python3 .hackathon/tools/kit.py fingerprint --workspace .
python3 .hackathon/tools/kit.py render-qa --workspace .
python3 .hackathon/tools/kit.py verify-qa --workspace .
```

핵심 질문의 topic 값은 각각 `problem`, `architecture`, `correctness`, `verification`, `tradeoffs`, `ai-control`이다. `priority`는 `core` 또는 `extra`이며 핵심은 주제당 1개, 전체는 6~12개다.

질문 객체 예시는 **형식 설명**이며 실제 답변으로 사용하지 않는다.

```json
{
  "id": "Q01",
  "topic": "problem",
  "priority": "core",
  "question": "실제 구현에 맞는 예상 질문",
  "short_answer": "실제 근거로 작성한 350자 이내 답변",
  "answer": "실제 처리·선택 이유·검증·한계를 설명한 답변",
  "evidence": [{"path": "src/example.ts", "line": 12, "quote": "해당 행에 있는 실제 짧은 문자열"}],
  "check_ids": [],
  "limitations": ["실제 한계 또는 미검증 범위"]
}
```

`source_fingerprint`는 `fingerprint`의 digest다. `reviewed_at`는 내용 검토를 실제 완료한 ISO 시각이다. 체크 ID를 참조하면 실제 저장된 실행 기록이 표시된다. 실패 기록도 근거로 사용할 수 있지만 성공한 것처럼 설명하지 않는다. 테스트 주장은 해당 체크 근거 또는 명확한 수동 검증 기록을 확인한다.

문답 지문과 개별 검사의 실행 지문은 목적이 다르다. 문답에는 장부·실행 기록 변경도 반영하고, 개별 검사는 검사 자체의 로그와 상태 갱신을 제외한 소스 및 관련 요구/답변을 연결한다. `audit-requirements`의 PASS는 그 연결의 구조 검사이며 문답 의미·참가자의 이해나 모든 요구 완료를 증명하지 않는다. 참가자의 중간 설명과 최종 자기 설명 결과는 실제 응답을 받은 경우에만 이해 확인으로 기록한다.

`check_ids`에는 `manual-check`의 실제 관찰 ID도 참조할 수 있다. 출력은 이를 ‘참가자 수동 진술’로 명시하고 자동 실행과 구분한다. 실패·NOT_RUN 근거도 답변의 한계 설명에 사용할 수 있으며 통과로 바꾸어 서술하지 않는다.

## 검사 범위

소스 지문은 의존성·Git 내부·일반 빌드 캐시·준비 레포 자체·생성한 복습 파일을 제외한 작업 공간의 파일 내용과 경로를 반영한다. 요구사항·결정·검증·체크 기록은 포함한다. 빌드 산출물·모든 제출 파일의 완전한 무결성 보증은 아니다.

파일 삭제·이름 변경·수정·체크 결과 변경은 지문을 바꾼다. 근거는 작업 공간 내부의 일반 UTF-8 파일이어야 하고 행 범위와 quote를 확인한다. 경로 이탈·심볼릭 링크를 통한 외부 읽기·생성 문답 자체를 근거로 삼기는 거절한다. 네트워크 요청은 하지 않는다.

검사기는 자연어 의미, 존재하지 않는 성능 주장, 참가자의 이해까지 판단하지 못한다. Codex의 실제 구현 대조와 참가자의 자기 설명이 필요하다. 사전 준비 상태에서 문답에 사업 사실이나 가짜 통과 결과를 채우지 않는다.
