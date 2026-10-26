"""Extract text from a PDF: pdftxt.py IN.pdf OUT.txt"""
import sys
import pypdf
r = pypdf.PdfReader(sys.argv[1])
with open(sys.argv[2], "w") as f:
    f.write("\n".join((p.extract_text() or "") for p in r.pages))
print(len(r.pages), "pages")
