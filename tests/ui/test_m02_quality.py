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


def test_UT_M02_03_mahalanobis_squared_distance_option(page):
    """마할라노비스: 선택지 'D² > 9 (거리 D > 3.0)' → 거리 D 가 3 을 넘는 행 수와 일치 (서버는 제곱거리 D² 를 임계값과 비교)"""
    _m02(page)
    pick_algo(page, 4)
    sel = page.locator("#algo-grid > *").nth(4).locator("select")
    sel.select_option(label=[o for o in sel.locator("option").all_inner_texts() if "D² > 9" in o][0])
    page.locator("#btn-detect").click()
    page.wait_for_function("()=>document.querySelector('#card-outliers').textContent.trim()!=='탐지 전'", timeout=120000)
    page.wait_for_function("()=>!document.querySelector('#btn-detect').disabled")
    cols = ["school_id", "treatment", "grade", "score_t1", "score_t2", "score_t3", "score_t4", "study_hours", "satisfaction", "passed"]
    x = RAW[cols].dropna().values
    d = x - x.mean(0)
    dist = np.sqrt(np.einsum("ij,jk,ik->i", d, np.linalg.pinv(np.cov(x, rowvar=False)), d))
    assert _outliers_of(page, "study_hours") == int((dist > 3.0).sum())
    assert _card_total(page) == int((dist > 3.0).sum())        # 카드는 변수별 합(×10)이 아니라 이상치 '행 수'


def test_UT_M02_03_mahalanobis_default_is_chi_square(page):
    """마할라노비스 기본 임계 = χ² 97.5% 분위수: 서버가 그 의미로 해석하는 값(≤1.5)을 보낸다"""
    urls = []
    page.on("request", lambda r: urls.append(r.url) if "/outliers" in r.url else None)
    _m02(page)
    detect(page, 4)
    assert any("method=mahalanobis" in u and re.search(r"threshold=1(\.0)?(&|$)", u) for u in urls), urls
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

