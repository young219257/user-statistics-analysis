"""화면 단위 테스트 공통 설정 (Playwright + pytest).

환경변수
  UI_BASE_URL          테스트 대상 주소 (기본 http://localhost:8090)
  UI_BROWSER_CHANNEL   chrome(기본, 설치된 Chrome 사용) | msedge | chromium(playwright 내장)
  UI_HEADED=1          브라우저 창을 띄워서 실행
"""
import os
import pathlib
import pytest
from playwright.sync_api import sync_playwright

BASE = os.environ.get("UI_BASE_URL", "http://localhost:8090").rstrip("/")
CHANNEL = os.environ.get("UI_BROWSER_CHANNEL", "chrome")
HEADED = os.environ.get("UI_HEADED") == "1"
REPORTS = pathlib.Path(__file__).parent / "reports"


@pytest.fixture(scope="session")
def browser():
    with sync_playwright() as p:
        kw = {"headless": not HEADED}
        if CHANNEL != "chromium":
            kw["channel"] = CHANNEL
        b = p.chromium.launch(**kw)
        yield b
        b.close()


@pytest.fixture
def page(browser):
    """테스트마다 새 브라우저 컨텍스트 = 새 세션(쿠키·sessionStorage 초기화)"""
    ctx = browser.new_context(viewport={"width": 1440, "height": 1100}, accept_downloads=True)
    pg = ctx.new_page()
    pg.set_default_timeout(45000)
    pg.js_errors = []
    pg.on("pageerror", lambda e: pg.js_errors.append(str(e)))
    yield pg
    ctx.close()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """실패한 테스트는 화면 캡처를 reports/ 에 저장"""
    outcome = yield
    rep = outcome.get_result()
    if rep.when == "call" and rep.failed:
        pg = item.funcargs.get("page") or item.funcargs.get("ready_page")
        if pg is not None:
            try:
                REPORTS.mkdir(exist_ok=True)
                pg.screenshot(path=str(REPORTS / f"{item.name}.png"), full_page=True)
            except Exception:
                pass
