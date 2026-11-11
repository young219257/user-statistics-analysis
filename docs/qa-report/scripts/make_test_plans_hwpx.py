# -*- coding: utf-8 -*-
"""Word 용 문서 생성 코드(mkdocs.py)의 구성을 그대로 두고, 문단·표 생성만 한글(HWPX)로 바꿔서 같은 문서를 만든다."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from hwpx import HwpxDocument
import make_test_plans as M

FONT = "맑은 고딕"
HU = 2834.6          # 1cm = 2834.6 HWPUNIT
LINE = 130           # 본문 줄 간격(%)


class Any:
    """Word 전용 설정(페이지 크기·스타일 등)을 흘려보내는 자리표시"""
    def __getattr__(self, k): return Any()
    def __setattr__(self, k, v): pass
    def __call__(self, *a, **k): return Any()
    def __getitem__(self, k): return Any()


class DocShim:
    def __init__(self):
        self.d = HwpxDocument.new()
        self.sections = [Any()]
        self.styles = Any()
        self.pending_break = False
        self._ids = {}
        self._reuse = self.d.paragraphs[0]          # 첫 문단은 쪽 번호·용지·여백 설정을 담고 있어 지우지 않고 재사용한다

    # 서식 id: 임시 문단에 서식을 적용해 paraPr id 를 얻은 뒤 표 안 문단에 재사용
    def para_pr(self, key, **fmt):
        if key not in self._ids:
            d = self.d
            p = d.add_paragraph("")
            d.set_paragraph_format(paragraph_index=len(d.paragraphs) - 1, **fmt)
            self._ids[key] = p.para_pr_id_ref
            d.remove_paragraph(p)
        return self._ids[key]

    def border(self, fill=None):
        key = ("bf", fill)
        if key not in self._ids:
            self._ids[key] = self.d.ensure_border_fill(border_color="#000000", border_width="0.12 mm", fill_color=fill)
        return self._ids[key]

    def new_para(self):
        if self._reuse is not None:
            p, self._reuse = self._reuse, None
            return p
        return self.d.add_paragraph("")

    def save(self, path):
        d = self.d
        path = path[:-5] + ".hwpx" if path.endswith(".docx") else path
        os.makedirs(os.path.dirname(path), exist_ok=True)
        d.save_to_path(path)
        self.path = path


# ---------------------------------------------------------------- 함수 교체 (mkdocs 의 같은 이름 함수를 대체)
def para(doc, text="", size=10, bold=False, align=None, space_after=4, indent=0, color=None):
    d = doc.d
    p = doc.new_para()
    p.clear_text()
    if text:
        p.add_run(text, size=size, bold=bold, font=FONT, color=("#" + color) if color else None)
    fmt = dict(alignment="CENTER" if align == "c" else "LEFT", spacing_after_pt=space_after, line_spacing_percent=LINE)
    if indent:
        fmt["indent_left_mm"] = indent * 10
    if doc.pending_break:
        fmt["page_break_before"] = True
        doc.pending_break = False
    d.set_paragraph_format(paragraph_index=len(d.paragraphs) - 1, **fmt)
    return p


def page_break(doc):
    doc.pending_break = True


def footer_pages(doc):
    d = doc.d
    d.set_page_setup(paper_size="A4", margin_left_mm=20, margin_right_mm=20, margin_top_mm=20, margin_bottom_mm=18)
    d.set_page_number(prefix="- ", suffix=" -")


def table(doc, header, rows, widths, size=9, center_cols=(), header_fill="D9D9D9"):
    d = doc.d
    bf = doc.border()
    bfh = doc.border("#" + header_fill)
    left = doc.para_pr("cell_left", alignment="LEFT", line_spacing_percent=110, spacing_after_pt=0)
    center = doc.para_pr("cell_center", alignment="CENTER", line_spacing_percent=110, spacing_after_pt=0)
    n = len(rows) + 1
    total = int(sum(widths) * HU)
    before = len(d.paragraphs)
    t = d.add_table(n, len(header), width=total, border_fill_id_ref=bf)
    t.set_column_widths([int(w * HU) for w in widths])
    host = len(d.paragraphs) - 1
    if sum(widths) < 16.9 and host >= before - 1:                # 좁은 표(표지 등)는 가운데 정렬
        d.set_paragraph_format(paragraph_index=host, alignment="CENTER")

    def put(r, c, text, bold, ctr):
        cell = t.cell(r, c)
        pid = center if ctr else left
        lines = str(text).split("\n")
        first = cell.paragraphs[0]
        first.clear_text()
        first.para_pr_id_ref = pid
        first.add_run(lines[0], size=size, bold=bold, font=FONT)
        for ln in lines[1:]:
            np_ = cell.add_paragraph("", para_pr_id_ref=pid)
            np_.add_run(ln, size=size, bold=bold, font=FONT)

    for j, h in enumerate(header):
        t.set_cell_border_fill(0, j, bfh)
        put(0, j, h, True, True)
    for i, row in enumerate(rows, 1):
        for j, v in enumerate(row):
            put(i, j, v, False, j in center_cols)
    para(doc, "", space_after=2)
    return t


def cover(doc, title, doc_kind):
    para(doc, "")                                                          # (첫 문단은 쪽 번호·여백 설정을 담고 있어 재사용)
    with open(M.LOGO, "rb") as f:                                          # 회사 로고(표지 맨 위, 가운데)
        doc.d.add_picture(f.read(), "png", width_mm=M.LOGO_WIDTH_CM * 10, align="CENTER")
    for _ in range(3):
        para(doc, "")
    para(doc, title, 26, True, "c", space_after=14)
    para(doc, M.PROJECT, 13, False, "c", space_after=60)
    table(doc, ["항목", "내용"], [["작성일", M.TODAY], ["버  전", "0.1"]], [4, 6], size=10)
    page_break(doc)
    para(doc, "문서 개정 이력", 14, True, "c", space_after=8)
    table(doc, ["문서명", doc_kind], [], [4, 12], size=10)
    rows = [["0.1", M.TODAY, "최초 작성", "", "", ""]] + [[""] * 6 for _ in range(7)]
    table(doc, ["버전", "날짜", "내용", "작성자", "검토자", "승인자"], rows, [1.6, 2.6, 6.0, 2.2, 2.2, 2.2], size=9, center_cols=(0, 1))
    page_break(doc)


# mkdocs 의 함수를 교체 (h1/h2/bullet/toc/cases_appendix/progress 는 교체된 para/table 을 자동으로 사용)
M.para, M.page_break, M.footer_pages, M.table, M.cover = para, page_break, footer_pages, table, cover
M.Document = DocShim
M.OUT = "/Users/gim-yeong-a/keris/이용자통계분석/테스트"

if __name__ == "__main__":
    for k in ("UT", "IT"):
        path, n = M.build(k)
        print(path.replace(".docx", ".hwpx"), "| 케이스", n)
