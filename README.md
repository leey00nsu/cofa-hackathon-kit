# Cofa Hackathon Kit

공개 자료를 가져와, 제공된 Codex로 고객 요구를 발견하고 구현·검증한 뒤 **제출 전에 실제 구현의 예상 문답까지 복습**하는 준비물입니다. 문제별 제품 코드나 완성 답안은 포함하지 않습니다.

## 당일: 기존 작업 공간에서 시작

공식 README와 제공 파일을 먼저 확인합니다. 작업 공간의 최상위 디렉터리에서 실행하세요. 준비 레포는 하위 폴더로 가져오며 공식 README를 덮어쓰지 않습니다.

```sh
git clone https://github.com/leey00nsu/cofa-hackathon-kit.git .hackathon-kit
python3 .hackathon-kit/scripts/kit.py install --workspace .
codex
```

설치에는 Python 3.10 이상이 필요합니다. 설치기는 네트워크 요청·패키지 설치·Codex 업데이트를 하지 않습니다. 이미 제공된 Python이 없다면 `.hackathon-kit/docs/START_PROMPT.md`와 `docs/OPERATING_RULES.md`를 Codex에게 직접 읽게 하고, 필요한 문서·스킬을 제공된 환경에서 배치하게 하세요. Python 설치나 플랫폼 변경을 강제하지 않습니다.

Codex에서 `.hackathon/START_PROMPT.md`의 지시로 시작하세요. 이미 Codex가 실행 중이면 새 세션을 시작하거나 새 운영 지시를 명시적으로 읽게 합니다. `/status`, `/model`, `/skills`의 실제 지원 여부와 모델 표기는 제공된 환경에서 확인합니다. 선택은 참가 안내의 허용 모델 중에서 합니다.

설치기는 다음을 준비합니다.

- 기존 `AGENTS.md`에 짧은 운영 지시를 추가합니다. 기존 내용은 보존합니다.
- `.hackathon/`에 요구사항·결정·검증 장부와 시작/마무리 지시를 배치합니다.
- `.agents/skills/`에 Matt Pocock의 engineering/productivity 스킬과 `implementation-brief`를 배치합니다.
- `docs/agents/`에 로컬 Markdown 트래커와 용어 문서 위치를 설정합니다. 기존 파일과 충돌하면 **어떤 파일도 쓰기 전에 중단**합니다.

Matt 전체 원본은 `vendor/matt-pocock-skills/`에 고정돼 있습니다. 기본 설치는 engineering/productivity 영역이고 `--matt core`는 필요한 10개만, `--matt none`은 새 문답 스킬만 배치합니다. Claude 전용·실험 중 스킬도 원본에는 보존하지만 기본 활성화하지 않습니다. 원본 `setup`을 다시 실행할 필요가 없습니다. 추적 방식은 로컬 Markdown으로 이미 정했습니다.

## 구현 중

고객에게 전달할 질문 1~3개 → 답변 근거 기록 → 작동하는 작은 흐름 → 실행·검증 → 다음 질문 순서로 진행합니다. 기술적 선택은 Codex가 제안하고 참가자가 판단합니다. 업무 사실을 임의로 확정하지 않습니다.

실행한 테스트를 기록하려면 다음처럼 명령을 전달합니다. 명령은 셸이 아닌 인자 목록으로 실행되며, 종료 코드와 출력이 작업 공간 안에 저장됩니다.

```sh
python3 .hackathon/tools/kit.py check --workspace . --id build -- npm run build
python3 .hackathon/tools/kit.py check --workspace . --id tests -- npm test
```

위 명령은 예시입니다. 실제 프로젝트의 명령을 사용하세요. Browser에서의 버튼·화면 확인은 참가자가 직접 수행하고 검증 장부에 별도로 남깁니다. 이 도구는 Computer Use나 브라우저 자동 조작을 실행하지 않습니다.

## 구현 완료: 예상 문답과 복습본까지

**작업 시작 후 약 145~155분에는 마무리로 전환**합니다. 기능을 더 넣기 전에 `.hackathon/FINISH_PROMPT.md`를 실행하거나 `$implementation-brief`를 호출하세요. Codex가 실제 파일·고객 근거·테스트 기록을 읽고 다음을 작성합니다.

| 파일 | 역할 |
| --- | --- |
| `.hackathon/study/qa.json` | 핵심 6개 + 필요할 때 추가 6개까지의 예상 질문·답변·근거 |
| `.hackathon/study/IMPLEMENTATION_QA.md` | 상세 문답, 실제 파일·행, 실행 기록, 한계 |
| `.hackathon/study/LAST_REVIEW.md` | 핵심 6개 짧은 답변을 모은 마지막 복습본 |

답변은 아직 공개되지 않은 실제 서술형 문항을 예측·보장하지 않습니다. **당일 구현을 끝낸 뒤 만들어지는 학습 자료**입니다. 빈 답변을 완성본으로 취급하지 않습니다. 코드나 근거 문서가 바뀌면 검사에서 오래된 문답을 차단하고 Codex가 내용을 다시 검토해야 합니다.

```sh
python3 .hackathon/tools/kit.py verify-qa --workspace .
```

이 검사는 파일 지문·근거 경로·행의 인용과 체크 기록의 구조를 검증합니다. 자연어 답변의 사실 여부나 참가자의 이해도는 보장하지 않습니다. 참가자가 핵심 답변을 자신의 말로 설명해 확인해야 합니다.

## 시간과 응시 경계

참가자 안내 기준: 2026-10-31 10:00~14:00 KST, 과제 최대 180분, 후속 서술형 6문항·각 5분. 문항 준비 대기는 전체 종료 시각에 포함됩니다. **14:00은 절대 종료이고 4시간 전체가 구현 시간은 아닙니다.**

예상 문답은 과제풀이 단계에서 생성·복습을 마칩니다. 제출물 확정 이후에는 AI 작업을 중단합니다. 서술형 중에는 AI·복사·붙여넣기가 금지됩니다. 그 단계에서 노트나 코드 열람이 가능한지는 제공된 화면과 운영 안내로 확인하며, 열람 가능을 전제로 준비하지 않습니다. 준비 대기를 복습 시간으로 간주하지 않습니다.

공개 자료의 Clone·다운로드와 시험 중 Git Push는 구분합니다. 당일에는 GitHub 로그인·포크·Push·외부 전송을 하지 않습니다. 공개 자료는 플랫폼 안의 Codex를 통해 가져오고 사용합니다. 개인 PC 파일 업로드, 개인 API 키·구독 연결, 외부 AI, Astra, Codex 업데이트, Computer Use, 플랫폼 제한 우회는 준비 흐름에 포함하지 않습니다.

이 레포는 2차 예선 결과 통지 전까지 Public을 유지합니다. 운영 안내와 과제 README가 이 준비물보다 우선합니다. 공식 PDF·개인 응시 링크·신분 정보·과제 데이터·실제 답안은 이 공개 레포에 올리지 않습니다.

## 사전 체험과 검증

- [15분 사전 체험 체크리스트](docs/PREVIEW_15_MIN.md)
- [180분 작업 운영](docs/TIMEBOX.md)
- [운영 규칙과 출처](docs/OPERATING_RULES.md)
- [스킬 사용법](docs/SKILLS.md)
- [상태·생성 파일 정의](docs/QA_CONTRACT.md)

준비 도구 자체의 검증:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/kit.py verify-vendor
```

라이선스: 자체 코드는 MIT, Matt 원본은 별도 MIT 저작권과 고정 커밋을 보존합니다. [출처](THIRD_PARTY.md)를 확인하세요.
