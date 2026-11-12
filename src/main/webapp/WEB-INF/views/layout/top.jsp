<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
<%@ taglib prefix="fn" uri="http://java.sun.com/jsp/jstl/functions" %>
<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title><c:out value="${pageTitle}"/> | 이용자통계분석</title>
  <meta name="description" content="공공기관 및 연구자를 위한 데이터 반입, 탐색적 데이터 분석(EDA), 다변량 고급 통계 분석 및 결과 리포트 생성 웹 서비스">
  <link rel="icon" type="image/svg+xml" href="${ctx}/static/vendor/edmgr-header-emblem.svg">
  <link rel="preconnect" href="https://cdn.jsdelivr.net">
  <link rel="stylesheet" crossorigin href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/static/pretendard.css">
  <link rel="stylesheet" href="${ctx}/static/css/app.css?v=20261159">
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

<%-- ============================ 1. 상단 헤더 (행정안전부 공식 누리집 띠 + 서비스 이름만 둔다) ============================ --%>
<div id="edd_gov_top" class="bg-gov">
  <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 h-8 flex items-center gap-1 text-[13px] text-ink-2">
    <img src="${ctx}/static/vendor/portal/ico-korea-flag.svg" alt="태극기" class="w-6 h-4 object-contain">
    <span>이 누리집은 대한민국 공식 전자정부 누리집입니다.</span>
  </div>
</div>
<a href="#main-content" class="skip-link">본문 바로가기</a>
<header class="w-full bg-white relative z-50" id="site-header">
  <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 h-[72px] flex items-center justify-between gap-4">
    <h1 class="m-0">
      <a href="${ctx}/analysis/step1" class="flex items-center gap-3.5" title="이용자통계분석 처음으로">
        <img src="${ctx}/static/vendor/edmgr-header-emblem.svg" alt="" class="h-9 w-auto" aria-hidden="true">
        <span class="text-[22px] font-bold tracking-tight text-[#575756]">이용자통계분석</span>
      </a>
    </h1>
    <button type="button" id="btn-help" class="inline-flex items-center gap-1.5 px-4 h-10 bg-white border border-brand rounded-md text-[15px] font-semibold text-brand hover:bg-brand-soft transition-colors cursor-pointer focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand" title="도움말 및 이용 가이드">
        <i data-lucide="circle-help" class="w-4 h-4"></i><span>도움말</span>
      </button>
  </div>
</header>

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
