/* 1단계: 데이터 준비 및 반입 — /api/v1/datasets, /api/v1/data-cards, /api/v1/datasets/merge
 * 데이터관리카드와 반입 데이터셋을 개수 제한 없이 여러 개 고를 수 있다.
 *  - 데이터셋마다 분석에 쓸 열을 체크한다 (결합 요청의 sources[].columns 로 전달해 처리량을 줄인다).
 *  - 2개 이상이면 공통 키 매핑(key_map)으로 열을 붙여(join) 결합하고, 결합 결과가 분석 대상이 된다.
 *  - 1개면 그 데이터셋이 분석 대상이다. 일부 열만 체크했다면 2단계로 넘어갈 때 POST /datasets/{id}/subset 으로
 *    그 열만 담은 새 데이터셋을 만들어 이후 단계에 쓴다.
 *  업로드·결합·변수 선택은 백그라운드 작업(202)이므로 대기 순번·진행 상태를 화면에 보여준다. */
(function () {
  'use strict';
  var A = window.App;

  var ROLES = [['numeric', '수치형 (Numeric)'], ['categorical', '범주형 (Categorical)'], ['boolean', '논리형 (Boolean)'], ['datetime', '일시형 (Datetime)'], ['text', '문자형 (Text)'], ['identifier', '식별자 (Identifier)'], ['constant', '상수 (Constant)']];
  var JOIN_TYPES = [['inner', '키가 모든 데이터셋에 있는 행만'], ['left', '1번 데이터셋의 행을 모두 유지'], ['right', '마지막 데이터셋의 행을 모두 유지'], ['outer', '어느 한쪽에라도 있는 행 모두']];
  var PAGE = 20;
  var ALLOWED = /\.(csv|txt|xlsx|xls|json|parquet)$/i;
  var MERGED_TAB = '__merged__';

  var sel = [];              // 선택한 데이터셋 [{id, kind:'card'|'dataset', d: DatasetDetail, use: {열이름: true}, alias}]
  var activeId = null;       // 열·미리보기에 보여줄 데이터셋 id (결합 결과는 MERGED_TAB)
  var datasets = [], cards = [];
  var uploadError = null, dragging = false, uploading = false;
  var preview = { dsId: null, rows: [], cols: [], total: 0, loading: false };
  // 결합 설정 (join 고정). keys: [{ 데이터셋id: 열이름 }] — 1번 데이터셋의 열 이름이 공통 키 이름이 된다
  var mcfg = { how: 'inner', keys: [{}], name: '', nameTouched: false };
  var merged = null, mergedSig = null, merging = false, mergeError = null, mergeJob = '';
  var uploadJob = '', proceeding = false, proceedJob = '';

  function find(id) { return sel.filter(function (s) { return s.id === id; })[0] || null; }
  function colsOf(s) { return (s.d && s.d.columns) || []; }
  function usedList(s) { return colsOf(s).filter(function (c) { return s.use[c.name]; }).map(function (c) { return c.name; }); }
  function isSubset(s) { return usedList(s).length < colsOf(s).length; }
  function shortName(n) { n = String(n || ''); return n.length > 14 ? n.slice(0, 14) : n; }

  /* ---------------- 결합 요청 ---------------- */
  function validKeys() {
    if (sel.length < 2) return [];
    return mcfg.keys.filter(function (k) { return sel.every(function (s) { return !!k[s.id]; }); });
  }
  function buildMerge() {
    var keys = validKeys();
    var keyNames = keys.map(function (k) { return k[sel[0].id]; });
    var sources = sel.map(function (s) {
      var src = { dataset_id: s.id, alias: s.alias };   // 별칭: 키가 아닌 열 이름이 겹칠 때 붙는 접미사 (데이터셋 이름으로 자동)
      var km = {};
      keys.forEach(function (k, i) { if (k[s.id] !== keyNames[i]) km[keyNames[i]] = k[s.id]; });
      if (Object.keys(km).length) src.key_map = km;
      if (isSubset(s)) {   // 쓰는 열만 보낸다. 키 열은 결합에 필요하므로 항상 포함
        var cols = usedList(s);
        keys.forEach(function (k) { if (cols.indexOf(k[s.id]) < 0) cols.push(k[s.id]); });
        src.columns = cols;
      }
      return src;
    });
    return { name: mcfg.name || defaultName(), mode: 'join', join_type: mcfg.how, keys: keyNames, sources: sources };
  }
  function defaultName() { return '결합_' + sel.map(function (s) { return shortName(s.d.name); }).join('+'); }
  function mergeProblem() {
    if (sel.length < 2) return null;
    if (sel.some(function (s) { return !usedList(s).length; })) return '분석에 사용할 열이 하나도 없는 데이터셋이 있습니다.';
    if (!validKeys().length) return '데이터셋마다 키로 쓸 열을 고르세요.';
    return null;
  }
  function isStale() { return !!merged && mergedSig !== JSON.stringify(buildMerge()); }

  /** 키 매핑 자동 채움: 비어 있는 칸은 첫 데이터셋 키와 같은 이름의 열로 */
  function autofillKeys() {
    if (sel.length < 2) return;
    var first = sel[0];
    if (mcfg.keys.length === 1 && !mcfg.keys[0][first.id]) {
      // 첫 키 추천: 모든 데이터셋에 같은 이름으로 있는 열 (식별자 우선)
      var common = colsOf(first).filter(function (c) { return sel.every(function (s) { return colsOf(s).some(function (x) { return x.name === c.name; }); }); });
      common.sort(function (a, b) { return (b.role === 'identifier') - (a.role === 'identifier'); });
      if (common.length) mcfg.keys[0][first.id] = common[0].name;
      else {
        // 같은 이름이 없으면: 데이터셋마다 사용 중인 식별자(identifier) 열이 정확히 하나일 때만 그 열들을 짝지어 추천
        var ids = sel.map(function (s) { return colsOf(s).filter(function (c) { return c.role === 'identifier'; }); });
        if (ids.every(function (l) { return l.length === 1; })) sel.forEach(function (s, i) { mcfg.keys[0][s.id] = ids[i][0].name; });
      }
    }
    mcfg.keys.forEach(function (k) {
      var name = k[first.id];
      if (!name) return;
      sel.forEach(function (s) { if (!k[s.id] && colsOf(s).some(function (c) { return c.name === name; })) k[s.id] = name; });
    });
  }

  /* ---------------- 분석 대상 (2단계로 넘길 데이터셋) ---------------- */
  function target() {
    if (!sel.length) return null;
    if (sel.length === 1) return sel[0].d;
    return merged && !isStale() ? merged : null;
  }
  function syncTarget() {
    var t = target();
    A.saveState({ datasetId: t ? t.id : null, datasetName: t ? t.name : null, datasetRows: t ? t.n_rows : null, usedColumns: null, rawDatasetId: null, analysisId: null });
  }

  /* ---------------- 데이터관리카드 ---------------- */
  function loadCards() {
    var q = A.$('#mgmt-search').value || '';
    return A.get('/api/v1/data-cards' + A.qs({ limit: 100, q: q })).then(function (p) {
      cards = p.items || [];
      A.$('#mgmt-total').textContent = '총 ' + A.num(p.total) + '건';
      renderCards();
    }).catch(function (e) { A.$('#mgmt-list').innerHTML = '<div class="p-4 text-xs text-rose-600">' + A.esc(e.message) + '</div>'; });
  }
  function checkBox(on) {
    return '<span class="w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-colors ' + (on ? 'bg-brand border-brand text-white' : 'border-rule-3 bg-white') + '">' + (on ? A.icon('check', 'w-3 h-3') : '') + '</span>';
  }
  function renderCards() {
    function row(c) {
      var on = !!find(c.id);
      var st = c.status && c.status !== 'ready' ? c.status : null;   // loading: 처음 적재 중, failed: 적재 실패
      return '<div role="button" tabindex="0" data-card="' + A.esc(c.id) + '" class="p-3 flex items-center justify-between transition-colors select-none ' + (st ? 'cursor-not-allowed opacity-60' : 'cursor-pointer ') + (on ? 'bg-brand-soft' : 'hover:bg-paper-3') + '">' +
        '<div class="flex items-center gap-2.5 min-w-0 pr-2">' + checkBox(on) + '<span class="text-body truncate ' + (on ? 'font-semibold text-ink' : 'text-ink-1') + '" title="' + A.esc(c.name) + '">' + A.esc(c.name) + '</span></div>' +
        (st ? '<span class="text-xs shrink-0 whitespace-nowrap px-1.5 rounded ' + (st === 'loading' ? 'text-link bg-brand-soft font-semibold' : 'text-ink-3 bg-paper-2') + '">' + (st === 'loading' ? '적재 중' : '적재 실패') + '</span>'
          : '<span class="text-xs font-mono text-ink-3 shrink-0">' + A.num(c.n_rows) + '행</span>') + '</div>';
    }
    // 선택 가능한 카드를 위에, 적재 실패는 아래에 따로 묶는다 (실패 배지가 목록 전체에 흩어지지 않게)
    var failed = cards.filter(function (c) { return c.status === 'failed'; });
    var usable = cards.filter(function (c) { return c.status !== 'failed'; });
    A.$('#mgmt-list').innerHTML = usable.map(row).join('') +
      (failed.length ? '<div class="px-3 py-2 text-xs font-semibold text-ink-3 bg-paper-3">적재 실패 ' + failed.length + '건 · \'카드 동기화\'로 다시 불러올 수 있습니다</div>' + failed.map(row).join('') : '') ||
      '<div class="p-4 text-body text-ink-3 text-center">등록된 데이터관리카드가 없습니다. \'카드 동기화\'로 불러올 수 있습니다.</div>';
    A.icons();
  }
  function syncCards() {
    var b = A.$('#mgmt-sync');
    b.disabled = true; b.textContent = '동기화 중...';
    A.post('/api/v1/data-cards/sync', {}).then(function (r) {
      // 성공 건은 목록에 바로 보이므로 따로 알리지 않고, 실패 건만 목록 아래에 표시
      A.fail(r.failed ? '데이터관리카드 ' + r.failed + '건을 불러오지 못했습니다. (성공 ' + r.succeeded + '건)' : null, '#mgmt-list');
      return loadCards();
    }).catch(function (e) { A.fail(e.message, '#mgmt-list'); }).then(function () { b.disabled = false; b.textContent = '카드 동기화'; });
  }

  /* ---------------- 반입 데이터셋 ---------------- */
  function loadDatasets() {
    return Promise.all([
      A.get('/api/v1/datasets' + A.qs({ limit: 100, source_type: 'upload' })),
      A.get('/api/v1/datasets' + A.qs({ limit: 100, source_type: 'merged' }))
    ]).then(function (r) {
      datasets = (r[0].items || []).concat(r[1].items || []);
      A.$('#ds-total').textContent = datasets.length + '건';
      renderDatasets();
    }).catch(function (e) { A.fail(e.message, '#ds-list'); });
  }
  function renderDatasets() {
    A.$('#ds-list').innerHTML = datasets.map(function (d) {
      var on = !!find(d.id);
      return '<div role="button" tabindex="0" data-ds="' + A.esc(d.id) + '" class="p-3 flex items-center justify-between gap-2 cursor-pointer select-none transition-colors ' + (on ? 'bg-blue-50/70' : 'hover:bg-paper-3/80') + '">' +
        '<div class="flex items-center gap-2.5 min-w-0">' + checkBox(on) + '<div class="min-w-0"><div class="text-xs font-bold text-ink truncate">' + A.esc(d.name) +
        (d.source_type === 'merged' ? ' <span class="ml-1 text-xs font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-1.5 rounded">결합</span>' : '') + '</div>' +
        '<div class="text-xs text-ink-4 font-mono mt-0.5">' + A.num(d.n_rows) + '행 · ' + d.n_cols + '변수' + (d.source_format ? ' · ' + A.esc(d.source_format) : '') + '</div></div></div>' +
        '<button type="button" data-del="' + A.esc(d.id) + '" class="p-1 text-rule-3 hover:text-rose-600 cursor-pointer shrink-0" title="삭제">' + A.icon('trash-2', 'w-3.5 h-3.5') + '</button></div>';
    }).join('') || '<div class="p-4 text-xs text-ink-4 text-center">반입된 데이터셋이 없습니다. 파일을 업로드해 주세요.</div>';
    A.icons();
  }

  /* ---------------- 업로드 ---------------- */
  function renderUpload() {
    var html;
    if (uploading) {
      html = '<div class="border-2 border-dashed border-blue-300 bg-blue-50/40 p-6 rounded-2xl text-center text-xs text-blue-800 font-semibold flex items-center justify-center gap-2"><span class="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full spin inline-block"></span>파일을 분석하고 있습니다...' +
        (uploadJob ? ' <span class="font-normal text-blue-700/80">(' + A.esc(uploadJob) + ')</span>' : '') + '</div>';
    } else {
      html = '<label id="dropzone" class="block border-2 border-dashed p-3 rounded-2xl transition-colors cursor-pointer text-center ' + (dragging ? 'border-blue-500 bg-blue-50/50' : 'border-rule hover:border-blue-400 bg-paper-3/40 hover:bg-blue-50/20') + '">' +
        '<input type="file" accept=".csv,.txt,.xlsx,.xls,.json,.parquet" class="hidden" id="file-input">' +
        '<div class="text-xs font-bold text-ink-0">클릭하여 파일 선택 또는 여기로 드래그 앤 드롭</div>' +
        (uploadError ? '<div class="mt-3 text-xs font-semibold text-rose-700 bg-rose-50 p-2 rounded-lg border border-rose-200">' + A.esc(uploadError) + '</div>' : '') + '</label>';
    }
    A.$('#upload-area').innerHTML = html;
  }
  function handleFile(file) {
    if (!ALLOWED.test(file.name)) { uploadError = '지원하지 않는 파일 형식입니다. (CSV, TXT, XLSX, XLS, JSON, Parquet)'; renderUpload(); return; }
    uploadError = null; uploading = true; renderUpload();
    var fd = new FormData();
    fd.append('file', file);
    uploadJob = '';
    A.api('POST', '/api/v1/datasets/upload', fd, { onJob: function (j) { var t = A.jobText(j); if (t !== uploadJob) { uploadJob = t; renderUpload(); } } }).then(function (d) {
      uploading = false; uploadJob = '';
      renderUpload();
      return loadDatasets().then(function () { if (!find(d.id)) return toggle('dataset', d.id); });
    }).catch(function (e) { uploading = false; uploadJob = ''; uploadError = e.message; renderUpload(); });
  }

  /* ---------------- 선택 (여러 개) ---------------- */
  function toggle(kind, id) {
    var s = find(id);
    if (s) { remove(id); return Promise.resolve(); }
    var c = kind === 'card' ? cards.filter(function (x) { return x.id === id; })[0] : null;
    if (c && c.status && c.status !== 'ready') {
      A.fail(c.status === 'loading' ? '데이터관리카드를 적재하고 있습니다. 잠시 후 다시 선택해 주세요.' : '적재에 실패한 데이터관리카드입니다. \'카드 동기화\'로 다시 불러와 주세요.', '#mgmt-list');
      return Promise.resolve();
    }
    return A.get('/api/v1/datasets/' + encodeURIComponent(id)).then(function (d) {
      var use = {};
      (d.columns || []).forEach(function (c) { use[c.name] = true; });
      // 별칭은 데이터셋 이름으로 자동 지정 (이름이 같으면 번호를 붙여 겹치지 않게)
      var alias = shortName(d.name), n = 2;
      while (sel.some(function (x) { return x.alias === alias; })) alias = shortName(d.name) + '_' + n++;
      sel.push({ id: id, kind: kind, d: d, use: use, alias: alias });
      activeId = id;
      autofillKeys();
      changed();
    }).catch(function (e) { A.fail(e.message, kind === 'card' ? '#mgmt-list' : '#ds-list'); });
  }
  function remove(id) {
    sel = sel.filter(function (s) { return s.id !== id; });
    mcfg.keys.forEach(function (k) { delete k[id]; });
    if (activeId === id) activeId = sel.length ? sel[0].id : null;
    if (sel.length < 2) { merged = null; mergedSig = null; if (activeId === MERGED_TAB) activeId = sel.length ? sel[0].id : null; }
    autofillKeys();
    changed();
  }
  /** 선택·열·결합 설정이 바뀔 때마다: 분석 대상 갱신 후 다시 그림 */
  function changed() {
    if (!mcfg.nameTouched) mcfg.name = sel.length >= 2 ? defaultName() : '';
    syncTarget();
    renderAll();
  }

  /* ---------------- 선택한 데이터 탭 ---------------- */
  function renderTabs() {
    var el = A.$('#s1-tabs');
    if (!sel.length) { el.innerHTML = '<span class="text-xs text-ink-4">위에서 데이터관리카드나 반입된 데이터셋을 체크하세요. 여러 개를 고르면 결합할 수 있습니다.</span>'; return; }
    var chips = sel.map(function (s, i) {
      var on = activeId === s.id;
      return '<div class="flex items-center rounded-lg border text-xs transition-colors ' + (on ? 'bg-brand border-brand text-white' : 'bg-white border-rule text-ink-1 hover:border-ink-4') + '">' +
        '<button type="button" data-tab="' + A.esc(s.id) + '" class="flex items-center gap-1.5 pl-2.5 pr-1.5 py-1.5 cursor-pointer max-w-[280px]">' +
        '<span class="font-mono text-xs opacity-70 shrink-0">' + (i + 1) + '</span>' +
        '<span class="px-1 rounded text-xs font-bold shrink-0 whitespace-nowrap leading-4 ' + (on ? 'bg-white/20' : (s.kind === 'card' ? 'bg-blue-50 text-blue-700' : 'bg-paper-2 text-ink-2')) + '">' + (s.kind === 'card' ? '카드' : '파일') + '</span>' +
        '<span class="truncate min-w-0 font-semibold">' + A.esc(s.d.name) + '</span>' +
        '<span class="font-mono text-xs opacity-70 shrink-0 whitespace-nowrap">' + usedList(s).length + '/' + colsOf(s).length + '열</span></button>' +
        '<button type="button" data-remove="' + A.esc(s.id) + '" title="선택 해제" class="pr-2 pl-0.5 py-1.5 opacity-60 hover:opacity-100 cursor-pointer">' + A.icon('x', 'w-3 h-3') + '</button></div>';
    });
    if (sel.length >= 2 && merged) {
      var st = isStale(), on = activeId === MERGED_TAB;
      chips.push('<button type="button" data-tab="' + MERGED_TAB + '" class="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border text-xs font-semibold cursor-pointer ' +
        (on ? 'bg-emerald-700 border-emerald-700 text-white' : 'bg-emerald-50 border-emerald-200 text-emerald-800 hover:border-emerald-400') + '">' + A.icon('combine', 'w-3.5 h-3.5') + '<span>결합 결과</span>' +
        '<span class="font-mono text-xs opacity-80">' + A.num(merged.n_rows) + '행 · ' + merged.n_cols + '열</span>' + (st ? '<span class="text-xs px-1 rounded bg-amber-400 text-amber-950">재결합 필요</span>' : '') + '</button>');
    }
    el.innerHTML = chips.join('');
  }

  /* ---------------- 열 선택 표 ---------------- */
  function renderColumns() {
    var body = A.$('#col-body'), all = A.$('#col-all');
    A.$('#col-title').textContent = '선택한 데이터' + (sel.length ? ' (' + sel.length + '개)' : '');
    var isMerged = activeId === MERGED_TAB;
    var s = isMerged ? null : find(activeId);
    var d = isMerged ? merged : (s && s.d);
    // 빈 상태: 표 머리·미리보기 카드를 숨기고 안내 문구만 남긴다
    A.$('#col-card').classList.toggle('hidden', !sel.length);   // 선택 전에는 열 선택 카드 자체를 숨김
    A.$('#col-body').closest('.overflow-x-auto').classList.toggle('hidden', !d);
    A.$('#preview-card').classList.toggle('hidden', !d);
    if (!d) { body.innerHTML = ''; all.checked = false; all.disabled = true; return; }
    var q = (A.$('#col-search').value || '').toLowerCase();
    var cols = d.columns || [];
    // 타입 변경 가능 여부는 서버가 열마다 알려주는 role_locked 를 따른다 (없으면 업로드 데이터만 변경 가능)
    var canEdit = function () { return !isMerged; };   // 결합 결과 탭만 읽기 전용. 카드 변수도 선택은 열어 두고, 서버가 거절(403)하면 오류를 보여준다
    all.disabled = isMerged;
    all.checked = isMerged || usedList(s).length === cols.length;
    all.indeterminate = !isMerged && usedList(s).length > 0 && usedList(s).length < cols.length;
    body.innerHTML = cols.filter(function (c) { return c.name.toLowerCase().indexOf(q) >= 0; }).map(function (c) {
      var on = isMerged || !!s.use[c.name], editable = canEdit(c);
      return '<tr class="transition-colors ' + (on ? 'hover:bg-paper-3/70' : 'bg-paper-3/60 text-ink-4') + '">' +
        '<td class="py-2 px-4"><input type="checkbox" aria-label="' + A.esc(c.name) + ' 분석에 사용" data-use="' + A.esc(c.name) + '" ' + (on ? 'checked ' : '') + (isMerged ? 'disabled ' : '') + 'class="accent-brand cursor-pointer"></td>' +
        '<td class="py-2 px-4 font-mono font-semibold ' + (on ? 'text-ink-0' : 'text-ink-4 line-through') + '">' + A.esc(c.name) + '</td>' +
        '<td class="py-2 px-4 text-right font-mono text-ink-3">' + A.num(c.n_unique) + '</td>' +
        '<td class="py-2 px-4 text-right font-mono ' + (c.n_missing ? 'text-amber-600' : 'text-ink-4') + '">' + A.num(c.n_missing || 0) + '</td>' +
        '<td class="py-2 px-4"><select aria-label="' + A.esc(c.name) + ' 타입" data-col="' + A.esc(c.name) + '"' + (editable ? '' : ' disabled title="결합 결과의 타입은 여기서 바꿀 수 없습니다."') + ' class="bg-white border border-rule rounded-md px-2 py-1 text-xs focus:outline-none focus:border-blue-600 ' + (editable ? 'text-ink-0 cursor-pointer' : 'text-ink-4 bg-paper-3 cursor-not-allowed') + '">' +
        ROLES.map(function (o) { return '<option value="' + o[0] + '"' + (c.role === o[0] ? ' selected' : '') + '>' + o[1] + '</option>'; }).join('') + '</select></td></tr>';
    }).join('');
  }

  /* ---------------- 결합 설정 ---------------- */
  function fieldCls() { return 'bg-white border border-rule-3 rounded-lg px-2.5 py-1.5 text-xs text-ink-0 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600'; }
  function renderMerge() {
    var box = A.$('#merge-card');
    if (sel.length < 2) { box.classList.add('hidden'); box.innerHTML = ''; return; }
    box.classList.remove('hidden');
    // 키 매핑: 한 줄에 [데이터셋1 키 열] = [데이터셋2 키 열] (좁은 화면은 세로로 쌓임)
    var rows = mcfg.keys.map(function (k, ri) {
      var partial = sel.some(function (s) { return !!k[s.id]; });   // 일부만 골랐을 때만 빈 칸을 경고색으로
      return '<div class="flex flex-col md:flex-row md:items-end gap-2">' + sel.map(function (s, i) {
        var v = k[s.id] || '', sid = 'mk-' + ri + '-' + i;
        return (i ? '<span class="hidden md:block pb-2 text-ink-4" aria-hidden="true">=</span>' : '') +
          '<div class="flex-1 min-w-0"><label for="' + sid + '" class="block text-xs text-ink-3 mb-1 truncate" title="' + A.esc(s.d.name) + '">' + A.esc(s.d.name) + '</label>' +
          '<select id="' + sid + '" data-key="' + ri + '" data-ds="' + A.esc(s.id) + '" class="w-full text-body ' + fieldCls() + (partial && !v ? ' !border-amber-400' : '') + '"><option value="">(키 열 선택)</option>' +
          colsOf(s).map(function (c) { return '<option value="' + A.esc(c.name) + '"' + (v === c.name ? ' selected' : '') + '>' + A.esc(c.name) + '</option>'; }).join('') + '</select></div>';
      }).join('') +
        (mcfg.keys.length > 1 ? '<button type="button" data-delkey="' + ri + '" class="self-end p-2 text-ink-4 hover:text-rose-600 cursor-pointer shrink-0" title="키 삭제" aria-label="키 ' + (ri + 1) + ' 삭제">' + A.icon('trash-2', 'w-4 h-4') + '</button>' : '') + '</div>';
    }).join('');
    var prob = mergeProblem(), st = isStale();
    var status = '';
    if (merging) status = '<div class="flex items-center gap-2 text-xs text-blue-800"><span class="w-3.5 h-3.5 border-2 border-blue-600 border-t-transparent rounded-full spin inline-block"></span>결합하고 있습니다... 데이터가 크면 시간이 걸릴 수 있습니다.' +
      '<span id="merge-job" class="text-blue-700/80">' + (mergeJob ? '(' + A.esc(mergeJob) + ')' : '') + '</span></div>';
    else if (mergeError) status = '<div class="text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-lg p-3">' + A.esc(mergeError) + '</div>';
    else if (merged && st) status = '<div class="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-3">선택한 데이터·열·키 매핑이 바뀌었습니다. [데이터 결합 실행]을 다시 눌러 주세요.</div>';
    else if (merged) {
      var warn = (merged.source_meta && merged.source_meta.warnings) || [];
      status = '<div class="text-xs text-emerald-800 bg-emerald-50 border border-emerald-200 rounded-lg p-3 flex items-center gap-2">' + A.icon('check-circle-2', 'w-4 h-4 shrink-0') +
        '<span>결합 완료: <strong>' + A.esc(merged.name) + '</strong> · ' + A.num(merged.n_rows) + '행 × ' + merged.n_cols + '열. 이 결과가 분석 대상입니다.</span></div>' +
        (warn.length ? '<div class="mt-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg p-2.5">' + warn.map(A.esc).join('<br>') + '</div>' : '');
    }
    box.innerHTML = '<div><h3 class="text-title font-semibold text-ink">데이터 결합</h3>' +
        '<p class="text-xs text-ink-3 mt-1">키가 같은 행끼리 옆으로 붙입니다. 데이터셋마다 키로 쓸 열을 고르세요. 이름이 달라도 됩니다 (예: 학교코드 = SCHUL_CODE).</p></div>' +
      '<div class="space-y-3">' + rows +
        '<button type="button" data-addkey="1" class="text-body font-semibold text-link hover:underline cursor-pointer">+ 키 추가</button></div>' +
      '<div class="flex flex-col lg:flex-row lg:items-end justify-between gap-3 pt-3 border-t border-paper-2">' +
        '<div class="flex flex-col sm:flex-row sm:items-center gap-x-5 gap-y-2 text-body">' +
          '<label class="flex items-center gap-2"><span class="text-ink-2 font-semibold shrink-0">남길 행</span><select data-m="how" class="min-w-0 ' + fieldCls() + '">' +
            JOIN_TYPES.map(function (j) { return '<option value="' + j[0] + '"' + (mcfg.how === j[0] ? ' selected' : '') + '>' + j[1] + ' (' + j[0] + ')</option>'; }).join('') + '</select></label>' +
          '<label class="flex items-center gap-2"><span class="text-ink-2 font-semibold shrink-0">결합 데이터셋 이름</span><input type="text" data-m="name" value="' + A.esc(mcfg.name) + '" class="w-full sm:w-64 ' + fieldCls() + '"></label></div>' +
        '<div class="flex flex-wrap items-center lg:justify-end gap-x-4 gap-y-2">' +
          (prob && !merging ? '<span class="text-xs text-ink-3">' + A.esc(prob) + '</span>' : '') +
          '<button type="button" id="btn-merge" ' + (merging || prob ? 'disabled ' : '') + 'class="px-5 py-2 bg-brand hover:bg-brand-dark disabled:bg-rule-3 disabled:cursor-not-allowed text-white text-body font-bold rounded-xl flex items-center gap-1.5 cursor-pointer shrink-0 whitespace-nowrap"' + (prob ? ' title="' + A.esc(prob) + '"' : '') + '>' + A.icon('combine', 'w-3.5 h-3.5') + '<span>데이터 결합 실행</span></button></div></div>' +
      status;
  }
  function runMerge() {
    var body = buildMerge(), sig = JSON.stringify(body);
    merging = true; mergeError = null; mergeJob = ''; renderMerge();
    A.post('/api/v1/datasets/merge', body, { onJob: function (j) {
      mergeJob = A.jobText(j);
      var el = document.getElementById('merge-job');
      if (el) el.textContent = mergeJob ? '(' + mergeJob + ')' : '';
    } }).then(function (d) {
      merged = d; mergedSig = sig; merging = false; mergeJob = '';
      activeId = MERGED_TAB;
      changed();
      loadDatasets();
    }).catch(function (e) { merging = false; mergeError = '결합에 실패했습니다: ' + e.message; renderMerge(); A.icons(); });
  }

  /* ---------------- 미리보기 ---------------- */
  function previewTarget() { return activeId === MERGED_TAB ? merged : ((find(activeId) || {}).d || null); }
  function loadPreview() {
    var cur = previewTarget();
    if (!cur || preview.loading) return;
    if (preview.dsId !== cur.id) preview = { dsId: cur.id, rows: [], cols: [], total: cur.n_rows, loading: false };
    if (preview.rows.length >= preview.total && preview.rows.length > 0) { renderPreview(); return; }
    preview.loading = true;
    var more = A.$('#preview-more');
    more.classList.remove('hidden'); more.classList.add('flex');
    var id = cur.id;
    A.get('/api/v1/datasets/' + encodeURIComponent(id) + '/preview' + A.qs({ limit: PAGE, offset: preview.rows.length })).then(function (r) {
      preview.loading = false;
      more.classList.add('hidden'); more.classList.remove('flex');
      if (!previewTarget() || previewTarget().id !== id) return;
      preview.rows = preview.rows.concat(r.rows || []);
      preview.cols = r.columns || preview.cols;
      preview.total = r.total_rows;
      renderPreview();
    }).catch(function (e) { preview.loading = false; more.classList.add('hidden'); more.classList.remove('flex'); A.fail(e.message, '#preview-scroll'); });
  }
  function renderPreview() {
    var cur = previewTarget();
    if (!cur) { A.$('#preview-name').textContent = ''; A.$('#preview-count').textContent = ''; A.$('#preview-head').innerHTML = ''; A.$('#preview-body').innerHTML = ''; return; }
    var s = activeId === MERGED_TAB ? null : find(activeId);
    var cols = preview.cols.filter(function (c) { return !s || s.use[c]; });   // 분석에 쓰는 열만
    A.$('#preview-name').textContent = cur.name;
    A.$('#preview-count').textContent = '(' + preview.rows.length + ' / ' + A.num(preview.total) + ' 행 · ' + cols.length + '열 표출)';
    A.$('#preview-head').innerHTML = '<tr class="text-ink-2 text-xs font-semibold"><th class="py-2 px-3 text-ink-4 w-10 text-center font-mono">#</th>' +
      cols.map(function (c) { return '<th class="py-2 px-3 text-ink-0 whitespace-nowrap">' + A.esc(c) + '</th>'; }).join('') + '</tr>';
    A.$('#preview-body').innerHTML = preview.rows.map(function (r, i) {
      return '<tr class="hover:bg-paper-3/70 transition-colors"><td class="py-1.5 px-3 text-ink-4 text-center">' + (i + 1) + '</td>' +
        cols.map(function (c) { var v = r[c]; return '<td class="py-1.5 px-3 truncate max-w-[160px] whitespace-nowrap text-ink-1">' + (v === null || v === undefined ? '' : A.esc(v)) + '</td>'; }).join('') + '</tr>';
    }).join('');
  }

  function setMsg(t) {
    var m = A.$('#s1-msg');
    m.textContent = t || '';
    m.classList.toggle('hidden', !t);
  }

  /** 상단 '현재 분석 대상'과 하단 '분석 투입 대상'·진행 버튼 */
  function renderFooter() {
    var t = target();
    A.$('#s1-current-name').textContent = t ? t.name : (sel.length >= 2 ? '결합 필요' : '선택 안 됨');
    var label;
    if (!sel.length) label = '없음';
    else if (sel.length === 1) label = t.name + ' (' + A.num(t.n_rows) + '행' + (isSubset(sel[0]) ? ', ' + usedList(sel[0]).length + '개 열 사용' : '') + ')';
    else label = t ? t.name + ' (결합 결과 ' + A.num(t.n_rows) + '행 × ' + t.n_cols + '열)' : '데이터 ' + sel.length + '개 선택됨 — 결합을 실행해야 진행할 수 있습니다';
    A.$('#s1-target-name').textContent = label;
    A.$('#s1-target-wrap').classList.toggle('hidden', !sel.length);   // 선택 전에는 '없음'을 보여주지 않는다
    A.$('#btn-proceed').disabled = !t;
  }

  function renderAll() {
    renderFooter();
    renderCards();
    renderDatasets();
    renderTabs();
    renderColumns();
    renderMerge();
    if (previewTarget()) loadPreview(); else renderPreview();
    A.icons();
  }

  /* ---------------- 이벤트 ---------------- */
  document.addEventListener('DOMContentLoaded', function () {
    A.$('#mgmt-search').addEventListener('input', A.debounce(loadCards, 300));
    A.$('#col-search').addEventListener('input', renderColumns);
    A.$('#mgmt-sync').addEventListener('click', syncCards);
    A.$('#mgmt-list').addEventListener('click', function (e) {
      var c = e.target.closest('[data-card]');
      if (c) toggle('card', c.getAttribute('data-card'));
    });
    A.$('#ds-list').addEventListener('click', function (e) {
      var del = e.target.closest('[data-del]');
      if (del) {
        var id = del.getAttribute('data-del');
        A.confirm('이 데이터셋과 관련 분석 결과를 삭제할까요?').then(function (ok) {
          if (!ok) return;
          return A.del('/api/v1/datasets/' + encodeURIComponent(id)).then(function () {
          if (find(id)) remove(id);
          if (merged && merged.id === id) { merged = null; mergedSig = null; }
          return loadDatasets().then(renderAll);
          }).catch(function (err) { A.fail(err.message, '#ds-list'); });
        });
        return;
      }
      var c = e.target.closest('[data-ds]');
      if (c) toggle('dataset', c.getAttribute('data-ds'));
    });

    A.$('#s1-tabs').addEventListener('click', function (e) {
      var rm = e.target.closest('[data-remove]');
      if (rm) { remove(rm.getAttribute('data-remove')); return; }
      var b = e.target.closest('[data-tab]');
      if (!b) return;
      activeId = b.getAttribute('data-tab');
      preview = { dsId: null, rows: [], cols: [], total: 0, loading: false };
      renderAll();
    });

    // 열 사용 체크 / 전체 / 타입 변경
    A.$('#col-body').addEventListener('change', function (e) {
      var s = find(activeId);
      var u = e.target.closest('input[data-use]');
      if (u && s) { s.use[u.getAttribute('data-use')] = u.checked; changed(); return; }
      var tsel = e.target.closest('select[data-col]');
      if (!tsel || !s) return;
      A.patch('/api/v1/datasets/' + encodeURIComponent(s.id) + '/columns/types', { columns: [{ name: tsel.getAttribute('data-col'), role: tsel.value }] }).then(function (d) {
        s.d = d;
        renderColumns();
      }).catch(function (err) { A.fail(err.message, '#col-card'); renderColumns(); });
    });
    A.$('#col-all').addEventListener('change', function () {
      var s = find(activeId);
      if (!s) return;
      var on = this.checked;
      var q = (A.$('#col-search').value || '').toLowerCase();
      colsOf(s).forEach(function (c) { if (c.name.toLowerCase().indexOf(q) >= 0) s.use[c.name] = on; });   // 검색 중이면 보이는 열만
      changed();
    });

    // 결합 설정
    var mc = A.$('#merge-card');
    mc.addEventListener('change', function (e) {
      var t = e.target;
      if (t.getAttribute('data-m') === 'how') { mcfg.how = t.value; changed(); }
      else if (t.hasAttribute('data-key')) {
        var k = mcfg.keys[+t.getAttribute('data-key')];
        k[t.getAttribute('data-ds')] = t.value;
        if (t.getAttribute('data-ds') === sel[0].id) autofillKeys();
        changed();
      }
    });
    mc.addEventListener('input', A.debounce(function (e) {
      var t = e.target;
      if (t.getAttribute('data-m') === 'name') { mcfg.name = t.value; mcfg.nameTouched = true; }
      else return;
      // 입력 중 포커스를 잃지 않도록 결합 설정 영역은 다시 그리지 않고, 분석 대상·탭만 갱신
      syncTarget();
      renderFooter();
      renderTabs(); A.icons();
    }, 250));
    mc.addEventListener('click', function (e) {
      if (e.target.closest('[data-addkey]')) { mcfg.keys.push({}); changed(); return; }
      var dk = e.target.closest('[data-delkey]');
      if (dk) { mcfg.keys.splice(+dk.getAttribute('data-delkey'), 1); changed(); return; }
      if (e.target.closest('#btn-merge')) runMerge();
    });

    // 업로드
    var ua = A.$('#upload-area');
    ua.addEventListener('change', function (e) { if (e.target.id === 'file-input' && e.target.files.length) handleFile(e.target.files[0]); });
    ua.addEventListener('dragover', function (e) { if (e.target.closest('#dropzone')) { e.preventDefault(); if (!dragging) { dragging = true; renderUpload(); } } });
    ua.addEventListener('dragleave', function (e) { if (e.target.closest('#dropzone') && dragging) { dragging = false; renderUpload(); } });
    ua.addEventListener('drop', function (e) {
      if (!e.target.closest('#dropzone')) return;
      e.preventDefault(); dragging = false;
      if (e.dataTransfer.files.length) handleFile(e.dataTransfer.files[0]);
    });

    A.$('#preview-scroll').addEventListener('scroll', function () {
      var el = this;
      if (el.scrollHeight - el.scrollTop <= el.clientHeight + 50 && preview.rows.length < preview.total) loadPreview();
    });
    A.$('#btn-proceed').addEventListener('click', function () {
      if (!target() || proceeding) return;
      syncTarget();
      if (sel.length !== 1 || !isSubset(sel[0])) { location.href = A.ctx + '/analysis/step2'; return; }
      // 데이터셋 하나에서 일부 열만 쓰는 경우: 그 열만 담은 새 데이터셋(source_type=subset)을 만들어 이후 단계에 쓴다
      var s = sel[0], b = this, label = b.querySelector('span');
      proceeding = true; b.disabled = true; setMsg('');
      label.textContent = '변수 선택 적용 중...';
      A.post('/api/v1/datasets/' + encodeURIComponent(s.id) + '/subset', { columns: usedList(s) }, { onJob: function (j) { var t = A.jobText(j); label.textContent = '변수 선택 적용 중' + (t ? ' · ' + t : '...'); } }).then(function (d) {
        A.saveState({ datasetId: d.id, datasetName: d.name, datasetRows: d.n_rows, usedColumns: null, rawDatasetId: null, analysisId: null });
        location.href = A.ctx + '/analysis/step2';
      }).catch(function (e) {
        proceeding = false; b.disabled = false; label.textContent = '2단계 품질 및 전처리 진행';
        setMsg('변수 선택을 적용하지 못했습니다: ' + e.message);
      });
    });

    renderUpload();
    // 초기 로딩: 목록만 불러온다. 이전 선택은 복원하지 않는다.
    Promise.all([loadCards(), loadDatasets()]).then(renderAll);
    A.icons();
  });
})();
