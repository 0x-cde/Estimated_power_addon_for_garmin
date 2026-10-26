"""Build the README bibliography section: build_md.py > section.md"""
import json
res = json.load(open("/tmp/ppx/fmt.json"))
res["peterman2015"] = ["aero"] + res["peterman2015"][1:]
MAN = [
 ("model","F","Kyle CR, Berto F (2001). *The mechanical efficiency of bicycle derailleur and hub-gear transmissions.* Human Power 52:3–11."),
 ("model","F","Rohloff B, Greb P (2003). Rebuttal of Kyle & Berto (2001), with a reply by C.R. Kyle. Human Power 55:11–15."),
 ("model","F","Danek T, Slawinski MA, Stanoev T (2020). *On modelling bicycle power-meter measurements: Part I. Estimating effects of air, rolling and drivetrain resistance.* arXiv:2005.04229. [arxiv.org/abs/2005.04229](https://arxiv.org/abs/2005.04229)"),
 ("model","F","Danek T, Slawinski MA, Stanoev T (2020). *On modelling bicycle power-meter measurements: Part II. Relations between rates of change of model quantities.* arXiv:2005.04480. [arxiv.org/abs/2005.04480](https://arxiv.org/abs/2005.04480)"),
 ("model","F","Slawinski MA, Slawinski RA, Stanoev T (2020). *On modelling bicycle power for velodromes: Part I: Formulation for individual pursuits.* arXiv:2005.04691. [arxiv.org/abs/2005.04691](https://arxiv.org/abs/2005.04691)"),
 ("model","A","Dahn K, Mai L, Poland J, Jenkins C (1991). *Frictional resistance in bicycle wheel bearings.* Cycling Science 3(3):28–32."),
 ("model","A","Kyle CR (1988). *The mechanics and aerodynamics of cycling.* In: Burke ER, Newsom MM (eds), Medical and Scientific Aspects of Cycling, pp. 235–252."),
 ("measure","F","Chung R (2012). *Estimating CdA with a power meter* (virtual elevation method). Presentation, not peer reviewed."),
 ("aero","F","Martin JC, Gardner AS, Barras M, Martin DT (2006). *Aerodynamic drag area of cyclists determined with field-based measures.* Sportscience 10:68–69."),
 ("rolling","F","Buder J, Fouchard E, Schwanitz S (2025). *The impact of tyre width, pressure and surface condition on rolling resistance and vibration transmission of bicycle tyres.* Journal of Science and Cycling 14(2), conference abstract."),
 ("rolling","F","Sellier M, Bellenoue S (2025). *A novel energy imbalance approach applied to rolling resistance assessment in cycling.* Journal of Science and Cycling 14(2), conference abstract."),
 ("rolling","A","Buder J, Schwanitz S, Odenwald S (2024). *Benchmarking rolling resistance of bicycle tyres on a laboratory treadmill.* Engineering of Sport 15 (ISEA 2024), Loughborough University."),
 ("rolling","F","Mastinu G, Gobbi M, Matrascia G (2019). *Bicycle tyres – rolling resistance.* Bicycle and Motorcycle Dynamics 2019 symposium, University of Padova (extended abstract)."),
 ("rolling","A","Nilges P (2004). *Auswirkung unterschiedlicher Mountainbikereifen auf die Rollwiderstandsleistung im Gelände* (effect of different mountain-bike tyres on rolling resistance off road). Thesis, German Sport University Cologne (print only)."),
 ("surface","F","Steyn WJvdM, Warnich J (2014). *Comparison of tyre rolling resistance for different mountain bike tyre diameters and surface conditions.* South African Journal for Research in Sport, Physical Education and Recreation 36(2):179–193."),
 ("surface","P","Li H, Buscheck J, Harvey J, Fitch D, Reger D, Wu R, et al. (2017). *Development of recommended guidelines for preservation treatments for bicycle routes.* UC Pavement Research Center report UCPRC-RR-2016-02 (Caltrans CA17-2693). [PDF](https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/f0016607-ca17-2693-finalreport.pdf)"),
 ("surface","P","Li H, Harvey JT, Thigpen C, Wu R. *Surface treatment macrotexture and bicycle ride quality.* UC Pavement Research Center report UCPRC-RR-2013-07. [PDF](https://escholarship.org/content/qt3dp663w0/qt3dp663w0.pdf)"),
 ("measure","A","Menaspà P, Haakonssen E, Sharma A, Clark B (2016). *Accuracy in measurement of elevation gain in road cycling.* Journal of Science and Cycling 5(1):10–12."),
]
rows = [(v[0], v[1], v[2]) for v in res.values()] + MAN
SECT = [("model","Power model and cycling dynamics"),("rolling","Rolling resistance"),
        ("surface","Road surface, roughness and vibration"),
        ("aero","Aerodynamic drag: frontal area, riding position, wind and drafting"),
        ("measure","Power meters, elevation data and field measurement")]
TAG = {"F": "", "P": " *(partly read)*", "A": " *(abstract or second-hand only)*"}
import unicodedata
def sortkey(line):
    return unicodedata.normalize("NFKD", line).encode("ascii", "ignore").decode().lower()
out = []
for key, title in SECT:
    out.append(f"**{title}**\n")
    for sec, st, line in sorted([r for r in rows if r[0] == key], key=lambda r: sortkey(r[2])):
        out.append(f"- {line}{TAG[st]}")
    out.append("")
print("\n".join(out).rstrip())
import sys
print(len(rows), "entries", file=sys.stderr)
