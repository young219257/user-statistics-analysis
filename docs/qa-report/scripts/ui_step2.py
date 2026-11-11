from playwright.sync_api import sync_playwright
import time, json
BASE="https://testlab-edmgr.kr/apps/app-20261006-160341"; O="/tmp/qa/out/"; S="/tmp/qa/shots/"
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",headless=True)
    pg=b.new_context(viewport={"width":1440,"height":1100}).new_page()
    pg.goto(BASE+"/analysis/step1",wait_until="networkidle")
    pg.locator("#file-input").set_input_files(O+"qa_main_utf8.csv")
    pg.wait_for_function("()=>!document.querySelector('#upload-area .spin') && document.querySelector('#ds-list [data-ds]')",timeout=90000); time.sleep(1.5)
    pg.locator("#btn-proceed").click(); pg.wait_for_url("**/step2",timeout=30000); pg.wait_for_load_state("networkidle"); time.sleep(2)
    pg.screenshot(path=S+"05_step2_initial.png",full_page=True)
    def cards(): return {k:pg.locator("#"+k).inner_text().replace("\n"," ") for k in ["card-rows","card-missing","card-out-label","card-outliers","card-dups"]}
    print("초기 카드:",cards())
    print("진단 경고/문구:",pg.locator("#judge-note").inner_text()[:200].replace("\n"," "))
    print("알고리즘 버튼:",[t.replace("\n"," | ")[:50] for t in pg.locator("#algo-grid > *").all_inner_texts()])
    print("전처리 전략 그룹 순서:")
    for g in pg.locator("#strategy-grid > *").all():
        t=g.inner_text().split("\n"); print("   ",t[0],"→",[x for x in t[1:] if x.strip()][:14:2])
    # 이상치 7종 실행
    n=pg.locator("#algo-grid > *").count()
    for i in range(n):
        pg.locator("#algo-grid > *").nth(i).click(); time.sleep(0.4)
        name=pg.locator("#algo-sel-name").inner_text()
        pg.locator("#btn-detect").click(); time.sleep(3.0)
        try: pg.wait_for_function("()=>!document.querySelector('#btn-detect').disabled",timeout=60000)
        except: pass
        rows=pg.locator("#var-body tr").all_inner_texts()
        print(f"[{name.strip()}] 카드:",pg.locator('#card-outliers').inner_text().replace("\n"," "),"| 기준:",pg.locator('#applied-formula').inner_text().replace("\n"," ")[:80],"| 변수행수:",len(rows))
        if i in (0,4): pg.screenshot(path=S+f"06_detect_{i}.png",full_page=True)
        if i==4: print("   마할라노비스 변수별:",[r.replace("\n"," ").replace("\t"," ")[:70] for r in rows[:5]])
    b.close()
