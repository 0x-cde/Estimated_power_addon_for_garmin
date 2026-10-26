"""Fetch Crossref metadata for bibliography entries: fetch.py out.json"""
import json, sys, time, urllib.request, urllib.parse
sys.path.insert(0, sys.argv[2]) if len(sys.argv) > 2 else None
from entries import E
UA = {"User-Agent": "bib-check/0.1 (mailto:research@example.org)"}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)
out = {}
for key, sec, st, doi, q in E:
    try:
        if doi:
            m = get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/()"))["message"]
            out[key] = {"via": "doi", "m": m}
        else:
            items = get("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(q))["message"]["items"]
            out[key] = {"via": "search", "cands": items}
    except Exception as e:
        out[key] = {"error": str(e)}
    time.sleep(0.3)
json.dump(out, open(sys.argv[1], "w"))
print(len(out), "done;", sum(1 for v in out.values() if "error" in v), "errors")
