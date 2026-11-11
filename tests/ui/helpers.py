"""화면 단위 테스트 헬퍼: 화면 조작(업로드·단계 이동·전처리·분석)과 값 읽기."""
import pathlib
import re
import time

from conftest import BASE

DATA = pathlib.Path(__file__).parent / "data"
MAIN = DATA / "qa_main_utf8.csv"          # 문제 주입 데이터 (결측·이상치·중복 등)
MAIN_CP949 = DATA / "qa_main_cp949.csv"
SCHOOL = DATA / "qa_school.csv"           # 결합용
CLEAN = DATA / "qa_clean_reference.csv"   # 문제 없는 기준 데이터 (계산 대조용)

# 화면 ID(JSP 파일명) → 접속 URL. 포털(edisn-ots)에 이식하면 여기만 바꾼다.
URLS = {
    "m01": "/analysis/step1",
    "m02": "/analysis/step2",
    "m03": "/analysis/step3",
    "m04": "/analysis/step4",
    "m05": "/analysis/step4/report",
    "m06": "/analysis/step5",
}


def url(screen):
    return BASE + URLS[screen]


def num(text):
    """'1,234.5' · '+0.04' · '12.5%' → float"""
    t = re.sub(r"[,%\s]", "", str(text)).replace("−", "-").replace("+", "")
    return float(t)


# ----------------------------------------------------------------- 1단계
def open_m01(page):
    page.goto(url("m01"), wait_until="networkidle")


def upload(page, *files, timeout=180000):
    """파일을 선택해 반입하고, 진행 표시가 끝날 때까지 기다린다 (실패해도 끝나면 반환)."""
    page.locator("#file-input").set_input_files([str(f) for f in files])
    page.wait_for_function("()=>!document.querySelector('#upload-area .spin')", timeout=timeout)
    page.wait_for_load_state("networkidle")
    time.sleep(0.8)


def start_with(page, *files):
    open_m01(page)
    upload(page, *files)


def upload_error(page):
    return " ".join(page.locator("#upload-area .krds-msg").all_inner_texts())


def to_m02(page):
    page.locator("#btn-proceed").click()
    page.wait_for_url("**/step2", timeout=60000)
    page.wait_for_load_state("networkidle")
    time.sleep(1.5)


# ----------------------------------------------------------------- 2단계
def pick_algo(page, idx=0):
    page.locator("#algo-grid > *").nth(idx).click()
    time.sleep(0.4)


def detect(page, idx=0):
    pick_algo(page, idx)
    page.locator("#btn-detect").click()
    page.wait_for_function("()=>document.querySelector('#card-outliers').textContent.trim()!=='탐지 전'", timeout=120000)
    page.wait_for_function("()=>!document.querySelector('#btn-detect').disabled", timeout=120000)
    time.sleep(0.5)


def var_rows(page):
    """이상치 진단 표 → {변수명: [칸 텍스트...]}"""
    out = {}
    for tr in page.locator("#var-body tr").all():
        cells = [c.strip() for c in tr.locator("td").all_inner_texts()]
        if cells:
            name = re.match(r"\w+", cells[0]).group()        # 이름 칸 뒤에 붙는 '범주형' 같은 배지는 제외
            out[name] = [name] + cells[1:]
    return out


def choose_rules(page, *labels):
    for lab in labels:
        page.get_by_text(lab, exact=True).click()
        time.sleep(0.2)


def to_m03(page):
    page.locator("#btn-next").click()
    page.wait_for_url("**/step3", timeout=120000)
    page.wait_for_load_state("networkidle")
    time.sleep(2.0)


def prepare_to_m03(page, file, *rules):
    """반입 → 2단계(IQR 탐지, 규칙 선택) → 3단계"""
    start_with(page, file)
    to_m02(page)
    detect(page, 0)
    if rules:
        choose_rules(page, *rules)
    to_m03(page)


# ----------------------------------------------------------------- 3단계
def stat_rows(page):
    """기초통계 표 → {변수명: {N, mean, std, min, q1, median, q3, max, skew, kurt}}"""
    keys = ["n", "mean", "std", "min", "q1", "median", "q3", "max", "skew", "kurt"]
    out = {}
    for tr in page.locator("#stat-body tr").all():
        cells = [c.strip() for c in tr.locator("td").all_inner_texts()]
        if len(cells) >= 11:
            out[cells[0]] = {k: num(v) for k, v in zip(keys, cells[1:11])}
    return out


def corr_matrix(page):
    """상관 행렬 표 → {(행, 열): 값}"""
    t = page.locator("#corr-wrap table").first
    head = [h.strip() for h in t.locator("thead th").all_inner_texts()][1:]
    out = {}
    for tr in t.locator("tbody tr").all():
        cells = [c.strip() for c in tr.locator("th,td").all_inner_texts()]
        for col, v in zip(head, cells[1:]):
            try:
                out[(cells[0], col)] = num(v)
            except ValueError:
                pass
    return out


# ----------------------------------------------------------------- 4단계
def open_m04(page):
    page.goto(url("m04"), wait_until="networkidle")
    time.sleep(1.5)


def pick_method(page, method):
    page.locator(f"#method-grid [data-method={method}]").click()
    time.sleep(0.6)


def run_and_wait(page):
    page.locator("#btn-run").click()
    time.sleep(3)
    page.wait_for_function("()=>!document.querySelector('#btn-run').disabled", timeout=180000)
    time.sleep(1.5)


def run_hlm(page, group="school_id", target="score_t4"):
    pick_method(page, "multilevel")
    page.locator("#sel-target").select_option(target)
    time.sleep(0.4)
    page.locator("#feat-none").click()
    time.sleep(0.3)
    page.locator("#par-group_column").select_option(group)
    time.sleep(0.3)
    run_and_wait(page)


def open_report(page):
    page.locator("#btn-report").click()
    page.wait_for_url("**/report", timeout=60000)
    page.wait_for_load_state("networkidle")
    time.sleep(4)
