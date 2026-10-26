"""Retry failed keys slowly: retry.py cr.json"""
import json, sys, time, urllib.request, urllib.parse
from entries import E
UA = {"User-Agent": "bib-check/0.1 (mailto:research@example.org)"}
def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return json.load(r)
d = json.load(open(sys.argv[1]))
for key, sec, st, doi, q in E:
    if "error" not in d.get(key, {"error": 1}): continue
    for attempt in range(3):
        try:
            if doi:
                d[key] = {"via": "doi", "m": get("https://api.crossref.org/works/" + urllib.parse.quote(doi, safe="/()"))["message"]}
            else:
                d[key] = {"via": "search", "cands": get("https://api.crossref.org/works?rows=3&query.bibliographic=" + urllib.parse.quote(q))["message"]["items"]}
            break
        except Exception as e:
            d[key] = {"error": str(e)}; time.sleep(5)
    time.sleep(1.5)
json.dump(d, open(sys.argv[1], "w"))
print(sum(1 for v in d.values() if "error" in v), "errors left")
