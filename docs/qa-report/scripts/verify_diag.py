import json, sys, numpy as np, pandas as pd
sys.path.insert(0,'/tmp/qa/scripts'); import api
rng=np.random.default_rng(7); api.session()
def up(df,name):
    p=f'/tmp/qa/out/diag_{name}.csv'; df.to_csv(p,index=False); st,u=api.upload(p); return u['id']
def run(ds,m,params,label):
    st,r=api.call("POST","/api/v1/analyses",json={"dataset_id":ds,"method":m,"name":"qa-"+label,"params":params,"preprocessing":{"drop_duplicates":False,"outlier_treatment":"keep","scaling":"none","encoding":"onehot"}})
    if st!=200 or not isinstance(r,dict) or r.get('status')!='succeeded': print(f"## {label}: HTTP {st} status={(r or {}).get('status') if isinstance(r,dict) else r} err={(r.get('error') if isinstance(r,dict) else '')}"); return None
    R=r['result']; print(f"## {label}: warnings={R.get('warnings')} warning={R.get('warning')} note={str(R.get('note'))[:120]} interp={str(R.get('interpretation'))[:200]}"); return r
n=300
# 1) 다중공선성: x2 = x1 + 작은 잡음
x1=rng.normal(0,1,n); d=pd.DataFrame({'x1':x1,'x2':x1+rng.normal(0,0.01,n),'x3':rng.normal(0,1,n)}); d['y']=2*d.x1+d.x3+rng.normal(0,1,n)
ds=up(d,'collin'); r=run(ds,'linear_regression',dict(target='y',features=['x1','x2','x3'],test_size=0),'다중공선성')
if r: print("   VIF:",[(v['term'],round(v['vif'],1)) for v in r['result']['diagnostics']['vif']])
# 2) 이분산 + 비정규 잔차
x=rng.uniform(1,10,n); d=pd.DataFrame({'x':x}); d['y']=x+rng.standard_t(2,n)*x*0.8
ds=up(d,'hetero'); r=run(ds,'linear_regression',dict(target='y',features=['x'],test_size=0),'이분산·비정규')
if r: print("   diag:",{k:(v.get('p_value'),v.get('normal',v.get('homoscedastic'))) for k,v in r['result']['diagnostics'].items() if isinstance(v,dict)})
# 3) 잔차 자기상관 (AR(1) ρ=0.9, 시계열형)
e=np.zeros(n); 
for i in range(1,n): e[i]=0.9*e[i-1]+rng.normal()
t=np.arange(n); d=pd.DataFrame({'t':t,'y':0.05*t+e}); ds=up(d,'autocorr'); r=run(ds,'linear_regression',dict(target='y',features=['t'],test_size=0),'자기상관')
if r: print("   DW:",r['metrics']['durbin_watson'])
# 4) 클래스 불균형 (양성 3%)
d=pd.DataFrame({'x':rng.normal(0,1,n)}); d['y']=(rng.random(n)<0.03).astype(int)
ds=up(d,'imb'); run(ds,'logistic_regression',dict(target='y',features=['x'],test_size=0.3),'클래스불균형')
# 5) 완전분리
d=pd.DataFrame({'x':rng.normal(0,1,n)}); d['y']=(d.x>0).astype(int); ds=up(d,'sep'); run(ds,'logistic_regression',dict(target='y',features=['x'],test_size=0),'완전분리')
# 6) ANOVA 등분산 위반 (분산비 25배) + 정규성 위반
g=np.repeat(['A','B','C'],100); y=np.r_[rng.normal(0,1,100),rng.normal(0.5,5,100),rng.normal(1,1,100)]; d=pd.DataFrame({'g':g,'y':y})
ds=up(d,'anova_hv'); r=run(ds,'anova',dict(target='y',features=[],factors=['g'],covariates=[],include_interaction=False),'ANOVA 등분산위반')
if r: print("   assumption:",json.dumps(r['result']['assumption_checks'],ensure_ascii=False)[:300],"| posthoc 방법:",list(r['result']['post_hoc'].keys()), "| Welch 키 존재:", 'welch' in json.dumps(r['result']).lower())
# 7) 표본 부족 (n=8)
d=pd.DataFrame({'x':rng.normal(0,1,8)}); d['y']=d.x+rng.normal(0,1,8); ds=up(d,'tiny'); run(ds,'linear_regression',dict(target='y',features=['x'],test_size=0),'표본8')
# 8) PSM 공통지지영역 없음
x=rng.normal(0,1,n); d=pd.DataFrame({'x':x,'tr':(x>0).astype(int)}); d['y']=x+d.tr+rng.normal(0,1,n); ds=up(d,'nooverlap'); r=run(ds,'psm',dict(target='y',features=['x'],treatment_column='tr',n_neighbors=1),'PSM 공통지지없음')
if r: print("   match_rate:",r['metrics']['match_rate'],"smd_after:",r['metrics']['mean_abs_smd_after'])
# 9) 다층모형 특이적합 (집단 효과 0)
d=pd.DataFrame({'g':rng.integers(0,20,n),'x':rng.normal(0,1,n)}); d['y']=d.x+rng.normal(0,1,n); ds=up(d,'singular'); r=run(ds,'multilevel',dict(target='y',features=['x'],group_column='g'),'다층 특이적합')
if r: print("   varcomp:",r['result']['variance_components'],"converged:",r['result']['model_fit'].get('converged'))
# 10) 상관: 범주형 문자열·상수열 선택 시 차단 여부
ds=json.load(open('/tmp/qa/out/ds_clean.json'))['ds']
api.session(); st,u=api.upload('/tmp/qa/out/qa_main_utf8.csv'); dsm=u['id']
st,r=api.call("POST","/api/v1/analyses",json={"dataset_id":dsm,"method":"correlation","name":"qa-cat","params":{"features":["region","const_col","study_hours","income"],"correlation_method":"pearson"},"preprocessing":{}})
print("## 범주형·상수·텍스트 열 상관 요청:", st, (r.get('status'), r.get('error'), r['result'].get('warnings') if isinstance(r.get('result'),dict) else None) if isinstance(r,dict) else r)
# 11) 가정 위반 없는 데이터에서 오탐 확인
d=pd.DataFrame({'x':rng.normal(0,1,n)}); d['y']=d.x+rng.normal(0,1,n); ds=up(d,'clean'); run(ds,'linear_regression',dict(target='y',features=['x'],test_size=0),'정상데이터(오탐확인)')
