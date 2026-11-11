import requests, time, json
BASE = "https://testlab-edmgr.kr/apps/app-20261006-160341"
S = requests.Session()
def session():
    r = S.post(BASE + "/api/v1/sessions", json={}, timeout=30); r.raise_for_status()
    j = r.json(); S.headers[j.get("token_header", "X-Session-Token")] = j["session_token"]; return j
def call(method, path, **kw):
    r = S.request(method, BASE + path, timeout=120, **kw)
    try: body = r.json()
    except Exception: body = r.text[:500]
    if r.status_code == 202 and isinstance(body, dict) and body.get("id"):   # job
        jid = body["id"]
        for _ in range(120):
            jr = S.get(BASE + f"/api/v1/jobs/{jid}", timeout=30).json()
            if jr.get("status") in ("succeeded", "failed", "cancelled"): break
            time.sleep(1)
        rurl = jr.get("result_url")
        if jr.get("status") == "succeeded":
            res = S.get(BASE + "/api/v1/" + rurl.split("/api/v1/", 1)[1], timeout=60) if rurl else None
            if res is None:
                base = {"dataset": "/api/v1/datasets/", "analysis": "/api/v1/analyses/"}[jr["resource_type"]]
                res = S.get(BASE + base + jr["resource_id"], timeout=60)
            try: return res.status_code, res.json()
            except Exception: return res.status_code, {"_nonjson": res.text[:300], "job": jr}
        return 500, {"job": jr}
    return r.status_code, body
def upload(path):
    with open(path, "rb") as f:
        return call("POST", "/api/v1/datasets/upload", files={"file": (path.split("/")[-1], f)})
