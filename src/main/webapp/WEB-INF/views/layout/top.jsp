<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fn" uri="http://java.sun.com/jsp/jstl/functions" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title><c:out value="${pageTitle}"/> | 교육데이터플랫폼 이용자통계분석 서비스</title>
  <meta name="description" content="공공기관 및 연구자를 위한 데이터 반입, 탐색적 데이터 분석(EDA), 다변량 고급 통계 분석 및 결과 리포트 생성 웹 서비스">
  <link rel="icon" type="image/svg+xml" href="${ctx}/static/vendor/edmgr-header-logo.svg">
  <link rel="preconnect" href="https://cdn.jsdelivr.net">
  <link rel="stylesheet" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
  <link rel="stylesheet" href="${ctx}/static/css/app.css">
  <!-- 폐쇄망 배포를 위해 라이브러리를 /static/vendor 에 포함 (Tailwind v4 browser build, Highcharts, Lucide) -->
  <script src="${ctx}/static/vendor/tailwind-browser.js"></script>
  <%-- design.md 토큰: 화면 코드는 brand/link/ink/rule 등 이름만 쓴다. 파랑 계열(blue/indigo/violet/purple/teal)은 하나의 남색-파랑 축, 중립색(slate/gray)은 ink·rule·paper 단계로 통일 --%>
  <style type="text/tailwindcss">
    @theme {
      --color-brand: #1e2c5d;
      --color-brand-dark: #16224f;
      --color-brand-soft: #e8ecf6;
      --color-link: #1558d6;
      --color-ink: #191f28;
      --color-ink-2: #4e5968;
      --color-ink-3: #6b7684;
      --color-ink-4: #6b7684;
      --color-rule: #e5e8eb;
      --color-muted: #6b7684;
      --color-rule-2: #f2f4f6;
      --color-rule-3: #d1d6db;
      --color-paper-2: #f2f4f6;
      --color-paper-3: #f9fafb;
      --color-gov: #edf1f5;
      --color-accent: #d14905;
      --color-accent-10: #fff4ec;
      --color-accent-20: #fbd9c3;
      --color-alert: #d63d00;
      --color-ink-0: #333d4b;
      --color-ink-1: #333d4b;
      --color-ink-deep: #131518;
      --color-chart-1: #256ef4;
      --color-chart-2: #e5484d;
      --color-chart-3: #14a58a;
      --color-chart-4: #f5a623;
      --color-chart-5: #7a5af8;
      --color-chart-6: #1e2c5d;
      --color-chart-7: #5aa9ff;
      --color-chart-8: #8a949e;
      --text-body: 13.5px;
      --text-body--line-height: 1.6;
      --text-title: 15px;
      --text-title--line-height: 1.4;
      --radius-md: 6px;
      --radius-lg: 8px;
      --radius-xl: 12px;
      --radius-2xl: 12px;
      --color-blue-50: oklch(97.2% 0.013 268);
      --color-blue-100: oklch(94% 0.028 268);
      --color-blue-200: oklch(88% 0.055 268);
      --color-blue-300: oklch(79% 0.095 266);
      --color-blue-400: oklch(68% 0.15 264);
      --color-blue-500: oklch(60% 0.19 263);
      --color-blue-600: oklch(56% 0.2 262);
      --color-blue-700: oklch(48% 0.17 265);
      --color-blue-800: oklch(39% 0.12 268);
      --color-blue-900: oklch(30% 0.08 272);
      --color-blue-950: oklch(23% 0.06 272);
      --color-indigo-50: oklch(97.2% 0.013 268);
      --color-indigo-100: oklch(94% 0.028 268);
      --color-indigo-200: oklch(88% 0.055 268);
      --color-indigo-300: oklch(79% 0.095 266);
      --color-indigo-400: oklch(68% 0.15 264);
      --color-indigo-500: oklch(60% 0.19 263);
      --color-indigo-600: oklch(56% 0.2 262);
      --color-indigo-700: oklch(48% 0.17 265);
      --color-indigo-800: oklch(39% 0.12 268);
      --color-indigo-900: oklch(30% 0.08 272);
      --color-indigo-950: oklch(23% 0.06 272);
      --color-violet-50: oklch(97.2% 0.013 268);
      --color-violet-100: oklch(94% 0.028 268);
      --color-violet-200: oklch(88% 0.055 268);
      --color-violet-300: oklch(79% 0.095 266);
      --color-violet-400: oklch(68% 0.15 264);
      --color-violet-500: oklch(60% 0.19 263);
      --color-violet-600: oklch(56% 0.2 262);
      --color-violet-700: oklch(48% 0.17 265);
      --color-violet-800: oklch(39% 0.12 268);
      --color-violet-900: oklch(30% 0.08 272);
      --color-violet-950: oklch(23% 0.06 272);
      --color-purple-50: oklch(97.2% 0.013 268);
      --color-purple-100: oklch(94% 0.028 268);
      --color-purple-200: oklch(88% 0.055 268);
      --color-purple-300: oklch(79% 0.095 266);
      --color-purple-400: oklch(68% 0.15 264);
      --color-purple-500: oklch(60% 0.19 263);
      --color-purple-600: oklch(56% 0.2 262);
      --color-purple-700: oklch(48% 0.17 265);
      --color-purple-800: oklch(39% 0.12 268);
      --color-purple-900: oklch(30% 0.08 272);
      --color-purple-950: oklch(23% 0.06 272);
      --color-teal-50: oklch(97.2% 0.013 268);
      --color-teal-100: oklch(94% 0.028 268);
      --color-teal-200: oklch(88% 0.055 268);
      --color-teal-300: oklch(79% 0.095 266);
      --color-teal-400: oklch(68% 0.15 264);
      --color-teal-500: oklch(60% 0.19 263);
      --color-teal-600: oklch(56% 0.2 262);
      --color-teal-700: oklch(48% 0.17 265);
      --color-teal-800: oklch(39% 0.12 268);
      --color-teal-900: oklch(30% 0.08 272);
      --color-teal-950: oklch(23% 0.06 272);
      /* 중립색: Tailwind slate·gray 를 design.md 의 ink·rule·paper 단계로 매핑 */
      --color-slate-50: var(--color-paper-3);
      --color-slate-100: var(--color-paper-2);
      --color-slate-200: var(--color-rule);
      --color-slate-300: var(--color-rule-3);
      --color-slate-400: var(--color-ink-4);
      --color-slate-500: var(--color-ink-3);
      --color-slate-600: var(--color-ink-2);
      --color-slate-700: var(--color-ink-1);
      --color-slate-800: var(--color-ink-0);
      --color-slate-900: var(--color-ink);
      --color-slate-950: var(--color-ink-deep);
      --color-gray-50: var(--color-paper-3);
      --color-gray-100: var(--color-paper-2);
      --color-gray-200: var(--color-rule);
      --color-gray-300: var(--color-rule-3);
      --color-gray-400: var(--color-ink-4);
      --color-gray-500: var(--color-ink-3);
      --color-gray-600: var(--color-ink-2);
      --color-gray-700: var(--color-ink-1);
      --color-gray-800: var(--color-ink-0);
      --color-gray-900: var(--color-ink);
      --color-gray-950: var(--color-ink-deep);
    }
  </style>
  <script src="${ctx}/static/vendor/lucide.min.js"></script>
  <script src="${ctx}/static/vendor/highcharts.js"></script>
  <script src="${ctx}/static/vendor/highcharts-more.js"></script>
  <script src="${ctx}/static/vendor/heatmap.js"></script>
  <script src="${ctx}/static/vendor/treemap.js"></script>
  <script src="${ctx}/static/vendor/treegraph.js"></script>
  <script src="${ctx}/static/vendor/exporting.js"></script>
</head>
<body class="min-h-screen bg-white flex flex-col font-sans text-ink antialiased">

<%-- ============================ 1. 상단 헤더 (교육데이터플랫폼 www.edmgr.kr 공통 헤더와 동일한 구성) ============================ --%>
<c:set var="portal" value="https://www.edmgr.kr" />
<div id="edd_gov_top" class="bg-gov">
  <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 h-8 flex items-center gap-1 text-[13px] text-ink-2">
    <img src="${ctx}/static/vendor/portal/ico-korea-flag.svg" alt="태극기" class="w-6 h-4 object-contain">
    <span>이 누리집은 대한민국 공식 전자정부 누리집입니다.</span>
  </div>
</div>
<a href="#main-content" class="skip-link">본문 바로가기</a>
<header class="w-full bg-white relative z-50" id="site-header">
  <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 h-[79px] flex items-center justify-between gap-4">
    <h1 class="m-0">
      <a href="${portal}/" class="flex items-center" title="교육데이터플랫폼 메인으로 가기">
        <img src="${ctx}/static/vendor/edmgr-header-logo.svg" alt="교육부 교육데이터플랫폼" class="h-9 w-auto">
      </a>
    </h1>
    <div class="flex items-center gap-1 text-[17px] font-bold text-ink">
      <button type="button" id="btn-search" class="flex items-center gap-1.5 px-3 h-10 rounded-md hover:bg-paper-2 transition-colors cursor-pointer">
        <img src="${ctx}/static/vendor/portal/icon_search2.svg" alt="" class="w-5 h-5"><span class="hidden md:inline">통합검색</span>
      </button>
      <button type="button" id="btn-login" class="hidden md:flex items-center gap-1.5 px-3 h-10 rounded-md hover:bg-paper-2 transition-colors cursor-pointer">
        <img src="${ctx}/static/vendor/portal/icon_login.svg" alt="" class="w-5 h-5"><span>로그인</span>
      </button>
      <a href="${portal}/new/memberAgre" class="hidden md:flex items-center gap-1.5 px-3 h-10 rounded-md hover:bg-paper-2 transition-colors">
        <img src="${ctx}/static/vendor/portal/icon_join.svg" alt="" class="w-5 h-5"><span>회원가입</span>
      </a>
    </div>
  </div>
  <%-- 주 메뉴: 메뉴 데이터는 common.js(PORTAL_MENUS) — 포털과 같은 5개 대메뉴·하위메뉴 --%>
  <div class="border-y border-rule">
    <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 h-14 flex items-center justify-between">
      <nav class="hidden lg:flex items-center h-full" id="gnb" aria-label="주 메뉴"></nav>
      <button type="button" id="btn-sitemap" class="flex items-center gap-2 h-10 px-2 text-[17px] font-bold text-ink rounded-md hover:bg-paper-2 transition-colors cursor-pointer ml-auto">
        <span>전체 메뉴</span><img src="${ctx}/static/vendor/portal/icon_menu2.svg" alt="" class="w-6 h-6">
      </button>
    </div>
  </div>

  <%-- 통합검색: 포털과 같이 /dtSearchResult 로 검색어(queryNav)를 POST --%>
  <div id="search-bar" class="hidden bg-white p-3 border-b border-rule shadow-lg anim-in">
    <form id="search-form" action="${portal}/dtSearchResult" method="post" class="max-w-3xl mx-auto flex items-center gap-3">
      <i data-lucide="search" class="w-4 h-4 text-ink-3 shrink-0"></i>
      <input type="text" id="search-input" name="queryNav" title="데이터 검색" placeholder="궁금하신 데이터를 검색해 보세요" class="flex-1 min-w-0 bg-transparent border-b border-rule-3 focus:border-link px-2 py-1.5 text-[15px] text-ink placeholder-ink-4 focus:outline-none">
      <button type="submit" id="search-go" class="px-3.5 py-1.5 bg-brand hover:bg-brand-dark text-white font-semibold text-[13.5px] rounded-md transition-colors cursor-pointer whitespace-nowrap shrink-0">검색</button>
      <button type="button" id="search-close" aria-label="검색 닫기" class="p-1 text-ink-3 hover:text-ink rounded-md cursor-pointer"><i data-lucide="x" class="w-4 h-4"></i></button>
    </form>
  </div>

  <div id="sitemap-modal" role="dialog" aria-modal="true" aria-labelledby="sitemap-title" class="hidden fixed inset-0 bg-ink-deep/40 z-50 items-start justify-center pt-16 px-4">
    <div class="bg-white rounded-lg w-full max-w-4xl shadow-lg border border-rule overflow-hidden anim-in">
      <div class="p-4 bg-paper-3 border-b border-rule/80 flex items-center justify-between">
        <div class="flex items-center gap-2.5">
          <img src="${ctx}/static/vendor/edmgr-header-logo.svg" alt="교육데이터플랫폼" class="h-7 w-auto object-contain">
          <span class="text-rule-3">|</span>
          <h2 id="sitemap-title" class="text-sm font-bold text-ink">전체 메뉴</h2>
        </div>
        <button type="button" data-close="sitemap-modal" aria-label="전체 메뉴 닫기" class="p-1.5 text-ink-2 hover:text-ink-0 rounded-lg hover:bg-rule transition-colors cursor-pointer"><i data-lucide="x" class="w-5 h-5"></i></button>
      </div>
      <div class="p-6 grid grid-cols-2 md:grid-cols-5 gap-6" id="sitemap-body"></div>
    </div>
  </div>
</header>

<%-- ============================ 1-1. 위치 표시 · 도움말 · 페이지 제목 (포털 화면과 동일) ============================ --%>
<div class="bg-white">
  <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 page-wrap">
    <div class="flex items-start justify-between pt-5">
      <ol class="flex items-center gap-1.5 text-[14px] text-ink" aria-label="현재 위치">
        <li><a href="${portal}/" class="flex items-center gap-1"><svg viewBox="0 0 24 24" class="w-4 h-4" aria-hidden="true"><path fill="#1e2124" d="M12 3.2 2.5 11h2.7v9.3h5.3v-5.8h3v5.8h5.3V11h2.7z"/></svg><span class="underline underline-offset-4">홈</span></a></li>
        <li aria-hidden="true"><i data-lucide="chevron-right" class="w-3.5 h-3.5 text-ink-3"></i></li>
        <li><span>분석지원</span></li>
      </ol>
      <button type="button" id="btn-help" class="mt-5 flex items-center gap-1.5 px-4 h-10 bg-paper-3 border border-rule-3 rounded-md text-[16px] text-ink hover:bg-paper-2 transition-colors cursor-pointer" title="도움말 및 이용 가이드">
        <i data-lucide="arrow-left-to-line" class="w-4 h-4"></i><span>도움말</span>
      </button>
    </div>
    <h2 class="text-[40px] leading-tight font-bold text-ink tracking-tight pt-6 pb-7">이용자통계분석</h2>
  </div>
</div>

<%-- ============================ 2. 5단계 진행 바 ============================ --%>
<c:set var="stepIdx" value="${activeStep == 'import' ? 0 : activeStep == 'preprocess' ? 1 : activeStep == 'eda' ? 2 : activeStep == 'modeling' ? 3 : 4}" />
<nav aria-label="분석 진행 단계" class="sticky top-0 z-40 bg-white border-y border-rule">
  <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 page-wrap">
    <c:set var="stepNames" value="${fn:split('데이터 반입,품질 및 전처리,데이터 탐색,통계 모델링,결과 관리', ',')}" />
    <c:set var="stepUrls" value="${fn:split('step1,step2,step3,step4,step5', ',')}" />
    <%-- 좁은 화면: 현재 단계 한 줄 + 진행 막대 --%>
    <div class="md:hidden flex items-center gap-3 h-14">
      <span class="w-8 h-8 rounded-full bg-brand text-white text-[14px] font-bold flex items-center justify-center shrink-0">${stepIdx + 1}</span>
      <span class="flex flex-col leading-tight min-w-0">
        <span class="text-xs font-semibold text-brand">STEP ${stepIdx + 1} / 5</span>
        <span class="text-[15px] font-bold text-ink truncate"><c:out value="${stepNames[stepIdx]}"/></span>
      </span>
      <span class="ml-auto w-24 h-1.5 rounded-full bg-paper-2 overflow-hidden shrink-0" aria-hidden="true"><span class="block h-full bg-brand" style="width:${(stepIdx + 1) * 20}%"></span></span>
    </div>
    <ol class="hidden md:grid grid-cols-5">
      <c:forEach var="nm" items="${stepNames}" varStatus="st">
        <c:set var="i" value="${st.index}" />
        <li class="flex items-center min-w-0">
          <a href="${ctx}/analysis/${stepUrls[i]}"
             class="relative flex items-center gap-2.5 h-16 pr-3 shrink-0 cursor-pointer select-none whitespace-nowrap group ${i == stepIdx ? 'after:absolute after:left-0 after:right-0 after:-bottom-px after:h-[3px] after:bg-brand' : ''}"
             ${i == stepIdx ? 'aria-current="step"' : ''}>
            <span class="w-8 h-8 rounded-full flex items-center justify-center text-[14px] font-bold shrink-0 transition-colors
              ${i == stepIdx ? 'bg-brand text-white' : (i < stepIdx ? 'bg-brand-soft text-brand' : 'bg-white border border-rule-3 text-ink-4 group-hover:border-brand')}">
              <c:choose>
                <c:when test="${i < stepIdx}"><i data-lucide="check" class="w-4 h-4" style="stroke-width:3"></i></c:when>
                <c:otherwise>${i + 1}</c:otherwise>
              </c:choose>
            </span>
            <span class="flex flex-col leading-tight">
              <span class="text-xs font-semibold tracking-wide ${i == stepIdx ? 'text-brand' : 'text-ink-4'}">STEP ${i + 1}</span>
              <span class="text-[15px] ${i == stepIdx ? 'font-bold text-ink' : (i < stepIdx ? 'font-semibold text-ink-2 group-hover:text-ink' : 'font-medium text-ink-4 group-hover:text-ink-2')}"><c:out value="${nm}"/></span>
            </span>
          </a>
          <c:if test="${i < 4}"><span class="flex-1 h-px mx-3 ${i < stepIdx ? 'bg-brand/40' : 'bg-rule'}" aria-hidden="true"></span></c:if>
        </li>
      </c:forEach>
    </ol>
  </div>
  <%-- 4단계 하위 화면 (모형 설정·실행 / 분석 결과 리포트) --%>
  <c:if test="${activeStep == 'modeling'}">
    <div class="border-t border-rule-2 bg-paper-3">
      <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 page-wrap flex items-center gap-6 h-11 text-[14px]">
        <a href="${ctx}/analysis/step4" class="h-full flex items-center border-b-2 ${subTab == 'run' ? 'border-brand font-bold text-ink' : 'border-transparent text-ink-3 hover:text-ink'}">4-1. 모형 설정·실행</a>
        <a href="${ctx}/analysis/step4/report" class="h-full flex items-center border-b-2 ${subTab == 'report' ? 'border-brand font-bold text-ink' : 'border-transparent text-ink-3 hover:text-ink'}">4-2. 분석 결과 리포트</a>
      </div>
    </div>
  </c:if>
</nav>

<%-- ============================ 3. 본문 (사이드바 없이 포털과 같은 폭) ============================ --%>
<div class="flex-1 w-full">
  <main id="main-content" tabindex="-1" class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 page-wrap py-8">
