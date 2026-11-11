<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ include file="layout/top.jsp" %>

<div class="space-y-6" id="step1-root">

  <%-- 1. 상단 페이지 헤더 --%>
  <div class="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
    <div>
      <h3 class="text-[28px] font-bold text-ink tracking-tight break-keep">분석 대상 데이터 준비</h3>
      <p class="step-lead">분석할 데이터를 고르고 사용할 열을 확인합니다.</p>
    </div>
  </div>

  <%-- 2. 데이터 고르기: 데이터관리카드·반입 데이터셋 모두 여러 개 선택 가능 --%>
  <div class="grid grid-cols-1 lg:grid-cols-12 gap-6">
    <div class="lg:col-span-5 card-modern sec flex flex-col">
      <div class="sec-head flex items-center justify-between">
        <div class="flex items-center gap-2">
<h3 class="text-title font-semibold text-ink">데이터관리카드</h3>
        </div>
        <div class="flex items-center gap-2">
          <span class="text-xs font-medium text-ink-4" id="mgmt-total"></span>
        </div>
      </div>
      <div class="sec-box flex flex-col space-y-3 flex-1">
      <div class="relative">
        <input type="text" id="mgmt-search" aria-label="데이터관리카드 검색" placeholder="데이터관리카드 검색" class="w-full bg-paper-3/80 border border-rule rounded-xl px-3 py-2 pl-8 text-xs text-ink-0 placeholder-ink-4 focus:outline-none focus:ring-2 focus:ring-blue-600/20 focus:border-blue-600 transition-colors">
        <i data-lucide="search" class="w-3.5 h-3.5 text-ink-4 absolute left-2.5 top-1/2 -translate-y-1/2"></i>
      </div>
      <div id="mgmt-list" class="border border-rule/80 rounded-xl divide-y divide-paper-2 h-[360px] shrink-0 overflow-y-auto bg-white"></div>
      </div>
    </div>

    <div class="lg:col-span-7 flex flex-col gap-4">
      <div class="card-modern sec">
        <div class="sec-head">
          <%-- KRDS 맥락적 도움말: 아이콘 버튼 → 팝오버 (동작은 common.js 가 공통 처리) --%>
          <div class="krds-contextual-help bottom left">
            <h3 class="tooltip-txt text-title font-semibold text-ink">데이터 업로드</h3>
            <div class="tooltip-action">
              <button type="button" id="btn-upload-help" class="tooltip-btn" aria-expanded="false" aria-controls="upload-help">
                <span class="sr-only">데이터 업로드 도움말</span>
                <i class="svg-icon ico-tooltip" aria-hidden="true"></i>
              </button>
              <div id="upload-help" class="tooltip-popover" role="tooltip" hidden>
                <h4 class="tooltip-title">데이터 반입 안내</h4>
                <div class="tooltip-contents">
                  <dl>
                  <dt>파일 형식·크기</dt>
                  <dd>CSV, XLSX. 한글 CSV는 UTF-8·CP949 모두 가능합니다. 파일 1건당 최대 10MB이며, 여러 파일을 한 번에 선택해도 됩니다.</dd>
                  <dt>분석·결합 용량</dt>
                  <dd>선택한 데이터셋의 합계가 30MB 이하여야 합니다. 남은 용량을 넘는 데이터셋은 선택할 수 없습니다.</dd>
                  <dt>XLSX 시트</dt>
                  <dd>첫 번째 시트만 반입됩니다. 시트가 하나인 파일을 권장합니다.</dd>
                  <dt>열 작성</dt>
                  <dd>한 열에 숫자와 문자가 섞여 있으면 문자 열로 반입됩니다. 숫자로 분석하려면 타입을 수치형으로 바꾸세요.</dd>
                  <dt>보관</dt>
                  <dd>반입한 데이터는 세션이 끝나면 삭제됩니다.</dd>
                </dl>
                </div>
                <button type="button" class="tooltip-close">
                  <span class="sr-only">닫기</span>
                  <i class="svg-icon ico-modal-close" aria-hidden="true"></i>
                </button>
              </div>
            </div>
          </div>
        </div>
        <div class="sec-box">
          <div id="upload-area"></div>
        </div>
      </div>
      <div class="card-modern sec flex flex-col flex-1">
        <div class="sec-head flex items-center justify-between">
          <div class="flex items-center gap-2">
<h3 class="text-title font-semibold text-ink">반입된 데이터셋</h3>
          </div>
          <span class="text-xs text-ink-4" id="ds-total"></span>
        </div>
        <div class="sec-box flex flex-col flex-1">
        <div id="ds-list" class="border border-rule/80 rounded-xl divide-y divide-paper-2 flex-1 min-h-[180px] overflow-y-auto bg-white"></div>
        <div id="ds-limit"></div>
        </div>
      </div>
    </div>
  </div>

  <%-- 3. 선택한 데이터: 데이터셋마다 분석에 쓸 열 고르기 --%>
  <div class="card-modern sec" id="col-card">
    <div class="sec-head">
            <h3 class="text-title font-semibold text-ink" id="col-title">선택한 데이터</h3>
            <p class="text-xs text-ink-3">데이터셋마다 분석에 사용할 열을 체크하세요. 쓰지 않는 열을 빼면 처리량이 줄어듭니다.</p>
    </div>
    <div class="sec-box sec-flush">
    <div class="p-4 border-b border-rule/80 bg-white space-y-3">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div id="s1-tabs" class="flex flex-wrap items-center gap-1.5"></div>
        <div class="flex items-center gap-2">
          <div class="relative">
            <input type="text" id="col-search" aria-label="변수명 검색" placeholder="변수명 검색" class="bg-paper-3 border border-rule rounded-lg pl-7 pr-2.5 py-1 text-xs text-ink-0 placeholder-ink-4 focus:outline-none focus:border-blue-600">
            <i data-lucide="search" class="w-3.5 h-3.5 text-ink-4 absolute left-2 top-1/2 -translate-y-1/2"></i>
          </div>
        </div>
      </div>
    </div>
    <div class="overflow-x-auto max-h-[300px] overflow-y-auto">
      <table class="w-full min-w-[520px] text-left text-body border-collapse whitespace-nowrap">
        <thead class="sticky top-0 bg-paper-3 z-10 border-b border-rule/80">
          <tr class="text-ink-3 font-semibold text-xs">
            <th class="py-2.5 px-4 w-28"><label class="flex items-center gap-1.5 cursor-pointer"><input type="checkbox" id="col-all" class="accent-brand"><span>분석 사용</span></label></th>
            <th class="py-2.5 px-4">변수명</th>
            <th class="py-2.5 px-4 text-right">고유값</th>
            <th class="py-2.5 px-4 w-48">타입</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-paper-2 text-body" id="col-body"></tbody>
      </table>
    </div>
        </div>
  </div>

  <%-- 4. 데이터 결합 설정 (2개 이상 선택 시) --%>
  <div class="card-modern sec hidden" id="merge-card"></div>

  <%-- 5. 데이터 미리보기 --%>
  <div class="card-modern sec" id="preview-card">
    <div class="sec-head flex items-center justify-between bg-white" id="preview-toggle" role="button" tabindex="0" aria-expanded="true" aria-controls="preview-scroll">
      <div class="flex items-center gap-2">
<h3 class="text-title font-semibold text-ink">데이터 미리보기</h3>
        <span class="text-xs text-ink-4 font-mono" id="preview-count"></span>
      </div>
      <span class="flex items-center gap-3"><span class="text-xs text-ink-4" id="preview-name"></span><i data-lucide="chevron-down" class="w-4 h-4 text-ink-4 preview-chev" aria-hidden="true"></i></span>
    </div>
    <div id="preview-scroll" class="sec-box sec-flush overflow-x-auto overflow-y-auto max-h-[320px]">
      <table class="w-full text-left text-body border-collapse">
        <thead class="sticky top-0 bg-paper-3/95 z-10 border-b border-rule/80" id="preview-head"></thead>
        <tbody class="divide-y divide-paper-2 font-mono text-body" id="preview-body"></tbody>
      </table>
      <div id="preview-more" class="hidden p-2 text-center text-xs text-ink-4 items-center justify-center gap-2">
        <span class="w-3 h-3 border-2 border-blue-600 border-t-transparent rounded-full spin inline-block"></span><span>데이터를 불러오는 중입니다</span>
      </div>
    </div>
  </div>

  <div id="s1-msg" role="alert" class="hidden krds-msg krds-danger items-start gap-2 py-1.5"></div>

  <%-- 6. 하단 액션 --%>
  <div class="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4">
    <button type="button" id="btn-proceed" class="sm:ml-auto px-6 py-2.5 bg-brand hover:bg-brand-dark disabled:bg-rule-3 disabled:cursor-not-allowed text-white font-semibold text-body rounded-xl transition-colors cursor-pointer flex items-center gap-2 whitespace-nowrap shrink-0">
      <span>2단계 품질 진단으로 이동</span><i data-lucide="arrow-right" class="w-4 h-4"></i>
    </button>
  </div>
</div>

<%@ include file="layout/bottom.jsp" %>
<script src="${ctx}/static/js/ot_dim_dmmbm03_m01.js?v=20261136"></script>
</body>
</html>
