# -*- coding: utf-8 -*-
"""이용자 통계분석 단위/통합 테스트 계획서 생성 (양식: EDEMS-업무단위코드-통합테스트계획서-v0.90 의 장·표 구성)"""
import os
from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

OUT = "/Users/gim-yeong-a/keris/이용자통계분석/테스트"
PROJECT = "교육행정데이터통합관리시스템 지능형 분석·활용 고도화 사업 (이용자 통계분석)"
TODAY = "2026-11-10"
import os as _os
LOGO = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "assets", "logo_mobigen.png")
if not _os.path.exists(LOGO):
    LOGO = "/Users/gim-yeong-a/edu-keris/docs/qa-report/assets/logo_mobigen.png"
LOGO_WIDTH_CM = 6.0      # 가로 6cm (원본 600x169 비율 유지 → 세로 약 1.7cm)

FONT = "맑은 고딕"
TBD = "【협의 필요】"

# ---------------------------------------------------------------- 공통 헬퍼
def set_font(run, size=10, bold=False, color=None):
    run.font.name = FONT; run.font.size = Pt(size); run.font.bold = bold
    run._element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    if color: run.font.color.rgb = RGBColor.from_string(color)

def shade(cell, fill):
    tcPr = cell._tc.get_or_add_tcPr(); shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear'); shd.set(qn('w:color'), 'auto'); shd.set(qn('w:fill'), fill); tcPr.append(shd)

def para(doc, text="", size=10, bold=False, align=None, space_after=4, indent=0, color=None):
    p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(space_after)
    if indent: p.paragraph_format.left_indent = Cm(indent)
    if align == 'c': p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(text); set_font(r, size, bold, color); return p

def h1(doc, text): return para(doc, text, 13, True, space_after=6)
def h2(doc, text): return para(doc, text, 11, True, space_after=4, indent=0.3)
def bullet(doc, text, indent=0.8): return para(doc, "• " + text, 10, indent=indent, space_after=2)

def table(doc, header, rows, widths, size=9, center_cols=(), header_fill='D9D9D9'):
    t = doc.add_table(rows=1, cols=len(header)); t.style = 'Table Grid'; t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, h in enumerate(header):
        c = t.rows[0].cells[i]; c.text = ""; shade(c, header_fill)
        r = c.paragraphs[0].add_run(h); set_font(r, size, True); c.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    for row in rows:
        cells = t.add_row().cells
        for i, v in enumerate(row):
            cells[i].text = ""
            lines = str(v).split("\n")
            for k, ln in enumerate(lines):
                p = cells[i].paragraphs[0] if k == 0 else cells[i].add_paragraph()
                p.paragraph_format.space_after = Pt(0)
                if i in center_cols: p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                set_font(p.add_run(ln), size)
    for row in t.rows:
        for i, w in enumerate(widths): row.cells[i].width = Cm(w)
    tblPr = t._tbl.tblPr                                   # Word·한글에서도 열 너비가 유지되도록 고정 레이아웃
    lay = OxmlElement('w:tblLayout'); lay.set(qn('w:type'), 'fixed'); tblPr.append(lay)
    for el in tblPr.findall(qn('w:tblW')): tblPr.remove(el)
    tw = OxmlElement('w:tblW'); tw.set(qn('w:w'), str(int(sum(widths) * 567))); tw.set(qn('w:type'), 'dxa'); tblPr.append(tw)
    grid = t._tbl.tblGrid
    for i, gc in enumerate(grid.findall(qn('w:gridCol'))): gc.set(qn('w:w'), str(int(widths[i] * 567)))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t

def page_break(doc): doc.add_page_break()

def footer_pages(doc):
    f = doc.sections[0].footer.paragraphs[0]; f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    def fld(code):
        r = f.add_run(); set_font(r, 9)
        a = OxmlElement('w:fldChar'); a.set(qn('w:fldCharType'), 'begin'); r._r.append(a)
        b = OxmlElement('w:instrText'); b.set(qn('xml:space'), 'preserve'); b.text = code; r._r.append(b)
        c = OxmlElement('w:fldChar'); c.set(qn('w:fldCharType'), 'end'); r._r.append(c)
    set_font(f.add_run("- "), 9); fld("PAGE"); set_font(f.add_run(" -"), 9)

# ---------------------------------------------------------------- 케이스 데이터
# (화면/대상, [(케이스ID, 항목, 절차·입력, 기대 결과), ...])
UNIT = [
 ("ot_dim_dmmbm03_m01 · 1단계 데이터 반입 / 데이터 결합 (test_m01_import.py)", [
  ("UT-M01-01", "CSV(UTF-8) 업로드", "qa_main_utf8.csv 선택", "반입 완료, 408행 16변수, 자동 선택(16/16 열)"),
  ("UT-M01-02", "CSV(CP949) 업로드", "qa_main_cp949.csv 선택", "408행 16변수, 한글(서울 등)이 깨지지 않음"),
  ("UT-M01-03", "XLSX(단일 시트) 업로드", "단일 시트 xlsx 선택", "408행 16변수, 형식 xlsx 표시"),
  ("UT-M01-04", "허용되지 않는 형식", "bad.txt 선택", "「지원하지 않는 파일 형식입니다」 표시, 반입 0건"),
  ("UT-M01-05", "파일 1건당 10MB 초과", "약 12.6MB csv 선택", "「최대 10.0MB」 안내, 서버로 보내지 않아 반입 0건"),
  ("UT-M01-06", "여러 파일 동시 업로드", "csv 2개 + xlsx + txt 한 번에 선택", "3건 반입·선택(탭 3개), 형식 오류 파일은 파일명과 함께 안내"),
  ("UT-M01-07", "합계 30MB 제한 (느린 케이스)", "약 9.5MB csv 4개 업로드", "30.0MB·남은 용량 경고, 3개까지 선택, 4번째는 「남은 용량 초과」로 선택 불가"),
  ("UT-M01-08", "데이터관리카드 선택", "카드 3개 순서대로 클릭", "2개까지 선택, 세 번째는 선택 불가"),
  ("UT-M01-09", "변수 속성·타입 변경", "income 사용 해제, grade 타입을 범주형으로 변경", "사용 열 15/16으로 감소, 타입 변경이 서버에 반영되어 유지"),
  ("UT-M01-10", "미리보기", "반입 직후 확인", "전체 행 수(408)와 첫 행(student_id)이 원본과 일치"),
  ("UT-M01-11", "삭제 확인창", "휴지통 → [취소] → 휴지통 → [삭제]", "취소 시 1건 유지, 삭제 시 0건"),
  ("UT-M01-12", "데이터 결합 행 수", "qa_main + qa_school, 키 school_id, inner/left/right/outer", "행 수 397 / 444 / 399 / 446 (pandas merge 결과와 일치)"),
  ("UT-M01-13", "결합 결과 단독 선택", "결합 실행 후 목록 확인", "「결합」 표시 데이터셋 1건 생성·단독 선택, 다른 데이터는 선택 불가 안내, 2단계 진행 가능"),
  ("UT-M01-14", "XLSX 숫자·문자 혼합 열 【현재 실패 예상: 결함 D-24】", "한 열에 숫자와 쉼표 문자열(\"6,865\")이 섞인 단일 시트 xlsx 업로드", "반입 성공(혼합 열은 텍스트 열). 현재는 서버 internal_error 로 실패"),
  ("UT-M01-15", "다중 시트 XLSX 차단", "시트가 2개인 xlsx 업로드", "서버로 보내지 않고 「시트가 2개입니다… 시트가 하나인 파일만 반입」 안내, 반입 0건. 업로드 안내 문구에도 조건 표기"),
  ("UT-M01-16", "결측으로 처리할 값 입력", "입력칸에 「-, 999」 입력 후 qa_main_utf8.csv 업로드", "서버로 전달되어 2단계 결측 건수가 해당 값 개수만큼 증가"),
 ]),
 ("ot_dim_dmmbm03_m02 · 2단계 품질 및 전처리 (test_m02_quality.py)", [
  ("UT-M02-01", "기본 품질 카드", "2단계 진입(탐지 전)", "408행×16변수, 결측 65건(공백 값 포함), 중복 5행, 이상치 「탐지 전」"),
  ("UT-M02-02", "이상치 탐지 7종 실행", "IQR·Z-score·수정 Z·Grubbs·마할라노비스·Isolation Forest·LOF", "study_hours: IQR 10, Z 7, 수정 Z 10, Grubbs 10 (pandas·Python 재계산). 마할라노비스·IF·LOF는 실행·진단 표시"),
  ("UT-M02-03", "마할라노비스 임계값", "기본(χ² 97.5% 분위수)과 「D² > 9 (거리 D > 3.0)」 선택", "기본은 서버가 χ² 분위수로 해석하는 값(1)을 전송, D² > 9 는 D>3 인 행 수(148)와 일치, 카드는 변수별 합이 아닌 이상치 행 수"),
  ("UT-M02-04", "임계값 변경 재탐지", "IQR 배수 1.5 → 3.0", "전체 이상치 건수 감소, study_hours 값이 pandas와 일치"),
  ("UT-M02-05", "전처리 기본 선택", "화면 진입", "결측=처리 안 함, 이상치=원본값 보존, 스케일링=미적용, 중복=유지가 각 그룹 맨 위에 선택됨"),
  ("UT-M02-06", "결측 처리", "중앙값/평균/최빈값/0 대체 → 3단계", "study_hours 평균이 pandas 대체 결과와 일치, 결측 없음. 행 제거는 결측 행 전체(350행) 제거 【현재 실패 예상: D-09】"),
  ("UT-M02-07", "이상치 처리", "윈저라이징/로그/행 제거(IQR 1.5)", "윈저라이징 최대=상한 경계, 로그=자연로그 평균, 행 제거 후 398행 【행 제거 현재 실패 예상: D-10】"),
  ("UT-M02-08", "스케일링", "표준화/정규화/로버스트", "평균 0·표준편차 1 / [0,1] / 중앙값 0, 표준화 설명에 ddof=0 표기"),
  ("UT-M02-09", "3단계 진행 조건", "탐지 전·후 [3단계] 버튼", "탐지 전 비활성, 탐지 응답 후 활성"),
  ("UT-M02-10", "ID·이진 열 제외", "이상치 진단 표 확인", "school_id·treatment·passed 등 ID·이진 열이 진단 대상에서 제외되고 제외 열이 안내됨"),
  ("UT-M02-11", "전처리 요청의 적용 열", "중앙값 대체 규칙으로 3단계 진행", "/preprocess 요청의 columns 에 식별자·이진 열이 없음"),
 ]),
 ("ot_dim_dmmbm03_m03 · 3단계 데이터 탐색 (test_m03_eda.py)", [
  ("UT-M03-01", "기초통계 표", "3단계 진입(qa_clean_reference.csv)", "N·평균·표준편차(ddof=1)·최소·Q1·중앙값·Q3·최대·왜도·첨도가 pandas와 일치"),
  ("UT-M03-02", "피어슨 상관 행렬", "방법: 피어슨", "행렬 값이 pandas corr과 일치(소수 2자리 표시 기준)"),
  ("UT-M03-03", "스피어만·켄달 상관", "방법 전환", "스피어만은 spearman, 켄달은 tau-b와 일치, 제목에 τ-b 표기"),
  ("UT-M03-04", "상위 변수쌍", "상관 강도 상위 목록", "|r| 내림차순이고 첫 쌍이 전체 최대"),
  ("UT-M03-05", "전처리 반영", "2단계에서 표준화 적용 후 진입", "기초통계가 평균 0·표준편차 1로 표시"),
 ]),
 ("ot_dim_dmmbm03_m04 · 4-1 통계 모형 설정·실행 (test_m04_modeling.py)", [
  ("UT-M04-01", "기법 13종 전환", "13개 기법 카드를 차례로 선택", "카드 13개, 선택마다 영역 전환, 스크립트 오류 없음"),
  ("UT-M04-02", "필수 항목 표시", "HLM 선택, 종속·집단 변수 비움 → 선택", "빨간 *, 「필수 선택 항목입니다.」와 빨간 테두리, 선택하면 즉시 해제"),
  ("UT-M04-03", "HLM 고정효과 선택 사항", "고정효과 변수 없이 실행", "집단·종속변수만으로 실행 성공(적합 완료), 오류 패널 없음"),
  ("UT-M04-04", "역할 중복 차단", "종속변수 score_t4 지정", "독립변수 목록의 score_t4는 선택 불가, 「종속변수로 사용 중」 표시"),
  ("UT-M04-05", "선형회귀 실행·리포트 이동", "선형회귀 실행 → [4-2 결과 보기]", "적합 완료, 리포트 화면에 기법명 표시"),
  ("UT-M04-06", "필수 누락 시 실행 차단", "HLM 필수 항목 비우고 실행", "누락 항목 표시, 새 분석이 시작되지 않음"),
  ("UT-M04-07", "상관분석 변수 후보", "상관분석 선택", "수치형·이진 열만 표시(범주형·ID·날짜·상수 제외)"),
  ("UT-M04-08", "종속변수 자동 선택 없음", "선형회귀 선택 직후", "종속변수가 비어 있고 필수 안내 표시"),
  ("UT-M04-09", "군집·PCA 표준화 기본", "K-평균 선택 후 실행", "「표준화 후 분석」이 기본 켜짐, 분석 요청에 scaling 을 보내지 않아 서버 기본(표준화)을 따름"),
  ("UT-M04-10", "군집·PCA 원 단위 분석", "PCA 선택, 「표준화 후 분석」 해제 후 실행", "분석 요청의 scaling 이 none"),
 ]),
 ("ot_dim_dmmbm03_m05 · 4-2 분석 결과 리포트 (test_m05_report.py)", [
  ("UT-M05-01", "결과 요약 카드", "HLM(무조건모형) 리포트 진입", "제목에 기법명, 집단 수·관측치·로그우도 표시, ICC가 statsmodels 값과 일치"),
  ("UT-M05-02", "표준 통계 결과표", "표 값 확인", "절편·τ00·σ²·로그우도·AIC가 statsmodels(REML/ML)와 일치, AIC/BIC 기준을 「(ML 기준)」으로 정확히 표기"),
  ("UT-M05-03", "추천 차트", "진단 시각화 차트 탭", "차트가 그려지고 데이터가 없는 차트는 표시되지 않음(탭 개수도 표시되는 차트 수)"),
  ("UT-M05-04", "차트 상세 보기", "차트 선택", "상세 보기로 전환(이전/다음·데이터 보기 컨트롤)"),
  ("UT-M05-05", "원시데이터·잔차", "원시데이터 탭", "관측치 수(400)와 표 표시"),
  ("UT-M05-06", "내부 필드명 미노출", "표·차트 텍스트 확인", "const_se, group_variance 등 내부 필드명이 없음"),
  ("UT-M05-07", "결과 저장", "[결과 저장] → 5단계", "저장한 분석이 목록에 표시"),
 ]),
 ("ot_dim_dmmbm03_m06 · 5단계 결과 관리 (test_m06_packaging.py)", [
  ("UT-M06-01", "패키지 목록·상세", "5단계 진입 → 패키지 선택", "목록에 표시, 상세에 PDF·Excel·공유·재현 버튼"),
  ("UT-M06-02", "PDF 내보내기", "[PDF 보고서]", "다운로드 성공(%PDF), 한글 본문 추출"),
  ("UT-M06-03", "Excel 내보내기", "[Excel 통계표]", "분석 하나 = 시트 하나(시트 이름은 분석 이름), 표 내용 포함"),
  ("UT-M06-04", "내보낸 값 일치", "PDF·Excel 값 확인", "ICC·로그우도·AIC·분산성분이 계산값과 일치(= 4-2 화면 값)"),
  ("UT-M06-05", "공유 링크·삭제", "공유 발급/해제, 삭제 [취소]/[삭제]", "발급·해제 동작, 취소 시 유지, 삭제 시 목록에서 제거"),
 ]),
]

INTEG = [
 ("IT-01 핵심 업무 흐름 (1→2→3→4→5)", [
  ("IT-01-01", "파일 반입 후 분석 완료까지", "qa_clean_reference.csv 반입 → 2단계 IQR 탐지 → 3단계 → 4단계 선형회귀 → 4-2 → 결과 저장 → 5단계", "각 단계 이동·데이터 유지, 최종 패키지 생성"),
  ("IT-01-02", "단계 간 데이터 유지", "각 단계 이동 후 뒤로 가기", "선택 데이터셋·설정이 유지되고 복원 정책(진입 시 이전 선택 미복원)과 일치"),
  ("IT-01-03", "직접 URL 접근", "데이터 없이 2~5단계 URL 직접 접근", "안내 후 1단계로 이동(가드 복원 확인)"),
 ]),
 ("IT-02 다중 파일 반입 → 결합 → 분석", [
  ("IT-02-01", "3개 파일 동시 반입", "CSV(UTF-8)·CSV(CP949)·XLSX 동시 선택", "3건 반입·자동 선택, 결합 영역 표시"),
  ("IT-02-02", "결합 후 분석", "qa_main + qa_school 결합 → 2~4단계", "결합 데이터셋(행 수 정답 일치)이 이후 단계에 사용됨"),
  ("IT-02-03", "카드 + 파일 혼합 결합", "카드 1개 + 업로드 1개 결합", "키 매핑·결합·분석 가능, 30MB 합계 제한 적용"),
 ]),
 ("IT-03 전처리 규칙 전파", [
  ("IT-03-01", "전처리 → 통계 → 모델링", "중앙값 대체 + 윈저라이징 + 표준화 적용 후 3·4단계", "3단계 통계와 4단계 분석이 전처리된 데이터 기준"),
  ("IT-03-02", "규칙 기록", "분석 실행 후 4-2·PDF 확인", "적용한 전처리 규칙(순서 포함)이 리포트에 기록됨"),
  ("IT-03-03", "재분석 시 규칙 재적용", "파라미터 변경 후 재실행", "같은 규칙으로 다시 계산, 결과가 파라미터에 맞게 변경"),
 ]),
 ("IT-04 13개 기법 종단 실행", [
  ("IT-04-01", "기법별 실행→리포트", "상관·회귀·로지스틱·트리 2종·군집 3종·PCA·ANOVA·HLM·성장곡선·PSM 각각 실행", "13개 모두 실행 성공, 4-2 표·차트 정상 표시"),
  ("IT-04-02", "가정 위반 데이터 경고", "공선성·불균형·미수렴 등 데이터로 실행", "해당 경고 문구 표시(현재 미표시 — 결함 확인 항목)"),
  ("IT-04-03", "부적합 변수 선택 차단", "타입에 맞지 않는 변수·기법 조합", "차단 또는 안내"),
 ]),
 ("IT-05 외부 분석 API 연계", [
  ("IT-05-01", "세션 발급·토큰 헤더", "첫 접속", "POST /api/v1/sessions 성공, 이후 호출에 토큰 헤더 전달"),
  ("IT-05-02", "작업(job) 비동기 처리", "업로드·분석 실행", "202 응답 → 작업 폴링 → 결과 조회, 진행 상태 표시"),
  ("IT-05-03", "상위 API 오류·지연", "API 중단 또는 느린 응답", "시간 초과·오류가 화면 안내로 표시, 화면이 멈추지 않음"),
  ("IT-05-04", "세션·데이터 만료", "1시간 이상 미사용 후 이용", "만료 안내 후 1단계 복귀 또는 재발급"),
  ("IT-05-05", "프록시 하위 경로", "APP_BASE_PATH/리버스 프록시 경유", "화면·API 경로가 하위 경로에서도 정상"),
 ]),
 ("IT-06 내보내기 연계", [
  ("IT-06-01", "화면·PDF·Excel 값 일치", "같은 분석 3종 비교(13개 기법)", "표·지표 값이 동일"),
  ("IT-06-02", "PDF 한글·차트", "PDF 열기", "한글 글꼴, 차트 이미지 정상"),
  ("IT-06-03", "대용량·다수 분석 패키지", "분석 여러 건을 담아 내보내기", "시간 초과 없이 생성"),
 ]),
 ("IT-07 패키지 재현·공유", [
  ("IT-07-01", "재현 실행", "5단계 [재현]", "같은 설정으로 분석 재실행, 결과 일치"),
  ("IT-07-02", "공유 링크", "발급 → 비로그인 브라우저 접근 → 해제", "발급 시 열람 가능, 해제 후 접근 불가"),
 ]),
 ("IT-08 데이터관리카드 연계", [
  ("IT-08-01", "카드 조회·선택·분석", "카드 검색 → 선택 → 분석", "카드 목록·행 수 표시, 적재 중·실패 카드는 선택 불가"),
  ("IT-08-02", "카드 타입 변경", "카드 변수 타입 변경", "원본은 유지되고 새 데이터셋이 생성되어 이후 단계에 사용"),
 ]),
 ("IT-09 예외·비정상 흐름", [
  ("IT-09-01", "업로드 중 이동·새로고침", "업로드 진행 중 새로고침", "중복·고아 데이터 없이 복구"),
  ("IT-09-02", "용량 제한 연계", "합계 30MB 경계 데이터셋 선택", "초과 선택 불가, 해제 시 재활성"),
  ("IT-09-03", "브라우저 호환", "Chrome 최신·Edge", "주요 흐름 정상"),
 ]),
 ("IT-10 포털 연계 (edisn-ots 이식 시)", [
  ("IT-10-01", "메뉴 진입·레이아웃", "포털 메뉴에서 ot_dim_dmmbm03_m01 진입", "공통 header/footer 적용, 스타일 충돌 없음"),
  ("IT-10-02", "인증·세션 연계", "로그인 사용자로 진입", "포털 인증 후 분석 API 세션 연계 방식대로 동작"),
  ("IT-10-03", "화면 간 이동 URL", "m01~m06 이동", "포털 URL 체계(/ot/dim/dmm/bm/…)로 이동"),
 ]),
]

# ---------------------------------------------------------------- 문서 생성
def cover(doc, title, doc_kind):
    lp = doc.add_paragraph(); lp.alignment = WD_ALIGN_PARAGRAPH.CENTER          # 회사 로고(표지 맨 위, 가운데)
    lp.add_run().add_picture(LOGO, width=Cm(LOGO_WIDTH_CM))
    for _ in range(4): para(doc, "")
    para(doc, title, 26, True, 'c', space_after=14)
    para(doc, PROJECT, 13, False, 'c', space_after=60)
    t = table(doc, ["항목", "내용"], [["작성일", TODAY], ["버  전", "0.1"]], [4, 6], size=10)
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    page_break(doc)
    para(doc, "문서 개정 이력", 14, True, 'c', space_after=8)
    table(doc, ["문서명", doc_kind], [], [4, 12], size=10)
    rows = [["0.1", TODAY, "최초 작성", "", "", ""]] + [[""] * 6 for _ in range(7)]
    table(doc, ["버전", "날짜", "내용", "작성자", "검토자", "승인자"], rows, [1.6, 2.6, 6.0, 2.2, 2.2, 2.2], size=9, center_cols=(0, 1))
    page_break(doc)

def toc(doc, items):
    para(doc, "목    차", 14, True, 'c', space_after=8)
    for it in items:
        lvl2 = it[:2] in ("가.", "나.", "다.", "라.", "마.")
        para(doc, it, 10, False, indent=0.9 if lvl2 else 0.2, space_after=1)
    page_break(doc)

def cases_appendix(doc, groups, title):
    h1(doc, title)
    n = 0
    for gname, cases in groups:
        h2(doc, gname)
        table(doc, ["케이스 ID", "테스트 항목", "절차 / 입력", "기대 결과", "결과"],
              [[c[0], c[1], c[2], c[3], ""] for c in cases], [2.2, 3.0, 4.6, 6.0, 1.2], size=8, center_cols=(0, 4))
        n += len(cases)
    para(doc, f"※ 총 {n}개 케이스 (초안). 결과란은 수행 후 Pass/Fail로 기재한다.", 9)
    return n

def progress(doc, groups, key_label):
    rows = []; tot = 0
    for gname, cases in groups:
        rows.append([gname, str(len(cases)), "", "", "", "", "", "", "", "0%"]); tot += len(cases)
    rows.append(["총계", str(tot), "", "", "", "", "", "", "", "0%"])
    table(doc, [key_label, "Case 총계", "Tester", "계획 시작", "계획 완료", "수행 시작", "수행 완료", "Pass", "Fail", "진척율"],
          rows, [4.6, 1.5, 1.6, 1.6, 1.6, 1.6, 1.6, 1.1, 1.1, 1.4], size=8, center_cols=(1, 3, 4, 5, 6, 7, 8, 9))
    para(doc, "※ 진척율 = (수행된 케이스 수 합 / 작성된 테스트 케이스 수 합) × 100", 9)
    return tot

SEV = [["치명", "통계값이 틀리거나 잘못된 해석·결론으로 이어지는 결함, 시스템 중단", "즉시 조치, 재개 전 필수"],
       ["높음", "주요 기능 오동작·실패, 데이터 손실·오표기, 핵심 흐름 불가", "다음 차수 이전 조치"],
       ["중간", "기능은 동작하나 안내·표시·제한이 부적절", "일정 협의 후 조치"],
       ["낮음", "문구·배치 등 경미한 결함", "여유 시 조치"]]

def build(kind):
    UT = kind == 'UT'
    w = "단위" if UT else "통합"
    title = f"{w}테스트계획서"
    groups = UNIT if UT else INTEG
    doc = Document()
    s = doc.sections[0]; s.page_width = Cm(21); s.page_height = Cm(29.7)
    s.left_margin = s.right_margin = Cm(2.0); s.top_margin = Cm(2.0); s.bottom_margin = Cm(1.8)
    doc.styles['Normal'].font.name = FONT; doc.styles['Normal'].element.rPr.rFonts.set(qn('w:eastAsia'), FONT)
    footer_pages(doc)
    cover(doc, title, title)
    toc_items = ["1. 목적", "가. 개요", "2. 용어 정의"] + \
        (["가. 단위 테스트(Unit Testing)", "나. 테스트 베드(Test Bed)", "다. 테스트 스텁(Test Stub)", "라. 테스트 드라이버(Test Driver)", "마. 프로젝트 용어"] if UT else
         ["가. 통합 테스트(Integration Testing)", "나. 테스트 베드(Test Bed)", "다. 테스트 스텁(Test Stub)", "라. 테스트 드라이버(Test Driver)", "마. 프로젝트 용어"]) + \
        ["3. 테스트 전략", "가. 테스트 목적", "나. 테스트 수행절차", "다. 테스트 수행기준", f"4. 테스트 범위", f"가. {w} 테스트 범위", f"나. {w} 테스트 제외 범위",
         "5. 테스트 환경", "가. 하드웨어", "나. 소프트웨어", "6. 테스트 조직과 역할", "가. 테스트 조직", "나. 역할 및 책임", "7. 테스트 수행 일정",
         "8. 테스트 데이터 생성 및 유지절차", "9. 테스트 관리활동", "가. 결함 관리", "나. 진척 관리", "10. 테스트 고려사항", "11. 산출물",
         f"부록 A. {w} 테스트 케이스 목록(초안)", "부록 B. 사전 점검(QA) 결과 요약"]
    toc(doc, toc_items)

    # 1. 목적
    h1(doc, "1. 목적"); h2(doc, "가. 개요")
    para(doc, f"본 문서는 {PROJECT}의 {w} 테스트 범위, 일정, 소요 자원, 테스트 환경 등에 대해 기술한 {w} 테스트 계획서이다.", indent=0.6)
    if UT:
        para(doc, "단위는 화면(JSP + JS) 1개와 서버(Java) 클래스·공통 모듈 1개를 하나의 단위로 본다. 화면 ID는 ot_dim_dmmbm03_m01 ~ m06을 기준으로 한다.", indent=0.6)
    else:
        para(doc, "통합은 화면 간 흐름(1→5단계), 서버(프록시)와 외부 분석 API의 연계, 내보내기(PDF/Excel), 데이터관리카드·포털과의 연계를 하나의 업무 흐름으로 본다.", indent=0.6)

    # 2. 용어
    h1(doc, "2. 용어 정의")
    if UT:
        defs = [("가. 단위 테스트(Unit Testing)", "프로그램의 가장 작은 단위(화면, 클래스, 함수)가 설계대로 동작하는지 개별적으로 검증하는 테스트이다."),]
    else:
        defs = [("가. 통합 테스트(Integration Testing)", "전체 시스템이 통합 완료될 때까지 단위 시스템간의 연계성(Interface) 및 기능 요구 사항들을 검증하고 하드웨어와 소프트웨어 구성 요소간의 상호 작용을 테스트하는 것이다.")]
    defs += [("나. 테스트 베드(Test Bed)", "테스트를 수행하기 위한 환경을 의미하며, 테스트 수행에 필요한 하드웨어, 계측기, 시뮬레이터, 소프트웨어 툴 그 밖의 지원요소를 포함하는 환경이다. [After IEEE 610]"),
             ("다. 테스트 스텁(Test Stub)", "아직 작성되지 않은 함수를 대체하기 위해 작성된 함수로, 최소한의 기능만 제공하며, 프로그램이 제대로 호출되는 지 테스트하기 위해 사용된다."),
             ("라. 테스트 드라이버(Test Driver)", "테스트 할 함수를 호출하기 위해 작성된 함수로, 일반적으로 함수 호출 시 필요한 파라미터와 변수로 구성되어 있다.")]
    for a, b in defs: h2(doc, a); para(doc, b, indent=0.9)
    h2(doc, "마. 프로젝트 용어")
    table(doc, ["용어", "설명"], [
        ["화면 ID", "JSP 파일명과 동일한 화면 식별자. ot_dim_dmmbm03_m01(데이터 반입·결합), m02(품질·전처리), m03(기초통계·상관), m04(모형 설정·실행), m05(분석 결과 리포트), m06(결과 관리)"],
        ["분석 API", "분석·반입·내보내기 기능을 제공하는 외부 API 서버(FastAPI). 서버(Java)는 /api/v1/** 요청을 UPSTREAM_API_BASE로 전달하는 프록시 역할을 한다."],
        ["작업(job)", "무거운 요청에 대해 분석 API가 202로 응답하고 상태를 조회해 결과를 받는 비동기 처리 단위"],
        ["허용 오차", "화면 값과 Python 독립 계산 값의 비교 기준. 소수점 3자리 또는 상대오차 1e-4"],
        ["Python 독립 계산", "같은 데이터를 pandas·scipy·statsmodels·scikit-learn으로 재계산하여 화면 값과 대조하는 검증 방식"],
    ], [3.2, 13.8], center_cols=(0,))

    # 3. 전략
    h1(doc, "3. 테스트 전략")
    if UT:
        para(doc, "본 프로젝트는 화면 6개(ot_dim_dmmbm03_m01~m06)를 단위로 구분하여 각각 독립적으로 검증한다. 단위 테스트는 tests/ui 의 자동화 코드(Playwright + pytest)로 수행한다. 실제 Chrome 에서 화면을 조작하고, 표시된 값은 테스트 데이터 CSV 를 pandas·scipy·statsmodels 로 직접 계산한 기대값과 대조한다. 알려진 결함으로 아직 실패하는 케이스는 xfail(사유 = 결함 번호)로 표시하여 결함이 조치되면 알 수 있게 한다.", indent=0.6)
    else:
        para(doc, "본 프로젝트는 단위 테스트 완료 후 점진적 통합 테스트 방식(Incremental Integration Strategy)을 적용한다. 1단계는 화면 간 업무 흐름(1→5단계)과 서버·분석 API 연계를 검증하고, 2단계는 내보내기·데이터관리카드·포털(edisn-ots) 연계 및 예외 흐름을 검증한다.", indent=0.6)
    h2(doc, "가. 테스트 목적")
    purposes = ["화면 단위 기능의 요구 대비 적합성 확인", "화면에 표시되는 값의 정확도 확인(Python 독립 계산 대조)", "입력 검증·오류 안내 등 예외 처리의 적절성 확인", "비정상적인 결과(에러 또는 버그) 발생 부분의 확인 및 해결", "수정 후 회귀 확인(자동 테스트 재실행)"] if UT else \
        ["사용자 관점의 업무 흐름(반입 → 전처리 → 탐색 → 모델링 → 결과 관리) 경로의 적절성 확인", "서버(프록시)와 외부 분석 API 간 연계·연동 확인", "단계 간 데이터·설정 전달(전처리 규칙 전파 등) 확인", "화면·PDF·Excel 간 결과 값 일치 확인", "비정상 흐름(만료·오류·시간 초과)에서의 동작 확인"]
    for p in purposes: bullet(doc, p)
    h2(doc, "나. 테스트 수행절차")
    steps = (["① 테스트 케이스 작성·검토", "② 테스트 환경·데이터 준비", "③ 단위 테스트 수행(pytest 실행)", "④ 결함 등록·조치", "⑤ 재테스트", "⑥ 결과 보고"] if UT else
             ["① 시나리오·케이스 작성·검토", "② 통합 환경 구축(앱·분석 API)", "③ 1차 통합 테스트(업무 흐름)", "④ 결함 조치·재테스트", "⑤ 2차 통합 테스트(연계·예외)", "⑥ 결과 보고"])
    table(doc, ["수행 절차"] * len(steps), [steps], [17.0 / len(steps)] * len(steps), size=8, center_cols=tuple(range(len(steps))))
    h2(doc, "다. 테스트 수행기준")
    table(doc, ["기준", "내용", "비고"], [
        ["선행기준", f"테스트 환경(앱 서버·분석 API·브라우저) 구축 완료\n테스트 케이스 작성 및 검토/승인 완료\n테스트 수행일정 및 Activity 수립 완료\n테스트 데이터 준비 및 검증 완료", ""],
        ["중단기준", "테스트 진행이나 결과에 심각한 영향을 주는 결함 발생(치명 등급)\n분석 API 장애 등 환경 문제로 수행 불가\n프로젝트 또는 고객의 요청", ""],
        ["재개기준", "중대한 결함이 조치 완료됨\n환경 장애 복구\n프로젝트 또는 고객의 요청", ""],
        ["완료 기준", f"케이스 수행률 100%\n치명·높음 등급 결함 조치 완료(미조치 0건)\n통계 계산 대조가 허용 오차 이내\n미조치 결함은 사유와 조치 계획 합의 {TBD}", "수치 기준 합의 필요"],
    ], [3.0, 11.0, 3.0], center_cols=(0,))

    # 4. 범위
    h1(doc, "4. 테스트 범위"); h2(doc, f"가. {w} 테스트 범위")
    para(doc, f"{w} 테스트 범위는 다음과 같다.", indent=0.6)
    if UT:
        scope = [["1", "ot_dim_dmmbm03_m01 데이터 반입·결합", "파일 업로드(CSV·XLSX·다중), 데이터관리카드, 변수 속성, 미리보기, 삭제, 결합"],
                 ["2", "ot_dim_dmmbm03_m02 품질 및 전처리", "품질 진단, 이상치 탐지 7종, 결측·이상치·스케일링 처리"],
                 ["3", "ot_dim_dmmbm03_m03 데이터 탐색", "기초통계, 피어슨·스피어만·켄달 상관"],
                 ["4", "ot_dim_dmmbm03_m04 모형 설정·실행", "분석 기법 13종 선택·설정·실행, 필수 항목 안내"],
                 ["5", "ot_dim_dmmbm03_m05 분석 결과 리포트", "결과표, 추천 차트, 차트 상세, 원시데이터·잔차, 결과 저장"],
                 ["6", "ot_dim_dmmbm03_m06 결과 관리", "패키지 목록, PDF/Excel 내보내기, 공유·삭제"]]
        excl = [["1", "서버(Java) 클래스·공통 JS 모듈 단위 테스트", "본 계획은 화면 단위로 한정. 필요 시 별도 계획 수립"],
                ["2", "13개 기법 전체의 계산 정확도 검증", "화면 단위에서는 다층모형(대표)의 표시 값만 대조. 전체 기법은 별도 Python 대조(QA 리포트)로 수행"],
                ["3", "분석 API 내부 로직", "별도 팀 관리. 화면에 표시된 값만 검증"],
                ["4", "포털 공통 헤더·푸터·메뉴, 로그인", "포털 공통 영역 / 로그인은 현재 미구현"],
                ["5", "성능·부하·보안 취약점 점검", "별도 테스트로 구분"],
                ["6", "다중 시트 XLSX 반입", "지원하지 않음(시트가 여러 개면 첫 시트만 반입됨). XLSX 는 시트가 하나인 파일만 반입 대상이므로 테스트도 단일 시트 파일로 수행"]]
    else:
        scope = [["1", "1→5단계 종단 업무 흐름", "반입 → 전처리 → 탐색 → 모델링 → 결과 관리까지의 연속 처리 (IT-01)"],
                 ["2", "다중 파일 반입·결합·분석", "여러 파일 반입 후 결합 데이터셋으로 이후 단계 수행 (IT-02)"],
                 ["3", "전처리 규칙 전파", "2단계 규칙이 3·4단계 및 리포트에 반영 (IT-03)"],
                 ["4", "13개 기법 종단 실행", "기법별 설정 → 실행 → 4-2 결과 (IT-04)"],
                 ["5", "서버–분석 API 연계", "세션 발급, 토큰 전달, 작업 폴링, 오류·시간 초과, 만료 (IT-05)"],
                 ["6", "내보내기 연계", "화면·PDF·Excel 값 일치 (IT-06)"],
                 ["7", "패키지 재현·공유", "재현 실행, 공유 링크 (IT-07)"],
                 ["8", "데이터관리카드 연계", "카드 조회·선택·타입 변경 (IT-08)"],
                 ["9", "예외·비정상 흐름", "새로고침·용량 경계·브라우저 (IT-09)"],
                 ["10", "포털(edisn-ots) 연계", "이식 시 메뉴·레이아웃·인증·URL 연계 (IT-10)"]]
        excl = [["1", "분석 API 내부 로직", "별도 팀 관리. 연계 인터페이스와 응답 값 검증으로 한정"],
                ["2", "로그인·회원 관리 연계", "미구현. 포털 인증 연계(IT-10-02)는 이식 결정 후 수행"],
                ["3", "성능·부하·보안 취약점 점검", "별도 테스트로 구분"],
                ["4", "모바일·태블릿 화면", "본 단계 지원 범위 외"],
                ["5", "다중 시트 XLSX 반입", "지원하지 않음(시트가 여러 개면 첫 시트만 반입됨). XLSX 는 시트가 하나인 파일만 반입 대상이므로 테스트도 단일 시트 파일로 수행"]]
    table(doc, ["No.", "기능" if not UT else "대상", "설명"], scope, [1.2, 5.6, 10.2], center_cols=(0,))
    h2(doc, f"나. {w} 테스트 제외 범위")
    para(doc, f"{w} 테스트의 제외 범위는 다음과 같다.", indent=0.6)
    table(doc, ["No.", "제외 범위", "제외 사유"], excl, [1.2, 6.0, 9.8], center_cols=(0,))

    # 5. 환경
    h1(doc, "5. 테스트 환경"); h2(doc, "가. 하드웨어")
    para(doc, f"{w} 테스트를 위한 하드웨어 요구사항은 다음과 같다.", indent=0.6)
    table(doc, ["No.", "하드웨어", "필요 수량", "보유 수량", "비고"], [
        ["1", "테스트 수행 PC(브라우저 구동)", "1", TBD, "인원 수에 맞춰 조정"],
        ["2", "애플리케이션 서버(VM): WAS 구동", "1", TBD, "공공클라우드 VM 사양 확정 후 기재"],
        ["3", "분석 API 서버(FastAPI)", "1", TBD, "기존 테스트 서버 사용 여부 확인"],
    ], [1.2, 7.0, 2.2, 2.2, 4.4], center_cols=(0, 2, 3))
    h2(doc, "나. 소프트웨어")
    para(doc, f"{w} 테스트를 위한 소프트웨어 요구사항은 다음과 같다.", indent=0.6)
    sw = [["1", "웹 브라우저: Chrome(검증 환경 157.x), Edge", "1", TBD, "최신 안정 버전"],
          ["2", "JDK 8 이상 (빌드 대상 Java 7), Maven 3.x", "1", TBD, "운영 JDK 버전 확정 필요"],
          ["3", "WAS: Tomcat 7 이상 (Servlet 3.0, JSP 2.2)", "1", TBD, "Spring MVC 4.3 기반 WAR"],
          ["4", "분석 API: UPSTREAM_API_BASE로 지정한 FastAPI 서버", "1", TBD, "테스트 서버 주소 확정 필요"]]
    if UT: sw += [["5", "Python 3.12 + pytest, Playwright", "1", TBD, "tests/ui 자동 테스트 실행(필수)"],
                  ["6", "pandas·numpy·scipy·statsmodels·openpyxl·pypdf", "1", TBD, "기대값 계산·내보내기 파일 검증용"]]
    else: sw += [["5", "Python 3.12 + pandas·scipy·statsmodels·scikit-learn", "1", TBD, "내보내기·값 대조용"],
                 ["6", "PDF/Excel 열람 도구(Acrobat, Excel/한셀)", "1", TBD, "내보내기 확인용"],
                 ["7", "edisn-ots 개발 환경(이식 검증 시)", "1", TBD, "IT-10 수행 시"]]
    table(doc, ["No.", "소프트웨어", "필요 수량", "보유 수량", "비고"], sw, [1.2, 7.6, 2.0, 2.0, 4.2], center_cols=(0, 2, 3))

    # 6. 조직
    h1(doc, "6. 테스트 조직과 역할"); h2(doc, "가. 테스트 조직")
    para(doc, f"PM → 테스트 관리(QA) → PL → 개발자 · 현업 TFT 순으로 보고·협업한다. 조직도와 담당자 이름은 확정 후 기재한다 {TBD}.", indent=0.6)
    h2(doc, "나. 역할 및 책임")
    table(doc, ["조직", "역할", "담당자"], [
        ["Steering Committee", "프로젝트/현업 협업체계 조율", "현업 TFT, PM"],
        ["PM", "테스트 전반적인 관리\n이슈사항 해결 지원 및 모니터링\n테스트 검토 및 승인", "PM"],
        ["테스트 관리", "테스트 계획서 검토\n테스트케이스 작성 가이드 및 적정성 검토\n테스트 진척 및 결함관리 현황 검토", "QA, 현업 TFT"],
        ["PL", f"{w} 테스트 계획서 작성\n테스트 설계/결과 검토\n테스트 실행 및 진척 모니터링", "PL, 현업 TFT"],
        ["개발자", "테스트 케이스 작성·수행 및 진척 등록\n결함 등록 및 발견된 결함 조치", "개발자"],
    ], [3.6, 9.4, 4.0], center_cols=(0,))

    # 7. 일정
    h1(doc, "7. 테스트 수행 일정")
    para(doc, f"본 문서는 프로젝트에서 개발한 시스템을 효과적으로 {w} 테스트가 가능한 일정을 구체적으로 기술한다. 일정은 확정 후 기재한다 {TBD}.", indent=0.6)
    D = "YY.MM.DD ~ YY.MM.DD"
    tasks = ([["단위테스트 계획서 보완", D, ""], ["단위테스트 케이스 작성(부록 A 보완)", D, ""], ["테스트 환경·데이터 준비", D, ""],
              ["1차 단위테스트 수행", D, ""], ["1차 식별된 결함 조치", D, ""], ["2차 단위테스트(재테스트) 수행", D, ""], ["결과 조치내역 확인", D, ""]] if UT else
             [["통합테스트 계획서 보완", D, ""], ["통합테스트 시나리오 및 케이스 작성", D, ""], ["통합테스트 환경 구축(앱·분석 API)", D, ""],
              ["1차 통합테스트 수행(업무 흐름)", D, ""], ["1차 식별된 결함 조치", D, ""], ["2차 통합테스트 수행(연계·예외)", D, ""],
              ["2차 식별된 결함 조치", D, ""], ["통합테스트 결과 조치내역 확인", D, ""]])
    rows = [[w + "테스트", t[0], t[1], t[2]] for t in tasks] + [["PL", f"{w}테스트 결과보고서 작성 및 보고", D, ""], ["현업 TFT", "결함보고서 및 결과보고서 작성", D, ""]]
    table(doc, ["구분", "Task", "일정", "비고"], rows, [3.0, 7.6, 4.4, 2.0], center_cols=(0,))

    # 8. 데이터
    h1(doc, "8. 테스트 데이터 생성 및 유지절차")
    para(doc, "테스트 데이터는 알려진 정답값을 가진 합성 데이터를 사용한다. 생성 스크립트(gen_data.py, seed 20261109)로 재현 가능하며, 심어 둔 문제와 정답값은 truth.json에 기록한다.", indent=0.6)
    table(doc, ["파일", "용도", "포함 내용"], [
        ["qa_main_utf8.csv / qa_main_cp949.csv", "반입·품질·전처리 점검", "408행 16열. 결측(study_hours MCAR 5%, income MAR), 위장 결측(\"-\", 999, -1), 이상치 10개, 중복(완전 5행·키 3행), 쉼표 숫자, 앞자리 0 코드, 상수 열"],
        ["qa_main.xlsx", "XLSX 반입 점검", "qa_main_utf8.csv 와 같은 내용의 단일 시트 XLSX (다중 시트 파일은 지원하지 않으므로 사용하지 않음)"],
        ["qa_mixed_column_minimal.xlsx", "XLSX 혼합 열 점검", "한 열에 숫자와 문자가 섞인 5행 단일 시트 XLSX (결함 D-24 재현용, 현재 반입 실패)"],
        ["qa_school.csv", "결합 점검", "school_id 숫자 키, 미매칭 키, 1:N 키"],
        ["qa_clean_reference.csv", "계산 정확도 대조", "문제를 주입하지 않은 400행 기준 데이터"],
    ], [4.6, 3.6, 8.8])
    for b in ["데이터 변경(생성·수정·삭제)은 테스트 케이스 순서에 따르며, 데이터 파일 원본은 변경하지 않는다.",
              "반입 데이터는 분석 API가 마지막 사용 후 1시간이 지나면 삭제하므로 차수별로 새로 반입한다.",
              "테스트 종료 후 반입한 데이터셋과 분석 결과는 화면의 삭제 기능으로 정리한다.",
              "실제 개인정보·운영 데이터는 사용하지 않는다."]: bullet(doc, b)
    if not UT: bullet(doc, "연계 시나리오(IT-05, IT-10)는 분석 API 테스트 서버와 포털 개발 환경이 준비된 후 수행한다.")

    # 9. 관리
    h1(doc, "9. 테스트 관리활동"); h2(doc, "가. 결함 관리")
    para(doc, "결함은 발견 즉시 이슈로 등록하고 아래 절차로 관리한다(이슈 관리 도구는 확정 후 기재 " + TBD + ").", indent=0.6)
    table(doc, ["결함 관리 절차"] * 5, [["① 결함 등록\n(재현 절차·기대/실제값·캡처)", "② 분류\n(서버/화면/양쪽, 심각도)", "③ 조치\n(담당자 지정·수정)", "④ 재테스트\n(조치 확인)", "⑤ 종료\n(결과 보고 반영)"]], [3.4] * 5, size=8, center_cols=(0, 1, 2, 3, 4))
    para(doc, "심각도 기준", 10, True, indent=0.6)
    table(doc, ["등급", "정의", "조치 기준"], SEV, [2.0, 10.0, 5.0], center_cols=(0,))
    para(doc, "결함 등록 시 '조치 위치'(서버 / 화면 / 서버+화면)를 함께 기재하여 담당 팀에 배정한다.", indent=0.6)
    h2(doc, "나. 진척 관리")
    para(doc, "테스트 진척 관리를 별도의 파일로 만들어 관련 담당자들이 함께 공유한다. 아래는 케이스 작성 기준의 진척관리 양식이다(수행 전이므로 수행 현황은 공란).", indent=0.6)
    tot = progress(doc, groups, "화면 / 대상" if UT else "시나리오")

    # 10. 고려사항
    h1(doc, "10. 테스트 고려사항")
    table(doc, ["진행 협조 사항", "잠재적 위험/이슈"], [[
        "현업 TFT 인원의 테스트 기간 내 지원\n분석 API 테스트 서버 사용 시간 및 점검 일정 합의\n테스트 데이터·초기 데이터 확인\n테스트 환경(브라우저·PC) 확보" + ("\n포털(edisn-ots) 개발 환경 접근 권한 확보" if not UT else ""),
        "분석 API 장애·응답 지연 시 테스트 수행이 중단될 수 있음\n반입 데이터가 1시간 후 삭제되므로 장시간 중단 시 재반입 필요\n" +
        ("테스트가 실제 분석 API 를 호출하므로 API 점검·장애 시간에는 수행할 수 없음\n화면에서만 강제하는 제한(카드 2개·합계 30MB·탐지 조건)은 서버가 막지 못함" if UT else "화면 단위 테스트는 자동화(tests/ui)되어 있으나 서버 클래스·통합 시나리오는 수동 수행이라 회귀 비용이 큼\n" + "포털 이식 시 스타일(CSS) 충돌과 인증·세션 연계 방식이 미확정이라 일정이 변동될 수 있음")]],
        [8.5, 8.5])

    # 11. 산출물
    h1(doc, "11. 산출물")
    table(doc, ["테스트 단계", "산출물", "필수/선택 구분", "관련 템플릿/양식"], [
        ["계획", f"{w} 테스트 계획서", "필수", f"{w} 테스트 계획서 템플릿(본 문서)"],
        ["설계", f"{w} 테스트 시나리오" if not UT else "단위 테스트 케이스", "필수", f"{w} 테스트 케이스 양식(부록 A 기반)"],
        ["수행", f"{w}테스트 케이스/로그", "필수", f"{w}테스트 케이스/로그 양식"],
        ["수행", "Defect Screen Dump(캡처)", "선택", "Defect Screen Dump 양식"],
        ["수행", "Defect Tracking(이슈 목록)", "필수", "Defect Tracking 양식"],
        ["수행", "Python 대조 코드·정답값", "선택", "docs/qa-report/scripts, data"],
        ["평가", f"{w} 테스트 결과 보고서", "필수", f"{w} 테스트 결과서 템플릿"],
    ], [3.0, 5.6, 3.0, 5.4], center_cols=(0, 2))
    page_break(doc)

    cases_appendix(doc, groups, f"부록 A. {w} 테스트 케이스 목록(초안)")
    page_break(doc)

    # 부록 B
    h1(doc, "부록 B. 사전 점검(QA) 결과 요약")
    para(doc, "2026-11-09~10에 테스트 서버에서 사전 점검을 수행하였다. 상세 내용과 근거는 docs/qa-report/QA_검증리포트.md에 있다.", indent=0.3)
    table(doc, ["항목", "결과"], [
        ["수행 방식", "분석 API 직접 호출 + Python 독립 계산 대조, 시스템 Chrome 자동 조작(STEP1~5 한 바퀴)"],
        ["수치 대조", "98개 값 비교, 불일치 0건 (선형회귀·상관·로지스틱·PCA·ANOVA·다층모형·K-평균·결합 행 수·대체·스케일링)"],
        ["식별 결함", "21건 등록 대상(서버 7 · 화면 10 · 서버+화면 4). 치명 1건(마할라노비스 거리가 D² 기준)"],
        ["화면 수정 완료", "화면에서 고칠 수 있는 항목을 모두 수정함: AIC/BIC 라벨, 종속변수 기본값, 내부 필드명, 용량 경고 위치, 상관 변수 후보, 명세 표기, 캐시 코드, 이상치 카드 집계, 빈 추천 차트 숨김, 다중 시트 XLSX 차단·안내, 결측 값 입력, 마할라노비스 임계값, ID·이진 열 제외, 군집·PCA 표준화 옵션, 서버 경고 표시, 필수 가드 복구"],
        ["미확인", "나머지 기법의 화면·PDF·Excel, 해석 문구, 재분석 규칙 재적용, 재현 기능"],
        ["자동 테스트 실행", "tests/ui 화면 단위 테스트: 75개 중 72개 통과, 3개 알려진 결함(xfail) — XLSX 혼합 열 반입(서버), 결측 행 제거 범위·이상치 행 제거 범위(서버)"],
    ], [3.4, 13.6], center_cols=(0,))
    para(doc, "※ 사전 점검은 본 계획서에 따른 공식 테스트 수행이 아니다. 공식 수행 시 결과는 부록 A의 결과란과 진척관리에 기재한다.", 9)
    os.makedirs(OUT, exist_ok=True)
    path = f"{OUT}/EDEMS-이용자통계분석-{w}테스트계획서-v0.1.docx"
    doc.save(path); return path, tot

if __name__ == "__main__":
    for k in ("UT", "IT"):
        p, n = build(k); print(p, "| 케이스", n)
