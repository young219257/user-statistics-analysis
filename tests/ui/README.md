# 화면 단위 테스트 (UI)

`ot_dim_dmmbm03_m01 ~ m06` 화면 6개를 **실제 브라우저(Chrome)** 로 조작해 검증하는 자동 테스트입니다.
Playwright(브라우저 조작) + pytest. 단위 테스트 계획서의 케이스 ID(`UT-M01-01` …)와 테스트 함수 이름(`test_UT_M01_01_…`)이 1:1 로 대응합니다.

| 파일 | 화면 | 케이스 |
|---|---|---|
| `test_m01_import.py` | m01 데이터 반입·결합 | UT-M01-01 ~ 16 |
| `test_m02_quality.py` | m02 품질 및 전처리 | UT-M02-01 ~ 11 |
| `test_m03_eda.py` | m03 데이터 탐색 | UT-M03-01 ~ 05 |
| `test_m04_modeling.py` | m04 모형 설정·실행 | UT-M04-01 ~ 10 |
| `test_m05_report.py` | m05 분석 결과 리포트 | UT-M05-01 ~ 07 |
| `test_m06_packaging.py` | m06 결과 관리 | UT-M06-01 ~ 05 |

기대값은 `data/` 의 CSV 를 **pandas / scipy / statsmodels 로 직접 계산**해서 비교합니다 (화면 값을 그대로 믿지 않음).

## 준비
```bash
cd tests/ui
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt          # 시스템 Chrome 을 쓰면 playwright install 은 필요 없음
```
- 테스트 대상 앱이 떠 있어야 합니다. 로컬 실행: 프로젝트 루트에서
  `mvn -Dmaven.compiler.source=8 -Dmaven.compiler.target=8 org.apache.tomcat.maven:tomcat7-maven-plugin:2.2:run -Dmaven.tomcat.port=8090 -Dmaven.tomcat.path=/`
- 분석 API(`UPSTREAM_API_BASE`)에 접근 가능해야 합니다 (업로드·분석·내보내기가 API 를 호출).

## 실행
```bash
pytest                                  # 전체 (약 8분)
pytest -m m02                           # 화면별 (m01 … m06)
pytest -m "not slow"                    # 30MB 합계 제한 같은 느린 케이스 제외
pytest -k "UT_M04_03"                   # 케이스 하나
UI_BASE_URL=https://배포주소 pytest      # 다른 환경 대상
UI_HEADED=1 pytest -k UT_M01_01         # 브라우저 창을 띄워 눈으로 확인
```
| 환경변수 | 기본값 | 설명 |
|---|---|---|
| `UI_BASE_URL` | `http://localhost:8090` | 테스트 대상 주소 |
| `UI_BROWSER_CHANNEL` | `chrome` | `chrome` · `msedge` · `chromium`(playwright 내장) |
| `UI_HEADED` | (없음) | `1` 이면 창을 띄움 |

실패한 케이스는 화면 캡처가 `reports/` 에 저장됩니다.

## 결과 읽는 법
- **passed**: 기대대로 동작.
- **xfailed**: *알려진 결함* 때문에 아직 실패하는 케이스. `reason` 에 결함 번호(QA 리포트 `docs/qa-report/`)가 적혀 있습니다.
  결함이 고쳐지면 **XPASS** 로 바뀌므로 그때 `@pytest.mark.xfail` 를 지웁니다.
- **failed**: 새로 발견된 문제이거나 화면이 바뀌어 테스트가 맞지 않게 된 것.

현재 xfail: `UT-M01-14`(XLSX 혼합 열 반입 실패 — 서버), `UT-M02-06 행 제거`, `UT-M02-07 이상치 행 제거`(적용 열 범위 — 서버). 나머지는 모두 통과합니다.

## 구조
- `helpers.py` — 화면 조작(업로드·단계 이동·전처리·분석)과 표 값 읽기. **화면 URL 은 여기의 `URLS` 한 곳만** 바꾸면 됩니다(포털 이식 시).
- `conftest.py` — 브라우저·세션 준비, 실패 캡처. 테스트마다 새 컨텍스트(= 새 세션)로 서로 영향이 없습니다. 같은 분석을 여러 케이스가 쓰는 파일(m03~m06)은 한 번 준비한 화면을 공유합니다.
- `data/` — 테스트 데이터 (`docs/qa-report/` 의 생성 스크립트·정답값과 동일).

## 알아둘 점
- 이 테스트는 **화면(JSP + JS)** 단위입니다. 서버(Java) 클래스·공통 모듈·13개 기법 전체의 계산 정확도는 포함하지 않습니다.
- 반입 데이터는 분석 API 가 1시간 후 삭제하므로 테스트는 매번 새로 반입합니다. 테스트가 올린 데이터는 세션 종료와 함께 정리됩니다.
