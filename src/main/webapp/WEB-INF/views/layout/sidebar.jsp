<%@ page pageEncoding="UTF-8" %>
<c:set var="mIdx" value="${activeStep == 'import' ? 0 : activeStep == 'preprocess' ? 1 : activeStep == 'eda' ? 2 : activeStep == 'modeling' ? 3 : 4}" />
<%-- 펼침 상태 --%>
<aside id="main-sidebar" class="w-60 bg-white border-r border-rule/80 flex flex-col shrink-0 select-none transition-colors duration-300">
  <div class="p-4 flex-1 flex flex-col space-y-6">
    <div class="space-y-3">
      <div class="flex items-center justify-between px-1">
        <span class="text-body font-semibold text-ink-2 sb-full">분석 파이프라인</span>
        <button type="button" id="sb-toggle" class="p-1 rounded-lg text-ink-4 hover:text-ink-1 hover:bg-paper-2 transition-colors cursor-pointer" title="사이드바 접기/펼치기" aria-label="사이드바 접기/펼치기">
          <i data-lucide="chevron-left" class="w-3.5 h-3.5" id="sb-toggle-icon"></i>
        </button>
      </div>

      <div class="space-y-1">
        <%-- 1 --%>
        <a href="${ctx}/analysis/step1" class="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between cursor-pointer ${mIdx == 0 ? 'bg-brand text-white shadow-xs' : 'text-ink-2 hover:bg-paper-3 hover:text-ink'}" title="1. 데이터 반입">
          <div class="flex items-center gap-2.5"><i data-lucide="database" class="w-4 h-4 shrink-0 ${mIdx == 0 ? 'text-white' : 'text-ink-4'}"></i><span class="sb-full">1. 데이터 반입</span></div>
          <c:if test="${mIdx == 0}"><span class="w-1.5 h-1.5 rounded-full bg-blue-300 sb-full"></span></c:if>
        </a>
        <%-- 2 --%>
        <a href="${ctx}/analysis/step2" class="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between cursor-pointer ${mIdx == 1 ? 'bg-brand text-white shadow-xs' : 'text-ink-2 hover:bg-paper-3 hover:text-ink'}" title="2. 품질 및 전처리">
          <div class="flex items-center gap-2.5"><i data-lucide="shield-check" class="w-4 h-4 shrink-0 ${mIdx == 1 ? 'text-white' : 'text-ink-4'}"></i><span class="sb-full">2. 품질 및 전처리</span></div>
          <c:if test="${mIdx == 1}"><span class="w-1.5 h-1.5 rounded-full bg-blue-300 sb-full"></span></c:if>
        </a>
        <%-- 3 --%>
        <a href="${ctx}/analysis/step3" class="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between cursor-pointer ${mIdx == 2 ? 'bg-brand text-white shadow-xs' : 'text-ink-2 hover:bg-paper-3 hover:text-ink'}" title="3. 데이터 탐색">
          <div class="flex items-center gap-2.5"><i data-lucide="bar-chart-2" class="w-4 h-4 shrink-0 ${mIdx == 2 ? 'text-white' : 'text-ink-4'}"></i><span class="sb-full">3. 데이터 탐색</span></div>
          <c:if test="${mIdx == 2}"><span class="w-1.5 h-1.5 rounded-full bg-blue-300 sb-full"></span></c:if>
        </a>
        <%-- 4 (그룹) --%>
        <div class="space-y-1">
          <a href="${ctx}/analysis/step4" class="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between cursor-pointer ${mIdx == 3 && subTab != 'report' ? 'bg-brand text-white shadow-xs' : (mIdx == 3 ? 'bg-blue-50 text-blue-900 font-bold' : 'text-ink-2 hover:bg-paper-3 hover:text-ink')}" title="4. 통계 모델링">
            <div class="flex items-center gap-2.5"><i data-lucide="cpu" class="w-4 h-4 shrink-0 ${mIdx == 3 && subTab != 'report' ? 'text-white' : 'text-ink-4'}"></i><span class="sb-full">4. 통계 모델링</span></div>
          </a>
          <div class="pl-3.5 space-y-0.5 border-l border-rule ml-4 py-0.5 sb-full">
            <a href="${ctx}/analysis/step4" class="w-full text-left px-2 py-1.5 rounded-lg text-xs transition-colors flex items-center gap-1.5 cursor-pointer ${mIdx == 3 && subTab != 'report' ? 'text-blue-700 font-bold bg-blue-50/60' : 'text-ink-3 hover:text-ink'}">
              <i data-lucide="sliders" class="w-3 h-3"></i><span>4-1. 모형 설정·실행</span>
            </a>
            <a href="${ctx}/analysis/step4/report" class="w-full text-left px-2 py-1.5 rounded-lg text-xs transition-colors flex items-center gap-1.5 cursor-pointer ${mIdx == 3 && subTab == 'report' ? 'text-blue-700 font-bold bg-blue-50/60' : 'text-ink-3 hover:text-ink'}">
              <i data-lucide="file-text" class="w-3 h-3"></i><span>4-2. 차트·원시데이터</span>
            </a>
          </div>
        </div>
        <%-- 5 --%>
        <a href="${ctx}/analysis/step5" class="w-full text-left px-3 py-2 rounded-xl text-xs font-semibold transition-colors flex items-center justify-between cursor-pointer ${mIdx == 4 ? 'bg-brand text-white shadow-xs' : 'text-ink-2 hover:bg-paper-3 hover:text-ink'}" title="5. 결과 관리">
          <div class="flex items-center gap-2.5"><i data-lucide="archive" class="w-4 h-4 shrink-0 ${mIdx == 4 ? 'text-white' : 'text-ink-4'}"></i><span class="sb-full">5. 결과 관리</span></div>
          <c:if test="${mIdx == 4}"><span class="w-1.5 h-1.5 rounded-full bg-blue-300 sb-full"></span></c:if>
        </a>
      </div>
    </div>
  </div>
</aside>
