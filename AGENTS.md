# Scope

이 저장소는 대회 전 공개 준비물이다. 실제 과제·고객 사실·테스트 결과·최종 답안을 미리 만들어 넣지 않는다.

작업 전에 당일 개발 규칙의 정본인 `templates/AGENTS.md`를 읽는다. 필요한 스킬만 사용한다. `vendor/`는 고정 원본이며 수정 시 출처와 해시를 갱신한다. 제공된 Codex를 업데이트하거나 외부 모델을 연결하는 설치 흐름을 추가하지 않는다.

준비 도구를 바꾸면 `python3 -m unittest discover -s tests -v`와 `python3 scripts/kit.py verify-vendor`로 확인한다. 브라우저 자동 조작은 사용하지 않는다.

당일 작업 공간에 적용할 지시는 `scripts/kit.py install`이 `templates/AGENTS.md`에서 읽어 기존 AGENTS에 추가한다. 공식 과제 README는 보존한다. 시작·인터뷰·자동 검증 안내만 `.hackathon/` 상위에 배치하고 상세 명령과 문답 규약은 필요한 단계에서 참조한다. 공개 전 관리 절차는 `maintainers/PUBLISH_REVIEW.md`에 둔다.

Evidence Tracking은 `templates/AGENTS.md`와 기존 장부 양식을 따른다. 준비 키트에는 일반 규칙·빈 양식·명시적인 가상 예시만 넣는다. 실제 고객 답변·프로젝트 요구·실행 로그는 이 저장소에 복사하지 않는다. Matt 원본 SKILL.md는 수정하지 않고 프로젝트 AGENTS 규칙으로 R→Q/D→구현 파일→V/실행 결과를 연결한다. 문서 작성을 공식 점수의 근거로 주장하지 않는다. 공개 생성·Push에는 사용자의 별도 승인이 필요하다.
