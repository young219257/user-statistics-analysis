import json, sys, numpy as np, pandas as pd
from scipy import stats
sys.path.insert(0,'/tmp/qa/scripts'); import api
api.session()
ds=json.load(open('/tmp/qa/out/ds_now.json'))['ds']
# 세션 새로 발급 → 재업로드 필요
st,d=api.upload('/tmp/qa/out/qa_main_utf8.csv'); ds=d['id']
raw=pd.read_csv('/tmp/qa/out/qa_main_utf8.csv')
num=raw[['school_id','treatment','grade','score_t1','score_t2','score_t3','score_t4','study_hours','satisfaction','passed']]
# Mahalanobis: 완전관측 행 기준
cc=num.dropna(); X=cc.values; mu=X.mean(0); S=np.cov(X,rowvar=False)
D=np.sqrt(np.einsum('ij,jk,ik->i',X-mu,np.linalg.pinv(S),X-mu))
print("완전관측 n=",len(cc)," D_M>3.0:",int((D>3).sum())," D_M>3.5:",int((D>3.5).sum())," 중앙값 D:",round(float(np.median(D)),2))
for th in (3.0,5.0,8.0):
    st,o=api.call("GET",f"/api/v1/datasets/{ds}/outliers",params={"method":"mahalanobis","threshold":th})
    r=[x for x in o if x['column']=='study_hours'][0]; print("앱 mahalanobis th=",th,"n_outliers=",r['n_outliers'], {k:v for k,v in r.items() if k not in('values','indices','rows','row_indices','outlier_rows')} if th==3.0 else "")
# Grubbs (반복, 양측, alpha=0.05)
x=raw['study_hours'].dropna().values.copy(); cnt=0
while len(x)>2:
    n=len(x); m=x.mean(); sd=x.std(ddof=1); i=np.argmax(abs(x-m)); G=abs(x[i]-m)/sd
    t=stats.t.ppf(1-0.05/(2*n),n-2); Gc=(n-1)/np.sqrt(n)*np.sqrt(t**2/(n-2+t**2))
    if G>Gc: x=np.delete(x,i); cnt+=1
    else: break
print("정답 Grubbs 반복 검출 수:",cnt)
