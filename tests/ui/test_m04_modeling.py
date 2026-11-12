"""ot_dim_dmmbm03_m04 · 4-1 통계 모형 설정·실행  (UT-M04-01 ~ 08)"""
import time

import pytest

from helpers import CLEAN, open_m04, pick_method, prepare_to_m03, run_and_wait, run_hlm

pytestmark = pytest.mark.m04

METHODS = ["correlation", "linear_regression", "logistic_regression", "decision_tree_regressor", "decision_tree_classifier",
           "kmeans", "hierarchical", "dbscan", "pca", "anova", "multilevel", "growth_curve", "psm"]


@pytest.fixture(scope="module")
def ready_page(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
    pg = ctx.new_page()
    pg.set_default_timeout(45000)
    pg.js_errors = []
    pg.on("pageerror", lambda e: pg.js_errors.append(str(e)))
    prepare_to_m03(pg, CLEAN)
    yield pg
    ctx.close()


def _fit_ok(pg):
    return pg.locator("#fit-badge").is_visible()


def test_UT_M04_01_all_13_methods_switch(ready_page):
    """기법 13종 전환: 카드가 13개이고, 선택할 때마다 변수·파라미터 영역이 전환되며 스크립트 오류가 없다"""
    pg = ready_page
    open_m04(pg)
    cards = pg.locator("#method-grid [data-method]")
    assert cards.count() == 13
    assert sorted(cards.evaluate_all("els=>els.map(e=>e.getAttribute('data-method'))")) == sorted(METHODS)
    for m in METHODS:
        pick_method(pg, m)
        assert pg.locator(f"#method-grid [data-method={m}]").get_attribute("aria-pressed") == "true"
        assert pg.locator("#target-box").inner_text().strip()
    assert pg.js_errors == []


def test_UT_M04_02_required_marks_and_messages(ready_page):
    """필수 항목 표시: 빨간 *, 비어 있으면 '필수 선택 항목입니다.' 와 빨간 테두리, 선택하면 즉시 해제"""
    pg = ready_page
    open_m04(pg)
    pick_method(pg, "multilevel")
    pg.locator("#sel-target").select_option("")
    pg.locator("#par-group_column").select_option("")
    time.sleep(0.4)
    assert pg.locator(".req-star:visible").count() >= 2
    errs = pg.locator(".req-field.is-error .req-msg:visible")
    assert errs.count() >= 2
    assert all("필수 선택 항목입니다." in t for t in errs.all_inner_texts())
    pg.locator("#sel-target").select_option("score_t4")
    pg.locator("#par-group_column").select_option("school_id")
    time.sleep(0.4)
    assert pg.locator(".req-field.is-error").count() == 0


def test_UT_M04_03_hlm_runs_without_fixed_effects(ready_page):
    """HLM: 고정효과 변수를 비워도(선택 사항) 집단·종속변수만으로 실행된다"""
    pg = ready_page
    open_m04(pg)
    run_hlm(pg)
    assert _fit_ok(pg)
    assert pg.locator("#result-panel.hidden").count() == 1      # 실패 안내 패널이 열리지 않음


def test_UT_M04_04_role_conflict_blocked(ready_page):
    """종속변수로 고른 열은 독립변수 목록에서 선택할 수 없고 '종속변수로 사용 중'이 표시된다"""
    pg = ready_page
    open_m04(pg)
    pick_method(pg, "linear_regression")
    pg.locator("#sel-target").select_option("score_t4")
    time.sleep(0.5)
    row = pg.locator("#feat-list label", has_text="score_t4")
    assert row.locator("input").is_disabled()
    assert "종속변수로 사용 중" in row.inner_text()


def test_UT_M04_05_linear_regression_runs_and_opens_report(ready_page):
    """선형회귀 실행 성공 → [4-2 분석 결과 보기]로 리포트 화면 이동"""
    pg = ready_page
    open_m04(pg)
    pick_method(pg, "linear_regression")
    pg.locator("#sel-target").select_option("score_t4")
    time.sleep(0.4)
    run_and_wait(pg)
    assert _fit_ok(pg)
    pg.locator("#btn-report").click()
    pg.wait_for_url("**/report")
    pg.wait_for_function("()=>!document.querySelector('#rp-title').textContent.includes('불러오는')", timeout=60000)
    assert "선형" in pg.locator("#rp-title").inner_text()


def test_UT_M04_06_missing_required_blocks_run(ready_page):
    """필수 항목이 비어 있으면 실행되지 않고 누락 항목이 표시된다"""
    pg = ready_page
    open_m04(pg)
    pick_method(pg, "multilevel")
    pg.locator("#sel-target").select_option("")
    pg.locator("#par-group_column").select_option("")
    before = pg.evaluate("()=>(JSON.parse(sessionStorage.getItem('edu.state')||'{}')).analysisId||null")
    pg.locator("#btn-run").click()
    time.sleep(2)
    assert pg.locator(".req-field.is-error .req-msg:visible").count() >= 1
    after = pg.evaluate("()=>(JSON.parse(sessionStorage.getItem('edu.state')||'{}')).analysisId||null")
    assert after == before                                      # 새 분석이 시작되지 않음


def test_UT_M04_07_correlation_candidates_numeric_only(ready_page):
    """상관분석 변수 후보: 수치형·이진 열만 (범주형·텍스트·날짜·상수 열은 제외)"""
    pg = ready_page
    open_m04(pg)
    pick_method(pg, "correlation")
    names = [t.strip().split("\n")[0] for t in pg.locator("#feat-list label").all_inner_texts()]
    assert "score_t1" in names
    assert not set(names) & {"region", "gender", "student_id", "survey_date", "const_col"}, names


def test_UT_M04_08_target_not_auto_selected(page):
    """종속변수는 자동 선택되지 않는다 (ID 성격의 첫 수치형 열이 기본값이 되지 않음)"""
    prepare_to_m03(page, CLEAN)
    open_m04(page)
    pick_method(page, "linear_regression")
    assert page.locator("#sel-target").input_value() == ""
    assert page.locator("#target-box .req-msg").is_visible()


def _post_analysis_body(pg, action):
    """action() 을 실행하는 동안 화면이 보내는 POST /api/v1/analyses 본문을 돌려준다 (서버 버전과 무관하게 화면 동작만 확인)"""
    import json
    bodies = []
    fn = lambda r: bodies.append(r.post_data) if r.method == "POST" and r.url.rstrip("/").endswith("/api/v1/analyses") else None
    pg.on("request", fn)
    try:
        action()
    finally:
        pg.remove_listener("request", fn)
    assert bodies, "분석 요청이 나가지 않음"
    return json.loads(bodies[-1])


def test_UT_M04_09_cluster_pca_guide_to_step2_scaling(ready_page):
    """군집·PCA: 4단계에는 표준화 선택이 없고, 2단계에서 스케일링하지 않았으면 2단계로 유도하는 안내가 나온다. 요청에는 scaling 을 보내지 않는다"""
    pg = ready_page
    open_m04(pg)
    for method in ("kmeans", "pca"):
        pick_method(pg, method)
        assert pg.locator("[data-par=standardize]").count() == 0                  # 4단계 표준화 선택 없음
        warn = pg.locator("#pre-warn .krds-warning")
        assert warn.is_visible() and "스케일링" in warn.inner_text()
        assert warn.locator("a.jn-link").get_attribute("href").endswith("/analysis/step2")
    pick_method(pg, "linear_regression")
    assert pg.locator("#pre-warn .krds-msg").filter(has_text="스케일링").count() == 0   # 다른 기법에는 안내 없음
    pick_method(pg, "kmeans")
    body = _post_analysis_body(pg, lambda: run_and_wait(pg))
    assert "scaling" not in body["preprocessing"]            # 스케일링은 2단계에서만 정한다
    assert "standardize" not in body["params"]


def test_UT_M04_10_guide_when_step2_scaling_applied(page):
    """2단계에서 표준화를 적용했으면 경고 대신 '2단계에서 표준화를 적용한 데이터' 안내가 나온다"""
    prepare_to_m03(page, CLEAN, "표준화 (Standard)")
    open_m04(page)
    pick_method(page, "kmeans")
    info = page.locator("#pre-warn .krds-info")
    assert info.is_visible() and "표준화(Standard)" in info.inner_text()
    assert page.locator("#pre-warn .krds-warning").count() == 0

