import sys, json; sys.path.insert(0,'/tmp/qa/scripts')
import api
api.session()
res = {}
for name in ["qa_main_utf8.csv","qa_main_cp949.csv","qa_main.xlsx","qa_school.csv"]:
    st, d = api.upload("/tmp/qa/out/"+name)
    res[name] = (st, d)
    print(name, st, (d.get("id"), d.get("n_rows"), d.get("n_cols"), d.get("source_format")) if isinstance(d, dict) else d)
json.dump({k:v for k,v in res.items()}, open("/tmp/qa/out/api_upload.json","w"), ensure_ascii=False, indent=1, default=str)
ids = {k:v[1].get("id") for k,v in res.items() if isinstance(v[1],dict)}
json.dump(ids, open("/tmp/qa/out/ids.json","w"))
