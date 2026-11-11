import json, sys, numpy as np, pandas as pd, warnings
warnings.filterwarnings("ignore")
import statsmodels.api as sm, statsmodels.formula.api as smf
from statsmodels.stats.outliers_influence import variance_inflation_factor as vif
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from scipy import stats
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans
sys.path.insert(0,'/tmp/qa/scripts'); import api
L=lambda m: json.load(open(f'/tmp/qa/out/an_{m}.json'))
df=pd.read_csv('/tmp/qa/out/qa_clean_reference.csv')
OK=lambda a,b,rt=1e-4,at=1e-3: bool(np.isclose(a,b,rtol=rt,atol=at))
rep=[]
def chk(tag,app,exp,rt=1e-4,at=1e-3):
    ok=OK(app,exp,rt,at); rep.append((tag,app,float(exp),ok))
    if not ok: print("  ✗",tag,"앱=",app,"정답=",float(exp))
# ---------- 선형회귀 ----------
F=['study_hours','grade','satisfaction','score_t1']
X=sm.add_constant(df[F]); y=df['score_t4']; ols=sm.OLS(y,X).fit()
R=L('linear_regression'); M=R['metrics']; res=R['result']
print("[선형회귀] 계수/SE/t/p/CI")
for c in res['coefficients']:
    t='const' if c['term']=='const' else c['term']
    chk(f"LR coef {t}",c['coefficient'],ols.params[t]); chk(f"LR se {t}",c['std_error'],ols.bse[t]); chk(f"LR t {t}",c['t_value'],ols.tvalues[t])
    chk(f"LR p {t}",c['p_value'],ols.pvalues[t],1e-3,1e-6); chk(f"LR ci_lo {t}",c['ci_lower'],ols.conf_int().loc[t,0]); chk(f"LR ci_hi {t}",c['ci_upper'],ols.conf_int().loc[t,1])
for k,v in {'r_squared':ols.rsquared,'adjusted_r_squared':ols.rsquared_adj,'f_statistic':ols.fvalue,'aic':ols.aic,'bic':ols.bic,'log_likelihood':ols.llf,'durbin_watson':durbin_watson(ols.resid)}.items(): chk("LR "+k,M[k],v)
chk("LR f_pvalue",M['f_pvalue'],ols.f_pvalue,1e-3,1e-12)
Xv=ols.model.exog
for d in res['diagnostics']['vif']: chk("LR VIF "+d['term'],d['vif'],vif(Xv,list(ols.params.index).index(d['term'])))
bp=het_breuschpagan(ols.resid,Xv); chk("LR BP lm",res['diagnostics']['homoscedasticity']['lm_statistic'],bp[0]); chk("LR BP p",res['diagnostics']['homoscedasticity']['p_value'],bp[1])
sw=stats.shapiro(ols.resid); chk("LR SW W",res['diagnostics']['normality']['statistic'],sw[0]); chk("LR SW p",res['diagnostics']['normality']['p_value'],sw[1])
print("  선형회귀 계수 필드:",sorted(res['coefficients'][1].keys()))
print("  diagnostics 키:",list(res['diagnostics'].keys()))
# ---------- 상관 ----------
cr=L('correlation')['result']; cols=['study_hours','income','score_t1','score_t4','satisfaction']
print("[상관] pearson 쌍")
for p in cr['pairs']:
    r,pv=stats.pearsonr(df[p['x']],df[p['y']]); chk(f"CORR r {p['x']}-{p['y']}",p['coefficient'],r); chk(f"CORR p {p['x']}-{p['y']}",p['p_value'],pv,1e-3,1e-9)
print("  pair 필드:",sorted(cr['pairs'][0].keys()))
api.session(); st,u=api.upload('/tmp/qa/out/qa_clean_reference.csv'); ds=u['id']
for meth in ['spearman','kendall']:
    st,c=api.call("GET",f"/api/v1/datasets/{ds}/correlation",params={"method":meth})
    mat=c.get('matrix'); cl=c.get('columns')
    if mat is None: print("  step3 응답:",str(c)[:200]); continue
    sub=[x for x in cl if x in ('score_t1','score_t4','satisfaction','study_hours')]
    for a_i in range(len(sub)):
        for b_i in range(a_i+1,len(sub)):
            a,b=sub[a_i],sub[b_i]; app=mat[cl.index(a)][cl.index(b)]
            if meth=='spearman': exp=stats.spearmanr(df[a],df[b])[0]
            else: exp=stats.kendalltau(df[a],df[b],variant='b')[0]
            exp_c=stats.kendalltau(df[a],df[b],variant='c')[0] if meth=='kendall' else None
            ok=OK(app,exp); rep.append((f"CORR {meth} {a}-{b}",app,float(exp),ok))
            if not ok: print("  ✗",meth,a,b,"앱=",app,"tau-b=",exp,"tau-c=",exp_c)
    print("  step3 상관 응답 키:",list(c.keys()))
# ---------- 로지스틱 (test_size=0) ----------
st,lr=api.call("POST","/api/v1/analyses",json={"dataset_id":ds,"method":"logistic_regression","name":"qa-lg0","params":{"target":"passed","features":F,"test_size":0,"max_iter":1000},"preprocessing":{"drop_duplicates":False,"outlier_treatment":"keep","scaling":"none","encoding":"onehot"}})
lm=sm.Logit(df['passed'],sm.add_constant(df[F])).fit(disp=0)
print("[로지스틱]")
for c in lr['result']['coefficients']:
    t='const' if c['term']=='const' else c['term']
    chk(f"LG coef {t}",c['coefficient'],lm.params[t],1e-3,1e-3)
chk("LG aic",lr['metrics']['aic'],lm.aic,1e-3,1e-2); chk("LG mcfadden",lr['metrics']['mcfadden'],lm.prsquared,1e-3,1e-3); chk("LG llf",lr['metrics']['log_likelihood'],lm.llf,1e-3,1e-2)
print("  로지스틱 계수 필드:",sorted(lr['result']['coefficients'][1].keys())); print("  metrics 키:",sorted(lr['metrics'].keys()))
# ---------- PCA ----------
pc=L('pca')['result']; pf=['study_hours','score_t1','score_t2','score_t3','score_t4']
print("[PCA]")
for name,Z in [("공분산(비표준화)",df[pf].values),("상관(표준화)",(df[pf]-df[pf].mean())/df[pf].std(ddof=1))]:
    p=PCA().fit(Z); print("  ",name,"설명분산비:",np.round(p.explained_variance_ratio_[:2],4),"고유값:",np.round(p.explained_variance_[:2],3))
print("  앱 설명분산비:",[round(c['explained_variance_ratio'],4) for c in pc['components']],"고유값:",[round(c['explained_variance'],3) for c in pc['components']])
print("  PCA preprocessing_steps:",pc['preprocessing_steps'])
# ---------- ANOVA ----------
an=L('anova')['result']
m=smf.ols('score_t4 ~ C(region)',df).fit(); at=sm.stats.anova_lm(m,typ=2)
t=an['anova_table'][0]; print("[ANOVA]")
chk("AN SS region",t['sum_sq'],at.loc['C(region)','sum_sq']); chk("AN F",t['f_statistic'],at.loc['C(region)','F']); chk("AN p",t['p_value'],at.loc['C(region)','PR(>F)'],1e-3,1e-9)
chk("AN eta2",t['eta_squared'],at.loc['C(region)','sum_sq']/at['sum_sq'].sum())
lev=stats.levene(*[g['score_t4'].values for _,g in df.groupby('region')],center='median'); chk("AN levene p",an['assumption_checks']['levene']['p_value'],lev.pvalue,1e-3,1e-6)
print("  ANOVA 필드/노트:",list(an.keys()))
# ---------- 다층모형 ----------
ml=L('multilevel')['result']; mm=smf.mixedlm('score_t4 ~ study_hours',df,groups=df['school_id']).fit(reml=True)
print("[다층모형]")
chk("ML const",ml['fixed_effects'][0]['coefficient'],mm.params['Intercept'],1e-3,1e-3); chk("ML b study",ml['fixed_effects'][1]['coefficient'],mm.params['study_hours'],1e-3,1e-3)
chk("ML se study",ml['fixed_effects'][1]['std_error'],mm.bse['study_hours'],1e-3,1e-4)
chk("ML group var",ml['variance_components']['group_variance'],float(mm.cov_re.iloc[0,0]),1e-3,1e-2); chk("ML resid var",ml['variance_components']['residual_variance'],mm.scale,1e-3,1e-2)
v=float(mm.cov_re.iloc[0,0]); chk("ML ICC(조건부)",ml['variance_components']['icc'],v/(v+mm.scale),1e-3,1e-3)
mm0=smf.mixedlm('score_t4 ~ 1',df,groups=df['school_id']).fit(reml=True); v0=float(mm0.cov_re.iloc[0,0]); chk("ML ICC(무조건)",L('multilevel')['metrics']['unconditional_icc'],v0/(v0+mm0.scale),1e-3,1e-3)
# ---------- K-means ----------
km=L('kmeans'); kf=['study_hours','score_t1','score_t4']; Z=df[kf].values
Zs=(Z-Z.mean(0))/Z.std(0,ddof=0)
print("[K-평균] 앱 total_ss",round(km['metrics']['total_ss'],1),"| raw 총제곱합",round(((Z-Z.mean(0))**2).sum(),1),"| 표준화 총제곱합",round(((Zs-Zs.mean(0))**2).sum(),1))
print("  K=3 inertia 앱:",round(km['metrics']['inertia'],1),"raw:",round(KMeans(3,n_init=10,random_state=0).fit(Z).inertia_,1),"표준화:",round(KMeans(3,n_init=10,random_state=0).fit(Zs).inertia_,1))
print("  kmeans preprocessing_steps:",km['result']['preprocessing_steps'])
# ---------- PSM ----------
ps=L('psm'); cb=ps['result']['covariate_balance']; print("[PSM] covariate_balance 항목:",json.dumps(cb,ensure_ascii=False)[:500])
for cvn in ['study_hours','grade']:
    t1=df[df.treatment==1][cvn]; t0=df[df.treatment==0][cvn]; smd=(t1.mean()-t0.mean())/np.sqrt((t1.var(ddof=1)+t0.var(ddof=1))/2); print("  매칭 전 SMD",cvn,round(smd,4))
bad=[r for r in rep if not r[3]]
print(f"\n== 총 {len(rep)}개 수치 비교, 불일치 {len(bad)}개 ==")
json.dump(rep,open('/tmp/qa/out/compare.json','w'),default=str)
