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


def test_UT_M05_08_table_headers_centered(ready_page):
    """결과 리포트의 모든 표 열 제목(thead th)이 가운데 정렬이다 (이슈 #3)"""
    pg = ready_page
    for tab in ("전체 종합", "표본별 원시데이터"):
        _tab(pg, tab)
        bad = pg.evaluate("""()=>[...document.querySelectorAll('#report-root table thead th')].filter(t=>t.getBoundingClientRect().width>0)
            .map(t=>[t.textContent.trim().slice(0,12), getComputedStyle(t).textAlign]).filter(x=>x[1]!=='center')""")
        assert not bad, (tab, bad[:5])


def test_UT_M05_09_scroll_table_header_has_no_gap(ready_page):
    """스크롤되는 원시 데이터 표: 스크롤해도 머리가 맨 위에 붙어 있고(틈 없음), 머리 폭 = 표 폭, 선은 border-collapse 가 아니다 (이슈 #3)"""
    pg = ready_page
    _tab(pg, "표본별 원시데이터")
    pg.evaluate("()=>{const w=document.querySelector('#rp-rawdata .scroll-tbl'); w.scrollTop = 150}")
    r = pg.evaluate("""()=>{const w=document.querySelector('#rp-rawdata .scroll-tbl'), th=w.querySelector('thead th'), t=w.querySelector('table');
        const wr=w.getBoundingClientRect(), hr=th.getBoundingClientRect(), cs=getComputedStyle(th);
        return {scrolled:w.scrollTop>0, gap:Math.round(hr.top-wr.top)-1, pos:cs.position, collapse:getComputedStyle(t).borderCollapse,
                same:Math.round(t.getBoundingClientRect().width)===Math.round([...w.querySelectorAll('thead th')].reduce((s,x)=>s+x.getBoundingClientRect().width,0))}}""")
    assert r["scrolled"] and r["gap"] == 0 and r["pos"] == "sticky" and r["collapse"] == "separate" and r["same"], r

def _gallery(pg):
    """진단 시각화 탭의 차트 목록 상태로 맞춘다 (앞선 테스트가 상세 화면을 열어 둔 채 끝났을 수 있다)"""
    _tab(pg, "진단 시각화")
    back = pg.locator("#rp-charts [data-cback]")
    if back.count():
        back.first.click()
        time.sleep(1.5)


def _img_ok(path, kind):
    data = open(path, "rb").read()
    sig = data[:8] == b"\x89PNG\r\n\x1a\n" if kind == "png" else data[:3] == b"\xff\xd8\xff"
    return sig and len(data) > 4000


def _open_menu(pg, scope="#rp-charts"):
    btn = pg.locator(f"{scope} [data-cexp-btn]").first
    btn.click()
    return btn, pg.locator(f"{scope} .cexp-menu:not([hidden])").first


def test_UT_M05_10_export_menu_card(ready_page):
    """차트 카드: 다운로드 아이콘 버튼 하나 → 메뉴(PNG 이미지 저장 / JPEG 이미지 저장 / 차트 인쇄). 기본 Highcharts 메뉴는 없다"""
    pg = ready_page
    _gallery(pg)
    assert pg.locator("#rp-charts .highcharts-contextbutton, #rp-charts .highcharts-exporting-group").count() == 0
    btn, menu = _open_menu(pg)
    assert btn.get_attribute("aria-haspopup") == "menu" and btn.get_attribute("aria-expanded") == "true"
    assert btn.get_attribute("aria-label") and menu.get_attribute("role") == "menu"
    assert [t.strip() for t in menu.locator("[role=menuitem]").all_inner_texts()] == ["PNG 이미지 저장", "JPEG 이미지 저장", "차트 인쇄"]
    assert pg.locator("#rp-charts [data-cback]").count() == 0          # 메뉴를 열어도 상세 화면으로 넘어가지 않는다
    with pg.expect_download() as dl:
        menu.locator("[data-cfmt=png]").click()
    assert dl.value.suggested_filename.endswith(".png") and dl.value.suggested_filename.startswith("Figure_1")
    assert _img_ok(dl.value.path(), "png")
    assert btn.get_attribute("aria-expanded") == "false" and pg.evaluate("()=>document.activeElement.hasAttribute('data-cexp-btn')")   # 닫히고 초점이 버튼으로 복귀


def test_UT_M05_10_export_jpeg_and_print(ready_page):
    """JPEG 이미지 저장, 차트 인쇄(브라우저 인쇄 창 호출)"""
    pg = ready_page
    _gallery(pg)
    _, menu = _open_menu(pg)
    with pg.expect_download() as dl:
        menu.locator("[data-cfmt=jpeg]").click()
    assert dl.value.suggested_filename.endswith(".jpg") and _img_ok(dl.value.path(), "jpeg")
    pg.evaluate("()=>{window.__printed=0; window.print=()=>{window.__printed++}}")   # 실제 인쇄 창은 띄우지 않는다
    _, menu = _open_menu(pg)
    menu.locator("[data-cfmt=print]").click()
    time.sleep(1)
    assert pg.evaluate("()=>window.__printed") >= 1


def test_UT_M05_10_export_menu_keyboard(ready_page):
    """접근성: 키보드로 열고(ArrowDown) 이동(↑↓·Home·End)하고 닫는다(Esc). 닫으면 초점이 버튼으로 돌아온다"""
    pg = ready_page
    _gallery(pg)
    btn = pg.locator("#rp-charts [data-cexp-btn]").first
    btn.focus()
    pg.keyboard.press("ArrowDown")
    assert btn.get_attribute("aria-expanded") == "true"
    names = lambda: pg.evaluate("()=>document.activeElement.textContent.trim()")
    assert names() == "PNG 이미지 저장"
    pg.keyboard.press("ArrowDown"); assert names() == "JPEG 이미지 저장"
    pg.keyboard.press("End"); assert names() == "차트 인쇄"
    pg.keyboard.press("ArrowDown"); assert names() == "PNG 이미지 저장"          # 끝에서 처음으로 순환
    pg.keyboard.press("Home"); assert names() == "PNG 이미지 저장"
    pg.keyboard.press("Escape")
    assert btn.get_attribute("aria-expanded") == "false"
    assert pg.evaluate("()=>document.activeElement.hasAttribute('data-cexp-btn')")
    btn.click(); pg.mouse.click(5, 5)                                           # 바깥 클릭으로도 닫힌다
    assert btn.get_attribute("aria-expanded") == "false"


def test_UT_M05_11_export_menu_detail(ready_page):
    """차트 자세히 보기에도 같은 내보내기 메뉴가 있고 PNG 를 내려받을 수 있다"""
    pg = ready_page
    _gallery(pg)
    pg.locator("#rp-charts [data-cidx]").first.click()
    time.sleep(2)
    btn, menu = _open_menu(pg)
    assert menu.locator("[role=menuitem]").count() == 3
    with pg.expect_download() as dl:
        menu.locator("[data-cfmt=png]").click()
    assert _img_ok(dl.value.path(), "png")
    pg.locator("#rp-charts [data-cback]").click()                       # 이후 07번 테스트가 목록 상태를 기대하지 않도록 정리


def test_UT_M05_07_save_result(ready_page):
    """[결과 저장] → 5단계 목록에 저장한 분석이 나타난다"""
    pg = ready_page
    pg.locator("#btn-save").click()
    time.sleep(4)
    pg.goto(url("m06"), wait_until="networkidle")
    time.sleep(2)
    assert "다층모형" in pg.locator("#pk-list").inner_text()
