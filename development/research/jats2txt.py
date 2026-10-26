"""JATS XML (Europe PMC) -> plain text body without references: jats2txt.py IN.xml OUT.txt"""
import re, sys, xml.etree.ElementTree as ET
raw = open(sys.argv[1], encoding="utf-8", errors="replace").read()
raw = re.sub(r"<!DOCTYPE[^>]*>", "", raw)
root = ET.fromstring(raw)
for ref in root.iter():
    for child in list(ref):
        if child.tag in ("ref-list", "back"):
            ref.remove(child)
parts = []
for el in root.iter():
    if el.tag in ("article-title", "abstract", "p", "title", "td", "th", "caption"):
        t = " ".join("".join(el.itertext()).split())
        if t: parts.append(t)
seen, out = set(), []
for p in parts:
    if p in seen: continue
    seen.add(p); out.append(p)
open(sys.argv[2], "w").write("\n".join(out))
print(len(out), "blocks")
