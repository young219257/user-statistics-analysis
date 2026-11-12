"""ot_dim_dmmbm03_m01 · 1단계 데이터 반입 / 데이터 결합  (UT-M01-01 ~ 13)"""
import random
import re
import time

import pandas as pd
import pytest

from helpers import MAIN, MAIN_CP949, SCHOOL, open_m01, start_with, upload, upload_error

pytestmark = pytest.mark.m01


def _big_csv(path, rows):
    random.seed(1)
    with open(path, "w") as f:
        f.write("a,b,c\n")
        for i in range(rows):
            f.write(f"{i},{random.random():.6f},x{i % 7}\n")
    return path


def _list_text(page):
    return page.locator("#ds-list").inner_text()


def test_UT_M01_01_csv_utf8_upload(page):
    """CSV(UTF-8) 업로드 → 반입 완료, 408행 16변수, 자동 선택"""
    start_with(page, MAIN)
    assert page.locator("#ds-total").inner_text().strip() == "1건"
    assert "408행, 16변수" in _list_text(page)
    assert page.locator("#ds-list input[type=checkbox], #ds-list [data-ds]").count() >= 1
    assert "16/16" in page.locator("#s1-tabs").inner_text()      # 자동 선택되어 탭이 생김


def test_UT_M01_02_csv_cp949_upload(page):
    """CSV(CP949) 업로드 → UTF-8과 같은 결과, 한글이 깨지지 않음"""
    start_with(page, MAIN_CP949)
    assert "408행, 16변수" in _list_text(page)
    assert "서울" in page.locator("#preview-body").inner_text()


def test_UT_M01_03_xlsx_single_sheet(page, tmp_path):
    """XLSX(단일 시트) 업로드 → 408행 16변수"""
    xlsx = tmp_path / "single.xlsx"
    pd.read_csv(MAIN).to_excel(xlsx, index=False)
    start_with(page, xlsx)
    txt = _list_text(page)
    assert "408행, 16변수" in txt and "xlsx" in txt


def test_UT_M01_04_unsupported_format(page, tmp_path):
    """허용되지 않는 형식(.txt) → 형식 오류 문구, 반입되지 않음"""
    bad = tmp_path / "bad.txt"
    bad.write_text("a,b\n1,2\n")
    open_m01(page)
    page.locator("#file-input").set_input_files(str(bad))
    time.sleep(1.5)
    assert "지원하지 않는 파일 형식" in upload_error(page)
    assert page.locator("#ds-total").inner_text().strip() == "0건"


def test_UT_M01_05_over_10mb_rejected(page, tmp_path):
    """파일 1건당 10MB 초과 → 안내 문구, 서버로 보내지 않음"""
    big = _big_csv(tmp_path / "big.csv", 700000)      # 약 12.6MB
    assert big.stat().st_size > 10 * 1024 * 1024
    open_m01(page)
    page.locator("#file-input").set_input_files(str(big))
    time.sleep(2)
    msg = upload_error(page)
    assert "최대 10.0MB" in msg
    assert page.locator("#ds-total").inner_text().strip() == "0건"


def test_UT_M01_06_multi_file_upload(page, tmp_path):
    """여러 파일 동시 선택 → 모두 반입·자동 선택, 형식 오류 파일은 사유를 모아 표시"""
    xlsx = tmp_path / "single.xlsx"
    pd.read_csv(MAIN).to_excel(xlsx, index=False)
    bad = tmp_path / "bad.txt"
    bad.write_text("x")
    open_m01(page)
    upload(page, MAIN, MAIN_CP949, xlsx, bad)
    assert page.locator("#ds-total").inner_text().strip() == "3건"
    assert page.locator("#s1-tabs [data-tab]").count() == 3
    assert "bad.txt" in upload_error(page)           # 실패 파일은 파일명과 함께 안내


@pytest.mark.slow
def test_UT_M01_07_total_30mb_limit(page, tmp_path):
    """선택한 데이터셋 합계 30MB 제한 → 경고 표시, 남은 용량을 넘는 데이터셋은 선택 불가"""
    open_m01(page)
    files = [_big_csv(tmp_path / f"d{i}.csv", 520000) for i in range(4)]   # 각 약 9.5MB, 합계 약 38MB
    for f in files:
        upload(page, f)
    limit = page.locator("#ds-limit").inner_text()
    assert "30.0MB" in limit and "남은 용량" in limit
    # 3개(약 28.5MB)까지만 선택되고, 4번째는 선택되지 않은 채 '남은 용량 초과'로 표시된다
    assert page.locator("#s1-tabs [data-tab]").count() == 3
    assert "남은 용량 초과" in page.locator("#ds-list").inner_text()
    assert page.locator("#ds-list [aria-disabled=true]").count() >= 1


def test_UT_M01_08_data_card_select_max_two(page):
    """데이터관리카드 선택 → 최대 2개, 초과 시 나머지는 선택 불가"""
    open_m01(page)
    cards = page.locator("#mgmt-list > *")
    assert cards.count() >= 3, "카드 목록이 비어 있음(분석 API 확인 필요)"
    cards.nth(0).click()
    page.wait_for_load_state("networkidle")
    cards.nth(1).click()
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)
    assert page.locator("#s1-tabs [data-tab]").count() == 2
    third = cards.nth(2)
    cls = (third.get_attribute("class") or "") + (third.get_attribute("aria-disabled") or "")
    assert "not-allowed" in cls or "true" in cls or "opacity" in cls


def test_UT_M01_09_column_use_and_type_change(page):
    """변수 속성: 분석 사용 해제 → 사용 열 수 감소, 타입 변경 → 서버에 반영되어 유지"""
    start_with(page, MAIN)
    page.locator('input[data-use="income"]').uncheck()
    time.sleep(0.8)
    assert "15/16" in page.locator("#s1-tabs").inner_text()
    sel = page.locator('select[data-col="grade"]')
    sel.select_option("categorical")
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)
    assert page.locator('select[data-col="grade"]').input_value() == "categorical"


def test_UT_M01_10_preview(page):
    """미리보기 → 일부 행 표시, 원본과 일치"""
    start_with(page, MAIN)
    assert "408" in page.locator("#preview-count").inner_text()
    first = pd.read_csv(MAIN).iloc[0]
    row = page.locator("#preview-body tr").first.inner_text()
    assert str(first["student_id"]) in row


def test_UT_M01_11_delete_with_confirm(page):
    """삭제 → 확인창: [취소]는 유지, [삭제]는 목록에서 제거"""
    start_with(page, MAIN)
    page.locator("[data-del]").first.click()
    page.locator("#confirm-no").click()
    time.sleep(0.5)
    assert page.locator("#ds-total").inner_text().strip() == "1건"
    page.locator("[data-del]").first.click()
    page.locator("#confirm-yes").click()
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)
    assert page.locator("#ds-total").inner_text().strip() == "0건"


def _merge(page, how):
    start_with(page, MAIN, SCHOOL)
    assert page.locator("#merge-card").is_visible()
    page.locator('select[data-m="how"]').select_option(how)
    page.locator("#btn-merge").click()
    page.wait_for_selector("#ds-list .ds-tag-merged", timeout=120000)
    page.wait_for_load_state("networkidle")
    time.sleep(1)
    return page.locator("#ds-list [data-ds]:has(.ds-tag-merged)").first.inner_text()


@pytest.mark.parametrize("how,expected", [("inner", 397), ("left", 444), ("right", 399), ("outer", 446)])
def test_UT_M01_12_merge_row_counts(page, how, expected):
    """데이터 결합 → 남길 행(inner/left/right/outer)별 행 수가 pandas merge 결과와 일치"""
    left = pd.read_csv(MAIN)
    right = pd.read_csv(SCHOOL)
    assert len(left.merge(right, on="school_id", how=how)) == expected   # 기대값 자체를 원본에서 검증
    item = _merge(page, how)
    m = re.search(r"([\d,]+)행", item)
    assert m and int(m.group(1).replace(",", "")) == expected, item


def test_UT_M01_13_merged_dataset_is_exclusive(page):
    """결합 후 → 결합 데이터셋이 목록에 '결합' 표시로 생기고 단독 선택, 다른 데이터는 선택 불가 안내"""
    _merge(page, "inner")
    assert page.locator("#ds-list .ds-tag-merged").count() == 1
    assert page.locator("#s1-tabs [data-tab]").count() == 1        # 결합 결과만 선택됨
    assert "결합된 데이터셋은" in page.locator("#ds-list").locator("xpath=..").inner_text()
    assert page.locator("#btn-proceed").is_enabled()                # 결합 결과로 2단계 진행 가능


@pytest.mark.xfail(reason="결함 D-24(S8): 한 열에 숫자와 문자가 섞인 XLSX 반입이 서버에서 internal_error 로 실패함", strict=False)
def test_UT_M01_14_xlsx_mixed_type_column(page, tmp_path):
    """XLSX 숫자·문자 혼합 열 → 반입되어야 한다 (같은 데이터를 CSV 로 올리면 성공하며, 혼합 열은 텍스트 열로 분류)"""
    x = tmp_path / "mixed.xlsx"
    pd.DataFrame({"id": [1, 2, 3, 4, 5], "income": [848.0, "6,865", 5381.0, "3,791", 1000.0]}).to_excel(x, index=False)
    start_with(page, x)
    assert page.locator("#ds-total").inner_text().strip() == "1건", upload_error(page)
    assert "5행" in _list_text(page)


def _focused_id(page):
    return page.evaluate("()=>document.activeElement && document.activeElement.id")


def test_UT_M01_15_krds_contextual_help(page):
    """KRDS 맥락적 도움말: 아이콘 버튼으로 열고 닫기, 팝오버 안 × 닫기, 닫으면 포커스가 버튼으로 복귀, Esc·바깥 클릭으로 닫기, 레이아웃을 밀지 않음"""
    open_m01(page)
    btn, pop = page.locator("#btn-upload-help"), page.locator("#upload-help")
    assert btn.get_attribute("aria-controls") == "upload-help"
    assert "tooltip-btn" in btn.get_attribute("class") and btn.locator(".ico-tooltip").count() == 1   # 아이콘만 있는 버튼
    assert pop.is_hidden() and btn.get_attribute("aria-expanded") == "false"      # 자동으로 열리지 않음
    before = page.locator("#upload-area").bounding_box()["y"]
    btn.click()
    assert pop.is_visible() and btn.get_attribute("aria-expanded") == "true"
    cls = page.locator(".krds-contextual-help").first.get_attribute("class")      # 위치 클래스는 바깥 래퍼에 붙는다
    assert ("bottom" in cls or "top" in cls) and any(c in cls for c in ("left", "center", "right"))
    css = pop.evaluate("e => { const s = getComputedStyle(e); return [s.width, s.paddingTop, s.borderTopLeftRadius, s.borderTopColor] }")
    assert css == ["360px", "24px", "12px", "rgb(177, 184, 190)"], css           # KRDS 표준 값(폭 36rem, 패딩 2.4rem, 모서리 1.2rem, gray-30)
    assert pop.locator(".tooltip-title").inner_text() == "데이터 반입 안내" and pop.locator(".tooltip-contents").count() == 1
    text = pop.inner_text()
    for word in ("데이터 반입 안내", "CSV, XLSX", "10MB", "30MB", "첫 번째 시트", "문자 열로 반입"):
        assert word in text, word
    assert page.locator("#upload-area").bounding_box()["y"] == before            # 위에 떠 있고 아래 내용을 밀지 않음
    pop.locator(".tooltip-close").click()
    assert pop.is_hidden() and _focused_id(page) == "btn-upload-help"             # × 로 닫으면 포커스가 버튼으로 복귀
    btn.click()
    btn.click()
    assert pop.is_hidden()                                                        # 버튼을 다시 누르면 닫힘
    btn.click()
    page.keyboard.press("Escape")
    assert pop.is_hidden() and _focused_id(page) == "btn-upload-help"             # Esc, 포커스 복귀
    btn.click()
    page.mouse.click(10, 10)
    assert pop.is_hidden()                                                        # 바깥 클릭


def test_UT_M01_15_help_stays_inside_narrow_screen(page):
    """좁은 화면에서도 도움말 팝오버가 화면 밖으로 잘리지 않는다 (KRDS: 화면 이탈 방지)"""
    page.set_viewport_size({"width": 420, "height": 900})
    open_m01(page)
    page.locator("#btn-upload-help").click()
    box = page.locator("#upload-help").bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= 420 + 1, box


def test_UT_M01_17_multi_sheet_xlsx_first_sheet_only(page, tmp_path):
    """시트가 2개인 XLSX → 막지 않고 반입되며 첫 번째 시트(main)만 읽힌다"""
    x = tmp_path / "multi.xlsx"
    with pd.ExcelWriter(x) as xw:
        pd.DataFrame({"id": [1, 2, 3], "v": [10, 20, 30]}).to_excel(xw, sheet_name="main", index=False)
        pd.DataFrame({"note": ["두 번째 시트"]}).to_excel(xw, sheet_name="memo", index=False)
    start_with(page, x)
    assert page.locator("#ds-total").inner_text().strip() == "1건", upload_error(page)
    assert "3행, 2변수" in _list_text(page)
