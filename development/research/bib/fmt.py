"""Format Crossref metadata as markdown citations: fmt.py cr.json > out.md"""
import json, sys, html, re
from entries import E
d = json.load(open(sys.argv[1]))
def initials(g):
    parts = re.split(r"[\s.]+", g.strip())
    return "".join(p[0] for p in parts if p and p[0].isalpha())
def authors(m):
    a = m.get("author", [])
    names = []
    for x in a:
        if "family" in x:
            fam = x["family"]
            if fam.isupper(): fam = fam.title()
            names.append((fam + " " + initials(x.get("given", ""))).strip())
        elif "name" in x:
            names.append(x["name"])
    if len(names) > 6:
        names = names[:6] + ["et al."]
    return ", ".join(names)
def clean(t):
    t = html.unescape(re.sub(r"<[^>]+>", "", t))
    return " ".join(t.split())
OVR = {
 "bassett1999": [("Bassett DR,", "Bassett DR Jr,"), ("1967???1996", "1967–1996"), ("31(11):1665.", "31(11):1665–1676.")],
 "sitko2026": [("66(9).", "66(9):1032–1038.")],
 "groeskamp2017": [(" (2017).", "Groeskamp S (2017)."), ("Journal Of Science & Cycling", "Journal of Science and Cycling")],
 "faria2005": [("??? Part 2", "– Part 2")],
 "candau1999": [("M??Nard", "Ménard"), ("31(10):1441.", "31(10):1441–1447.")],
 "reiser2003": [("*Cycling: Cycling on rollers", "*Cycling on rollers")],
 "vazquez2026": [("Fernández EV,", "Vázquez Fernández E,"), ("Preprint (Research Square).", "Research Square preprint, not peer reviewed.")],
 "tomiyama2024": [("Lecture Notes in Civil Engineering 67–76.", "In: Lecture Notes in Civil Engineering (Springer), pp. 67–76.")],
 "macdermid2015sv": [("2015:1–10.", "2015:191075.")],
 "greenwell1995": [("L. Bridge EK", "Bridge EKL")],
}
res = {}
for key, sec, st, doi, q in E:
    m = d[key]["m"]
    title = clean((m.get("title") or [""])[0])
    sub = m.get("subtitle") or []
    if sub and clean(sub[0]).lower() not in title.lower():
        title = title.rstrip(".") + ": " + clean(sub[0])
    year = ((m.get("published-print") or m.get("issued", {})).get("date-parts") or [[None]])[0][0]
    cont = clean((m.get("container-title") or [""])[0])
    vol, iss, pg = m.get("volume"), m.get("issue"), m.get("page") or m.get("article-number")
    loc = ""
    if vol: loc += vol
    if iss: loc += "(" + iss + ")"
    if pg: loc += (":" if loc else "") + pg.replace("-", "–")
    if m.get("type") == "posted-content":
        cont = cont or "Preprint (" + (m.get("institution", [{}])[0].get("name", "") or "not peer reviewed") + ")"
    doi_ = m["DOI"]
    parts = [authors(m) + f" ({year}).", f"*{title.rstrip('.')}.*"]
    if cont: parts.append(cont + (" " + loc if loc else "") + ".")
    parts.append(f"[doi:{doi_}](https://doi.org/{doi_})")
    line = " ".join(parts)
    for a, b in OVR.get(key, []):
        assert a in line, (key, a)
        line = line.replace(a, b)
    res[key] = (sec, st, line)
json.dump(res, open("/tmp/ppx/fmt.json", "w"), ensure_ascii=False, indent=0)
for k, (sec, st, line) in res.items():
    print(sec, st, line)
