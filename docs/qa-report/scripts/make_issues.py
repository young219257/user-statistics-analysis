import os, json
OUT="/Users/gim-yeong-a/edu-keris/docs/qa-report/issues"
REPORT="docs/qa-report/QA_검증리포트.md"
FOOT=f"\n\n---\n근거·재현 스크립트·캡처: `{REPORT}` (스크립트 `docs/qa-report/scripts/`, 데이터 `docs/qa-report/data/`, 캡처 `docs/qa-report/screenshots/`). 테스트 대상 `https://testlab-edmgr.kr/apps/app-20261006-160341/`, 검증일 2026-11-09."
SRV="서버 코드는 이 저장소에 없어 API 응답으로 추정한 것입니다. 원인은 서버 담당자가 확인해 주세요."
I=[]
def add(id_,title,sev,where,body): I.append(dict(id=id_,title=title,sev=sev,where=where,body=body))
# ---------- 서버 ----------
add("S1","[QA][화면+서버][중간] 마할라노비스 임계값의 의미가 화면(거리 D)과 서버(제곱거리 D²)에서 달라 기본값에서 전체 행이 이상치가 됨","중간",["frontend","server"],f"""## 증상
마할라노비스 거리 탐지의 기본 임계값 3.0에서 전체 행(388/388, 100%)이 이상치로 판정됩니다. 화면에서도 모든 변수가 100.00% / "검토 필요"로 표시됩니다.

## 원인 (서버 소스 확인)
서버의 이상치 탐지 코드는 **제곱거리 D²를 임계값과 비교**하도록 의도적으로 만들어져 있습니다(임계값 ≤ 1.5이면 자유도=변수 수인 χ² 분포의 97.5% 분위수 사용, 그보다 크면 D² 한계로 직접 사용). 반면 화면은 임계값을 "거리 D_M 기준 3.0"으로 안내하고 3.0을 그대로 보냈습니다. 10개 변수에서 D²의 중앙값은 약 8~9라서 D² > 3.0이면 거의 모든 행이 걸립니다(앱 값 388/351/203 = D² > 3/5/8의 정답 개수와 일치).

## 조치
- **화면(수정 완료):** 선택지를 서버 의미에 맞춰 "χ² 97.5% 분위수(표준, 기본)", "D² > 6.25 / 9 / 12.25 (거리 D > 2.5 / 3.0 / 3.5)"로 바꾸고 공식 문구도 D²로 수정. 기본값은 서버가 χ² 분위수로 해석하는 값(1)을 전송.
- **서버(확인 요청):** API 문서에 `threshold`의 의미(D²·χ² 분위수 특례)를 명시해 주세요.

대조 코드: `scripts/verify_outlier2.py`. {SRV}""")
add("S2","[QA][화면][낮음] 다중 시트 XLSX는 첫 시트만 반입됨 — 화면에서 단일 시트 파일만 반입하도록 안내","낮음",["frontend"],f"""## 현황
XLSX는 **시트가 하나인 파일만 반입**하는 것으로 정했습니다. 그런데 시트가 2개 이상인 파일을 올리면 **오류 없이 반입되고, 서버가 첫 번째 시트만 읽고 나머지 시트는 경고 없이 무시**합니다(반입 결과 `ingest_options.sheet = 0`, `warnings = []`). 사용자는 다른 시트가 빠졌다는 사실을 알 수 없습니다.

## 재현
`qa_multisheet_repro.xlsx`(시트 `main` 408행 16열 + `memo` 1행 2열) 업로드 → 반입 성공, 408행 16열(첫 시트만).

## 개선안
1. 업로드 영역 안내에 "XLSX는 시트가 하나인 파일만 반입할 수 있습니다." 문구 추가 (`ot_dim_dmmbm03_m01.js`의 업로드 안내, `bottom.jsp` 도움말)
2. (선택) 업로드 전에 XLSX의 시트 수를 검사해 2개 이상이면 서버로 보내지 않고 "시트가 하나인 파일로 저장해 다시 올려 주세요"라고 안내

## 비고
- 서버 결함이 아니라 지원 범위 외로 분류했습니다. 테스트 케이스·테스트 데이터도 단일 시트 XLSX를 사용합니다.
- 처음 QA에서는 "다중 시트 업로드가 `internal_error`로 실패"로 보고했으나 **원인 오진**이었습니다(실패 원인은 별도 이슈: 숫자·문자가 섞인 열).""")
add("S8","[QA][서버][높음] XLSX에서 한 열에 숫자와 문자가 섞여 있으면 반입이 internal_error로 실패함","높음",["server"],f"""## 증상
한 열에 숫자 셀과 문자 셀이 함께 있는 XLSX를 올리면 작업(job)이 즉시 실패하고 "작업 중 예기치 못한 오류가 발생했습니다. 자세한 원인은 서버 로그를 확인하세요."(`error.code=internal_error`)만 표시되어, 사용자가 원인을 알 수 없습니다. **같은 데이터를 CSV로 올리면 정상 반입**됩니다(혼합 열은 텍스트 열로 분류).

## 재현 (최소 파일)
첨부 `qa_mixed_column_minimal.xlsx` (시트 1개, 5행 2열):

| id | income |
|---|---|
| 1 | 848 (숫자) |
| 2 | "6,865" (문자) |
| 3 | 5381 (숫자) |
| 4 | "3,791" (문자) |
| 5 | 1000 (숫자) |

업로드 → 작업 상태 `failed`, `error.code=internal_error`.

## 원인 좁히기 (같은 문제 주입 데이터 408행 16열 기준)
| 파일 | 결과 |
|---|---|
| `income` 열이 숫자+문자 혼합 (시트 1개) | **실패** |
| `income` 열이 숫자+문자 혼합 + 시트 2개 (어제 반입한 원본과 같은 방식) | **실패** |
| `income` 열 제거 | 성공 |
| `income` 열을 모두 숫자로 통일 | 성공 |
| `income` 열을 모두 문자로 통일 | 성공 |
| 쉼표 문자 값만 결측으로 바꿈 | 성공 |
| 최소 파일에서 숫자만 남김 (`minimal_numeric`) | 성공 |
| 같은 내용의 CSV | 성공 |

시트 수는 원인이 아닙니다(시트 1개여도 실패, 시트 2개여도 데이터가 깨끗하면 성공).

## 기대 동작
혼합 타입 열은 텍스트 열로 반입하거나, 최소한 원인 열을 알려 주는 오류 메시지를 반환합니다.

## 첨부 파일 (이슈 작성 화면에 끌어다 놓기)
- `qa_mixed_column_minimal.xlsx` — 최소 재현 (4.9KB)
- `qa_main_injected_2sheets.xlsx` — QA에서 처음 실패한 파일과 같은 방식·같은 seed로 재생성한 408행 16열 + `memo` 시트 (38KB)

## 고칠 곳
서버(XLSX 수집·열 타입 추론). {SRV}""")
add("S3","[QA][서버][높음] 타입 추론: 앞자리 0 코드가 숫자로, 쉼표 숫자가 텍스트로 분류됨","높음",["server"],f"""## 증상
- 학교코드 `"00101"`~`"00130"`이 `role=numeric, dtype=int64`로 읽혀 `101`이 됩니다(프로파일 min=101). 경고 없음.
- `"1,234"`처럼 쉼표가 든 숫자 열(`income`)이 `role=text`로 분류되어 기초통계·이상치·상관에서 **경고 없이 제외**됩니다.

## 재현
`data/qa_main_utf8.csv` 반입 후 열 정보 확인 (`school_id`, `income`).

## 기대값
앞자리 0 열은 문자열 유지(또는 경고), 천 단위 구분자 숫자는 파싱하거나 "숫자처럼 보이는 텍스트 열" 경고.

## 영향
코드 열이 바뀌어 결합 키가 어긋나고, 숫자 변수가 분석에서 빠집니다. {SRV}""")
add("S4","[QA][서버][높음] 위장 결측(\"-\", 999, -1) 미탐지, 이상치로 조용히 처리됨","높음",["server"],f"""## 증상
- `region`의 `"-"`는 범주 값으로 남고, `"NA"`, `"null"`, `""`, `" "`만 결측 처리됩니다.
- `satisfaction`의 `999`, `-1`은 수치로 통계에 포함되고(`max=999`), 이후 윈저라이징·표준화에서 **조용히 눌립니다**(표준화 후 최대 3.38). 위장 결측 경고는 없고 프로파일 경고는 상수 열 하나뿐입니다.

## 재현
`data/qa_main_utf8.csv` → STEP2 프로파일, 이상치 처리(윈저라이징) 후 STEP3 통계.

## 개선안
센티널 후보(`-`, `999`, `-1`, `9999` 등) 탐지 경고, 또는 사용자 지정 결측값 입력. {SRV}""")
add("S5","[QA][서버][높음] 통계 가정 위반·데이터 문제 경고(warnings)가 거의 없음","높음",["server"],f"""## 증상
가정 위반 데이터로 각 기법을 실행해도 `result.warnings`가 모두 빈 배열입니다. (상수 열, DBSCAN 전부 잡음 경고만 정상 동작)

| 상황 | 실제 지표(API) | 경고 |
|---|---|---|
| 다중공선성 | VIF 10061 | 없음 |
| 잔차 자기상관(AR(1) ρ=0.9) | DW 0.253 | 없음 |
| 이분산·비정규 | Shapiro p=2.8e-33 | 없음 |
| 클래스 불균형(양성 3%) | - | 없음 |
| 완전분리 | - | 없음 |
| 표본 n=8 | - | 없음 |
| ANOVA 등분산 위반 | Levene p=6e-38 | 없음 (Welch 대안도 없음) |
| PSM 공통지지 없음 | match_rate=0.0 | 없음 |
| 다층모형 특이 적합 | `converged=false` | 없음 |

정상 데이터에서는 오탐이 없었습니다. 대조 코드: `scripts/verify_diag.py`.

## 개선안
`{{code, message, suggestion}}` 경고 규칙 추가: VIF>10, DW 범위, 진단 p<.05 요약, 양성 비율, n<변수 수×10, 매칭률·caliper, `converged=false`, Levene 위반 시 대안 검정 안내.

## 참고
화면은 서버 경고를 이미 렌더링합니다(`ot_dim_dmmbm03_m05.js:854` `renderWarnings`). 서버가 채우면 화면 수정 없이 표시됩니다. {SRV}""")
add("S6","[QA][서버][중간] 결합(merge) 시 미매칭 키·1:N 행 증가 경고가 없음","중간",["server","frontend"],f"""## 증상
`qa_main` + `qa_school`을 `school_id`로 결합했을 때 행 수는 정답과 일치(inner 397 / left 444 / right 399 / outer 446)하지만 `warnings=[]`입니다. 미매칭 키(128~130 3개 학교), 우측 여분 키(998, 999), 1:N 키(101, 102), left 결합의 행 증가(408→444)에 대한 안내가 없습니다.

## 개선안
서버가 미매칭 키 수, 1:N 키, 행 증가율을 `warnings`로 반환하고, 화면은 결합 완료 시 이를 표시합니다.

## 확인 필요
화면(`ot_dim_dmmbm03_m01.js`)이 결합 응답의 `warnings`를 렌더링하는지는 확인하지 못했습니다. {SRV}""")
add("S7","[QA][서버][중간] 전처리 적용 범위가 모호함 (결측 행 제거·이상치 제거)","중간",["server","frontend"],f"""## 증상
- `missing_strategy=drop_rows`: 388행만 남습니다. 수치 열의 결측만 제거되고 텍스트(`income`)·범주(`region`) 결측 행은 남습니다(전체 결측 기준이면 350행, income 제외 385행).
- `outlier_treatment=drop`, IQR 1.5: 393행(15행 제거). `study_hours` 기준 정답은 398행으로, 모든 수치 열 기준으로 제거한 것으로 **추정**(미확인).

## 개선안
적용 대상 열 범위를 응답 또는 화면 문구에 명시하고, 필요하면 열 선택 옵션 제공. 재현: `scripts/verify_preproc.py`. {SRV}""")
# ---------- 화면 ----------
add("F1","[QA][화면][높음] 다층모형 AIC/BIC에 '(REML)' 오표기 (실제 ML 기준)","높음",["frontend","server"],f"""## 증상
4-2 리포트·PDF·Excel의 AIC/BIC 옆에 "(REML)"이 붙어 있으나 값은 **ML 적합 기준**입니다. 한 표 안에서 로그우도는 REML 값, AIC/BIC는 ML 값이라 기준이 섞여 있습니다.

## 근거
무조건모형(`score_t4 ~ 1`, 집단 `school_id`):
| 적합 | 로그우도 | AIC | BIC |
|---|---|---|---|
| REML | -1351.512 | 2709.025 | 2720.999 |
| ML | -1352.197 | 2710.393 | 2722.368 |
| **앱 표시** | -1351.512 | **2710.393 (REML)** | **2722.368 (REML)** |

서버 응답에는 `model_fit.information_criteria_basis="ML"`이 있는데 화면이 무시하고 `estimation_method`를 출력합니다.

## 고칠 곳
- 화면(즉시): `src/main/webapp/static/js/ot_dim_dmmbm03_m05.js:733` `aicCell`에서 `model_fit.information_criteria_basis`를 표기
- 서버(근본): 정보기준을 REML 기준으로 일관되게 계산하거나 기준 필드를 명확히 제공
캡처: `screenshots/15_report_hlm.png`""")
add("F2","[QA][화면][중간] 종속변수 기본값이 ID 성격의 첫 수치형 열로 자동 선택됨","중간",["frontend"],f"""## 증상
STEP4에서 종속변수를 지정하지 않으면 첫 번째 수치형 열(`school_id`)이 자동 선택됩니다. 이 때문에 HLM 집단변수 목록에서 `school_id`가 제외되어 선택할 수 없었습니다(종속변수와 같은 열은 제외하는 규칙).

## 고칠 곳
`src/main/webapp/static/js/ot_dim_dmmbm03_m04.js:322`, `:380` (`cfg.target = numericCols()[0].name`). 자동 선택을 없애고 직접 고르게 하거나 ID·고유값 많은 열은 후보에서 제외.""")
add("F3","[QA][화면][낮음] 내부 필드명이 표 헤더·차트 축에 그대로 노출","낮음",["frontend"],f"""## 증상
- 다층모형 확률효과 표 헤더: `const_se`, `const_ci_lower`, `const_ci_upper` (화면·PDF·Excel 모두)
- 분산 성분 차트 축: `group_variance`, `residual_variance`

## 고칠 곳
`ot_dim_dmmbm03_m05.js:764` `renderRandomEffects`에서 `const`만 한글 매핑하고 나머지는 원문 출력. 라벨 매핑 추가. 분산 성분 차트 라벨은 `charts.js`.
캡처: `screenshots/15_report_hlm.png`""")
add("F4","[QA][화면][낮음] STEP1 용량 경고 문구가 '의견 보내기' 플로팅 버튼에 가려짐","낮음",["frontend"],"""## 증상
1440px 화면에서 반입된 데이터셋 아래 주황 경고("분석·결합에는 선택한 데이터셋 합계 30.0MB 이하만…")의 오른쪽 끝이 우측 하단 "의견 보내기" 버튼에 가려집니다.

## 고칠 곳
`app.css` — 경고 영역 우측 여백 확보 또는 플로팅 버튼 위치 조정.
캡처: `screenshots/04_upload_errors.png`""")
add("F5","[QA][화면][중간] 상관분석에서 범주·상수·텍스트 열 선택이 허용됨","중간",["frontend"],f"""## 증상
`region`(범주), `const_col`(상수), `income`(텍스트)를 상관분석 변수로 요청하면 오류·경고 없이 `succeeded`로 끝납니다(어떤 열이 계산에서 빠졌는지도 안내 없음).

## 원인
화면이 허용하고 있습니다: `ot_dim_dmmbm03_m04.js:60` `CAT_FEAT`에 `correlation`이 포함되어 있고 주석이 "모든 기법에서 범주형 독립변수 허용"입니다.

## 개선안
상관분석 후보를 수치형·이진 열로 제한. 서버 쪽 검증은 보조로 추가.""")
add("F6","[QA][화면][낮음] 명세 미표기: 켄달 tau-b, 표준화 ddof","낮음",["frontend"],"""## 증상
- 켄달 상관값은 tau-b와 일치하지만(scipy 대조 불일치 0) 화면에 변형이 표기되지 않습니다.
- 표준화 후 `std(ddof=0)=1.0`, `std(ddof=1)=1.0012`로 ddof=0을 쓰는 반면, 프로파일의 std는 ddof=1이라 정의가 다릅니다.

## 개선안
화면에 "Kendall τ-b", "표준화: 모표준편차(ddof=0)"처럼 정의를 표기.""")
add("F7","[QA][화면][낮음] JSP의 캐시 방지 코드가 정적 호스팅에서 그대로 출력됨","낮음",["frontend"],"""## 증상
JS/CSS 주소에 붙인 `?v=<%= System.currentTimeMillis() %>`가 테스트랩(JSP를 서버에서 실행하지 않고 정적 파일로 서빙)에서는 URL에 **그대로 출력**됩니다. 정적 서버가 쿼리를 무시해 파일은 로드되지만 캐시 방지는 동작하지 않습니다.

## 개선안
정적 호스팅에서도 동작하는 방식(빌드 번호 등)으로 교체. 대상: `WEB-INF/views/*.jsp`, `layout/top.jsp`, `layout/bottom.jsp`.""")
add("F8","[QA][화면][중간] STEP2 '이상치 검출' 카드가 변수별 건수의 합(행 단위 아님)","중간",["frontend","server"],"""## 증상
마할라노비스에서 카드가 **3,880건**(= 388행 × 10변수)으로 표시됩니다. 행 단위가 아니라 변수별 건수의 합으로 보입니다(S1과 함께 보면 이상치 판정이 100%인 상태).

## 고칠 곳
`ot_dim_dmmbm03_m02.js` `totalOutliers()` — 행 단위(중복 제거) 건수로 표시하거나 "변수별 합계"로 명시. 서버가 행 단위 건수를 주면 더 정확.
캡처: `screenshots/06_detect_4.png`""")
add("F9","[QA][화면][중간] 데이터가 없는 차트가 1순위로 추천됨","중간",["frontend","server"],"""## 증상
다층모형(고정효과가 절편뿐인 모형)에서 1순위 추천 차트 "Figure 1. 고정효과 계수"가 "이 차트에 표시할 데이터가 없습니다."로 비어 있습니다.

## 고칠 곳
- 화면(즉시): `charts.js`에서 데이터 없는 추천 차트를 숨기고 순위 재정렬 (`noDataMsg` 경로)
- 서버: 데이터가 없는 추천은 `chart_recommendations`에서 제외
캡처: `screenshots/15_report_hlm.png`""")
# ---------- 양쪽 ----------
add("B1","[QA][서버+화면][높음] K-평균·PCA가 표준화 없이 원척도로 계산되고 표기도 없음","높음",["server","frontend"],f"""## 증상
- K-평균: 앱 `total_ss`=49147.4 = **원척도** 총제곱합(표준화 시 1200.0), K=3 inertia 15130.4 = 원척도 sklearn 결과(표준화 시 556.9)
- PCA: 설명분산비 [0.8428, 0.0532]·고유값 [205.05, 12.93] = **공분산 기준**(상관 기준은 [0.709, 0.1878])
- 두 기법 모두 `preprocessing_steps=[]`, 화면에 기준 표기·옵션 없음. 스케일이 큰 변수가 결과를 지배합니다.

## 개선안
서버: 표준화 옵션과 사용 기준(공분산/상관) 필드. 화면: 옵션 UI와 기준 표기. 재현: `scripts/verify_models.py`. {SRV}""")
add("B2","[QA][서버+화면][높음] ID·이진 열이 이상치 탐지·진단·표준화 대상에 포함됨","높음",["server","frontend"],f"""## 증상
- 이상치 진단 표·탐지 대상에 `school_id`(ID 성격), `treatment`·`passed`(0/1), `grade`(3수준), `satisfaction`이 나열되고 `school_id`는 "검토 필요" 판정을 받습니다.
- 표준화(스케일링)가 `school_id`에도 적용되어 STEP3 통계가 평균 0.00, 표준편차 1.00, 범위 -1.65~1.57로 바뀝니다. 코드값이 의미 없는 값이 됩니다.

## 개선안
서버: `/preprocess`에 제외 열 지정 지원, 탐지 대상에서 ID·이진·저고유값 열 제외. 화면: 위 열을 제외해서 요청(현재 요청에는 열 지정이 없음: `ot_dim_dmmbm03_m02.js` `buildPreprocessRequest`). 임시로 화면에서 `role`/`n_unique`로 필터 가능.
캡처: `screenshots/06_detect_4.png`, `screenshots/08b_step3_after_prep.png`""")
add("B3","[QA][서버+화면][중간] 기법별 필수 지표 누락","중간",["server","frontend"],f"""## 증상 (API 응답 필드 기준, 수치 대조 98건은 불일치 0)
| 기법 | 누락 지표 |
|---|---|
| 상관분석 | 95% 신뢰구간, 쌍별 n, 다중비교 보정 |
| 선형회귀 | 표준화 β, Cook's D, DW 판정 문구 |
| 로지스틱 | Nagelkerke R², Hosmer-Lemeshow |
| PCA | KMO, Bartlett 검정 |
| ANOVA | ω², Welch ANOVA, Games-Howell, 제곱합 유형 표기 |
| 다층모형 | 우도비 검정(LRT), marginal·conditional R² |
| PSM | 분산비 |

선형회귀 표준화 β는 소스에도 "API가 주지 않아 표시하지 않는다"고 적혀 있습니다(`ot_dim_dmmbm03_m05.js:225`).

## 개선안
서버: 지표 계산·필드 추가. 화면: 결과표에 열 추가. 대조 코드: `scripts/verify_models.py`. {SRV}""")
add("B4","[QA][서버+화면][중간] 성장곡선: wide 형식(score_t1~t4)을 바로 분석할 수 없음","중간",["server","frontend"],"""## 증상
`time_column`이 열 하나만 받아 시점별 열(`score_t1`~`score_t4`)로 된 wide 형식 데이터를 wide→long 변환 없이 분석할 수 없습니다. 변환의 정확성은 검증하지 못했습니다(구조상 관찰).

## 개선안
서버: wide→long 변환 지원. 화면: 시점 열 선택·시간 코딩 방식 표기 UI.""")
FIXED = {
 "S1":"화면 선택지·공식 수정 완료(서버 문서 확인 요청 남음)", "S2":"화면 수정 완료 — 업로드 안내 문구 + 업로드 전 시트 수 검사(2개 이상이면 서버로 보내지 않음)",
 "S4":"화면 일부 수정 — '결측으로 처리할 값' 입력칸 추가(서버 na_values 전달). 자동 탐지·경고는 서버 몫",
 "F1":"화면 수정 완료","F2":"화면 수정 완료","F3":"화면 수정 완료","F4":"화면 수정 완료","F5":"화면 수정 완료","F6":"화면 수정 완료","F7":"화면 수정 완료(고정 버전 값, 수정 시 올려야 함)",
 "F8":"화면 수정 완료 — 마할라노비스는 이상치 행 수, 그 외는 '변수별 합계'로 표기","F9":"화면 수정 완료 — 데이터 없는 추천 차트를 숨기고 탭 개수도 맞춤",
 "B1":"화면 원인 수정 완료 — 화면이 분석 요청에 scaling='none'을 항상 보내 서버의 기본 표준화(군집·PCA)를 막고 있었음. 이제 '표준화 후 분석' 옵션(기본 켜짐). 서버 master는 기본 표준화·경고를 이미 지원하므로 테스트랩 서버 버전 확인 필요",
 "B2":"화면 일부 수정 — 이상치 진단·전처리 대상에서 식별자(…_id 등)·이진 열 제외, 전처리 요청에 columns 전달. 서버는 소문자 '_id' 접미사를 식별자로 추론하지 않음(서버 몫)",
}
os.makedirs(OUT,exist_ok=True)
for f in os.listdir(OUT): os.remove(os.path.join(OUT,f))
sh=["#!/usr/bin/env bash","# QA 이슈 일괄 등록. 사전: gh auth login (또는 GH_TOKEN 설정). 실행 위치: 저장소 루트","set -euo pipefail","cd \"$(dirname \"$0\")/../../..\"","D=docs/qa-report/issues",
 "gh label create qa --color 5319e7 --description 'QA 검증 결과' --force","gh label create server --color b60205 --description '서버(API) 수정 필요' --force","gh label create frontend --color 1d76db --description '화면(JSP/JS/CSS) 수정 필요' --force",
 "gh label create sev:치명 --color 000000 --force","gh label create sev:높음 --color d93f0b --force","gh label create sev:중간 --color fbca04 --force","gh label create sev:낮음 --color c2e0c6 --force",""]
for it in I:
    fn=f"{it['id']}.md"; status = (f"> **처리 현황 (2026-11-11):** {FIXED[it['id']]}\n\n" if it["id"] in FIXED else "")
    open(os.path.join(OUT,fn),"w",encoding="utf-8").write(status+it["body"]+FOOT+"\n")
    labs=",".join(["qa"]+it["where"]+["sev:"+it["sev"]])
    sh.append(f"gh issue create --title {json.dumps(it['title'],ensure_ascii=False)} --label {json.dumps(labs,ensure_ascii=False)} --body-file \"$D/{fn}\"")
open(os.path.join(OUT,"create_issues.sh"),"w").write("\n".join(sh)+"\n"); os.chmod(os.path.join(OUT,"create_issues.sh"),0o755)
print(len(I),"issues")
