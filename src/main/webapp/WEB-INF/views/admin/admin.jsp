<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%-- 관리자 화면(초안, 목업 데이터). 다른 화면·공통 레이아웃과 독립. 제거: admin 패키지 + views/admin + static/admin --%>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="robots" content="noindex,nofollow">
  <title>관리자 | 이용자통계분석 서비스</title>
  <link rel="stylesheet" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
  <link rel="stylesheet" href="static/admin/admin.css">
</head>
<body>

<%-- 인증: 서버가 구동 시 생성해 로그에 한 번 출력하는 관리자 토큰 --%>
<main id="gate" class="gate" hidden>
  <form id="gate-form" class="gate-card" autocomplete="off">
    <h1>관리자 인증</h1>
    <p>서버를 시작할 때 로그에 한 번 출력된 관리자 토큰을 입력하세요.</p>
    <label for="gate-token">관리자 토큰</label>
    <input id="gate-token" type="password" spellcheck="false" placeholder="토큰 붙여넣기">
    <p id="gate-error" class="gate-error" role="alert" hidden></p>
    <button type="submit" class="btn btn-primary">확인</button>
    <p class="hint">초안(목업) 화면입니다. 아무 값이나 입력하면 들어갈 수 있습니다.</p>
  </form>
</main>

<div id="app" class="shell" hidden>
  <aside class="side">
    <div class="side-title">
      <strong>이용자통계분석</strong>
      <span>관리자</span>
    </div>
    <nav id="nav" aria-label="관리자 메뉴">
      <button type="button" data-view="dashboard">대시보드</button>
      <button type="button" data-view="jobs">작업 모니터링</button>
      <button type="button" data-view="sessions">세션 관리</button>
      <button type="button" data-view="cards">데이터관리카드</button>
      <button type="button" data-view="storage">데이터셋·패키지</button>
      <button type="button" data-view="sweeper">정리(sweeper)</button>
      <button type="button" data-view="settings">설정 조회</button>
    </nav>
    <div class="side-foot">
      <span class="mock-badge">목업 데이터</span>
      <button type="button" id="logout" class="link">로그아웃</button>
    </div>
  </aside>

  <main class="main">
    <header class="page-head">
      <div>
        <h1 id="view-title"></h1>
        <p id="view-lead"></p>
      </div>
      <button type="button" id="refresh" class="btn btn-ghost" aria-label="새로고침">새로고침</button>
    </header>
    <div id="view"></div>
  </main>
</div>

<div id="modal" class="modal" role="alertdialog" aria-modal="true" aria-labelledby="modal-msg" hidden>
  <div class="modal-box">
    <p id="modal-msg"></p>
    <div class="modal-actions">
      <button type="button" id="modal-no" class="btn btn-ghost">취소</button>
      <button type="button" id="modal-yes" class="btn btn-primary">확인</button>
    </div>
  </div>
</div>
<div id="toast" class="toast" role="status" aria-live="polite" hidden><span class="toast-dot"></span><span id="toast-msg"></span></div>

<script src="static/admin/admin-mock.js"></script>
<script src="static/admin/admin.js"></script>
</body>
</html>
