from playwright.sync_api import sync_playwright
import time
BASE="https://testlab-edmgr.kr/apps/app-20261006-160341"; O="/tmp/qa/out/"; S="/tmp/qa/shots/"
def wait_idle(pg,t=60):
    pg.wait_for_function("()=>!document.querySelector('#upload-area .spin')",timeout=t*1000)
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",headless=True)
    pg=b.new_context(viewport={"width":1440,"height":1100}).new_page()
    pg.goto(BASE+"/analysis/step1",wait_until="networkidle")
    inp=pg.locator("#file-input")
    print("multiple 속성:", inp.get_attribute("multiple") is not None, "| accept:", inp.get_attribute("accept"))
    # 1) 3개 동시 (UTF-8 csv, CP949 csv, 단일시트 xlsx)
    inp.set_input_files([O+"qa_main_utf8.csv",O+"qa_main_cp949.csv",O+"qa_single.xlsx"])
    time.sleep(1); pg.screenshot(path=S+"02_uploading.png")
    wait_idle(pg,120); pg.wait_for_load_state("networkidle")
    print("반입 건수 표시:",pg.locator("#ds-total").inner_text(),"| 업로드 오류영역:",pg.locator("#upload-area .krds-msg").all_inner_texts())
    pg.screenshot(path=S+"03_after_multi_upload.png",full_page=True)
    # 2) 허용 안되는 형식 + 11MB + 다중시트 xlsx 동시
    pg.locator("#file-input").set_input_files([O+"bad.txt",O+"big11mb.csv",O+"qa_main.xlsx"])
    wait_idle(pg,120); time.sleep(2)
    print("혼합 업로드 오류문구:",pg.locator("#upload-area .krds-msg").all_inner_texts())
    pg.screenshot(path=S+"04_upload_errors.png",full_page=True)
    print("데이터셋 목록:",[t.split("\n")[0:2] for t in pg.locator("#ds-list [data-ds]").all_inner_texts()][:6])
    b.close()
