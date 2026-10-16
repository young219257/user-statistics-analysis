/* 교육데이터 이용자통계분석 서비스 - 공통 스크립트 (API 클라이언트 / 세션 토큰 / 헤더 / 모달 / 토스트) */
(function () {
  'use strict';

  var App = window.App = window.App || {};
  App.ctx = window.__CTX__ || '';

  /* ------------------------------------------------------------ 유틸 */
  App.esc = function (v) {
    if (v === null || v === undefined) return '';
    return String(v).replace(/[&<>"']/g, function (c) {
      return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
    });
  };
  App.num = function (v, d) {
    if (v === null || v === undefined || v === '' || isNaN(v)) return '-';
    return Number(v).toLocaleString('ko-KR', { minimumFractionDigits: d || 0, maximumFractionDigits: d === undefined ? 2 : d });
  };
  App.fix = function (v, d) {
    if (v === null || v === undefined || v === '' || isNaN(v)) return '-';
    return Number(v).toFixed(d === undefined ? 2 : d);
  };
  App.pFmt = function (p) {
    if (p === null || p === undefined || isNaN(p)) return '-';
    return p < 0.001 ? '< 0.001' : Number(p).toFixed(4);
  };
  App.date = function (iso) {
    if (!iso) return '-';
    var d = new Date(iso);
    if (isNaN(d.getTime())) return String(iso);
    function z(n) { return n < 10 ? '0' + n : String(n); }
    return d.getFullYear() + '-' + z(d.getMonth() + 1) + '-' + z(d.getDate()) + ' ' + z(d.getHours()) + ':' + z(d.getMinutes());
  };
  App.icons = function () {
    if (window.lucide && window.lucide.createIcons) window.lucide.createIcons();
  };
  /* design.md 색 토큰 값 읽기 (차트처럼 클래스를 못 쓰는 곳용): App.tok('ink-3') → '#6d7882' */
  var tokCache = {};
  App.tok = function (name) {
    if (!(name in tokCache)) tokCache[name] = getComputedStyle(document.documentElement).getPropertyValue('--color-' + name).trim();
    return tokCache[name];
  };
  App.icon = function (name, cls) {
    return '<i data-lucide="' + name + '" class="' + (cls || 'w-4 h-4') + '"></i>';
  };
  App.$ = function (sel, root) { return (root || document).querySelector(sel); };
  App.$$ = function (sel, root) { return Array.prototype.slice.call((root || document).querySelectorAll(sel)); };
  App.debounce = function (fn, ms) {
    var t;
    return function () {
      var a = arguments, c = this;
      clearTimeout(t);
      t = setTimeout(function () { fn.apply(c, a); }, ms);
    };
  };
  App.isNum = function (v) { return typeof v === 'number' && isFinite(v); };
  App.qs = function (obj) {
    var parts = [];
    Object.keys(obj || {}).forEach(function (k) {
      var v = obj[k];
      if (v === undefined || v === null || v === '') return;
      if (Array.isArray(v)) v.forEach(function (x) { parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(x)); });
      else parts.push(encodeURIComponent(k) + '=' + encodeURIComponent(v));
    });
    return parts.length ? '?' + parts.join('&') : '';
  };

  /* ------------------------------------------------------------ 브라우저 탭 상태 (sessionStorage) */
  var STATE_KEY = 'edu.state', TOKEN_KEY = 'edu.sessionToken';
  function readJson(key) {
    try { return JSON.parse(sessionStorage.getItem(key) || 'null'); } catch (e) { return null; }
  }
  App.state = readJson(STATE_KEY) || {};
  App.saveState = function (patch) {
    if (patch) Object.keys(patch).forEach(function (k) { App.state[k] = patch[k]; });
    try { sessionStorage.setItem(STATE_KEY, JSON.stringify(App.state)); } catch (e) { /* ignore */ }
    return App.state;
  };
  App.resetState = function () {
    App.state = {};
    try { sessionStorage.removeItem(STATE_KEY); } catch (e) { /* ignore */ }
  };

  /* ------------------------------------------------------------ 세션 토큰 (쿠키 저장) + API 클라이언트 */
  function getCookie(name) {
    var m = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()\[\]\\\/+^])/g, '\\$1') + '=([^;]*)'));
    return m ? decodeURIComponent(m[1]) : null;
  }
  function setCookie(name, value) {
    document.cookie = name + '=' + encodeURIComponent(value) + '; path=' + (App.ctx || '/') + '; SameSite=Lax';
  }
  function readCookieJson(name) {
    try { return JSON.parse(getCookie(name) || 'null'); } catch (e) { return null; }
  }

  var session = readCookieJson(TOKEN_KEY);        // { token, header }
  var issuing = null;

  function errMsg(body, status) {
    var d = body && body.detail;
    if (typeof d === 'string') return d;
    if (Array.isArray(d)) return d.map(function (x) { return (x.loc ? x.loc.slice(1).join('.') + ': ' : '') + (x.msg || ''); }).join(' / ');
    if (body && body.message) return body.message;
    return '요청 처리에 실패했습니다. (' + status + ')';
  }
  function stripHtml(s) {
    return String(s).replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim();
  }

  /** POST /api/v1/sessions — 토큰 발급 (쿠키에 보관, 브라우저의 모든 탭이 공유) */
  App.ensureSession = function (force) {
    if (session && session.token && !force) return Promise.resolve(session);
    if (issuing) return issuing;
    issuing = fetch(App.ctx + '/api/v1/sessions', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}', credentials: 'same-origin' })
      .then(function (res) {
        return res.json().catch(function () { return null; }).then(function (j) {
          if (!res.ok || !j || !j.session_token) throw new Error(errMsg(j, res.status));
          session = { token: j.session_token, header: j.token_header || 'X-Session-Token' };
          try { setCookie(TOKEN_KEY, JSON.stringify(session)); } catch (e) { /* ignore */ }
          if (force) App.resetState();
          return session;
        });
      })
      .then(function (s) { issuing = null; return s; }, function (e) { issuing = null; throw e; });
    return issuing;
  };

  function send(method, url, body, opts, retried) {
    return App.ensureSession().then(function (s) {
      var init = { method: method, headers: {}, credentials: 'same-origin' };
      init.headers[s.header] = s.token;
      if (body instanceof FormData) init.body = body;
      else if (body !== undefined && body !== null) {
        init.headers['Content-Type'] = 'application/json';
        init.body = JSON.stringify(body);
      }
      return fetch(App.ctx + url, init).then(function (res) {
        if (res.status === 401 && !retried) {           // 세션 만료 → 재발급 후 1회 재시도 (이전 세션의 데이터는 삭제된 상태)
          return App.ensureSession(true).then(function () {
            return send(method, url, body, opts, true);
          });
        }
        if (opts.raw) return res;
        if (res.status === 204) return null;
        var ct = res.headers.get('content-type') || '';
        if (ct.indexOf('json') >= 0) {
          return res.json().then(function (j) {
            if (!res.ok) { var e = new Error(errMsg(j, res.status)); e.status = res.status; throw e; }
            // 202 + 작업(JobRead): 백그라운드 작업이 끝날 때까지 기다렸다가 최종 결과를 돌려준다 (호출부는 기존과 동일하게 결과만 받음)
            if (res.status === 202 && isJob(j)) return waitJob(j, retryAfter(res), method, url, opts.onJob);
            return j;
          });
        }
        if (!res.ok) {
          return res.text().then(function (t) {
            var clean = t ? stripHtml(t).slice(0, 300) : '';
            var e2 = new Error(clean || '요청 처리에 실패했습니다. (' + res.status + ')');
            e2.status = res.status;
            throw e2;
          }, function () {
            var e2 = new Error('요청 처리에 실패했습니다. (' + res.status + ')'); e2.status = res.status; throw e2;
          });
        }
        return res.text();
      });
    });
  }
  App.api = function (method, url, body, opts) { return send(method, url, body, opts || {}, false); };

  /* ------------------------------------------------------------ 백그라운드 작업 (API 명세: 202 Accepted + JobRead → GET /api/v1/jobs/{id}) */
  var JOB_TIMEOUT_MS = 30 * 60 * 1000;   // 장시간 큐(재현 등)를 고려한 최대 대기
  function isJob(j) { return j && typeof j === 'object' && j.id && j.status && j.status_url && j.kind; }
  function retryAfter(res) {
    var v = parseFloat(res.headers.get('retry-after'));
    return isFinite(v) && v > 0 ? Math.min(v, 10) * 1000 : 1000;
  }
  /** 서버가 준 경로(status_url·result_url)를 이 앱의 프록시 경로로 바꾼다 (절대 URL이면 경로만 사용) */
  function apiPath(u) {
    if (!u) return null;
    var m = /^https?:\/\/[^/]+(\/.*)$/.exec(u);
    var p = m ? m[1] : u;
    var i = p.indexOf('/api/v1/');
    return i >= 0 ? p.slice(i) : p;
  }
  function sleep(ms) { return new Promise(function (r) { setTimeout(r, ms); }); }
  /** 작업이 끝나면 결과를 읽는다: result → result_url → resource(dataset/analysis) → (탐색 GET) 같은 요청 재전송 */
  function jobResult(job, method, url) {
    if (job.result) return Promise.resolve(job.result);
    var ru = apiPath(job.result_url);
    if (ru) return App.get(ru);
    if (job.resource_type && job.resource_id) {
      var base = { dataset: '/api/v1/datasets/', analysis: '/api/v1/analyses/' }[job.resource_type];
      if (base) return App.get(base + encodeURIComponent(job.resource_id));
    }
    if (method === 'GET') return App.get(url);   // 탐색 API: 작업 완료 후 같은 요청은 캐시에서 200 으로 응답
    return Promise.resolve(job);
  }
  /** onJob(job): 상태를 조회할 때마다 호출 (예약 대기 순번·진행 상태 표시용, 선택). 작업 상태는
   *  queued(세션 대기열 예약, queue_position) → pending(워커 대기) → running → succeeded / failed / cancelled */
  function waitJob(job, delay, method, url, onJob) {
    var started = Date.now();
    function poll(j, wait) {
      if (onJob) { try { onJob(j); } catch (x) { /* 표시용이라 무시 */ } }
      if (j.status === 'succeeded') return jobResult(j, method, url);
      if (j.status === 'cancelled') {
        // 분석은 취소돼도 분석 레코드(status=cancelled)가 남으므로 그걸 돌려줘 화면이 상태를 표시하게 한다
        if (j.kind === 'analysis' && (j.result_url || j.resource_id)) {
          return App.get(apiPath(j.result_url) || '/api/v1/analyses/' + encodeURIComponent(j.resource_id));
        }
        var c = new Error('작업이 취소되었습니다.');
        c.code = 'cancelled'; c.job = j;
        return Promise.reject(c);
      }
      if (j.status === 'failed') {
        // 분석은 실패해도 분석 레코드(status=failed, error)가 남으므로 그걸 돌려줘 화면이 실패 사유를 표시하게 한다
        if (j.kind === 'analysis' && (j.result_url || j.resource_id)) {
          return App.get(apiPath(j.result_url) || '/api/v1/analyses/' + encodeURIComponent(j.resource_id));
        }
        var e = new Error((j.error && j.error.message) || '작업 처리에 실패했습니다.');
        e.code = j.error && j.error.code; e.job = j;
        return Promise.reject(e);
      }
      if (Date.now() - started > JOB_TIMEOUT_MS) return Promise.reject(new Error('작업이 너무 오래 걸려 대기를 중단했습니다. 잠시 후 다시 확인해 주세요.'));
      return sleep(wait).then(function () {
        return App.api('GET', apiPath(j.status_url) || '/api/v1/jobs/' + encodeURIComponent(j.id), undefined, { raw: true });
      }).then(function (res) {
        return res.json().catch(function () { return null; }).then(function (nj) {
          if (!res.ok || !nj) { var e2 = new Error(errMsg(nj, res.status)); e2.status = res.status; throw e2; }
          return poll(nj, retryAfter(res));
        });
      });
    }
    return poll(job, delay);
  }
  App.get = function (u, opts) { return App.api('GET', u, undefined, opts); };
  App.post = function (u, b, opts) { return App.api('POST', u, b === undefined ? {} : b, opts); };
  /** 작업 상태 → 화면 문구 (예약 대기 순번 포함) */
  App.jobText = function (j) {
    if (!j) return '';
    if (j.status === 'queued') return '대기열에서 차례를 기다리는 중' + (j.queue_position ? ' (' + j.queue_position + '번째)' : '');
    if (j.status === 'pending') return '처리 서버 배정을 기다리는 중';
    if (j.status === 'running') return '처리 중';
    return '';
  };
  App.patch = function (u, b) { return App.api('PATCH', u, b === undefined ? {} : b); };
  App.del = function (u) { return App.api('DELETE', u); };

  /** 세션 유지: 5분마다 heartbeat (토큰이 있을 때만) */
  setInterval(function () {
    if (session && session.token) App.api('POST', '/api/v1/sessions/current/heartbeat', {}).catch(function () { /* ignore */ });
  }, 5 * 60 * 1000);

  /* ------------------------------------------------------------ 토스트 */
  var toastTimer;
  App.toast = function (msg, kind) {
    var t = document.getElementById('toast');
    if (!t) return;
    document.getElementById('toast-msg').textContent = msg;
    var ic = t.querySelector('svg, i');
    t.classList.remove('hidden');
    t.classList.add('flex');
    t.style.borderColor = kind === 'error' ? 'var(--color-err)' : '';
    if (ic) ic.style.color = kind === 'error' ? 'var(--color-err-on-dark)' : 'var(--color-ok-on-dark)';
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () { t.classList.add('hidden'); t.classList.remove('flex'); }, kind === 'error' ? 5000 : 3000);
  };
  /* 인라인 오류: 토스트 대신 문제가 난 영역(anchor) 바로 아래에 표시. anchor 없으면 본문 맨 위.
   * 같은 영역에 다시 오면 내용만 바꾸고, App.fail(null, anchor) 로 지운다. */
  App.fail = function (msg, anchor) {
    var el = typeof anchor === 'string' ? document.querySelector(anchor) : anchor;
    var main = document.getElementById('main-content');
    var key = el ? (el.id || (el.id = 'fa-' + Math.random().toString(36).slice(2, 8))) : 'page';
    var box = document.querySelector('[data-fail-for="' + key + '"]');
    if (!msg) { if (box) box.remove(); return; }
    if (!box) {
      box = document.createElement('div');
      box.setAttribute('data-fail-for', key);
      box.setAttribute('role', 'alert');
      box.className = 'flex items-start gap-2 text-[13.5px] text-rose-800 bg-rose-50 border border-rose-200 rounded-md px-3 py-2 mt-2';
      box.innerHTML = '<span class="flex-1 min-w-0 break-words" data-fail-msg></span>' +
        '<button type="button" class="shrink-0 text-rose-700 hover:text-rose-900 cursor-pointer" aria-label="오류 닫기">' + App.icon('x', 'w-4 h-4') + '</button>';
      box.querySelector('button').addEventListener('click', function () { box.remove(); });
      if (el) el.insertAdjacentElement('afterend', box);
      else if (main) { box.classList.remove('mt-2'); box.classList.add('mb-4'); main.insertAdjacentElement('afterbegin', box); }
    }
    box.querySelector('[data-fail-msg]').textContent = msg;
    App.icons();
  };

  /* 확인 창: 되돌릴 수 없는 삭제에만. 포털 모달과 같은 모양, Esc·바깥 클릭은 취소 */
  App.confirm = function (msg, okLabel) {
    var m = document.getElementById('confirm-modal');
    if (!m) return Promise.resolve(window.confirm(msg));
    document.getElementById('confirm-msg').textContent = msg;
    var yes = document.getElementById('confirm-yes'), no = document.getElementById('confirm-no');
    yes.textContent = okLabel || '삭제';
    var back = document.activeElement;
    App.openModal('confirm-modal');
    no.focus();
    return new Promise(function (resolve) {
      function done(v) {
        yes.removeEventListener('click', onYes); no.removeEventListener('click', onNo);
        m.removeEventListener('click', onBack); document.removeEventListener('keydown', onKey, true);
        App.closeModal('confirm-modal');
        if (back && back.focus) back.focus();
        resolve(v);
      }
      function onYes() { done(true); }
      function onNo() { done(false); }
      function onBack(e) { if (e.target === m) done(false); }
      function onKey(e) { if (e.key === 'Escape') { e.stopPropagation(); done(false); } }
      yes.addEventListener('click', onYes); no.addEventListener('click', onNo);
      m.addEventListener('click', onBack); document.addEventListener('keydown', onKey, true);
    });
  };
  App.toastFlash = function (msg) {
    try { sessionStorage.setItem('flashToast', msg); } catch (e) { /* ignore */ }
  };

  /* ------------------------------------------------------------ 모달 */
  App.openModal = function (id) {
    var m = document.getElementById(id);
    if (!m) return;
    m.classList.remove('hidden');
    m.classList.add('flex');
  };
  App.closeModal = function (id) {
    var m = document.getElementById(id);
    if (!m) return;
    m.classList.add('hidden');
    m.classList.remove('flex');
  };

  /* ------------------------------------------------------------ 파일 저장 (클라이언트 생성) */
  App.saveText = function (filename, text, mime) {
    var a = document.createElement('a');
    a.href = URL.createObjectURL(new Blob([text], { type: mime || 'application/json' }));
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
  };

  /** 서버가 생성하는 파일(PDF/Excel) 다운로드: 세션 토큰 헤더가 필요하므로 fetch → Blob 으로 저장 */
  App.downloadFile = function (method, url, body, fallbackName) {
    return App.api(method, url, body, { raw: true }).then(function (res) {
      if (!res.ok) {
        return res.json().catch(function () { return null; }).then(function (j) { throw new Error(errMsg(j, res.status)); });
      }
      var cd = res.headers.get('content-disposition') || '';
      var m = /filename\*=UTF-8''([^;]+)/i.exec(cd);
      var name = fallbackName;
      if (m) { try { name = decodeURIComponent(m[1]); } catch (e) { /* ignore */ } }
      return res.blob().then(function (b) {
        var a = document.createElement('a');
        a.href = URL.createObjectURL(b);
        a.download = name;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        setTimeout(function () { URL.revokeObjectURL(a.href); }, 1000);
        return name;
      });
    });
  };

  /** 현재 분석 대상 데이터셋이 없으면 1단계로 안내 */
  // TEMP: 로컬 테스트를 위해 가드 비활성화. 테스트 끝나면 아래 원래 구현으로 되돌릴 것.
  App.requireDataset = function () {
    return true;
    /*
    if (App.state.datasetId) return true;
    App.toastFlash('먼저 1단계에서 분석할 데이터셋을 선택하거나 업로드해 주세요.');
    location.href = App.ctx + '/analysis/step1';
    return false;
    */
  };
  /** 데이터셋 조회 실패(404 등: 세션 만료로 삭제된 경우)를 공통 처리 */
  App.datasetGone = function (e) {
    if (e && (e.status === 404 || e.status === 401)) {
      App.saveState({ datasetId: null, datasetName: null, rawDatasetId: null });
      App.toastFlash('선택한 데이터셋을 찾을 수 없습니다. 다시 선택해 주세요.');
      location.href = App.ctx + '/analysis/step1';
      return true;
    }
    return false;
  };

  /* ------------------------------------------------------------ 헤더 메뉴 */
  // 교육데이터플랫폼(www.edmgr.kr) 주 메뉴와 동일. 이 서비스는 '분석지원 > 이용자 통계분석' 메뉴를 고도화한 것이다.
  var PORTAL = window.__PORTAL__ || 'https://www.edmgr.kr';
  var SELF_PATH = '/ot/dim/dmm/bm/ot_dim_dmmbm03_m01';   // 이용자 통계분석 (현재 서비스)
  var MENUS = [
    { title: '플랫폼소개', items: [
        ['플랫폼소개', '/intro/service_intro'],
        ['공지사항', '/ot/uss/bos/ib/ot_uss_bosib01_000?bbsId=BBS0000000001'],
        ['자료실', '/ot/uss/bos/ib/ot_uss_bosib01_000?bbsId=BBS0000000002'],
        ['교육데이터 웹툰', '/ot/uss/bos/ib/ot_uss_bosib01_010?bbsId=BBS0000000005'],
        ['자주묻는질문', '/ot/uss/bos/ib/ot_uss_bosib01_000?bbsId=BBS0000000003'],
        ['문의하기', '/ot/uss/qur/qr/newInqrReq'],
        ['데이터제공현황', '/intro/service_provided']
      ] },
    { title: '데이터검색', items: [
        ['데이터검색', '/dtSearchResult'],
        ['법제도로 찾기', '/ot/cof/cof/mn/lawSstmSearch'],
        ['데이터관리카드', '/ot/cof/cof/mn/dtcfSearch'],
        ['교육행정데이터 표준화 용어사전', '/ot/dim/mdm/mr/ot_dim_mdmmr01_m01'],
        ['교육데이터맵', '/intro/service_datamap']
      ] },
    { title: '데이터개방', items: [
        ['OpenAPI신청', '/ot/udp/api/cm/ot_udp_apicm01_m01'],
        ['개발자소통창구', '/ot/udp/api/db/ot_udp_apidb01_m01'],
        ['개방 포털 모음집', '/intro/service_openportal']
      ] },
    { title: '데이터활용', items: [
        ['시각화가이드', '/intro/service_vslzguide'],
        ['분석시각화', '/ot/dim/dmm/am/ot_dim_dmmam21_m01'],
        ['분석보고서', '/ot/ans/ans/as/ot_ans_ansas01_m02?rptSn=86c66c0ad17345f1ab5863abacc08bc597090e84e1374ec195e7a70ff5f67efc'],
        ['교육통계분석', '/ot/ans/ans/as/ot_ans_ansas01_m01?rptSn=0e5074cd69fe4df58a684a12bbaf438ba59b51b9d5c74712b0c5c93a5c7f8102'],
        ['수상작사례', '/ot/uss/prp/xc/ot_uss_prpxc01_m01'],
        ['참여형콘텐츠', '/ot/dim/dmm/am/ot_dim_dmmam51_m01']
      ] },
    { title: '분석지원', items: [
        ['데이터 안심구역', '/intro/service_safezone'],
        ['에듀데이터서비스(EDSS)', '/intro/service_edss'],
        ['활용지원서비스', '/intro/service_utlzsprt'],
        ['이용자 셀프분석', '/ot/dim/dmm/am/ot_dim_dmmam41_m01'],
        ['이용자 통계분석', '/ot/dim/dmm/bm/ot_dim_dmmbm03_m01']
      ] }
  ];
  function menuHref(h) { return h === SELF_PATH ? App.ctx + '/analysis/step1' : PORTAL + h; }
  function isSelf(h) { return h === SELF_PATH; }

  function renderGnb() {
    var nav = document.getElementById('gnb');
    if (!nav) return;
    nav.innerHTML = MENUS.map(function (m) {
      var items = m.items.map(function (it) {
        var self = isSelf(it[1]);
        return '<li><a href="' + menuHref(it[1]) + '" class="block px-5 py-2.5 text-[15px] transition-colors ' + (self ? 'text-link font-bold bg-brand-soft' : 'text-ink hover:bg-paper-2') + '">' + it[0] + '</a></li>';
      }).join('');
      return '<div class="relative h-full" data-menu>' +
        '<button type="button" class="gnb-btn h-full flex items-center gap-1.5 px-4 text-[17px] font-bold transition-colors cursor-pointer select-none hover:bg-paper-2 text-ink" aria-expanded="false"><span>' + m.title + '</span>' + App.icon('chevron-down', 'w-4 h-4 transition-transform') + '</button>' +
        '<ul class="gnb-panel hidden absolute top-full left-0 min-w-[220px] bg-white border border-rule rounded-b-lg shadow-lg py-2 z-50">' + items + '</ul></div>';
    }).join('');

    var sm = document.getElementById('sitemap-body');
    if (sm) sm.innerHTML = MENUS.map(function (m) {
      return '<div class="space-y-2.5"><div class="text-sm font-bold text-ink pb-2 border-b border-rule">' + m.title + '</div><ul class="space-y-1.5 text-[13px]">' +
        m.items.map(function (it) {
          var self = isSelf(it[1]);
          return '<li><a href="' + menuHref(it[1]) + '" class="block py-1 transition-colors ' + (self ? 'font-bold text-link' : 'text-ink-2 hover:text-link') + '">' + it[0] + '</a></li>';
        }).join('') + '</ul></div>';
    }).join('');

    nav.addEventListener('click', function (e) {
      var btn = e.target.closest('.gnb-btn');
      if (!btn) return;
      var panel = btn.parentElement.querySelector('.gnb-panel');
      var open = !panel.classList.contains('hidden');
      closeAllMenus();
      if (!open) {
        panel.classList.remove('hidden');
        btn.setAttribute('aria-expanded', 'true');
        var ch = btn.querySelector('svg');
        if (ch) ch.style.transform = 'rotate(180deg)';
      }
    });
  }

  function closeAllMenus() {
    App.$$('#gnb .gnb-panel').forEach(function (p) { p.classList.add('hidden'); });
    App.$$('#gnb .gnb-btn svg').forEach(function (s) { s.style.transform = ''; });
    App.$$('#gnb .gnb-btn').forEach(function (b) { b.setAttribute('aria-expanded', 'false'); });
  }

  /** design.md: 클릭 가능한 div(role="button")도 키보드로 조작 — Enter/Space 를 click 으로 */
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Enter' && e.key !== ' ') return;
    var t = e.target;
    if (!t || t.getAttribute('role') !== 'button' || /^(BUTTON|A|INPUT|SELECT|TEXTAREA)$/.test(t.tagName)) return;
    e.preventDefault();
    t.click();
  });

  function initHeader() {
    renderGnb();
    var fam = document.getElementById('btn-family'), famList = document.getElementById('family-list');
    if (fam && famList) {
      fam.addEventListener('click', function (e) {
        e.stopPropagation();
        var open = famList.classList.toggle('hidden') === false;
        fam.setAttribute('aria-expanded', String(open));
      });
      document.addEventListener('click', function (e) { if (!e.target.closest('#family-site')) { famList.classList.add('hidden'); fam.setAttribute('aria-expanded', 'false'); } });
    }
    document.addEventListener('click', function (e) {
      if (!e.target.closest('#gnb')) closeAllMenus();
    });
    var bs = document.getElementById('btn-search');
    if (bs) bs.addEventListener('click', function () {
      var bar = document.getElementById('search-bar');
      bar.classList.toggle('hidden');
      if (!bar.classList.contains('hidden')) document.getElementById('search-input').focus();
    });
    var sc = document.getElementById('search-close');
    if (sc) sc.addEventListener('click', function () { document.getElementById('search-bar').classList.add('hidden'); });
    // 통합검색은 포털 검색(/dtSearchResult)으로 실제 제출된다. 빈 검색어만 막는다.
    var sf = document.getElementById('search-form');
    if (sf) sf.addEventListener('submit', function (e) {
      var si = document.getElementById('search-input');
      if (!si.value.trim()) { e.preventDefault(); si.focus(); }
    });
    var map = { 'btn-sitemap': 'sitemap-modal', 'btn-help': 'help-modal', 'btn-login': 'login-modal' };
    Object.keys(map).forEach(function (bid) {
      var b = document.getElementById(bid);
      if (b) b.addEventListener('click', function () { App.openModal(map[bid]); });
    });
    document.addEventListener('click', function (e) {
      var c = e.target.closest('[data-close]');
      if (c) App.closeModal(c.getAttribute('data-close'));
      if (e.target.id === 'help-modal' || e.target.id === 'login-modal' || e.target.id === 'sitemap-modal') App.closeModal(e.target.id);
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === 'Escape') ['help-modal', 'login-modal', 'sitemap-modal'].forEach(App.closeModal);
    });
  }

  /* ------------------------------------------------------------ 사이드바 */
  function initSidebar() {
    var sb = document.getElementById('main-sidebar');
    var btn = document.getElementById('sb-toggle');
    if (!sb || !btn) return;
    function apply(collapsed) {
      sb.classList.toggle('w-60', !collapsed);
      sb.classList.toggle('w-14', collapsed);
      App.$$('.sb-full', sb).forEach(function (el) { el.style.display = collapsed ? 'none' : ''; });
      var ic = document.getElementById('sb-toggle-icon');
      if (ic) ic.style.transform = collapsed ? 'rotate(180deg)' : '';
      App.$$('a', sb).forEach(function (a) { a.style.justifyContent = collapsed ? 'center' : ''; });
    }
    var saved = false;
    try { saved = localStorage.getItem('sbCollapsed') === '1'; } catch (e) { /* ignore */ }
    apply(saved);
    btn.addEventListener('click', function () {
      saved = !saved;
      try { localStorage.setItem('sbCollapsed', saved ? '1' : '0'); } catch (e) { /* ignore */ }
      apply(saved);
    });
  }

  document.addEventListener('DOMContentLoaded', function () {
    initHeader();
    initSidebar();
    try {
      var f = sessionStorage.getItem('flashToast');
      if (f) { sessionStorage.removeItem('flashToast'); App.fail(f); }
    } catch (e) { /* ignore */ }
    App.icons();
  });
})();
