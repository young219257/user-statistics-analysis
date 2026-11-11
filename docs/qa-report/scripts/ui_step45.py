from playwright.sync_api import sync_playwright
import time, re, json
BASE="https://testlab-edmgr.kr/apps/app-20261006-160341"; O="/tmp/qa/out/"; S="/tmp/qa/shots/"; D="/tmp/qa/dl/"
def settle(pg,t=2): pg.wait_for_load_state("networkidle"); time.sleep(t)
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",headless=True)
    ctx=b.new_context(viewport={"width":1440,"height":1100},accept_downloads=True); pg=ctx.new_page()
    pg.goto(BASE+"/analysis/step1",wait_until="networkidle")
    pg.locator("#file-input").set_input_files(O+"qa_clean_reference.csv")
    pg.wait_for_function("()=>!document.querySelector('#upload-area .spin') && document.querySelector('#ds-list [data-ds]')",timeout=90000); time.sleep(1.5)
    pg.locator("#btn-proceed").click(); pg.wait_for_url("**/step2",timeout=30000); settle(pg)
    pg.locator("#algo-grid > *").nth(0).click(); time.sleep(.5); pg.locator("#btn-detect").click(); time.sleep(3)
    pg.locator("#btn-next").click(); pg.wait_for_url("**/step3",timeout=90000); settle(pg)
    pg.goto(BASE+"/analysis/step4",wait_until="networkidle"); settle(pg)
    # --- 선형회귀 실행 (기본 선택값 확인 후 종속변수만 지정) ---
    print("기본 기법:",pg.locator("#method-grid [aria-pressed=true]").inner_text().replace("\n"," ")[:40],"| 기본 종속변수:",pg.locator("#sel-target").input_value(),"| 독립:",pg.locator("#feat-count").inner_text())
    pg.locator("#sel-target").select_option("score_t4"); time.sleep(.5)
    pg.locator("#btn-run").click(); time.sleep(3); pg.wait_for_function("()=>!document.querySelector('#btn-run').disabled",timeout=120000); time.sleep(2)
    pg.screenshot(path=S+"11_step4_lr_result.png",full_page=True)
    print("실행 후 결과패널:",re.sub(r"\s+"," ",pg.locator("#result-panel").inner_text())[:300])
    # --- HLM: 고정효과 변수 없이 + 필수 오류 UX ---
    pg.locator("#method-grid [data-method=multilevel]").click(); time.sleep(.8)
    pg.locator("#sel-target").select_option("score_t4"); time.sleep(.4); pg.locator("#feat-none").click(); time.sleep(.5)
    print("HLM 별표 수:",pg.locator(".req-star:visible").count(),"| 오류문구:",[t for t in pg.locator(".req-msg:visible").all_inner_texts()])
    pg.screenshot(path=S+"12_step4_hlm_before.png",full_page=True)
    pg.locator("#btn-run").click(); time.sleep(4)
    print("HLM 집단변수 미선택 후 실행 → 오류문구:",pg.locator(".req-field.is-error .req-msg:visible").count(),"| 토스트/결과:",re.sub(r"\s+"," ",pg.locator("#result-panel").inner_text())[:160])
    pg.screenshot(path=S+"13_step4_hlm_error.png",full_page=True)
    pg.locator("#par-group_column").select_option("school_id"); time.sleep(.5)
    pg.locator("#btn-run").click(); time.sleep(3); pg.wait_for_function("()=>!document.querySelector('#btn-run').disabled",timeout=120000); time.sleep(2)
    print("HLM 집단변수 선택 후:",re.sub(r"\s+"," ",pg.locator("#result-panel").inner_text())[:240])
    pg.screenshot(path=S+"14_step4_hlm_result.png",full_page=True)
    # --- 4-2 리포트 ---
    pg.locator("#btn-report").click(); pg.wait_for_url("**/report",timeout=60000); settle(pg,4)
    pg.screenshot(path=S+"15_report_hlm.png",full_page=True)
    print("리포트 진단영역:",re.sub(r"\s+"," ",pg.locator("#rp-diag").inner_text())[:300] if pg.locator("#rp-diag").count() else "없음")
    print("리포트 탭:",pg.locator("#rp-tabs").inner_text().replace("\n"," | ")[:200])
    # 저장 → STEP5
    if pg.locator("#btn-save").is_visible(): pg.locator("#btn-save").click(); time.sleep(4)
    pg.goto(BASE+"/analysis/step5",wait_until="networkidle"); settle(pg,3)
    pg.screenshot(path=S+"16_step5.png",full_page=True)
    print("STEP5 목록:",pg.locator("#pk-list").inner_text().replace("\n"," | ")[:200])
    for act,name in [("pdf","pkg.pdf"),("excel","pkg.xlsx")]:
        try:
            with pg.expect_download(timeout=180000) as di: pg.locator(f"[data-act={act}]").first.click()
            dl=di.value; dl.save_as(D+name); print(act,"다운로드 OK:",dl.suggested_filename)
        except Exception as e: print(act,"다운로드 실패:",str(e)[:150])
    b.close()
