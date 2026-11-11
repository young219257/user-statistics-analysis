# 교육데이터 이용자통계분석 서비스 (Spring 4 / JSP)

교육데이터플랫폼(www.edmgr.kr) **분석지원 > 이용자 통계분석** 메뉴를 고도화한 웹 서비스입니다.
외부 통계분석 API(`/api/v1/**`, FastAPI · OpenAPI 3.1)를 프록시로 연결하고, 화면(JSP + 바닐라 JS)이 그 API 를 직접 호출합니다.
Java 7 · Spring MVC 4.3 (Spring Boot 아님) · WAR 배포 · Tailwind(브라우저 빌드) · Highcharts · Lucide.

> 폐쇄망 배포를 전제로 화면에 쓰는 라이브러리(Tailwind, Highcharts, Lucide)와 포털 아이콘·이미지는 모두 `static/vendor/` 에 들어 있습니다.
> (예외: 글꼴 Pretendard 만 CDN 링크이며, 없으면 맑은 고딕 등 시스템 글꼴로 대체됩니다.)

## 목차
1. [구조](#구조) · 2. [설정·빌드](#설정빌드) · 3. [요청 흐름](#요청-흐름) · 4. [클라이언트 공통 동작](#클라이언트-공통-동작)
5. [단계별 화면 — API 와 화면 제어](#단계별-화면--api-와-화면-제어) · 6. [화면 간 상태](#화면-간-상태) · 7. [API 전체 목록](#api-전체-목록)
8. [PDF / Excel 내보내기](#pdf--excel-내보내기) · 9. [디자인 시스템](#디자인-시스템) · 10. [알려진 제한·주의](#알려진-제한주의)

---

## 구조
```
src/main/java/kr/or/keris/statistics/
  ApiProxyController  /api/v1/**, /health → 외부 API 로 그대로 전달 (요청 메서드·본문·쿼리 유지, PATCH·multipart 지원)
  BasePathFilter      리버스 프록시 하위 경로(APP_BASE_PATH) 제거 후 forward
  Upstream            외부 API 호출 공통 클라이언트 (프록시·내보내기가 공유, Apache HttpClient)
  ExportController    PDF / Excel 내보내기 (외부 API 에 없는 기능 → 이 서버에서 직접 생성). 화면이 4-2 결과 화면에서 읽어 보낸 내용(`screens`)으로 만들고, 없으면 API 응답을 표로 옮기는 예전 방식으로 대체
  export/             Report(문서 모델: 키-값·표 + 화면형 구역 `Screen`) · ReportBuilder(화면 내용/JSON→문서) · PdfExporter(iText 2.1.7) · ExcelExporter(POI 3.17) · FontResolver
  PageController      JSP 6개 화면 (step1~5, step4/report) — 데이터는 화면 JS 가 /api/v1 을 직접 호출
  Config              환경변수 → -D 시스템 프로퍼티 순으로 설정 읽기
src/main/webapp/WEB-INF/
  web.xml, dispatcher-servlet.xml
  views/layout/top.jsp      포털 헤더·위치 표시·페이지 제목·5단계 진행 바 + 디자인 토큰(Tailwind @theme)
  views/layout/bottom.jsp   포털 하단 + 도움말·로그인 안내·삭제 확인 모달 + 토스트
  views/ot_dim_dmmbm03_m01.jsp … m06.jsp
      m01 1단계 데이터 반입 · m02 2단계 품질 및 전처리 · m03 3단계 데이터 탐색 · m04 4-1 모형 설정·실행 · m05 4-2 분석 결과 리포트 · m06 5단계 결과 관리
src/main/webapp/static/
  css/app.css               디자인 토큰(:root) · 공통 규칙(포커스 링·표 숫자·움직임 줄이기)
  js/common.js              세션·API 클라이언트·백그라운드 작업 대기·오류/확인 창·헤더 메뉴
  js/ot_dim_dmmbm03_m01.js … ot_dim_dmmbm03_m06.js    단계별 화면 로직,  ot_dim_dmmbm03_m05.js(4-2)  charts.js(추천 차트)  viz.js(표·트리·지표 공용 렌더러)
  vendor/                   Tailwind·Highcharts·Lucide·포털 아이콘 (폐쇄망용)
design.md                   디자인 시스템 기준 (색·글자·모서리·알림·접근성 규칙) — 화면 수정 시 이 문서를 따른다
```

## 설정·빌드

### 환경변수 (또는 -D 옵션)
| 이름 | 기본값 | 설명 |
|---|---|---|
| `UPSTREAM_API_BASE` | `https://testlab-edmgr.kr/apps/rest-api` | 프록시 대상 (외부 API 기준 주소) |
| `APP_BASE_PATH` | (없음) | 리버스 프록시가 붙이는 하위 경로. 예: `/apps/9`. `X-Forwarded-Prefix` 헤더가 있으면 그 값이 우선 |
| `PDF_FONT_PATH` | (없음) | PDF 한글 글꼴 파일(.ttf/.ttc). 아래 [PDF / Excel](#pdf--excel-내보내기) 참고 |

Tomcat 에서는 `bin/setenv.sh` 에 `export UPSTREAM_API_BASE=...` 또는 `JAVA_OPTS="-DUPSTREAM_API_BASE=..."` 로 지정합니다.

### 빌드
```bash
mvn clean package            # → target/app.war  (JDK 7 + Maven 3.x 필요)
```
JDK 8 이상에서 컴파일만 확인하려면: `mvn -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 clean package`

### 로컬 개발
* Tomcat 의 docBase 가 `target/app` 이면 `src/main/webapp` 을 `target/app` 에 복사(rsync)하는 것만으로 JSP·JS·CSS 변경이 반영됩니다 (Java 변경은 재빌드).
* 외부 API 는 파이썬 백엔드(FastAPI) 를 `UPSTREAM_API_BASE` 로 가리키면 됩니다. 백엔드에서 `uvicorn app.main:app --reload` 로 띄웁니다.
  (`USA_CELERY_TASK_ALWAYS_EAGER=true` 로 브로커 없이 쓰는 경우, `fastapi dev` 는 이 설정을 무시하고 큐에 연결하려다 503 이 나므로 uvicorn 을 쓰세요.)
* 정적 파일에는 캐시 무효화 파라미터를 붙이지 않았습니다. 수정 후에는 브라우저에서 강력 새로고침(Cmd/Ctrl+Shift+R)이 필요합니다.

---

## 요청 흐름
```
브라우저 ──▶ Tomcat(JSP 화면, /static/**)
   │
   └─ fetch('/api/v1/...')  X-Session-Token 헤더 ──▶ ApiProxyController ──▶ UPSTREAM_API_BASE/api/v1/...
```
* 프록시는 경로·쿼리·메서드·본문(JSON, multipart)을 그대로 넘기고, 다음 헤더만 전달합니다.
  * 요청: `X-Session-Id`, `X-Session-Token`, `Authorization`, 접근 쿠키(`keris_testlab_access`)
  * 응답: `Content-Type`, `Content-Disposition`, **`Retry-After`**(작업 재조회 간격), **`Location`**, 상태 코드
* 화면 JSP 는 데이터를 담지 않습니다. `PageController` 는 뷰 이름과 하위 경로(`ctx`), 현재 단계(`activeStep`/`subTab`), 제목만 모델에 담습니다.
* 화면 URL: `/analysis/step1` ~ `/analysis/step5`, `/analysis/step4/report`(4-2, `?id=<분석ID>` 로 특정 분석 표시). `/` 와 `/analysis` 는 step1 로 이동.

---

## 클라이언트 공통 동작 (`common.js`)

### 세션
* 첫 API 호출 때 `POST /api/v1/sessions` 로 토큰을 발급받아 **쿠키 `edu.sessionToken`**(`{token, header}` JSON, 세션 쿠키·`SameSite=Lax`)에 보관하고, 모든 호출에 `X-Session-Token` 헤더로 보냅니다. 쿠키는 브라우저 전체가 공유하므로 같은 브라우저의 다른 탭도 같은 세션을 씁니다.
* **5분마다** `POST /sessions/current/heartbeat` 로 세션을 연장합니다. 서버는 마지막 요청 1시간 뒤 세션과 데이터(데이터셋·분석)를 삭제합니다 (공유 중인 패키지는 7일 유지).
* 응답이 **401** 이면 토큰을 다시 발급받아(이전 데이터는 서버에서 삭제된 상태 → 화면 상태도 초기화) **요청을 한 번 다시 보냅니다.** 안내 문구는 띄우지 않습니다.
* 선택한 데이터셋을 더 이상 찾을 수 없으면(404/401, `App.datasetGone`) 상태를 비우고 1단계로 보내며 "선택한 데이터셋을 찾을 수 없습니다. 다시 선택해 주세요." 를 1단계 맨 위에 표시합니다.

### API 클라이언트
| 함수 | 설명 |
|---|---|
| `App.get/post/patch/del(url, body, opts)` | JSON 호출. 응답 본문이 JSON 이면 파싱해 돌려주고, 오류면 `Error(message, status)` 로 reject. 메시지는 `detail`(문자열·검증 오류 배열) → `message` → 상태 코드 순으로 만든다 |
| `App.api(method, url, FormData)` | 파일 업로드(multipart) |
| `opts.onJob(job)` | 백그라운드 작업 상태를 조회할 때마다 호출 (진행 표시용) |
| `App.downloadFile(method, url, body, 파일명)` | 서버가 만든 파일(PDF/Excel)을 토큰 헤더 포함 fetch → Blob → 저장. `Content-Disposition` 의 파일명을 우선 사용 |
| `App.qs({a:1,b:[2,3]})` | 쿼리스트링 조립 (빈 값·null 은 생략) |

### 백그라운드 작업 (202 Accepted + JobRead)
업로드·결합·변수 선택(subset)·변수 타입 변경(카드)·전처리·분석·카드 동기화·프로파일 등은 서버가 큐에서 처리하며 `202` 와 작업(`JobRead`)을 돌려줍니다. 클라이언트는 **호출부가 결과만 받도록** 이를 자동으로 기다립니다.
* `GET /api/v1/jobs/{id}`(`status_url`)를 응답의 **`Retry-After` 초 간격(헤더가 없으면 1초, 최대 10초)** 으로 조회하고, **최대 30분** 기다립니다.
* 상태 흐름: `queued`(세션 대기열 예약, `queue_position`) → `pending`(워커 대기) → `running` → `succeeded` / `failed` / `cancelled`.
  화면에는 `App.jobText(job)` 로 "대기열에서 차례를 기다리는 중 (N번째)" · "처리 서버 배정을 기다리는 중" · "처리 중" 을 보여줍니다.
* 성공하면 `result` → `result_url` → `resource_type/resource_id`(dataset·analysis) 순으로 결과를 읽어 돌려줍니다.
* **분석**(`kind=analysis`)이 `failed`/`cancelled` 로 끝나면 오류를 던지지 않고 **분석 레코드(상태·오류 사유 포함)를 돌려줘** 4-1 화면이 결과 패널에 사유를 보여줍니다. 그 밖의 작업은 `Error`(`code`, `job`)로 reject 합니다.
* 탐색 GET(`profile`, `outliers`, `correlation`)이 202 를 주면 작업이 끝난 뒤 같은 요청을 다시 보내 캐시된 200 응답을 받습니다.
* 서버 거절(429 `too_busy`, 413 `job_too_large`, 503 `queue_unavailable` 등)은 서버 메시지를 그대로 해당 영역에 표시합니다.

### 알림 정책
| 도구 | 용도 |
|---|---|
| `App.fail(msg, anchor)` | **오류는 토스트 대신 문제가 난 영역 바로 아래**에 닫기 버튼과 함께 표시. `anchor` 가 없으면 본문 맨 위. `App.fail(null, anchor)` 로 지움 |
| `App.confirm(msg)` | 되돌릴 수 없는 삭제(데이터셋·패키지)에서만 쓰는 확인 모달 (Promise<boolean>). Esc·바깥 클릭은 취소, 닫히면 원래 위치로 포커스 복귀 |
| `App.toast(msg, kind)` | 완료·실패를 알리는 짧은 알림. 화면 오른쪽 중간쪽에 짙은 바탕·흰 글씨로 3초(실패는 5초, 빨간 점 표시). 결합 완료·분석 완료·결합 실패·분석 실패에 씁니다. 실패는 토스트와 함께 해당 영역 아래에 사유도 표시 |
| `App.tok('ink-3')` | CSS 색 토큰 값 읽기 (Highcharts 처럼 클래스를 못 쓰는 곳용) |

### 공통 UI
* **헤더·하단**은 포털과 같은 구성입니다. 주 메뉴·전체 메뉴(`PORTAL_MENUS`)는 포털의 5개 대메뉴를 그대로 옮긴 것이고, 현재 서비스는 `분석지원 > 이용자 통계분석`(`SELF_PATH`)입니다.
* **통합검색**: 입력한 검색어를 포털 `POST https://www.edmgr.kr/dtSearchResult` (필드 `queryNav`)로 제출합니다. 빈 검색어는 제출하지 않습니다.
* **5단계 진행 바**: 단계 링크로 자유롭게 이동할 수 있습니다(단, 2단계는 아래 조건 참고). 모바일(<768px)에서는 "STEP n / 5 + 진행 막대"로 접힙니다. 4단계에서는 "4-1 모형 설정·실행 / 4-2 분석 결과 리포트" 하위 탭이 보입니다.
* **도움말**(실제 기능·서버 제한 기준: 파일 최대 10MB, 세션 1시간, 공유 7일) 과 **로그인 안내**(계정은 포털에서) 모달.
* **키보드**: `role="button"` 인 div(카드·행·탭)는 `tabindex="0"` 이며 Enter/Space 가 click 으로 동작합니다. 포커스 링은 즉시 표시(2px)됩니다. 모든 입력창·선택창에는 `<label for>` 또는 `aria-label` 이 있습니다.

---

## 단계별 화면 — API 와 화면 제어

### 1단계 · 데이터 반입 (`ot_dim_dmmbm03_m01.js`)
**목적**: 분석할 데이터를 고르고(여러 개), 필요하면 결합합니다. 결과로 "분석 대상 데이터셋" 하나가 정해집니다.

| 영역 | API | 화면 제어 |
|---|---|---|
| 데이터관리카드 목록 | `GET /data-cards?limit=100&q=` | 검색어 입력 0.3초 뒤 재조회. **적재가 끝난 카드만** 표시하고(적재 중·실패는 목록과 "총 N건"에서 제외) 동기화 버튼은 없음 |
| 반입된 데이터셋 | `GET /datasets?source_type=upload` + `source_type=merged` | 두 목록을 합쳐 표시(결합 결과는 "결합" 배지, 크기 표시, 분석용 30MB 초과는 흐리게 "30MB 초과"). 목록 안에서 스크롤 |
| 파일 업로드 | `POST /datasets/upload` (multipart, 202 작업) | 클릭 또는 끌어다 놓기. **확장자(csv·txt·xlsx·xls·json·parquet)만 클라이언트에서 검사**, 용량 등은 서버가 거절(메시지 표시). 업로드 중 "파일을 분석하고 있습니다… (대기 순번)" 표시, 완료되면 목록을 갱신하고 **자동 선택** |
| 데이터셋 삭제 | `DELETE /datasets/{id}` | 확인 모달 후 삭제. 선택 중이면 선택 해제, 결합 결과였다면 결합 상태 초기화 |
| 선택 | `GET /datasets/{id}` | 선택 규칙: **데이터관리카드는 최대 2개**, **반입 데이터셋은 분석·결합에 쓰는 합계 30MB 이하**(`size_bytes`, 결합 결과는 제한 없음). **결합된 데이터셋은 단독으로만** 선택: 결합 결과를 고르면 기존 선택이 해제되고, 결합 결과가 선택된 상태에서 다른 데이터를 고르면 결합 결과가 해제됨. 선택하면 상세(변수 목록)를 읽어 "선택한 데이터" 탭에 추가. 별칭(alias)은 데이터셋 이름 앞 14자(중복이면 `_2`…) |
| 선택한 데이터 | – | **선택 전에는 이 카드·미리보기·하단 "분석 투입 대상" 줄이 숨겨짐**. 탭을 눌러 데이터셋을 전환하고 ×로 선택 해제 |
| 변수 속성 | `PATCH /datasets/{id}/columns/types` | 변수마다 **[분석 사용] 체크**(전체 선택은 검색으로 걸러진 열만). 타입 선택창을 바꾸면 **즉시 서버에 저장**(저장 중에는 그 선택창 잠금)하고 응답(DatasetDetail)으로 표를 다시 그림. **데이터관리카드**는 서버가 카드를 건드리지 않고 "<카드명> (타입 변경)" **새 데이터셋을 만드는 작업(202)** 을 돌려주므로, 화면은 그 선택 항목을 새 데이터셋으로 갈아탑니다(탭 이름이 바뀌고 이후 단계는 새 데이터셋으로 진행, 카드 목록의 선택 표시는 유지). 오류는 카드 아래에 표시하고 원래 타입으로 되돌림. 결합 결과 탭은 읽기 전용 |
| 미리보기 | `GET /datasets/{id}/preview?limit=20&offset=` | 20행씩, 상자 맨 아래 50px 이내로 스크롤하면 다음 행을 이어서 조회. 분석에 쓰도록 체크한 열만 표시 |
| 데이터 결합 | `POST /datasets/merge` (202 작업) | 아래 "데이터 결합" 참고 |
| 2단계 진행 | `POST /datasets/{id}/subset` (일부 열만 쓸 때) | 아래 "분석 대상과 진행 조건" 참고 |

**데이터 결합 (2개 이상 선택 시 나타남)**
* 요청: `{ name, mode:'join', join_type, keys:[결과 키 이름…], sources:[{dataset_id, alias, key_map?, columns?}] }`
  * `keys` 는 **1번 데이터셋의 키 열 이름**. 다른 데이터셋의 키 열 이름이 다르면 `sources[i].key_map = {결과 키 이름: 그 데이터셋의 열}` 로 대응시킵니다.
  * 일부 열만 체크한 데이터셋은 `columns` 에 **체크한 열 + 키 열**만 보내 처리량을 줄입니다.
  * `join_type`: `inner`(키가 모두 있는 행만) · `left`(1번 유지) · `right`(마지막 유지) · `outer`(모두).
* 키 매핑 화면: 한 줄에 `[데이터셋1 키 열] = [데이터셋2 키 열]`, `[+ 키 추가]` 로 키를 늘리고 삭제할 수 있습니다. 키마다 모든 데이터셋의 열이 채워져야 유효합니다.
* **키 자동 추천**: 모든 데이터셋에 같은 이름으로 있는 열(식별자 우선), 없으면 데이터셋마다 식별자(identifier) 열이 **정확히 하나일 때** 그 열들을 짝지어 미리 선택합니다. 사용자가 바꿀 수 있습니다.
* 결합 실행 버튼은 **모든 선택 데이터에 쓸 열이 있고 유효한 키가 하나 이상일 때만** 활성입니다. 이유는 버튼 왼쪽에 표시됩니다. 일부 데이터셋만 키를 골랐을 때만 빈 칸이 노란 테두리로 강조됩니다.
* 진행 중에는 "결합하고 있습니다… (대기 순번/처리 중)" 을 표시합니다. 완료되면 "결합이 완료되었습니다." 토스트가 뜨고, **재료로 쓴 데이터의 선택은 풀리며 결합된 데이터셋 하나만 선택**되어 미리보기가 열립니다. 실패하면 토스트와 함께 결합 영역 아래에 **서버가 준 사유를 그대로**(닫기 버튼 포함) 표시합니다.
* **무효화(stale)**: 선택 데이터·체크한 열·키 매핑·옵션을 바꾸면(요청 본문이 달라지면) 이전 결과는 무효가 되어 분석 대상에서 빠지고 "다시 실행해 주세요" 안내가 표시됩니다.

**분석 대상과 진행 조건**
| 선택 상태 | 분석 대상 | [2단계 품질 및 전처리 진행] |
|---|---|---|
| 없음 | 없음 | 비활성 |
| 1개 | 그 데이터셋 | 활성. 일부 열만 쓰면 `POST /datasets/{id}/subset {columns}` (202 작업, "변수 선택 적용 중…")로 **그 열만 담은 새 데이터셋**을 만든 뒤 이동. 전부 쓰면 바로 이동 |
| 2개 이상 | 유효한 결합 결과 | 결합 전·결과가 무효가 되면 비활성 |

### 2단계 · 데이터 품질 및 전처리 (`ot_dim_dmmbm03_m02.js`)
| 동작 | API | 화면 제어 |
|---|---|---|
| 진입 | `GET /datasets/{id}` → `GET /datasets/{id}/profile?include_outliers=false` | 이상치 탐지 없이 기본 품질(행·변수, 결측, 중복 행)만 조회. 2단계는 항상 **원본 데이터셋**(`rawDatasetId`)을 기준으로 진단 |
| 탐지 실행 | `GET /datasets/{id}/outliers?method=&threshold=` | 이상치 기법 7종(`iqr`·`zscore`·`modified_zscore`·`grubbs`·`mahalanobis`·`isolation_forest`·`lof`) 카드에서 하나를 고르면 그 카드의 **임계값 선택창이 열림**(기본값 자동). 선택하지 않은 카드는 기본값만 글자로 표시. **[선택 기법으로 이상치 탐지 실행]은 프로파일 로드가 끝나고 기법을 선택했을 때만 활성**, 탐지 중에는 "알고리즘 연산 중…" |
| 결과 표시 | – | 품질 요약, 변수별 결측·이상치 개수·이상치 비율(%)·왜도와 **판정**(화면 기준: 이상치 비율 1% 미만 "확인 권장"·1% 이상 "검토 필요", \|왜도\|>1 "비대칭 분포"(최솟값>0이면 "로그 변환 권장"), 결측 있으면 "결측치 있음", 탐지 후 문제없으면 "양호"). 기준은 표 아래에 표시, 변수 행을 누르면 상세(최솟값~최댓값, 판정 경계, 검출된 표본)가 아래에 표시 |
| 전처리 규칙 | – | 카드 4개(결측치·이상치·스케일링·중복 행)에서 라디오로 선택. **기본값은 항목별 맨 위 옵션**(중앙값 대체 · 윈저라이징 · 표준화 · 유지). 선택값은 `sessionStorage` 에 보관 |
| 3단계 진행 | `POST /datasets/{id}/preprocess` | **이상치 탐지를 실행해 정상 응답을 받기 전에는 [3단계 데이터 탐색(EDA) 진행]이 비활성**(옆에 안내 문구)이고, **상단 단계 바로 3~4단계로 건너뛰는 클릭도 막혀 안내 오류가 표시**됩니다(**5단계 결과 관리는 탐지와 무관하게 이동 가능**). 활성이면: 결측치·이상치·스케일링 규칙이 모두 "처리 안 함/보존/미적용"이면 원본 그대로 이동, 아니면 규칙(+마지막으로 실행한 `outlier_method`/`outlier_threshold`)으로 **전처리된 새 데이터셋**을 만든 뒤 그 데이터셋으로 이동. 실패하면 버튼 위에 사유 표시 |

> 분석 실행(4-1)에 보내는 `PreprocessingSpec` 은 `{drop_duplicates, outlier_treatment:'keep', scaling:'none', encoding:'onehot'}` 입니다. 결측·이상치·스케일링은 위 `/preprocess` 로 이미 데이터셋에 적용했으므로 다시 적용하지 않고, 중복 행 제거와 범주형 인코딩만 분석 요청에서 지정합니다.

### 3단계 · 데이터 탐색 EDA (`ot_dim_dmmbm03_m03.js`)
| 동작 | API | 화면 제어 |
|---|---|---|
| 기초통계 | `GET /datasets/{id}/profile?include_outliers=false` | 전처리된 데이터셋의 수치형 변수별 N·평균·표준편차·사분위·왜도·첨도·결측률. 표 안에서 스크롤(머리행·변수명 열 고정) |
| 상관분석 | `GET /datasets/{id}/correlation?method=` | 방법 선택(피어슨·스피어만·켄달)을 바꾸면 다시 조회. 매트릭스(강도별 색)와 상위 10쌍(강도·유의확률) |

### 4-1 · 통계 모형 설정·실행 (`ot_dim_dmmbm03_m04.js`)
| 동작 | API | 화면 제어 |
|---|---|---|
| 진입 | `GET /datasets/{id}`, (이전 분석이 있으면) `GET /analyses/{id}`, `GET /methods` | 데이터셋 변수로 선택지를 만들고, 서버가 주는 기법 설명이 있으면 카드 설명을 보강(실패해도 내장 목록으로 동작) |
| 실행 | `POST /analyses` (202 작업) | 아래 요청 형식. 실행 중에는 버튼 비활성 |

**분석 기법 13종** (분류별 카드): 기초 — 상관분석 `correlation`, 주성분분석 `pca` · 예측 — 선형회귀 `linear_regression`, 로지스틱 회귀 `logistic_regression`, 의사결정나무(회귀/분류) `decision_tree_regressor/classifier` · 군집 — K-평균 `kmeans`, 계층적 `hierarchical`, `dbscan` · 고급 — 분산분석 `anova`, 다층모형 `multilevel`, 성장곡선 `growth_curve`, 성향점수매칭 `psm`.

**화면 제어 규칙**
* 기법을 고르면 종속변수·독립변수·파라미터 영역이 그 기법에 맞게 다시 구성됩니다. 종속변수가 필요한 기법이면 **첫 수치형 변수를 기본 종속변수**로, 독립변수는 **종속변수를 뺀 앞 4개 수치형 변수**를 기본 선택합니다 (전체선택/해제 가능, "N개 선택" 표시).
* 종속변수를 바꾸면 독립변수에서 자동으로 제외됩니다. 데이터셋에 없는 변수는 선택에서 제거됩니다.
* 파라미터(검증 비율, 절편, 양성 클래스, 가중치 변수, 최대 반복, 트리 깊이·리프 표본·가지치기, 군집 수·자동 탐색, 연결법, eps·min_samples, 성분 수, 요인·공변량, 집단·시간·처치 변수, 캘리퍼·이웃 수, 식별자 변수)는 기법별로 필요한 것만 보입니다.
* **검증(`validate`)**: 종속변수 필수 기법에서 미선택 / 독립변수 0개(ANOVA·성장곡선은 선택) / 필수 파라미터 미선택(다층모형 집단 변수, 성장곡선 시간 변수, PSM 처치 변수) / ANOVA 요인 0개 → 요청을 보내지 않고 결과 패널에 실패 사유를 표시합니다.
* 요청: `{ dataset_id, method, name: "<기법명> - <데이터셋명>", params:{ target?, features[], …기법별 }, preprocessing: <2단계 PreprocessingSpec> }`.
  `군집 수 자동 탐색`을 켜면 `auto_k_range:[2,8]` 을 보내고 `n_clusters` 는 생략합니다. 빈 값은 보내지 않습니다.
* **결과 표시**: 분석이 성공하면 "분석이 완료되었습니다." 토스트만 띄우고 결과 상자는 두지 않습니다. 실패·취소는 오류 사유를 빨간 글씨 한 줄(닫기 버튼 포함)로 표시하고 "분석에 실패했습니다." 토스트가 함께 뜹니다. 요청 전에는 안내 상자가 없습니다. **[4-2 분석 결과 보기]는 분석 완료(분석 상태 `succeeded` 또는 작업 `succeeded`)일 때만 활성**이고, 새 분석을 시작하면 다시 비활성이 됩니다. "분석 파이프라인 조건"(선택 모형·종속변수·투입 변수)은 접고 펼 수 있습니다.
* 설정(`config`)과 마지막 분석 ID 는 `sessionStorage` 에 보관해 4-2·5단계 "재현"에서 복원합니다.

### 4-2 · 분석 결과 리포트 (`ot_dim_dmmbm03_m05.js`, `charts.js`, `viz.js`)
| 동작 | API | 화면 제어 |
|---|---|---|
| 진입 | `GET /analyses/{id}` (`?id=` 없으면 마지막 분석) | 요약 카드 + 탭 4개 |
| 원시데이터 | `GET /datasets/{id}/preview?limit=200` | 상위 200행(분석 결과에 예측값·잔차가 있으면 열로 덧붙임), 검색어로 화면 필터. 실패해도 조용히 무시 |
| 결과 패키지 저장 | `POST /packages {name, description, analysis_ids:[id]}` | 성공하면 버튼이 "저장 완료"로 2.5초간 바뀜. 실패하면 버튼 옆에 오류 |

* **탭**: 전체 종합 리포트(결과표 + 추천 차트) · 표준 통계 결과표 · 진단 시각화 차트(추천 수) · 표본별 원시데이터 및 잔차(행 수).
* **표준 통계 결과표**: 기법별 SPSS 형식 표(선형회귀: 모형 요약·ANOVA·계수·적합도·진단 / 로지스틱 / 의사결정나무(트리 차트+노드 표) / 군집 / PCA / ANOVA / 다층·성장곡선 / PSM 등). 유의확률에는 `*` 표시를 위 첨자로 붙이고 표 아래에 별표 설명(`*. p < .05 …`)을 둡니다. **각주는 서버가 준 문구(`result.note`, `diagnostics.multicollinearity_warning`)만** 표시하며 화면이 임의로 쓴 설명·기준 판정(예: DW 1.5~2.5, VIF ≤ 10)은 넣지 않습니다. 서버가 true/false 로 준 판정(정규성·등분산성 등)만 문장으로 옮깁니다.
* **추천 차트**: 별도 API 없이 분석 응답의 `chart_recommendations`(종류·제목·사유·순위) + `chart_data` 를 Highcharts 로 그립니다. 데이터가 없는 추천은 "이 차트에 표시할 데이터가 없습니다."로 표시합니다. 카드를 누르면 **상세 보기**(차트 크게 + 이전/다음 + [차트 데이터 조회]로 원시 데이터 표 최대 1,000행).
* 분석이 실패한 결과는 요약 카드 대신 오류 사유를 표시합니다.

### 5단계 · 결과 관리 (`ot_dim_dmmbm03_m06.js`)
| 동작 | API | 화면 제어 |
|---|---|---|
| 목록 | `GET /packages?limit=100` | 첫 패키지를 자동 선택. 카드: 이름·분석 건수·"공유 중"·생성 일시 |
| 상세 | `GET /packages/{id}` | 매니페스트(분석 요약 지표·전처리·변수 설정)를 표시. 분석이 여러 개면 분석별 버튼으로 전환 |
| 회귀계수 표 | `GET /analyses/{id}` | 선택한 분석의 계수·표준오차·t/z·p·유의수준(`***`/`ns`)을 분석 상세에서 읽어 표시 |
| 삭제 | `DELETE /packages/{id}` | 확인 모달 후 삭제, 선택 중이면 다음 패키지 선택 |
| 공유 | `POST /packages/{id}/share` → `GET`, `DELETE /packages/{id}/share` | 공유 아이콘: 미발급이면 링크 발급, 발급됐으면 링크 영역 열고 닫기. 링크 = `<origin><ctx>/api/v1/shared/<token>`, [복사]는 클립보드(버튼이 "복사됨"으로 바뀜), [공유 해제] |
| 재현 | `GET /datasets/{원본id}` | 원본 데이터셋이 현재 세션에 남아 있으면 선택한 분석의 데이터셋·변수·파라미터·전처리를 `sessionStorage` 에 복원하고 **4-1 로 이동**(실행은 사용자가 직접). 없으면 "원본 데이터셋이 현재 세션에 없어 재현할 수 없습니다" 안내 |
| 내보내기 | `POST /export/package/{id}/pdf`, `…/excel` | 담긴 분석마다 `GET /analyses/{id}` 로 결과를 받아 **`ot_dim_dmmbm03_m05.js` 로 4-2 화면을 화면 밖에 그려** 표·지표·(PDF 는) 차트를 읽고 서버로 보내 파일을 만듭니다. [PDF 보고서]·[Excel 통계표] |

---

## 화면 간 상태
서버는 화면 상태를 갖지 않습니다. 브라우저 **탭의 `sessionStorage['edu.state']`** 에 보관합니다 (`App.state` / `App.saveState` / `App.resetState`).

| 키 | 쓰는 곳 | 의미 |
|---|---|---|
| `datasetId`, `datasetName`, `datasetRows` | 1·2단계 | **현재 분석 대상 데이터셋** (3·4단계는 이 데이터셋 사용). 1단계에서 결합 결과/단일 데이터셋/subset, 2단계에서 전처리 결과로 바뀜 |
| `rawDatasetId` | 2단계 | 전처리 전 원본 데이터셋. 2단계로 다시 오면 원본 기준으로 진단 |
| `usedColumns` | 1단계 | 항상 초기화(null) — 열 선택은 subset/merge 요청으로 서버에 반영 |
| `prepUi` | 2단계 | 전처리 카드 선택값(`prep`)과 마지막으로 실행한 탐지(`outlier`) |
| `preprocessing` | 2단계 → 4-1 | 분석 요청에 실을 `PreprocessingSpec` |
| `config` | 4-1, 5단계 재현 | 기법·종속변수·독립변수·파라미터 |
| `analysisId` | 4-1 → 4-2 | 마지막 분석 ID (데이터셋이 바뀌면 null) |

그 밖에 쿠키 `edu.sessionToken`(세션 토큰, 브라우저 공유), `sessionStorage['flashToast']`(페이지 이동 뒤 한 번 보여줄 안내), `localStorage['sbCollapsed']`(사용하지 않는 사이드바 접힘 값)가 있습니다. 탭을 새로 열면 세션은 공유하지만 화면 진행 상태는 이어지지 않습니다.

---

## API 전체 목록
화면이 호출하는 외부 API (`/api/v1` 기준, 모두 프록시 경유). 상세 스키마는 백엔드의 `/docs`(OpenAPI)를 참고하세요.

| 메서드 · 경로 | 용도 | 호출 위치 |
|---|---|---|
| `POST /sessions` | 세션 토큰 발급 | 공통 |
| `POST /sessions/current/heartbeat` | 세션 연장 (5분마다) | 공통 |
| `GET /jobs/{id}` | 백그라운드 작업 상태 조회 (`Retry-After` 간격) | 공통 (202 응답 처리) |
| `GET /data-cards` | 데이터관리카드 목록 (`limit`, `q`) | 1단계 |
| `POST /data-cards/sync` | 카드 선언 파일 동기화 | (현재 화면에서 호출하지 않음) |
| `GET /datasets` | 반입 데이터셋 목록 (`source_type=upload|merged`, `limit`) | 1단계 |
| `POST /datasets/upload` | 파일 반입 (multipart, 202) | 1단계 |
| `GET /datasets/{id}` | 데이터셋 상세(변수 목록·`role`·`role_locked`) | 1·2·4-1·5단계 |
| `DELETE /datasets/{id}` | 데이터셋 삭제 | 1단계 |
| `PATCH /datasets/{id}/columns/types` | 변수 타입 변경 `{columns:[{name, role}]}` (카드는 새 데이터셋을 만드는 202 작업) | 1단계 |
| `GET /datasets/{id}/preview` | 미리보기 (`limit`, `offset`) | 1단계, 4-2 |
| `POST /datasets/merge` | 데이터셋 결합 (join, 202) | 1단계 |
| `POST /datasets/{id}/subset` | 사용할 열만 담은 새 데이터셋 (202) | 1단계 |
| `GET /datasets/{id}/profile` | 기초 통계·품질 프로파일 (`include_outliers`) | 2·3단계 |
| `GET /datasets/{id}/outliers` | 이상치 탐지 (`method`, `threshold`) | 2단계 |
| `POST /datasets/{id}/preprocess` | 전처리 적용 → 새 데이터셋 | 2단계 |
| `GET /datasets/{id}/correlation` | 상관행렬 (`method`) | 3단계 |
| `GET /methods` | 분석 기법 설명 (보강용) | 4-1 |
| `POST /analyses` | 분석 실행 (202) | 4-1 |
| `GET /analyses/{id}` | 분석 결과 상세 (`metrics`·`result`·`chart_recommendations`·`chart_data`) | 4-1, 4-2, 5단계 |
| `POST /packages` | 결과 패키지 저장 | 4-2 |
| `GET /packages`, `GET /packages/{id}` | 패키지 목록·상세(매니페스트) | 5단계 |
| `DELETE /packages/{id}` | 패키지 삭제 | 5단계 |
| `POST /packages/{id}/share`, `DELETE /packages/{id}/share` | 공유 링크 발급·해제 | 5단계 |
| `GET /shared/{token}` | 공유 링크로 패키지 조회 (세션 없이) | 공유 링크 |

이 서버가 직접 제공하는 경로: `GET /export/package/{id}/{pdf|excel}`, `GET|POST /export/analysis/{id}/{pdf|excel}` (아래 내보내기), `GET /health`(프록시).
화면은 쓰지 않지만 백엔드에는 `/data-cards/{id}`·`/refresh`·`/definitions`, `/datasets/{id}/columns`·`/meta/limits`·`/report`, `/analyses` 목록·삭제·`chart-recommendations`·`chart-data`, `/packages/{id}/reproduce`, `DELETE /sessions/current`, `GET /jobs` 목록·취소 등이 있습니다.

**서버 규칙 중 화면에 영향을 주는 것**
* 데이터관리카드는 모든 세션이 함께 쓰는 공용 원본이라 **카드 자체는 바꾸지 않습니다**(이름 변경 `PATCH /datasets/{id}` 는 403 `read_only`). 카드의 변수 타입을 바꾸면 카드의 모든 변수를 담고 지정한 변수만 타입을 바꾼 **새 데이터셋(`source_type=subset`)** 을 백그라운드 작업(202)으로 만들고, 작업의 `resource_id` 가 새 데이터셋 id 입니다. 바꿀 타입이 하나도 없으면 작업 없이 200 으로 카드를 그대로 돌려줍니다. 카드에서 이어받은 변수(`role_locked=true`)도 바꿀 수 있고, 바꾼 변수는 `role_locked=false` 가 됩니다.
* 타입을 바꿀 때 변환할 수 없는 값은 결측이 되고 응답 `warnings` 로 알립니다(화면에 알림으로 표시).
* 업로드 응답의 `id` 는 데이터셋이 아니라 **작업 id** 입니다. 데이터셋 id 는 작업의 `resource_id` 입니다 (클라이언트가 자동 처리).

---

## PDF / Excel 내보내기
외부 API 에 없는 기능이라 이 서버가 파일을 만듭니다. **4-2 결과 리포트 화면에 보이는 내용을 그대로** 담기 위해, 표·지표 카드·차트의 모양은 화면(`ot_dim_dmmbm03_m05.js`)이 정하고 서버는 받은 내용을 파일로 그립니다.

**흐름 (5단계 [PDF 보고서]·[Excel 통계표])**
1. 화면이 패키지에 담긴 분석마다 `GET /analyses/{id}` 로 결과를 받습니다.
2. `ot_dim_dmmbm03_m05.js`(`ReportPdf.render`)가 4-2 화면과 같은 코드로 **화면 밖의 숨은 영역**(`#rp-offscreen`)에 그립니다.
3. 그려진 지표 카드·통계표(`colspan`·`rowspan` 포함)·각주를 읽고, PDF 는 Highcharts 차트를 PNG 이미지로 바꿉니다.
4. `POST /export/package/{id}/{pdf|excel}` 본문 `{ "screens": [ { title, method, sections:[{title, kpis, tables, notes}], images:[{rank,title,subtitle,data}] } ] }` 로 서버에 보내고, 서버가 파일을 만들어 내려줍니다 (`App.downloadFile`).

| 엔드포인트 | 내용 |
|---|---|
| `POST /export/package/{id}/{pdf\|excel}` | 본문 `screens` 로 만든 파일. 본문이 없으면(`GET`) 아래 예전 방식 |
| `POST /export/analysis/{id}/{pdf\|excel}` | 분석 한 건. 본문 `{ "screen": {...} }` (화면 버튼은 없음) |
| `GET /export/package/{id}/{pdf\|excel}`, `GET /export/analysis/{id}/{pdf\|excel}` | **예전 방식**: 서버가 API 응답(JSON)의 스칼라·표를 그대로 옮긴 범용 형식 (4-2 화면과 모양이 다름) |

**PDF** (`PdfExporter`, iText 2.1.7, A4)
* 제목 → 구역(분석 결과 요약 카드, 모형 요약, ANOVA, 계수 …)별로 카드 제목 · 지표 카드 줄 · 회색 머리 표(칸 병합 유지) · 각주 · 차트(Figure) 순서입니다. 분석이 여러 개면 분석마다 새 쪽에서 시작합니다.
* 분석 개요·분석 조건·패키지 요약·순위 표시·내보낸 시각은 넣지 않고 **결과만** 담습니다. 각주는 서버가 준 문구와 별표 설명만 나옵니다.
* iText 2.1.7 은 가로·세로 병합이 겹치거나 비는 칸이 있으면 `NullPointerException` 으로 문서 전체를 실패시킵니다. 그래서 병합 칸 자리를 직접 계산하고, 표마다 임시 문서에 먼저 그려 보아 실패하면 병합 없는 표로 대체합니다. 머리에 세로 병합이 있는 표는 머리 줄 반복을 끕니다(켜면 병합 칸이 첫 줄 높이로만 그려짐).
* **한글 글꼴**: `PDF_FONT_PATH`(예: `/opt/fonts/NanumGothic.ttf`) → `WEB-INF/fonts/*.ttf` → OS 글꼴(AppleGothic, NanumGothic, Noto CJK, 맑은 고딕) 순으로 찾습니다. 못 찾으면 한글이 표시되지 않고 안내 문구가 들어갑니다.

**Excel** (`ExcelExporter`, POI 3.17)
* 분석 하나 = 시트 하나(시트 이름은 분석 이름). 구역 제목 → 지표(항목·값·설명) → 통계표(칸 병합 유지) → 각주 순으로 위에서 아래로 씁니다. **차트는 넣지 않습니다.**
* 숫자로 읽히는 칸은 숫자로 넣고 소수 자릿수는 화면과 같게 둡니다. 별표가 붙은 값(`.000***`)은 글자로 남습니다.

**운영 시 확인**: 서버(Java) 변경은 "Update resources" 만으로 반영되지 않아 재시작해야 합니다. 실패 원인은 서버 로그의 `내보내기 실패`(스택)로 확인합니다. 파일명은 `Content-Disposition`(`filename*=UTF-8''…`) 에서 읽습니다.

---

## 디자인 시스템
`design.md` 가 화면 디자인의 기준입니다 (포털 남색 기반, 흰 배경, 토스식 구성). 화면마다 색·글꼴·모양을 따로 정하지 않습니다.
* **색**: 토큰 이름만 씁니다 — `brand`(#1e2c5d, 주 행동), `link`, `ink`·`ink-2~4`, `rule`·`rule-2~3`, `paper-2~3`, 차트 계열색 `chart-1~6`. 선택 카드(분석 기법·알고리즘·전처리 규칙)는 남색 테두리. 상태색은 성공 초록 · 위험 빨강. 결과 영역의 포인트색(파랑·초록·빨강)은 KRDS 계열 채도입니다. 색은 `top.jsp` 의 Tailwind `@theme` 와 `app.css` 의 `:root` 에 정의하고, 차트 등은 `App.tok(name)` 으로 읽습니다.
* **글자**: Pretendard 하나. 본문·표 13px · 보조 12px · 카드 제목 15px · 단계 제목 20px · 라벨 13px/500. 숫자는 `tabular-nums`.
* **모양**: **배경은 항상 흰색**. 영역(카드)마다 1px 옅은 테두리 네모(모서리 16)를 두고 제목은 그 안 맨 위에 둡니다. 네모 안에 네모는 만들지 않되, 고르는 것(선택 카드·입력칸)과 목록·통계 지표만 예외로 둡니다. 체크박스는 16px 네모, 라디오 14px, 버튼 36px(단계 이동 40px).
* **알림·접근성**: 위 [알림 정책](#알림-정책), 키보드 조작, 모든 입력창 이름, `prefers-reduced-motion` 지원.

---

## 알려진 제한·주의
* **`App.requireDataset()` 가드**: 데이터셋이 없으면 안내 후 1단계로 이동합니다(로컬 테스트용 TEMP 비활성화는 되돌려 두었습니다).
* 데이터관리카드의 변수 타입을 바꾸면 카드가 아니라 **새 데이터셋**이 만들어져 이후 단계에 쓰입니다(카드 원본·다른 사용자에게는 영향 없음). 타입을 바꿀 때마다 새 데이터셋이 하나씩 생기며(세션 만료 때 함께 삭제), 이 데이터셋은 "반입된 데이터셋" 목록(upload·merged)에는 나타나지 않습니다.
* 2단계 진행 조건(탐지 응답)은 화면(클라이언트)에서만 강제합니다. 서버 API 는 탐지 없이도 전처리·분석을 허용합니다.
* `metrics` / `result` / `chart_data` 의 세부 구조는 명세에 정의되어 있지 않아, 스칼라 지표는 카드로, 나머지는 표·트리로 표시하고 차트는 자주 쓰는 형태(배열·`{x,y}` 행·히스토그램·행렬 등)를 추정해서 그립니다. 실제 응답에 맞춰 `static/js/charts.js` 의 `KIND_PLANS`/`plan()` 과 `viz.js` 를 조정하세요.
* 반입·결합·타입 변경 응답의 `warnings` 는 화면에 표시합니다(반입·결합은 업로드 영역의 주의 문구, 타입 변경은 알림).
* 화면 쪽 제한(데이터관리카드 2개·반입 데이터셋 30MB·2단계 탐지 조건)은 **화면에서만 강제**합니다. 서버 API 는 그 제한 없이 분석·결합을 받으므로 화면을 거치지 않는 호출은 막지 못합니다. ZIP 재현 번들은 제공하지 않습니다.
* 5단계 PDF·Excel 은 분석 수만큼 4-2 화면을 숨은 영역에 그려서 만들기 때문에, 데이터가 큰 분석은 파일이 만들어지기까지 시간이 걸릴 수 있습니다. 서버가 주지 않은 값(표준화 계수 등)은 계산해 넣지 않습니다.
* 선택한 데이터·분석 진행 상태는 브라우저 탭에만 있어, 세션이 만료(1시간)되거나 탭을 새로 열면 1단계부터 다시 진행해야 합니다.
