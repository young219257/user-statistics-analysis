<%@ page language="java" contentType="text/html; charset=UTF-8" pageEncoding="UTF-8"%>
<%@ taglib prefix="c" uri="http://java.sun.com/jsp/jstl/core" %>
  </main>
</div>

<%-- ============================ 푸터 (교육데이터플랫폼 www.edmgr.kr 공통 푸터와 동일한 구성) ============================ --%>
<c:set var="portal" value="https://www.edmgr.kr" />
<footer id="footer" class="mt-12 bg-paper-2 text-ink-2">
  <%-- 관련 기관 --%>
  <div class="bg-white border-y border-rule-2">
    <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9">
      <div class="relative w-[212px]" id="family-site">
        <button type="button" id="btn-family" aria-expanded="false" class="w-full flex items-center justify-between px-6 h-14 -my-px border-x border-rule-2 text-[15px] text-ink bg-white hover:bg-paper-3 cursor-pointer">
          <span>관련 기관</span><i data-lucide="plus" class="w-3.5 h-3.5"></i>
        </button>
        <ul id="family-list" class="hidden absolute bottom-full left-0 w-full max-h-80 overflow-y-auto bg-white border border-rule-2 shadow-lg py-1 z-40">
          <li><a href="https://www.moe.go.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">교육부</a></li>
          <li><a href="https://mods.go.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">국가데이터처</a></li>
          <li><a href="https://www.nile.or.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">국가평생교육진흥원</a></li>
          <li><a href="https://www.kosac.re.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국과학창의재단</a></li>
          <li><a href="https://www.kedi.re.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국교육개발원</a></li>
          <li><a href="https://www.kice.re.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국교육과정평가원</a></li>
          <li><a href="https://www.keris.or.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국교육학술정보원</a></li>
          <li><a href="https://www.kcue.or.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국대학교육협의회</a></li>
          <li><a href="https://www.kasfo.or.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국사학진흥재단</a></li>
          <li><a href="https://www.kosaf.go.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국장학재단</a></li>
          <li><a href="https://www.krivet.re.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국직업능력연구원</a></li>
          <li><a href="https://www.nypi.re.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국청소년정책연구원</a></li>
          <li><a href="https://ssif.or.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">학교안전공제중앙회</a></li>
          <li><a href="https://www.koies.or.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국교육시설안전원</a></li>
          <li><a href="https://www.schoolkeepa.or.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">한국교육환경보호원</a></li>
          <li><a href="https://kicce.re.kr" target="_blank" title="새창" class="block px-4 py-2 text-[15px] text-ink hover:bg-paper-2">육아정책연구소</a></li>
        </ul>
      </div>
    </div>
  </div>
  <div class="max-w-[1440px] mx-auto px-4 sm:px-6 lg:px-9 pt-10 pb-12">
    <img src="${ctx}/static/vendor/edmgr-header-logo.svg" alt="교육데이터플랫폼" class="h-9 w-auto">
    <div class="mt-8 text-[17px] leading-relaxed" style="word-break: keep-all;">
      <address class="not-italic mb-3">
        <strong>(30119)</strong> 세종특별자치시 갈매로 408, 14동 정부세종청사 (교육부)<br>
        <strong>(41061)</strong> 대구광역시 동구 동내로 64 (한국교육학술정보원)
      </address>
      <div class="flex flex-wrap items-center gap-x-6 gap-y-1">
        <span class="font-bold text-ink">문의 edudataadm@keris.or.kr</span>
        <span>☎ 1644-7756(상담센터)</span>
      </div>
    </div>
    <div class="mt-8 pt-4 border-t border-rule-2 flex flex-col lg:flex-row lg:items-end justify-between gap-6">
      <div>
        <div class="flex flex-wrap items-center gap-6 text-[15px] text-ink">
          <a href="javascript:window.open('${portal}/agreement','agreement','width=1024,height=800,scrollbars=yes');" title="새창으로 이동" class="py-2 hover:underline">이용약관</a>
          <a href="javascript:window.open('${portal}/privacy','privacy','width=1024,height=800,scrollbars=yes');" title="새창으로 이동" class="py-2 font-bold text-alert hover:underline">개인정보처리방침</a>
          <a href="javascript:window.open('${portal}/copyright','copyright','width=1024,height=800,scrollbars=yes');" title="새창으로 이동" class="py-2 hover:underline">저작권정책</a>
        </div>
        <p class="mt-4 mb-0 text-[15px] text-ink-3">COPYRIGHTⓒEDMGR. ALL Rights Reserved.</p>
      </div>
      <div class="flex items-center gap-6">
        <a href="https://www.moe.go.kr" target="_blank" title="새창열림"><img src="${ctx}/static/vendor/portal/footer-logo-edu.svg" alt="교육부" class="h-9 w-auto"></a>
        <span class="text-[15px] font-bold text-ink">시도교육청</span>
        <a href="https://www.keris.or.kr" target="_blank" title="새창열림"><img src="${ctx}/static/vendor/portal/img_footer_bn_1.png" alt="KERIS" class="h-9 w-auto"></a>
      </div>
    </div>
  </div>
</footer>

<%-- ============================ 도움말 모달 (실제 기능·서버 제한값 기준) ============================ --%>
<div id="help-modal" role="dialog" aria-modal="true" aria-labelledby="help-title" class="hidden fixed inset-0 bg-ink/50 items-center justify-center z-50 p-4">
  <div class="bg-white rounded-xl shadow-xl max-w-2xl w-full border border-rule overflow-hidden max-h-[90vh] flex flex-col">
    <div class="px-6 py-4 border-b border-rule flex items-center justify-between">
      <h2 id="help-title" class="text-[17px] font-bold text-ink">이용자통계분석 이용 안내</h2>
      <button type="button" data-close="help-modal" class="p-1.5 text-ink-3 hover:text-ink rounded-md hover:bg-paper-2 cursor-pointer" aria-label="닫기"><i data-lucide="x" class="w-5 h-5"></i></button>
    </div>
    <div class="px-6 py-4 overflow-y-auto">
      <p class="text-[13px] text-ink-2">분석은 다섯 단계로 진행합니다. 상단 단계 바에서 각 단계로 이동할 수 있습니다.</p>
      <ol class="mt-2">
        <li class="flex gap-3 py-3 border-t border-rule first:border-t-0">
          <span class="w-6 h-6 shrink-0 rounded-full bg-brand text-white text-xs font-bold flex items-center justify-center">1</span>
          <div><div class="text-[15px] font-bold text-ink">데이터 반입</div><p class="mt-0.5 text-[13px] leading-relaxed text-ink-2">데이터관리카드나 직접 올린 파일(CSV·TXT·XLSX·XLS·JSON·Parquet, 최대 10MB)을 고릅니다. 여러 개를 고르면 공통 키로 결합하고, 데이터셋마다 분석에 쓸 열을 체크할 수 있습니다.</p></div>
        </li>
        <li class="flex gap-3 py-3 border-t border-rule first:border-t-0">
          <span class="w-6 h-6 shrink-0 rounded-full bg-brand text-white text-xs font-bold flex items-center justify-center">2</span>
          <div><div class="text-[15px] font-bold text-ink">품질 및 전처리</div><p class="mt-0.5 text-[13px] leading-relaxed text-ink-2">결측치·중복 행을 확인하고, 이상치 탐지 기법을 골라 탐지합니다. 결측치·이상치·스케일링 규칙을 정하면 3단계로 넘어갈 때 규칙이 적용된 새 데이터셋이 만들어집니다. 원본은 바뀌지 않습니다.</p></div>
        </li>
        <li class="flex gap-3 py-3 border-t border-rule first:border-t-0">
          <span class="w-6 h-6 shrink-0 rounded-full bg-brand text-white text-xs font-bold flex items-center justify-center">3</span>
          <div><div class="text-[15px] font-bold text-ink">데이터 탐색</div><p class="mt-0.5 text-[13px] leading-relaxed text-ink-2">수치형 변수의 기술통계와 상관행렬(피어슨·스피어만·켄달)을 확인합니다.</p></div>
        </li>
        <li class="flex gap-3 py-3 border-t border-rule first:border-t-0">
          <span class="w-6 h-6 shrink-0 rounded-full bg-brand text-white text-xs font-bold flex items-center justify-center">4</span>
          <div><div class="text-[15px] font-bold text-ink">통계 모델링</div><p class="mt-0.5 text-[13px] leading-relaxed text-ink-2">상관분석·회귀·의사결정나무·군집·주성분·분산분석·다층모형·성장곡선·성향점수매칭 등 13개 기법 중 하나를 골라 변수와 파라미터를 정하고 실행합니다. 결과 리포트에서 기법별 통계표와 추천 차트를 확인합니다.</p></div>
        </li>
        <li class="flex gap-3 py-3 border-t border-rule first:border-t-0">
          <span class="w-6 h-6 shrink-0 rounded-full bg-brand text-white text-xs font-bold flex items-center justify-center">5</span>
          <div><div class="text-[15px] font-bold text-ink">결과 관리</div><p class="mt-0.5 text-[13px] leading-relaxed text-ink-2">저장한 분석 패키지를 조회·삭제하고, 공유 링크(7일 유지)를 만들거나 같은 조건으로 다시 분석합니다. PDF 보고서와 Excel 통계표로 내보낼 수 있습니다.</p></div>
        </li>
      </ol>
      <p class="mt-2 pt-3 border-t border-rule text-xs text-ink-3">반입한 데이터와 분석 결과는 마지막 사용 후 1시간이 지나면 삭제됩니다. 공유 링크를 만든 분석 패키지만 7일간 보관됩니다.</p>
    </div>
    <div class="px-6 py-3 border-t border-rule flex justify-end">
      <button type="button" data-close="help-modal" class="px-4 py-2 bg-brand hover:bg-brand-dark text-white font-bold rounded-xl text-[13px] transition-colors cursor-pointer">닫기</button>
    </div>
  </div>
</div>

<%-- ============================ 로그인 안내 (계정 인증은 교육데이터플랫폼 포털에서) ============================ --%>
<div id="login-modal" role="dialog" aria-modal="true" aria-labelledby="login-title" class="hidden fixed inset-0 bg-ink/50 items-center justify-center z-50 p-4">
  <div class="bg-white rounded-xl shadow-xl max-w-md w-full border border-rule overflow-hidden">
    <div class="px-6 py-4 border-b border-rule flex items-center justify-between">
      <h2 id="login-title" class="text-[17px] font-bold text-ink">로그인</h2>
      <button type="button" data-close="login-modal" class="p-1.5 text-ink-3 hover:text-ink rounded-md hover:bg-paper-2 cursor-pointer" aria-label="닫기"><i data-lucide="x" class="w-5 h-5"></i></button>
    </div>
    <div class="px-6 py-5 text-[13px] text-ink-2 leading-relaxed">
      로그인은 교육데이터플랫폼 계정으로 합니다. 이용자통계분석은 로그인하지 않아도 이용할 수 있으며, 반입한 데이터는 현재 브라우저 세션에만 보관됩니다.
    </div>
    <div class="px-6 py-3 border-t border-rule flex justify-end gap-2">
      <button type="button" data-close="login-modal" class="px-4 py-2 bg-white border border-rule-3 hover:bg-paper-2 text-ink font-semibold rounded-xl text-[13px] transition-colors cursor-pointer">닫기</button>
      <a href="https://www.edmgr.kr/" class="px-4 py-2 bg-brand hover:bg-brand-dark text-white font-bold rounded-xl text-[13px] transition-colors whitespace-nowrap">교육데이터플랫폼으로 이동</a>
    </div>
  </div>
</div>

<%-- 확인 창 (되돌릴 수 없는 삭제에만 사용 · App.confirm) --%>
<div id="confirm-modal" role="alertdialog" aria-modal="true" aria-labelledby="confirm-msg" class="hidden fixed inset-0 bg-ink/50 items-center justify-center z-50 p-4">
  <div class="bg-white rounded-xl shadow-xl max-w-sm w-full border border-rule overflow-hidden">
    <p id="confirm-msg" class="px-6 pt-5 pb-4 text-[15px] font-semibold text-ink leading-relaxed"></p>
    <div class="px-6 pb-5 flex justify-end gap-2">
      <button type="button" id="confirm-no" class="px-4 py-2 bg-white border border-rule-3 hover:bg-paper-2 text-ink font-semibold rounded-xl text-[13.5px] transition-colors cursor-pointer whitespace-nowrap">취소</button>
      <button type="button" id="confirm-yes" class="px-4 py-2 bg-rose-700 hover:bg-rose-800 text-white font-semibold rounded-xl text-[13.5px] transition-colors cursor-pointer whitespace-nowrap">삭제</button>
    </div>
  </div>
</div>

<%-- 토스트 --%>
<div id="toast" role="status" aria-live="polite" aria-atomic="true" class="hidden fixed bottom-6 right-6 z-50 bg-ink text-white px-4 py-2.5 rounded-lg shadow-lg text-[13.5px] font-medium border border-ink-1 items-center gap-2 anim-in max-w-md">
  <span class="toast-dot" aria-hidden="true"></span><span id="toast-msg"></span>
</div>

<script>window.__CTX__ = '${ctx}';</script>
<script src="${ctx}/static/js/common.js"></script>
<script src="${ctx}/static/js/viz.js"></script>
