package kr.or.keris.statistics.export;

import java.util.ArrayList;
import java.util.List;

/** PDF / Excel 공통 문서 모델 (섹션 = 키-값 목록 + 표 + 이미지) */
public class Report {
    public String title;
    public String subtitle;
    public final List<Section> sections = new ArrayList<Section>();

    public Section section(String title) {
        Section s = new Section(title);
        sections.add(s);
        return s;
    }

    /** 4-2 리포트 화면에서 그대로 옮겨 온 구역들(화면형). 비어 있으면 sections 로 그린다. */
    public final List<Screen> screen = new ArrayList<Screen>();

    public static class Cell {
        public final String text;
        public final boolean head;
        public final int colspan, rowspan;

        public Cell(String text, boolean head, int colspan, int rowspan) {
            this.text = text;
            this.head = head;
            this.colspan = Math.max(1, colspan);
            this.rowspan = Math.max(1, rowspan);
        }
    }

    public static class Kpi {
        public final String label, value, caption;

        public Kpi(String label, String value, String caption) {
            this.label = label;
            this.value = value;
            this.caption = caption;
        }
    }

    public static class Screen {
        public final String title;
        public final List<Kpi> kpis = new ArrayList<Kpi>();
        public final List<List<List<Cell>>> tables = new ArrayList<List<List<Cell>>>();
        public final List<String> notes = new ArrayList<String>();
        public final List<Figure> figures = new ArrayList<Figure>();
        /** true 면 분석 하나의 시작을 알리는 큰 제목(패키지에 분석이 여러 개일 때) */
        public boolean banner;

        public Screen(String title) {
            this.title = title;
        }
    }

    public static class Figure {
        public final String rank, title, subtitle;
        public final byte[] png;

        public Figure(String rank, String title, String subtitle, byte[] png) {
            this.rank = rank;
            this.title = title;
            this.subtitle = subtitle;
            this.png = png;
        }
    }

    public final List<Figure> figures = new ArrayList<Figure>();

    public static class Section {
        public final String title;
        public final List<Object[]> kv = new ArrayList<Object[]>();      // {라벨, 값}
        public final List<Table> tables = new ArrayList<Table>();
        public final List<Img> images = new ArrayList<Img>();            // PDF 전용

        Section(String title) {
            this.title = title;
        }

        public Section put(String label, Object value) {
            kv.add(new Object[]{label, value});
            return this;
        }
    }

    public static class Table {
        public final String title;
        public final List<String> headers = new ArrayList<String>();
        public final List<List<Object>> rows = new ArrayList<List<Object>>();
        /** true 면 Excel 에만 넣는다 (차트 원본 데이터·원시데이터처럼 PDF 에는 너무 큰 표) */
        public boolean excelOnly;

        public Table(String title) {
            this.title = title;
        }
    }

    public static class Img {
        public final String title;
        public final byte[] png;

        public Img(String title, byte[] png) {
            this.title = title;
            this.png = png;
        }
    }
}
