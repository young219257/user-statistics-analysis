package kr.or.keris.statistics.export;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.text.SimpleDateFormat;
import java.util.ArrayList;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.apache.poi.ss.usermodel.BorderStyle;
import org.apache.poi.ss.usermodel.Cell;
import org.apache.poi.ss.usermodel.CellStyle;
import org.apache.poi.ss.usermodel.FillPatternType;
import org.apache.poi.ss.usermodel.Font;
import org.apache.poi.ss.usermodel.HorizontalAlignment;
import org.apache.poi.ss.usermodel.IndexedColors;
import org.apache.poi.ss.usermodel.Row;
import org.apache.poi.ss.usermodel.Sheet;
import org.apache.poi.ss.usermodel.VerticalAlignment;
import org.apache.poi.ss.util.CellRangeAddress;
import org.apache.poi.xssf.usermodel.XSSFWorkbook;

/**
 * Report → .xlsx. 엑셀은 보는 문서가 아니라 값을 가져다 쓰는 표 묶음으로 만든다.
 *
 *   시트 1 "요약"  : 분석 개요·핵심 지표·분석 조건을 "항목 | 값" 두 열로, 아래에 표 목록(시트 이름·행 수)
 *   시트 2…       : 표마다 시트 1개 (머리글 한 줄 · 첫 행 고정 · 자동 필터 · 숫자는 숫자로 · p값은 0.000)
 *   순서          : 리포트 화면 순서(개요 → 결과표 → 차트 → 원본 데이터), 큰 표(excelOnly)는 뒤쪽
 *
 * POI 3.17 (Java 7 호환)
 */
public final class ExcelExporter {
    private ExcelExporter() { }

    private static final int MAX_CELL = 32000;

    public static byte[] write(Report report) throws IOException {
        if (!report.screen.isEmpty()) return writeScreens(report);   // 4-2 화면에서 받은 내용(PDF 와 같은 구성)
        XSSFWorkbook wb = new XSSFWorkbook();
        try {
            Font bold = wb.createFont();
            bold.setBold(true);
            Font title = wb.createFont();
            title.setBold(true);
            title.setFontHeightInPoints((short) 14);
            Font muted = wb.createFont();
            muted.setColor(IndexedColors.GREY_50_PERCENT.getIndex());

            CellStyle titleStyle = wb.createCellStyle();
            titleStyle.setFont(title);
            CellStyle mutedStyle = wb.createCellStyle();
            mutedStyle.setFont(muted);
            CellStyle sectionStyle = wb.createCellStyle();
            sectionStyle.setFont(bold);
            sectionStyle.setFillForegroundColor(IndexedColors.LIGHT_CORNFLOWER_BLUE.getIndex());
            sectionStyle.setFillPattern(FillPatternType.SOLID_FOREGROUND);
            CellStyle head = wb.createCellStyle();
            head.setFont(bold);
            head.setFillForegroundColor(IndexedColors.GREY_25_PERCENT.getIndex());
            head.setFillPattern(FillPatternType.SOLID_FOREGROUND);
            head.setBorderBottom(BorderStyle.THIN);
            head.setAlignment(HorizontalAlignment.CENTER);
            head.setVerticalAlignment(VerticalAlignment.CENTER);
            head.setWrapText(true);
            CellStyle labelStyle = wb.createCellStyle();
            labelStyle.setFont(bold);
            CellStyle textStyle = wb.createCellStyle();
            textStyle.setWrapText(true);
            textStyle.setVerticalAlignment(VerticalAlignment.TOP);
            CellStyle intStyle = wb.createCellStyle();
            intStyle.setDataFormat(wb.createDataFormat().getFormat("#,##0"));
            CellStyle dblStyle = wb.createCellStyle();
            dblStyle.setDataFormat(wb.createDataFormat().getFormat("#,##0.0000"));
            CellStyle pStyle = wb.createCellStyle();
            pStyle.setDataFormat(wb.createDataFormat().getFormat("0.000"));

            // 표마다 시트 이름을 미리 정해, 요약 시트의 표 목록에서 같은 이름을 보여 준다.
            Set<String> used = new HashSet<String>();
            String summaryName = unique("요약", used);
            List<Report.Table> order = new ArrayList<Report.Table>();
            List<String> sheetNames = new ArrayList<String>();
            for (Report.Section s : report.sections) {
                for (Report.Table tb : s.tables) {
                    order.add(tb);
                    sheetNames.add(unique(tb.title, used));
                }
            }

            Sheet summary = wb.createSheet(summaryName);
            int r = 0;
            cell(summary.createRow(r++), 0, report.title, titleStyle, intStyle, dblStyle);
            String sub = report.subtitle == null ? "" : report.subtitle + "  ·  ";
            cell(summary.createRow(r++), 0, sub + "내보낸 시각 " + new SimpleDateFormat("yyyy-MM-dd HH:mm").format(new Date()), mutedStyle, intStyle, dblStyle);
            r++;

            for (Report.Section s : report.sections) {
                if (s.kv.isEmpty()) continue;
                Row h = summary.createRow(r++);
                cell(h, 0, s.title, sectionStyle, intStyle, dblStyle);
                cell(h, 1, null, sectionStyle, intStyle, dblStyle);
                for (Object[] kv : s.kv) {
                    Row row = summary.createRow(r++);
                    cell(row, 0, kv[0], labelStyle, intStyle, dblStyle);
                    Object v = kv[1];
                    cell(row, 1, v, v instanceof String ? textStyle : null, intStyle, dblStyle);
                }
                r++;
            }
            if (!order.isEmpty()) {
                Row h = summary.createRow(r++);
                cell(h, 0, "표 목록", sectionStyle, intStyle, dblStyle);
                cell(h, 1, "시트 이름 · 행 수", sectionStyle, intStyle, dblStyle);
                for (int i = 0; i < order.size(); i++) {
                    Row row = summary.createRow(r++);
                    cell(row, 0, order.get(i).title, null, intStyle, dblStyle);
                    cell(row, 1, sheetNames.get(i) + " · " + order.get(i).rows.size() + "행", null, intStyle, dblStyle);
                }
            }
            summary.setColumnWidth(0, 28 * 256);
            summary.setColumnWidth(1, 64 * 256);

            for (int i = 0; i < order.size(); i++) {
                Report.Table tb = order.get(i);
                Sheet sh = wb.createSheet(sheetNames.get(i));
                int cols = tb.headers.size();
                Row hr = sh.createRow(0);
                int[] w = new int[cols];
                boolean[] isP = new boolean[cols];
                for (int c = 0; c < cols; c++) {
                    String hd = tb.headers.get(c);
                    cell(hr, c, hd, head, intStyle, dblStyle);
                    w[c] = Math.max(8, len(hd) + 2);
                    isP[c] = isPValueHeader(hd);
                }
                int rn = 1;
                for (List<Object> rowData : tb.rows) {
                    Row row = sh.createRow(rn++);
                    for (int c = 0; c < rowData.size(); c++) {
                        cell(row, c, rowData.get(c), null, intStyle, c < cols && isP[c] ? pStyle : dblStyle);
                        if (c < w.length) w[c] = Math.min(60, Math.max(w[c], len(rowData.get(c)) + 2));
                    }
                }
                for (int c = 0; c < w.length; c++) sh.setColumnWidth(c, w[c] * 256);
                sh.createFreezePane(0, 1);
                if (cols > 0 && !tb.rows.isEmpty()) sh.setAutoFilter(new CellRangeAddress(0, tb.rows.size(), 0, cols - 1));
            }
            wb.setActiveSheet(0);
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            wb.write(out);
            return out.toByteArray();
        } finally {
            wb.close();
        }
    }

    /**
     * 4-2 결과 화면의 내용을 그대로: 분석 하나 = 시트 하나. 구역 제목 → 지표 → 통계표(칸 병합 유지) → 각주 순으로 위에서 아래로 쌓는다.
     * 숫자로 읽히는 칸은 숫자로 넣는다(소수 자릿수는 화면과 같게). 차트는 넣지 않는다.
     */
    private static byte[] writeScreens(Report report) throws IOException {
        XSSFWorkbook wb = new XSSFWorkbook();
        try {
            Font bold = wb.createFont();
            bold.setBold(true);
            Font title = wb.createFont();
            title.setBold(true);
            title.setFontHeightInPoints((short) 14);
            Font muted = wb.createFont();
            muted.setColor(IndexedColors.GREY_50_PERCENT.getIndex());
            Font navy = wb.createFont();
            navy.setBold(true);
            navy.setColor(IndexedColors.DARK_BLUE.getIndex());

            CellStyle titleStyle = wb.createCellStyle();
            titleStyle.setFont(title);
            CellStyle sectionStyle = wb.createCellStyle();
            sectionStyle.setFont(bold);
            sectionStyle.setBorderBottom(BorderStyle.THIN);
            CellStyle noteStyle = wb.createCellStyle();
            noteStyle.setFont(muted);
            CellStyle kpiLabel = wb.createCellStyle();
            kpiLabel.setFont(muted);
            CellStyle kpiText = wb.createCellStyle();
            kpiText.setFont(navy);
            kpiText.setAlignment(HorizontalAlignment.RIGHT);

            Set<String> used = new HashSet<String>();
            Sheet sh = null;
            int r = 0;
            int maxCols = 1;
            List<int[]> widthRows = new ArrayList<int[]>();
            int[] width = new int[16];
            boolean first = true;
            for (Report.Screen sc : report.screen) {
                if (sc.banner || sh == null) {
                    if (sh != null) finishSheet(sh, width);
                    String name = sc.banner ? sc.title : report.title;
                    sh = wb.createSheet(unique(name, used));
                    width = new int[16];
                    r = 0;
                    cellText(sh.createRow(r++), 0, sc.banner ? sc.title : report.title, titleStyle);
                    r++;
                    if (sc.banner) continue;
                }
                if (sc.title != null && !sc.title.isEmpty()) {
                    Row h = sh.createRow(r++);
                    cellText(h, 0, sc.title, sectionStyle);
                    for (int c = 1; c < 8; c++) h.createCell(c).setCellStyle(sectionStyle);
                }
                for (Report.Kpi k : sc.kpis) {
                    Row row = sh.createRow(r++);
                    cellText(row, 0, k.label, kpiLabel);
                    putValue(wb, row, 1, k.value, kpiText);
                    if (!k.caption.isEmpty()) cellText(row, 2, k.caption, noteStyle);
                    width[0] = Math.max(width[0], len(k.label) + 2);
                    width[1] = Math.max(width[1], len(k.value) + 2);
                }
                for (List<List<Report.Cell>> rows : sc.tables) r = writeGrid(wb, sh, r, rows, width);
                for (String n : sc.notes) cellText(sh.createRow(r++), 0, n, noteStyle);
                r++;   // 구역 사이 빈 줄
            }
            if (sh != null) finishSheet(sh, width);
            if (wb.getNumberOfSheets() == 0) wb.createSheet("분석 결과");
            wb.setActiveSheet(0);
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            wb.write(out);
            return out.toByteArray();
        } finally {
            wb.close();
        }
    }

    private static void finishSheet(Sheet sh, int[] width) {
        for (int c = 0; c < width.length; c++) sh.setColumnWidth(c, Math.min(Math.max(width[c], 10), 40) * 256);
    }

    /** 표 하나를 칸 병합 그대로 쓴다. 반환값은 다음에 쓸 줄 번호. */
    private static int writeGrid(XSSFWorkbook wb, Sheet sh, int r0, List<List<Report.Cell>> rows, int[] width) {
        int nRows = rows.size();
        int cols = 1;
        for (List<Report.Cell> rr : rows) { int n = 0; for (Report.Cell c : rr) n += c.colspan; cols = Math.max(cols, n); }
        cols = Math.min(cols, width.length);
        boolean[][] occ = new boolean[nRows][cols];
        CellStyle head = wb.createCellStyle();
        Font bold = wb.createFont();
        bold.setBold(true);
        head.setFont(bold);
        head.setFillForegroundColor(IndexedColors.GREY_25_PERCENT.getIndex());
        head.setFillPattern(FillPatternType.SOLID_FOREGROUND);
        head.setAlignment(HorizontalAlignment.CENTER);
        head.setVerticalAlignment(VerticalAlignment.CENTER);
        head.setBorderBottom(BorderStyle.THIN); head.setBorderTop(BorderStyle.THIN); head.setBorderLeft(BorderStyle.THIN); head.setBorderRight(BorderStyle.THIN);
        CellStyle textBody = wb.createCellStyle();
        textBody.setBorderBottom(BorderStyle.THIN); textBody.setBorderTop(BorderStyle.THIN); textBody.setBorderLeft(BorderStyle.THIN); textBody.setBorderRight(BorderStyle.THIN);
        textBody.setVerticalAlignment(VerticalAlignment.CENTER);
        for (int r = 0; r < nRows; r++) {
            Row row = sh.createRow(r0 + r);
            int col = 0;
            for (Report.Cell c : rows.get(r)) {
                while (col < cols && occ[r][col]) col++;
                if (col >= cols) break;
                int span = Math.min(c.colspan, cols - col);
                int rspan = Math.min(c.rowspan, nRows - r);
                for (int dr = 0; dr < rspan; dr++) for (int dc = 0; dc < span; dc++) occ[r + dr][col + dc] = true;
                CellStyle st = c.head ? head : textBody;
                Row target = row;
                // 병합으로 덮이는 칸에도 같은 서식을 줘서 테두리·바탕이 끊기지 않게 한다
                for (int dr = 0; dr < rspan; dr++) {
                    Row rw = dr == 0 ? row : (sh.getRow(r0 + r + dr) != null ? sh.getRow(r0 + r + dr) : sh.createRow(r0 + r + dr));
                    for (int dc = 0; dc < span; dc++) { if (dr == 0 && dc == 0) continue; Cell cc = rw.createCell(col + dc); cc.setCellStyle(st); }
                }
                if (c.head) cellText(target, col, c.text, st); else putValue(wb, target, col, c.text, st);
                if (span > 1 || rspan > 1) sh.addMergedRegion(new CellRangeAddress(r0 + r, r0 + r + rspan - 1, col, col + span - 1));
                if (span == 1) width[col] = Math.max(width[col], len(c.text) + 2);
                col += span;
            }
        }
        return r0 + nRows + 0;
    }

    private static void cellText(Row row, int col, String text, CellStyle style) {
        Cell c = row.createCell(col);
        c.setCellValue(text == null ? "" : (text.length() > MAX_CELL ? text.substring(0, MAX_CELL) : text));
        if (style != null) c.setCellStyle(style);
    }

    /** 숫자로 읽히면 숫자로(소수 자릿수는 화면 표기와 같게), 아니면 글자로 넣는다. */
    private static void putValue(XSSFWorkbook wb, Row row, int col, String text, CellStyle base) {
        String t = text == null ? "" : text.trim();
        String plain = t.replace(",", "");
        if (plain.matches("[-+\\u2212]?\\d*\\.?\\d+") && plain.length() <= 18) {
            try {
                double d = Double.parseDouble(plain.replace('\u2212', '-'));
                int dot = plain.indexOf('.');
                int dec = dot < 0 ? 0 : plain.length() - dot - 1;
                StringBuilder f = new StringBuilder(dec == 0 ? "0" : "0.");
                for (int i = 0; i < dec; i++) f.append('0');
                CellStyle st = wb.createCellStyle();
                if (base != null) st.cloneStyleFrom(base);
                st.setDataFormat(wb.createDataFormat().getFormat(f.toString()));
                st.setAlignment(HorizontalAlignment.RIGHT);
                Cell c = row.createCell(col);
                c.setCellValue(d);
                c.setCellStyle(st);
                return;
            } catch (NumberFormatException ignore) { /* 글자로 */ }
        }
        cellText(row, col, t, base);
    }

    /** 열 이름이 유의확률(p값)이면 소수 셋째 자리 서식을 쓴다. */
    private static boolean isPValueHeader(String h) {
        if (h == null) return false;
        String s = h.toLowerCase().replace(" ", "");
        return s.contains("유의확률") || s.contains("p-value") || s.contains("p값") || s.equals("p") || s.endsWith("_p") || s.contains("pvalue");
    }

    private static int len(Object v) {
        if (v == null) return 1;
        String s = String.valueOf(v);
        int n = 0;
        for (int i = 0; i < s.length(); i++) n += s.charAt(i) > 0x2E80 ? 2 : 1;   // 한글은 2배 폭
        return Math.min(n, 60);
    }

    private static void cell(Row row, int col, Object v, CellStyle style, CellStyle intStyle, CellStyle dblStyle) {
        Cell c = row.createCell(col);
        if (v == null) {
            c.setCellValue("");
        } else if (v instanceof Long || v instanceof Integer) {
            c.setCellValue(((Number) v).doubleValue());
            c.setCellStyle(style != null ? style : intStyle);
            return;
        } else if (v instanceof Number) {
            double d = ((Number) v).doubleValue();
            if (Double.isNaN(d) || Double.isInfinite(d)) c.setCellValue("");
            else c.setCellValue(d);
            c.setCellStyle(style != null ? style : dblStyle);
            return;
        } else if (v instanceof Boolean) {
            c.setCellValue((Boolean) v);
        } else {
            String s = String.valueOf(v);
            c.setCellValue(s.length() > MAX_CELL ? s.substring(0, MAX_CELL) : s);
        }
        if (style != null) c.setCellStyle(style);
    }

    /** 시트 이름: 31자 이내, 금지문자 치환, 중복 시 번호 부여 */
    private static String unique(String name, Set<String> used) {
        String base = (name == null || name.trim().isEmpty() ? "시트" : name).replaceAll("[\\\\/?*\\[\\]:]", "_").trim();
        if (base.length() > 28) base = base.substring(0, 28);
        String n = base;
        int i = 2;
        while (used.contains(n.toLowerCase())) n = base + "_" + (i++);
        used.add(n.toLowerCase());
        return n;
    }
}
