/* 4-1단계: 통계 모형 설정 및 실행 — POST /api/v1/analyses, GET /api/v1/analyses */
(function () {
  'use strict';
  var A = window.App;
  if (!A.requireDataset()) return;
  var dsId = A.state.datasetId;

  /* API AnalysisMethod 14종. fields = AnalysisParams 중 화면에 노출할 항목 */
  var METHODS = [
    { id: 'correlation', name: '상관분석', en: 'Correlation', cat: '기초', icon: 'network', desc: '변수 간 상관계수 행렬', target: false, feat: '투입 변수', fields: ['correlation_method'] },
    { id: 'linear_regression', name: '선형회귀', en: 'Linear Regression', cat: '예측', icon: 'trending-up', desc: '연속형 종속변수 예측', target: true, feat: '독립변수', fields: ['weight_column', 'test_size', 'fit_intercept'] },
    { id: 'logistic_regression', name: '로지스틱 회귀', en: 'Logistic Regression', cat: '예측', icon: 'git-branch', desc: '이진 범주 확률 예측', target: true, feat: '독립변수', fields: ['positive_label', 'weight_column', 'test_size', 'max_iter'] },
    { id: 'decision_tree_regressor', name: '의사결정나무(회귀)', en: 'Decision Tree Regressor', cat: '예측', icon: 'git-branch', desc: '규칙 기반 연속형 예측', target: true, feat: '독립변수', fields: ['max_depth', 'min_samples_leaf', 'ccp_alpha', 'test_size'] },
    { id: 'decision_tree_classifier', name: '의사결정나무(분류)', en: 'Decision Tree Classifier', cat: '예측', icon: 'git-branch', desc: '규칙 기반 범주 분류', target: true, feat: '독립변수', fields: ['positive_label', 'max_depth', 'min_samples_leaf', 'ccp_alpha', 'test_size'] },
    { id: 'kmeans', name: 'K-평균 군집', en: 'K-Means', cat: '군집', icon: 'pie-chart', desc: '유사 관측치 K개 군집화', target: false, feat: '투입 변수', fields: ['n_clusters', 'auto_k', 'label_columns'] },
    { id: 'hierarchical', name: '계층적 군집', en: 'Hierarchical', cat: '군집', icon: 'network', desc: '덴드로그램 기반 군집', target: false, feat: '투입 변수', fields: ['n_clusters', 'linkage', 'label_columns'] },
    { id: 'dbscan', name: 'DBSCAN', en: 'DBSCAN', cat: '군집', icon: 'pie-chart', desc: '밀도 기반 군집·노이즈 탐지', target: false, feat: '투입 변수', fields: ['eps', 'min_samples', 'label_columns'] },
    { id: 'pca', name: '주성분분석', en: 'PCA', cat: '기초', icon: 'layers', desc: '차원 축소·요인 구조 파악', target: false, feat: '투입 변수', fields: ['n_components'] },
    { id: 'anova', name: '분산분석 (ANOVA/ANCOVA)', en: 'ANOVA', cat: '고급', icon: 'award', desc: '집단 간 평균 차이 검정', target: true, feat: '추가 독립변수 (선택)', fields: ['factors', 'covariates', 'include_interaction'], featOptional: true },
    { id: 'multilevel', name: '다층모형 (HLM)', en: 'Multilevel', cat: '고급', icon: 'layers', desc: '집단 내 위계 구조 반영 회귀', target: true, feat: '고정효과 변수 (선택)', fields: ['group_column', 'random_slope'], featOptional: true },
    { id: 'growth_curve', name: '성장곡선모형', en: 'Growth Curve', cat: '고급', icon: 'trending-up', desc: '시간에 따른 변화 궤적', target: true, feat: '추가 독립변수 (선택)', fields: ['time_column', 'group_column', 'random_slope'], featOptional: true },
    { id: 'psm', name: '성향점수매칭 (PSM)', en: 'Propensity Score Matching', cat: '고급', icon: 'award', desc: '처치 효과 추정을 위한 매칭', target: true, feat: '공변량 (Covariates / X)', fields: ['treatment_column', 'caliper', 'n_neighbors'] }
  ];
  var FIELDS = {
    test_size: { t: 'select', label: '검증(홀드아웃) 비율', def: 0, num: true, opts: [[0, '사용 안 함 (전체 적합)'], [0.2, '20%'], [0.3, '30%']] },
    fit_intercept: { t: 'check', label: '절편 포함', def: true },
    positive_label: { t: 'text', label: '양성(1) 클래스 값 (선택)', ph: '예: 1 / Y / 합격' },
    weight_column: { t: 'col', label: '가중치 변수 (선택)', from: 'numeric' },
    max_iter: { t: 'select', label: '최대 반복 횟수', def: 200, num: true, opts: [[100, '100'], [200, '200 (기본)'], [500, '500'], [1000, '1000']] },
    max_depth: { t: 'select', label: '최대 트리 깊이', def: 3, num: true, opts: [['', '제한 없음'], [2, '2단계'], [3, '3단계'], [4, '4단계'], [5, '5단계'], [8, '8단계']] },
    min_samples_leaf: { t: 'select', label: '리프 최소 표본 수', def: 1, num: true, opts: [[1, '1'], [5, '5'], [10, '10'], [20, '20']] },
    ccp_alpha: { t: 'select', label: '가지치기 강도 (ccp_alpha)', def: 0, num: true, opts: [[0, '0 (없음)'], [0.001, '0.001'], [0.01, '0.01'], [0.05, '0.05']] },
    n_clusters: { t: 'select', label: '군집 수 (K)', def: 3, num: true, opts: [[2, '2개'], [3, '3개'], [4, '4개'], [5, '5개'], [6, '6개'], [8, '8개']] },
    auto_k: { t: 'check', label: '군집 수 자동 탐색 (엘보/실루엣, K=2~8)', def: false },
    linkage: { t: 'select', label: '연결법 (linkage)', def: 'ward', opts: [['ward', 'Ward'], ['complete', 'Complete'], ['average', 'Average'], ['single', 'Single']] },
    eps: { t: 'select', label: '반경 (eps)', def: 0.5, num: true, opts: [[0.3, '0.3'], [0.5, '0.5'], [0.8, '0.8'], [1, '1.0'], [1.5, '1.5']] },
    min_samples: { t: 'select', label: '최소 이웃 수 (min_samples)', def: 5, num: true, opts: [[3, '3'], [5, '5'], [10, '10'], [20, '20']] },
    n_components: { t: 'select', label: '추출 성분 수', def: 2, num: true, opts: [[1, '1'], [2, '2'], [3, '3'], [4, '4'], [5, '5'], [6, '6']] },
    correlation_method: { t: 'select', label: '상관계수 방법', def: 'pearson', opts: [['pearson', 'Pearson'], ['spearman', 'Spearman'], ['kendall', 'Kendall']] },
    factors: { t: 'cols', label: '요인 (범주형 독립변수)', from: 'any' },
    covariates: { t: 'cols', label: '공변량 (ANCOVA, 선택)', from: 'numeric' },
    include_interaction: { t: 'check', label: '상호작용 항 포함', def: true },
    group_column: { t: 'col', label: '집단(상위 수준) 변수', from: 'any', required: true },
    time_column: { t: 'col', label: '시간 변수', from: 'numeric', required: true },
    random_slope: { t: 'check', label: '랜덤 기울기 포함', def: false },
    treatment_column: { t: 'col', label: '처치(0/1) 변수', from: 'binary', required: true },
    caliper: { t: 'select', label: '캘리퍼 (매칭 허용 거리)', def: '', num: true, opts: [['', '제한 없음'], [0.05, '0.05'], [0.1, '0.1'], [0.2, '0.2']] },
    n_neighbors: { t: 'select', label: '매칭 이웃 수', def: 1, num: true, opts: [[1, '1:1'], [2, '1:2'], [3, '1:3'], [5, '1:5']] },
    label_columns: { t: 'cols', label: '식별자 변수 (원시데이터 표시용, 선택)', from: 'any' }
  };

  var dataset = null, methods = METHODS, analysis = null, running = false;
  var cfg = Object.assign({ method: 'linear_regression', target: '', features: [], params: {} }, A.state.config || {});

  function meta(id) { return methods.filter(function (m) { return m.id === id; })[0] || methods[0]; }
  function cols() { return dataset ? dataset.columns || [] : []; }
  function numericCols() { return cols().filter(function (c) { return c.role === 'numeric' || c.role === 'boolean'; }); }
  function anyCols() { return cols().filter(function (c) { return c.role !== 'constant'; }); }
  /** 독립변수 후보: 범주형도 선택할 수 있는 기법(서버가 원-핫 인코딩으로 처리)은 범주형 변수를 함께 보여 준다 */
  var CAT_FEAT = { linear_regression: 1, logistic_regression: 1, decision_tree_regressor: 1, decision_tree_classifier: 1, multilevel: 1,
    correlation: 1, kmeans: 1, hierarchical: 1, dbscan: 1, pca: 1, anova: 1, growth_curve: 1, psm: 1 };   // 모든 기법에서 범주형 독립변수 허용
  function featCols(exceptTarget) {
    var m = meta(cfg.method);
    var list = CAT_FEAT[cfg.method] ? cols().filter(function (c) { return c.role === 'numeric' || c.role === 'boolean' || c.role === 'categorical'; }) : numericCols();
    return list.filter(function (c) { return !exceptTarget || !m.target || c.name !== cfg.target; });
  }
  /** 처치 변수 후보: boolean 열과 고유값이 정확히 2개인 수치형 열 */
  function binaryCols() { return cols().filter(function (c) { return c.role === 'boolean' || (c.role === 'numeric' && c.n_unique === 2); }); }
  function pool(kind) { return kind === 'numeric' ? numericCols() : kind === 'binary' ? binaryCols() : anyCols(); }

  function pv(key) { return cfg.params[key] !== undefined ? cfg.params[key] : FIELDS[key].def; }

  /* ---------------- 기법 선택 ---------------- */
  function renderMethods() {
    A.$('#method-grid').innerHTML = methods.map(function (m) {
      var on = cfg.method === m.id;
      return '<button type="button" data-method="' + m.id + '" data-cat="' + A.esc(m.cat) + '" aria-pressed="' + on + '" class="p-3 rounded-xl border text-left transition-colors cursor-pointer flex flex-col justify-between ' + (on ? 'border-brand bg-brand-soft' : 'border-rule bg-white hover:border-rule-3 hover:bg-paper-3') + '">' +
        '<div class="flex items-center justify-between w-full mb-1.5"><div class="p-1.5 rounded-lg ' + (on ? 'bg-brand text-white' : 'bg-paper-2 text-ink-2') + '">' + A.icon(m.icon, 'w-3.5 h-3.5') + '</div><span class="text-xs text-muted">' + A.esc(m.cat) + '</span></div>' +
        '<div><div class="text-body font-bold truncate ' + (on ? 'text-brand' : 'text-ink') + '">' + A.esc(m.name) + '</div><div class="text-xs text-ink-3 mt-0.5">' + A.esc(m.desc) + '</div></div></button>';
    }).join('');
    A.icons();
  }

  /* ---------------- 변수/파라미터 ---------------- */
  var SELECT_CLS = 'w-full appearance-none bg-white border border-rule-3 rounded-lg pl-3 pr-8 py-2 text-xs text-ink-0 transition-colors hover:border-ink-4 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600';
  function selectWrap(innerSelect) {
    return '<div class="relative">' + innerSelect + '<i data-lucide="chevron-down" class="w-3.5 h-3.5 text-ink-4 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none"></i></div>';
  }
  /** 모든 필드를 동일한 박스(테두리·배경)로 감싸 좌/우 리듬을 맞춘다 */
  var fldSeq = 0;
  var REQ_STAR = '<span class="req-star" aria-hidden="true">*</span><span class="sr-only">(필수)</span>';
  var REQ_MSG = '<p class="req-msg" role="alert">필수 선택 항목입니다.</p>';
  var touched = {};   // 사용자가 건드렸거나 실행을 시도한 필수 항목: 비어 있으면 오류 문구를 보여 준다
  /** reqKey 가 있으면 필수 항목: 라벨 뒤에 빨간 별표(*)를 붙이고, 비어 있으면 오류 문구(.is-error)를 보여 준다 */
  function field(label, body, reqKey) {
    // 라벨을 입력칸과 for/id 로 연결 (라벨을 눌러도 입력칸에 포커스가 가고, 스크린리더가 이름을 읽는다)
    var m = body.match(/\sid="([^"]+)"/), id = m ? m[1] : 'fld-' + (++fldSeq);
    if (!m) body = body.replace(/<(select|input)\b/, '<$1 id="' + id + '"');
    return '<div class="space-y-1.5' + (reqKey ? ' req-field' : '') + '"' + (reqKey ? ' data-req="' + reqKey + '"' : '') + '><label for="' + id + '" class="text-body font-semibold text-ink block">' + label + (reqKey ? REQ_STAR : '') + '</label>' + body + (reqKey ? REQ_MSG : '') + '</div>';
  }
  /** 필수 항목이 비어 있는지 */
  function reqEmpty(key) {
    if (key === 'target') return !cfg.target;
    if (key === 'features') return !cfg.features.length;
    var v = cfg.params[key];
    return Array.isArray(v) ? !v.length : !v;
  }
  /** 필수 항목 표시 갱신: 독립변수 영역의 별표 여부, 비어 있는 항목에 오류 문구 */
  function updateReq() {
    var m = meta(cfg.method), fb = A.$('#feat-box'), fr = A.$('#feat-req');
    if (fb) { if (m.featOptional) fb.removeAttribute('data-req'); else fb.setAttribute('data-req', 'features'); }
    if (fr) fr.classList.toggle('hidden', !!m.featOptional);
    [].forEach.call(document.querySelectorAll('[data-req]'), function (el) {
      var k = el.getAttribute('data-req');
      el.classList.toggle('is-error', reqEmpty(k));   // 비어 있으면 항상 오류 표시 (선택하면 즉시 해제)
    });
  }
  /** 실행 시도 시: 비어 있는 필수 항목을 모두 오류로 표시하고 첫 항목으로 이동 */
  function flagMissing() {
    [].forEach.call(document.querySelectorAll('[data-req]'), function (el) {
      var k = el.getAttribute('data-req');
      if (reqEmpty(k)) touched[k] = true;
    });
    updateReq();
    var first = document.querySelector('[data-req].is-error');
    if (first) { first.scrollIntoView({ behavior: 'smooth', block: 'center' }); var f = first.querySelector('select,input'); if (f) f.focus({ preventScroll: true }); }
    return !!first;
  }
  function colSelect(id, key, from, selected, optional) {
    return selectWrap('<select id="' + id + '" data-key="' + key + '" class="' + SELECT_CLS + '">' +
      '<option value="">' + (optional ? '(사용 안 함)' : '필수 선택') + '</option>' +
      pool(from).filter(function (c) { return !(key === 'treatment_column' || key === 'group_column' || key === 'time_column') || c.name !== cfg.target; }).map(function (c) { return '<option value="' + A.esc(c.name) + '"' + (selected === c.name ? ' selected' : '') + '>' + A.esc(c.name) + '</option>'; }).join('') + '</select>');
  }

  /** 선형회귀·의사결정나무(회귀)인데 종속변수의 고유값이 2개면 실행 버튼 위에 안내한다 (고유값 수는 열 정보 n_unique) */
  function updatePreWarn() {
    var el = A.$('#pre-warn');
    if (!el) return;
    var c = (cfg.method === 'linear_regression' || cfg.method === 'decision_tree_regressor') && cfg.target ? cols().filter(function (x) { return x.name === cfg.target; })[0] : null;
    el.innerHTML = c && c.n_unique === 2 ? '<div class="krds-msg krds-warning flex items-start gap-2 py-1.5 mb-3" role="alert"><span class="flex-1 min-w-0">이분형 종속변수입니다. 로지스틱 회귀를 권장합니다.</span></div>' : '';
  }
  /** 다른 역할(종속·처치·집단·시간·가중치·요인·공변량)로 이미 쓴 열은 독립변수 목록에서 선택할 수 없게 한다 */
  var ROLE_NAME = { target: '종속변수', treatment_column: '처치 변수', group_column: '집단 변수', time_column: '시간 변수', weight_column: '가중치 변수', factors: '요인', covariates: '공변량' };
  function usedRoles() {
    var m = meta(cfg.method), used = {};
    if (m.target && cfg.target) used[cfg.target] = ROLE_NAME.target;
    m.fields.forEach(function (k) {
      var v = cfg.params[k];
      if (!ROLE_NAME[k] || v == null || v === '') return;
      [].concat(v).forEach(function (n) { if (n) used[n] = ROLE_NAME[k]; });
    });
    return used;
  }
  function renderFeatList() {
    var used = usedRoles();
    cfg.features = cfg.features.filter(function (f) { return !used[f]; });
    A.$('#feat-list').innerHTML = featCols(false).map(function (c) {
      var on = cfg.features.indexOf(c.name) >= 0, role = used[c.name];
      return '<label class="flex items-center gap-2 p-1.5 rounded text-xs transition-colors ' + (role ? 'text-ink-4 cursor-not-allowed' : 'text-ink-1 hover:bg-white cursor-pointer') + '"' + (role ? ' aria-disabled="true"' : '') + '><input type="checkbox" data-feat="' + A.esc(c.name) + '" ' + (on ? 'checked' : '') + (role ? ' disabled' : '') + ' class="rounded text-blue-600 focus:ring-blue-500 border-rule-3 ' + (role ? 'cursor-not-allowed' : 'cursor-pointer') + '"><span class="truncate">' + A.esc(c.name) + '</span><span class="ml-auto text-xs text-ink-4 font-mono shrink-0">' + (role ? role + '로 사용 중' : A.esc(c.role)) + '</span></label>';
    }).join('') || '<div class="text-xs text-ink-4 p-2">선택 가능한 변수가 없습니다. 1단계에서 변수 타입을 확인하세요.</div>';
    A.$('#feat-count').textContent = cfg.features.length + '개 선택';
  }
  function renderVars() {
    var m = meta(cfg.method);
    var box = A.$('#target-box');
    if (m.target) {
      box.innerHTML = field(cfg.method === 'psm' ? '결과변수' : '종속변수', colSelect('sel-target', 'target', 'numeric', cfg.target, false), 'target'); updatePreWarn();
    } else {
      // 오른쪽 파라미터 박스와 같은 크기가 되도록 같은 field 틀(라벨 + 입력 높이)로 안내를 표시
      box.innerHTML = field('종속변수', '<div class="w-full bg-paper-2/70 border border-rule rounded-lg px-3 py-2 text-xs text-ink-3">선택한 <strong class="text-ink-1">' + A.esc(m.name) + '</strong> 기법은 종속변수 지정이 필요하지 않습니다.</div>');
    }
    A.$('#feat-title').textContent = m.feat;
    renderFeatList();
    A.$('#feat-count').textContent = cfg.features.length + '개 선택';

    A.$('#extra-params').innerHTML = m.fields.map(function (k) {
      var f = FIELDS[k];
      if (f.t === 'select') {
        return field(f.label, selectWrap('<select data-par="' + k + '" class="' + SELECT_CLS + '">' +
          f.opts.map(function (o) { return '<option value="' + o[0] + '"' + (String(pv(k)) === String(o[0]) ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select>'));
      }
      if (f.t === 'check') {
        return '<div class="py-1"><label class="flex items-center gap-2 text-body text-ink font-semibold cursor-pointer"><input type="checkbox" data-par="' + k + '" ' + (pv(k) ? 'checked' : '') + ' class="rounded text-blue-600 border-rule-3 focus:ring-blue-500">' + f.label + '</label></div>';
      }
      if (f.t === 'text') {
        return field(f.label, '<input type="text" data-par="' + k + '" value="' + A.esc(cfg.params[k] || '') + '" placeholder="' + A.esc(f.ph || '') + '" class="w-full bg-white border border-rule-3 rounded-lg px-3 py-2 text-xs transition-colors hover:border-ink-4 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600">');
      }
      if (f.t === 'col') {
        return field(f.label, colSelect('par-' + k, k, f.from, cfg.params[k], !f.required).replace('data-key="' + k + '"', 'data-par="' + k + '"'), f.required ? k : null);
      }
      var sel = cfg.params[k] || [];
      return field(f.label, '<div class="border border-rule rounded-lg p-2 max-h-32 overflow-y-auto space-y-0.5 bg-white">' +
        pool(f.from).map(function (c) { return '<label class="flex items-center gap-2 text-xs text-ink-1 cursor-pointer p-1 rounded hover:bg-paper-3"><input type="checkbox" data-multi="' + k + '" value="' + A.esc(c.name) + '" ' + (sel.indexOf(c.name) >= 0 ? 'checked' : '') + ' class="rounded text-blue-600 border-rule-3"><span class="truncate">' + A.esc(c.name) + '</span></label>'; }).join('') + '</div>', cfg.method === 'anova' && k === 'factors' ? k : null);
    }).join('');
    A.$('#btn-run').disabled = running;
    updateReq();
  }

  /* ---------------- 요청 조립 ---------------- */
  function buildParams() {
    var m = meta(cfg.method), p = { features: cfg.features.slice() };
    if (m.target) p.target = cfg.target;
    m.fields.forEach(function (k) {
      var f = FIELDS[k], v = pv(k);
      if (k === 'auto_k') { if (v) p.auto_k_range = [2, 8]; return; }
      if (k === 'n_clusters' && pv('auto_k')) return;
      if (f.t === 'cols') { if (v && v.length) p[k] = v; return; }
      if (v === '' || v === undefined || v === null) return;
      if (f.t === 'text' && !String(v).trim()) return;
      p[k] = f.num ? Number(v) : v;
    });
    return p;
  }
  function validate() {
    var m = meta(cfg.method);
    if (m.target && !cfg.target) return '종속변수를 선택하세요.';
    if (!m.featOptional && !cfg.features.length) return '변수를 1개 이상 선택하세요.';
    var miss = m.fields.filter(function (k) { return FIELDS[k].required && !cfg.params[k]; });
    if (miss.length) return '필수 항목을 선택하세요: ' + FIELDS[miss[0]].label;
    if (cfg.method === 'anova' && !(cfg.params.factors || []).length) return 'ANOVA 요인(범주형 변수)을 1개 이상 선택하세요.';
    return null;
  }

  /* ---------------- 결과 패널 ---------------- */
  var STATUS = { succeeded: ['수렴 성공', 'text-brand'], failed: ['실패', 'text-rose-700'], running: ['실행 중', 'text-ink-2'], pending: ['대기', 'text-ink-2'], cancelled: ['취소됨', 'text-ink-2'] };
  var jobOk = false;   // 이번 실행의 작업(job)이 succeeded 로 끝났는지
  /** 분석 완료: 분석 상태가 succeeded 이거나, 작업이 succeeded 로 끝났고 분석이 실패·취소가 아닌 경우 */
  function isDone() {
    if (!analysis) return false;
    if (analysis.status === 'succeeded') return true;
    return jobOk && analysis.status !== 'failed' && analysis.status !== 'cancelled';
  }
  /** 분석이 성공으로 끝난 뒤에만 '4-2 분석 결과 보기'를 연다 */
  function syncReportBtn(ok) {
    var b = A.$('#btn-report');
    if (!b) return;
    b.setAttribute('aria-disabled', ok ? 'false' : 'true');
    b.tabIndex = ok ? 0 : -1;
    b.title = ok ? '' : '분석 실행이 끝나면 볼 수 있습니다';
  }
  document.addEventListener('click', function (e) {
    var b = e.target.closest && e.target.closest('#btn-report');
    if (b && b.getAttribute('aria-disabled') === 'true') e.preventDefault();
  });
  function renderResult() {
    var p = A.$('#result-panel');
    var ok = isDone();
    syncReportBtn(ok);
    p.classList.remove('hidden');
    A.$('#fit-badge').classList.toggle('hidden', !ok);
    A.$('#fit-badge').classList.toggle('flex', !!ok);
    if (!analysis) {
      // 요청 전에는 결과 영역을 보여 주지 않는다
      p.innerHTML = '';
      p.classList.add('hidden');
      A.icons();
      return;
    }
    // 성공한 분석은 결과 영역을 두지 않는다 (완료 알림은 토스트로)
    if (ok) { p.innerHTML = ''; p.classList.add('hidden'); A.icons(); return; }
    // 실패·취소: 박스 없이 빨간 글씨 한 줄 + 닫기(X). 데이터 결합 실패와 같은 모양
    var r = analysis;
    var text = r.status === 'cancelled' ? '대기 중이던 분석 요청이 취소되었습니다. 다시 실행해 주세요.' : (r.error || '분석 연산에 실패했습니다. 변수·파라미터 설정을 확인한 뒤 다시 시도해 주세요.');
    p.innerHTML = '<div class="mfail flex items-start gap-2" role="alert"><p class="mfail-head flex-1 min-w-0 break-words whitespace-pre-wrap">' + A.esc(text) + '</p></div>';
    A.icons();
  }

  function renderPipe() {
    var m = meta(cfg.method);
    A.$('#pipe-body').innerHTML = '<div class="p-4 text-xs">' +
      '<div class="p-3 bg-paper-3 rounded-lg border border-rule/80 space-y-2"><div class="font-bold text-ink-0 text-xs pb-1 border-b border-rule">모델 및 변수 바인딩 명세</div><div class="space-y-1 text-xs">' +
      '<div class="flex justify-between"><span class="text-ink-3">선택 모형:</span><span class="font-semibold text-ink-0">' + A.esc(m.name) + ' (' + A.esc(m.en) + ')</span></div>' +
      '<div class="flex justify-between"><span class="text-ink-3">종속변수:</span><span class="font-semibold text-ink-0">' + (m.target ? A.esc(cfg.target || '-') : '없음 (비지도/탐색)') + '</span></div>' +
      '<div class="pt-1"><span class="text-ink-3 block mb-1">투입 변수 (' + cfg.features.length + '개):</span><div class="flex flex-wrap gap-1">' + cfg.features.map(function (f) { return '<span class="text-xs text-ink-1">' + A.esc(f) + '</span>'; }).join('') + '</div></div></div></div></div>';
  }

  function run() {
    if (running) return;
    var bad = validate();
    if (bad && flagMissing()) { A.toast(bad, 'error'); return; }
    if (bad) { analysis = { method: cfg.method, status: 'failed', error: bad, created_at: new Date().toISOString() }; renderResult(); A.toast('분석에 실패했습니다.', 'error'); return; }
    running = true;
    jobOk = false;
    A.$('#result-panel').classList.add('hidden');   // 이전 실패 문구는 새 분석을 시작할 때 지운다
    syncReportBtn(false);   // 새 분석을 시작하면 이전 결과 보기는 다시 닫고, 완료되면 연다
    var b = A.$('#btn-run');
    b.disabled = true;
    b.innerHTML = '<span>분석 연산 수행 중...</span>';
    var m = meta(cfg.method);
    A.saveState({ config: cfg });
    A.post('/api/v1/analyses', { dataset_id: dsId, method: cfg.method, name: m.name + ' - ' + (A.state.datasetName || dsId), params: buildParams(), preprocessing: A.state.preprocessing || {} }, { onJob: function (j) { if (j && j.status === 'succeeded') jobOk = true; } }).then(function (r) {
      analysis = r;
      A.saveState({ analysisId: r.id });
      renderResult();
      if (isDone()) A.toast('분석이 완료되었습니다.');
      else if (r.status === 'failed') A.toast('분석에 실패했습니다.', 'error');
    }).catch(function (e) {
      // 요청 자체가 실패한 경우(검증 오류·네트워크 등)도 연산 결과 패널에 실패로 표시
      analysis = { method: cfg.method, status: 'failed', error: e.message, created_at: new Date().toISOString() };
      renderResult();
      A.toast('분석에 실패했습니다.', 'error');
    }).then(function () {
      running = false;
      b.disabled = false;
      b.innerHTML = '<span>분석 실행</span>';
      A.icons();
    });
  }

  function defaultFeatures() {
    var m = meta(cfg.method);
    return numericCols().filter(function (c) { return !m.target || c.name !== cfg.target; }).slice(0, 4).map(function (c) { return c.name; });
  }
  function refreshAll() { renderMethods(); renderVars(); renderPipe(); A.icons(); }

  document.addEventListener('DOMContentLoaded', function () {
    A.$('#method-grid').addEventListener('click', function (e) {
      var b = e.target.closest('[data-method]');
      if (!b) return;
      cfg.method = b.getAttribute('data-method'); touched = {};
      var m = meta(cfg.method);
      if (m.target && !cfg.target && numericCols().length) cfg.target = numericCols()[0].name;
      cfg.features = cfg.features.filter(function (f) { return f !== cfg.target || !m.target; });
      if (!cfg.features.length && !m.featOptional) cfg.features = defaultFeatures();
      refreshAll();
    });
    A.$('#target-box').addEventListener('change', function (e) {
      if (e.target.id !== 'sel-target') return;
      cfg.target = e.target.value; touched.target = true;
      cfg.features = cfg.features.filter(function (f) { return f !== cfg.target; });
      renderVars(); renderPipe(); A.icons();
    });
    A.$('#feat-list').addEventListener('change', function (e) {
      var id = e.target.getAttribute('data-feat');
      if (!id) return;
      var i = cfg.features.indexOf(id);
      if (e.target.checked && i < 0) cfg.features.push(id);
      if (!e.target.checked && i >= 0) cfg.features.splice(i, 1);
      A.$('#feat-count').textContent = cfg.features.length + '개 선택';
      touched.features = true; updateReq(); renderPipe(); A.icons();
    });
    A.$('#feat-all').addEventListener('click', function () {
      var m = meta(cfg.method);
      var usedNow = usedRoles();
      cfg.features = featCols(true).filter(function (c) { return !usedNow[c.name]; }).map(function (c) { return c.name; });
      renderVars(); renderPipe(); A.icons();
    });
    A.$('#feat-none').addEventListener('click', function () { cfg.features = []; touched.features = true; renderVars(); renderPipe(); A.icons(); });
    A.$('#extra-params').addEventListener('change', function (e) {
      var t = e.target, k = t.getAttribute('data-par'), mk = t.getAttribute('data-multi');
      if (mk) {
        var arr = cfg.params[mk] || [];
        var i = arr.indexOf(t.value);
        if (t.checked && i < 0) arr.push(t.value);
        if (!t.checked && i >= 0) arr.splice(i, 1);
        cfg.params[mk] = arr; touched[mk] = true;
        if (ROLE_NAME[mk]) renderFeatList();
        updateReq();
        return;
      }
      if (!k) return;
      cfg.params[k] = t.type === 'checkbox' ? t.checked : t.value; touched[k] = true;
      updateReq();
      if (ROLE_NAME[k]) { renderFeatList(); updatePreWarn(); }
      if (k === 'auto_k') { renderVars(); A.icons(); }
    });
    A.$('#btn-run').addEventListener('click', run);
    A.$('#pipe-toggle').addEventListener('click', function () {
      var b = A.$('#pipe-body'), open = b.classList.toggle('hidden') === false;
      A.$('#pipe-txt').textContent = open ? '접기' : '상세 보기';
      A.$('#pipe-ic').style.transform = open ? 'rotate(180deg)' : '';
    });

    A.get('/api/v1/datasets/' + encodeURIComponent(dsId)).then(function (d) {
      dataset = d;
      var m = meta(cfg.method);
      var names = cols().map(function (c) { return c.name; });
      if (cfg.target && names.indexOf(cfg.target) < 0) cfg.target = '';
      cfg.features = cfg.features.filter(function (f) { return names.indexOf(f) >= 0; });
      if (m.target && !cfg.target && numericCols().length) cfg.target = numericCols()[0].name;
      if (!cfg.features.length && !m.featOptional) cfg.features = defaultFeatures();
      refreshAll();
      renderResult();
      if (A.state.analysisId) {
        return A.get('/api/v1/analyses/' + encodeURIComponent(A.state.analysisId)).then(function (r) { analysis = r; renderResult(); }).catch(function () { A.saveState({ analysisId: null }); });
      }
    }).catch(function (e) { if (!A.datasetGone(e)) A.fail(e.message); });

    // API 가 제공하는 기법 설명이 있으면 보강 (실패해도 내장 목록으로 동작)
    A.get('/api/v1/methods').then(function (list) {
      (list || []).forEach(function (x) {
        var id = x.id || x.method || x.key || x.value, m = METHODS.filter(function (y) { return y.id === id; })[0];
        if (m && x.description) m.desc = x.description;
      });
      renderMethods(); A.icons();
    }).catch(function () { /* ignore */ });
    A.icons();
  });
})();
