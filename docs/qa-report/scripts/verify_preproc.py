import json, sys, numpy as np, pandas as pd
sys.path.insert(0,'/tmp/qa/scripts'); import api
api.session()
raw=pd.read_csv('/tmp/qa/out/qa_main_utf8.csv')
num=raw[['school_id','treatment','grade','score_t1','score_t2','score_t3','score_t4','study_hours','satisfaction','passed']].dropna()
X=num.values; mu=X.mean(0); S=np.cov(X,rowvar=False); d=X-mu
D2=np.einsum('ij,jk,ik->i',d,np.linalg.pinv(S),d)
print("D² > 3/5/8 개수:", int((D2>3).sum()), int((D2>5).sum()), int((D2>8).sum()), "(앱: 388/351/203)")

def fetch_all(dsid):
    rows=[];off=0
    while True:
        st,r=api.call("GET",f"/api/v1/datasets/{dsid}/preview",params={"limit":500,"offset":off})
        rr=r.get('rows') or r.get('data') or []
        rows+=rr; off+=500
        if len(rr)<500: break
    return rows, r
def run(req):
    st,u=api.upload('/tmp/qa/out/qa_main_utf8.csv'); ds=u['id']
    st,o=api.call("POST",f"/api/v1/datasets/{ds}/preprocess",json=req)
    if st!=200: return st,o,None
    rows,meta=fetch_all(o['id']); return st,o,pd.DataFrame(rows)
sh=raw['study_hours']
cases={
 'median':{'missing_strategy':'median','outlier_treatment':'keep','scaling':'none'},
 'mean':{'missing_strategy':'mean','outlier_treatment':'keep','scaling':'none'},
 'mode':{'missing_strategy':'mode','outlier_treatment':'keep','scaling':'none'},
 'drop_rows':{'missing_strategy':'drop_rows','outlier_treatment':'keep','scaling':'none'},
 'zero':{'missing_strategy':'zero','outlier_treatment':'keep','scaling':'none'},
 'winsor_iqr':{'missing_strategy':'none','outlier_treatment':'winsorize','scaling':'none','outlier_method':'iqr','outlier_threshold':1.5},
 'drop_iqr':{'missing_strategy':'none','outlier_treatment':'drop','scaling':'none','outlier_method':'iqr','outlier_threshold':1.5},
 'log':{'missing_strategy':'none','outlier_treatment':'log','scaling':'none'},
 'standard':{'missing_strategy':'median','outlier_treatment':'keep','scaling':'standard'},
 'minmax':{'missing_strategy':'median','outlier_treatment':'keep','scaling':'minmax'},
 'robust':{'missing_strategy':'median','outlier_treatment':'keep','scaling':'robust'},
}
out={}
for name,req in cases.items():
    st,o,df=run(req)
    if df is None: print(name, "HTTP",st, str(o)[:200]); continue
    col=pd.to_numeric(df.get('study_hours'),errors='coerce')
    info={'n_rows':len(df),'n_na_study':int(col.isna().sum()),'mean':round(float(col.mean()),4),'std1':round(float(col.std(ddof=1)),4),'std0':round(float(col.std(ddof=0)),4),'min':round(float(col.min()),4),'max':round(float(col.max()),4)}
    out[name]=info; print(name, info, "| cols:", len(df.columns))
print("== 정답 ==")
q1,q3=sh.quantile(.25),sh.quantile(.75); iqr=q3-q1; lo,hi=q1-1.5*iqr,q3+1.5*iqr
print("median대체 후 중앙값/평균:", sh.fillna(sh.median()).mean().round(4), "| mean대체 평균:", sh.fillna(sh.mean()).mean().round(4), "| mode:", sh.mode().iloc[0], "| zero 평균:", sh.fillna(0).mean().round(4))
print("drop_rows 행수(전체 결측행 제거):", len(raw.dropna(subset=raw.columns.difference(['income']).tolist()+[])), "(income 포함 시:", len(raw.dropna()),")")
w=sh.clip(lo,hi); print("winsorize(IQR): max", round(w.max(),4), "mean", round(w.mean(),4))
print("drop(IQR) 후 행수:", int(len(raw)-((sh<lo)|(sh>hi)).sum()))
filled=sh.fillna(sh.median()); print("standard(중앙값대체): mean 0, std ddof1 =1 / ddof0 =", round(float(filled.std(ddof=0)/filled.std(ddof=1)),4))
print("robust 기대: median 0, IQR 1 → min", round(float(((filled-filled.median())/(filled.quantile(.75)-filled.quantile(.25))).min()),4))
json.dump(out,open('/tmp/qa/out/preproc_app.json','w'),indent=1)
