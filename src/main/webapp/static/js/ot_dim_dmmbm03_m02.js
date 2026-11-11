/* 2단계: 데이터 품질 진단 및 전처리 — GET /api/v1/datasets/{id}/profile, PreprocessingSpec 을 화면 상태로 보관 */
(function () {
  'use strict';
  var A = window.App;

  // 이상치 탐지 기법 = API OutlierMethod. threshold 는 profile/outliers 의 outlier_threshold / threshold 로 전달
  var ALGOS = [
    { id: 'iqr', name: 'IQR (사분위수 범위)', tag: '단변량', desc: '사분위수 범위 기반 비모수 탐지', label: 'IQR 배수 (k):', def: 1.5, opts: [[1.5, '1.5배 (표준 이상치)'], [2.0, '2.0배 (중간 이상치)'], [3.0, '3.0배 (극단 이상치)']], formula: 'x < Q1 − k·IQR  또는  x > Q3 + k·IQR' },
    { id: 'zscore', name: 'Z-score (표준점수)', tag: '모수적', desc: '정규분포 기준 표준점수 기반 탐지', label: '임계값 (|Z|):', def: 3.0, opts: [[2.5, '2.5 (엄격한 98.8% 기준)'], [3.0, '3.0 (표준 99.7% 기준)'], [3.5, '3.5 (극단값만 탐지)']], formula: '|x − μ| / σ > 임계값' },
    { id: 'modified_zscore', name: '수정된 Z-score (MAD)', tag: '로버스트', desc: '중앙값·중위절대편차 기반 왜곡 방지 탐지', label: '임계값 (|M_i|):', def: 3.5, opts: [[3.0, '3.0 (보수적 탐지)'], [3.5, '3.5 (Iglewicz 표준)'], [4.0, '4.0 (극단치 전용)']], formula: '0.6745·|x − 중앙값| / MAD > 임계값' },
    { id: 'grubbs', name: "Grubbs' 검정", tag: '가설검정', desc: '유의확률 기반 최대 극단치 순차 검정', label: '유의수준 (α):', def: 0.05, opts: [[0.01, 'α = 0.01 (99% 신뢰수준)'], [0.05, 'α = 0.05 (95% 신뢰수준 표준)'], [0.10, 'α = 0.10 (90% 신뢰수준)']], formula: '최대 |x − μ| / σ 가 임계값 초과' },
    { id: 'mahalanobis', name: '마할라노비스 거리', tag: '다변량 공분산', desc: '변수 간 공분산·상관관계 기반 다변량 탐지', label: '제곱거리(D²) 임계:', def: 1, opts: [[1, 'χ² 97.5% 분위수 (표준, 권장)'], [6.25, 'D² > 6.25 (거리 D > 2.5)'], [9, 'D² > 9 (거리 D > 3.0)'], [12.25, 'D² > 12.25 (거리 D > 3.5)']], formula: 'D² = (x−μ)ᵀ Σ⁻¹ (x−μ) > 임계치 (표준: 자유도=변수 수인 χ² 분포의 97.5% 분위수)' },
    { id: 'isolation_forest', name: 'Isolation Forest', tag: '트리 앙상블', desc: '의사결정나무 분할 기반 고립치 탐지', label: '고립 점수 임계치:', def: 0.60, opts: [[0.55, '0.55 (보수적 탐지)'], [0.60, '0.60 (표준 권장 임계치)'], [0.65, '0.65 (극단 고립치만)']], formula: '고립 점수 > 임계치' },
    { id: 'lof', name: 'LOF (국소 이상치 계수)', tag: '국소 밀도', desc: '이웃 밀도차 기반 국소 고립치 탐지', label: 'LOF 임계치:', def: 1.5, opts: [[1.3, '1.3 (민감 탐지)'], [1.5, '1.5 (표준 권장 기준)'], [1.8, '1.8 (극단 희박 밀도치)']], formula: 'LOF > 임계치' }
  ];
  // PreprocessingSpec 값(API) ↔ 화면 표시
  // 처음 들어오면 API 기본값과 같게: 아무것도 바꾸지 않는다 (사용자가 직접 고른 것만 적용)
  var DEFAULTS = { missing_strategy: 'none', outlier_treatment: 'keep', scaling: 'none', drop_duplicates: false };
  var STRATS = {
    missing_strategy: { title: '1. 결측치 정제', opts: [['none', '처리 안 함 (None)', '원본 유지'], ['median', '중앙값으로 대체', '왜곡 방지 권장'], ['mean', '평균값으로 대체', '정규분포형 적합'], ['mode', '최빈값으로 대체', '이산/범주형 적합'], ['drop_rows', '결측치 행 제거 (Drop)', '완전 관측치만 보존'], ['zero', '0 대체 (Zero)', '0으로 치환']] },
    outlier_treatment: { title: '2. 이상치(Outlier) 정제', opts: [['keep', '원본값 보존 (Keep)', '진단만 수행'], ['winsorize', '윈저라이징 (클리핑)', '임계 경계값 보정'], ['drop', '이상치 행 제거 (Drop)', '이상 관측치 삭제'], ['log', '로그 변환 (Log)', '스케일 완화']] },
    scaling: { title: '3. 특성 스케일링', opts: [['none', '미적용 (None)', '원시 스케일'], ['standard', '표준화 (Standard)', '평균 0, 분산 1 (ddof=0)'], ['minmax', '정규화 (MinMax)', '0~1 범위'], ['robust', '로버스트 (Robust)', 'IQR 기반 스케일']] },
    drop_duplicates: { title: '4. 중복 행 처리', opts: [[false, '유지 (Keep)', '중복 행 그대로'], [true, '중복 제거 (Drop)', '완전 동일 행 삭제']] }
  };

  if (!A.requireDataset()) return;
  // 2단계는 항상 원본 데이터셋 기준. 이미 전처리된 데이터셋으로 넘어간 뒤 다시 와도 원본(rawDatasetId)으로 진단·전처리한다.
  var dsId = A.state.rawDatasetId || A.state.datasetId;
  var ui = A.state.prepUi || {};
  // 이상치 탐지 기법은 기본 선택 없음. 사용자가 기법을 고르고 '탐지 실행' 버튼을 눌러야 /outliers 를 호출한다.
  var sel = { method: null, threshold: null };
  var active = null;   // 마지막으로 탐지를 실행한 기법 {method, threshold}
  // 전처리 규칙은 항목별 맨 위 옵션이 기본 선택. 저장된 선택이 있으면 유효한 값만 덮어쓴다.
  var pcfg = {};
  Object.keys(STRATS).forEach(function (k) {
    var saved = ui.prep && ui.prep[k];
    var valid = STRATS[k].opts.some(function (o) { return o[0] === saved; });
    pcfg[k] = valid ? saved : DEFAULTS[k];
  });
  var profile = null, dataset = null, selectedCol = null;

  function algo(id) { return ALGOS.filter(function (a) { return a.id === id; })[0] || null; }
  /* 변수별 상태: 결측과 이상치를 따로 표시한다. 이상치 상태는 서버 recommendation 을 우선하고, 비율 기준은 상수로 둔다 */
  var OUT_LOW_RATIO = 0.01;   // 이상치 비율이 이 값 미만이면 '확인 권장'
  var SKEW_LIMIT = 1;         // recommendation 이 없는 응답에서만 쓰는 |왜도| 기준
  function missStatus(mc) { return mc > 0 ? [['결측 있음', true]] : [['양호', false]]; }
  function outStatus(n, o, detected) {
    if (!detected || !o) return [];
    var lines = [], rec = o.recommendation;
    if (!(o.n_outliers > 0)) lines.push(['양호', false]);
    else if (o.ratio < OUT_LOW_RATIO) lines.push(['확인 권장', false]);
    else if (rec !== 'log') lines.push(['검토 필요', true]);
    if (o.n_outliers > 0 && rec === 'log') lines.push(['비대칭 분포 – 로그 변환 권장', false]);
    else if (rec === undefined && n && n.skewness != null && Math.abs(n.skewness) > SKEW_LIMIT && n.min != null && n.min > 0) lines.push(['비대칭 분포 – 로그 변환 권장', false]);
    return lines;
  }
  function statusHtml(lines) { return lines.map(function (j) { return '<span class="block ' + (j[1] ? 'text-warn-ink font-bold' : 'text-ink-2') + '">' + j[0] + '</span>'; }).join('') || '<span class="text-rule-3">-</span>'; }
  function outCount(o) {
    var s = A.num(o.n_outliers);
    return o.n_lower != null && o.n_upper != null ? s + ' <span class="text-xs font-normal text-ink-3">(하 ' + A.num(o.n_lower) + ' / 상 ' + A.num(o.n_upper) + ')</span>' : s;
  }
  function byCol(list) { var m = {}; (list || []).forEach(function (x) { m[x.column] = x; }); return m; }

  /** 이상치 진단·전처리 규칙의 대상 열: 역할이 numeric 인 열 중 식별자로 보이는 열(…_id, …코드, …번호)과 이진 열(role≠numeric)은 제외한다.
   *  서버는 영문 소문자 '_id' 접미사를 식별자로 추론하지 않으므로 이름 규칙을 화면에서 보완한다. 1단계 '변수 속성'에서 타입을 바꾸면 달라진다. */
  var ID_NAME = /(^|[_\s-])(id|code|no)$|코드$|번호$/i;
  function colInfo(name) { return ((dataset && dataset.columns) || []).filter(function (c) { return c.name === name; })[0] || null; }
  function isRuleTarget(n) {
    var c = colInfo(n.column);
    if (c && c.role && c.role !== 'numeric') return false;
    return !ID_NAME.test(String(n.column));
  }
  function ruleTargets() { return (profile && profile.numeric || []).filter(isRuleTarget); }
  function excludedNums() { return (profile && profile.numeric || []).filter(function (n) { return !isRuleTarget(n); }); }

  /** 결측치·이상치·스케일링 → POST /datasets/{id}/preprocess 요청 (전처리된 새 데이터셋 생성) */
  function buildPreprocessRequest() {
    var req = { missing_strategy: pcfg.missing_strategy, outlier_treatment: pcfg.outlier_treatment, scaling: pcfg.scaling };
    // 이상치 판정은 2단계에서 탐지를 실행한 기법·임계값과 맞춘다 (명세 권고). 탐지를 안 했으면 서버 기본값
    if (active) { req.outlier_method = active.method; req.outlier_threshold = Number(active.threshold); }
    var cols = ruleTargets().map(function (n) { return n.column; });
    if (cols.length) req.columns = cols;                 // 식별자·이진 열에는 규칙(결측·이상치·스케일링)을 적용하지 않는다
    return req;
  }
  function needsPreprocess() { return pcfg.missing_strategy !== 'none' || pcfg.outlier_treatment !== 'keep' || pcfg.scaling !== 'none'; }
  /** 분석 실행 시 보내는 PreprocessingSpec: 결측치·이상치·스케일링은 이미 데이터셋에 적용됐으므로 다시 하지 않고,
   *  /preprocess 에 없는 중복 행 제거와 범주형 인코딩만 여기서 지정한다. */
  function buildSpec() {
    // scaling 은 보내지 않는다(null): 서버가 기법별 기본값을 쓴다(군집·PCA 는 표준화, 그 외는 없음). 'none' 을 보내면 군집·PCA 가 원 단위로 계산된다.
    return { drop_duplicates: !!pcfg.drop_duplicates, outlier_treatment: 'keep', encoding: 'onehot' };
  }
  function persist() {
    A.saveState({ preprocessing: buildSpec(), prepUi: { outlier: active, prep: pcfg } });
  }
  function setMsg(text) {
    var m = A.$('#prep-msg');
    m.textContent = text || '';
    m.classList.toggle('hidden', !text); m.classList.toggle('flex', !!text);
  }

  /* ---------------- 알고리즘 카드 ---------------- */
  /** 이상치 탐지 기법: 같은 모양 카드 격자 대신 선택 목록. 임계값은 고른 기법에서만 보인다 */
  function renderAlgos() {
    A.$('#algo-grid').innerHTML = ALGOS.map(function (a) {
      var on = sel.method === a.id;
      return '<div data-algo="' + a.id + '" role="button" tabindex="0" aria-pressed="' + on + '" class="p-3.5 rounded-xl border text-left transition-colors cursor-pointer relative flex flex-col justify-between ' + (on ? 'border-brand bg-brand-soft' : 'border-rule hover:border-rule-3 hover:bg-paper-3 bg-white') + '">' +
        '<div><div class="flex items-center justify-between gap-1"><span class="text-body font-bold text-ink">' + A.esc(a.name) + '</span><span class="text-xs text-muted whitespace-nowrap">' + a.tag + '</span></div>' +
        '<p class="text-xs text-ink-3 mt-1.5 leading-relaxed">' + a.desc + '</p></div>' +
        '<div class="mt-3 pt-2 border-t flex items-center justify-between gap-2 text-xs ' + (on ? 'border-brand/20' : 'border-rule') + '"><span class="font-semibold ' + (on ? 'text-ink-2' : 'text-ink-3') + '">' + a.label + '</span>' +
          (on
            ? '<select data-thr="1" aria-label="' + A.esc(a.name) + ' ' + A.esc(a.label.replace(/:$/, '')) + '" class="bg-white border border-rule-3 rounded px-1.5 py-0.5 text-xs font-bold text-ink focus:outline-none focus:ring-2 focus:ring-link/30 focus:border-link">' +
              a.opts.map(function (o) { return '<option value="' + o[0] + '"' + (Number(sel.threshold) === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select>'
            // 선택하지 않은 카드: 누를 수 없는 선택창 대신 기본값을 글자로만 보여준다 (카드를 고르면 선택창으로 바뀜)
            : '<span class="text-xs text-ink-3 py-0.5">' + (a.opts.filter(function (o) { return o[0] === a.def; })[0] || a.opts[0])[1] + '</span>') + '</div></div>';
    }).join('');
    var a = algo(sel.method);
    A.$('#algo-sel-name').textContent = a ? a.name : '-';
    syncDetectBtn();
  }
  /** 탐지 실행 버튼: 데이터(프로파일) 로드가 끝나고 기법을 선택했을 때만 활성. 탐지 중에도 비활성 */
  var detecting = false;
  function syncDetectBtn() {
    var b = A.$('#btn-detect');
    b.disabled = detecting || !profile || !sel.method;
    b.title = !profile ? '데이터를 불러오는 중입니다' : !sel.method ? '위 카드에서 탐지 기법을 선택하세요' : '';
    if (detecting) return;   // 탐지 중에는 '탐지하는 중' 표시 유지
    var label = b.querySelector('span');
    if (label) label.textContent = !profile ? '데이터 불러오는 중...' : '이상치 탐지 실행';
  }

  /* ---------------- 진단 결과 ---------------- */
  /** 이상치 건수 카드 값. 마할라노비스는 모든 변수가 같은 '이상치 행 수'를 돌려주므로 합하지 않고 그대로 쓰고(행 기준),
   *  그 외 기법은 대상 변수별 건수의 합이다. */
  function totalOutliers() {
    var names = {};
    ruleTargets().forEach(function (n) { names[n.column] = true; });
    var list = (profile.outliers || []).filter(function (o) { return names[o.column]; });
    if (active && active.method === 'mahalanobis') return list.reduce(function (m, o) { return Math.max(m, o.n_outliers || 0); }, 0);
    return list.reduce(function (s, o) { return s + (o.n_outliers || 0); }, 0);
  }

  function renderQuality() {
    if (!profile) return;
    var a = active && algo(active.method);
    var outs = totalOutliers();
    A.$('#card-rows').textContent = A.num(profile.n_rows) + '행 × ' + profile.n_cols + '변수';
    var cm = A.$('#card-missing');
    cm.textContent = A.num(profile.total_missing_cells) + '건 (' + (profile.missing_ratio * 100).toFixed(1) + '%)';
    cm.className = 'text-lg font-bold font-mono mt-0.5 block ' + (profile.total_missing_cells > 0 ? 'kpi-bad' : 'kpi-ok');
    A.$('#card-out-label').textContent = a ? '이상치 검출 (' + a.name + (a.id === 'mahalanobis' ? ' · 행 기준' : ' · 변수별 합계') + ')' : '이상치 검출';
    var co = A.$('#card-outliers');
    co.textContent = a ? A.num(outs) + '건' : '탐지 전';
    co.className = 'text-lg font-bold font-mono mt-0.5 block ' + (!a ? 'kpi-idle' : outs > 0 ? 'kpi-bad' : 'kpi-ok');
    var cd = A.$('#card-dups');
    cd.textContent = A.num(profile.n_duplicated_rows) + '행';
    cd.className = 'text-lg font-bold font-mono mt-0.5 block ' + 'text-ink';
    A.$('#applied-name').textContent = a ? a.name : '미실행';
    A.$('#applied-formula').textContent = a ? a.formula : '위에서 탐지 기법을 선택하고 실행하세요';
    A.$('#th-out').textContent = a ? '이상치 (' + a.name + ')' : '이상치';

    var miss = byCol(profile.missing), outl = byCol(profile.outliers);
    var nums = ruleTargets();
    if (!selectedCol && nums.length) selectedCol = nums[0].column;
    var TD = '<td class="py-2.5 px-3 text-right">', DASH = '<span class="text-rule-3">-</span>';
    function missCell(mc) { return TD + (mc > 0 ? '<span class="text-warn-ink font-bold">' + A.num(mc) + '</span>' : '<span class="text-ink-4">0</span>') + '</td>'; }
    function rowOpen(col) { return '<tr data-col="' + A.esc(col) + '" class="cursor-pointer transition-colors ' + (col === selectedCol ? 'bg-brand-soft font-semibold' : 'hover:bg-paper-3') + '">'; }
    var NAME = '<td class="py-2.5 px-3 font-sans font-medium text-ink whitespace-nowrap">';
    A.$('#var-body').innerHTML = nums.map(function (n) {
      var mc = (miss[n.column] || {}).n_missing || n.missing || 0, o = outl[n.column];
      return rowOpen(n.column) + NAME + A.esc(n.column) + '</td>' + missCell(mc) +
        TD + (!a || !o ? DASH : o.n_outliers > 0 ? '<span class="text-warn-ink font-bold">' + outCount(o) + '</span>' : '<span class="text-ink-4">0</span>') + '</td>' +
        TD + (!a || !o ? DASH : '<span class="text-ink-2">' + A.fix((o.ratio || 0) * 100, 2) + '%</span>') + '</td>' +
        TD + (n.skewness == null ? DASH : '<span class="text-ink-2">' + A.fix(n.skewness, 2) + '</span>') + '</td>' +
        '<td class="py-2.5 px-3 font-sans text-xs">' + statusHtml(missStatus(mc)) + '</td>' +
        '<td class="py-2.5 px-3 font-sans text-xs">' + statusHtml(outStatus(n, o, !!a)) + '</td></tr>';
    }).join('') + (profile.categorical || []).map(function (c) {
      var mc = (miss[c.column] || {}).n_missing != null ? miss[c.column].n_missing : c.missing || 0;
      return rowOpen(c.column) + NAME + A.esc(c.column) + '<span class="ml-1.5 text-xs font-normal text-ink-3">범주형</span></td>' + missCell(mc) +
        TD + DASH + '</td>' + TD + DASH + '</td>' + TD + DASH + '</td>' +
        '<td class="py-2.5 px-3 font-sans text-xs">' + statusHtml(missStatus(mc)) + '</td><td class="py-2.5 px-3 font-sans text-xs">' + DASH + '</td></tr>';
    }).join('') || '<tr><td colspan="7" class="py-6 text-center text-ink-4 font-sans">표시할 변수가 없습니다.</td></tr>';
    A.$('#judge-note').textContent = '이상치 상태: 이상치 없음 → 양호, 비율 ' + (OUT_LOW_RATIO * 100) + '% 미만 → 확인 권장, 그 외 → 검토 필요. 로그 변환 권장은 서버 권고(recommendation)를 따릅니다. 이상치 상태는 탐지를 실행한 뒤에 표시됩니다.' +
      (excludedNums().length ? ' 식별자·이진 열은 진단과 전처리 대상에서 제외했습니다: ' + excludedNums().map(function (n) { return n.column; }).join(', ') + ' (1단계 변수 속성에서 타입을 바꾸면 달라집니다).' : '');
    renderDetail();
    renderAlgos();
  }

  function renderDetail() {
    var card = A.$('#detail-card');
    var n = (profile.numeric || []).filter(function (x) { return x.column === selectedCol; })[0];
    if (!n) {
      var cat = (profile.categorical || []).filter(function (x) { return x.column === selectedCol; })[0];
      if (cat) {   // 범주형 변수: 서버가 준 요약(고유값 수·최빈값·상위 값)
        var tv = (cat.top_values || []).slice(0, 8).map(function (t) { var k = Object.keys(t); return '<div class="flex items-center justify-between text-xs px-1 py-1.5 border-b border-paper-2 gap-2"><span class="text-ink-2 font-bold truncate">' + A.esc(t.value != null ? t.value : t[k[0]]) + '</span><span class="text-ink-0 font-bold">' + A.num(t.count != null ? t.count : t[k[1]]) + '건</span></div>'; }).join('');
        card.innerHTML = '<div class="sec-head flex items-center justify-between flex-wrap gap-2"><h4 class="text-title font-semibold text-ink">[' + A.esc(cat.column) + '] 범주형 변수 요약</h4></div>' +
          '<div class="sec-box space-y-3"><div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-body font-mono">' +
          [['유효 관측치', A.num(cat.count)], ['결측치', A.num(cat.missing)], ['고유값 수', A.num(cat.n_unique)], ['최빈값', A.esc(cat.mode == null ? '-' : cat.mode)]].map(function (b) { return '<div class="p-3 rounded-xl border text-left bg-paper-3 border-rule"><span class="text-ink-3 text-xs block font-sans whitespace-nowrap">' + b[0] + '</span><span class="block mt-0.5 truncate">' + b[1] + '</span></div>'; }).join('') +
          '</div>' + (tv ? '<div class="pt-2 border-t border-paper-2"><div class="text-xs font-bold text-ink-0 mb-1.5">값별 건수 (상위)</div>' + tv + '</div>' : '') + '</div>';
        return;
      }
      card.innerHTML = '<div class="text-xs text-ink-4 text-center py-6">표시할 변수가 없습니다.</div>'; return;
    }
    var o = byCol(profile.outliers)[selectedCol];
    var a = active && algo(active.method);
    function box(label, v, hi) { return '<div class="p-3 rounded-xl border text-left ' + (hi ? 'bg-brand-soft border-brand/40' : 'bg-paper-3 border-rule') + '"><span class="' + (hi ? 'text-brand font-semibold' : 'text-ink-3') + ' text-xs block font-sans whitespace-nowrap">' + label + '</span><strong class="text-ink text-[15px]">' + A.fix(v, 2) + '</strong></div>'; }
    var bounds = a && o && (o.lower_bound !== null && o.lower_bound !== undefined || o.upper_bound !== null && o.upper_bound !== undefined) ? '하한: ' + A.fix(o.lower_bound, 2) + ' | 상한: ' + A.fix(o.upper_bound, 2) : '평균: ' + A.fix(n.mean, 2) + ' | 표준편차: ±' + A.fix(n.std, 2);
    var samples = '';
    if (a && o && o.n_outliers > 0) {
      var idx = o.sample_indices || [], vals = o.sample_values || [];
      samples = '<div class="pt-2 border-t border-paper-2"><div class="text-xs font-bold text-ink-0 mb-1.5 flex items-center justify-between"><span>검출된 이상치 표본 (' + A.num(o.n_outliers) + '건, ' + (o.ratio * 100).toFixed(1) + '%' + (o.n_outliers > idx.length ? ', 상위 ' + idx.length + '건 표시' : '') + ')</span><span class="text-xs font-normal text-ink-4">탐지 기준: ' + A.esc(a.name) + '</span></div><div class="max-h-36 overflow-y-auto space-y-1">' +
        idx.slice(0, 20).map(function (ri, i) { return '<div class="flex items-center justify-between text-xs px-1 py-1.5 border-b border-paper-2 gap-2"><span class="text-ink-2 font-bold shrink-0">#' + ri + '행</span><span class="text-ink-0 font-bold">관측값: ' + A.esc(vals[i]) + '</span></div>'; }).join('') + '</div></div>';
    }
    if (!a) samples = '<div class="pt-2 border-t border-paper-2 text-xs text-ink-4">이상치 분포는 위에서 탐지 기법을 선택하고 탐지를 실행하면 표시됩니다.</div>';
    card.innerHTML = '<div class="sec-head flex items-center justify-between flex-wrap gap-2"><h4 class="text-title font-semibold text-ink">[' + A.esc(n.column) + '] 통계 지표' + (a ? ' 및 이상치 분포' : '') + '</h4><span class="text-xs text-ink-3 font-mono">' + bounds + '</span></div>' +
      '<div class="sec-box space-y-3"><div class="grid grid-cols-2 sm:grid-cols-5 gap-3 text-body font-mono">' + box('최솟값', n.min) + box('1사분위(Q1)', n.q1) + box('중앙값', n.median, true) + box('3사분위(Q3)', n.q3) + box('최댓값', n.max) + '</div>' + samples + '</div>';
  }

  /* ---------------- 전처리 전략 ---------------- */
  function renderStrategies() {
    A.$('#strategy-grid').innerHTML = Object.keys(STRATS).map(function (k) {
      var g = STRATS[k];
      return '<div class="p-4 rounded-xl border border-rule bg-paper-3 space-y-2.5"><span class="text-body font-bold text-ink block pb-2 border-b border-rule">' + g.title + '</span><div class="space-y-1">' +
        g.opts.map(function (o) {
          var on = pcfg[k] === o[0];
          return '<label class="flex items-center justify-between gap-2 px-2.5 py-2 rounded-lg border text-body cursor-pointer transition-colors ' + (on ? 'bg-white border-brand font-semibold text-brand' : 'border-transparent text-ink-2 hover:bg-white') + '">' +
            '<div class="flex items-center gap-2 min-w-0"><input type="radio" name="' + k + '" value="' + o[0] + '" ' + (on ? 'checked' : '') + ' class="text-blue-600 focus:ring-blue-600"><span class="whitespace-nowrap">' + o[1] + '</span></div><span class="text-xs text-ink-3 font-normal text-right">' + o[2] + '</span></label>';
        }).join('') + '</div></div>';
    }).join('');
  }

  /** 진입 시: 이상치 탐지 없이 기본 품질 프로파일만 조회 */
  function loadProfile() {
    return A.get('/api/v1/datasets/' + encodeURIComponent(dsId) + '/profile' + A.qs({ include_outliers: false })).then(function (p) {
      profile = p;
      renderQuality();
      persist();
    });
  }
  /** '탐지 실행' 버튼: 선택한 기법·임계값으로 이상치 탐지 */
  function runDetect() {
    var req = { method: sel.method, threshold: sel.threshold };
    return A.get('/api/v1/datasets/' + encodeURIComponent(dsId) + '/outliers' + A.qs(req)).then(function (list) {
      profile.outliers = list || [];
      active = req;
      renderQuality();
      persist();
      syncNextBtn();
    });
  }
  /** 3단계 진행 버튼: 이상치 탐지를 실행해 정상 응답을 받은 뒤(active 확정)에만 활성 */
  var proceeding = false;
  function syncNextBtn() {
    var b = A.$('#btn-next'), ready = !!active;
    b.disabled = proceeding || !ready;
    b.title = ready ? '' : '먼저 이상치 탐지를 실행하세요';
    A.$('#next-hint').classList.toggle('hidden', ready);
  }

  document.addEventListener('DOMContentLoaded', function () {
    renderAlgos();
    renderStrategies();
    syncNextBtn();
    // 상단 단계 표시줄로 3·4단계에 바로 건너뛰는 것은 이상치 탐지 후에만 가능하다. 5단계(결과 관리)는 탐지와 상관없이 이동할 수 있다
    document.addEventListener('click', function (e) {
      var a = e.target.closest('a[href]');
      if (!a || active) return;
      if (!/\/analysis\/step[34](\/|$|\?)/.test(a.getAttribute('href') || '')) return;
      e.preventDefault();
      A.fail('이상치 탐지 완료 후 다음 단계로 이동할 수 있습니다.');
    });
    A.$('#algo-grid').addEventListener('click', function (e) {
      if (e.target.closest('select')) return;
      var c = e.target.closest('[data-algo]');
      if (!c) return;
      var a = algo(c.getAttribute('data-algo'));
      if (sel.method !== a.id) { sel.method = a.id; sel.threshold = a.def; }
      renderAlgos();
      A.icons();
    });
    A.$('#algo-grid').addEventListener('change', function (e) {
      if (e.target.closest('select[data-thr]')) sel.threshold = Number(e.target.value);
    });
    A.$('#btn-detect').addEventListener('click', function () {
      var b = this;
      if (!profile || !sel.method || detecting) return;
      detecting = true; syncDetectBtn();
      b.innerHTML = '<span class="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full spin inline-block"></span><span>알고리즘 연산 중...</span>';
      var card = b.closest('.card-modern') || b;
      runDetect().then(function () {
        A.fail(null, card);
        A.toast('이상치 탐지가 완료되었습니다.');
      }).catch(function (e) { if (!A.datasetGone(e)) A.fail(e.message, card); }).then(function () {
        detecting = false; syncDetectBtn();
        b.innerHTML = '<span>이상치 탐지 실행</span>';
        A.icons();
      });
    });
    A.$('#var-body').addEventListener('click', function (e) {
      var tr = e.target.closest('tr[data-col]');
      if (!tr) return;
      selectedCol = tr.getAttribute('data-col');
      renderQuality();
    });
    A.$('#strategy-grid').addEventListener('change', function (e) {
      var r = e.target;
      if (r.type !== 'radio') return;
      pcfg[r.name] = r.value === 'true' ? true : r.value === 'false' ? false : r.value;
      renderStrategies();
      persist();
    });
    A.$('#btn-next').addEventListener('click', function () {
      var b = this, label = b.querySelector('span');
      if (!active) return;   // 탐지 응답을 받기 전에는 진행하지 않는다
      persist();
      setMsg('');
      if (!needsPreprocess()) {   // 적용할 규칙이 없으면 원본 그대로 진행
        A.saveState({ datasetId: dsId, datasetName: dataset && dataset.name, datasetRows: dataset && dataset.n_rows, rawDatasetId: dsId, analysisId: null });
        location.href = A.ctx + '/analysis/step3';
        return;
      }
      proceeding = true; syncNextBtn();
      label.textContent = '전처리 적용 중...';
      // 원본은 그대로 두고 전처리된 새 데이터셋(source_type=preprocessed)을 만든다. 이후 3·4단계는 이 데이터셋으로 진행
      A.post('/api/v1/datasets/' + encodeURIComponent(dsId) + '/preprocess', buildPreprocessRequest()).then(function (d) {
        A.saveState({ datasetId: d.id, datasetName: d.name, datasetRows: d.n_rows, rawDatasetId: dsId, analysisId: null });
        location.href = A.ctx + '/analysis/step3';
      }).catch(function (err) {
        if (A.datasetGone(err)) return;
        setMsg('전처리 적용에 실패했습니다: ' + err.message);
        proceeding = false; syncNextBtn();
        label.textContent = '3단계 데이터 탐색(EDA) 진행';
      });
    });

    A.get('/api/v1/datasets/' + encodeURIComponent(dsId)).then(function (d) {
      dataset = d;
      return loadProfile();
    }).then(function () { A.icons(); }).catch(function (e) { if (!A.datasetGone(e)) A.fail(e.message); });
    A.icons();
  });
})();
