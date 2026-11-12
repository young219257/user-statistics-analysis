"""ot_dim_dmmbm03_m02 · 2단계 품질 및 전처리  (UT-M02-01 ~ 10)

기대값은 qa_main_utf8.csv 를 pandas 로 직접 계산한다. 서버(분석 API)의 알려진 결함으로 아직 실패하는 케이스는
xfail 로 표시하고 사유(결함 번호)를 적는다. 결함이 고쳐지면 XPASS 로 알려 주므로 xfail 표시를 제거한다.
"""
import re
import time

import numpy as np
import pandas as pd
import pytest

from helpers import (MAIN, choose_rules, detect, num, pick_algo, prepare_to_m03, stat_rows,
                     start_with, to_m02, to_m03, var_rows)

pytestmark = pytest.mark.m02
RAW = pd.read_csv(MAIN)
SH = RAW["study_hours"]


def _m02(page):
    start_with(page, MAIN)
    to_m02(page)


def _outliers_of(page, var):
    cell = var_rows(page)[var][2]                    # 예: '10 (하 0 / 상 10)'
    return int(re.match(r"[\d,]+", cell).group().replace(",", ""))


def test_UT_M02_01_quality_cards(page):
    """기본 품질 카드: 행×열, 결측, 중복이 pandas 와 일치, 이상치는 '탐지 전'"""
    _m02(page)
    assert page.locator("#card-rows").inner_text().strip() == f"{len(RAW)}행 × {RAW.shape[1]}변수"
    blank = RAW.apply(lambda c: c.notna() & c.astype(str).str.strip().eq(""))   # 공백만 있는 값도 결측으로 센다
    missing = int((RAW.isna() | blank).sum().sum())              # 위장 결측("-", 999 등)은 값으로 취급
    assert f"{missing}건" in page.locator("#card-missing").inner_text()
    assert page.locator("#card-dups").inner_text().strip() == f"{int(RAW.duplicated().sum())}행"
    assert page.locator("#card-outliers").inner_text().strip() == "탐지 전"


def _iqr_count(k):
    q1, q3 = SH.quantile(.25), SH.quantile(.75)
    i = q3 - q1
    return int(((SH < q1 - k * i) | (SH > q3 + k * i)).sum())


def _z_count(t):
    return int((((SH - SH.mean()) / SH.std(ddof=1)).abs() > t).sum())


def _modz_count(t):
    d = SH - SH.median()
    return int(((0.6745 * d / d.abs().median()).abs() > t).sum())


@pytest.mark.parametrize("idx,name,expected", [
    (0, "IQR", _iqr_count(1.5)),
    (1, "Z-score", _z_count(3.0)),
    (2, "수정 Z-score", _modz_count(3.5)),
    (3, "Grubbs", 10),                      # 반복 Grubbs 검정(α=0.05) 독립 계산값
])
def test_UT_M02_02_detect_study_hours(page, idx, name, expected):
    """이상치 탐지 4종: study_hours 이상치 개수가 Python 재계산과 일치"""
    _m02(page)
    detect(page, idx)
    assert _outliers_of(page, "study_hours") == expected


@pytest.mark.parametrize("idx", [4, 5, 6])
def test_UT_M02_02_detect_multivariate_runs(page, idx):
    """마할라노비스·Isolation Forest·LOF: 실행되어 결과(변수별 진단)가 표시된다 (값은 무작위/다변량이라 존재만 확인)"""
    _m02(page)
    detect(page, idx)
    assert page.locator("#card-outliers").inner_text().strip() != "탐지 전"
    assert "study_hours" in var_rows(page)


def _card_total(page):
    return int(re.match(r"[\d,]+", page.locator("#card-outliers").inner_text().strip()).group().replace(",", ""))


def _targets(page):
    """진단 표의 수치형 대상 변수(식별자·이진·범주형 제외) — 서버로 보내는 columns 와 같다"""
    return page.evaluate("()=>[...document.querySelectorAll('#var-body tr')].filter(tr=>!tr.firstElementChild.textContent.includes('범주형')).map(tr=>tr.dataset.col)")


def test_UT_M02_03_mahalanobis_chi_square_option(page):
    """마할라노비스: 선택지가 변수 수(자유도)에 맞는 χ² 분위수이고, 'χ² 99%'를 고르면 D² 가 그 값을 넘는 행 수와 일치한다"""
    from scipy.stats import chi2
    _m02(page)
    cols = _targets(page)
    df = len(cols)
    pick_algo(page, 4)
    sel = page.locator("#algo-grid > *").nth(4).locator("select")
    labels = sel.locator("option").all_inner_texts()
    assert any(f"{chi2.ppf(0.975, df):.2f}" in t for t in labels), labels          # 97.5% = 서버 기본
    assert len(labels) == 3 and not any("95%" in o for o in labels), labels         # 97.5% · 99% · 99.9% (이슈 #4)
    target = [o for o in labels if "χ² 99% " in o][0]
    sel.select_option(label=target)
    page.locator("#btn-detect").click()
    page.wait_for_function("()=>document.querySelector('#card-outliers').textContent.trim()!=='탐지 전'", timeout=120000)
    page.wait_for_function("()=>!document.querySelector('#btn-detect').disabled")
    x = RAW[cols].dropna().values
    d = x - x.mean(0)
    d2 = np.einsum("ij,jk,ik->i", d, np.linalg.pinv(np.cov(x, rowvar=False)), d)
    n = int((d2 > chi2.ppf(0.99, df)).sum())
    note = page.locator("#judge-note").inner_text()                     # 마할라노비스는 변수별이 아니라 변수 조합(행) 기준으로 한 번만 표시
    assert abs(int(re.search(r"이상치는 ([\d,]+)행", note).group(1).replace(",", "")) - n) <= 1, (note, n)
    assert abs(_card_total(page) - n) <= 1                              # 카드는 변수별 합이 아니라 이상치 '행 수'


def test_UT_M02_03_mahalanobis_default_is_chi_square(page):
    """마할라노비스 기본 임계 = χ² 97.5% 분위수: 서버가 그 의미로 해석하는 값(≤1.5)을 보낸다"""
    urls = []
    page.on("request", lambda r: urls.append(r.url) if "/outliers" in r.url else None)
    _m02(page)
    detect(page, 4)
    assert any("method=mahalanobis" in u and re.search(r"threshold=1(\.0)?(&|$)", u) for u in urls), urls
    u = [u for u in urls if "method=mahalanobis" in u][0]
    assert "columns=" in u and "school_id" not in u, u                   # 식별자·이진 열을 뺀 대상 변수만 보낸다(자유도 = 대상 변수 수)
    assert "χ²" in page.locator("#applied-formula").inner_text()


def test_UT_M02_04_threshold_change(page):
    """IQR 배수를 1.5 → 3.0 으로 바꿔 재탐지 → 전체 이상치 건수가 줄고 study_hours 값은 pandas 와 일치"""
    _m02(page)
    detect(page, 0)
    base_total = _card_total(page)
    assert _outliers_of(page, "study_hours") == _iqr_count(1.5)
    sel = page.locator("#algo-grid > *").nth(0).locator("select")
    opts = sel.locator("option").all_inner_texts()
    sel.select_option(label=[o for o in opts if "3.0" in o][0])
    page.locator("#btn-detect").click()
    time.sleep(3)
    page.wait_for_function("()=>!document.querySelector('#btn-detect').disabled")
    assert _card_total(page) < base_total
    assert _outliers_of(page, "study_hours") == _iqr_count(3.0)


def test_UT_M02_05_default_rules_first_and_selected(page):
    """전처리 규칙: 각 그룹의 기본값이 맨 위에 있고 선택된 상태"""
    _m02(page)
    groups = page.locator("#strategy-grid > *")
    expected_first = ["처리 안 함 (None)", "원본값 보존 (Keep)", "미적용 (None)", "유지 (Keep)"]
    assert groups.count() == 4
    for i, first in enumerate(expected_first):
        g = groups.nth(i)
        labels = [t.strip().split("\n")[0] for t in g.locator("label").all_inner_texts()]
        assert labels[0] == first
        assert g.locator("input:checked").count() == 1
        assert g.locator("label:has(input:checked)").first.inner_text().strip().split("\n")[0] == first


def _after_rules(page, *rules):
    prepare_to_m03(page, MAIN, *rules)
    return stat_rows(page)["study_hours"]


@pytest.mark.parametrize("rule,expected_mean", [
    ("중앙값으로 대체", SH.fillna(SH.median()).mean()),
    ("평균값으로 대체", SH.fillna(SH.mean()).mean()),
    ("최빈값으로 대체", SH.fillna(SH.mode().iloc[0]).mean()),
    ("0 대체 (Zero)", SH.fillna(0).mean()),
])
def test_UT_M02_06_missing_strategy(page, rule, expected_mean):
    """결측 처리 → 3단계에서 study_hours 평균이 pandas 대체 결과와 일치, 결측 없음"""
    row = _after_rules(page, rule)
    assert row["n"] == len(RAW)
    assert abs(row["mean"] - expected_mean) < 0.01


@pytest.mark.xfail(reason="결함 D-09: 결측 행 제거가 수치 열의 결측만 대상으로 함(텍스트·범주 열 결측 행이 남음)", strict=False)
def test_UT_M02_06_missing_drop_rows(page):
    """결측 행 제거 → 결측이 있는 모든 행이 제거된다"""
    prepare_to_m03(page, MAIN, "결측치 행 제거 (Drop)")
    assert page.locator("#stat-rows").inner_text().strip().startswith(f"{len(RAW.dropna())}")


def test_UT_M02_07_outlier_winsorize(page):
    """윈저라이징(IQR 1.5) → study_hours 최대값이 상한 경계로 제한된다"""
    q1, q3 = SH.quantile(.25), SH.quantile(.75)
    upper = q3 + 1.5 * (q3 - q1)
    row = _after_rules(page, "윈저라이징 (클리핑)")
    assert abs(row["max"] - upper) < 0.01


def test_UT_M02_07_outlier_log(page):
    """로그 변환 → 자연로그 적용 (평균이 ln(x) 평균과 일치)"""
    row = _after_rules(page, "로그 변환 (Log)")
    assert abs(row["mean"] - np.log(SH).mean()) < 0.01


@pytest.mark.xfail(reason="결함 D-10: 이상치 행 제거가 study_hours 외 수치 열(satisfaction 등)의 이상치 행까지 제거함", strict=False)
def test_UT_M02_07_outlier_drop(page):
    """이상치 행 제거(IQR) → study_hours 이상치 행 수만큼만 제거"""
    prepare_to_m03(page, MAIN, "이상치 행 제거 (Drop)")
    assert page.locator("#stat-rows").inner_text().strip().startswith(f"{len(RAW) - _iqr_count(1.5)}")


def test_UT_M02_08_scaling_standard(page):
    """표준화 → 평균 0, 표준편차 1 (ddof 표기는 전략 설명에 있음)"""
    row = _after_rules(page, "표준화 (Standard)")
    assert abs(row["mean"]) < 0.01 and abs(row["std"] - 1) < 0.01


def test_UT_M02_08_scaling_minmax(page):
    """정규화 → 최소 0, 최대 1"""
    row = _after_rules(page, "정규화 (MinMax)")
    assert abs(row["min"]) < 0.01 and abs(row["max"] - 1) < 0.01


def test_UT_M02_08_scaling_robust(page):
    """로버스트 → 중앙값 0"""
    row = _after_rules(page, "로버스트 (Robust)")
    assert abs(row["median"]) < 0.01


def test_UT_M02_08_standard_description_has_ddof(page):
    """표준화 설명에 표준편차 정의(ddof=0)가 표기된다"""
    _m02(page)
    assert "ddof=0" in page.locator("#strategy-grid").inner_text()


def test_UT_M02_09_next_requires_detection(page):
    """3단계 진행 버튼: 탐지 전에는 비활성, 탐지 응답 후 활성"""
    _m02(page)
    assert page.locator("#btn-next").is_disabled()
    detect(page, 0)
    assert page.locator("#btn-next").is_enabled()


def test_UT_M02_10_id_and_binary_columns_excluded(page):
    """이상치 진단 표에서 ID·이진 열이 제외된다"""
    _m02(page)
    detect(page, 0)
    names = set(var_rows(page))
    assert not (names & {"school_id", "treatment", "passed"}), names


def test_UT_M02_11_preprocess_request_excludes_id_and_binary(page):
    """전처리 요청의 적용 대상 열(columns)에서 식별자·이진 열을 뺀다"""
    import json
    bodies = []
    page.on("request", lambda r: bodies.append(r.post_data) if r.method == "POST" and "/preprocess" in r.url else None)
    prepare_to_m03(page, MAIN, "중앙값으로 대체")      # 규칙을 하나 골라야 전처리 요청이 나간다
    assert bodies, "전처리 요청이 나가지 않음"
    cols = json.loads(bodies[-1]).get("columns") or []
    assert "study_hours" in cols and "score_t1" in cols
    assert not set(cols) & {"school_id", "treatment", "passed", "student_id"}, cols


def test_UT_M02_12_algo_card_copy_matches_api(page):
    """카드 문구가 API 동작과 맞다: IF·LOF 는 변수별(단변량), Grubbs 는 순차 검정, IF 0.60 에 '표준 권장' 표기 없음, 라벨 |M| (이슈 #4)"""
    _m02(page)
    grid = page.locator("#algo-grid").inner_text()
    assert grid.count("변수별로 따로 탐지") == 2
    assert "순차 Grubbs 검정" in grid and "|M|" in grid and "|M_i|" not in grid
    assert "표준 권장 임계치" not in grid and "0.60" in grid
    assert grid.count("다변량") == 2          # 마할라노비스 배지('다변량 공분산')와 설명 한 곳뿐


@pytest.mark.parametrize("idx", [5, 6])
def test_UT_M02_12_no_boundary_for_if_and_lof(page, idx):
    """Isolation Forest·LOF 는 하한·상한 경계가 없으므로 '경계 없음'으로 표시한다 (이슈 #4)"""
    _m02(page)
    detect(page, idx)
    assert "경계 없음" in page.locator("#detail-card .sec-head").inner_text()


def test_UT_M02_12_mahalanobis_is_combination_result(page):
    """마할라노비스는 변수별 칸을 비우고 '변수 조합 기준 결과'(행 수·D² 임계)를 한 번만 보여 준다 (이슈 #4)"""
    _m02(page)
    detect(page, 4)
    cells = var_rows(page)["study_hours"]
    assert cells[2] == "-" and cells[3] == "-"                     # 변수별 이상치·비율 칸 비움
    assert "변수 조합 기준 결과" in page.locator("#detail-card .sec-head").inner_text()
    note = page.locator("#judge-note").inner_text()
    assert "행 전체를 한 번에 판정" in note and "D² " in note


def test_UT_M02_13_mahalanobis_allows_only_drop_treatment(page):
    """마할라노비스는 서버가 이상치 행 제거(Drop)만 허용 → 윈저라이징·로그 변환은 비활성이고, 미리 골랐다면 '원본값 보존'으로 되돌린다"""
    _m02(page)
    choose_rules(page, "윈저라이징 (클리핑)")                           # 먼저 윈저라이징을 고른 뒤
    detect(page, 4)                                                    # 마할라노비스를 실행
    assert page.locator('input[name="outlier_treatment"][value="winsorize"]').is_disabled()
    assert page.locator('input[name="outlier_treatment"][value="log"]').is_disabled()
    assert page.locator('input[name="outlier_treatment"][value="drop"]').is_enabled()
    assert page.locator('input[name="outlier_treatment"][value="keep"]').is_checked()


def test_UT_M02_13_winsorize_still_allowed_for_other_methods(page):
    """마할라노비스가 아닌 기법에서는 윈저라이징·로그 변환을 그대로 고를 수 있다"""
    _m02(page)
    detect(page, 0)
    assert page.locator('input[name="outlier_treatment"][value="winsorize"]').is_enabled()
    assert page.locator('input[name="outlier_treatment"][value="log"]').is_enabled()


def test_UT_M02_13_discrete_column_note_for_if_and_lof(page):
    """Isolation Forest·LOF: 고유값이 적은 이산형 열(예: 5점 척도)은 판정이 불안정하다는 안내를 보인다"""
    _m02(page)
    detect(page, 5)
    note = page.locator("#judge-note").inner_text()
    assert "이산형" in note and "Isolation Forest" in note
