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

## 2026-11-02 추가 비교에서 참고한 원리

아래 고정판을 읽고 기존 검사기·기록·학습 절차를 보완했다. 코드·SKILL·양식을 직접 복사하지 않았고 추가 패키지·모델·설치기를 동봉하거나 실행하지 않는다. 이 목록은 해당 저장소의 공식 승인·동작 보증 또는 저장소 전체에 대한 재사용 허락을 뜻하지 않는다.

- [ripplelover/cofa-ready-kit · b70748d](https://github.com/ripplelover/cofa-ready-kit/tree/b70748d1d6a0956eb8d41052b7ffd448766e5961): 다중 테스트 요약의 실패 보존과 데이터 결합/비율 확인 관점.
- [suwonyoo/yoo-playbook · 308dc9d](https://github.com/suwonyoo/yoo-playbook/tree/308dc9df78691656c96e4f2c6407fa98e4cb1090): 원본 실행 로그의 보존·내용 일치 확인 관점.
- [mmporong/kit · b103ed5](https://github.com/mmporong/kit/tree/b103ed5632abe4ebc679d7a029fca6cb37b06567), [Ju-unn/codex-lean-kit · 2970269](https://github.com/Ju-unn/codex-lean-kit/tree/2970269b4c400bfe7b56304df2b559b43fadf268): 자료의 뜻·계산 대상·예측 시점에 맞는 검증 선택.
- [zittenyetten/cofa-probe-kit · 0b4a9b2](https://github.com/zittenyetten/cofa-probe-kit/tree/0b4a9b21d38f26935444fcea074b3fd39677c6e0), [jangabc3/cofa-kit · 2e8390f](https://github.com/jangabc3/cofa-kit/tree/2e8390ff4bae5637a6f32cf80b928dc902e8287d): 실제 제안·결정 주체·참가자 개입 사건 구분.
- [NaYoung1017/my-cofa-plugin · aa89b3f](https://github.com/NaYoung1017/my-cofa-plugin/tree/aa89b3fd3887b5a26658c240e0e7a651845b7f8b): 같은 입력 한 건의 처리 과정을 따라가는 보충 학습 관점.
- [bladem0117/cofa-kit · cef41cf](https://github.com/bladem0117/cofa-kit/tree/cef41cfa3ac628a784e2547a1bf04bd1da8f0be2), [AgenticLab-SH/sh-workflows · c5616c6](https://github.com/AgenticLab-SH/sh-workflows/tree/c5616c6adcbd6d513e1df1fc53b09e538e9db70b), [hyeongus2/codex-kit · e1f6acb](https://github.com/hyeongus2/codex-kit/tree/e1f6acbb473f3e321de2737b0e5167371bd6dc8d): 재개 시 상태 대조·실패 접근 전환·위임 파일 담당 관점.
