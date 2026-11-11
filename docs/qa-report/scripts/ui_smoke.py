from playwright.sync_api import sync_playwright
BASE="https://testlab-edmgr.kr/apps/app-20261006-160341"
with sync_playwright() as p:
    b=p.chromium.launch(channel="chrome",headless=True)
    pg=b.new_context(viewport={"width":1440,"height":1000}).new_page()
    errs=[]; pg.on("console",lambda m: errs.append(m.text) if m.type=="error" else None)
    pg.goto(BASE+"/",wait_until="networkidle",timeout=60000)
    print("title:",pg.title(),"| url:",pg.url)
    pg.screenshot(path="/tmp/qa/shots/01_step1_home.png",full_page=True)
    print("console errors:",errs[:5])
    b.close()
