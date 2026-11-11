from playwright.sync_api import sync_playwright
import time, json
BASE="https://testlab-edmgr.kr/apps/app-20261006-160341"; O="/tmp/qa/out/"; S="/tmp/qa/shots/"
def settle(pg,t=2): pg.wait_for_load_state("networkidle"); time.sleep(t)
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",headless=True)
    ctx=b.new_context(viewport={"width":1440,"height":1100},accept_downloads=True); pg=ctx.new_page()
    msgs=[]; pg.on("console",lambda m: msgs.append((m.type,m.text[:150])) if m.type in("error","warning") else None)
    # STEP1: 깨끗한 기준 데이터 사용 (알고리즘 값 확인용)
    pg.goto(BASE+"/analysis/step1",wait_until="networkidle")
    pg.locator("#file-input").set_input_files(O+"qa_clean_reference.csv")
    pg.wait_for_function("()=>!document.querySelector('#upload-area .spin') && document.querySelector('#ds-list [data-ds]')",timeout=90000); time.sleep(1.5)
    pg.locator("#btn-proceed").click(); pg.wait_for_url("**/step2",timeout=30000); settle(pg)
    # STEP2: IQR 탐지 실행 → 결측 중앙값, 이상치 윈저라이징, 표준화 선택 후 진행
    pg.locator("#algo-grid > *").nth(0).click(); time.sleep(0.5); pg.locator("#btn-detect").click(); time.sleep(3)
    pg.locator("#strategy-grid > *").nth(0).locator("label,[role=radio],input").nth(1).click(); 
    pg.locator("#strategy-grid > *").nth(1).locator("label,[role=radio],input").nth(1).click()
    pg.locator("#strategy-grid > *").nth(2).locator("label,[role=radio],input").nth(1).click()
    pg.screenshot(path=S+"07_step2_prep_selected.png",full_page=True)
    pg.locator("#btn-next").click(); pg.wait_for_url("**/step3",timeout=60000); settle(pg,3)
    # STEP3
    pg.screenshot(path=S+"08_step3.png",full_page=True)
    print("STEP3 배지:",pg.locator("#eda-badge").inner_text()[:100],"| 변수 수:",pg.locator("#stat-count").inner_text(),"행:",pg.locator("#stat-rows").inner_text())
    sel=pg.locator("#corr-method"); print("상관방법 옵션:",sel.locator("option").all_inner_texts())
    for v in sel.locator("option").evaluate_all("o=>o.map(x=>x.value)"):
        sel.select_option(v); time.sleep(2.5); print("   ",v,"표 첫행:",pg.locator("#pairs-wrap").inner_text()[:140].replace("\n"," "))
    pg.screenshot(path=S+"09_step3_corr.png",full_page=True)
    # STEP4: 선형회귀 필수표시 확인
    pg.goto(BASE+"/analysis/step4",wait_until="networkidle"); settle(pg)
    pg.screenshot(path=S+"10_step4_default.png",full_page=True)
    print("STEP4 필수표시(*) 개수:",pg.locator(".req-star:visible").count(),"| 오류문구 노출:",pg.locator(".req-field.is-error .req-msg:visible").count())
    b.close()
    print("콘솔 오류/경고:",msgs[:6])
