"""ot_dim_dmmbm03_m03 · 3단계 데이터 탐색  (UT-M03-01 ~ 05)

qa_clean_reference.csv(문제 없는 400행)를 반입해 2단계를 통과한 뒤, 3단계 화면의 표 값을 pandas 와 대조한다.
"""
import re
import time

import pandas as pd
import pytest

from conftest import BASE, HEADED, CHANNEL
from helpers import CLEAN, corr_matrix, prepare_to_m03, stat_rows

pytestmark = pytest.mark.m03
DF = pd.read_csv(CLEAN)
STAT_COLS = ["school_id", "grade", "score_t1", "score_t2", "score_t3", "score_t4", "study_hours", "income", "satisfaction"]


@pytest.fixture(scope="module")
def ready_page(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
    pg = ctx.new_page()
    pg.set_default_timeout(45000)
    prepare_to_m03(pg, CLEAN)
    yield pg
    ctx.close()


def _close(a, b, tol=0.011):
    return abs(a - b) <= max(tol, abs(b) * 1e-3)


def test_UT_M03_01_basic_stats_match_pandas(ready_page):
    """기초통계 표: N·평균·표준편차(ddof=1)·최소·Q1·중앙값·Q3·최대·왜도·첨도가 pandas 와 일치"""
    rows = stat_rows(ready_page)
    assert set(STAT_COLS) <= set(rows), rows.keys()
    bad = []
    for c in STAT_COLS:
        s, r = DF[c], rows[c]
        exp = {"n": s.count(), "mean": s.mean(), "std": s.std(ddof=1), "min": s.min(), "q1": s.quantile(.25),
               "median": s.median(), "q3": s.quantile(.75), "max": s.max(), "skew": s.skew(), "kurt": s.kurt()}
        bad += [(c, k, r[k], round(float(v), 3)) for k, v in exp.items() if not _close(r[k], float(v))]
    assert not bad, bad


def _select_method(pg, value):
    pg.locator("#corr-method").select_option(value)
    pg.wait_for_load_state("networkidle")
    time.sleep(2.5)


def _compare_corr(pg, method):
    m = corr_matrix(pg)
    assert m, "상관 행렬을 읽지 못함"
    exp = DF.select_dtypes("number").corr(method=method)     # kendall 은 tau-b
    bad = [(a, b, v, round(exp.loc[a, b], 3)) for (a, b), v in m.items()
           if a in exp.index and b in exp.columns and abs(v - exp.loc[a, b]) > 0.011]
    assert not bad, bad[:5]


def test_UT_M03_02_pearson_matrix(ready_page):
    """피어슨 상관 행렬이 pandas 와 일치"""
    _select_method(ready_page, "pearson")
    _compare_corr(ready_page, "pearson")


def test_UT_M03_03_spearman_matrix(ready_page):
    """스피어만 상관 행렬이 pandas 와 일치"""
    _select_method(ready_page, "spearman")
    _compare_corr(ready_page, "spearman")


def test_UT_M03_03_kendall_matrix_tau_b(ready_page):
    """켄달 상관 행렬이 tau-b 값과 일치하고 화면에 τ-b 가 표기된다"""
    _select_method(ready_page, "kendall")
    _compare_corr(ready_page, "kendall")
    assert "τ-b" in ready_page.locator("#corr-title").inner_text()


def test_UT_M03_04_top_pairs_sorted(ready_page):
    """상관 강도 상위 변수쌍: |r| 내림차순이고 첫 쌍이 전체 최대"""
    _select_method(ready_page, "pearson")
    txt = ready_page.locator("#pairs-wrap").inner_text()
    pairs = [(a, b, float(r)) for a, b, r in re.findall(r"(\S+)\s*↔\s*(\S+)\s+(-?\d\.\d+)", txt)]
    assert len(pairs) >= 5
    vals = [abs(r) for _, _, r in pairs]
    assert vals == sorted(vals, reverse=True)
    c = DF.select_dtypes("number").corr().abs()
    best = max(c.loc[i, j] for i in c.index for j in c.columns if i < j)
    assert abs(vals[0] - best) < 0.011


def test_UT_M03_05_preprocessing_is_reflected(page):
    """2단계에서 표준화를 적용하면 3단계 기초통계가 전처리된 값(평균 0, 표준편차 1)으로 표시된다"""
    prepare_to_m03(page, CLEAN, "표준화 (Standard)")
    r = stat_rows(page)["score_t1"]
    assert abs(r["mean"]) < 0.01 and abs(r["std"] - 1) < 0.01
