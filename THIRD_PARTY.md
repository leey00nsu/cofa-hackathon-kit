# 공개 자료 출처

## Matt Pocock Skills

- 원본: https://github.com/mattpocock/skills
- 고정 커밋: `a496f5513d4a4cf889bc48e189e579f4b0bdf6aa`
- 포함 범위: 원본 `skills/` 전체, README, LICENSE
- 라이선스: MIT, Copyright (c) 2026 Matt Pocock. `vendor/matt-pocock-skills/LICENSE` 보존.
- 수정: 동봉한 원본은 변경하지 않음. 대회용 적용 차이는 `templates/AGENTS.md`의 프로젝트 운영 지시에만 기록.
- 검증: `vendor/snapshot.json`에 동봉 파일의 SHA-256 목록. `python3 scripts/kit.py verify-vendor`로 확인.
- 업데이트: 자동 갱신·플러그인 설치를 실행하지 않음. 대회 전 검증한 고정본을 사용.

## 참가자 안내

사용자가 제공한 참가자 메일과 3개 PDF를 규칙 확인에 사용했다. 원문·QR·개인 링크·이미지는 동봉하지 않는다. 운영 규칙의 요약은 준비 절차이며 공식 안내를 대체하지 않는다. 미공개 과제·고객별 요구·실제 답안은 포함하지 않는다.

공개 배경 설명:

- https://www.getcofa.com/ko/probe
- https://skhynix-hackathon.com/ai-2026
- https://learn.chatgpt.com/docs/build-skills
- https://learn.chatgpt.com/docs/agent-configuration/agents-md

## 검증 보완 설계에서 참고한 공개 사례

다음 저장소의 설계 원리를 비교했다. 코드·스킬 원문을 복사하거나 자동 설치하지 않고 기존 `scripts/kit.py`와 장부에 독립 구현했다. 해당 프로젝트의 실환경 호환성·성능 주장을 이 키트의 검증 결과로 사용하지 않는다.

- https://github.com/arcturus0637-rgb/cofa-prelim-kit — 요구와 최신 성공 근거 연결.
- https://github.com/Navv6/ank-probe-harness — 소스/계획 변경 후 근거 재검토.
- https://github.com/phy0916/cofa-probe-starter — 장부 필수 필드와 중복 참조 검사.
- https://github.com/hongkevin/cofathon-prep — 검사 0건과 통과 구분.
- https://github.com/hamjoon2003/sk-hynix-2nd-harness — unittest 실행 수와 skip 관찰.

자동 검증 운영은 Python unittest와 Node node:test의 표준 runner를 사용한다. HTTP/임시 데이터 참조 코드는 이 저장소에서 작성했으며 다른 프로젝트의 앱 코드를 포함하지 않는다.

- https://docs.python.org/3/library/unittest.html
- https://nodejs.org/api/test.html
