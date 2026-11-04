package kr.or.keris.statistics.export;

import com.lowagie.text.Chunk;
import com.lowagie.text.Document;
import com.lowagie.text.DocumentException;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.HeaderFooter;
import com.lowagie.text.Image;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.Phrase;
import com.lowagie.text.Rectangle;
import com.lowagie.text.pdf.BaseFont;
import com.lowagie.text.pdf.PdfPCell;
import com.lowagie.text.pdf.PdfPTable;
import com.lowagie.text.pdf.PdfWriter;
import java.awt.Color;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;
import java.util.Locale;

/**
 * Report → PDF (iText 2.1.7). 4-2 분석 결과 리포트 화면을 닮게 만든다.
 *
 *   머리말        : 분석 이름 · 기법 · 내보낸 시각, 아래 가는 선
 *   핵심 지표     : 지표 카드 줄 (라벨 작게, 값 크게) — 화면 상단 요약 카드
 *   개요·조건     : 항목(회색) | 값 목록, 줄 사이 옅은 선
 *   결과표        : 카드 제목 + 회색 머리 표 + 아랫줄만 있는 행 + 각주 — 화면의 통계표(statCard)
 *   차트          : "Figure n. 제목" + 설명 + 이미지 (이미지가 전달된 경우)
 *
 * 한글 표시에는 TTF 폰트가 필요하다(FontResolver 참고).
 */
public final class PdfExporter {
    private PdfExporter() { }

    private static final Color NAVY = new Color(30, 44, 93);         // #1e2c5d
    private static final Color INK = new Color(25, 31, 40);          // #191f28
    private static final Color MUTED = new Color(107, 118, 132);     // #6b7684
    private static final Color RULE = new Color(229, 232, 235);      // #e5e8eb
    private static final Color RULE_SOFT = new Color(242, 244, 246); // #f2f4f6
    private static final Color HEAD_BG = new Color(242, 244, 246);   // 표 머리 회색
    private static final Color CHIP_BG = new Color(232, 236, 246);   // #e8ecf6

    private static final int MAX_ROWS = 60;
    private static final int MAX_COLS = 9;
    private static final int KPI_PER_ROW = 4;

    public static byte[] write(Report report, BaseFont base) throws DocumentException, IOException {
        boolean korean = base != null;
        if (base == null) base = BaseFont.createFont(BaseFont.HELVETICA, BaseFont.WINANSI, BaseFont.NOT_EMBEDDED);
        Font fTitle = new Font(base, 14, Font.BOLD, INK);
        Font fSub = new Font(base, 8.5f, Font.NORMAL, MUTED);
        Font fCardTitle = new Font(base, 10.5f, Font.BOLD, INK);
        Font fLabel = new Font(base, 8.5f, Font.NORMAL, MUTED);
        Font fValue = new Font(base, 9, Font.NORMAL, INK);
        Font fKpiLabel = new Font(base, 7.5f, Font.NORMAL, MUTED);
        Font fKpiValue = new Font(base, 11, Font.BOLD, NAVY);
        Font fHead = new Font(base, 7.5f, Font.NORMAL, MUTED);
        Font fCell = new Font(base, 8, Font.NORMAL, INK);
        Font fTableTitle = new Font(base, 9, Font.BOLD, INK);
        Font fNote = new Font(base, 7.5f, Font.NORMAL, MUTED);
        Font fFoot = new Font(base, 7.5f, Font.NORMAL, MUTED);
        Font fChip = new Font(base, 7.5f, Font.BOLD, NAVY);

        ByteArrayOutputStream out = new ByteArrayOutputStream();
        Document doc = new Document(PageSize.A4, 40, 40, 44, 48);
        PdfWriter writer = PdfWriter.getInstance(doc, out);
        HeaderFooter footer = new HeaderFooter(new Phrase("- ", fFoot), new Phrase(" -", fFoot));
        footer.setAlignment(Element.ALIGN_CENTER);
        footer.setBorder(Rectangle.NO_BORDER);
        doc.setFooter(footer);
        doc.open();

        // 머리말
        doc.add(new Paragraph(nz(report.title), fTitle));
        doc.add(rule(6, 4));
        if (!korean) doc.add(new Paragraph("※ 한글 폰트를 찾지 못해 한글이 표시되지 않습니다. 서버에 PDF_FONT_PATH 또는 /WEB-INF/fonts/ 에 TTF 폰트를 지정하세요.", fNote));

        if (!report.screen.isEmpty()) {
            writeScreen(doc, writer, report, base, fCardTitle, fCell, fHead, fNote, fKpiLabel, fKpiValue, fTableTitle, fChip);
            doc.close();
            return out.toByteArray();
        }

        int figure = 0;
        for (Report.Section s : report.sections) {
            boolean any = !s.kv.isEmpty() || !s.images.isEmpty();
            for (Report.Table t : s.tables) if (!t.excelOnly) any = true;
            if (!any) continue;

            // 제목이 쪽 맨 아래에 혼자 남지 않게, 남은 자리가 모자라면 다음 쪽에서 시작한다
            if (writer.getVerticalPosition(true) < 170) doc.newPage();
            Paragraph head = new Paragraph(s.title, fCardTitle);
            head.setSpacingBefore(14);
            head.setSpacingAfter(2);
            doc.add(head);
            doc.add(rule(2, 6));

            if (!s.kv.isEmpty()) {
                if (isKpiSection(s)) doc.add(kpiGrid(s, fKpiLabel, fKpiValue));
                else doc.add(kvList(s, fLabel, fValue));
            }
            for (Report.Table t : s.tables) {
                if (t.excelOnly) continue;
                doc.add(table(t, fHead, fCell, fTableTitle, fNote));
            }
            for (Report.Img img : s.images) {
                figure++;
                PdfPTable cap = new PdfPTable(new float[]{12, 88});
                cap.setWidthPercentage(100);
                cap.setSpacingBefore(10);
                PdfPCell chip = new PdfPCell(new Phrase("Figure " + figure, fChip));
                chip.setBackgroundColor(CHIP_BG);
                chip.setBorder(Rectangle.NO_BORDER);
                chip.setPadding(3);
                chip.setHorizontalAlignment(Element.ALIGN_CENTER);
                cap.addCell(chip);
                PdfPCell t = new PdfPCell(new Phrase(nz(img.title), fTableTitle));
                t.setBorder(Rectangle.NO_BORDER);
                t.setPaddingLeft(8);
                t.setVerticalAlignment(Element.ALIGN_MIDDLE);
                cap.addCell(t);
                doc.add(cap);
                try {
                    Image im = Image.getInstance(img.png);
                    im.scaleToFit(500, 260);
                    im.setAlignment(Element.ALIGN_CENTER);
                    im.setSpacingBefore(4);
                    doc.add(im);
                } catch (Exception e) {
                    doc.add(new Paragraph("(차트 이미지를 불러오지 못했습니다)", fNote));
                }
            }
        }
        doc.close();
        return out.toByteArray();
    }

    /** 4-2 리포트 화면의 구역을 그대로: 카드 제목 → 지표 카드 줄 → 통계표(병합 머리 포함) → 각주 → Figure. */
    private static void writeScreen(Document doc, PdfWriter writer, Report report, BaseFont base, Font fCardTitle, Font fCell, Font fHead,
                                    Font fNote, Font fKpiLabel, Font fKpiValue, Font fTableTitle, Font fChip) throws DocumentException {
        Font fHeadBold = new Font(base, 8, Font.BOLD, INK);
        Font fBanner = new Font(base, 12.5f, Font.BOLD, NAVY);
        int fig = 0;
        boolean first = true;
        for (Report.Screen sc : report.screen) {
            if (sc.banner) {
                if (!first) doc.newPage();   // 분석마다 새 쪽에서 시작
                Paragraph bp = new Paragraph(sc.title, fBanner);
                bp.setSpacingAfter(2);
                doc.add(bp);
                doc.add(rule(2, 4));
                first = false;
                continue;
            }
            first = false;
            if (!sc.title.isEmpty()) {
                if (writer.getVerticalPosition(true) < 170) doc.newPage();
                Paragraph head = new Paragraph(sc.title, fCardTitle);
                head.setSpacingBefore(14);
                head.setSpacingAfter(2);
                doc.add(head);
                doc.add(rule(2, 6));
            }
            if (!sc.kpis.isEmpty()) {
                int cols = Math.min(KPI_PER_ROW, sc.kpis.size());
                PdfPTable g = new PdfPTable(cols);
                g.setWidthPercentage(100);
                g.setSpacingAfter(6);
                for (Report.Kpi k : sc.kpis) {
                    PdfPCell c = new PdfPCell();
                    c.setBorderColor(RULE);
                    c.setBorderWidth(0.8f);
                    c.setPadding(7);
                    c.addElement(new Paragraph(k.label, fKpiLabel));
                    Paragraph v = new Paragraph(k.value, fKpiValue);
                    v.setSpacingBefore(2);
                    c.addElement(v);
                    if (!k.caption.isEmpty()) c.addElement(new Paragraph(k.caption, fNote));
                    g.addCell(c);
                }
                int rest = (cols - (sc.kpis.size() % cols)) % cols;
                for (int i = 0; i < rest; i++) { PdfPCell e = new PdfPCell(new Phrase(" ")); e.setBorder(Rectangle.NO_BORDER); g.addCell(e); }
                doc.add(g);
            }
            for (List<List<Report.Cell>> rows : sc.tables) doc.add(safeTable(rows, fHeadBold, fCell));
            for (String n : sc.notes) {
                Paragraph np = new Paragraph(n, fNote);
                np.setSpacingBefore(2);
                doc.add(np);
            }
            for (Report.Figure f : sc.figures) {
                fig++;
                if (writer.getVerticalPosition(true) < 300) doc.newPage();
                Paragraph cap = new Paragraph(f.title, fTableTitle);
                cap.setSpacingBefore(12);
                doc.add(cap);
                if (!f.subtitle.isEmpty()) doc.add(new Paragraph(f.subtitle, fNote));
                try {
                    Image im = Image.getInstance(f.png);
                    im.scaleToFit(500, 270);
                    im.setAlignment(Element.ALIGN_CENTER);
                    im.setSpacingBefore(4);
                    doc.add(im);
                } catch (Exception e) {
                    doc.add(new Paragraph("(차트 이미지를 불러오지 못했습니다)", fNote));
                }
            }
        }
    }

    /**
     * 병합 칸이 있는 표를 먼저 임시 문서에 그려 보고, iText 가 거부하면 병합 없는 표로 바꾼다.
     * 표 하나가 문서 전체(내보내기)를 실패시키지 않게 하기 위한 안전장치다.
     */
    private static PdfPTable safeTable(List<List<Report.Cell>> rows, Font fHead, Font fCell) throws DocumentException {
        try {
            PdfPTable t = screenTable(rows, fHead, fCell);
            Document probe = new Document(PageSize.A4);
            PdfWriter.getInstance(probe, new ByteArrayOutputStream());
            probe.open();
            probe.add(t);
            probe.close();
            return screenTable(rows, fHead, fCell);   // 시험에 쓴 표는 다시 쓸 수 없어 새로 만든다
        } catch (Throwable e) {
            return plainTable(rows, fHead, fCell);
        }
    }

    /** 병합 없이 칸을 그대로 펼친 표. */
    private static PdfPTable plainTable(List<List<Report.Cell>> rows, Font fHead, Font fCell) {
        int cols = 1;
        for (List<Report.Cell> r : rows) cols = Math.max(cols, Math.min(r.size(), 14));
        PdfPTable tb = new PdfPTable(cols);
        tb.setWidthPercentage(100);
        tb.setSpacingBefore(4);
        for (List<Report.Cell> r : rows) {
            for (int c = 0; c < cols; c++) {
                Report.Cell cell = c < r.size() ? r.get(c) : null;
                PdfPCell pc = new PdfPCell(new Phrase(cell == null ? " " : cell.text, cell != null && cell.head ? fHead : fCell));
                pc.setPadding(4);
                pc.setBorderColor(RULE);
                pc.setBorderWidth(0.6f);
                if (cell != null && cell.head) {
                    pc.setBackgroundColor(HEAD_BG);
                    pc.setHorizontalAlignment(Element.ALIGN_CENTER);
                } else if (cell != null) {
                    pc.setHorizontalAlignment(looksNumeric(cell.text) ? Element.ALIGN_RIGHT : Element.ALIGN_LEFT);
                }
                tb.addCell(pc);
            }
        }
        return tb;
    }

    /** 화면 표를 칸 병합(colspan·rowspan)까지 그대로 옮긴다. 머리 칸은 회색, 숫자는 오른쪽 정렬. */
    private static PdfPTable screenTable(List<List<Report.Cell>> rows, Font fHead, Font fCell) throws DocumentException {
        int cols = 0;
        for (List<Report.Cell> r : rows) { int n = 0; for (Report.Cell c : r) n += c.colspan; cols = Math.max(cols, n); }
        cols = Math.min(Math.max(cols, 1), 14);
        PdfPTable tb = new PdfPTable(cols);
        tb.setWidthPercentage(100);
        tb.setSpacingBefore(4);
        int headRows = 0;
        for (List<Report.Cell> r : rows) { if (!r.isEmpty() && r.get(0).head) headRows++; else break; }
        boolean headerSpan = false;
        for (int r = 0; r < headRows; r++) for (Report.Cell c : rows.get(r)) if (c.rowspan > 1) headerSpan = true;
        tb.setHeaderRows(headerSpan ? 0 : headRows);   // 머리에 세로 병합이 있으면 머리 반복을 끈다(켜면 병합 칸이 첫 줄 높이로만 그려진다)
        // 병합 칸이 차지하는 자리를 직접 계산한다. iText 2.1.7 은 colspan 과 rowspan 을 함께 가진 칸,
        // 비어 있는 칸, 표 끝을 넘는 rowspan 이 있으면 NullPointerException 으로 문서 전체를 실패시킨다.
        //  - 한 칸 너비의 rowspan 은 iText 에 맡기고
        //  - colspan 이 있는 rowspan 은 윗줄 칸 + 아랫줄 빈 칸(윗선 없음)으로 합쳐 보이게 한다
        int nRows = rows.size();
        int[][] kind = new int[nRows][cols];      // 0 비어 있음, 1 rowspan 이 차지, 2 합쳐 보이는 빈 칸 시작, 3 그 이어지는 칸
        int[][] fillSpan = new int[nRows][cols];
        for (int r = 0; r < nRows; r++) {
            java.util.Iterator<Report.Cell> it = rows.get(r).iterator();
            int col = 0;
            while (col < cols) {
                if (kind[r][col] == 1 || kind[r][col] == 3) { col++; continue; }
                if (kind[r][col] == 2) {
                    int span = fillSpan[r][col];
                    PdfPCell f = new PdfPCell(new Phrase(" ", fCell));
                    f.setColspan(span);
                    f.setBackgroundColor(HEAD_BG);
                    f.setBorderColor(RULE);
                    f.setBorderWidth(0.6f);
                    f.setBorder(Rectangle.LEFT | Rectangle.RIGHT | Rectangle.BOTTOM);
                    tb.addCell(f);
                    col += span;
                    continue;
                }
                if (!it.hasNext()) {
                    PdfPCell blank = new PdfPCell(new Phrase(" ", fCell));
                    blank.setBorderColor(RULE);
                    blank.setBorderWidth(0.6f);
                    tb.addCell(blank);
                    col++;
                    continue;
                }
                Report.Cell c = it.next();
                int span = Math.min(c.colspan, cols - col);
                for (int k = 1; k < span; k++) if (kind[r][col + k] != 0) { span = k; break; }
                int rspan = Math.min(c.rowspan, nRows - r);
                PdfPCell pc = new PdfPCell(new Phrase(c.text, c.head ? fHead : fCell));
                pc.setColspan(span);
                pc.setPadding(4);
                pc.setBorderColor(RULE);
                pc.setBorderWidth(0.6f);
                if (c.head) {
                    pc.setBackgroundColor(HEAD_BG);
                    pc.setHorizontalAlignment(Element.ALIGN_CENTER);
                    pc.setVerticalAlignment(Element.ALIGN_MIDDLE);
                } else {
                    pc.setHorizontalAlignment(looksNumeric(c.text) ? Element.ALIGN_RIGHT : Element.ALIGN_LEFT);
                }
                if (rspan > 1 && span == 1) {
                    pc.setRowspan(rspan);
                    for (int dr = 1; dr < rspan; dr++) kind[r + dr][col] = 1;
                } else if (rspan > 1) {
                    pc.setBorder(Rectangle.LEFT | Rectangle.RIGHT | Rectangle.TOP);   // 아래 칸과 이어 보이게
                    for (int dr = 1; dr < rspan; dr++) {
                        kind[r + dr][col] = 2;
                        fillSpan[r + dr][col] = span;
                        for (int k = 1; k < span; k++) kind[r + dr][col + k] = 3;
                    }
                }
                tb.addCell(pc);
                col += span;
            }
        }
        tb.completeRow();
        return tb;
    }

    private static boolean looksNumeric(String s) {
        if (s == null || s.isEmpty()) return false;
        return s.matches("[-+]?[.\\d,]+(\\.\\d+)?%?\\*{0,3}");
    }

    /** 핵심 지표 섹션만 카드 줄로 그린다 (화면 상단의 요약 카드). */
    private static boolean isKpiSection(Report.Section s) {
        return s.title != null && s.title.endsWith("핵심 지표");
    }

    private static PdfPTable kpiGrid(Report.Section s, Font fLabel, Font fValue) throws DocumentException {
        int n = s.kv.size();
        int cols = Math.min(KPI_PER_ROW, Math.max(n, 1));
        PdfPTable g = new PdfPTable(cols);
        g.setWidthPercentage(100);
        g.setSpacingAfter(4);
        for (int i = 0; i < n; i++) {
            Object[] row = s.kv.get(i);
            PdfPCell c = new PdfPCell();
            c.setBorderColor(RULE);
            c.setBorderWidth(0.8f);
            c.setPadding(7);
            Paragraph label = new Paragraph(String.valueOf(row[0]), fLabel);
            Paragraph value = new Paragraph(fmt(row[1]), fValue);
            value.setSpacingBefore(2);
            c.addElement(label);
            c.addElement(value);
            g.addCell(c);
        }
        int rest = (cols - (n % cols)) % cols;
        for (int i = 0; i < rest; i++) {
            PdfPCell e = new PdfPCell(new Phrase(" "));
            e.setBorder(Rectangle.NO_BORDER);
            g.addCell(e);
        }
        return g;
    }

    /** 개요·조건: 항목 이름(회색) | 값, 줄 사이 옅은 선. */
    private static PdfPTable kvList(Report.Section s, Font fLabel, Font fValue) throws DocumentException {
        PdfPTable kv = new PdfPTable(new float[]{26, 74});
        kv.setWidthPercentage(100);
        for (Object[] row : s.kv) {
            kv.addCell(lineCell(String.valueOf(row[0]), fLabel, Element.ALIGN_LEFT));
            kv.addCell(lineCell(fmt(row[1]), fValue, Element.ALIGN_LEFT));
        }
        return kv;
    }

    /** 결과표: 회색 머리 + 아랫줄만 있는 행. 숫자는 오른쪽, 글자는 왼쪽 정렬 (화면의 통계표와 같은 규칙). */
    private static PdfPTable table(Report.Table t, Font fHead, Font fCell, Font fTitle, Font fNote) throws DocumentException {
        int cols = Math.min(t.headers.size(), MAX_COLS);
        PdfPTable tb = new PdfPTable(Math.max(cols, 1));
        tb.setWidthPercentage(100);
        tb.setSpacingBefore(8);
        tb.setHeaderRows(2);
        PdfPCell title = new PdfPCell(new Phrase(t.title, fTitle));
        title.setColspan(Math.max(cols, 1));
        title.setBorder(Rectangle.NO_BORDER);
        title.setPaddingBottom(4);
        tb.addCell(title);
        boolean[] numeric = new boolean[Math.max(cols, 1)];
        int shown = Math.min(t.rows.size(), MAX_ROWS);
        for (int c = 0; c < cols; c++) {
            int num = 0, all = 0;
            for (int r = 0; r < shown; r++) {
                List<Object> row = t.rows.get(r);
                if (c < row.size() && row.get(c) != null) { all++; if (row.get(c) instanceof Number) num++; }
            }
            numeric[c] = all > 0 && num * 2 >= all;
        }
        for (int c = 0; c < cols; c++) {
            PdfPCell h = new PdfPCell(new Phrase(t.headers.get(c), fHead));
            h.setBackgroundColor(HEAD_BG);
            h.setBorder(Rectangle.BOTTOM);
            h.setBorderColor(RULE);
            h.setPadding(4);
            h.setHorizontalAlignment(numeric[c] ? Element.ALIGN_RIGHT : Element.ALIGN_LEFT);
            tb.addCell(h);
        }
        for (int r = 0; r < shown; r++) {
            List<Object> row = t.rows.get(r);
            for (int c = 0; c < cols; c++) {
                tb.addCell(lineCell(c < row.size() ? fmt(row.get(c)) : "", fCell, numeric[c] ? Element.ALIGN_RIGHT : Element.ALIGN_LEFT));
            }
        }
        StringBuilder note = new StringBuilder();
        if (t.rows.size() > shown) note.append("전체 ").append(t.rows.size()).append("행 중 ").append(shown).append("행만 표시했습니다. ");
        if (t.headers.size() > cols) note.append("열 ").append(t.headers.size()).append("개 중 ").append(cols).append("개만 표시했습니다. ");
        if (note.length() > 0) {
            note.append("전체 내용은 Excel 내보내기를 이용하세요.");
            PdfPCell nc = new PdfPCell(new Phrase(note.toString(), fNote));
            nc.setColspan(Math.max(cols, 1));
            nc.setBorder(Rectangle.NO_BORDER);
            nc.setPaddingTop(4);
            tb.addCell(nc);
        }
        return tb;
    }

    /** 아랫줄만 있는 셀. */
    private static PdfPCell lineCell(String text, Font f, int align) {
        PdfPCell c = new PdfPCell(new Phrase(text, f));
        c.setBorder(Rectangle.BOTTOM);
        c.setBorderColor(RULE_SOFT);
        c.setBorderWidth(0.8f);
        c.setPadding(4);
        c.setPaddingTop(5);
        c.setHorizontalAlignment(align);
        return c;
    }

    /** 가는 구분선. */
    private static PdfPTable rule(float before, float after) {
        PdfPTable r = new PdfPTable(1);
        r.setWidthPercentage(100);
        r.setSpacingBefore(before);
        r.setSpacingAfter(after);
        PdfPCell c = new PdfPCell(new Phrase(" ", new Font(Font.HELVETICA, 1)));
        c.setBorder(Rectangle.BOTTOM);
        c.setBorderColor(RULE);
        c.setBorderWidth(0.8f);
        c.setFixedHeight(1);
        r.addCell(c);
        return r;
    }

    private static String nz(String s) {
        return s == null ? "" : s;
    }

    static String fmt(Object v) {
        if (v == null) return "-";
        if (v instanceof Boolean) return ((Boolean) v) ? "예" : "아니오";
        if (v instanceof Double || v instanceof Float) {
            double d = ((Number) v).doubleValue();
            if (Double.isNaN(d) || Double.isInfinite(d)) return "-";
            String s = String.format(Locale.ROOT, "%.4f", d);
            s = s.replaceAll("0+$", "").replaceAll("\\.$", "");
            return s;
        }
        String s = String.valueOf(v);
        return s.length() > 300 ? s.substring(0, 300) + "…" : s;
    }
}
