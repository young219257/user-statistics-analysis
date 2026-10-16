# Design — 이용자통계분석 (교육데이터플랫폼 분석지원 메뉴)

교육데이터플랫폼(www.edmgr.kr) 포털 안의 한 메뉴를 고도화한 업무 도구다. 모든 화면은 이 파일을 기준으로
수정한다. 화면마다 따로 색·글꼴·모양을 정하지 않는다.

## Genre
modern-minimal (공공 포털 업무 도구). 장식보다 기능, 정보 밀도는 높게, 색은 절제.

## Macrostructure family
- 앱 화면(1~5단계): **Workbench** — 포털 헤더 · 위치 표시 · 페이지 제목 · 단계 바(고정) · 작업 영역 · 포털 하단.
  작업 영역은 섹션 카드를 세로로 쌓고, 섹션 안은 구분선과 간격으로 나눈다. 카드 안에 카드는 금지지만,
  서로 병렬인 항목 묶음(2단계 통계 지표 5칸·전처리 규칙 4칸, 4-1 분석 기법, 이상치 알고리즘)은 항목 카드
  (`rounded-xl border-rule bg-paper-3`, 칸 사이 간격 12~16px)로 구분한다. 선택된 항목은 brand 테두리·brand-soft 바탕.
- 헤더·하단은 포털과 동일하게 유지하며 이 시스템의 재디자인 대상이 아니다.

## Theme (토큰 · `static/css/app.css` :root, Tailwind 이름은 `layout/top.jsp` @theme)
| 토큰 | 값 | Tailwind | 용도 |
|---|---|---|---|
| `--color-brand` | #1e2c5d | `brand` | 주 행동 버튼, 현재 단계, 선택 상태 |
| `--color-brand-dark` | #151f42 | `brand-dark` | 주 버튼 hover |
| `--color-brand-soft` | #eef2fe | `brand-soft` | 선택된 항목 배경 |
| `--color-link` | #256ef4 | `link` | 링크·보조 강조 (blue-* 계열 전체가 이 색상 축으로 매핑됨) |
| `--color-ink` | #1e2124 | `ink` | 제목·본문 |
| `--color-ink-2` | #464c53 | `ink-2` | 보조 본문 |
| `--color-ink-3` | #6d7882 | `ink-3` | 설명·캡션 |
| `--color-ink-4` | #8a949e | `ink-4` | 비활성 |
| `--color-rule` | #dfe3eb | `rule` | 구분선 |
| `--color-paper` | #ffffff | — | 바탕 |
| `--color-paper-2` | #f1f3f5 | `paper-2` | 하단·hover 바탕 |
| `--color-focus` | #256ef4 | — | 키보드 포커스 링 |
| `--color-chart-1…6` | link · rose · emerald · amber · brand · ink-4 | — | 차트 계열색 (`App.tok('chart-n')`) |
- 상태색은 세 가지만: 성공 emerald, 경고 amber, 오류 rose. violet·indigo·purple·teal 은 brand/link 축으로 매핑.
- 코드에서는 중립색을 토큰 이름으로 쓴다 (`text-ink-3`, `border-rule`, `bg-paper-2` …). 옛 `slate-*`·`gray-*` 는 같은 단계로
  매핑되어 있어 남아 있어도 같은 색이지만 새 코드에는 쓰지 않는다. 파랑 계열은 `blue-*` 하나만 쓴다(indigo·violet·purple·teal 금지).
- 중립색 단계: Tailwind `slate-*`·`gray-*` 는 ink·rule·paper 단계로 매핑되어 있다 (50 paper-3 · 100 paper-2 · 200 rule ·
  300 rule-3 · 400 ink-4 · 500 ink-3 · 600 ink-2 · 700 ink-1 · 800 ink-0 · 900 ink · 950 ink-deep).
- 화면 코드에 hex 를 직접 쓰지 않는다. 필요한 색은 토큰을 먼저 추가한다. 클래스를 못 쓰는 곳(Highcharts 옵션 등)은
  `App.tok('ink-3')` 으로 토큰 값을 읽는다.

## Typography
- 글꼴: Pretendard 하나 (포털과 동일). 숫자는 `tabular-nums` (고정폭 글꼴 대신). 코드·JSON 만 고정폭.
- 크기 단계: 11(배지 전용) · 12(캡션 `text-xs`) · 13.5(본문·표 `text-body`) · 15(카드 제목 `text-title`) · 17 ·
  24(단계 제목) · 40(페이지 제목) px. 카드 제목은 `text-title font-semibold text-ink`, 앞에 장식 아이콘을 두지 않는다.
  9·10px 금지. 제목은 항상 정체(roman), 기울임 금지.

## Shape
- 모서리: 6px(입력·작은 버튼) · 10px(카드·큰 버튼) · 원형(배지·단계 원). 그 외 값 쓰지 않음.
- 그림자: 카드는 1px 테두리만. 그림자는 떠 있는 요소(메뉴·모달·토스트)에만.

## Motion
- 색·투명도만 전환 (`transition-colors`), `transition-all` 금지. 깜빡임(pulse) 장식 금지.
- `prefers-reduced-motion` 에서 전환 제거.

## Microinteractions stance
- 화면에 결과가 바로 보이는 동작은 알림 없이 처리 (silent success). 알림은 실패·보이지 않는 결과에만.
- 서버 오류는 해당 영역 바로 아래에 표시 (`App.fail(msg, anchor)`, 토스트 금지). 되돌릴 수 없는 삭제만
  확인을 받는다 (`App.confirm(msg)` — 포털 모달 모양, 브라우저 기본 확인창 금지).
- 겹침 순서: 헤더·메뉴·모달·토스트 모두 `z-50` 하나, 나중에 놓인 요소가 위.
- 클릭 가능한 요소는 모두 키보드로 조작 가능 (`button` 또는 `role="button"` + `tabindex="0"` + Enter/Space).
- 키보드 포커스 링은 즉시 표시 (2px `--color-focus`, offset 2px).

## CTA voice
- 주 행동: `brand` 채움, 10px 모서리, 한 줄(줄바꿈 금지), 화살표 아이콘은 다음 단계 이동에만.
- 보조 행동: 흰 바탕 + `rule` 테두리.

## What pages MUST share
포털 헤더·하단, 단계 바, 위 토큰·글꼴 크기·모서리·버튼 모양.

## Accessibility
- 모든 입력창·선택창에 이름이 있어야 한다: `<label for>` 로 연결하거나 `aria-label`. placeholder 는 이름이 아니다.
- 버튼 글자는 `text-body`(13.5px) 이상. 12px(`text-xs`)는 캡션·배지·표 머리용.
- 카드·섹션 제목 앞에 장식 아이콘·점을 두지 않는다 (상태 경고 아이콘만 예외).

## Copy
지어낸 수치·기능·계정 금지. 도움말은 실제 기능과 서버 제한값(`/api/v1/datasets/meta/limits`) 기준.
