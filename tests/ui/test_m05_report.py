"""ot_dim_dmmbm03_m05 · 4-2 분석 결과 리포트  (UT-M05-01 ~ 07)

다층모형(HLM, 고정효과 변수 없음 = 무조건모형)을 실행한 결과 화면을 statsmodels MixedLM 계산값과 대조한다.
"""
import time
import warnings

import pandas as pd
import pytest
import statsmodels.formula.api as smf

from helpers import CLEAN, open_m04, open_report, prepare_to_m03, run_hlm, url

pytestmark = pytest.mark.m05
warnings.filterwarnings("ignore")
DF = pd.read_csv(CLEAN)


def _expected():
    reml = smf.mixedlm("score_t4 ~ 1", DF, groups=DF["school_id"]).fit(reml=True)
    ml = smf.mixedlm("score_t4 ~ 1", DF, groups=DF["school_id"]).fit(reml=False)
    tau, s2 = float(reml.cov_re.iloc[0, 0]), float(reml.scale)
    return {"icc": tau / (tau + s2), "tau": tau, "sigma2": s2, "intercept": float(reml.params["Intercept"]),
            "llf_reml": float(reml.llf), "aic_ml": float(-2 * ml.llf + 2 * 3)}


EXP = _expected()


@pytest.fixture(scope="module")
def ready_page(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
    pg = ctx.new_page()
    pg.set_default_timeout(45000)
    prepare_to_m03(pg, CLEAN)
    open_m04(pg)
    run_hlm(pg)
    open_report(pg)
    pg.wait_for_function("()=>!document.querySelector('#rp-title').textContent.includes('불러오는')", timeout=60000)
    yield pg
    ctx.close()


def _body(pg):
    return pg.locator("#rp-body").inner_text().replace("−", "-")


def _tab(pg, text):
    pg.locator("#rp-tabs button", has_text=text).first.click()
    time.sleep(2.5)


def test_UT_M05_01_summary_cards(ready_page):
    """결과 요약 카드: 제목에 기법명, 핵심 지표(ICC·집단 수·관측치·로그우도)가 표시되고 ICC 가 계산값과 일치"""
    pg = ready_page
    assert "다층모형" in pg.locator("#rp-title").inner_text()
    body = _body(pg)
    assert f"{EXP['icc']:.3f}" in body
    for word in ("집단 수", "관측치", "로그 우도"):
        assert word in body


def test_UT_M05_02_table_values_match_statsmodels(ready_page):
    """표준 통계 결과표: 고정효과·분산성분·ICC·로그우도·AIC 가 statsmodels 값과 일치"""
    body = _body(ready_page)
    for label, v in [("절편", EXP["intercept"]), ("τ00", EXP["tau"]), ("σ²", EXP["sigma2"]), ("로그우도", EXP["llf_reml"]), ("AIC(ML)", EXP["aic_ml"])]:
        decimals = 4 if label in ("τ00", "σ²") else 3
        assert f"{v:.{decimals}f}" in body, (label, v)


def test_UT_M05_02_aic_basis_label(ready_page):
    """AIC/BIC 옆 표기는 '(REML)'이 아니라 실제 산출 기준(ML 기준)이다"""
    body = _body(ready_page)
    assert "(ML 기준)" in body
    assert f"{EXP['aic_ml']:.3f} (REML)" not in body


def test_UT_M05_03_recommended_charts(ready_page):
    """추천 차트: 차트가 그려지고, 데이터가 없는 차트가 표시되지 않는다"""
    pg = ready_page
    _tab(pg, "진단 시각화")
    assert pg.locator("#rp-charts .highcharts-container").count() >= 2
    assert "표시할 데이터가 없습니다" not in pg.locator("#rp-charts").inner_text()


def test_UT_M05_04_chart_detail_view(ready_page):
    """차트를 누르면 상세 보기로 전환된다"""
    pg = ready_page
    _tab(pg, "진단 시각화")
    pg.locator("#rp-charts [data-cidx]").first.click()
    time.sleep(2)
    assert pg.locator("#rp-charts [data-cnav], #rp-charts [data-cdata]").count() >= 1


def test_UT_M05_05_raw_data_and_residual_tab(ready_page):
    """표본별 원시데이터 탭: 관측치 수(400)와 표가 표시된다"""
    pg = ready_page
    _tab(pg, "표본별 원시데이터")
    assert "400" in pg.locator("#rp-rawdata").inner_text() or "400" in pg.locator("#rp-tabs").inner_text()
    assert pg.locator("#rp-rawdata table tbody tr").count() >= 1


def test_UT_M05_06_no_internal_field_names(ready_page):
    """내부 필드명(const_se, group_variance 등)이 표·차트에 노출되지 않는다"""
    pg = ready_page
    _tab(pg, "전체 종합")
    text = pg.evaluate("()=>document.querySelector('#rp-body').textContent") + pg.evaluate("()=>document.querySelector('#rp-charts')?.textContent||''")
    for token in ("const_se", "const_ci_lower", "const_ci_upper", "group_variance", "residual_variance"):
        assert token not in text, token


def test_UT_M05_07_save_result(ready_page):
    """[결과 저장] → 5단계 목록에 저장한 분석이 나타난다"""
    pg = ready_page
    pg.locator("#btn-save").click()
    time.sleep(4)
    pg.goto(url("m06"), wait_until="networkidle")
    time.sleep(2)
    assert "다층모형" in pg.locator("#pk-list").inner_text()
