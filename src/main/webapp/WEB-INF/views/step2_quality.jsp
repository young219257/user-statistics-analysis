<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ include file="layout/top.jsp" %>

<div class="space-y-6" id="step2-root">

  <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
    <div>
      <h3 class="text-[28px] font-bold text-ink tracking-tight break-keep">데이터 품질 진단 및 전처리 규칙 수립</h3>
      <p class="step-lead">이상치 탐지 방법을 고르고 결측치·이상치 처리 규칙을 정합니다.</p>
    </div>
  </div>

  <%-- 이상치 탐지 알고리즘 선택 (7대 기법) --%>
  <div class="card-modern sec">
    <div class="sec-head">
      <h3 class="text-title font-semibold text-ink">이상치 탐지 알고리즘 선택</h3>
    </div>
    <div class="sec-box">
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 mt-3 items-stretch" id="algo-grid"></div>

    <div class="mt-3.5 flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-paper-3 border border-rule rounded-lg p-3">
      <div class="flex items-center gap-2 flex-wrap">
        <span class="text-body text-ink">선택 알고리즘: <span class="text-brand font-semibold" id="algo-sel-name"></span></span>
      </div>
      <button type="button" id="btn-detect" disabled class="px-4 py-2 bg-brand hover:bg-brand-dark disabled:bg-ink-4 disabled:hover:bg-ink-4 disabled:cursor-not-allowed text-white font-bold text-body rounded-xl transition-colors cursor-pointer flex items-center justify-center gap-1.5 shrink-0">
        <span>이상치 탐지 실행</span>
      </button>
    </div>
    </div>
  </div>

  <%-- 품질 진단 요약 --%>
  <div class="space-y-4">
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      <div class="card-modern p-4"><span class="text-xs font-medium text-ink-4 block">총 관측치</span><span class="text-lg font-bold text-ink font-mono mt-0.5 block" id="card-rows">-</span></div>
      <div class="card-modern p-4"><span class="text-xs font-medium text-ink-4 block">결측치</span><span class="text-lg font-bold font-mono mt-0.5 block" id="card-missing">-</span></div>
      <div class="card-modern p-4"><span class="text-xs font-medium text-ink-4 block" id="card-out-label">이상치 검출</span><span class="text-lg font-bold font-mono mt-0.5 block" id="card-outliers">-</span></div>
      <div class="card-modern p-4"><span class="text-xs font-medium text-ink-4 block">중복 행</span><span class="text-lg font-bold font-mono mt-0.5 block" id="card-dups">-</span></div>
    </div>

    <div class="card-modern sec">
      <div class="sec-head flex items-center justify-between">
        <div>
          <h4 class="text-title font-semibold text-ink">변수별 결측치 및 이상치 진단 현황</h4>
          <p class="text-xs text-ink-4 mt-0.5">현재 적용 알고리즘: <span class="font-bold text-ink-1" id="applied-name"></span> (<span id="applied-formula" class="font-mono"></span>)</p>
        </div>
        <span class="text-xs text-ink-4 font-medium whitespace-nowrap">클릭 시 상세 분석</span>
      </div>
      <div class="sec-box">
      <div class="overflow-x-auto md:max-h-64">
        <table class="w-full min-w-[420px] text-left text-body border-collapse whitespace-nowrap">
          <thead><tr class="bg-paper-3 text-ink-2 border-b border-rule text-xs">
            <th class="py-2.5 px-3">변수명</th><th class="py-2.5 px-3 text-right">결측치</th><th class="py-2.5 px-3 text-right" id="th-out">이상치</th><th class="py-2.5 px-3 text-right">상태</th>
          </tr></thead>
          <tbody class="divide-y divide-paper-2 font-mono text-body" id="var-body"></tbody>
        </table>
      </div>
      </div>
    </div>

    <div class="card-modern sec space-y-3" id="detail-card"></div>
  </div>

  <%-- 정제 전략 설정 --%>
  <div class="card-modern sec">
    <div class="sec-head">
<h3 class="text-title font-semibold text-ink">데이터 정제 및 전처리 규칙 설정</h3>
    </div>
    <div class="sec-box">
    <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4" id="strategy-grid"></div>
    </div>
  </div>

  <div id="prep-msg" class="hidden text-xs text-rose-700 py-1.5"></div>

  <div class="flex flex-wrap items-center justify-between gap-3 pt-2">
    <a href="${ctx}/analysis/step1" class="px-4 py-2.5 bg-white hover:bg-paper-3 border border-rule-3 text-ink-1 font-semibold text-body rounded-xl transition-colors cursor-pointer flex items-center gap-1.5 whitespace-nowrap shrink-0">
      <i data-lucide="arrow-left" class="w-4 h-4"></i><span>1단계 데이터 반입으로 돌아가기</span>
    </a>
    <p id="next-hint" class="text-xs text-ink-3 ml-auto text-right">이상치 탐지를 실행해 결과를 받으면 다음 단계로 진행할 수 있습니다.</p>
    <button type="button" id="btn-next" disabled class="px-5 py-2.5 bg-brand hover:bg-brand-dark disabled:bg-rule-3 disabled:cursor-not-allowed text-white font-bold text-body rounded-xl transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap shrink-0">
      <span>3단계 데이터 탐색으로 이동</span><i data-lucide="arrow-right" class="w-4 h-4"></i>
    </button>
  </div>
</div>

<%@ include file="layout/bottom.jsp" %>
<script src="${ctx}/static/js/step2.js"></script>
</body>
</html>
