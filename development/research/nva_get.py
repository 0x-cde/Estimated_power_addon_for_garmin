"""Download first open PDF of an NVA (Norway) publication found by title search: nva_get.py "title words" OUT.pdf"""
import json, sys, urllib.parse, urllib.request
q = urllib.parse.quote(sys.argv[1])
d = json.load(urllib.request.urlopen(f"https://api.nva.unit.no/search/resources?query={q}&results=5", timeout=30))
for h in d.get("hits", []):
    for a in h.get("associatedArtifacts", []):
        if a.get("type") == "OpenFile" and a.get("mimeType") == "application/pdf":
            pid = h["identifier"]; fid = a["identifier"]
            link = json.load(urllib.request.urlopen(f"https://api.nva.unit.no/publication/{pid}/filelink/{fid}", timeout=30))["id"]
            open(sys.argv[2], "wb").write(urllib.request.urlopen(link, timeout=60).read())
            print("ok", h.get("handle"), a.get("name"), a.get("publisherVersion")); sys.exit()
print("no open file")
