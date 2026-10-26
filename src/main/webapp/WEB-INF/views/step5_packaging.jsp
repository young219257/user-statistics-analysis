<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ include file="layout/top.jsp" %>

<div class="space-y-6">

  <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
    <div>
      <h3 class="text-[28px] font-bold text-ink tracking-tight break-keep">분석 결과 관리 및 재현 패키지</h3>
      <p class="step-lead">저장한 분석 결과를 다시 열거나 내려받습니다.</p>
    </div>
  </div>

  <div id="pk-notice" class="hidden p-3.5 bg-paper-3 border border-rule rounded-lg text-body text-ink items-center gap-2 ">
    <span id="pk-notice-msg"></span>
  </div>

  <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
    <%-- 좌: 패키지 목록 --%>
    <div class="lg:col-span-5 space-y-4">
      <div class="card-modern p-4 space-y-3">
        <div class="flex items-center justify-between pb-2 border-b border-paper-2">
          <h4 class="text-title font-semibold text-ink" id="pk-title">저장된 분석 패키지</h4>
        </div>
        <div class="space-y-2.5 max-h-[420px] overflow-y-auto pr-1" id="pk-list"></div>
      </div>
    </div>

    <%-- 우: 상세 --%>
    <div class="lg:col-span-7 card-modern p-5 space-y-4" id="pk-detail"></div>
  </div>

  <div class="flex justify-start pt-1">
    <a href="${ctx}/analysis/step4" class="px-4 py-2.5 bg-white hover:bg-paper-2 text-ink-1 font-semibold text-body rounded-xl transition-colors border border-rule cursor-pointer flex items-center gap-1.5 whitespace-nowrap shrink-0">
      <i data-lucide="arrow-left" class="w-4 h-4"></i><span>4단계 통계 모델링으로 돌아가기</span>
    </a>
  </div>
</div>

<%@ include file="layout/bottom.jsp" %>
<script src="${ctx}/static/js/step5.js"></script>
</body>
</html>
