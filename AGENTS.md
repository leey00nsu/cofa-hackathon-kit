# Scope

이 저장소는 대회 전 공개 준비물이다. 실제 과제·고객 사실·테스트 결과·최종 답안을 미리 만들어 넣지 않는다.

작업 전에 `docs/OPERATING_RULES.md`를 읽는다. 필요한 스킬만 사용한다. `vendor/`는 고정 원본이며 수정 시 출처와 해시를 갱신한다. 제공된 Codex를 업데이트하거나 외부 모델을 연결하는 설치 흐름을 추가하지 않는다.

준비 도구를 바꾸면 `python3 -m unittest discover -s tests -v`와 `python3 scripts/kit.py verify-vendor`로 확인한다. 브라우저 자동 조작은 사용하지 않는다.

당일 작업 공간에 적용할 지시는 `scripts/kit.py install`이 별도로 추가한다. 공식 과제 README는 보존한다.
