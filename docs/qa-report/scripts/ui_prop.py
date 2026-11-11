from playwright.sync_api import sync_playwright
import time, re
BASE="https://testlab-edmgr.kr/apps/app-20261006-160341"; O="/tmp/qa/out/"; S="/tmp/qa/shots/"
def settle(pg,t=2): pg.wait_for_load_state("networkidle"); time.sleep(t)
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",headless=True)
    pg=b.new_context(viewport={"width":1440,"height":1100}).new_page()
    pg.goto(BASE+"/analysis/step1",wait_until="networkidle")
    pg.locator("#file-input").set_input_files(O+"qa_main_utf8.csv")   # 문제 주입 데이터로 전처리 전파 확인
    pg.wait_for_function("()=>!document.querySelector('#upload-area .spin') && document.querySelector('#ds-list [data-ds]')",timeout=90000); time.sleep(1.5)
    pg.locator("#btn-proceed").click(); pg.wait_for_url("**/step2",timeout=30000); settle(pg)
    pg.locator("#algo-grid > *").nth(0).click(); time.sleep(.5); pg.locator("#btn-detect").click(); time.sleep(3)
    for t in ["중앙값으로 대체","윈저라이징 (클리핑)","표준화 (Standard)"]:
        pg.get_by_text(t,exact=True).click(); time.sleep(.3)
    pg.screenshot(path=S+"07_step2_prep_selected.png",full_page=True)
    sel=[g.inner_text().split("\n")[0] for g in pg.locator("#strategy-grid > *").all()]
    checked=pg.evaluate("()=>[...document.querySelectorAll('#strategy-grid input:checked')].map(i=>i.closest('label')?.innerText.split('\\n')[0])")
    print("선택된 전처리:",checked)
    pg.locator("#btn-next").click(); pg.wait_for_url("**/step3",timeout=90000); settle(pg,3)
    rows=pg.locator("#stat-body tr").all_inner_texts()
    for r in rows:
        if any(k in r for k in ("study_hours","income","school_id","satisfaction")): print("STEP3:",re.sub(r"\s+"," ",r)[:150])
    print("STEP3 상단:",pg.locator("#eda-badge").inner_text())
    pg.screenshot(path=S+"08b_step3_after_prep.png",full_page=True)
    b.close()
