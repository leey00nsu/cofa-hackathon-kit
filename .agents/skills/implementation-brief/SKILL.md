---
name: implementation-brief
description: Build evidence-based implementation Q&A and a short review sheet before a Cofa hackathon submission. Use when wrapping up an implementation or preparing to explain the actual code. Do not answer live post-submission exam questions.
---

# 제출 전 구현 문답

이 스킬은 **과제풀이 단계**의 구현 완료·설명 준비용이다. 제출물 확정 후, 후속 서술형 중 또는 실제 서술형 문제의 답변 요청이면 AI 답변을 생성하지 않고 참가자가 직접 응시하도록 안내한다. 문서 열람이 허용된다고 가정하지 않는다.

1. 공식 과제 README, `.hackathon/OPERATING_RULES.md`, `.hackathon/INTERVIEW_PROTOCOL.md`, 요구사항·결정·검증 기록을 읽는다. 탐색 표와 실제 고객 확인 답변을 점검하고, 묻지 않은 영역·미확인 규칙·확인했지만 미구현인 요구를 구분한다. 중요한 미확인은 남은 시간에 맞는 질문으로 제안하고 답을 받지 못하면 한계로 남긴다. 실제 구현 파일과 핵심 데이터 흐름을 확인한다. 없는 DB·API·아키텍처·성능·테스트·결정 이유를 만들지 않는다. 시간과 규정이 우선이다.
2. 필수조건을 대조하고 중요한 결함은 수정·재검증한다. 그 후 문답 작성 중에는 코드를 안정시킨다. 실행 근거가 필요하면 `python3 .hackathon/tools/kit.py check --workspace . --id <id> -- <실제 명령 인자들>`로 기록한다. Browser는 참가자가 직접 확인한다.
3. `python3 .hackathon/tools/kit.py prepare-qa --workspace .`로 처음 문답 파일을 만들고, 이미 있으면 보존하며 갱신한다. `docs/QA_CONTRACT.md`의 배치본 `.hackathon/QA_CONTRACT.md`를 읽어 `.hackathon/study/qa.json`을 실제 답변으로 채운다.
4. 핵심 6개 주제는 문제·우선순위, 구조·데이터 흐름, 업무 규칙·데이터 정확성, 검증·오류 복구, 대안·한계·변경 대응, AI 지시·판단이다. 각 주제당 핵심 질문 1개, 필요할 때 추가 질문 최대 6개다. 실제 서술형 문항과 일치한다고 주장하지 않는다.
5. 각 답변은 결론 → 실제 구현과 이유 → 검증 근거 → 한계로 작성한다. 짧은 답변은 350자 이내, 상세 답변은 참가자가 자신의 말로 설명할 수 있을 정도로 구체적으로 쓴다. 근거마다 실제 상대 경로·행 번호·그 행에 존재하는 짧은 인용을 확인한다. 일반 원리만 적거나 사후 추정을 당시 의도로 표현하지 않는다.
6. `render-qa`, `verify-qa` 명령으로 파일 지문·근거·출력 문서를 검증한다. 검사 실패를 고치되 내용 검토 없이 지문만 바꾸지 않는다. 코드·요구사항·체크 기록이 바뀌면 관련 답변을 재검토한 뒤 `fingerprint`로 현재 지문을 받아 JSON에 반영하고 다시 렌더한다.
7. 참가자에게 `.hackathon/study/LAST_REVIEW.md`부터 읽게 하고, 핵심 6개를 본인 말로 설명하도록 안내한다. 시간이 있으면 과제풀이 중 예상 질문을 하나씩 연습할 수 있다. 부족한 이해는 코드에 근거해 설명한다. 참가자 복습과 직접 제출을 위한 시간을 남긴다.

완료 시 두 문서 경로, 실제 검사 결과, 미구현·미검증·한계를 알린다. 스크립트의 통과는 구조·일치 검사이며 답변의 의미적 정확성·참가자 이해·공식 채점 결과를 보장하지 않는다. 제출 버튼을 자동 조작하지 않는다. 확정 이후 AI를 멈춘다.
