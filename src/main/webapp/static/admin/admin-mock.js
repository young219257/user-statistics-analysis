/* 관리자 화면(초안) 목업 데이터. 실제 API 가 생기면 admin.js 의 api 객체만 fetch 로 바꾸면 된다.
 * 이름(JobKind, DatasetSource, share_grace_period_days 등)은 서버 용어를 따랐다. 값은 모두 가짜다. */
(function () {
  var NOW = Date.now();
  var MIN = 60 * 1000, HOUR = 60 * MIN, DAY = 24 * HOUR;
  function ago(ms) { return new Date(NOW - ms).toISOString(); }
  function ahead(ms) { return new Date(NOW + ms).toISOString(); }

  var settings = {
    job_pending_timeout_seconds: 300,
    job_time_limit_seconds: 1800,
    share_grace_period_days: 7
  };

  var sessions = [
    { id: 'sess_8f21c0a4', status: 'active', last_heartbeat: ago(40 * 1000), datasets: 3, jobs: 5 },
    { id: 'sess_1a77be09', status: 'active', last_heartbeat: ago(3 * MIN), datasets: 1, jobs: 2 },
    { id: 'sess_c04d9e12', status: 'active', last_heartbeat: ago(9 * MIN), datasets: 6, jobs: 11 },
    { id: 'sess_5be2f7d3', status: 'idle', last_heartbeat: ago(48 * MIN), datasets: 2, jobs: 0 },
    { id: 'sess_92aa31ce', status: 'idle', last_heartbeat: ago(2 * HOUR + 10 * MIN), datasets: 4, jobs: 3 },
    { id: 'sess_d3e80b55', status: 'expired', last_heartbeat: ago(7 * HOUR), datasets: 1, jobs: 1 },
    { id: 'sess_77f0a9b1', status: 'active', last_heartbeat: ago(25 * 1000), datasets: 0, jobs: 1 }
  ];

  var jobs = [
    { id: 'job_01hx7a', kind: 'analysis', status: 'running', session: 'sess_c04d9e12', created: ago(47 * MIN), started: ago(46 * MIN), elapsed_s: 46 * 60,
      title: '선형회귀 - 학교별 지원금', error: null },
    { id: 'job_01hx7b', kind: 'merge', status: 'pending', session: 'sess_8f21c0a4', created: ago(18 * MIN), started: null, elapsed_s: 0,
      title: '결합_급식비집행실적+법인회계', error: null },
    { id: 'job_01hx7c', kind: 'ingest', status: 'queued', session: 'sess_1a77be09', created: ago(40 * 1000), started: null, elapsed_s: 0,
      title: '학생독서행태_시군구별.xlsx 반입', error: null },
    { id: 'job_01hx7d', kind: 'analysis', status: 'failed', session: 'sess_c04d9e12', created: ago(3 * HOUR), started: ago(3 * HOUR - 20 * 1000), elapsed_s: 1800,
      title: '의사결정나무(회귀) - 전국 학교', error: { code: 'timeout', message: '작업이 제한 시간(1800초)을 넘어 종료되었습니다.', reason: 'timeout' } },
    { id: 'job_01hx7e', kind: 'analysis', status: 'failed', session: 'sess_92aa31ce', created: ago(5 * HOUR), started: ago(5 * HOUR - 8 * 1000), elapsed_s: 412,
      title: 'K-평균 군집 - 지역별 참여율', error: { code: 'oom', message: '메모리 한도를 넘어 워커가 종료되었습니다. (사용량 4.1GiB / 한도 4GiB)', reason: 'oom' } },
    { id: 'job_01hx7f', kind: 'profile', status: 'failed', session: 'sess_5be2f7d3', created: ago(9 * HOUR), started: ago(9 * HOUR - 3 * 1000), elapsed_s: 0,
      title: '데이터 프로파일링', error: { code: 'fail_lost', message: '워커와 연결이 끊겨 작업 결과를 잃었습니다. 워커 재시작 중 회수되었습니다.', reason: 'fail_lost' } },
    { id: 'job_01hx7g', kind: 'package_export', status: 'succeeded', session: 'sess_8f21c0a4', created: ago(25 * MIN), started: ago(25 * MIN - 2000), elapsed_s: 14,
      title: 'PDF 보고서 생성', error: null },
    { id: 'job_01hx7h', kind: 'analysis', status: 'succeeded', session: 'sess_8f21c0a4', created: ago(1 * HOUR), started: ago(1 * HOUR - 3000), elapsed_s: 92,
      title: '상관분석 - 참여율 7개', error: null },
    { id: 'job_01hx7i', kind: 'sync_data_cards', status: 'succeeded', session: 'sess_77f0a9b1', created: ago(2 * HOUR), started: ago(2 * HOUR - 1000), elapsed_s: 38,
      title: '데이터관리카드 동기화', error: null },
    { id: 'job_01hx7j', kind: 'analysis', status: 'cancelled', session: 'sess_c04d9e12', created: ago(4 * HOUR), started: ago(4 * HOUR - 5000), elapsed_s: 120,
      title: '로지스틱 회귀 - 이탈 여부', error: null },
    { id: 'job_01hx7k', kind: 'merge', status: 'running', session: 'sess_92aa31ce', created: ago(2 * MIN), started: ago(2 * MIN - 2000), elapsed_s: 118,
      title: '결합_학교별위치+급식', error: null },
    { id: 'job_01hx7l', kind: 'ingest', status: 'failed', session: 'sess_1a77be09', created: ago(6 * HOUR), started: ago(6 * HOUR - 1000), elapsed_s: 6,
      title: '교비자금예산서.csv 반입', error: { code: 'invalid_file', message: '업로드 한도(200MB)를 넘는 파일입니다.', reason: 'limit' } }
  ];

  var cards = [
    { id: 'card_001', name: '급식비집행실적(EDSS)', status: 'loaded', rows: 165717, loaded_at: ago(35 * MIN), error: null },
    { id: 'card_002', name: '법인회계자금예산서(예산)', status: 'loaded', rows: 21568, loaded_at: ago(35 * MIN), error: null },
    { id: 'card_003', name: '유초중등학생현황[교육통계][EDSS]', status: 'loaded', rows: 362164, loaded_at: ago(2 * HOUR), error: null },
    { id: 'card_004', name: '지역별사교육참여율[통계청]', status: 'loaded', rows: 203, loaded_at: ago(2 * HOUR), error: null },
    { id: 'card_005', name: '고등교육기관졸업자학생인적취업정보', status: 'failed', rows: 0, loaded_at: ago(1 * DAY + 3 * HOUR),
      error: '원천 DB 연결 시간이 초과되었습니다. (timeout 30s)' },
    { id: 'card_006', name: '교비자금예산서교비회계통합', status: 'failed', rows: 0, loaded_at: ago(1 * DAY + 3 * HOUR),
      error: '열 정의가 카드 정의와 다릅니다. (기대 12열 / 실제 11열)' },
    { id: 'card_007', name: '학교별위치정보', status: 'loaded', rows: 32889, loaded_at: ago(2 * HOUR), error: null },
    { id: 'card_008', name: '학생의체력증진에관한사항(종목별평균기록통계)', status: 'loading', rows: 0, loaded_at: null, error: null }
  ];

  var datasets = [
    { id: 'ds_a01', name: '결합_급식비집행실적+법인회계', source: 'merged', size_mb: 412.6, status: 'ready', session: 'sess_8f21c0a4' },
    { id: 'ds_a02', name: '유초중등학생현황[교육통계][EDSS]', source: 'data_card', size_mb: 268.4, status: 'ready', session: 'sess_c04d9e12' },
    { id: 'ds_a03', name: '학생독서행태_시군구별.xlsx', source: 'upload', size_mb: 3.2, status: 'ready', session: 'sess_1a77be09' },
    { id: 'ds_a04', name: '전처리_학교별지원금', source: 'preprocessed', size_mb: 96.8, status: 'ready', session: 'sess_c04d9e12' },
    { id: 'ds_a05', name: '지역별사교육참여율[통계청]', source: 'data_card', size_mb: 0.4, status: 'ready', session: 'sess_92aa31ce' },
    { id: 'ds_a06', name: '교비자금예산서.csv', source: 'upload', size_mb: 187.0, status: 'failed', session: 'sess_1a77be09' },
    { id: 'ds_a07', name: '결합_학교별위치+급식', source: 'merged', size_mb: 54.1, status: 'building', session: 'sess_92aa31ce' },
    { id: 'ds_a08', name: '급식비집행실적(EDSS)', source: 'data_card', size_mb: 131.5, status: 'ready', session: 'sess_8f21c0a4' }
  ];

  var packages = [
    { id: 'pkg_01', name: '선형회귀 결과 패키지', shared: true, size_mb: 12.3, session: 'sess_8f21c0a4', unshared_at: null, expires_at: ahead(2 * DAY + 6 * HOUR), state: 'shared' },
    { id: 'pkg_02', name: '상관분석 결과 패키지', shared: true, size_mb: 4.8, session: 'sess_c04d9e12', unshared_at: null, expires_at: ahead(6 * DAY), state: 'shared' },
    { id: 'pkg_03', name: '군집분석 결과 패키지', shared: false, size_mb: 38.9, session: 'sess_92aa31ce', unshared_at: ago(5 * DAY), expires_at: ahead(1 * DAY + 2 * HOUR), state: 'grace' },
    { id: 'pkg_04', name: '의사결정나무 결과 패키지', shared: false, size_mb: 77.2, session: 'sess_d3e80b55', unshared_at: ago(8 * DAY), expires_at: ago(1 * DAY), state: 'expired' }
  ];

  var sweeper = {
    last_run_at: ago(52 * MIN),
    last_result: { sessions_removed: 3, datasets_removed: 5, packages_removed: 1, files_removed: 42, freed_mb: 1824.5, duration_s: 6.4 },
    schedule: '매시 정각 (usa.sweep)'
  };

  var config = [
    { group: '업로드', items: [
      { key: 'upload_max_mb', label: '업로드 한도', value: '200 MB' },
      { key: 'upload_allowed_ext', label: '허용 확장자', value: 'csv, xlsx' }
    ] },
    { group: '작업', items: [
      { key: 'job_time_limit_seconds', label: '작업 시간 제한', value: '1,800 초' },
      { key: 'job_memory_limit_mb', label: '작업 메모리 제한', value: '4,096 MB' },
      { key: 'job_pending_timeout_seconds', label: 'pending 허용 시간', value: '300 초' },
      { key: 'session_max_concurrent_jobs', label: '세션당 동시 실행 한도', value: '2' }
    ] },
    { group: '보관', items: [
      { key: 'share_grace_period_days', label: '공유 해제 유예 기간', value: '7 일' },
      { key: 'session_ttl_minutes', label: '세션 유지 시간', value: '120 분' },
      { key: 'storage_dir', label: '저장소 경로', value: '/var/lib/usa/storage' }
    ] },
    { group: '연결 정보 (민감값)', items: [
      { key: 'database_dsn', label: 'DB 연결 문자열 (DSN)', value: 'postgresql://usa_app:Zx9!mK2#qL@db.internal:5432/usa', secret: true },
      { key: 'redis_url', label: 'Redis 브로커', value: 'redis://:r3d1s-s3cr3t@broker.internal:6379/0', secret: true },
      { key: 'admin_token', label: '관리자 토큰', value: 'adm_7c1e90f4b2a64d58a3f0', secret: true },
      { key: 'datasource_password', label: '원천 DB 비밀번호', value: 'Kr!s2026#src', secret: true }
    ] }
  ];

  function failuresPerHour() {
    var base = [0, 0, 1, 0, 0, 0, 2, 1, 0, 3, 1, 0, 0, 0, 1, 2, 0, 0, 4, 1, 0, 0, 1, 1];
    return base;
  }

  window.AdminMock = {
    now: NOW,
    settings: settings,
    sessions: sessions,
    jobs: jobs,
    cards: cards,
    datasets: datasets,
    packages: packages,
    sweeper: sweeper,
    config: config,
    failuresPerHour: failuresPerHour,
    health: { worker: { ok: true, detail: '워커 2대 응답 (마지막 확인 12초 전)' }, redis: { ok: true, detail: '브로커 응답 3ms' } },
    storage: { dir: '/var/lib/usa/storage', used_gb: 18.4, total_gb: 50 }
  };
}());
