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

## 2026-11-03 추가 비교에서 참고한 원리

아래 고정판의 일반 원리를 참고해 기존 안내를 독립 작성했다. 코드·SKILL·양식을 직접 복사하거나 동봉하지 않았다. 라이선스 미지정·NOASSERTION을 포함한 저장소의 공개 상태를 복사 허가로 해석하지 않으며, 작성자의 실행·호환성·점수 주장을 이 키트의 검증 결과로 사용하지 않는다. 비공개 자료·구체 과제 답안·새 설치기·외부 훅·모델은 가져오지 않는다.

- [semobuilder/exam-solver · cba452d](https://github.com/semobuilder/exam-solver/tree/cba452d9441197c8d68bc0365d751982b817887e): 새 정보 없는 반복 질의의 종료, 저장/확정/후속/최종 접수 구분, 장애 관측·타이머 불일치 대응.
- [arcturus0637-rgb/cofa-prelim-kit · 4e2300a](https://github.com/arcturus0637-rgb/cofa-prelim-kit/tree/4e2300ab02f91b50938aa7c0bf747a87a2249e44), [kane313759-netizen/Myskill · b4f4fee](https://github.com/kane313759-netizen/Myskill/tree/b4f4fee0d4fb8db8274164530d5f09cd2aeccb82): 최적화의 업무 근거·제약·종료 상태와 최적성 보장 범위.
- [jui-ced/kit · 62af335](https://github.com/jui-ced/kit/tree/62af3352b8d9ad9e6c3a33c42a92c77da53a4a45), [song0328/cofa-workflow · d148c98](https://github.com/song0328/cofa-workflow/tree/d148c984314cbde68d44a602b73350faee5f0afa): 같은 조건의 유효한 기준선 비교와 품질·실측·한계 구분.
- [MIIXmix/cofa-kit · b975af0](https://github.com/MIIXmix/cofa-kit/tree/b975af0f12b8af5ac3407b2b63093d1edc24fa56): 입력/설정 변경 뒤 결과의 기준과 늦은 응답 검증.
- [HyeongiJeon/CodexHarness · d106c7b](https://github.com/HyeongiJeon/CodexHarness/tree/d106c7b26b31320cd741430a5ce4e3960531509f): 프로세스·포트·문서/자산/API 응답을 나누는 미리보기 장애 진단.
- [hyeongus2/codex-kit · 9fd2591](https://github.com/hyeongus2/codex-kit/tree/9fd2591f2072c7a0e0ff05134b40e958181c5e01), [LSJ0621/task_workflow · 133469d](https://github.com/LSJ0621/task_workflow/tree/133469d6e3e5534f18ab69c54998c6f37501edfe): 파일 담당과 별개인 공유 의존성·실행환경 변경 조정.
- [allsleep7610/hynix-hackathon-workflow · fb136df](https://github.com/allsleep7610/hynix-hackathon-workflow/tree/fb136dfc14fa0367ba6670179afdfe2389b6397c): 인계 위치와 같은 정본을 명시적으로 식별하는 관점.

이번 검사기 수정은 현재 키트와 자체 가상 입력의 재현에서 도출했다. 외부 검사기 코드나 실제 고객 기록을 이식하지 않는다.

## 2026-11-05 추가 비교에서 참고한 원리

아래 고정판을 비교해 기존 검사기와 인터뷰·검증·병렬 운영 지침을 보완했다. 코드·SKILL·양식을 직접 복사하지 않고 현재 코드와 명시적인 가상 입력에서 독립 구현·서술했다. 공개 상태를 재배포 허가로 간주하지 않으며 외부 앱·검사기·설치기·테스트를 실행하거나 동봉하지 않았다. 새 프레임워크·모델·브라우저 자동화는 추가하지 않는다.

- [ripplelover/cofa-ready-kit · d6745cb](https://github.com/ripplelover/cofa-ready-kit/tree/d6745cbe30097ce2a5ccb5215ab2eb59387d30ed): 다중 테스트 요약의 불확실성·실패 보존, JSON 중복 키 거절. 현재 키트에 합성 입력을 넣어 재현한 동작을 기준으로 수정했다.
- [zittenyetten/cofa-probe-lite · b2f4e4a](https://github.com/zittenyetten/cofa-probe-lite/tree/b2f4e4a46574f90f556fd43a4c0f691e3242b37d), [ApexIllumination/cofa-devdominics-revised · af873b8](https://github.com/ApexIllumination/cofa-devdominics-revised/tree/af873b8ff1d85034d480b4c5a241406ab7b11c53): 정정 원문 누적, 충돌의 대상·판본·결정 권한 확인.
- [PKJthecreator/probe-kit · 0707ae3](https://github.com/PKJthecreator/probe-kit/tree/0707ae3a6e50c442374eb6fdbda606e0c645134f), [aeginventor/work-kit · caeba09](https://github.com/aeginventor/work-kit/tree/caeba091757ab3674ef1ae11af3b4b0ab71ff09a): CSV 구조 손실 검사, 실제 독립 검사기가 규칙 위반 복사본도 거절하는지 확인. 공백·식별자·중복 처리 정책은 가져오지 않는다.
- [wonjangchoi/kit · d71f0cb](https://github.com/wonjangchoi/kit/tree/d71f0cbf51c6fa19835e879e57a9336627c13208), [hyeongus2/codex-kit · 54f12ef](https://github.com/hyeongus2/codex-kit/tree/54f12ef2df1880422b12213b342d870e8b78e6ce): 공유 변경 전 복구 기준·범위, 다른 작업자의 변경 보존.
- [MIIXmix/cofa-kit · 4d0d2fa](https://github.com/MIIXmix/cofa-kit/tree/4d0d2fa5190350749818491b761f58c564669ffb), [taehyeong51/26_skhynix_hackerthon · 7e2d90a](https://github.com/taehyeong51/26_skhynix_hackerthon/tree/7e2d90a5b75f7d08d00bf51c0e62e7202a47d35a): 실제 배치와 API 요청 주소 대조, 핵심 화면의 상태·입력 유지·실패 뒤 다음 행동 확인.

이 참고 목록은 공식 평가 배점·실환경 호환성·복구 성공·접근성 인증을 보증하지 않는다. 일반 운영 지침의 적용과 실제 고객 기능 검증 결과를 구분한다.
