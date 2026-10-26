# Estimated Power — methodology and design decisions

This document explains how the Estimated Power data field calculates power,
what analysis the model is based on, and why each design decision was made.

Estimated Power is an **estimate**, not a measurement. It is designed for riders
without a power meter who want a consistent number to track their riding over
time. It cannot match a power meter second by second, and some situations
(drafting, braking, strong gusty wind) are not modelled.

## 1. What the device can and cannot provide

The estimate only uses data that a Connect IQ data field can read on the
supported Edge models (540, 550, 840, 850, 1040, 1050).

| Input | Available to a data field? | How it is used |
|---|---|---|
| Speed | Yes (`Activity.Info.currentSpeed`; speed sensor if paired, otherwise GPS) | Every term of the model |
| Distance, barometric altitude | Yes (`elapsedDistance`, `altitude`) | Road gradient |
| Air pressure | Yes (`ambientPressure`, barometer) | Air density |
| Direction of travel | Yes (`track`, GPS course; compass heading as fallback) | Head- or tailwind component |
| Cadence | Yes, with a cadence sensor | Coasting detection only |
| Rider weight and height | Yes (`UserProfile`) | Mass and frontal area |
| Weather: wind, temperature, humidity | Yes (`Toybox.Weather`, synced from the phone) | Wind and air density |
| Ride profile sport and sub-sport | Yes (`Activity.getProfileInfo()`) | Selects the bike preset |
| List of the rider's Edge profiles | **No** (the phone settings are static; the device only knows the current profile) | Presets use a fixed list of ride types |
| Paved / unpaved surface | Indirectly: the Edge's map-based surface splits (`onTimerSplitStart/End`, split types *paved* and *unpaved*) | Switches rolling resistance |
| Road gradient from the device or maps | **No.** No grade field, no map elevation lookup, no grade complication | Computed from altitude instead |
| Road type or quality from maps | **No** | Real-road factor (section 3.4) |
| Bike weight from the Edge bike profile | **No** | Entered in a bike preset |
| Device temperature sensor | **No.** `Sensor.getInfo()` is documented to crash data fields; `SensorHistory` and complications are not available on these models | Weather temperature used instead |

## 2. Model structure

Each second the data field calculates the power needed at the pedals to hold
the current speed, using the road-cycling model of Martin et al. (1998). That
model was validated against power meters with R² = 0.97 and a standard error of
2.7 W under controlled conditions.

```
P = ( P_roll + P_gravity + P_air + P_accel + P_bearings + L ) / η

P_roll     = Crr · m · g · cos θ · v
P_gravity  = m · g · sin θ · v
P_air      = ½ · ρ · (CdA + F_w) · v_air · |v_air| · v
P_accel    = ½ · m_eff · (v² − v_prev²) / Δt
P_bearings = v · (91 + 8.7 · v) · 10⁻³
L          = 2 W,  η = 0.985   (drivetrain: fixed loss + 1.5 %)
```

Martin et al. used a constant efficiency of 0.976. Drivetrain measurements show
a fixed loss (seals, lubricant, chain) plus a share of the power (Rohloff &
Greb 2003; Kyle & Berto 2001), so efficiency is lower at recreational power.
The fixed-plus-share form gives the same result as 0.976 at about 170 W and
about 1 W more at 75 W.

| Symbol | Meaning |
|---|---|
| v | ground speed, m/s |
| v_air | air speed along the direction of travel, m/s (v + headwind component) |
| m | rider + bike + extra mass, kg |
| m_eff | m + 1.4 kg: the rotational inertia of the wheels as equivalent mass |
| θ | road angle, atan(gradient) |
| g | 9.80665 m/s² |
| ρ | air density, kg/m³ |
| CdA | drag area of rider + bike, m² |
| F_w | 0.0044 m², extra drag of the rotating wheels and spokes |
| Crr | rolling resistance coefficient |
| η | drivetrain efficiency |

Rules applied each second:

- Below 1 m/s, or while a cadence sensor reports 0 rpm (coasting), power is 0.
- Negative results (braking, descending) are set to 0, as a power meter would report.
- The acceleration term is skipped if the gap since the previous reading is not between 0.5 and 3 s.
- The displayed and recorded value is the mean of the last 3 per-second values (fixed for now; see section 5).
- Lap and ride averages include zeros (coasting and stops while the timer runs).

Published platform models (Strava's documented formula, community
reverse-engineering of Zwift) use the same structure without the bearing,
wheel-drag and drivetrain terms. Those terms add about 4 % to the estimate.
They are kept because they are part of the validated model and represent real
losses.

## 3. Parameters and why they were chosen

### 3.1 Air drag (CdA)

```
A_TT = 0.0293 · height^0.725 · mass^0.425 + 0.0604      (m², height in m, mass in kg)
CdA  = 0.707 · A_TT · position factor
```

- **Frontal area:** the equation of Bassett et al. (1999), from height and body
  mass. It estimates the total frontal area of rider and bike in an aero position.
  The constant term most likely represents the bicycle (an interpretation; the
  sources do not state it).
- **Drag coefficient 0.707:** the average from wind-tunnel tests of riders on
  their bikes, as quoted alongside the Bassett equation. Together these give a
  time-trial CdA.
- **Riding position:** other positions are scaled with ratios of typical
  published CdA values (drops ~0.30, hoods ~0.33, upright ~0.40 m²). The
  aero-bar factor is 1.15 rather than 1.00: the Bassett × 0.707 value (~0.23 m²)
  is a static wind-tunnel figure, while pedalling and field-measured time-trial
  CdA is 0.25–0.29 m² (García-López et al. 2008: +31 % pedalling vs static;
  field values in Malizia & Blocken 2021).
  Riders change position during a ride and the estimate must not need any input
  while riding, so each option is a time-weighted mix. Power is linear in CdA,
  so the mix gives the correct average.

| Position option | Mix | Factor |
|---|---|---|
| Road | 70 % hoods, 30 % drops | 1.405 |
| Time trial | 95 % aero bars, 5 % base bar (braking, corners) | 1.165 |
| Upright | flat bar (MTB, city) | 1.75 |

- **Clothing:** a preset option, cycling kit (× 1.00) or casual clothes
  (× 1.17). In 557 coast-down tests of urban riders, riders in casual clothes
  had a mean CdA of 0.570 m² against 0.486 m² in sport clothing (Tengattini &
  Bigazzi 2018). The same study's tops/hoods ratio (1.21) is close to the
  model's upright/road ratio (1.25), so the position factors are kept and the
  clothing difference is applied separately. Casual is the default for the
  Commuting ride type.

- **Wheel rotation drag (F_w = 0.0044 m²):** wind-tunnel CdA does not include the
  drag of spinning wheels. Martin et al. measured this separately. Other work
  suggests larger values for some wheels; the Martin value is used for
  consistency with the rest of the model. Its effect is below 1 %.
- **Tyre width:** the Bassett frontal area was derived on narrow-tyred bikes, so
  it represents road tyres. Wind-tunnel tests measure about 0.010 m² of extra
  drag area per 10 mm of extra tyre width (about 3.6 W per 10 mm at 30 km/h and
  almost 12 W at 45 km/h). Peer-reviewed data show the same direction: the
  wheel's drag area grows with the tyre-to-rim width ratio (Crane & Morton 2018,
  via Malizia & Blocken 2020). Knobs and tread roughness add to this, and a wide
  rim matched to the tyre roughly halves it. The rider sets the tyre width in
  the preset (18–60 mm, in 1 mm steps), and the model adds 0.0010 m² per mm
  above 28 mm; 28 mm and narrower add nothing:

  | Width | Extra CdA | At 25 km/h | At 35 km/h |
  |---|---|---|---|
  | ≤ 28 mm | 0 | 0 W | 0 W |
  | 32 mm | +0.004 m² | +1 W | +2 W |
  | 40 mm | +0.012 m² | +3 W | +7 W |
  | 45 mm | +0.017 m² | +4 W | +10 W |
  | 50 mm | +0.022 m² | +5 W | +13 W |
  | 60 mm | +0.032 m² | +7 W | +18 W |

  Width affects only drag for now. Its effect on rolling resistance is unclear:
  at equal pressure a wider version of the same tyre rolled about 10 % easier
  (Rothhämel 2023), another study found the opposite (Henchoz et al. 2010, as
  cited), and in practice wider tyres run at lower pressure. Club data will be
  used to check it.

- CdA is always derived from the rider's height and weight, the position, the
  clothing and the tyre width. There is no override, so results stay comparable between riders
  and between rides.

### 3.2 Mass

Rider mass comes from the Garmin user profile (or an override). Bike and extra
mass (bottles, bags, clothing) come from the bike preset, because the Edge's own
bike profiles are not readable by Connect IQ. Mass errors matter mainly on
climbs (about 5 W per 2 kg on a 7 % climb at 12 km/h).

### 3.3 Rolling resistance of the tyre

```
Crr_drum = tyre watts × class factor / (42.5 kg · g · 8.0 m/s)        road and MTB tyres
Crr_drum = tread watts / (42.5 kg · g · 8.0 m/s)                       gravel tyres
```

Tyre rolling resistance is expressed in the form used by public drum tests: the
watts needed by one tyre at 42.5 kg load and 28.8 km/h.

| Tyre type | Watts, all-round class | Crr on the drum |
|---|---|---|
| Road | 15 W | 0.0045 |
| Mountain bike | 30 W | 0.0090 |

Tyre class (road and MTB tyres): Fast = 20 % lower, All-round = reference,
Durable (puncture protection, comfort casings) = 35 % higher.

Gravel tyres differ mostly in their tread, so the preset asks for the tread
instead of the class:

| Gravel tread | Watts | Crr on the drum |
|---|---|---|
| Slick | 13.3 W | 0.0040 |
| File tread / low knobs | 16 W | 0.0048 |
| Knobby | 20 W | 0.0060 |

The knobby value is about 0.002 above the slick, from field data: knobby tyres
measured +0.0022 over slicks in 557 urban coast-downs (Tengattini & Bigazzi
2018), and smooth tyres 21 % below knobby ones off-road (Bertucci et al. 2013).
No study compared a file tread with a slick of the same width, so the file tread
sits between them as an estimate. It keeps the value of the former fast gravel
setting, and knobby keeps the former all-round gravel value. All tyre values
are placeholders until averaged test data is available.

### 3.4 Real roads: + 0.0033

Drum tests and good, smooth asphalt underestimate the rolling resistance of
ordinary roads. A field study for the California Department of Transportation
(UCPRC-RR-2016-02) measured it on eight straight, flat road sections with a road
bike, a crank power meter and the Martin model:

| Surface | Crr (μ) | Relative to the good-asphalt baseline |
|---|---|---|
| Good dense asphalt (baseline, value assumed by the study) | 0.0040 | 1.0 |
| Other asphalt sections | 0.0066–0.0098 | 1.65–2.45 |
| Chip seal sections | 0.0068–0.0096 | 1.7–2.4 |

Rolling resistance correlated with surface macrotexture (mean profile depth,
R² 0.70) more than with roughness (IRI, R² 0.34). Road-tyre and pavement
research on car tyres shows the same direction: rolling resistance rises with
surface texture.

What the study measured are the differences from the baseline: +0.0026 to
+0.0058, median about +0.0035 (its μ includes wheel-bearing friction). The
ratios in the table exist only because the baseline was assigned μ = 0.004
rather than measured, so a ratio such as 1.8 inherits that assumption, while
the measured differences do not. Club power-meter rides will check the value.

**Decision:** paved Crr = drum Crr + 0.0033 for all tyre types: the study's
median difference (+0.0035) minus the wheel-bearing share it contains (about
0.0002), because bearings are a separate term in the model. The tyre class
scales only the drum part. The device cannot know the road quality, so a single
typical value is used.

An earlier version used drum Crr × 1.8. For road tyres both give almost the
same value (0.0078 vs 0.0081 all-round), so the platform comparison in
section 4.3, made with × 1.8, still applies: the mean segment ratio moved from
0.82 to 0.93 and the segment RMS error from about 20 % to 12.4 %. For gravel and
MTB tyres the addition gives lower values (0.0093 vs 0.0108; 0.0123 vs 0.0162);
independent field data on paved paths (road bikes 0.0070, MTBs 0.0089,
including bearings; Tengattini & Bigazzi 2018) supports the lower values.

### 3.4a Tyre temperature

Rolling resistance rises in the cold. Pendulum tests of one bicycle tyre from
−30 to +25 °C fitted Crr ∝ 1 / (T + 46.8) (Rothhämel 2023), which is +29 % from
20 to 5 °C; the same paper's linear fit over 5–25 °C gives roughly half of that.
The model uses half strength:

```
Crr_tyre(T) = Crr_tyre(20 °C) × (1 + 0.5 × ((20 + 46.8)/(T + 46.8) − 1)),  T clamped to −20…40 °C
```

| T | 0 °C | 5 °C | 10 °C | 20 °C | 30 °C |
|---|---|---|---|---|---|
| Factor | 1.21 | 1.14 | 1.09 | 1.00 | 0.93 |

That is the factor on the tyre Crr; at 25 km/h on a road bike, 5 °C adds about
7 W. T is the air temperature: a data field cannot read the Edge's temperature
sensor, so it is the weather temperature, else the last stored weather
temperature (under 6 h old), else 15 °C; indoors 20 °C. The factor is
recalculated when the temperature changes, not every second. The unpaved
addition (section 3.5) is not scaled, since it is mostly surface loss.

### 3.5 Unpaved surfaces

While the Edge reports an unpaved split, a fixed amount is added to the paved
Crr:

| Tyre type | Unpaved addition | Resulting Crr (all-round, 20 °C) |
|---|---|---|
| Road | +0.0070 | 0.0148 |
| Gravel | +0.0043 | 0.0124 (file tread) |
| Mountain bike | +0.0040 | 0.0163 |

Measured surface differences are additions of similar size whatever the tyre:
fine gravel +0.0025 and coarse gravel +0.0061 above asphalt (Meyer et al. 2016;
1.2× and 1.5× in ratio terms). Gravel tyres get the middle of that range,
+0.0043 (about 1.35×),
gravel and grass about +0.004 above bitumen (Steyn & Warnich 2014), a soft
running track +0.0038 above an asphalt path (Tengattini & Bigazzi 2018). Road
tyres get more because slick, high-pressure tyres sink in and slip on loose
surfaces and higher pressure loses more on rough ground (Nilges 2004, as cited
by Rothhämel 2023), so gravel tyres end up ahead of road tyres there. The exact
values per tyre type are judgement within the measured range and will be refined
with club power-meter data.

Example, 80 kg total at 25 km/h, rolling resistance power at the pedals:

| Tyre (fast class; gravel by tread) | Paved | Unpaved |
|---|---|---|
| Road | 38 W | 77 W |
| Gravel, slick | 40 W | 64 W |
| Gravel, file tread | 45 W | 69 W |
| Gravel, knobby | 51 W | 75 W |
| Mountain bike | 58 W | 80 W |

Surface detection relies on Garmin's map data. Recorded test rides with gravel
sections contained alternating paved and unpaved splits matching the unpaved
stretches. Splits with no distance are ignored. Accuracy depends on how current
Garmin's map data is.

### 3.6 Road gradient

Connect IQ does not expose a gradient value or map elevation, so gradient is the
slope of a least-squares line through barometric altitude against distance,
over the most recent ≥25 m of road with at least 4 readings. It is limited to
±30 % and held while stopped.

The window length was chosen by testing on recorded barometric data, comparing
the live estimate with a gradient calculated afterwards over the whole road:

| Window | RMS error (percentage points of gradient) |
|---|---|
| 5 m | 1.43–1.53 |
| 10 m | 0.95–1.09 |
| 15 m | 0.80–0.94 |
| **25 m** | **0.73–0.84** |
| 40 m | 0.78–0.80 |
| 60 m | 0.83–0.96 |

Shorter windows looked better on noise-free virtual altitude but are clearly
worse on real barometer data. The delay is roughly half the window: about 2 s at
25 km/h and 4–5 s at 10 km/h. Gradient error is the largest source of
second-to-second noise (section 5).

### 3.7 Air density and temperature

```
ρ = (p − p_v) / (287.058 · T) + p_v / (461.495 · T)
p_v = RH · 610.78 · 10^(7.5·t / (t + 237.3))         (Tetens equation)
```

- Pressure p comes from the barometer. Without it, the standard-atmosphere
  pressure for the current altitude is used.
- Temperature and humidity come from Garmin's weather. The Edge's own
  temperature sensor is not readable by a data field (section 1).
- If weather becomes unavailable, the last weather values are kept for the rest
  of the ride. They are also saved on the device, so a ride that starts without
  weather can use them if they are under 6 hours old; otherwise 15 °C and 50 %.
  A 15 °C error changes air drag by about 5–6 % and, through the
  tyre-temperature factor (section 3.4a), rolling resistance by up to about
  10 %, which is a few watts at typical speeds.

### 3.8 Wind

```
headwind = wind speed × exposure × cos(wind direction − direction of travel)
```

- Wind speed and direction come from Garmin's weather (current conditions, or
  the nearest hourly forecast when current conditions have no wind), read once
  a minute. Garmin refreshes weather every 15–30 minutes, so gusts and local
  shelter are not captured.
- Weather stations report wind at 10 m. It is reduced to rider height using the
  logarithmic wind profile ln(1.2/z₀)/ln(10/z₀). A fixed "mixed terrain" value
  is used (z₀ = 0.1 m, factor 0.54); sheltered (z₀ = 0.25 m) would give 0.43 and
  open country (z₀ = 0.03 m) 0.64. It is not a setting, because riders cannot
  judge it reliably and it changes along a route.
- Only the head- or tailwind component is used; crosswind drag is not modelled.
- Garmin documents the wind bearing only as "North = 0, East = 90". The model
  assumes the meteorological convention (direction the wind comes from). This
  needs confirming on a device.

### 3.9 Bike presets per ride type

Bike setup (tyre type, tyre class, position, bike weight, extra weight of 1, 1.5
or 2 kg) is stored in presets, one per ride type. When the activity starts, the
ride type of the Edge profile (its sport and sub-sport) selects the preset, so
nothing has to be changed during a ride. Ride types are chosen from a fixed list
because Connect IQ cannot show the rider's Edge profiles in the phone settings.
Two bikes of the same ride type cannot be told apart; the first matching preset
is used.

Bike weight has no default and must be entered, because it varies too much
between bikes for a default to be meaningful. The preset list starts empty;
without a preset, built-in values for the ride type are used.

| Edge ride type | Supported | Built-in values without a preset |
|---|---|---|
| Road (and profiles with no specific type) | Yes | Road tyres, road position |
| Gravel | Yes | Gravel tyres, road position |
| Mountain | Yes | MTB tyres, upright position |
| Commuting | Yes | Road tyres, upright position |
| Indoor cycling | Yes: no gradient, wind or surface switching, 20 °C | Road tyres, road position |
| Cyclocross, e-bike, other activities | No: the field shows "--" and records nothing | — |

Cyclocross is excluded because its frequent, large power changes (short
accelerations, dismounts, very low speeds) cannot be estimated reliably from
speed and gradient. E-bikes are excluded because the motor's contribution is
unknown. Indoors there is no road gradient, wind or surface, and barometric
altitude drift would create false gradients, so those inputs are ignored. Indoor
estimates are based on wheel speed with the road model and are not calibrated
to a trainer's resistance curve.

## 4. Analysis performed

### 4.1 Virtual rides with trainer-based power

Three indoor virtual rides were recorded with power calculated by the virtual
platform from a fluid trainer's resistance curve. The platform's virtual speed
is itself computed from that power with its own physics, so these files test
whether the model reproduces a known physics engine. They do not measure
real-world accuracy.

- With real-world default parameters, the estimate was 19–38 % above the
  platform's power. Climbs agreed within about 0–12 %. Flats and descents were
  higher, showing lower air drag in the virtual model.
- With a fitted CdA, one ride was reproduced almost exactly: ride average within
  1 %, 30 s mean error 5 W, 5 min mean error 1 W. The other two needed a lower
  CdA, consistent with virtual drafting. The fitted rolling resistance, 0.004,
  matched the community-documented virtual value for road wheels.
- Estimate and platform power aligned best at 0–1 s delay, so the model adds no
  timing lag.

**Conclusion:** the model structure and the gradient and acceleration handling
are sound. The virtual platform's drag values were not adopted, because they
describe a virtual world.

### 4.2 Comparison of published model variants

On one outdoor ride (2.5 h, gravel bike), several published or reverse-engineered
variants were compared, relative to the model before the real-road factor (= 100):

| Variant | Relative estimate |
|---|---|
| This model before the real-road factor (Martin structure, tyre-based Crr) | 100 |
| Same, with a typical virtual-platform gravel Crr (0.008) | 112 |
| Virtual-platform-like model (simple structure, weight-scaled CdA, gravel Crr) | 105 |
| Virtual-platform-like model, road wheels | 91 |
| Heil (2001) drag coefficient × Bassett frontal area | 98 |
| Third-party platform estimate for the same ride | 132 |

**Conclusion:** no published formula variant explained the third-party estimate.
The differences come from parameter values (mainly rolling resistance by bike
type), not from the equation.

### 4.3 Segment-level comparison with a third-party estimate

Thirty segment estimates from a third-party platform were located in the same
outdoor ride by elapsed time, distance and gradient. Twenty were unambiguous and
used for the comparison.

| Model state | Mean ratio model / platform | RMS error |
|---|---|---|
| Before the real-road factor | 0.82 | ~20 % |
| After the real-road factor | 0.93 | 12.4 % |
| After adding tyre-width drag (current) | 0.94 | 11.6 % |

Steep climbs (5.7–9.1 %) were already within 9–12 % before the change,
because gravity dominates there. The difference was on flatter roads, where
rolling resistance and air drag dominate.

### 4.4 Hypotheses tested and rejected

- **Noisy GPS speed inflating the third-party estimate.** Simulating a
  point-by-point calculation from GPS-derived speed with a zero floor first
  appeared to match. On inspection, that result came from a few GPS position
  jumps creating unrealistic spikes. With those filtered, the pipeline remained
  20–29 % below the platform estimate, so it does not explain the difference.
- **A missing term in the equation.** Comparing against the published models
  found only the wheel-rotation drag term missing; it was added (+0.7 %).

### 4.5 Coasting analysis

While coasting (cadence 0), rider power is zero, so deceleration measures air
drag plus rolling resistance directly. Coasting stretches from five outdoor rides
were analysed. There were too few clean windows, over too narrow a speed range,
to separate CdA from Crr reliably, and light braking cannot be ruled out. The
gentle-gradient fits did agree that total resistance at 23 km/h was 60–90 %
higher than the model before the real-road factor. That pointed to the same
conclusion as the literature in section 3.4. A dedicated coast-down test
(no braking, both directions, several speeds) is planned.

### 4.6 Sensitivity

Example: 85.5 kg rider + bike, hoods (CdA 0.348 m²), all-round road tyres, 15 °C.

| Situation | Base | Gradient off by 1 % | Headwind off by 2 m/s | CdA off by 10 % | Crr off by 0.001 | Mass off by 2 kg |
|---|---|---|---|---|---|---|
| Flat, 25 km/h | 124 W | ±59 W | ±48 W | ±7 W | ±6 W | ±1 W |
| Flat, 35 km/h | 272 W | ±83 W | ±91 W | ±20 W | ±8 W | ±2 W |
| 7 % climb, 12 km/h | 232 W | ±28 W | ±13 W | ±1 W | ±3 W | ±5 W |

Gradient and wind errors dominate short-term accuracy. Gradient errors largely
cancel over a ride that starts and ends at similar altitude, so lap and ride
averages are much more reliable than the 3 s value.

## 5. Decisions

| Decision | Reason |
|---|---|
| Martin et al. (1998) model structure | Validated against power meters; includes all significant losses. |
| Physics-based defaults instead of copying a platform's values | Platforms use fixed values per bike type, and platforms disagree with each other. Physical values with documented sources stay consistent between rides, which is what progress tracking needs. |
| Real-road addition +0.0033 for all tyre types | The measured quantity in the field study is a difference from good asphalt, not a ratio (section 3.4); the device cannot detect road quality. |
| Tyre-temperature factor at half strength | Rolling resistance rises in the cold; the source's two fits differ by about 2× (section 3.4a). |
| Time-trial factor 1.15, clothing option | Pedalling and field CdA exceed static wind-tunnel values; casual clothing measured 17 % higher CdA (section 3.1). |
| Drivetrain loss 2 W + 1.5 % | Measured losses have a fixed part; same as 0.976 at ~170 W (section 2). |
| Tyre width as a preset setting (18–60 mm) driving extra drag area | Width, not tyre type, decides the extra drag; a gravel bike on slicks or a road bike on 32 mm tyres is then described correctly (section 3.1). |
| Tread instead of class for gravel tyres | Gravel tyres differ mainly in tread; field data put knobby about 0.002 Crr above slick (section 3.3). |
| Unpaved additions, largest for road tyres | Measured surface losses are additions of similar size; slick road tyres lose more on loose surfaces (section 3.5). |
| Time-weighted riding-position mixes | Riders change position during a ride; no input is needed while riding. |
| Bike presets matched to the ride type | Bike data and the list of Edge profiles are not readable; matching by ride type selects the right setup automatically. |
| Cyclocross and e-bikes not supported | Cyclocross power changes too much to estimate reliably; an e-bike motor's contribution is unknown. |
| Barometric gradient over 25 m | Best of the windows tested on real barometer data (section 3.6); map gradient is not available. |
| Weather first, last weather value as fallback | The device's temperature sensor cannot be read by a data field. Temperature affects air density and the tyre-temperature factor. |
| Drafting not modelled | It cannot be detected reliably. Estimates while drafting will be higher than the rider's actual output. |
| Negative power set to 0; coasting = 0 | Matches how power meters report braking and coasting. With a cadence sensor the 3 s mean is clamped rather than each second, so noise does not bias averages upwards. |
| 3 s averaging, not a setting | Smooths second-to-second noise while staying responsive; the final window will be chosen from test results. |
| No CdA/Crr overrides, fixed wind exposure | Keeps estimates comparable and avoids settings riders cannot judge reliably. |
| Bike weight required, no default | Bike weights vary too much for a default to be meaningful. |
| Estimate written to the FIT file, optionally tagged as power | Garmin Connect shows it as a Connect IQ chart. Some third-party services accept the power tag when no real power meter data is present. |
| One field that adapts to its slot (3 s power; lap average beside or underneath in large slots) | The Edge's built-in power fields only accept a paired power meter, and separate Connect IQ apps cannot share settings or data, so a single field shows the lap average where there is room. |
| No extra sensors, network requests or high-rate sensor data | The data field only reads values the Edge already calculates, so its battery impact is minimal. |

## 6. Known limitations and open items

- Not modelled: drafting, crosswind drag, standing on the pedals, braking while
  pedalling, tyre pressure.
- The tyre-temperature factor rests on one tyre on a lab rig and uses air, not
  tyre, temperature.
- Gradient lag: just past a crest the gradient still reads positive for a few
  seconds, so the estimate briefly reads high.
- Without a cadence sensor, negative values are set to 0 before averaging,
  which biases averages slightly upwards when the estimate is noisy around low
  power.
- Weather is area-level and refreshed every 15–30 minutes; the wind direction
  convention needs confirming on a device.
- Tyre rolling-resistance values are placeholders pending averaged test data.
- The unpaved additions per tyre type are judgement within the measured range.
- Validation against rides recorded with real power meters is still to be done.

## 7. References

- Martin JC, Milliken DL, Cobb JE, McFadden KL, Coggan AR. Validation of a
  mathematical model for road cycling power. *J Appl Biomech* 1998;14:276–291.
  https://collections.lib.utah.edu/dl_files/b4/8e/b48ef26086091662c561e673d7bd990d77868437.pdf
- Bassett DR, Kyle CR, Passfield L, Broker JP, Burke ER. Comparing cycling world
  hour records, 1967–1996: modeling with empirical data. *Med Sci Sports Exerc*
  1999;31:1665–1676.
- Faria EW, Parker DL, Faria IE. The science of cycling: factors affecting
  performance (parts 1 and 2). *Sports Med* 2005 (restates the Bassett equation).
  https://www.researchgate.net/publication/7906170_The_science_of_cycling_physiology_and_training_-_part_1
- Coggan A. Estimation of CdA from anthropometric data (Cd ≈ 0.707 from Kyle's
  wind-tunnel data). http://www.trainingandracingwithapowermeter.com/2011/04/estimation-of-cda-from-anthropometric.html
- Heil DP. Body mass scaling of projected frontal area in competitive cyclists.
  *Eur J Appl Physiol* 2001. https://www.researchgate.net/publication/11788060_Body_mass_scaling_of_projected_frontal_area_in_competitive_cyclists
- Translating uphill cycling into a head-wind and vice versa (range of wheel
  rotation drag values). *Journal of Science and Cycling*.
  https://www.jsc-journal.com/index.php/JSC/article/download/296/391
- UC Pavement Research Center. Development of recommended guidelines for
  preservation treatments for bicycle routes, UCPRC-RR-2016-02 (Caltrans).
  https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/f0016607-ca17-2693-finalreport.pdf
- UC Pavement Research Center. Surface treatment macrotexture and bicycle ride
  quality. https://escholarship.org/content/qt3dp663w0/qt3dp663w0.pdf
- Swiss Side. Aerodynamics in gravel: performance test (tyre width and tread).
  https://www.swissside.com/en-us/blogs/aero-tech-tips/gravel-report
- Cyclingnews. Lab tested: 40mm road tyres are faster for nearly everyone.
  https://www.cyclingnews.com/features/lab-tested-40mm-road-tyres-are-faster-for-nearly-everyone-and-heres-why/
- Silca. Part 5: Tire pressure and aerodynamics.
  https://silca.cc/blogs/silca/part-5-tire-pressure-and-aerodynamics
- CyclingAbout. The fastest aero gravel bikes, wind tunnel tested (TOUR data,
  slick vs treaded tyres). https://www.cyclingabout.com/fastest-aero-gravel-bikes-wind-tunnel-tests/
- Silca. Part 4B: Rolling resistance and impedance.
  https://silca.cc/blogs/silca/part-4b-rolling-resistance-and-impedance
- NCAT Report 14-07: Effects of pavement properties on vehicular rolling
  resistance. https://eng.auburn.edu/research/centers/ncat/files/reports/2014/rep14-07.pdf
- NCAT Report 20-04: Influence of asphalt pavement characteristics on rolling
  resistance. https://eng.auburn.edu/research/centers/ncat/files/technical-reports/rep20-04.pdf
- Tire/road rolling resistance modeling: discussing the surface macrotexture
  effect. *Coatings* 2021;11(5):538. https://doi.org/10.3390/coatings11050538
- Bicycle Rolling Resistance, test method (drum protocol: 42.5 kg, 28.8 km/h).
  https://www.bicyclerollingresistance.com/the-test
- Strava power calculation description (support article, as quoted).
  https://www.roadbikereview.com/threads/whats-up-with-strava-watts.367269/
- ZwiftInsider. Rolling resistance on Zwift: Crr of various wheels.
  https://zwiftinsider.com/crr/
- ZwiftInsider. How rider weight affects speed on Zwift. https://zwiftinsider.com/rider-weight-speed/
- Hilton G. Zwift bike selector (reverse-engineered physics). https://greghilton.co.uk/php/zwift-bike-selector.html
- Garmin Connect IQ API documentation (SDK 9.3.0): Activity.Info,
  Activity.ProfileInfo, Activity.SplitInfo, WatchUi.DataField, UserProfile,
  Weather, FitContributor, Sensor, SensorHistory, Complications, Properties and
  app settings. https://developer.garmin.com/connect-iq/api-docs/
- Garmin Connect IQ forum: native field numbers in Garmin Connect and
  third-party services.
  https://forums.garmin.com/developer/connect-iq/i/bug-reports/nativenum-field-is-ignored-by-garmin-connect-so-accessories-can-t-be-integrated-properly
- Standard formulas: Tetens equation (saturation vapour pressure), International
  Standard Atmosphere (pressure vs altitude), logarithmic wind profile.
- Rothhämel M. On rolling resistance of bicycle tyres with ambient temperature in
  focus. *Int J Vehicle Systems Modelling and Testing* 2023;17(1):67–80.
  https://doi.org/10.1504/ijvsmt.2023.132317
- Tengattini S, Bigazzi AY. Physical characteristics and resistance parameters
  of typical urban cyclists. *J Sports Sci* 2018;36(20):2383–2391.
  https://doi.org/10.1080/02640414.2018.1458587
- García-López J, Rodríguez-Marroyo JA, Juneau C, Peleteiro J, Martínez AC,
  Villa JG. Reference values and improvement of aerodynamic drag in professional
  cyclists. *J Sports Sci* 2008;26(3):277–286. https://doi.org/10.1080/02640410701501697
- Malizia F, Blocken B. Cyclist aerodynamics through time: better, faster,
  stronger. *J Wind Eng Ind Aerodyn* 2021;214:104673. https://doi.org/10.1016/j.jweia.2021.104673
- Meyer D, Kloss G, Senner V. What is slowing me down? Estimation of rolling
  resistances during cycling. *Procedia Eng* 2016;147:526–531. https://doi.org/10.1016/j.proeng.2016.06.232
- Steyn WJvdM, Warnich J. Comparison of tyre rolling resistance for different
  mountain bike tyre diameters and surface conditions. *S Afr J Res Sport Phys
  Educ Recreat* 2014;36(2):179–193.
- Kyle CR, Berto F. The mechanical efficiency of bicycle derailleur and hub-gear
  transmissions. *Human Power* 2001;52:3–11.
- Rohloff B, Greb P. Rebuttal of Kyle & Berto (2001), with a reply by C.R. Kyle.
  *Human Power* 2003;55:11–15.
- Nilges P. Auswirkung unterschiedlicher Mountainbikereifen auf die
  Rollwiderstandsleistung im Gelände. German Sport University Cologne, 2004
  (as cited by Rothhämel 2023).
- The full research bibliography is in the README.
