#!/usr/bin/env bash
# QA 이슈 일괄 등록. 사전: gh auth login (또는 GH_TOKEN 설정). 실행 위치: 저장소 루트
set -euo pipefail
cd "$(dirname "$0")/../../.."
D=docs/qa-report/issues
gh label create qa --color 5319e7 --description 'QA 검증 결과' --force
gh label create server --color b60205 --description '서버(API) 수정 필요' --force
gh label create frontend --color 1d76db --description '화면(JSP/JS/CSS) 수정 필요' --force
gh label create sev:치명 --color 000000 --force
gh label create sev:높음 --color d93f0b --force
gh label create sev:중간 --color fbca04 --force
gh label create sev:낮음 --color c2e0c6 --force

gh issue create --title "[QA][화면+서버][중간] 마할라노비스 임계값의 의미가 화면(거리 D)과 서버(제곱거리 D²)에서 달라 기본값에서 전체 행이 이상치가 됨" --label "qa,frontend,server,sev:중간" --body-file "$D/S1.md"
gh issue create --title "[QA][화면][낮음] 다중 시트 XLSX는 첫 시트만 반입됨 — 화면에서 단일 시트 파일만 반입하도록 안내" --label "qa,frontend,sev:낮음" --body-file "$D/S2.md"
gh issue create --title "[QA][서버][높음] XLSX에서 한 열에 숫자와 문자가 섞여 있으면 반입이 internal_error로 실패함" --label "qa,server,sev:높음" --body-file "$D/S8.md"
gh issue create --title "[QA][서버][높음] 타입 추론: 앞자리 0 코드가 숫자로, 쉼표 숫자가 텍스트로 분류됨" --label "qa,server,sev:높음" --body-file "$D/S3.md"
gh issue create --title "[QA][서버][높음] 위장 결측(\"-\", 999, -1) 미탐지, 이상치로 조용히 처리됨" --label "qa,server,sev:높음" --body-file "$D/S4.md"
gh issue create --title "[QA][서버][높음] 통계 가정 위반·데이터 문제 경고(warnings)가 거의 없음" --label "qa,server,sev:높음" --body-file "$D/S5.md"
gh issue create --title "[QA][서버][중간] 결합(merge) 시 미매칭 키·1:N 행 증가 경고가 없음" --label "qa,server,frontend,sev:중간" --body-file "$D/S6.md"
gh issue create --title "[QA][서버][중간] 전처리 적용 범위가 모호함 (결측 행 제거·이상치 제거)" --label "qa,server,frontend,sev:중간" --body-file "$D/S7.md"
gh issue create --title "[QA][화면][높음] 다층모형 AIC/BIC에 '(REML)' 오표기 (실제 ML 기준)" --label "qa,frontend,server,sev:높음" --body-file "$D/F1.md"
gh issue create --title "[QA][화면][중간] 종속변수 기본값이 ID 성격의 첫 수치형 열로 자동 선택됨" --label "qa,frontend,sev:중간" --body-file "$D/F2.md"
gh issue create --title "[QA][화면][낮음] 내부 필드명이 표 헤더·차트 축에 그대로 노출" --label "qa,frontend,sev:낮음" --body-file "$D/F3.md"
gh issue create --title "[QA][화면][낮음] STEP1 용량 경고 문구가 '의견 보내기' 플로팅 버튼에 가려짐" --label "qa,frontend,sev:낮음" --body-file "$D/F4.md"
gh issue create --title "[QA][화면][중간] 상관분석에서 범주·상수·텍스트 열 선택이 허용됨" --label "qa,frontend,sev:중간" --body-file "$D/F5.md"
gh issue create --title "[QA][화면][낮음] 명세 미표기: 켄달 tau-b, 표준화 ddof" --label "qa,frontend,sev:낮음" --body-file "$D/F6.md"
gh issue create --title "[QA][화면][낮음] JSP의 캐시 방지 코드가 정적 호스팅에서 그대로 출력됨" --label "qa,frontend,sev:낮음" --body-file "$D/F7.md"
gh issue create --title "[QA][화면][중간] STEP2 '이상치 검출' 카드가 변수별 건수의 합(행 단위 아님)" --label "qa,frontend,server,sev:중간" --body-file "$D/F8.md"
gh issue create --title "[QA][화면][중간] 데이터가 없는 차트가 1순위로 추천됨" --label "qa,frontend,server,sev:중간" --body-file "$D/F9.md"
gh issue create --title "[QA][서버+화면][높음] K-평균·PCA가 표준화 없이 원척도로 계산되고 표기도 없음" --label "qa,server,frontend,sev:높음" --body-file "$D/B1.md"
gh issue create --title "[QA][서버+화면][높음] ID·이진 열이 이상치 탐지·진단·표준화 대상에 포함됨" --label "qa,server,frontend,sev:높음" --body-file "$D/B2.md"
gh issue create --title "[QA][서버+화면][중간] 기법별 필수 지표 누락" --label "qa,server,frontend,sev:중간" --body-file "$D/B3.md"
gh issue create --title "[QA][서버+화면][중간] 성장곡선: wide 형식(score_t1~t4)을 바로 분석할 수 없음" --label "qa,server,frontend,sev:중간" --body-file "$D/B4.md"
