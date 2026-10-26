# Ground / surface resistance — verified sources (working notes)

1. Vázquez Fernández E, Dell'Orto G, Moore JK (2026). Vibration-induced power loss in cycling: experimental quantification on a simulated cobblestone surface. Research Square preprint, doi:10.21203/rs.3.rs-10390782/v1 (posted 3 Aug 2026, CC BY, NOT peer reviewed). READ IN FULL.
   - Indoor coast-down, one rider, Giant TCR, Vittoria Randonneur 700x28C, 5 wooden planks 20x90 mm matched to cobblestone "pseudo-BRI" (BRI 257 at 15 km/h).
   - Reference (smooth hall floor): CdA seated 0.427, off-saddle 0.290 (coasting, upright); Crr 0.0110 @350 kPa, 0.0114 @400, 0.0093 @450, 0.0089 @500, 0.0092 @550 (touring tyre, hall floor).
   - Vibration loss 5-351 W, 12.8-61.4% of total; quadratic in speed; seated 550 kPa: 43.9 W @10 km/h -> 351 W @30 km/h. At 30 km/h 164 W @350 kPa vs 351 W @550 kPa; at 15 km/h 48 -> 60 W.
   - Model: P_vl = K * a * P * v^2, a = 2.50e-3 W h2 km-2 kPa-1, K_seated 0.298, K_offsaddle 0.193 (R2 0.883). Text says a is "divided by rider mass" — ambiguous.
   - Data: Zenodo 10.5281/zenodo.20692132; code github.com/EloyVazquezf/Vibration-Induced Power Losses.
   - Lesson: on rough surfaces higher pressure lowers Crr but raises total loss; loss is NOT proportional to v like Crr — ∝ v^2 in power (i.e. force ∝ v).
2. Turner MM (2024). Cycling on rough roads: a model for resistance and vibration. Vehicle System Dynamics 62(10):2729-2749. doi:10.1080/00423114.2024.2304031. (arXiv 2405.00019, OA). Roughness resistance from damping in rider; scales with vertical stiffness and road roughness (IRI/PSD).
3. Li H, Buscheck J, Harvey J, Fitch D, Reger D, Wu R, Ketchell R, Hernandez J, Haynes B, Thigpen C (2017). Development of recommended guidelines for preservation treatments for bicycle routes. UCPRC-RR-2016-02 / Caltrans CA17-2693. 67 sections, 155 riders; MPD, IRI vs acceptability; Ch.8 physical rolling-resistance model (global μ). Free PDF dot.ca.gov. (Our real-road factor 1.65-2.45x, median 1.8, comes from this.)
4. Li H, Harvey JT, Thigpen C, Wu R (2013). Surface treatment macrotexture and bicycle ride quality. UCPRC-RR-2013-07. eScholarship OA.
5. Steyn & Warnich (2014) — bitumen/gravel/grass/sand; surface largest effect (see rolling notes 18).
6. Bertucci, Rogier, Reiser (2013) — road/sand/grass MTB tyres (rolling notes 17).
7. Fenre & Klein-Paste (2021a,b) — instrumented bike; winter surfaces Crr 0.010-0.056 (rolling notes 5,6).
8. Ejsmont et al. (2017) road texture (MPD) influence; (2021) Coatings; (2024) drum vs road methods (rolling notes 13-15).
9. Sandberg U et al. (2011). Road surface influence on tyre/road rolling resistance. MIRIAM SP1-04 (VTI).
10. Karlsson R, Hammarström U, Sörensen H, Eriksson O (2011). Road surface influence on rolling resistance: coastdown measurements for a car and an HGV. VTI notat 24A-2011 (earlier listed wrongly as "rapport 724A").
11. Nielens H, Lejeune T (2004). Bicycle shock absorption systems and energy expended by the cyclist. Sports Med 34(2):71-80. doi:10.2165/00007256-200434020-00001. Power dissipated by suspension minimal on most terrains.
12. Nielens H, Lejeune T (2001). Energy cost of riding bicycles with shock absorption systems on a flat surface. Int J Sports Med 22:400-404. VO2 difference ≤3% n.s.
13. Lépine J, Champoux Y, Drouet JM (2014). Road bike comfort: on the measurement of vibrations induced to cyclist. Sports Eng 17(2):113-122. doi:10.1007/s12283-013-0145-8.
14. Lépine J, Champoux Y, Drouet JM (2015). The relative contribution of road bicycle components on vibration induced to the cyclist. Sports Eng 18:79-91. Handlebar & fork main contributors at hands.
15. Pelland-Leblanc JP, Lépine J, Champoux Y, Drouet JM (2014). Using power as a metric to quantify vibration transmitted to the cyclist. Procedia Eng 72:392-397. Cobblestones vs lab.
16. Vanwalleghem J, De Baere I, Loccufier M, Van Paepegem W (2013). Sensor design for outdoor racing bicycle field testing for human vibration comfort evaluation. Meas Sci Technol 24(9):095002. 43.9 W absorbed at rider interfaces on cobblestones (as cited in #1).
17. Bíl M, Andrášik R, Kubeček J (2015). How comfortable are your cycling tracks? A new method for objective bicycle vibration measurement. Transp Res C 56:415-425. doi:10.1016/j.trc.2015.05.007. Dynamic Comfort Index; r=-0.94 with perception.
18. Gao J, Sha A, Huang Y et al. (2018). Evaluating the cycling comfort on urban roads based on cyclists' perception of vibration. J Clean Prod. (verify volume)
19. Tomiyama K et al. (2024). A concept of surface roughness index for cycle path: Bicycle Ride Index (BRI). Proc Int Conf Maintenance & Rehabilitation of Pavements, Springer, pp 67-76. doi:10.1007/978-3-031-63584-7_8. Quarter-bike model at 15 km/h, sensitive to 0.5-500 mm wavelengths (IRI is 0.5-50 m, car at 80 km/h).
20. Toljic M, Brezina T, Emberger G (2021). Influence of surface roughness on cyclists' velocity choices. Proc ICE Municipal Engineer 174(1):2-13. 3750 cyclists, 7 surfaces incl. cobbles/gravel: speeds barely differ (median 19.4-20.7 km/h). 
21. "What is slowing me down? Estimation of rolling resistances during cycling" (2016). Procedia Eng (ISEA 2016), S1877705816306798. 4-wheel e-bike, power + speed regression: Crr asphalt 0.0122, fine gravel 0.0147, coarse gravel 0.0183 (ratios 1.20x, 1.50x); vibration classifies surface. (authors to verify)
22. Gee-Clough D (1978/79). The effect of wheel width on the rolling resistance of rigid wheels in sand. J Terramechanics (S0022489878900022). Width strongly raises Crr in sand; sqrt(z/D) law.
23. Macdermid PW, Fink PW, Stannard SR (2015). Tyre volume and pressure effects on impact attenuation during mountain bike riding. Shock Vib 2015:191075 (rolling notes 20).
24. Buder et al (2025) JSC — tarmac vs cobblestones on treadmill (rolling notes 21).
25. Crenna et al (2025) Eng — vibration vs width/pressure (rolling notes 28).
26. Viellehner J, Potthast W (2021). The effect of cycling-specific vibration on neuromuscular performance. MSSE 53(5):936-944. doi:10.1249/MSS.0000000000002565.
27. Wilson DG, Schmidt T, Papadopoulos J (2020). Bicycling Science, 4th ed. MIT Press. "Bump resistance".
18 (fix). Gao J, Sha A, Huang Y, Hu L, Tong Z, Jiang W (2018). Evaluating the cycling comfort on urban roads based on cyclists' perception of vibration. J Clean Prod 192:531-541. doi:10.1016/j.jclepro.2018.04.275.
28. Gao J et al. (2019). Cycling comfort on asphalt pavement: influence of the pavement-tyre interface on vibration. J Clean Prod 223:323-341.
29. Nilges (2004) — 9 tyres on asphalt, gravel, grassland, 150-400 kPa: on asphalt Crr falls with pressure, on gravel and grass the OPPOSITE (as cited in Rothhämel 2023 literature review — primary not located; likely German thesis/report). PRIMARY NOT VERIFIED.
30. Islam MS (M.Sc thesis). Off-road performance of bicycle wheels: with special emphasis on rolling resistance. Compact soil, loose soil, grass; wheel diameters 660/610/457/355 mm (as cited in LEJPT narrow-wheel review). PRIMARY NOT VERIFIED.
Grey:
- Karrasch J / FlexFit: off-road tyre Crr database via Chung virtual-elevation, 57 tyres, 5 surfaces (2026) — field method, not peer reviewed.
- Cyclingnews (2026): Vittoria Terreno Dry 31-61 mm lab tests — Crr rises with width on gravel lab surfaces until MTB sizes.

## Turner 2024 (read arXiv full text)
- Roughness resistance FORCE: F_ro = π² k_B n0² G_d(n0)  (Eq.17; power P = F_ro·v), n0 = 0.1 m⁻¹, IRI ≈ 0.22·sqrt(G_d) with G_d in 1e-6 m³, IRI in m/km  =>  F_ro ∝ k_B · IRI².
- Depends ONLY on bicycle vertical stiffness k_B (≈ 2kT·kF/(2kT+kF), tyre kT per tyre, frame kF) and roughness; NOT on rider physiology, mass or speed (force constant with speed in this linear model).
- Dominant response at 2-10 Hz, wavelengths 0.5-4 m at 30 km/h ("roughness", not "texture").
- Example: stiff frame (1 MN/m) 23 mm tyres at max pressure: at IRI 5 m/km total resistance (rolling+roughness) > 2x smooth; at IRI 10 m/km ~6x. 40 mm tyre at optimal pressure 1.5-2x lower than 23 mm when IRI ≳ 10. Optimal pressure = max for IRI ≲ 5, min for IRI ≳ 10.
- Trunk roads IRI ≲ 5 m/km; secondary roads wide range up to ~30; unpaved maintained roads ~10 (per IRI literature cited).
- CONFLICT with Vázquez Fernández 2026 (power ∝ v², i.e. force ∝ v, on discrete planks). Unresolved; different excitation (random roughness vs periodic planks).
## Not extracted
- (resolved) Steyn & Warnich 2014 Table 2 read: bituminous 0.002±0.001, gravel 0.006±0.002, grass 0.007±0.002, sand 0.030±0.006; 26in 0.013, 29in 0.010; 180/250/500 kPa 0.012/0.012/0.011; 70/80/90 kg 0.011/0.012/0.012.
- Rothhämel 2023 temperature/pressure model: Inderscience PDF blocked to scripted download.
