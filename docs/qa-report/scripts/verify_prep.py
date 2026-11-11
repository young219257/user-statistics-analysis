import json, sys, numpy as np, pandas as pd
sys.path.insert(0,'/tmp/qa/scripts'); import api
api.session()
st,d=api.upload('/tmp/qa/out/qa_main_utf8.csv'); ds=d['id']
json.dump({'ds':ds},open('/tmp/qa/out/ds_now.json','w'))
_,p=api.call("GET",f"/api/v1/datasets/{ds}/profile",params={"include_outliers":"false"})
raw=pd.read_csv('/tmp/qa/out/qa_main_utf8.csv')
print("== 프로파일 수치 vs pandas (원본 그대로 읽은 값) ==")
bad=[]
for r in p['numeric']:
    s=pd.to_numeric(raw[r['column']],errors='coerce')
    exp={'count':int(s.notna().sum()),'missing':int(s.isna().sum()),'mean':s.mean(),'std':s.std(ddof=1),'median':s.median(),
         'q1':s.quantile(.25),'q3':s.quantile(.75),'min':s.min(),'max':s.max(),'skewness':s.skew(),'kurtosis':s.kurt()}
    for k,v in exp.items():
        a=r.get(k)
        if a is None or not np.isclose(a,v,rtol=1e-4,atol=1e-3): bad.append((r['column'],k,a,float(v)))
print("불일치:", bad if bad else "없음")
print("std 정의: ddof=1 기준 일치 여부 위에 반영 / 만약 ddof=0 이었다면 불일치로 나타남")
print("== 이상치 탐지 (study_hours) ==")
s=raw['study_hours']
for m,th in [('iqr',1.5),('zscore',3.0),('modified_zscore',3.5),('grubbs',0.05),('mahalanobis',3.0),('isolation_forest',0.6),('lof',1.5)]:
    st,o=api.call("GET",f"/api/v1/datasets/{ds}/outliers",params={"method":m,"threshold":th})
    if m=='iqr': json.dump(o,open('/tmp/qa/out/outliers_iqr.json','w'),ensure_ascii=False,indent=1)
    if isinstance(o,list):
        row=[x for x in o if x.get('column')=='study_hours']
        print(m, th, st, "study_hours:", {k:row[0].get(k) for k in ('n_outliers','lower_bound','upper_bound','method','threshold') if row and k in row[0]} if row else "해당 열 없음", "| 열 목록:", [x.get('column') for x in o])
    else: print(m, st, str(o)[:200])
q1,q3=s.quantile(.25),s.quantile(.75); iqr=q3-q1
print("정답 IQR:", int(((s<q1-1.5*iqr)|(s>q3+1.5*iqr)).sum()), (q1-1.5*iqr,q3+1.5*iqr))
z=(s-s.mean())/s.std(ddof=1); print("정답 |z|>3:", int((z.abs()>3).sum()))
mz=0.6745*(s-s.median())/(s-s.median()).abs().median(); print("정답 modZ>3.5:", int((mz.abs()>3.5).sum()))
