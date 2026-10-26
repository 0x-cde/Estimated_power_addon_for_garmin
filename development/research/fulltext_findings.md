# Full-text reading log

Each entry: what was read, the key quantitative findings, and caveats. "FULL" = whole body text read.

## Previously read in full
- Martin 1998, Bassett 1999 (equations as images), Defraeye 2010 preprint, Turner 2024, Vázquez Fernández 2026, Steyn & Warnich 2014 — see notes_*.md.

## Hyttinen, Rothhämel, Jerrelind, Drugge 2024 (PLoS ONE) — FULL
- Transient tyre-temperature model: heat in = Fz·Crr·v; out = convection h(v)=h_nat 5.1 W/m²K + 3.59·v, road contact convection, radiation (ε 0.96). Tyre mass 0.5 kg, c 2005 J/kgK, width 50 mm.
- Uses Rothhämel's Crr(T) regression (form garbled in PDF); Table 1 lists b1 = b2 = 0.96 (typesetting error) -> coefficients NOT recoverable from this paper.
- ~9 min at constant speed reaches steady tyre temperature.
- Warm weather: warm-up effect on Crr only 1-2 %. Below 0 °C even small tyre warming cuts Crr substantially.
- At cold ambient, 30 -> 10 km/h raises Crr ~10 % (= pressure 400 -> 300 kPa).
- -10 °C ambient: total energy +10-15 % per 10 °C drop (rolling + denser air), for a commuter cycle.
- Model NOT validated against measurements (authors' future work). Simulation uses Cd 1.0, A 0.6 m², 100 kg.

## Buder, Fouchard, Schwanitz 2025 (JSC conference abstract, 8 p) — FULL
- p.a.v.e. treadmill (200 mm drum!), coast-out 40→10 km/h; GP5000 2024 23/25/28/30/32 mm with TPU tubes; 4 riders 79±3 kg; 6 pressures 0.5 bar steps within ETRTO range.
- Wider = longer coast-out on both surfaces; benefit plateaus beyond 30 mm. Optimal pressure for minimum Crr higher than common practice (within limits). Heavier system = shorter COD; wider tyres less sensitive to weight.
- Simulated cobbles (periodic 150 mm long, ~4 mm high bumps): COD only 0.5–1 % shorter -> mild excitation; NOT comparable with real cobbles.
- Vibration RMS: width dominant, pressure secondary; front > rear.
- No numeric Crr values given (figures only). Small drum exaggerates deformation (authors' caveat).

## Sellier & Bellenoue 2025 (JSC conference abstract, 5 p) — FULL
- Coasting between two points, pitot dynamic pressure + exact wheel revolutions; calibration 8 runs at 18–30 km/h gives CdA 0.369 m² (coasting position, R² 0.998); then Crr tests 4 runs at ~15 km/h.
- 28 mm tubeless race tyres, 73 kg rider, tree-sheltered road. Lower pressure -> higher Crr and smaller effective wheel circumference.
- TT vs non-TT same brand: 6 W @6 bar, 11 W @3 bar (normalised 45 km/h, 81.5 kg). M3 7–11 % lower than M1/M2.
- Temperature: 13.7 °C vs 18.1 °C tyre: +2.8 W @45 km/h, 81.5 kg (≈ ΔCrr +0.00028, i.e. ~+6-8 % per °C?? only if Crr≈0.004 -> abstract claims +26 %). Heated/cooled in water baths.
- Reported σ 0.00046 "(or 1.4 %)" is internally inconsistent with road Crr ~0.003–0.005; absolute Crr values only in figures. No surface comparison.

## Garimella et al. 2020 (Appl Sci) — FULL
- 10 amateur males (176 cm, 74.6 kg). Statistical 3D body shape from 7 anthropometrics, reposed from mocap; CFD at 60 km/h, ρ 1.181, rider ONLY (no bike), smooth surface, coarse mesh (trends only).
- CFD drag (N): TT 26.8–35.7 (mean 29.2), Hoods 31.8–45.0 (38.5), Drops 26.0–40.0 (32.7). => rider-only CdA ≈ TT 0.177, hoods 0.234, drops 0.199 m²; ratios hoods/TT 1.32, drops/TT 1.12 (static, no bike).
- Cd (vs camera area incl. bike): TT 0.58–0.76, hoods 0.66–0.81, drops 0.63–0.76. Bike alone projected area 0.15 m².
- Drag vs projected area R² 0.72. Frontal-area regression: RMSE 0.032–0.037 m², relative error SD ~9–10 %, ICC only 0.43–0.51 (cross-validated) -> individual prediction is weak.
- Hip, back, neck, elbow angles and upper-body girth matter most.

## Hopker, Barnes, Fennell, Gibson 2025 (Eur J Sport Sci) — FULL
- Body Rocket: 4 force sensors at rider contact points (bar, saddle, both pedals) -> measures RIDER drag only (bike excluded), 100 Hz, sensor accuracy 0.05–0.1 N (manufacturer, unpublished).
- Wind tunnel 11.5 m/s with discs 50–100 mm (Cd 1.12) on 1 m rod: r 0.99 vs theory, mean diff 0.002 ± 0.005 m²; smallest step 0.002 m². Velodrome (10 males, TT position, 41 km/h): LoA −0.012…+0.009 m², bias −0.001; rider-only CdA 0.208 ± 0.03 m²; CV 1.67 %, TE 0.004 m², ICC 0.99.
- Large discs under-read (wake shields rider); velodrome banking makes measured airspeed slightly high -> CdA slightly low.
- Context cited: Valenzuela 2020 (Notio detects upright->aero ~0.07 m² but not helmet 0.008 / wheel 0.006); Kordi 2022 (Notio 0.002 m² with discs); Bruez 2023 (Notio outdoors 0.058 m² off theoretical, ICC 0.98); Ordiñana-Perez 2023 (Notio 2–4 % below math models); DeGolier 2024 (BR within 2.3 % of tunnel). Barry 2015: hoods -> crouched aerobars −16.7 % drag ≈ 70 W at 45 km/h.
- Funded by Innovate UK grant shared with Body Rocket Ltd (conflict noted; analysis "independent").
- Point made: virtual elevation assumes fixed drivetrain/rolling losses; errors with speed fluctuations.

## Dyer & Disley 2018 (Disabil Rehabil Assist Technol; accepted manuscript) — FULL
- One para-cyclist (1.72 m, 73 kg; system 86 kg), two prostheses. Wind tunnel 14 & 16 m/s, yaw 0/5/10°, CV 0.7–0.9 %. Velodrome VE (Chung) at 42/38/34 km/h, Crr assumed 0.004 (from earlier trials), ρ 1.198, PowerTap ±1.5 %: CV 2–3 %.
- VE gave CdA 0.03 m² LOWER than tunnel; excluding 10° yaw cuts gap by 0.012–0.014 m². Results relative, not interchangeable. Single subject.
- Cites: bicycle equipment 31–39 % of drag; aero up to 96 % of power at elite speeds.

## Groeskamp 2017 (JSC) — FULL
- Martin-model based; "incline-equivalent wind" v_α ≈ v_d·√α, v_d = sqrt(2mg/(ρ(CdA+Fw))).
- Table: CdA commuter 0.65 (100 kg), amateur 0.40 (85 kg), pro TT 0.28 (77 kg) — from Wilson 2004 (secondary).
- Notes Greenwell 1995 and Tew & Sayers 1999 imply Fw = 2–25 % of CdA (up to ~0.06 m²) vs Martin's 0.0044; author uses 0.04 (not validated).
- Mont Ventoux (7.3 %) ≈ 56 km/h headwind for an amateur. Drafting cited up to 40 % power saving.

## Fintelman, Hemida, Sterling, Li 2015 (J Wind Eng Ind Aerodyn 144:31-41; accepted ms) — FULL
- Mannequin in DROPPED position on road bike, static wheels, 9.91 m/s, frontal area rider+bike 0.55 m² at 0° yaw. Experiment at 15° yaw: CFX 0.644 (=> CdA ≈ 0.354 m²), side 0.281, lift 0.178.
- Drag share: mannequin ~70 %, bicycle ~30 % (at 15°); bike ~20 % of drag at 0° (from 2014 exp.). Bike ~60 % of side force at 60°.
- Drag coefficient varies only ~9 % across yaw range in RANS; low drag at >60° yaw. Side forces ≈ 2× drag at 15° (Barry 2012, TT); spoked wheel side force 5–6× its drag.
- Rotating rims/tyres changed coefficients < 1.8 %. Skin friction ~3 % of drag. LES within ~5 % of experiment; RANS k-ε under-predicts.
- Disc vs spoked rear wheel: ~2 % less drag but double side force at ~9 m/s crosswind (Hanna 2002, unvalidated).

## Danek, Slawinski, Stanoev 2020a/b (arXiv 2005.04229, 2005.04480) — FULL
- Model P·(1−λ) = V(mg sinθ + ma + Crr mg cosθ + ½ρCdA(V+w)²); ρ = 1.225·exp(−0.00011856 h). Assioma Duo pedals; GPS speed/altitude; m 111 kg; wind set to 0.
- Flat segment (10.5 m/s, 258.8 W): CdA 0.2607 ± 0.003, Crr 0.00231 ± 0.0054 (!), λ 0.0357 ± 0.0004. Climb 4.6 % (4.1 m/s, 287 W): CdA 0.270, Crr 0.0130 ± 0.011 (!), λ 0.030.
- KEY: Crr is effectively unidentifiable from steady single-speed data (SD > value); CdA and Crr trade off: ∂CdA/∂Crr = −2mg/(ρV²) = −16.4 on the flat (−109 on the climb). 1 % CdA ↔ 6.9 % Crr on the flat. Supports the fit_rides.py "narrow speed range" warning.
- Sensitivities (flat): +1 % speed needs +2.3 % power; climb +1.1 %. Mass matters ~20× more on the 4.6 % climb than on the flat.
- Headwind/tailwind 5 m/s example: ±10 % power split saves ~16 s over 10 km.

## Kyle & Berto 2001 (Human Power 52:3-11) — FULL
- Motor-driven crank dynamometer; output via Monark ergometer wheel; 80/150/200 W at 75 rpm; chains oiled. Reported efficiencies INCLUDE ergometer-drive losses (1–6 W) -> true values 2–2.5 % higher (1–3 % per fig. 14).
- Efficiency rises with load: Shimano 27-sp gear 44/16 uncorrected 91 % at 50 W -> >97 % at 370 W; corrected >98 % at high load (agrees with Spicer >98 % at 200 W, 52/15).
- 12-tooth sprockets worse: 91.2 % vs 16-tooth 93.5 % (uncorrected). Adjacent gears differ 1–3 %. Cross-chaining little effect. Hub gears ~2 % below derailleurs; oil-lubricated, worn-in 3-speeds equal to derailleurs.
## Rohloff & Greb 2003 rebuttal + Kyle reply (Human Power 55:11-15) — FULL
- Rohloff (run-in 100 km, 314 W constant torque 50 N·m): derailleur and Speedhub 95–98.5 %. 1000 km dirty chain/sprockets: −1 % (derailleur).
- Loss model: power-dependent % + power-INDEPENDENT constant watts (seals, lubricant viscosity). E.g. 3 % + 3 W -> 91 % at 50 W, 96 % at 200 W, 96.4 % at 500 W. Below 200 W the constant part dominates and varies ±1 W with temperature.
- Kyle reply: differences mostly due to load; derailleur 307–370 W ≈ 98 %; speed variation within crank cycle ±0.13 %.
- MODEL IMPLICATION: a constant η = 0.976 may overstate efficiency at recreational power (100–200 W); an affine loss (a few W + 2–3 %) is better supported. Martin's 0.977 came from SRM vs ergometer at its test powers.

## Dahmen, Byshko, Saupe, Röder, Mantler 2011 (Sports Eng 14:95-110; Konstanz version) — FULL
- Martin model (no wind, no spoke drag) on two climbs: Ottenberg 2.8 km, 8.3 % avg (max 15.2), Wachtbüeler Höhe 4.2 km, 6.1 %. SRM + Garmin Edge 705 + differential GPS (σh < 3 cm) for the height profile; gradient where DGPS fails estimated from the model itself.
- Parameters used: Crr 0.004 (ergometer default "asphalt"), Cd 0.7 × A 0.4 m² (CdA 0.28), wheel inertia Iw 0.28 kg·m² (measured by pendulum — 2× Martin's 0.14), β0 0.091 N, β1 0.0087 N·s/m, η 0.975, ρ 1.2.
- Field vs model: r 0.96–0.99, 98.9–99.6 % of variance explained; power bias +4.9 to +8.0 W (≈ 4 %), SD 19–20 W (≈ 9 %) at 10–11 km/h. Speed bias −0.4/+0.17 km/h, SD 0.65–0.73 km/h.
- 8 W bias equivalent to 3.3 kg mass error or 0.13 % gradient error -> gradient is the main error source on climbs (standard GPS altitude too poor; needs DGPS or barometer).
- Power split at 10 km/h on 8.3 %: gravity 91.8 %, rolling 4.4 %, aero 3.6 %, bearings 0.1 %, KE 0.
## Dahmen, Wolf, Saupe 2012 (IFAC "Applications of mathematical models of road cycling") — FULL
- Only FOUR compound coefficients are identifiable from power+speed: η, Crr, bearings β0/β1, CdA cannot all be separated (e.g. mgμ+β0 together). Their calibration fits speed (not power) along non-flat, variable-speed rides. Ergometer vs field: 1–2 W mean, 23 W SD.
- Optimal TT pacing via critical-power model; 14:09 -> 13:54 min on a climb in simulator.

## Berjisian, Bigazzi, Barkh 2023 (PLoS ONE 18(12):e0295027) — FULL  [authors now verified]
- 16 Vancouver segments; Endomondo crowd GPS vs field survey/LiDAR. Phone GPS horizontal error 7–13 m; vertical 1.5–3× worse.
- Best crowd grade method (smooth + DBSCAN + medoid on per-trace GRADE): RMSE ~1 % grade with ~150 cleaned traces; computing grade from a composite elevation doubles the error. Median RMSE grade: crowd 4 %, high-res DEM/LiDAR 1 %, low-res 5 %, RwGPS 8 % (ground-truth sites with few traces).
- Cites Meng et al.: barometric grade RMSE 0.5 % vs GPS-altitude 2.6 %. Cloudy weather worsens GPS accuracy.
- Urban cyclist power formula P = 1030(0.0077 + G)v + 0.342v³ (from Tengattini & Bigazzi params): at 20 km/h a 1 % grade error = 57 W (56 %).

## Malizia & Blocken 2020 (J Wind Eng Ind Aerodyn 200:104134; TU/e version of record) — FULL (30 p review)
- Aero ≈ 90 % of resistance above 40 km/h on flat. Rider 60–82 % of drag, bicycle 18–40 % depending on position.
- Martin model restated; yaw: Cooper 2003 — at 13.4 m/s with 3.13 m/s wind (N-American annual mean at ~2 m, all directions equally likely) only 10 % chance yaw > 16°.
- Rolling (Bourlet 1894 / Kyle & Burke 1984 / Wilson 2004): Crr track 0.004 / min 0.0016 / min 0.002; ROAD average 0.009 / 0.0034 / 0.008. Kyle 1988/2002 speed term Crr2 = 0.0502 N·s/m per wheel (17" wheel, drum).
- Coast-down vs tunnel: field drag usually LARGER (Kyle & Burke; Burns & Sullivan, better agreement upright than aero). Moving legs + rotating wheels raise drag +6 % (Crouch 2017) to +30 % (García-López 2008); isolated rotating wheel +15–30 % vs static (Kyle).
- Wheels: rotational drag 20–40 % (Kyle) / 25–55 % (Jermy 2008) of wheel drag; 36->24 spokes −35 %, ->16 a further −10 %. Spoked wheels 50–150 % more drag than best disc.
- Crane & Morton 2018: wind-averaged drag area rises ~linearly with tyre-width/rim-width ratio (slope ≈ 0.034 m², R² 0.87) — a 10 % wider tyre ≈ +0.4 N per wheel at 13.4 m/s (≈ +0.0037 m² per wheel). Tyres should be no wider than the rim (Kyle 2002; Hed patent 1.05–1.15 rim/tyre). => supports a tyre-width CdA term; extrapolating to 45 mm on a ~21–25 mm rim gives several 0.01 m² for two wheels (outside tested range).
- Bike details: cables 0.16 N/m bare, 0.50 N/m sheathed in crossflow; aero bottle −0.13 N, aero crank −0.14…−0.21 N at 48 km/h (reference rider+standard track bike 31–36 N at 48 km/h -> CdA ≈ 0.29–0.34). Aero fork −2.5 %. Clip-on vs cow-horn −13.7…−15.5 % (Kyle 1989). Handlebar 20 mm down + 20 mm forward −3.1…−5.8 % (Oggiano 2008).
- Calls out large discrepancies between wheel studies (Zipp 808 Cd 0.02–0.05) and lack of uniform protocols.

## Fenre & Klein-Paste 2021a (J Cold Reg Eng 35(2); NTNU accepted ms) — FULL
- Instrumented hybrid bike: PowerTap hub (downstream of drivetrain), Garmin Edge 130 speed, Velocomp Aeropod pitot + barometric/accelerometer slope. 42 mm 29" studded tyres @ 2 bar; system weight 834–874 N; samples only with cadence > 0 (braking assumed only when not pedalling); bearings and drivetrain neglected.
- Wind tunnel (pedalling, loose clothes, upright hybrid): CdA 0.670 @2.7 m/s -> 0.605 @13.5 m/s; frontal area 0.501 m² -> Cd 1.34–1.21. Field CdA (speed sweep 10–30 km/h) 0.648 ± 0.014.
- Crr on moist asphalt (studded tyre): 0.0073 ± 0.0008 (n=322). Known added resistance (dynamo) recovered with 96.5 % accuracy in wind up to 9.9 m/s gusts and 9 % slopes. Precision ±0.005 with 9 s, ±0.002 with 55 s, ±0.001 with 220 s of 1 Hz data.
- Cites Wilson 2004: well-maintained road bike on paved surface Crr ≈ 0.005. Commuters avoid >3 % grades ≈ Crr 0.035 total.
- Gives full citation for "What is slowing me down?": Meyer D, Kloss G, Senner V (2016) Procedia Eng 147:526–531, doi:10.1016/j.proeng.2016.06.232. Also Hölzel, Höchtl, Senner (2012) Cycling comfort on different road surfaces, Procedia Eng 34:479–484.

## Fenre & Klein-Paste 2021b (Cold Reg Sci Technol 187:103282; published OA) — FULL
- Same instrumented hybrid (42 mm studded @ 2 bar, min recommended), 20.3 km route × 4 days, 103 sections (80–1520 m), air temps −6.9…+4.9 °C. Sections < 24 samples dropped (SEM ≈ ±0.003).
- Median Crr: wet asphalt 0.010 (n 4234), dry asphalt 0.012, compact snow 0.014, slush <2 cm on asphalt 0.016, loose snow <2 cm on compact 0.020, slush <2 cm on ice 0.023, loose snow <2 cm on asphalt 0.027, slush 2–5 cm on ice 0.030, loose 2–5 cm on compact 0.035, loose snow >5 cm 0.056. Per-second SD 0.014–0.027 (very noisy at 1 Hz).
- Authors attribute high bare-asphalt Crr to studs, cold rubber (~0 °C) and low pressure; wet < dry (water lubricates stud slip).
- Comfort threshold suggested Crr ≈ 0.025 (one rider). Bare-road maintenance avg Crr 0.012 vs winter-road 0.021.
- Cited: Wilson 2004 Crr 0.002 (racing tyres, hard smooth) to 0.008 (utility tyres low pressure); soft ground (sand/snow) 10–100× (Michelin 2003). Pradko & Lee 1966: bumps < 60 mm and < 6 Hz cost < 2.7 W (≈ ΔCrr 0.0012 at 10 km/h, 84 kg); losses rise by orders of magnitude at higher amplitude/frequency.
- Data: Mendeley dataset (Fenre & Klein-Paste 2020).

## Lépine, Champoux, Drouet 2014 (Sports Eng 17:113-122; accepted ms via Cambridge repository) — FULL
- Lab (hydraulic shakers / treadmill with dowel), non-pedalling seated rider, tyres 8 bar; measures RMS acceleration and force at stem and seatpost (ISO 5349 / 2631 weighting).
- Hand position (drops significant), wrist angle, static hand force (±30 N) and rider mass all change measured vibration significantly; wheel-set ranking (Fulcrum 7 + 23 mm clincher vs Zipp 202 + tubular) stable only if test conditions are held constant — can be inverted otherwise.
- No power-loss data. Relevance: comfort methodology only.

## Lépine, Champoux, Drouet 2015 (Sports Eng 18:79-91; thesis-chapter version) — FULL
- Lab road simulator replaying 26 km/h on a GRANULAR (coarse asphalt) road, seated non-pedalling rider, 23 mm tyres 8 bar; 2^4 factorial (wheels, fork, frame, handlebar).
- Absorbed vibration power at each brake hood ≈ 1.6–2.2 W; at the seatpost ≈ 3.0–3.4 W (from figure scales) -> total a few W (~5–8 W) on rough-ish asphalt at 26 km/h. Contrast: Vanwalleghem 2013 43.9 W at interfaces on cobbles; Vázquez 2026 ~100–200 W on plank "cobbles" at 20–25 km/h.
- Hands: handlebar and fork dominate; buttocks: wheels and frame dominate. Stem no effect. Absorbed power was the most consistent metric.
- MODEL IMPLICATION: on ordinary paved roads vibration losses are small (single-digit W), consistent with the real-road Crr factor absorbing them; on cobbles/rough unpaved they become tens to hundreds of W.

## Ejsmont, Ronowski, Ydrefors, Owczarzak, Sommer, Świeczko-Żurek 2024 (Int J Automot Technol 25:965-976; OA via VTI DiVA) — FULL
- CAR tyres (205/55R16, labels A–F), trailer R2Mk.3 on 6 roads vs 2.0 m drum with steel or road-replica surfaces vs VTI flat-bed (TTF).
- Steel drum (ISO 28580 / SAE J2452) correlates poorly with road (R² 0.46–0.78) and gives LOWER Crr; on aggressive surface dressing (MPD 3.15 mm) road Crr ≈ 2× steel-drum value; ~30 % error typical on ordinary surfaces; tyre RANKING also changes. Replica-covered drums (with Clark–Dodge flat correction CRR_F = CRR_R·sqrt(1+r/R)) agree well (R² > 0.8, slope ~1 on DAC16).
- MPD of surfaces: ISO test track 0.50, DAC11 0.60, DAC16 0.8, SMA8 1.07, PCC 1.22, surface dressing 3.15, steel drum 0.1 mm.
- Temperature correction for car tyres: −1.5·10⁻⁴ per °C (≈ −1.5 %/°C at Crr ≈ 0.01).
- Trailer needs 15–30 min warm-up; 0.1 % road grade -> several % error; coast-down on 100–200 m sections unusable for cars.
- Relevance: supports the real-road > drum factor (direction and order of magnitude), but car-tyre data.

## UCPRC-RR-2016-02 (Li, Buscheck, Harvey et al. 2017, Caltrans CA17-2693) — Ch. 1–3, 8, 11 read FULL; Ch. 4–7, 9–10 (survey statistics, texture vs specifications, long-term monitoring) skimmed; appendices (data tables/forms) not read
- Rolling-resistance part (Ch. 8): ONE road bike, upright on hoods, crank power meter (SRM-type), 8 flat sections 0.33–1 mi, ≥ 6 runs each direction at 150–350 W, weather station mid-section at rider height, gusty runs discarded; Martin "CdA calculator" (R² ≥ 98 %).
- CRUCIAL CAVEAT: the baseline HMA section (MPD 0.58 mm, IRI 1.49 m/km) was ASSIGNED μ = 0.004 ("based upon previously used average values"), and CdA = 0.383 m² was fitted under that assumption. μ ("global coefficient of friction") = Crr + bearing friction. Other sections' μ are therefore baseline + measured increments:
  Section: MPD / IRI(in/mi) -> μ : HMA 1.18/95 -> 0.0075; HMA 0.96/265 -> 0.0071; HMA 1.79/327 -> 0.0098; HMA 0.53/222 -> 0.0066; chip 2.12/236 -> 0.0096; chip 2.25/132 -> 0.0085; chip 1.06/150 -> 0.0068.
  => increments over baseline +0.0026…+0.0058 (median +0.0035); ratios 1.65–2.45 (median 1.875) ONLY if the baseline truly is 0.004 for that bike/tyre (tyre model and pressure not reported).
- μ correlates with MPD (R² 0.70) more than IRI (R² 0.34); same surface type can differ (HMA up to 0.0098, chip seal 0.0068). Chip seal (MPD 2.12, IRI 3.7 m/km) vs baseline: ~2.1–2.3 km/h slower at 150–350 W.
- Two crank power meters differed by 4.5 % on average (R² 0.988). SRM accuracy ±2.5 %, temperature effect up to 5.2 % (cited). Lit: silk tyres smooth surface Crr 0.0016; μ track 0.0025, taxiway 0.0043 (Martin 2006).
- Ride quality: 80 % of riders accept MPD ≤ 1.8 mm, 50 % ≤ 2.3 mm; vibration more sensitive above MPD 2 mm and IRI 5 m/km; 155 riders, 67 sections, 2194 observations.
- MODEL IMPLICATION: our "real-road factor 1.8" is the ratio to an ASSUMED 0.004 baseline. The data more directly support an ADDITIVE real-road increment of ~+0.003…+0.006 (median ≈ +0.0035) over smooth new asphalt. For a road tyre (drum Crr 0.0045) additive and ×1.8 give almost the same (0.0080 vs 0.0081); for gravel/MTB tyres the multiplicative form gives more (0.0108 vs 0.0095; 0.0162 vs 0.0125). Also bearings are inside μ (our model adds bearings separately -> slight double count, ≈ 0.0002 Crr-equivalent at 25 km/h, 85 kg).

## UCPRC-RR-2013-07 (Li, Harvey, Thigpen, Wu 2014; eScholarship) — executive summary, methods overview and conclusions read; survey appendices skimmed
- Chip seal on SLO-1 prompted complaints; MPD measured three ways; ride quality 3.5 @ MPD 1.0, 3.0 @ 1.5, 2.5 @ 2.0, 1.5 @ 3.0 mm; acceptable MPD ≈ 2.0–2.7 mm for club riders. NO rolling-resistance/power measurements in this report (those are only in the 2016 follow-up).

## Peterman, Lim, Ignatz, Edwards, Byrnes 2015 (PeerJ 3:e1144; Europe PMC full text) — FULL
- 19 Cat Pro/1/2 males (174 ± 6 cm, 70 ± 8 kg), PowerTap hubs, field Ad and Rr by di Prampero regression on flat road (Edwards & Byrnes 2007; Lim 2011); 22.1 km TT at 1625 m altitude (ρ ≈ 0.97–1.0).
- Field Ad 0.349 ± 0.059 m² (0.258–0.462; equipment mix: 6 plain road bikes, 4 road + aerobars, 9 TT bikes; TT subgroup 0.258–0.355). Rider-only projected area AP 0.338 ± 0.050 m²; Ad/AP ("Cd") 1.03 ± 0.12, range 0.82–1.26; AP explains only 54 % of Ad; AP and Cd uncorrelated.
- Field Crr 0.006 ± 0.002 (0.004–0.009), Rr 4.9 ± 1.3 N, tyres 8.3 bar, real Colorado roads -> independent support for real-road Crr ≈ 1.5–2× smooth-surface race-tyre values.
- Frontal-area estimators: Olds 1995 and Heil 2001/2002 unbiased vs digitised AP; all BSA-fraction and most other anthropometric formulas OVER-predict (0.399–0.550 m²).
- TT power split: aero 89.8 % (272 W), rolling 10.2 % (31 W) at ~42 km/h. Funded by CycleOps (declared no influence).

## Bouillod, Soto-Romero, Grappe, Bertucci, Brunet, Cassirame 2022 (Sensors 22:386; Europe PMC full text) — FULL body (study table skimmed)
- 74 validity studies; SRM is the usual reference (31 studies); only 11 field studies.
- Accuracy of PowerTap, Stages, Garmin Vector ≈ ±2–3 % (150–350 W) vs SRM; CVs ~2 %; drivetrain losses ~2.4 % (pedal-based reads highest, hub-based lowest).
- Temperature: SRM offset shifts ~2 W per °C if not re-zeroed; CompuTrainer −7 W in cold; PowerTap/Vector/Stages accuracy degraded in heat (Shute). -> re-zero after warm-up.
- Vibration: Stages, Garmin Vector (48–52 Hz) and Favero Duo (30–40 Hz) read significantly LOW under vibration (accelerometer cadence saturation?); SRM, PowerTap G3, Rotor InPower unaffected. -> CLUB DATA QA: pedal / crank-arm accelerometer meters may under-read on cobbles, gravel and MTB terrain — record meter type and treat unpaved residuals from such meters with caution.
- Single-sided (left ×2) meters depend on L/R balance, which varies with cadence, load and fatigue. Standing raised measured power +2.1 % (SRM) / +2.4 % (PowerTap) at the same treadmill speed; Stages −4.4 %.
- Short averaging windows (1 s) inflate disagreement; ≥5 s recommended for submaximal comparison.
- Field power variability CV 14.5 % (flat) vs 6.8 % ergometer.

## Blocken, Defraeye, Koninckx, Carmeliet, Hespel 2013 (Comput Fluids 71:435-445; preprint) — FULL
- Same tunnel/rider as Defraeye 2010 (183 cm, 72 kg, aero helmet, long-sleeve suit, disc wheels, STATIC legs); frontal areas UP 0.41 / DP 0.37 / TTP 0.34 m².
- Drafting at 0.01 m: trailing rider −27.1 % (UP), −23.1 % (DP), −13.8 % (TTP); leading rider −0.8/−1.7/−2.6 %. Tunnel: leader −1.6 % at 0.15 m (DP). Older field data: trailing rider −33 % power at 40 km/h (Kyle), VO2 −18 % at 32 km/h and −27 % at 37–40 km/h (McCole), up to −49 % drag in tunnel (Zdravkovich).
- Bicycle = 30–35 % of total drag (citing Defraeye). Static legs likely underestimate drafting gains. Relevance: quantifies why estimates read high in groups (drafting not modelled — accepted decision).

## Gao, Sha, Huang, Hu, Tong, Jiang 2018 (J Clean Prod 192:531-541; White Rose accepted ms) — methods + results read (perception-threshold section skimmed)
- 46 asphalt sections in Xi'an, handlebar accelerometer (ISO 2631 a_wv), shared bikes; solid-tyre 25 kg bike vibrates most (1.56 vs 0.89–1.12 m/s² for inflatable-tyre bikes).
- Vibration rises ~linearly with speed: a_wv 1.71 / 2.31 / 3.12 m/s² at 10 / 14.5 / 18.6 km/h. 17 riders rated comfort; comfort ∝ acceptability. No power/resistance data -> comfort only.

## Faria, Parker, Faria 2005 (Sports Med 35:313-337; author upload) — FULL read (physiology sections skimmed: cadence, economy, intensity, pacing, altitude)
- Position: upright straight-arm -> hands on drops −20 % drag; drops -> full aero crouch a further −10…17 %; upright -> aero total −30…35 %. Aero position costs ~37 W metabolic and ~3 % net efficiency (no wind).
- Aero > 90 % of resistance above 30 km/h (Kyle). Frontal area ≈ 18 % of body surface area; quotes Bassett FA = 0.0293·H^0.725·M^0.425 + 0.0604 (aero bars) — independent confirmation of the formula.
- Rolling: concrete vs blacktop ~5 % difference; higher pressure lowers Crr; Crr ∝ 1/wheel radius; coast-down may slightly underestimate Crr and overestimate drag (Candau). Drafting −40 % energy (mid-pack), −14 % VO2 at 39.5 km/h.
- Cross-check of our position factors (ratios to TT/aero): this review implies drops ≈ 1.11–1.20 × aero and upright ≈ 1.43–1.54 × aero; Defraeye 2010 tunnel: drops 1.15, upright 1.28; Jeukendrup & Martin: drops ≈ 1.23, upright ≈ 1.43; Garimella CFD (rider only): drops 1.12, hoods 1.32. OUR factors: drops 1.30, hoods 1.45, upright 1.75 — on the HIGH side of the literature ratios. But our TT base (Cd 0.707 × Bassett ≈ 0.23 m²) matches STATIC tunnel TT values, while pedalling/field TT values are ~0.26–0.34 (García-López 0.341 dynamic; Peterman TT 0.258–0.355). Net effect: road-mode absolute CdA ≈ 0.33 m² sits close to field road values (Sellier coasting 0.369, UCPRC hoods 0.383, Fintelman static drops 0.354) — the high ratios partly compensate a low (static) base. Re-parameterising (higher base, lower ratios) would change TT mode most.

## Chung 2012 "Estimating CdA with a power meter" (112-slide presentation + notes, not peer reviewed) — slides read FULL, speaker notes read for the analysis sections
- Virtual elevation (VE): from power, speed, mass, ρ and guessed (Crr, CdA), compute slope s = P/(mgv) − Crr − a/g − ρCdA·v²/(2mg); integrate to an elevation profile; choose CdA (given Crr) so each lap nets zero elevation. Accelerations: use the central difference a(t) = (v(t+Δt) − v(t−Δt))/(2Δt) because recorded samples are interval averages (simple back-difference lags half an interval).
- Diagnostics: braking -> sudden step up in VE; unmeasured wind -> VE profile becomes speed-dependent / out-and-back legs don't match; position change -> lap slope change. Classic constant-speed regression is not robust (gave negative CdA on a 5-min subset).
- Sensitivities (flat lap course): +1 % mass -> −0.3 % CdA; +1 % ρ -> −1.0…−1.5 % CdA; +1 % Crr -> −0.3 % CdA; a 33 % Crr change moved CdA only 2.5 % on a flat TT. Crr and CdA separable only with extra information: two speeds up the same hill with known elevation gain, monotonic speed sweep on a flat velodrome (Shen method), or known true elevation profile.
- Elevation sources: GPS altitude "accurate but not precise", barometric altimeter "precise but not accurate" — don't treat either as ground truth for Crr separation.
- Precision: classic method CdA SD 0.0025–0.003 m² (Coggan); VE CV as low as 0.3 % (SD 0.0006 m²) for experienced users; detected a 5×5 cm card (0.0025 m²). Example rider in hoods/tops, warmers + vest, Crr assumed 0.0035: CdA 0.415 vs 0.436 sitting up.
- Martin's drivetrain loss 2.3 % noted; PowerTap hubs are downstream (η = 1). Suggests modelling losses as fixed W + fixed % as an option.
- MODEL/FIT IMPLICATIONS for fit_rides.py: use central-difference acceleration; flag braking (VE jumps) and wind-dependent residuals; Crr only identifiable from rides with speed variety on grades with trustworthy elevation.

## Slawinski, Slawinski, Stanoev 2020 (arXiv 2005.04691, velodrome Part I) — FULL
- Velodrome model separating wheel (black line) and centre-of-mass paths (lean angle tanϑ = V²/(r g)); lateral tyre friction term. Example: CdA 0.2, Crr 0.002, 12 m/s -> 229.7 W vs 242.7 W from the straight-road formula.
- From power and speed alone only the ratios CdA/(1−λ), Crr/(1−λ) are identifiable (drivetrain loss λ must be assumed; hub meters λ ≈ 0). Relevance: low (track), but confirms the identifiability limit noted by Dahmen 2012 and Danek 2020.

## Cohen, Brunet, Roy, Clanet 2021 (J Fluid Mech 914:A38; publisher OA PDF) — FULL (phase-diagram section skimmed)
- Energy balance Pm = ½ρ·S·CD·V³ + MgαV + μMgV + d/dt(½MV²). Crossover speed where aero = rolling: Vμ = sqrt(2μMg/(ρSCD)) ≈ 15 km/h for μ 0.0032, SCD 0.25, M 80 kg.
- Wind-tunnel compilation (fig. 4b): upright 0.27–0.52, dropped 0.24–0.33, TT 0.21–0.34 m². TT model with SCD 0.25 predicts flat Tour TTs within 8 %; climbs within 10 % after adding aero + μ 0.0032. Sprint position ≈ 0.30 m² (Blocken 2019); descent positions 0.15 (superman) – 0.233 m² (Froome), from Blocken 2018.
- Power–duration heuristic Pmax(T) = Π[e^(−T/τ) + 1 − γ ln(T/τ+1)], τ ≈ 32 s, γ 0.0886. Mean cadence 81–87 rpm in grand tours. Relevance: physics framing; confirms aero/rolling crossover ≈ 15 km/h (rolling dominates for slow riders/climbs).

## Steyn & Warnich 2014 (S Afr J Res Sport Phys Educ Recreat 36(2):179-193; UP repository) — FULL
- Method: coast-downs from only ~15 km/h to stop, speed from two GPS units (±0.5 km/h), aero term computed with ASSUMED Cd 0.76 × A 0.509 m² and ρ 1.07 (Pretoria); Crr from Δv/Δt; both directions averaged; 3 riders weighted to 70/80/90 kg; 26"/29" hardtail/full-suspension; 180/250/500 kPa; surfaces: chip-sealed bitumen, "gravel" (= sand with unconsolidated stones < 25 mm), grass, soft sand.
- Table 2 means: bitumen 0.002, grass 0.007, gravel 0.006, sand 0.030 (sand 4.5–15× others); pressure and mass effects small and noisy (CoV ~100 %); 29" < 26" off-road, negligible difference on bitumen; suspension no measurable rolling advantage. 100 mm rock: 2–28 % shorter roll-out (worse at low pressure, heavier rider, 26", hardtail).
- Quality caveat: 0.002 for knobby MTB tyres on chip seal is implausibly low (other studies 0.005–0.008 for road tyres on real roads) -> absolute values unreliable (low-speed GPS-derived deceleration, assumed aero); relative ordering is the usable result.

## Martin, Gardner, Barras, Martin 2006 (Sportscience 10:68-69; free) — FULL
- Instructions for a 6-trial field CdA test (constant speed per trial, speeds from ~10 km/h up to the fastest steady speed, 470 m straight flat road worked well, absolute barometric pressure, wind component per trial). Spreadsheet uses TYPICAL μ values because μ is unstable with few points — another confirmation that Crr is poorly identifiable from few steady runs.

# Papers read in full (2026-10-25)

## Grappe, Candau, Barbier, Hoffman, Belli, Rouillon 1999 (Ergonomics 42(10):1361-1371) — FULL
- One rider (66.2 kg, 1.72 m), 9.8 kg bike, hallway (tiled floor) coast-downs with 3 timing switches, 30 runs per condition at 2.5–12.8 m/s, rider keeps pedalling without drive to mimic leg turbulence; upright on tops.
- Pressure (22 mm tubular Vittoria Corsa CX, P in kPa): Crr 0.0101 @150, 0.0069 @300, 0.0050 @600, 0.0040 @900, 0.0038 @1200 -> Cr = 0.1071·P^−0.477 (P in kPa, r² 0.99). 600 -> 900 kPa: −20 %.
- Load (23 mm clincher at 1000 kPa): +0/5/10/15 kg -> Crr 0.0035/0.0036/0.0037/0.0040 (+11.4 % for +15 kg, ≈ Crr ∝ load^0.6 over that range); polynomial Cr = 1.92e−8·Fv² − 2.86e−5·Fv + 0.0142 (Fv in N), linear trend n.s. (p 0.084).
- Literature table: cycling Crr 0.001–0.0081; Pugh 1974 asphalt aerodrome 0.0081 (630 kPa); di Prampero 1979 car track asphalt 0.0046; Kyle & van Valkenburgh 1985 smooth asphalt road 0.0017–0.0043; velodromes 0.0030–0.0031.
- Coast-down repeat tests can vary > 10 % if grade, steering and rider behaviour are not controlled.
- MODEL NOTE: our Crr is mass-independent per kg (F = Crr·m·g). Grappe suggests Crr itself rises with load (≈ +0.7 % per kg); Rothhämel says minor. Effect for a heavy vs light rider ≈ 10 % of rolling term — second order.

## Rothhämel 2023 (Int J Vehicle Systems Modelling and Testing 17(1):67-80; OA) — FULL
- Two-wheeled pendulum (two 26" wheels on a rigid pipe + eccentric 20 kg weight; no bearings involved), Schwalbe Marathon Supreme 42-559 and 50-559, 50–500 kPa, loads 432–1020 N, fine concrete at room temperature; climate chamber −30…+25 °C on smoothed steel and chequer plate (628 N only). 11 runs per setting.
- Load: Crr nearly independent of load (curves overlap), contrary to Grappe 1999.
- Width: 42 mm tyre ~10 % higher Crr than 50 mm of the same model (4–26 % depending on pressure/load; +8 % even at 90 % of each tyre's max pressure). Contradicts Henchoz 2010 (28 mm +0.002 vs 22 mm on treadmill).
- Pressure: strong non-linear rise at low pressure, flattening above ~300–400 kPa (Figs 1–2; read only as plots).
- Temperature: Crr rises steeply in the cold, more so at low pressure. Linearised gradient 5–25 °C (Table 4): −44.8e-6/K @200 kPa, −31.8e-6/K @300, −28.1e-6/K @500 kPa. Baseline on smooth steel Crr 0.0029 @500 kPa, 25 °C.
- Model (eq. 4/5; fraction layout lost in text extraction, reconstructed and checked against the 0.0029 baseline): Crr = b1 + b2/(T + b3), simplified Crr = b2/(T + 46.8), T in °C, b2 = 0.204 (500 kPa), 0.233 (300), 0.278 (200) on smooth steel.
  It implies d ln Crr/dT = −1/(T+46.8) ≈ −1.6 %/K at 15 °C; 20 -> 5 °C = +29 %. The Table 4 linear gradients give only ≈ +15 % for the same step at 500 kPa — the two disagree by ~2×; unresolved (figure not checkable without a PDF renderer).
- Caveats: one tyre model, steel/chequer plate, ambient = tyre temperature (no self-heating from rolling, which for bicycle tyres is small but not zero).
- Gives the Nilges citation (item in its reference list): Nilges 2004 — asphalt/gravel/grass, 150–400 kPa, higher pressure WORSE on gravel and grass. Also cites Bertucci 2013 (grass: low pressure slightly better), Reiser 2003 (width not distinguishable on road), Whitt & Wilson (flat above ~500 kPa).

## García-López, Rodríguez-Marroyo, Juneau, Peleteiro, Córdova, Villa 2008 (J Sports Sci 26(3):277-286) — FULL
- 5 pro road riders (71.6 kg, 1.79 m), ITER wind tunnel 15 m/s, force plate; Mavic Open Pro 32-spoke wheels, 23 mm @ 9 atm; front wheel NOT rotating (fixed on ergometer); 10 min pedalling at 5.5 W/kg (Axiom; true ≈ 4.9–5.0 W/kg).
- CdA (Table I): TT bike static 0.260 ± 0.011 -> TT pedalling 0.341 ± 0.013 (+31 %) -> after lowering bars/advancing pads 0.293 (−14 %) -> without aero helmet 0.297 (n.s.). Standard road bike, hands on bars, no helmet, pedalling: 0.481 ± 0.017 (frontal area 0.364 m², Cd 1.33).
- Ratios: road-bike pedalling / TT pedalling optimised = 1.64; / TT static = 1.85. TT-bike drag alone 0.122 m² (Ménard 1992: 0.146).
- Frontal area 0.30–0.31 m² on TT bike, NOT correlated with BSA; drag area correlates only with torso angle (r 0.42). CdA/kg higher for small riders. Aero helmet helped 3/5 riders, hurt 1 (+14.5 %).
- Literature range cited: upright 0.299–0.390, drops 0.251–0.370, aero 0.191–0.304 m². Reliability CV 1.1 %.
- MODEL NOTE: strongest evidence that pedalling CdA exceeds static values used for Bassett-type bases; but this road-bike value (0.481) is high vs other studies (0.30–0.43) — single lab, static front wheel, no helmet.

## Tengattini & Bigazzi 2018a (J Transp Eng A 144(7):04018031) — FULL
- Coast-down with 12 IR time traps over 100 m + 2D ultrasonic anemometer + surveyed grade; finite-element fit with wind and grade. Rider 78 kg/1.83 m on ~30-year-old road bike, 30 mm commuter tyres, 2 panniers, tops position, back-pedalling.
- Indoor (smooth concrete): Crr 0.0051, CdA 0.449. 80 -> 40 psi: Crr 0.0066 (+29 %). Drops vs tops: CdA 0.401 (−11 %). +10 kg: no change.
- Outdoor asphalt bikeway, headwind: Crr 0.0064 ± 0.0013, CdA 0.63 ± 0.11 (40 psi: Crr 0.0084; drops: 0.539, −14 %). Running track (soft polyurethane): Crr 0.0102.
- Outdoor CdA ≫ indoor (0.63 vs 0.45): attributed to crosswind/gusts and Cd vs Re; parameters absorb all v⁰ and v² effects (bearings, brake rub, speed-dependent Crr).
- Asphalt/smooth-concrete Crr ratio ≈ 1.25 (different but similar bikes).

## Tengattini & Bigazzi 2018b (J Sports Sci 36(20):2383-2391) — FULL
- 557 intercepted urban cyclists, Vancouver, summer 2016, single coast-down each (same rig), off-street paved paths, in-use bikes (no maintenance), coasting (no instruction on legs), wind ≤ low.
- Mean Crr 0.0077 (SD 0.0036; IQR 0.0049–0.0100; Weibull k 2.28, λ 0.00874). Mean CdA 0.559 m² (SD 0.170; IQR 0.434–0.655; Gamma α 10.99, β 19.68). Bike mass 13.7 kg, bike+cargo 18.3, rider 74.7, total 92.2 kg. Tyre width mean 35 mm, pressure ~350 kPa.
- By position: drops Crr 0.0056 / CdA 0.463 (n 22); hoods 0.0061 / 0.477 (n 90); tops 0.0081 / 0.579 (n 438).
- By bike: road 0.0070 / 0.505; hybrid 0.0079 / 0.579; mountain 0.0089 / 0.603; cruiser 0.0078 / 0.640; e-bike 0.0103 / 0.614.
- Tyre: slick 0.0070, commuter 0.0074, knobby 0.0092. Clothing: sport 0.0063 / 0.486, casual 0.0079 / 0.570 (22 % power difference at 15 km/h). Helmet: no effect. Crr ↑ with width and mass, ↓ with pressure; CdA ↑ with width, mass, age, BMI.
- Measurement SD ≈ 0.001 Crr, 0.1 CdA; corrected ranges (±2 SD) 0.001–0.015 Crr, 0.28–0.83 CdA.
- MODEL NOTE: these are coasting values incl. casual clothing, cargo and bike condition; much higher than the project's upright CdA (~0.41) and road CdA (~0.33). Field Crr for road bikes 0.0070 vs project road all-round 0.0081 (incl. our bearing term ≈ 0.0002).

## Meyer, Kloss, Senner 2016 (Procedia Eng 147:526-531; OA) — FULL
- Four-wheeled 70 kg e-bike prototype (QuadRad), 75 kg rider, 3 bar, power (motor + rider) vs speed at 5–25 km/h, both directions, 5 days per surface; fit P = ½ρCdA v³ + Crr m g v.
- Crr: asphalt 0.01221 ± 0.00129, fine gravel 0.01468 ± 0.00128, coarse gravel 0.01832 ± 0.00236 (sig.). CdA 0.84/0.79/0.75 (n.s.).
- Ratios to asphalt: fine gravel ×1.20 (+0.0025), coarse ×1.50 (+0.0061). Includes bearings/drivetrain. Absolute values high because of the vehicle.
- Handlebar vibration magnitude rises linearly with speed and with surface roughness; used to classify the surface.

## Macdermid, Miller, Macdermid, Fink 2015 (Shock and Vibration 2015:191075; OA) — FULL
- 12 national-level XC riders, 29" full-suspension bike with suspension locked, two flights of 8 steps; tyres 35/55/60-622 at pressures scaled by volume (low ×0.666, moderate 0.3 psi per kg system mass for 2.2", high ×1.333); 128 Hz accelerometers at bar, wrist, ankle, seatpost, lumbar, forehead.
- Bigger tyres: faster through the section and lower impact exposure; higher pressure: more acceleration exposure, no time effect. No rolling-resistance or power data. Relevance: off-road comfort only.

## Ejsmont & Sommer 2021 (Coatings 11(7):776; OA) — FULL
- Car/slick motorsport tyres; drum with road-surface replicas (GUT, −15…+30 °C chamber) and R2 Mk.2 trailer.
- MPD (mean profile depth) correlates weakly with Crr; tyres only envelop the texture summits — "enveloped MPD" ≈ 70 % of nominal on SMA8 and 45 % on surface dressing; Crr correlates much better with enveloped MPD.
- Surface dressing (MPD 4.5 mm) vs SMA8 (1.6 mm): Crr +50 % for both soft and hard slicks (0.0102 -> 0.0158; 0.0119 -> 0.0178 at 80 km/h). Soft tread ~15 % lower Crr than hard.
- Road vs replica-drum results correlate well. Water stored in texture cools tyres and raises Crr (cited).
- MODEL NOTE: rough chip-seal type surfaces can add tens of % to Crr even when "paved"; no bicycle data.

## Crenna, Belotti, Colò, Morettini, Tenerini 2025 (Eng 6(9):245; OA) — FULL
- Portable MEMS logger (Raspberry Pi, 1344 Hz) on bars and seatpost; road bike on a closed circuit (IRI ≈ 2 m/km estimated), 24 vs 40 km/h, 4 vs 6 bar, 24/28/32 mm, inner tube vs tubeless.
- Handlebar RMS dominated by speed; pressure ≤ 34 % of the speed effect, then width, then tube type. Regression R² 0.94. No rolling-resistance or power data. Relevance: comfort only.

## Padilla, Mujika, Angulo, Goiriena 2000 (J Appl Physiol 89:1522-1527) — FULL
- Hour record 53.040 km (1994), rider 188 cm / 81 kg. Wind tunnel (static, 50 km/h): CdA 0.244 m², frontal area 0.3755 m² (18.1 % of BSA), Cd 0.65.
- Power estimated with assumed Crr 0.0025 (track), ρ 1.225: 509.5 W. García-López 2008 notes static tunnel CdA under-states pedalling CdA, so this power estimate is likely low.

## Fintelman, Sterling, Hemida, Li 2014 (Procedia Eng 72:720-725; Birmingham OA copy) — FULL
- Mannequin in drops on a road bike and isolated road vs TT bike, 2×2 m tunnel, 9.91 m/s, yaw 0–90°.
- CdA peaks at ~15° yaw, then falls; side force coefficient up to > 2× max drag; total crosswind load up to ~2.5× drag. Torso 16° vs 24°: up to 15 % lower drag (≈ 0.05 m² at 15° yaw).
- At 0° yaw the bike + uprights ≈ 27 % of drag (uprights 8 %). TT bike drag up to 50 % (0.05 m²) lower than road bike but side force up to 34 % higher; rear disc −7 % drag at 0°, +20 % side force.

## Pelland-Leblanc, Lépine, Champoux, Drouet 2014 (Procedia Eng 72:392-397; OA) — FULL
- Two road bikes, cobbled descent and lab shakers; compares acceleration, force and absorbed power at hoods and seatpost. Absorbed power ranks bikes like acceleration and needs no ISO filter. No resistance data. Relevance: comfort methodology only.

## Mastinu, Gobbi, Matrascia 2019 (Bicycle and Motorcycle Dynamics 2019 symposium, Padova; extended abstract) — FULL
- New twin-wheel arm rig on a 2.6 m drum (Politecnico di Milano / Pirelli), ~500 N per tyre, load cell 10 N FS, bearing drag measured separately, aerodynamic drag of forward motion excluded. Crr "a few thousandths"; accuracy 0.1 N. No tyre values given.

## Fenre & Klein-Paste 2021a, published version (J Cold Reg Eng 35(2), DOI 10.1061/(ASCE)CR.1943-5495.0000244; CC BY) — FULL
- Checked against the accepted manuscript read earlier: same numbers (Crr 0.0073 ± 0.0008 on asphalt, n 322; 96.5 % accuracy; precision ±0.005…±0.001). No new findings.

## Crouch, Burton, LaBry, Blair 2017 (Sports Eng 20:81-110; OA) — FULL
- Review of competition aerodynamics. Drag varies ~20 % around the crank cycle (vertical crank = high-drag asymmetric wake); pedalling Cd ≈ 6 % above static horizontal-crank Cd (Crouch 2014).
- Position: upright -> drops −15…20 %, -> TT −30…35 % (average WT data). TT CdA varies up to 40 % between tunnel studies and 60 % vs indirect methods. Table 4 (selected): Gibertini & Grassi 2008 dynamic upright 0.282–0.318, drops 0.275–0.289, TT 0.223–0.235; Kyle & Burke static upright 0.32, drops 0.26; Jeukendrup & Martin upright 0.358, drops 0.307, TT 0.240–0.269; Barry 2015 dynamic upright 0.343, drops 0.295–0.332; García-López 2008 dynamic upright 0.428–0.521.
- Frontal area explains only ~50 % of drag variation between riders/positions (Bassett 1999). Rider ≈ 80 % of total drag; bike ≈ 20 %.
- Wheels alone: disc ≈ −70 % Cd vs conventional spoked, deep-section ≈ −60 %; reported zero-yaw wheel Cd varies 2× between studies.
- Drafting: trailing rider −15…50 % immediately behind, −10…30 % at ~1 bike length; 2nd rider −30…45 %, 3rd+ −35…55 %; leader −1…5 %. Team pursuit power 70.8/64.1/64.0 % of lead (Broker 1999). Side-by-side overtaking can raise both riders' drag ~6 %.
- Field methods: coast-down (legs spinning), linear regression P/v = ½ρCdA v² + m g Crr.

## Malizia & Blocken 2021 (J Wind Eng Ind Aerodyn 214:104673; OA) — FULL
- Review (history + state of the art). Rider body/clothing 64–82 % of drag; bike 18–36 % (≈ 30 % in Nonweiler 1956 and Kyle & Burke 1984; 21–23 % for TT bikes).
- Table 3 CdA by position (selected): Nonweiler 1956 static upright 0.362–0.374, drops 0.283–0.325 (upright 11–32 % higher); Grappe 1997 field (dynamic) upright 0.299, drops 0.276, TT 0.262; Gibertini & Grassi 2008 dynamic upright 0.318, hoods 0.282–0.304, drops 0.275–0.289, TT 0.223–0.235; Defraeye 2010 WT static upright 0.270, drops 0.243, TT 0.211; Barry 2015b dynamic upright 0.343, hoods (horizontal forearms) 0.295, drops 0.306–0.332; Spoelstra 2019 field outdoor upright 0.341, TT 0.254; Valenzuela 2020 field upright 0.351, TT 0.273–0.280; Zdravkovich 1996 hoods ref., drops −12 % / −20 % (bent arms), TT −36 %; Defraeye drops −18 %, TT −32 % vs upright.
- Yaw (Table 1): Martin 1998 TT bike CdA 0.269 (0°) -> 0.238 (15°); Kyle 1991 road bike 0.427 (0°), 0.448 (10°), 0.415 (30°); triathlon 0.221 -> 0.181 (30°).
- Pedalling vs static: dynamic CFD 5–10 % lower than time-averaged static unsteady CFD (Griffith 2019) — contrasts with García-López (+31 %) and Crouch (+6 %); evidence is mixed and setup-dependent.
- Standing sprint ≈ +25 % CdA vs seated (Martin 2006/2007). Loose jacket and trousers +30 % drag (Nonweiler). Larger skinsuit sizes +0.9…6.3 %. Helmet 2–8 % of total drag at 30 km/h; aero vs road helmet 9.9–16.8 % (wind-averaged, mannequin).
- Drafting: 2nd rider −38…54 % at ~0 gap, −33…46 % at 1 m; small yaw (3–5°) reduces the benefit sharply (47 -> 30 %); staggered −23 %. Pacelines (Blocken 2018a): rider 2 ≈ 61–65 %, rider 3 ≈ 50–55 %, rider 4 ≈ 46–51 % of solo drag; leader 97–99 %. Peloton mid-rear 5–10 % of solo drag. Motorcycle 2.5/10/30/50 m ahead: −48/−23/−12/−7 %.
- Passing traffic briefly raised TT speed up to ~5 km/h (Kyle). Pickup truck draft −62 % VO2.
