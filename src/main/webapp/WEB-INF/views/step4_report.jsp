<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ include file="layout/top.jsp" %>

<div class="space-y-6" id="report-root">

  <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
    <div>
<div class="flex items-center gap-2 mb-2"><span class="px-2.5 py-1 rounded-full text-xs font-semibold bg-brand-soft text-link" id="rp-method">통계 분석 모형</span></div>      <h3 class="text-[24px] font-bold text-ink tracking-tight" id="rp-title">분석 결과를 불러오는 중...</h3>
    </div>
    <div class="flex items-center gap-2 shrink-0">
      <button type="button" id="btn-save" class="hidden px-4 py-2 bg-brand hover:bg-brand-dark disabled:bg-emerald-700 text-white rounded-xl text-body font-semibold transition-colors items-center gap-1.5 cursor-pointer">
        <i data-lucide="save" class="w-3.5 h-3.5"></i><span>결과 패키지 저장</span>
      </button>
    </div>
  </div>

  <div id="rp-empty" class="hidden card-modern p-12 text-center text-ink-3 space-y-3">
    <i data-lucide="cpu" class="w-8 h-8 mx-auto text-rule-3"></i>
    <div class="text-sm font-semibold text-ink-1">표시할 분석 결과가 없습니다.</div>
    <div class="text-xs">4-1단계에서 모형을 설정하고 분석을 실행해 주세요.</div>
    <a href="${ctx}/analysis/step4" class="inline-block px-4 py-2 bg-brand text-white rounded-xl text-xs font-bold">모형 설정·실행으로 이동</a>
  </div>

  <div id="rp-body" class="space-y-6 hidden">
    <div id="rp-diag" class="card-modern p-5 space-y-3"></div>

    <div class="flex items-center justify-between bg-paper-2/80 rounded-xl p-1 border border-rule/70">
      <div class="flex items-center gap-1 flex-wrap" id="rp-tabs"></div>
    </div>

    <div id="rp-result" class="space-y-4"></div>
    <div id="rp-charts"></div>
    <div id="rp-rawdata" class="card-modern p-5 space-y-3"></div>
  </div>

  <div class="flex flex-wrap justify-between items-center gap-3 pt-2">
    <a href="${ctx}/analysis/step4" class="px-4 py-2.5 bg-white hover:bg-paper-2 text-ink-1 font-semibold text-body rounded-lg transition-colors border border-rule cursor-pointer flex items-center gap-1.5 whitespace-nowrap shrink-0">
      <i data-lucide="arrow-left" class="w-4 h-4"></i><span>4-1단계 모형 설정 및 재실행</span>
    </a>
    <a href="${ctx}/analysis/step5" class="px-4 py-2.5 bg-brand hover:bg-brand-dark text-white font-bold text-body rounded-lg transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap shrink-0">
      <span>5단계 결과 관리 및 패키징</span><i data-lucide="arrow-right" class="w-4 h-4"></i>
    </a>
  </div>
</div>

<%@ include file="layout/bottom.jsp" %>
<script src="${ctx}/static/js/charts.js"></script>
<script src="${ctx}/static/js/report.js"></script>
</body>
</html>
