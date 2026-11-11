"""ot_dim_dmmbm03_m06 · 5단계 결과 관리  (UT-M06-01 ~ 05)

다층모형 분석 1건을 저장한 패키지를 만들어 목록·내보내기(PDF/Excel)·공유·삭제를 확인하고,
내보낸 파일의 값이 statsmodels 계산값(= 4-2 화면 값)과 같은지 대조한다.
"""
import io
import time
import warnings

import openpyxl
import pandas as pd
import pytest
import statsmodels.formula.api as smf
from pypdf import PdfReader

from helpers import CLEAN, open_m04, open_report, prepare_to_m03, run_hlm, url

pytestmark = pytest.mark.m06
warnings.filterwarnings("ignore")
DF = pd.read_csv(CLEAN)


def _expected():
    reml = smf.mixedlm("score_t4 ~ 1", DF, groups=DF["school_id"]).fit(reml=True)
    ml = smf.mixedlm("score_t4 ~ 1", DF, groups=DF["school_id"]).fit(reml=False)
    tau, s2 = float(reml.cov_re.iloc[0, 0]), float(reml.scale)
    return {"icc": f"{tau / (tau + s2):.3f}", "llf": f"{float(reml.llf):.3f}", "aic": f"{-2 * float(ml.llf) + 6:.3f}",
            "tau": f"{tau:.4f}", "sigma2": f"{s2:.4f}"}


EXP = _expected()


@pytest.fixture(scope="module")
def ready_page(browser):
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
    pg = ctx.new_page()
    pg.set_default_timeout(60000)
    prepare_to_m03(pg, CLEAN)
    open_m04(pg)
    run_hlm(pg)
    open_report(pg)
    pg.wait_for_function("()=>!document.querySelector('#rp-title').textContent.includes('불러오는')", timeout=60000)
    pg.locator("#btn-save").click()
    time.sleep(4)
    pg.goto(url("m06"), wait_until="networkidle")
    time.sleep(2)
    yield pg
    ctx.close()


def _download(pg, act):
    with pg.expect_download(timeout=180000) as di:
        pg.locator(f"[data-act={act}]").first.click()
    path = di.value.path()
    return di.value.suggested_filename, open(path, "rb").read()


def test_UT_M06_01_package_list_and_detail(ready_page):
    """패키지 목록에 저장한 분석이 보이고, 선택하면 상세(내보내기·공유·재현 버튼)가 열린다"""
    pg = ready_page
    pg.goto(url("m06"), wait_until="networkidle")
    time.sleep(2)
    assert pg.locator("#pk-list [data-id]").count() >= 1
    pg.locator("#pk-list [data-id]").first.click()
    time.sleep(1.5)
    assert "다층모형" in pg.locator("#pk-detail").inner_text()
    for act in ("pdf", "excel", "share", "reproduce"):
        assert pg.locator(f"[data-act={act}]").count() == 1, act


def test_UT_M06_02_pdf_export(ready_page):
    """PDF 보고서: 다운로드되고 한글 본문이 추출된다"""
    pg = ready_page
    pg.locator("#pk-list [data-id]").first.click()
    time.sleep(1)
    name, data = _download(pg, "pdf")
    assert name.endswith(".pdf") and data[:4] == b"%PDF"
    text = "".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(data)).pages)
    assert "다층모형" in text and "ICC" in text


def test_UT_M06_03_excel_export(ready_page):
    """Excel 통계표: 다운로드되고 분석 하나 = 시트 하나(시트 이름은 분석 이름, README 정의)로 구성된다"""
    pg = ready_page
    pg.locator("#pk-list [data-id]").first.click()
    time.sleep(1)
    name, data = _download(pg, "excel")
    assert name.endswith(".xlsx")
    wb = openpyxl.load_workbook(io.BytesIO(data), data_only=True)
    assert len(wb.sheetnames) == 1 and wb.sheetnames[0].startswith("다층모형")
    rows = [r for r in wb.worksheets[0].iter_rows(values_only=True) if any(c is not None for c in r)]
    assert len(rows) >= 10                                         # 구역 제목·지표·통계표가 위에서 아래로 이어짐


def test_UT_M06_04_exported_values_match_computed(ready_page):
    """PDF·Excel 의 핵심 지표(ICC·로그우도·AIC·분산성분)가 계산값과 일치 (4-2 화면 값과 동일)"""
    pg = ready_page
    pg.locator("#pk-list [data-id]").first.click()
    time.sleep(1)
    _, pdf = _download(pg, "pdf")
    _, xlsx = _download(pg, "excel")
    pdf_text = "".join((p.extract_text() or "") for p in PdfReader(io.BytesIO(pdf)).pages).replace("−", "-")
    wb = openpyxl.load_workbook(io.BytesIO(xlsx), data_only=True)
    cells = " ".join(str(c) for ws in wb.worksheets for row in ws.iter_rows(values_only=True) for c in row if c is not None).replace("−", "-")
    for label, v in EXP.items():
        assert v in pdf_text, ("PDF", label, v)
        assert v in cells, ("Excel", label, v)


def test_UT_M06_05_share_link_and_delete(ready_page):
    """공유 링크 발급·해제, 삭제(확인창 취소/삭제)"""
    pg = ready_page
    pg.locator("#pk-list [data-id]").first.click()
    time.sleep(1)
    pg.locator("[data-act=share]").click()
    pg.wait_for_selector("[data-act=copy], [data-act=unshare]", timeout=30000)
    assert pg.locator("[data-act=unshare]").count() == 1
    pg.locator("[data-act=unshare]").click()
    time.sleep(2)
    assert pg.locator("[data-act=unshare]").count() == 0
    n = pg.locator("#pk-list [data-id]").count()
    pg.locator("[data-del]").first.click()
    pg.locator("#confirm-no").click()
    time.sleep(0.8)
    assert pg.locator("#pk-list [data-id]").count() == n          # 취소하면 유지
    pg.locator("[data-del]").first.click()
    pg.locator("#confirm-yes").click()
    time.sleep(3)
    assert pg.locator("#pk-list [data-id]").count() == n - 1       # 삭제하면 목록에서 제거
