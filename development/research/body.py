"""Print a paper's text up to its reference list, cleaned: body.py t.txt
Drops figure-layer junk (very short lines), dedupes repeated sentences, joins lines."""
import re, sys
s = open(sys.argv[1], errors="replace").read()
m = None
for pat in [r"\n\s*References\s*\n", r"\n\s*REFERENCES\s*\n", r"\n\s*Bibliography\s*\n", r"\n\s*Literature [Cc]ited\s*\n", r"\n\s*References and [Nn]otes\s*\n"]:
    for mm in re.finditer(pat, s):
        if mm.start() > len(s) * 0.4:
            m = mm; break
    if m: break
if m: s = s[:m.start()]
lines = [l.strip() for l in s.splitlines()]
lines = [l for l in lines if len(l) >= 5 and not l.startswith("/gid")]
text = " ".join(lines)
text = re.sub(r"(\w)- (\w)", r"\1\2", text)
text = re.sub(r"\s+", " ", text)
sents = re.split(r"(?<=[.!?])\s+", text)
seen, out = set(), []
for x in sents:
    k = re.sub(r"\W", "", x.lower())[:80]
    if len(k) > 20 and k in seen: continue
    seen.add(k); out.append(x)
text = " ".join(out)
# wrap
w, line = [], ""
for word in text.split(" "):
    if len(line) + len(word) > 160: w.append(line); line = word
    else: line = (line + " " + word).strip()
w.append(line)
print("\n".join(w))
