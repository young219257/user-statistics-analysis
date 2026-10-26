<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ include file="layout/top.jsp" %>

<div class="space-y-6">

  <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
    <div>
      <h3 class="text-[28px] font-bold text-ink tracking-tight break-keep">기초통계 요약 및 상관관계 분석</h3>
      <p class="step-lead">변수별 분포와 변수 사이의 상관관계를 확인합니다.</p>
    </div>
    <div class="text-body text-ink-2 shrink-0" id="eda-badge">불러오는 중...</div>
  </div>

  <%-- 기초통계량 --%>
  <div class="card-modern sec">
    <div class="sec-head flex flex-col sm:flex-row sm:items-center justify-between gap-2">
      <h4 class="text-title font-semibold text-ink flex items-center gap-1.5">
        <span>전체 수치형 변수 기초통계량</span>
        <span class="text-body text-muted" id="stat-count">0개 변수</span>
      </h4>
      <div class="text-xs text-ink-3">총 관측치: <strong class="font-mono text-ink-0" id="stat-rows">-</strong></div>
    </div>
    <%-- 변수가 많으면 기본 높이(420px) 안에서 스크롤, 머리행·변수명 열 고정 (app.css .matrix-scroll) --%>
    <div class="sec-box sec-flush">
    <div class="matrix-scroll">
      <table class="w-full text-left text-body border-collapse">
        <thead>
          <tr class="bg-paper-3 text-ink-1 border-b border-rule text-xs font-semibold">
            <th class="py-2.5 px-3 mx-sticky">변수명</th>
            <th class="py-2.5 px-2.5 text-right font-medium">유효표본(N)</th>
            <th class="py-2.5 px-2.5 text-right font-medium">평균</th>
            <th class="py-2.5 px-2.5 text-right font-medium">표준편차</th>
            <th class="py-2.5 px-2.5 text-right font-medium">최솟값</th>
            <th class="py-2.5 px-2.5 text-right font-medium">1사분위(Q1)</th>
            <th class="py-2.5 px-2.5 text-right font-medium">중앙값</th>
            <th class="py-2.5 px-2.5 text-right font-medium">3사분위(Q3)</th>
            <th class="py-2.5 px-2.5 text-right font-medium">최댓값</th>
            <th class="py-2.5 px-2.5 text-right font-medium">왜도</th>
            <th class="py-2.5 px-2.5 text-right font-medium">첨도</th>
            <th class="py-2.5 px-3 text-right font-medium">결측치율</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-paper-2 font-mono text-body" id="stat-body">
          <tr><td colspan="12" class="py-8 text-center text-ink-4 font-sans">불러오는 중...</td></tr>
        </tbody>
      </table>
    </div>
    </div>
  </div>

  <%-- 상관행렬 --%>
  <div class="card-modern sec">
    <div class="sec-head flex flex-col sm:flex-row sm:items-center justify-between gap-2">
      <div>
        <h4 class="text-title font-semibold text-ink">
          <span id="corr-title">상관계수 행렬</span>
        </h4>
        <p class="text-xs text-ink-3 mt-0.5">변수 쌍 간의 상관계수(r)입니다. -1.0(완전 음의 상관)부터 +1.0(완전 양의 상관)까지 분포합니다.</p>
      </div>
      <div class="flex items-center gap-3 flex-wrap">
        <select id="corr-method" aria-label="상관계수 방법" class="bg-white border border-rule-3 rounded-lg px-2.5 py-1 text-xs text-ink-0 focus:outline-none focus:border-blue-600 cursor-pointer">
          <option value="pearson">피어슨</option>
          <option value="spearman">스피어만</option>
          <option value="kendall">켄달</option>
        </select>
        <div class="flex items-center gap-3 text-xs text-ink-2 flex-wrap">
          <div class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-blue-100 border border-blue-300 inline-block"></span><span>강한 양의 상관 (r ≥ 0.7)</span></div>
          <div class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-blue-50 border border-blue-200 inline-block"></span><span>보통 양의 상관 (0.4 ≤ r &lt; 0.7)</span></div>
          <div class="flex items-center gap-1"><span class="w-3 h-3 rounded bg-paper-2 border border-rule-3 inline-block"></span><span>음의 상관 (r ≤ -0.4)</span></div>
        </div>
      </div>
    </div>
    <div class="sec-box">
    <div class="overflow-x-auto" id="corr-wrap"><div class="py-6 text-center text-xs text-ink-4">불러오는 중...</div></div>
    <div class="pt-4 hidden" id="pairs-wrap"></div>
    </div>
  </div>

  <div class="flex flex-wrap items-center justify-between gap-3 pt-2">
    <a href="${ctx}/analysis/step2" class="px-4 py-2.5 bg-white hover:bg-paper-3 border border-rule-3 text-ink-1 font-semibold text-body rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap shrink-0">
      <i data-lucide="arrow-left" class="w-4 h-4"></i><span>2단계로 돌아가기</span>
    </a>
    <a href="${ctx}/analysis/step4" class="px-5 py-2.5 bg-brand hover:bg-brand-dark text-white font-bold text-body rounded-xl transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap shrink-0">
      <span>4단계 모형 설정으로 이동</span><i data-lucide="arrow-right" class="w-4 h-4"></i>
    </a>
  </div>
</div>

<%@ include file="layout/bottom.jsp" %>
<script src="${ctx}/static/js/step3.js"></script>
</body>
</html>
