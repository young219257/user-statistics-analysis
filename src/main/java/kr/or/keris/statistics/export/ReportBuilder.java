package kr.or.keris.statistics.export;

import com.fasterxml.jackson.databind.JsonNode;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;

/** API 응답(JSON)을 Report 로 변환. metrics/result/chart_data 는 구조가 가변이라 스칼라는 키-값, 객체 배열은 표로 옮긴다. */
public final class ReportBuilder {
    private ReportBuilder() { }

    private static final Map<String, String> LABELS = new HashMap<String, String>();
    static {
        String[][] l = {
            {"r2", "R²"}, {"r_squared", "R²"}, {"adj_r2", "수정 R²"}, {"adj_r_squared", "수정 R²"}, {"rmse", "RMSE"}, {"mae", "MAE"}, {"mse", "MSE"},
            {"accuracy", "정확도"}, {"precision", "정밀도"}, {"recall", "재현율"}, {"f1", "F1"}, {"f1_score", "F1"}, {"auc", "AUC"}, {"roc_auc", "ROC-AUC"},
            {"n_samples", "표본 수"}, {"n_obs", "관측치 수"}, {"n_features", "변수 수"}, {"n_clusters", "군집 수"}, {"aic", "AIC"}, {"bic", "BIC"},
            {"p_value", "p-value"}, {"f_statistic", "F-통계량"}, {"silhouette", "실루엣"}, {"silhouette_score", "실루엣"}, {"inertia", "군집내 제곱합"},
            {"coefficients", "회귀계수"}, {"intercept", "절편"}, {"feature_importance", "변수 중요도"}, {"target", "종속변수"}, {"features", "독립변수"},
            {"missing_strategy", "결측 처리"}, {"outlier_treatment", "이상치 처리"}, {"outlier_method", "이상치 탐지 기법"}, {"outlier_threshold", "이상치 임계값"},
            {"scaling", "스케일링"}, {"encoding", "인코딩"}, {"drop_duplicates", "중복 제거"}, {"test_size", "검증 비율"}, {"random_state", "난수 시드"}
        };
        for (String[] p : l) LABELS.put(p[0], p[1]);
    }

    static String label(String key) {
        String v = LABELS.get(key);
        return v != null ? v : key.replace('_', ' ');
    }

    /** JSON 스칼라 → Java 값 (null 유지) */
    static Object scalar(JsonNode n) {
        if (n == null || n.isNull() || n.isMissingNode()) return null;
        if (n.isBoolean()) return n.booleanValue();
        if (n.isIntegralNumber()) return n.longValue();
        if (n.isNumber()) return n.doubleValue();
        return n.asText();
    }

    static boolean isScalar(JsonNode n) {
        return n == null || n.isValueNode();
    }

    static boolean isObjectArray(JsonNode n) {
        if (n == null || !n.isArray() || n.size() == 0) return false;
        for (JsonNode x : n) if (!x.isObject()) return false;
        return true;
    }

    static boolean isMatrix(JsonNode n) {
        if (n == null || !n.isArray() || n.size() == 0) return false;
        for (JsonNode r : n) {
            if (!r.isArray() || r.size() == 0) return false;
            for (JsonNode c : r) if (!c.isNumber() && !c.isNull()) return false;
        }
        return true;
    }

    static boolean isScalarArray(JsonNode n) {
        if (n == null || !n.isArray()) return false;
        for (JsonNode x : n) if (!x.isValueNode()) return false;
        return true;
    }

    /** 스칼라/스칼라 배열을 {라벨, 값} 목록으로 평탄화 (중첩 객체는 경로로 연결) */
    static void flatten(String prefix, JsonNode node, List<Object[]> out, int depth) {
        if (node == null || depth > 4) return;
        if (node.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> it = node.fields();
            while (it.hasNext()) {
                Map.Entry<String, JsonNode> e = it.next();
                String key = prefix.isEmpty() ? label(e.getKey()) : prefix + " · " + label(e.getKey());
                JsonNode v = e.getValue();
                if (v.isNull()) continue;
                if (v.isValueNode()) out.add(new Object[]{key, scalar(v)});
                else if (isScalarArray(v)) out.add(new Object[]{key, join(v, 30)});
                else if (v.isObject()) flatten(key, v, out, depth + 1);
            }
        }
    }

    static String join(JsonNode arr, int max) {
        StringBuilder sb = new StringBuilder();
        int i = 0;
        for (JsonNode x : arr) {
            if (i > 0) sb.append(", ");
            if (i >= max) { sb.append("… (총 ").append(arr.size()).append("개)"); break; }
            sb.append(x.asText());
            i++;
        }
        return sb.toString();
    }

    /** 객체 배열/행렬을 표로 수집 (중첩 구조는 재귀) */
    static void collectTables(String title, JsonNode node, List<Report.Table> out, boolean excelOnly, int depth) {
        if (node == null || depth > 4 || out.size() > 60) return;
        if (isObjectArray(node)) {
            Set<String> cols = new LinkedHashSet<String>();
            int probe = Math.min(node.size(), 50);
            for (int i = 0; i < probe; i++) {
                Iterator<String> names = node.get(i).fieldNames();
                while (names.hasNext()) cols.add(names.next());
            }
            Report.Table t = new Report.Table(title);
            t.excelOnly = excelOnly;
            for (String c : cols) t.headers.add(label(c));
            int max = Math.min(node.size(), 20000);
            for (int i = 0; i < max; i++) {
                List<Object> row = new ArrayList<Object>();
                for (String c : cols) {
                    JsonNode v = node.get(i).get(c);
                    if (v == null || v.isNull()) row.add(null);
                    else if (v.isValueNode()) row.add(scalar(v));
                    else row.add(v.toString().length() > 200 ? v.toString().substring(0, 200) + "…" : v.toString());
                }
                t.rows.add(row);
            }
            out.add(t);
        } else if (isMatrix(node)) {
            Report.Table t = new Report.Table(title);
            t.excelOnly = excelOnly;
            int width = node.get(0).size();
            for (int j = 0; j < width; j++) t.headers.add(String.valueOf(j + 1));
            for (JsonNode r : node) {
                List<Object> row = new ArrayList<Object>();
                for (JsonNode c : r) row.add(scalar(c));
                t.rows.add(row);
            }
            out.add(t);
        } else if (node.isObject()) {
            Iterator<Map.Entry<String, JsonNode>> it = node.fields();
            while (it.hasNext()) {
                Map.Entry<String, JsonNode> e = it.next();
                JsonNode v = e.getValue();
                if (v.isValueNode() || isScalarArray(v)) continue;
                collectTables(title + " · " + label(e.getKey()), v, out, excelOnly, depth + 1);
            }
        }
    }

    static String statusLabel(String status) {
        if (status == null) return null;
        if ("succeeded".equals(status)) return "성공";
        if ("failed".equals(status)) return "실패";
        if ("running".equals(status)) return "실행 중";
        if ("pending".equals(status)) return "대기";
        if ("cancelled".equals(status)) return "취소";
        return status;
    }

    private static String text(JsonNode n, String field) {
        JsonNode v = n == null ? null : n.get(field);
        return v == null || v.isNull() ? null : v.asText();
    }

    /**
     * 분석 1건 → 섹션들. prefix 는 패키지 내보내기에서 분석을 구분하기 위한 접두어(예: "A1 ").
     * dataset / rawPreview 는 없어도 된다.
     */
    public static void addAnalysis(Report r, String prefix, JsonNode a, JsonNode dataset, JsonNode rawPreview, List<Report.Img> images) {
        JsonNode metrics = a.get("metrics");
        if (metrics != null && metrics.size() > 0) {
            Report.Section s = r.section(prefix + "핵심 지표");
            List<Object[]> kv = new ArrayList<Object[]>();
            flatten("", metrics, kv, 0);
            s.kv.addAll(kv);
            collectTables(prefix + "지표", metrics, s.tables, false, 0);
        }

        JsonNode result = a.get("result");
        if (result != null && result.size() > 0) {
            Report.Section s = r.section(prefix + "표준 통계 결과표");
            List<Object[]> rk = new ArrayList<Object[]>();
            flatten("", result, rk, 0);
            s.kv.addAll(rk);
            collectTables(prefix + "결과", result, s.tables, false, 0);
        }

        JsonNode recs = a.get("chart_recommendations");
        if (recs != null && recs.size() > 0) {
            Report.Section s = r.section(prefix + "진단 시각화 차트");
            if (images != null) s.images.addAll(images);
        }

        JsonNode cd = a.get("chart_data");
        if (cd != null && cd.size() > 0) {
            Report.Section s = r.section(prefix + "차트 원본 데이터");
            collectTables(prefix + "차트", cd, s.tables, true, 0);
            if (s.tables.isEmpty()) r.sections.remove(s);
        }

        if (rawPreview != null && rawPreview.has("rows")) {
            Report.Section s = r.section(prefix + "표본별 원시데이터 및 잔차");
            Report.Table t = new Report.Table(prefix + "원시데이터(상위 " + rawPreview.get("rows").size() + "행)");
            t.excelOnly = true;
            JsonNode cols = rawPreview.get("columns");
            List<String> names = new ArrayList<String>();
            if (cols != null) for (JsonNode c : cols) { names.add(c.asText()); t.headers.add(c.asText()); }
            for (JsonNode row : rawPreview.get("rows")) {
                List<Object> cells = new ArrayList<Object>();
                for (String n : names) cells.add(scalar(row.get(n)));
                t.rows.add(cells);
            }
            s.tables.add(t);
        }
    }

    /** 4-2 화면에서 모아 보낸 구역(표·지표·각주)과 차트 이미지를 Report 로 옮긴다. */
    public static Report fromScreen(JsonNode scr, String fallbackTitle) {
        Report r = new Report();
        r.title = text(scr, "title") != null && !text(scr, "title").isEmpty() ? text(scr, "title") : fallbackTitle;
        r.subtitle = "분석 결과";
        addScreen(r, scr, false);
        return r;
    }

    /** 분석 패키지: 담긴 분석마다 4-2 화면 내용을 이어 붙인다. */
    public static Report fromScreens(JsonNode screens, String packageTitle) {
        Report r = new Report();
        r.title = packageTitle;
        r.subtitle = "분석 결과";
        int i = 0;
        if (screens != null) for (JsonNode scr : screens) {
            i++;
            addScreen(r, scr, screens.size() > 1 || i > 1);
        }
        return r;
    }

    private static void addScreen(Report r, JsonNode scr, boolean banner) {
        if (banner) {
            Report.Screen b = new Report.Screen(nz(text(scr, "title")));
            b.banner = true;
            r.screen.add(b);
        }
        JsonNode secs = scr.get("sections");
        if (secs != null) for (JsonNode s : secs) {
            Report.Screen sc = new Report.Screen(text(s, "title") == null ? "" : text(s, "title"));
            JsonNode kp = s.get("kpis");
            if (kp != null) for (JsonNode k : kp) sc.kpis.add(new Report.Kpi(nz(text(k, "label")), nz(text(k, "value")), nz(text(k, "caption"))));
            JsonNode tbs = s.get("tables");
            if (tbs != null) for (JsonNode t : tbs) {
                List<List<Report.Cell>> rows = new ArrayList<List<Report.Cell>>();
                for (JsonNode row : t) {
                    List<Report.Cell> cells = new ArrayList<Report.Cell>();
                    for (JsonNode c : row) {
                        cells.add(new Report.Cell(nz(text(c, "t")), c.path("h").asBoolean(false), c.path("cs").asInt(1), c.path("rs").asInt(1)));
                    }
                    if (!cells.isEmpty()) rows.add(cells);
                    if (rows.size() >= 400) break;
                }
                if (!rows.isEmpty()) sc.tables.add(rows);
            }
            JsonNode nt = s.get("notes");
            if (nt != null) for (JsonNode n : nt) sc.notes.add(n.asText());
            r.screen.add(sc);
        }
        JsonNode imgs = scr.get("images");
        if (imgs != null && imgs.size() > 0) {
            Report.Screen figs = new Report.Screen("");
            for (JsonNode im : imgs) {
                String data = nz(text(im, "data"));
                int comma = data.indexOf(',');
                if (!data.startsWith("data:image/") || comma < 0) continue;
                try {
                    byte[] png = org.springframework.util.Base64Utils.decodeFromString(data.substring(comma + 1));
                    figs.figures.add(new Report.Figure(nz(text(im, "rank")), nz(text(im, "title")), nz(text(im, "subtitle")), png));
                } catch (IllegalArgumentException ignore) { /* 깨진 이미지는 건너뛴다 */ }
                if (figs.figures.size() >= 30) break;
            }
            if (!figs.figures.isEmpty()) r.screen.add(figs);
        }
    }

    private static String nz(String s) {
        return s == null ? "" : s;
    }

    public static Report forAnalysis(JsonNode a, JsonNode dataset, JsonNode rawPreview, List<Report.Img> images) {
        Report r = new Report();
        r.title = text(a, "name");
        r.subtitle = "분석 결과";
        addAnalysis(r, "", a, dataset, rawPreview, images);
        return r;
    }

    public static Report forPackage(JsonNode pkg, List<JsonNode> analyses, List<JsonNode> datasets) {
        Report r = new Report();
        r.title = text(pkg, "name");
        r.subtitle = "분석 결과";
        for (int i = 0; i < analyses.size(); i++) {
            addAnalysis(r, "A" + (i + 1) + " ", analyses.get(i), i < datasets.size() ? datasets.get(i) : null, null, null);
        }
        return r;
    }
}
