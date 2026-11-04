/* 관리자 화면(초안). 데이터는 admin-mock.js 의 목업. 실제 연결 시 아래 api 객체만 fetch('/api/v1/admin/...') 로 바꾼다.
 * 이 파일은 서비스 화면의 공통 스크립트(common.js 등)를 쓰지 않는다. */
(function () {
  'use strict';
  var M = window.AdminMock;
  var $ = function (s, r) { return (r || document).querySelector(s); };
  var esc = function (v) { return String(v == null ? '' : v).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); };
  var TOKEN_KEY = 'usa_admin_token';
  var PENDING_LIMIT = M.settings.job_pending_timeout_seconds;     // 이 시간보다 오래 pending 이면 강조
  var SLOW_LIMIT = 15 * 60;                                       // 이 시간보다 오래 running 이면 강조(초안 기준값)

  /* ---------- 데이터 접근 계층 (목업 → 실제 API 로 교체할 자리) ---------- */
  function wait(v) { return new Promise(function (res) { setTimeout(function () { res(v); }, 120); }); }
  var api = {
    dashboard: function () { return wait(M); },
    jobs: function () { return wait(M.jobs); },
    cancelJob: function (id) {
      var j = M.jobs.filter(function (x) { return x.id === id; })[0];
      if (j && (j.status === 'running' || j.status === 'pending' || j.status === 'queued')) j.status = 'cancelled';
      return wait(j);
    },
    sessions: function () { return wait(M.sessions); },
    killSession: function (id) {
      M.sessions = M.sessions.filter(function (s) { return s.id !== id; });
      M.jobs.forEach(function (j) { if (j.session === id && /running|pending|queued/.test(j.status)) j.status = 'cancelled'; });
      return wait(true);
    },
    cards: function () { return wait(M.cards); },
    syncCards: function (id) {
      M.cards.forEach(function (c) {
        if (id && c.id !== id) return;
        if (c.status === 'failed' && c.id === 'card_006') { c.error = '열 정의가 카드 정의와 다릅니다. (기대 12열 / 실제 11열)'; return; }
        c.status = 'loaded'; c.error = null; c.loaded_at = new Date().toISOString(); c.rows = c.rows || 1000;
      });
      return wait({ succeeded: M.cards.filter(function (c) { return c.status === 'loaded'; }).length, failed: M.cards.filter(function (c) { return c.status === 'failed'; }).length });
    },
    datasets: function () { return wait(M.datasets); },
    packages: function () { return wait(M.packages); },
    unsharePackage: function (id) { var p = M.packages.filter(function (x) { return x.id === id; })[0]; if (p) { p.shared = false; p.state = 'grace'; p.unshared_at = new Date().toISOString(); p.expires_at = new Date(Date.now() + M.settings.share_grace_period_days * 864e5).toISOString(); } return wait(p); },
    deletePackage: function (id) { M.packages = M.packages.filter(function (x) { return x.id !== id; }); return wait(true); },
    sweeper: function () { return wait(M.sweeper); },
    runSweep: function () {
      M.sweeper.last_run_at = new Date().toISOString();
      M.sweeper.last_result = { sessions_removed: 1, datasets_removed: 2, packages_removed: 0, files_removed: 9, freed_mb: 311.2, duration_s: 2.1 };
      return wait(M.sweeper);
    },
    config: function () { return wait(M.config); }
  };

  /* ---------- 공통 도우미 ---------- */
  function fmtTime(iso) { if (!iso) return '-'; var d = new Date(iso); var p = function (n) { return String(n).padStart(2, '0'); }; return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate()) + ' ' + p(d.getHours()) + ':' + p(d.getMinutes()); }
  function fmtAgo(iso) {
    if (!iso) return '-';
    var s = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 1000));
    if (s < 60) return s + '초 전'; if (s < 3600) return Math.floor(s / 60) + '분 전'; if (s < 86400) return Math.floor(s / 3600) + '시간 전';
    return Math.floor(s / 86400) + '일 전';
  }
  function fmtDur(sec) { sec = Math.round(sec || 0); if (sec < 60) return sec + '초'; if (sec < 3600) return Math.floor(sec / 60) + '분 ' + (sec % 60) + '초'; return Math.floor(sec / 3600) + '시간 ' + Math.floor(sec % 3600 / 60) + '분'; }
  function fmtNum(n) { return Number(n).toLocaleString('ko-KR'); }
  function fmtMb(mb) { return mb >= 1024 ? (mb / 1024).toFixed(1) + ' GB' : mb.toFixed(1) + ' MB'; }
  function dday(iso) { var d = Math.ceil((new Date(iso).getTime() - Date.now()) / 864e5); return d < 0 ? Math.abs(d) + '일 지남' : d === 0 ? '오늘' : 'D-' + d; }
  var toastTimer;
  function toast(msg, kind) {
    var t = $('#toast'); $('#toast-msg', t).textContent = msg; t.dataset.kind = kind === 'error' ? 'error' : 'ok'; t.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(function () { t.hidden = true; }, kind === 'error' ? 5000 : 3000);
  }
  function confirmBox(msg, okLabel) {
    return new Promise(function (resolve) {
      var m = $('#modal'), yes = $('#modal-yes'), no = $('#modal-no'), back = document.activeElement;
      $('#modal-msg').textContent = msg; yes.textContent = okLabel || '확인'; m.hidden = false; no.focus();
      function done(v) { m.hidden = true; yes.onclick = no.onclick = null; document.removeEventListener('keydown', key); if (back && back.focus) back.focus(); resolve(v); }
      function key(e) { if (e.key === 'Escape') done(false); }
      yes.onclick = function () { done(true); }; no.onclick = function () { done(false); };
      m.onclick = function (e) { if (e.target === m) done(false); };
      document.addEventListener('keydown', key);
    });
  }
  function chip(text, cls) { return '<span class="chip ' + (cls || '') + '">' + esc(text) + '</span>'; }
  function table(head, rows, opts) {
    opts = opts || {};
    if (!rows.length) return '<div class="empty">' + esc(opts.empty || '표시할 항목이 없습니다.') + '</div>';
    return '<div class="table-wrap"><table><thead><tr>' + head.join('') + '</tr></thead><tbody>' + rows.join('') + '</tbody></table></div>';
  }

  var KIND = { ingest: '반입', profile: '프로파일링', merge: '결합', analysis: '분석', package_export: '내보내기', sync_data_cards: '카드 동기화' };
  var JSTATUS = { queued: ['대기열', 'info'], pending: ['대기', 'warn'], running: ['실행 중', 'info'], succeeded: ['성공', 'ok'], failed: ['실패', 'bad'], cancelled: ['취소', ''] };
  var SOURCE = { upload: '업로드', data_card: '데이터관리카드', merged: '결합', preprocessed: '전처리' };

  /* ---------- 화면별 렌더 ---------- */
  var views = {};

  views.dashboard = {
    title: '대시보드', lead: '서비스 상태를 한눈에 봅니다.',
    render: function (el) {
      return api.dashboard().then(function (d) {
        var active = d.sessions.filter(function (s) { return s.status === 'active'; }).length;
        var by = { queued: 0, pending: 0, running: 0, failed: 0 };
        d.jobs.forEach(function (j) { if (by[j.status] != null) by[j.status]++; });
        var st = d.storage, pct = Math.round(st.used_gb / st.total_gb * 100), hours = d.failuresPerHour();
        var fail24 = hours.reduce(function (n, v) { return n + v; }, 0);
        var max = Math.max.apply(null, hours.concat([1]));
        el.innerHTML =
          '<div class="grid cols-4">' +
          kpi('활성 세션', fmtNum(active), '전체 ' + d.sessions.length + '개') +
          kpi('최근 24시간 실패', fmtNum(fail24), '작업 기준', fail24 > 0 ? 'bad' : 'ok') +
          kpi('실행 중 작업', fmtNum(by.running), '대기 ' + by.pending + ' · 대기열 ' + by.queued) +
          kpi('저장소 사용량', pct + '%', st.used_gb + ' / ' + st.total_gb + ' GB', pct >= 80 ? 'bad' : '') + '</div>' +
          '<div class="grid cols-2" style="margin-top:16px">' +
          '<section class="card"><div class="card-head"><h2>상태별 작업 수</h2></div><div class="rows">' +
          [['queued', '대기열 (queued)'], ['pending', '대기 (pending)'], ['running', '실행 중 (running)'], ['failed', '실패 (failed)']].map(function (r) {
            return '<div class="row"><span class="l">' + r[1] + '</span><span class="r">' + chip(by[r[0]] + '건', r[0] === 'failed' && by.failed ? 'bad' : '') + '</span></div>'; }).join('') + '</div></section>' +
          '<section class="card"><div class="card-head"><h2>시스템 상태</h2></div><div class="rows">' +
          health('워커', d.health.worker) + health('Redis 브로커', d.health.redis) +
          '<div class="row"><span class="l">저장소 경로</span><span class="r mono">' + esc(st.dir) + '</span></div></div>' +
          '<div class="bar' + (pct >= 80 ? ' warn' : '') + '" aria-hidden="true"><i style="width:' + pct + '%"></i></div>' +
          '<div class="row" style="border:0;padding:0"><span class="l">저장소</span><span class="r">' + st.used_gb + ' / ' + st.total_gb + ' GB (' + pct + '%)</span></div></section></div>' +
          '<section class="card"><div class="card-head"><h2>시간대별 실패 (최근 24시간)</h2><span class="sub">막대가 높을수록 실패가 많은 시간입니다</span></div>' +
          '<div class="spark" role="img" aria-label="시간대별 실패 건수">' + hours.map(function (n) { return '<i class="' + (n >= 3 ? 'hot' : '') + '" style="height:' + Math.max(4, n / max * 100) + '%" title="' + n + '건"></i>'; }).join('') + '</div></section>';
      });
      function kpi(k, v, s, cls) { return '<div class="kpi"><div class="k">' + k + '</div><div class="v ' + (cls || '') + '">' + v + '</div><div class="s">' + s + '</div></div>'; }
      function health(n, h) { return '<div class="row"><span class="l">' + n + '</span><span class="r"><span class="dot ' + (h.ok ? '' : 'bad') + '"></span>' + esc(h.detail) + '</span></div>'; }
    }
  };

  views.jobs = {
    title: '작업 모니터링', lead: '전체 세션의 작업을 조건별로 보고, 오래 걸리는 작업을 찾아 취소합니다.',
    render: function (el) {
      var f = { kind: '', status: '', session: '', min: '' }, sel = null, data = [];
      function slow(j) { return (j.status === 'pending' || j.status === 'queued') ? (Date.now() - new Date(j.created).getTime()) / 1000 > PENDING_LIMIT : (j.status === 'running' && j.elapsed_s > SLOW_LIMIT); }
      function paint() {
        var rows = data.filter(function (j) {
          return (!f.kind || j.kind === f.kind) && (!f.status || j.status === f.status) && (!f.session || j.session.indexOf(f.session) >= 0) && (!f.min || j.elapsed_s >= Number(f.min) * 60);
        });
        $('#jobs-body', el).innerHTML = table(['<th>작업</th>', '<th>종류</th>', '<th>상태</th>', '<th>세션</th>', '<th class="num">소요</th>', '<th>생성</th>', '<th></th>'],
          rows.map(function (j) {
            var s = JSTATUS[j.status], flag = slow(j) ? (j.status === 'running' ? chip('오래 걸림', 'bad') : chip('대기 지연', 'bad')) : '';
            return '<tr data-id="' + j.id + '" class="' + (slow(j) ? 'is-alert ' : '') + (sel === j.id ? 'is-selected' : '') + '">' +
              '<td><div>' + esc(j.title) + '</div><div class="mono" style="color:var(--ink-3)">' + j.id + '</div></td><td>' + esc(KIND[j.kind] || j.kind) + '</td>' +
              '<td>' + chip(s[0], s[1]) + ' ' + flag + '</td><td class="mono">' + j.session + '</td><td class="num">' + (j.elapsed_s ? fmtDur(j.elapsed_s) : '-') + '</td><td>' + fmtAgo(j.created) + '</td>' +
              '<td><button type="button" class="btn btn-ghost btn-sm" data-detail="' + j.id + '">상세</button></td></tr>';
          }), { empty: '조건에 맞는 작업이 없습니다.' });
        var j = data.filter(function (x) { return x.id === sel; })[0];
        $('#job-detail', el).innerHTML = j ? detail(j) : '';
      }
      function detail(j) {
        var s = JSTATUS[j.status], cancelable = /running|pending|queued/.test(j.status);
        return '<section class="card detail"><div class="card-head"><h2>작업 상세</h2>' + chip(s[0], s[1]) + '</div><dl>' +
          '<dt>작업 ID</dt><dd class="mono">' + j.id + '</dd><dt>이름</dt><dd>' + esc(j.title) + '</dd><dt>종류</dt><dd>' + esc(KIND[j.kind] || j.kind) + ' <span class="mono">(' + j.kind + ')</span></dd>' +
          '<dt>세션</dt><dd class="mono">' + j.session + '</dd><dt>생성 / 시작</dt><dd>' + fmtTime(j.created) + ' / ' + fmtTime(j.started) + '</dd><dt>소요 시간</dt><dd>' + (j.elapsed_s ? fmtDur(j.elapsed_s) : '-') + '</dd></dl>' +
          (j.error ? '<div class="errbox"><strong>' + esc(j.error.code) + '</strong>' + (j.error.reason ? ' · 실패 원인: ' + esc(j.error.reason) : '') + '\n' + esc(j.error.message) + '</div>' : '') +
          '<div class="actions">' + (cancelable ? '<button type="button" class="btn btn-danger" data-cancel="' + j.id + '">강제 취소</button>' : '') + '<button type="button" class="btn btn-ghost" data-close>닫기</button></div></section>';
      }
      el.innerHTML = '<div class="filters">' +
        '<select data-f="kind" aria-label="종류"><option value="">종류 전체</option>' + Object.keys(KIND).map(function (k) { return '<option value="' + k + '">' + KIND[k] + '</option>'; }).join('') + '</select>' +
        '<select data-f="status" aria-label="상태"><option value="">상태 전체</option>' + Object.keys(JSTATUS).map(function (k) { return '<option value="' + k + '">' + JSTATUS[k][0] + '</option>'; }).join('') + '</select>' +
        '<input data-f="session" placeholder="세션 ID" aria-label="세션 ID"><input data-f="min" type="number" min="0" placeholder="소요 N분 이상" aria-label="소요 시간(분) 이상"></div>' +
        '<div id="jobs-body"></div><div id="job-detail"></div>';
      el.addEventListener('input', function (e) { var k = e.target.dataset.f; if (k) { f[k] = e.target.value; paint(); } });
      el.addEventListener('click', function (e) {
        var d = e.target.closest('[data-detail]'), c = e.target.closest('[data-cancel]'), x = e.target.closest('[data-close]'), tr = e.target.closest('tr[data-id]');
        if (d || (tr && !c && !x)) { sel = (d || tr).dataset.detail || tr.dataset.id; paint(); }
        if (x) { sel = null; paint(); }
        if (c) confirmBox('이 작업을 강제로 취소할까요?\n실행 중인 작업은 즉시 중단됩니다.', '강제 취소').then(function (ok) {
          if (ok) api.cancelJob(c.dataset.cancel).then(function () { return api.jobs(); }).then(function (r) { data = r; paint(); toast('작업을 취소했습니다.'); });
        });
      });
      return api.jobs().then(function (r) { data = r; paint(); });
    }
  };

  views.sessions = {
    title: '세션 관리', lead: '활성 세션과 보유 자원을 확인하고, 필요하면 강제 종료합니다.',
    render: function (el) {
      function paint(list) {
        var order = { active: 0, idle: 1, expired: 2 }, label = { active: ['활성', 'ok'], idle: ['유휴', 'warn'], expired: ['만료', ''] };
        list = list.slice().sort(function (a, b) { return order[a.status] - order[b.status]; });
        el.innerHTML = table(['<th>세션</th>', '<th>상태</th>', '<th>마지막 heartbeat</th>', '<th class="num">데이터셋</th>', '<th class="num">작업</th>', '<th></th>'],
          list.map(function (s) { return '<tr><td class="mono">' + s.id + '</td><td>' + chip(label[s.status][0], label[s.status][1]) + '</td><td>' + fmtAgo(s.last_heartbeat) + '</td><td class="num">' + s.datasets + '</td><td class="num">' + s.jobs + '</td>' +
            '<td style="text-align:right"><button type="button" class="btn btn-danger btn-sm" data-kill="' + s.id + '">강제 종료</button></td></tr>'; }), { empty: '세션이 없습니다.' });
      }
      el.onclick = function (e) {
        var k = e.target.closest('[data-kill]'); if (!k) return;
        confirmBox('세션 ' + k.dataset.kill + '을(를) 강제 종료할까요?\n이 세션의 데이터셋과 진행 중인 작업이 함께 정리됩니다.', '강제 종료').then(function (ok) {
          if (ok) api.killSession(k.dataset.kill).then(function () { return api.sessions(); }).then(function (l) { paint(l); toast('세션을 종료했습니다.'); });
        });
      };
      return api.sessions().then(paint);
    }
  };

  views.cards = {
    title: '데이터관리카드', lead: '카드 정의와 적재 상태를 확인하고 수동으로 동기화합니다.',
    render: function (el) {
      var last = '';
      function paint(list) {
        var st = { loaded: ['적재 완료', 'ok'], loading: ['적재 중', 'info'], failed: ['실패', 'bad'] };
        var ok = list.filter(function (c) { return c.status === 'loaded'; }).length, bad = list.filter(function (c) { return c.status === 'failed'; }).length;
        el.innerHTML = '<div class="filters" style="justify-content:space-between;align-items:center"><span>전체 ' + list.length + '건 · 적재 ' + ok + ' · 실패 ' + bad + '</span>' +
          '<button type="button" class="btn btn-primary" data-sync-all>전체 동기화</button></div>' +
          table(['<th>카드</th>', '<th>상태</th>', '<th class="num">행 수</th>', '<th>마지막 적재</th>', '<th>실패 사유</th>', '<th></th>'],
            list.map(function (c) { return '<tr><td>' + esc(c.name) + '</td><td>' + chip(st[c.status][0], st[c.status][1]) + '</td><td class="num">' + (c.rows ? fmtNum(c.rows) : '-') + '</td><td>' + (c.loaded_at ? fmtTime(c.loaded_at) + ' <span style="color:var(--ink-3)">(' + fmtAgo(c.loaded_at) + ')</span>' : '-') + '</td>' +
              '<td style="color:var(--bad)">' + esc(c.error || '') + '</td><td style="text-align:right"><button type="button" class="btn btn-ghost btn-sm" data-sync="' + c.id + '"' + (c.status === 'loading' ? ' disabled' : '') + '>다시 적재</button></td></tr>'; })) +
          (last ? '<div class="log">' + esc(last) + '</div>' : '');
      }
      function run(id) {
        toast('동기화를 실행합니다…');
        api.syncCards(id).then(function (r) { last = fmtTime(new Date().toISOString()) + ' 동기화 결과: 성공 ' + r.succeeded + '건, 실패 ' + r.failed + '건'; return api.cards(); })
          .then(function (l) { paint(l); toast(last.indexOf('실패 0건') > 0 ? '동기화를 마쳤습니다.' : '일부 카드를 불러오지 못했습니다.', last.indexOf('실패 0건') > 0 ? '' : 'error'); });
      }
      el.onclick = function (e) {
        var a = e.target.closest('[data-sync-all]'), o = e.target.closest('[data-sync]');
        if (a) run(); else if (o) run(o.dataset.sync);
      };
      return api.cards().then(paint);
    }
  };

  views.storage = {
    title: '데이터셋·패키지', lead: '용량을 많이 차지하는 항목을 찾고, 공유 중인 패키지를 정리합니다.',
    render: function (el) {
      var sort = { key: 'size_mb', dir: -1 }, ds = [], pk = [];
      function paint() {
        var list = ds.slice().sort(function (a, b) { var x = a[sort.key], y = b[sort.key]; return (x > y ? 1 : x < y ? -1 : 0) * sort.dir; });
        var total = ds.reduce(function (n, d) { return n + d.size_mb; }, 0), st = { ready: ['준비됨', 'ok'], building: ['생성 중', 'info'], failed: ['실패', 'bad'] };
        function th(k, label, cls) { return '<th class="sortable ' + (cls || '') + '" data-sort="' + k + '"' + (sort.key === k ? ' aria-sort="' + (sort.dir < 0 ? 'descending' : 'ascending') + '"' : '') + '>' + label + '</th>'; }
        var pst = { shared: ['공유 중', 'info'], grace: ['유예 중', 'warn'], expired: ['삭제 대상', 'bad'] };
        el.innerHTML = '<section class="card"><div class="card-head"><h2>데이터셋</h2><span class="sub">전체 ' + ds.length + '개 · 합계 ' + fmtMb(total) + '</span></div>' +
          table([th('name', '이름'), th('source', '출처'), th('size_mb', '크기', 'num'), th('status', '상태'), th('session', '소유 세션')],
            list.map(function (d) { return '<tr><td>' + esc(d.name) + '</td><td>' + esc(SOURCE[d.source] || d.source) + '</td><td class="num">' + fmtMb(d.size_mb) + '</td><td>' + chip(st[d.status][0], st[d.status][1]) + '</td><td class="mono">' + d.session + '</td></tr>'; })) + '</section>' +
          '<section class="card"><div class="card-head"><h2>패키지</h2><span class="sub">공유 해제 후 ' + M.settings.share_grace_period_days + '일 유예 뒤 삭제 대상이 됩니다</span></div>' +
          table(['<th>이름</th>', '<th>상태</th>', '<th class="num">크기</th>', '<th>만료 예정</th>', '<th>소유 세션</th>', '<th></th>'],
            pk.map(function (p) { return '<tr><td>' + esc(p.name) + '</td><td>' + chip(pst[p.state][0], pst[p.state][1]) + '</td><td class="num">' + fmtMb(p.size_mb) + '</td>' +
              '<td>' + (p.expires_at ? fmtTime(p.expires_at) + ' <span style="color:' + (p.state === 'expired' ? 'var(--bad)' : 'var(--ink-3)') + '">(' + dday(p.expires_at) + ')</span>' : '-') + '</td><td class="mono">' + p.session + '</td>' +
              '<td style="text-align:right;white-space:nowrap">' + (p.shared ? '<button type="button" class="btn btn-ghost btn-sm" data-unshare="' + p.id + '">공유 해제</button> ' : '') + '<button type="button" class="btn btn-danger btn-sm" data-del="' + p.id + '">삭제</button></td></tr>'; }),
            { empty: '패키지가 없습니다.' }) + '</section>';
      }
      function load() { return Promise.all([api.datasets(), api.packages()]).then(function (r) { ds = r[0]; pk = r[1]; paint(); }); }
      el.onclick = function (e) {
        var s = e.target.closest('[data-sort]'), u = e.target.closest('[data-unshare]'), d = e.target.closest('[data-del]');
        if (s) { var k = s.dataset.sort; sort = { key: k, dir: sort.key === k ? -sort.dir : (k === 'size_mb' ? -1 : 1) }; paint(); }
        if (u) confirmBox('이 패키지의 공유를 해제할까요?\n해제 후 ' + M.settings.share_grace_period_days + '일이 지나면 삭제 대상이 됩니다.', '공유 해제').then(function (ok) { if (ok) api.unsharePackage(u.dataset.unshare).then(load).then(function () { toast('공유를 해제했습니다.'); }); });
        if (d) confirmBox('이 패키지를 삭제할까요?\n삭제하면 되돌릴 수 없습니다.', '삭제').then(function (ok) { if (ok) api.deletePackage(d.dataset.del).then(load).then(function () { toast('패키지를 삭제했습니다.'); }); });
      };
      return load();
    }
  };

  views.sweeper = {
    title: '정리(sweeper)', lead: '만료된 세션·데이터셋·패키지를 정리하는 작업의 실행 상태입니다.',
    render: function (el) {
      function paint(s) {
        var r = s.last_result;
        el.innerHTML = '<section class="card"><div class="card-head"><h2>마지막 실행 (usa.sweep)</h2><button type="button" class="btn btn-primary" data-run>지금 실행</button></div>' +
          '<div class="rows"><div class="row"><span class="l">실행 주기</span><span class="r">' + esc(s.schedule) + '</span></div>' +
          '<div class="row"><span class="l">마지막 실행</span><span class="r">' + fmtTime(s.last_run_at) + ' (' + fmtAgo(s.last_run_at) + ')</span></div>' +
          '<div class="row"><span class="l">소요 시간</span><span class="r">' + r.duration_s + '초</span></div></div></section>' +
          '<section class="card"><div class="card-head"><h2>결과</h2></div><div class="grid cols-4">' +
          [['삭제한 세션', r.sessions_removed + '개'], ['삭제한 데이터셋', r.datasets_removed + '개'], ['삭제한 패키지', r.packages_removed + '개'], ['확보한 용량', fmtMb(r.freed_mb)]].map(function (k) {
            return '<div class="kpi"><div class="k">' + k[0] + '</div><div class="v">' + k[1] + '</div></div>'; }).join('') + '</div></section>';
      }
      el.onclick = function (e) {
        if (!e.target.closest('[data-run]')) return;
        confirmBox('지금 정리 작업을 실행할까요?\n만료된 항목이 바로 삭제됩니다.', '실행').then(function (ok) { if (ok) api.runSweep().then(function (s) { paint(s); toast('정리를 마쳤습니다.'); }); });
      };
      return api.sweeper().then(paint);
    }
  };

  views.settings = {
    title: '설정 조회', lead: '현재 적용 중인 설정 값입니다. 읽기 전용이며 민감한 값은 가려 두었습니다.',
    render: function (el) {
      return api.config().then(function (groups) {
        el.innerHTML = groups.map(function (g) {
          return '<section class="card"><div class="card-head"><h2>' + esc(g.group) + '</h2></div><div class="rows">' + g.items.map(function (i) {
            var v = i.secret ? '<button type="button" class="secret" data-secret="' + esc(i.key) + '" aria-label="' + esc(i.label) + ' 값 보기">••••••••••</button>' : esc(i.value);
            return '<div class="row"><span class="l">' + esc(i.label) + ' <span class="mono" style="color:var(--ink-3)">' + esc(i.key) + '</span></span><span class="r">' + v + '</span></div>';
          }).join('') + '</div></section>';
        }).join('');
        el.onclick = function (e) {
          var b = e.target.closest('[data-secret]'); if (!b) return;
          var item = [].concat.apply([], groups.map(function (g) { return g.items; })).filter(function (i) { return i.key === b.dataset.secret; })[0];
          var shown = b.classList.toggle('shown'); b.textContent = shown ? item.value : '••••••••••';
        };
      });
    }
  };

  /* ---------- 앱 골격 ---------- */
  var current = 'dashboard';
  function show(name) {
    current = views[name] ? name : 'dashboard';
    var v = views[current];
    $('#view-title').textContent = v.title; $('#view-lead').textContent = v.lead; document.title = v.title + ' | 이용자통계분석 관리자';
    [].forEach.call(document.querySelectorAll('#nav button'), function (b) { if (b.dataset.view === current) b.setAttribute('aria-current', 'page'); else b.removeAttribute('aria-current'); });
    var el = $('#view'); var fresh = el.cloneNode(false); el.parentNode.replaceChild(fresh, el);   // 이전 화면의 이벤트 정리
    fresh.innerHTML = '<div class="empty">불러오는 중…</div>';
    v.render(fresh).catch(function (e) { fresh.innerHTML = '<div class="empty">불러오지 못했습니다. ' + esc(e && e.message || '') + '</div>'; });
    if (location.hash !== '#' + current) history.replaceState(null, '', '#' + current);
  }
  function enter() { $('#gate').hidden = true; $('#app').hidden = false; show((location.hash || '').replace('#', '') || 'dashboard'); }
  function leave() { sessionStorage.removeItem(TOKEN_KEY); $('#app').hidden = true; $('#gate').hidden = false; $('#gate-token').value = ''; $('#gate-token').focus(); }

  $('#nav').addEventListener('click', function (e) { var b = e.target.closest('button[data-view]'); if (b) show(b.dataset.view); });
  $('#refresh').addEventListener('click', function () { show(current); });
  $('#logout').addEventListener('click', leave);
  $('#gate-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var t = $('#gate-token').value.trim(), err = $('#gate-error');
    if (!t) { err.textContent = '관리자 토큰을 입력해 주세요.'; err.hidden = false; return; }
    err.hidden = true; sessionStorage.setItem(TOKEN_KEY, t); enter();      // 초안: 값 검증 없음 (실제로는 서버가 토큰을 확인)
  });
  if (sessionStorage.getItem(TOKEN_KEY)) enter(); else { $('#gate').hidden = false; $('#gate-token').focus(); }
}());
