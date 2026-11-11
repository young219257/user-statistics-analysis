import json, sys, pandas as pd
sys.path.insert(0,'/tmp/qa/scripts'); import api
api.session()
st,u=api.upload('/tmp/qa/out/qa_clean_reference.csv'); ds=u['id']; print("clean ds", st, u['n_rows'], [ (c['name'],c['role']) for c in u['columns']][:16])
json.dump({'ds':ds},open('/tmp/qa/out/ds_clean.json','w'))
F=['study_hours','grade','satisfaction','score_t1']
P={
 'correlation':dict(features=['study_hours','income','score_t1','score_t4','satisfaction'],correlation_method='pearson'),
 'linear_regression':dict(target='score_t4',features=F,fit_intercept=True,test_size=0),
 'logistic_regression':dict(target='passed',features=F,test_size=0.3,max_iter=200),
 'decision_tree_regressor':dict(target='score_t4',features=F,max_depth=3,min_samples_leaf=5,test_size=0.3),
 'decision_tree_classifier':dict(target='passed',features=F,max_depth=3,min_samples_leaf=5,test_size=0.3),
 'kmeans':dict(features=['study_hours','score_t1','score_t4'],n_clusters=3),
 'hierarchical':dict(features=['study_hours','score_t1','score_t4'],n_clusters=3,linkage='ward'),
 'dbscan':dict(features=['study_hours','score_t1','score_t4'],eps=0.5,min_samples=5),
 'pca':dict(features=['study_hours','score_t1','score_t2','score_t3','score_t4'],n_components=2),
 'anova':dict(target='score_t4',features=[],factors=['region'],covariates=[],include_interaction=True),
 'multilevel':dict(target='score_t4',features=['study_hours'],group_column='school_id',random_slope=False),
 'growth_curve':dict(target='score_t4',features=[],time_column='grade',group_column='school_id',random_slope=False),
 'psm':dict(target='score_t4',features=['study_hours','grade'],treatment_column='treatment',n_neighbors=1),
}
res={}
for m,p in P.items():
    st,r=api.call("POST","/api/v1/analyses",json={"dataset_id":ds,"method":m,"name":"qa-"+m,"params":p,"preprocessing":{"drop_duplicates":False,"outlier_treatment":"keep","scaling":"none","encoding":"onehot"}})
    res[m]=(st,r); json.dump(r,open(f'/tmp/qa/out/an_{m}.json','w'),ensure_ascii=False,indent=1)
    keys=list(r.keys()) if isinstance(r,dict) else None
    print(m, st, (r.get('status'), (r.get('error') or {}) if isinstance(r,dict) else '') , keys if st==200 else str(r)[:200])
