<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ include file="layout/top.jsp" %>

<div class="space-y-6">

  <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
    <div>
      <h3 class="text-[24px] font-bold text-ink tracking-tight break-keep">통계 모형 설정 및 연산 실행</h3>
    </div>
    <div class="flex items-center gap-2 shrink-0 flex-wrap">
      <span id="fit-badge" class="hidden px-3 py-1.5 rounded-xl bg-emerald-50 text-emerald-800 border border-emerald-200 text-xs font-bold items-center gap-1.5">
        <i data-lucide="check-circle-2" class="w-3.5 h-3.5 text-emerald-600"></i><span>적합 완료</span>
      </span>
    </div>
  </div>

  <%-- 분석 기법 선택 --%>
  <div class="card-modern p-3.5 sm:p-4 space-y-2.5">
    <div class="flex items-center justify-between">
      <h4 class="text-title font-semibold text-ink">분석 기법 선택</h4>
    </div>
    <div class="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-2.5" id="method-grid"></div>
  </div>

  <%-- 변수 및 파라미터 --%>
  <div class="bg-white rounded-xl border border-rule p-4 sm:p-5 space-y-4">
    <div class="space-y-4">
      <div class="pb-2.5 border-b border-paper-2 flex items-center justify-between">
        <h4 class="text-title font-semibold text-ink">변수 및 파라미터 설정</h4>
      </div>
      <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div class="space-y-4">
          <div id="target-box"></div>
          <div class="space-y-1.5">
            <div class="flex items-center justify-between text-xs">
              <label class="font-semibold text-ink-0" id="feat-title">독립변수 (Features / X)</label>
              <div class="flex items-center gap-1.5 text-xs">
                <button type="button" id="feat-all" class="text-blue-700 hover:text-blue-800 hover:underline cursor-pointer font-medium">전체선택</button>
                <span class="text-rule-3">|</span>
                <button type="button" id="feat-none" class="text-ink-4 hover:underline cursor-pointer">해제</button>
                <span class="ml-1 px-2 py-0.5 bg-blue-50 text-blue-800 border border-blue-200 rounded font-mono font-bold text-xs" id="feat-count">0개 선택</span>
              </div>
            </div>
            <div class="border border-rule rounded-lg p-2 max-h-52 overflow-y-auto space-y-1 bg-paper-3/40" id="feat-list"></div>
          </div>
        </div>
        <div id="extra-params" class="space-y-3"></div>
      </div>
    </div>
    <div class="pt-2">
      <button type="button" id="btn-run" class="w-full py-3 bg-brand hover:bg-brand-dark disabled:opacity-50 text-white font-bold text-xs rounded-xl transition-colors cursor-pointer flex items-center justify-center gap-2">
        <i data-lucide="play" class="w-3.5 h-3.5"></i><span>통계 모델 분석 실행 (Run)</span>
      </button>
    </div>
  </div>

  <%-- 통계 결과 (성공/실패) --%>
  <div class="card-modern p-4 sm:p-5" id="result-panel"></div>

  <%-- 파이프라인 조건 --%>
  <div class="card-modern overflow-hidden">
    <button type="button" id="pipe-toggle" class="w-full px-4 py-3 bg-paper-3/70 hover:bg-paper-2/70 flex items-center justify-between text-left transition-colors cursor-pointer border-b border-paper-2">
      <div class="flex items-center gap-2">
        <span class="text-title font-semibold text-ink">분석 파이프라인 조건 및 사전 전처리 검토 명세</span>
        <span class="px-1.5 py-0.5 rounded text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">검증 완료</span>
      </div>
      <div class="flex items-center gap-2 text-xs text-ink-3"><span id="pipe-txt">상세 보기</span><i data-lucide="chevron-down" class="w-4 h-4 text-ink-4" id="pipe-ic"></i></div>
    </button>
    <div id="pipe-body" class="hidden"></div>
  </div>

  <div class="flex flex-wrap justify-between items-center gap-3 pt-2">
    <a href="${ctx}/analysis/step3" class="px-4 py-2.5 bg-white hover:bg-paper-2 text-ink-1 font-semibold text-body rounded-lg transition-colors border border-rule cursor-pointer flex items-center gap-1.5 whitespace-nowrap shrink-0">
      <i data-lucide="arrow-left" class="w-4 h-4"></i><span>3단계 데이터 탐색(EDA)으로 돌아가기</span>
    </a>
    <a href="${ctx}/analysis/step4/report" class="px-4 py-2.5 bg-brand hover:bg-brand-dark text-white font-bold text-body rounded-lg transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap shrink-0">
      <span>4-2. 진단 차트 및 원시데이터 확인</span><i data-lucide="arrow-right" class="w-4 h-4"></i>
    </a>
  </div>
</div>

<%@ include file="layout/bottom.jsp" %>
<script src="${ctx}/static/js/step4.js"></script>
</body>
</html>
