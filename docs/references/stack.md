# 기본 스택과 실행

새 웹 앱을 배치하거나 DB·컨테이너를 다룰 때 읽는다. 기본은 **Next.js App Router·React·TypeScript·Tailwind CSS·shadcn/ui·PostgreSQL**이다. 공식 과제가 지정한 스택·DB·버전·제출 위치와 기존 프로젝트가 우선이다. 이전 시험의 DB·Docker 조건을 이번 과제의 확정 조건으로 기록하지 않는다.

## 준비한 범위

준비 레포의 `starters/nextjs/`는 빈 앱·공통 UI 부품, 실제 DB 연결을 확인하는 `/api/health`, 자동 검사와 Docker 설정만 포함한다. 고객 데이터·업무 화면·업무 테이블·완성 답안은 없다. 자료 import, 스키마 변경 이력, 업무 데이터 저장·조회는 고객의 실제 R/Q/D에 따라 구현한다.

Next.js·React·Tailwind와 개발 도구는 `package.json`의 정확한 버전 및 `package-lock.json`으로 고정한다. 시험 당일 `latest`를 다시 선택하지 않고 `npm ci`로 설치한다. DB는 PostgreSQL 18 계열의 고정한 공식 이미지가 기본이다. DB 연결 라이브러리는 `pg`이며 서버 코드에서만 `DATABASE_URL`을 읽는다. 고객 입력은 SQL 문자열에 이어 붙이지 않고 매개변수로 전달한다. 여러 변경을 함께 성공·실패시켜야 하면 같은 DB 연결의 트랜잭션을 사용한다. 이 구성이 모든 과제에 ORM이나 특정 업무 정책을 요구하지는 않는다.

검사 도구의 호환 설정도 잠금 파일대로 유지한다. 현재 스타터는 TypeScript 7 검사기와, 린트 도구가 사용하는 TypeScript 6 API를 공식 병행 설치 방식으로 고정했다. 해당 버전과 Node 요구 범위는 `package.json`을 확인하며 당일에 한쪽만 임의 갱신하지 않는다. 제공 Node가 범위를 만족하는지와 `npm ci`·타입·lint·빌드의 실제 성공을 함께 확인한다.

## 배치 전 확인

- 제공된 앱·패키지·Docker 설정이 있으면 그것부터 읽는다. 새 스타터로 교체하지 않는다.
- `node --version`, `npm --version`, 허용된 패키지·이미지 다운로드와 실제 포트를 확인한다. Next.js 자체의 최소 Node는 20.9이며 스타터는 Node 22 계열로 준비한다. 제공 환경이 맞지 않으면 전역 업데이트나 제한 우회를 강제하지 않는다.
- Docker를 사용할 때 `docker version`과 `docker compose version`으로 CLI뿐 아니라 실행 엔진·권한을 확인한다. 실제 과제가 Docker를 필수로 지정했는데 사용할 수 없다면 관찰한 오류를 남기고 공식 문의 절차를 따른다. 다른 컨테이너·볼륨·설정은 건드리지 않는다.

## 화면 디자인의 기본

동봉한 shadcn/ui 컴포넌트 소스와 `components.json`, 공통 CSS 변수를 재사용한다. 같은 역할의 버튼·입력·카드·표·알림은 같은 부품과 테마를 사용하고, 색상·테두리·글자 크기·여백을 화면마다 제각각 정하지 않는다. 추가 부품이 필요하면 허용된 공개 원본에서 필요한 것만 가져오고 라이선스·정확한 의존성 버전·실제 파일을 확인한다. 준비된 부품을 당일 다시 생성하거나 전역 스킬·플러그인을 설치할 필요는 없다.

- **읽는 순서:** 화면 목적·현재 상태·가장 중요한 행동을 먼저 보여준다. 관련 입력·결과·설명은 묶고, 장식용 지표나 동작하지 않는 업무 버튼을 추가하지 않는다.
- **일관성:** 공통 테마의 배경·본문·주요 행동·경고 색과 일정한 간격을 사용한다. 긴 한국어·표의 긴 값도 잘리거나 겹치지 않게 처리한다. 외부 폰트 다운로드를 빌드·실행의 필수조건으로 두지 않는다.
- **상태와 피드백:** 해당 기능에 실제로 있는 빈 결과·처리 중·오류·저장 완료를 구분한다. 오류는 색만으로 표현하지 않고 문구와 실제 가능한 수정·재시도 행동을 함께 안내한다. 처리 중 기존 입력을 잃지 않게 한다.
- **조작:** 입력에는 보이는 이름을 붙이고 키보드 이동·포커스를 유지한다. 좁은 화면에서는 레이아웃을 조정하고, 큰 표는 읽을 수 있는 스크롤 영역을 사용한다.

이 기준은 기존 R·V의 최종 UI 목록에서 실제 핵심 흐름과 함께 확인한다. 새 디자인 승인 장부를 만들거나 모든 기능에 불필요한 상태를 추가하지 않는다. shadcn 사용·타입 검사·HTML 응답만으로 디자인·접근성·실제 조작을 검증했다고 쓰지 않는다.

## 새 앱을 시작하기

기존 앱이 없는 과제 작업 공간 루트에서 원래 준비 레포의 명령을 실행한다. `.hackathon/tools/kit.py`에는 스타터 소스가 동봉되지 않으므로 배치에 사용하지 않는다.

```sh
python3 .hackathon-kit/scripts/kit.py scaffold --workspace .
```

필요한 파일 목록만 복사하며 기존 README·AGENTS·요구 장부는 보존한다. 충돌이나 심볼릭 링크가 있으면 파일을 쓰기 전에 멈춘다. 기존 `.gitignore`에는 로컬 설정·의존성·빌드 결과 제외 규칙만 덧붙인다. 이미 추적된 비밀값은 ignore로 보호되지 않으므로 공개 전 따로 확인한다. 배치가 완료돼도 의존성 설치·DB 기동·기능 구현·검증이 완료된 것은 아니다.

환경값이 없을 때만 `.env.example`을 `.env`로 복사해 실제 로컬 설정을 채운다. 기존 `.env`를 덮어쓰지 않는다. `.env.example`의 값은 합성 연습용이며 실제 비밀값·고객 자료는 공개하지 않는다.

Docker가 허용되고 준비됐다면 과제 폴더에서 실행한다.

```sh
docker compose up --build -d
docker compose ps
```

Compose 안에서 앱은 서비스 이름 `db`로 DB에 연결한다. DB 포트를 호스트에 기본 공개하지 않는다. 앱 포트는 `.env`의 `APP_PORT`로 조정하고 실제 URL을 안내한다. DB가 요청을 받을 수 있는지 검사한 후 앱을 시작하며, 데이터는 별도 이름의 볼륨에 남긴다. PostgreSQL 18의 저장 경로는 이미지 설정을 따르며 이전 버전의 예시를 그대로 복사하지 않는다. 초기화 SQL은 새 볼륨을 만들 때만 실행된다. 기존 볼륨에 스키마를 바꾸려면 실제 마이그레이션을 작성하며 `down -v`로 자료를 지워 해결하지 않는다.

앱을 로컬 Node에서 개발하려면 `npm ci` 후 `DATABASE_URL`에 실제로 접속 가능한 PostgreSQL 주소를 지정하고 `npm run dev`를 실행한다. Compose의 `db` 주소는 호스트 Node에서 바로 사용할 수 없다. 이 방식이 필요할 때만 허용된 DB 접속 방식을 준비하고 두 환경의 주소를 구분한다. 컨테이너는 `0.0.0.0`에서 수신하고 제공 미리보기의 실제 포트·경로를 사용한다.

## 자동 검사와 실제 DB 확인

`npm run verify`는 타입·lint·단위/API 경계 검사·빌드를 실행하고 실패 코드를 반환한다. `npm test`는 Node TAP 출력을 사용한다. 기존 Evidence 도구의 `check --test-runner node -- npm test`로 실제 관련 R과 연결한다. 타입·lint·빌드는 기능 테스트 건수에 합치지 않고 별도 실행으로 기록한다. 초기 타입 생성이나 빌드로 소스가 바뀌면 현재 소스 기준의 관련 검증이 필요하며 과거 지문을 고쳐 통과로 만들지 않는다.

DB 통합 검사는 전용 `TEST_DATABASE_URL`이 있을 때만 실행한다. 앱 DB와 같은 주소를 사용하지 않으며 테스트가 만든 범위만 정리한다. 환경값이 없어 건너뛴 DB 검사는 미실행이다. 연결 대역을 쓴 단위 검사를 실제 PostgreSQL 성공으로 설명하지 않는다. `verify`가 정상 종료돼도 DB 검사가 skip이면 DB 검증은 남는다.

과제가 DB·Docker를 요구하면 실제 제품에서 다음 중 필요한 것을 확인하고 기존 V/R에 연결한다.

- 확인한 업무 조건에 맞는 테이블·키·필수값·제약과 스키마 변경 적용.
- 실제 API의 저장 → 재조회 → 같은 DB로 앱/컨테이너 재시작 → 재조회. 테스트가 소유한 DB·컨테이너·볼륨만 사용한다.
- 중복·동시 수정·오류·트랜잭션 실패에서 무엇이 저장되거나 되돌아가는지.
- 빈 DB에서 이미지 빌드·기동·초기화 후 고객의 필수 마지막 결과까지 이어지는지.

`/api/health`의 DB 연결 성공, 이미지 빌드, `compose ps`만으로 위 업무가 검증되지는 않는다. 연결 실패는 성공 상태로 숨기지 않고 실제 오류 범위·복구·남은 검증을 알린다. 브라우저 자동화는 하지 않으며 최종 실제 UI는 참가자가 확인한다.

## 공식 참고

- [Next.js 설치와 실행 조건](https://nextjs.org/docs/app/getting-started/installation)
- [Tailwind의 Next.js 설정](https://tailwindcss.com/docs/installation/framework-guides/nextjs)
- [shadcn/ui의 Next.js 설정](https://ui.shadcn.com/docs/installation/next) · [Tailwind v4 지원](https://ui.shadcn.com/docs/tailwind-v4)
- [PostgreSQL 지원 버전](https://www.postgresql.org/support/versioning/)
- [PostgreSQL 공식 Docker 이미지](https://hub.docker.com/_/postgres)
- [Compose의 DB 준비 상태 대기](https://docs.docker.com/compose/how-tos/startup-order/)
- [pg 매개변수 쿼리](https://node-postgres.com/features/queries) · [트랜잭션](https://node-postgres.com/features/transactions)
