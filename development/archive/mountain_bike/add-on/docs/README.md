# Estimated Power — Connect IQ data field for Garmin Edge

Estimates the rider's power output in real time, without a power meter, from
data the Edge already has. It shows a rolling 3 s average and records the
estimate to the activity FIT file.

> **Status:** first draft. Compiles with Connect IQ SDK 9.3.0 for the Edge 540, 550,
> 840, 850, 1040 and 1050 (strict type checking); earlier builds loaded in the
> simulator. The latest model changes (real-road addition, unpaved additions,
> tyre temperature, time-trial factor, clothing setting, drivetrain losses,
> clamping) are tested with the Python reference model and compiled, but not yet
> run in the simulator or on a device. See [Open items](#open-items).
>
> The analysis behind the model and the reasoning for each decision are in
> [docs/METHODOLOGY.md](docs/METHODOLOGY.md).

## How it works

Once per second (the Connect IQ `compute()` rate) the field calculates the
power needed at the cranks:

```
P = ( Crr·m·g·cosθ·v               rolling resistance
    + m·g·sinθ·v                   gravity
    + ½·ρ·(CdA + 0.0044)·v_air·|v_air|·v   aerodynamic drag (with wind) + wheel rotation drag
    + d(½·m_eff·v²)/dt             acceleration
    + v·(91 + 8.7·v)·10⁻³ )        wheel bearings
    + 2 W ) / 0.985                drivetrain: fixed loss + 1.5 %
```

This is the model of Martin et al. (1998), with drivetrain losses as a fixed
part plus a share of the power (Rohloff 2003; Kyle & Berto 2001). Coasting is
recorded as 0 when a cadence sensor reads 0 rpm. Values below zero (braking,
descending) are recorded as 0: with a cadence sensor the 3 s mean is clamped
(negative values while pedalling are mostly gradient noise, and clamping each
second would bias averages upwards); without one, each second is clamped. The displayed and recorded value is the mean of the last 3 per-second
values (fixed for now; the window will be decided from test results).

### Display

The field adapts to the size of the slot it is placed in:

| Slot | Shows |
|---|---|
| Full width and wide (width ≥ 1.6 × height) | 3 s power with "W" on the left, lap average with "Lap" on the right |
| Tall (≥ 30 % of the screen height) | 3 s power with "W", lap average with "Lap" underneath |
| Smaller slots | 3 s power with "W" only |

The lap value is drawn at most 60 % of the height of the 3 s value. Before the
timer starts, and right after a new lap, the lap value shows "--".

| Input | Source on the device | Notes |
|---|---|---|
| Speed `v` | `Activity.Info.currentSpeed` | Uses a speed sensor if paired, otherwise GPS. |
| Gradient `θ` | Least-squares fit of `altitude` vs `elapsedDistance` over the last ≥25 m | Connect IQ does **not** expose the Edge's own grade value. |
| Rider weight, height | `UserProfile.getProfile()` | Can be overridden in the settings. |
| Bike + extra weight | Bike preset for the ride type of the current Edge profile | Connect IQ does **not** expose the Edge bike profile. |
| CdA | Bassett et al. (1999) total frontal area of rider + bike from height and weight × Cd 0.707 × riding-position factor × clothing factor, + tyre-width drag (0.0010 m² per mm above 28 mm), + 0.0044 m² for wheel rotation (Martin et al. 1998) | Position is a time-weighted mix (see Settings). |
| Crr | Tyre type and class from the preset + 0.0033 for real roads, × tyre-temperature factor; + an unpaved addition while the Edge reports an unpaved surface | Surface comes from the Edge's map-based paved/unpaved splits. |
| Air density `ρ` | `ambientPressure` (barometer) + weather temperature and humidity | Without barometer data, uses the standard atmosphere at the current altitude. Without weather, keeps the last weather temperature/humidity (saved on the device, used if under 6 h old), else 15 °C / 50 %. The Edge's own temperature sensor cannot be read by a data field. |
| Wind | `Weather.getCurrentConditions()` (or the nearest hourly forecast) projected onto the GPS track | Reduced from the 10 m station height to rider height with a log wind profile. |

## Checking the original assumptions

| Assumption | Holds? | Details |
|---|---|---|
| Rider weight is available | ✅ Yes | `UserProfile.Profile.weight` (grams). Can be `null` if not set. |
| Rider height is available | ✅ Yes | `UserProfile.Profile.height` (cm). |
| Equipment / bike weight is available | ❌ No | The Edge stores bike weight in its bike profiles, but no Connect IQ API exposes it. The user enters it in a bike preset, which is matched to the ride type of the Edge profile. |
| Road surface is available | ⚠️ Indirectly | Connect IQ has no API to query map data or road type. Data fields do get `onTimerSplitStart/End` events (API 5.2.2, all supported Edges), and one split type is `SPLIT_TYPE_SURFACE_TYPE_UNPAVED`. Split types `SPLIT_TYPE_SURFACE_TYPE_PAVED` (42) and `SPLIT_TYPE_SURFACE_TYPE_UNPAVED` (34) alternate through the ride: test rides with gravel sections recorded several short unpaved splits matching the unpaved stretches; all-paved rides have one paved split. Detection is confirmed in recorded FIT files; the live Connect IQ callback is not yet tested on a device. |
| Ride profile (road / gravel / MTB ...) | ✅ Yes | `Activity.getProfileInfo()` (API 3.2) gives the profile name, sport and sub-sport, e.g. `SUB_SPORT_ROAD`, `SUB_SPORT_GRAVEL_CYCLING`, `SUB_SPORT_MOUNTAIN`, `SUB_SPORT_COMMUTING`, `SUB_SPORT_INDOOR_CYCLING`. Presets are matched by ride type (sub-sport), chosen from a list; profile names are not used. Cyclocross and e-bike profiles (`SPORT_E_BIKING`) are not supported. |
| Cadence | ✅ Yes | `currentCadence`, if a cadence sensor is paired. Only used to detect coasting; power is not calculated from cadence. |
| Speed | ✅ Yes | `currentSpeed`. |
| Road gradient | ⚠️ Partly | No grade field exists in `Activity.Info`, no map elevation lookup exists, and there is no grade complication. Map-based elevation is only exposed while following a course (`elevationAtNextPoint`, ClimbPro climb splits), which is too sparse for second-by-second gradient. It is computed from barometric altitude over the last 25 m, which adds a few seconds of lag and is the largest source of error (see below). |
| Weather / wind | ✅ Yes, with caveats | `Toybox.Weather` (API 3.2+) gives wind speed (m/s) and bearing, temperature and humidity. Data fields can use it; the open-source Windsock field does. The data comes from the phone, is only refreshed every 15–30 min, is a station or model value rather than local, and wind can be `null`. |
| Air pressure | ✅ Yes | `ambientPressure` from the barometer. Each supported model's spec sheet should be checked to confirm it has one. |
| Add power to the ride data | ⚠️ Partly | `FitContributor` writes the estimate to the FIT file. It appears in Garmin Connect as a separate Connect IQ chart plus lap and session averages. It is **not** treated as native power: Garmin deliberately blocks Connect IQ apps from overriding native fields. With the *Tag as power in FIT file* setting on, the field is marked as FIT native power (record field 7). Strava has been reported to use that as power when the file has no real power-meter data. |
| 3–5 s delay | ✅ Yes | 1 Hz updates, 3 s averaging, plus a few seconds of gradient lag on changing slopes. |

### Device support beyond the Edge range

The estimate does not use maps at all, since Connect IQ cannot read map data.
The things that matter are Connect IQ API 3.2+ (for `Toybox.Weather`), a
barometric altimeter, and GPS track and speed. Garmin lists `Toybox.Weather`
on many watches with maps (fēnix 6/7/8, epix, Enduro, several Forerunners) and
on the eTrex Touch. Watches with a barometer could run this code unchanged at
the **same** quality: the model would not need to change. Each model's
barometer and product id would need checking before it is added to
[manifest.xml](manifest.xml). They are deliberately left out for now, since
the Edge range comes first.

## Expected accuracy

Sensitivity for an 85.5 kg rider + bike on the hoods (CdA 0.348 m², all-round
road tyres, 15 °C), computed with the Python reference model kept in the
development workspace (outside this repo):

| Situation | Base estimate | Grade off by 1 % | Headwind off by 2 m/s | CdA off by 10 % | Crr off by 0.001 | Mass off by 2 kg |
|---|---|---|---|---|---|---|
| Flat, 25 km/h | 124 W | ±59 W | ±48 W | ±7 W | ±6 W | ±1 W |
| Flat, 35 km/h | 272 W | ±83 W | ±91 W | ±20 W | ±8 W | ±2 W |
| 7 % climb, 12 km/h | 232 W | ±28 W | ±13 W | ±1 W | ±3 W | ±5 W |

What this means in practice:

- **Steady climbs** are the most accurate case. Gravity dominates, and a sustained
  slope gives the gradient fit time to settle.
- **Flat and rolling roads** are dominated by gradient and wind error. Short-term
  (3 s) values will be noisy; lap and ride averages are much more reliable,
  because gradient errors cancel out over a ride that starts and ends at similar
  altitudes.
- **Drafting** in a group is not detected, so the estimate will be too high. This is accepted by design; drafting will not be modelled.
- **Crosswind** effects on drag are not modelled; only the headwind component is used.
- **Braking** cannot be detected; the estimate is clamped to 0 when negative.

## Settings

Edited in the Connect IQ / Garmin Connect app on the phone. Nothing needs to be
changed during a ride: the bike preset is picked automatically when the activity
starts, and the road surface switches automatically.

### Bike presets

One preset per Edge ride type, chosen from a list. A preset applies to every
Edge profile of that type; if several presets have the same type, the first is
used (two bikes of the same type cannot be told apart). The Edge's list of
profiles is not available to the phone settings, so names are not used. The
list starts empty; without a preset, built-in values for the ride type are used
(all-round tyres, 9 kg bike, 1.5 kg extra).

| Edge ride type | Supported | Built-in values without a preset |
|---|---|---|
| Road (and profiles with no specific type) | Yes | Road tyres, road position |
| Gravel | Yes | Gravel tyres, road position |
| Mountain | Yes | MTB tyres, upright position |
| Commuting | Yes | Road tyres, upright position, casual clothes |
| Indoor cycling | Yes: no gradient, wind or surface switching, 20 °C | Road tyres, road position |
| Cyclocross, e-bike, other activities | No: the field shows "--" and records nothing | — |

| Field | Choices | Meaning |
|---|---|---|
| Edge ride type | Road / Gravel / Mountain / Commuting / Indoor cycling | Matched to the ride type of the Edge profile. |
| Tyre type | Road / Gravel / MTB | Road and MTB, all-round class: 15 W / 30 W per tyre on the drum test (42.5 kg, 28.8 km/h), i.e. drum Crr 0.0045 / 0.0090, + 0.0033 for real roads = 0.0078 / 0.0123 at 20 °C. |
| Tyre width | 18–60 mm, in 1 mm steps | Adds drag area: 0.0010 m² per mm above 28 mm (45 mm: +0.017 m², about +4 W at 25 km/h). Default without a preset: 28 mm (road, commuting, indoor), 42 mm (gravel), 57 mm (mountain). |
| Tyre class (road and MTB tyres) | Fast / All-round / Durable | Fast = 20 % less drum rolling resistance, Durable = 35 % more. Not used for gravel tyres. |
| Tread (gravel tyres only) | Slick / File tread / Knobby | Replaces the class for gravel tyres: 13.3 / 16 / 20 W on the drum (Crr 0.0040 / 0.0048 / 0.0060). Default: file tread. |
| Riding position | Road / Time trial / Upright | Road = 70 % hoods + 30 % drops (factor 1.405); Time trial = 95 % aero bars + 5 % base bar (1.165); Upright = flat bar (1.75). Factor × the static time-trial CdA. The aero-bar factor is 1.15 because pedalling and field-measured time-trial CdA (0.25–0.29 m²) is higher than static wind-tunnel values. |
| Clothing | Cycling kit / Casual clothes | Casual clothes (and bags) × 1.17 CdA, from 557 measured urban riders (Tengattini & Bigazzi 2018). Default: casual for Commuting, cycling kit for the other ride types. |
| Bike weight kg | **Required**, 3–40 kg, no default | Entered by the rider. |
| Extra weight | 1 / 1.5 / 2 kg | Bottles, bags, shoes, helmet, clothing. |

CdA and rolling resistance are always derived from the rider and preset; there
are no overrides.

Real roads: the drum Crr is increased by **+0.0033**. Field measurements in
UCPRC-RR-2016-02 (Caltrans) found ordinary asphalt and chip seal +0.0026 to
+0.0058 above good dense asphalt (median about +0.0035, including bearing
friction; bearings are modelled separately, about 0.0002). An earlier version
multiplied by 1.8, but that ratio depends on a baseline the study assumed rather
than measured; the measured quantity is the difference. The tyre class scales
only the drum (casing) part.

Unpaved sections add **+0.0070** (road tyres), **+0.0043** (gravel tyres) or
**+0.0040** (MTB tyres). Gravel measured +0.0025 (fine) to +0.0061 (coarse)
above asphalt (Meyer et al. 2016); gravel tyres get the middle of that range.
Soft surfaces measured about +0.004 (Steyn &
Warnich 2014; Tengattini & Bigazzi 2018). Slick road tyres sink in and slip on
loose surfaces, so they get more, and gravel tyres end up ahead of road tyres
there. These values will be refined with club power-meter data.

Tyre temperature: rolling resistance rises in the cold. The tyre Crr is scaled by
1 + 0.5 × ((20 + 46.8)/(T + 46.8) − 1), from Rothhämel (2023) at half strength
because the paper's two fits differ by about 2×. T is the air temperature,
clamped to −20…40 °C: data fields cannot read the Edge's temperature sensor, so
it is the weather temperature, else the last stored weather temperature (under
6 h old), else 15 °C; indoors 20 °C. Example: ×1.07 at 5 °C, ×0.97 at 30 °C.
The factor is recalculated only when the temperature changes. The unpaved
addition is not scaled.

The tyre watts are placeholders until averaged test data is available.

### Rider and recording

| Setting | Default | Meaning |
|---|---|---|
| Rider weight kg | 0 (use profile) | Overrides the Garmin profile weight. |
| Rider height cm | 0 (use profile) | Overrides the Garmin profile height. |
| Tag as power in FIT file | On | Marks the recorded field as FIT native power. Takes effect from the next activity. |

Fixed, not settings: wind exposure "mixed" (×0.54 of the reported 10 m wind) and
a 3 s averaging window (to be decided from test results).

## Project layout

```
manifest.xml                  Data field, API 3.2.0+, Edge product list, permissions
monkey.jungle
source/
  EstimatedPowerApp.mc        App entry; reloads settings when they change
  EstimatedPowerField.mc      SimpleDataField: inputs, weather, smoothing, FIT recording
  PowerModel.mc               Pure physics (no device state)
  GradeEstimator.mc           Distance-window regression of altitude for gradient
resources/
  strings/strings.xml
  settings/properties.xml     Setting defaults
  settings/settings.xml       Phone settings UI
  fitcontributions/           How Garmin Connect shows the recorded fields
  drawables/                  Launcher icon (placeholder)
```

## Building

This folder holds the add-on itself. The tooling used to build and
test it (Docker setup for the SDK Manager and simulator, a Python reference model
with unit tests) is in the `development/` folder next to this one.

With that in place:

```sh
../development/devenv/ciq.sh compile edge840   # build the add-on
../development/devenv/ciq.sh simulator &       # start the simulator
../development/devenv/ciq.sh run edge840       # load the add-on into it
```

Replace the placeholder application id in `manifest.xml` before publishing.

## Open items

- **Supported models:** Edge 540, 550, 840, 850, 1040 and 1050 only. Older Edges
  (530, 830, 1030 family, Explore 2, MTB) and the Edge 1060 are deliberately left out.
- **One field only.** The field shows the 3 s estimate in every slot size. Separate
  lap/ride-average fields would need companion apps, which cannot share settings
  or data with this add-on, so riders would have to set everything up twice; not
  planned. Lap and ride averages are recorded in the FIT file and shown in Garmin
  Connect. The Edge's built-in power fields only accept a paired power meter.
- **Live surface switching untested on a device.** The paved/unpaved splits are
  confirmed in recorded FIT files; `onTimerSplitStart/End` firing live is not yet
  confirmed.
- **Presets start empty.** Connect IQ requires default presets to include every
  field, so shipping defaults would mean a default bike weight. Until the rider
  creates a preset, built-in values are used. The code accepts preset values as
  numbers or text, in case Garmin Connect stores them as text (untested).
- **Launcher icon** is 40×40; the Edge 840 expects 35×35, and the compiler scales it.
  Per-device icon sizes still need checking.
- **Wind bearing convention not confirmed.** Garmin documents `windBearing` only as
  "North = 0, East = 90". The code assumes it is the direction the wind comes
  *from*, which is the usual meteorological convention. The open-source Windsock
  field appears to assume the opposite. Check this on a device against a known
  weather report, and if needed set `WIND_BEARING_OFFSET_DEG = 180.0` in
  `EstimatedPowerField.mc`.
- **Validation:** compare against rides recorded with a real power meter, using
  the Python reference model on the FIT data, then tune the Crr table, the position
  factors and the gradient window.
- Possible improvement: when a power meter *is* present, fit the rider's CdA and Crr
  automatically and save them for rides without it.

## Sources

Full reasoning and analysis: [docs/METHODOLOGY.md](docs/METHODOLOGY.md).
The wider literature research is listed under [Research bibliography](#research-bibliography).

**Physics model**
- Martin JC, Milliken DL, Cobb JE, McFadden KL, Coggan AR. *Validation of a mathematical model
  for road cycling power.* J Appl Biomech 1998;14:276–291
  ([PDF](https://collections.lib.utah.edu/dl_files/b4/8e/b48ef26086091662c561e673d7bd990d77868437.pdf)).
  Model structure, wheel bearings, wheel inertia, wheel rotation drag (0.0044 m²), drivetrain efficiency.
- Bassett DR, Kyle CR, Passfield L, Broker JP, Burke ER. *Comparing cycling world hour records,
  1967–1996: modeling with empirical data.* Med Sci Sports Exerc 1999;31:1665–1676. Frontal area
  from height and mass.
- Faria EW, Parker DL, Faria IE. *The science of cycling.* Sports Med 2005
  ([part 1](https://www.researchgate.net/publication/7906170_The_science_of_cycling_physiology_and_training_-_part_1)).
  Restates the Bassett equation.
- Coggan A. [Estimation of CdA from anthropometric data](http://www.trainingandracingwithapowermeter.com/2011/04/estimation-of-cda-from-anthropometric.html).
  Cd ≈ 0.707 from wind-tunnel data.
- Heil DP. [Body mass scaling of projected frontal area in competitive cyclists](https://www.researchgate.net/publication/11788060_Body_mass_scaling_of_projected_frontal_area_in_competitive_cyclists).
  Eur J Appl Physiol 2001. Used in the model comparison.
- [Translating uphill cycling into a head-wind and vice versa](https://www.jsc-journal.com/index.php/JSC/article/download/296/391),
  Journal of Science and Cycling. Range of wheel rotation drag values.
- Standard formulas: Tetens equation (vapour pressure), International Standard Atmosphere,
  logarithmic wind profile.

**Rolling resistance and road surfaces**
- UC Pavement Research Center, [UCPRC-RR-2016-02](https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/f0016607-ca17-2693-finalreport.pdf)
  (Caltrans). Field-measured bicycle rolling resistance on real roads; source of the +0.0033 real-road addition (see Settings).
- UC Pavement Research Center, [Surface treatment macrotexture and bicycle ride quality](https://escholarship.org/content/qt3dp663w0/qt3dp663w0.pdf).
- Silca, [Part 4B: Rolling resistance and impedance](https://silca.cc/blogs/silca/part-4b-rolling-resistance-and-impedance).

**Tyre width and aerodynamics**
- Swiss Side, [Aerodynamics in gravel](https://www.swissside.com/en-us/blogs/aero-tech-tips/gravel-report).
  About 0.010 m² extra drag area per 10 mm of tyre width; source of the gravel/MTB drag increments.
- Cyclingnews, [40mm road tyres lab test](https://www.cyclingnews.com/features/lab-tested-40mm-road-tyres-are-faster-for-nearly-everyone-and-heres-why/);
  Silca, [Part 5: Tire pressure and aerodynamics](https://silca.cc/blogs/silca/part-5-tire-pressure-and-aerodynamics);
  CyclingAbout, [aero gravel bikes wind-tunnel tests](https://www.cyclingabout.com/fastest-aero-gravel-bikes-wind-tunnel-tests/).
- NCAT [Report 14-07](https://eng.auburn.edu/research/centers/ncat/files/reports/2014/rep14-07.pdf) and
  [Report 20-04](https://eng.auburn.edu/research/centers/ncat/files/technical-reports/rep20-04.pdf);
  [Coatings 2021;11(5):538](https://doi.org/10.3390/coatings11050538). Rolling resistance vs pavement texture.
- Bicycle Rolling Resistance, [test method](https://www.bicyclerollingresistance.com/the-test).
  Drum protocol (42.5 kg, 28.8 km/h) used to express tyre values. No test data from this site is used.

**Platform comparisons (analysis only, no values adopted)**
- Strava power calculation description, [as quoted](https://www.roadbikereview.com/threads/whats-up-with-strava-watts.367269/);
  [forum discussion of its assumptions](https://www.bikeforums.net/general-cycling-discussion/1316048-strava-power-estimates.html);
  [Strava calorie calculation](https://support.strava.com/en-us/articles/15402159-how-does-strava-calculate-calories).
- ZwiftInsider, [Crr of various wheels](https://zwiftinsider.com/crr/) and
  [rider weight and speed](https://zwiftinsider.com/rider-weight-speed/);
  G. Hilton, [Zwift bike selector](https://greghilton.co.uk/php/zwift-bike-selector.html).

**Garmin Connect IQ**
- API documentation (SDK 9.3.0): [Activity.Info](https://developer.garmin.com/connect-iq/api-docs/Toybox/Activity/Info.html),
  [Activity.ProfileInfo](https://developer.garmin.com/connect-iq/api-docs/Toybox/Activity/ProfileInfo.html),
  [Activity.SplitInfo](https://developer.garmin.com/connect-iq/api-docs/Toybox/Activity/SplitInfo.html),
  [WatchUi.DataField](https://developer.garmin.com/connect-iq/api-docs/Toybox/WatchUi/DataField.html),
  [UserProfile.Profile](https://developer.garmin.com/connect-iq/api-docs/Toybox/UserProfile/Profile.html),
  [Weather](https://developer.garmin.com/connect-iq/api-docs/Toybox/Weather.html),
  [Weather.CurrentConditions](https://developer.garmin.com/connect-iq/api-docs/Toybox/Weather/CurrentConditions.html),
  [Weather.HourlyForecast](https://developer.garmin.com/connect-iq/api-docs/Toybox/Weather/HourlyForecast.html),
  [FitContributor](https://developer.garmin.com/connect-iq/api-docs/Toybox/FitContributor.html),
  [Session.createField (`:nativeNum`)](https://developer.garmin.com/connect-iq/api-docs/Toybox/ActivityRecording/Session.html),
  [Sensor](https://developer.garmin.com/connect-iq/api-docs/Toybox/Sensor.html),
  [SensorHistory](https://developer.garmin.com/connect-iq/api-docs/Toybox/SensorHistory.html),
  [Complications](https://developer.garmin.com/connect-iq/api-docs/Toybox/Complications.html),
  [Properties and app settings](https://developer.garmin.com/connect-iq/core-topics/properties-and-app-settings/).
- Garmin Connect ignoring `:nativeNum`: [bug report](https://forums.garmin.com/developer/connect-iq/i/bug-reports/nativenum-field-is-ignored-by-garmin-connect-so-accessories-can-t-be-integrated-properly),
  [feature request](https://forums.garmin.com/developer/connect-iq/i/bug-reports/please-allow-nativenum-fit-fields-to-override-native-fields-in-garmin-connect),
  [third-party services and nativeNum power](https://forums.garmin.com/developer/connect-iq/f/discussion/4854/fitcontributor-nativenum-functionality/1758405).
- Weather in data fields: [uaraven/windsock](https://github.com/uaraven/windsock),
  [forum thread](https://forums.garmin.com/developer/connect-iq/f/discussion/237382/weather-for-datafield),
  [wind direction thread](https://forums.garmin.com/developer/connect-iq/f/discussion/238145/wind-direction-indicator).

## Research bibliography

The physics behind the estimate (rolling resistance, aerodynamic drag, road
surfaces and the power model) was checked against the literature below. Entries
marked *(partly read)* or *(abstract or second-hand only)* were not available in
full, so their numbers are used only as cited by other work; all other entries
were read in full. DOIs and bibliographic details were checked against Crossref
where a DOI exists.

**Power model and cycling dynamics**

- Atkinson G, Peacock O, Passfield L (2007). *Variable versus constant power strategies during cycling time-trials: Prediction of time savings using an up-to-date mathematical model.* Journal of Sports Sciences 25(9):1001–1009. [doi:10.1080/02640410600944709](https://doi.org/10.1080/02640410600944709) *(abstract or second-hand only)*
- Bassett DR Jr, Kyle CR, Passfield L, Broker JP, Burke ER (1999). *Comparing cycling world hour records, 1967–1996: modeling with empirical data.* Medicine & Science in Sports & Exercise 31(11):1665–1676. [doi:10.1097/00005768-199911000-00025](https://doi.org/10.1097/00005768-199911000-00025)
- Cohen C, Brunet E, Roy J, Clanet C (2021). *Physics of road cycling and the three jerseys problem.* Journal of Fluid Mechanics 914:A38. [doi:10.1017/jfm.2020.1022](https://doi.org/10.1017/jfm.2020.1022)
- Dahmen T, Byshko R, Saupe D, Röder M, Mantler S (2011). *Validation of a model and a simulator for road cycling on real tracks.* Sports Engineering 14(2-4):95–110. [doi:10.1007/s12283-011-0076-1](https://doi.org/10.1007/s12283-011-0076-1)
- Dahmen T, Wolf S, Saupe D (2012). *Applications of Mathematical Models of Road Cycling.* IFAC Proceedings Volumes 45(2):804–809. [doi:10.3182/20120215-3-at-3016.00142](https://doi.org/10.3182/20120215-3-at-3016.00142)
- Dahn K, Mai L, Poland J, Jenkins C (1991). *Frictional resistance in bicycle wheel bearings.* Cycling Science 3(3):28–32. *(abstract or second-hand only)*
- Danek T, Slawinski MA, Stanoev T (2020). *On modelling bicycle power-meter measurements: Part I. Estimating effects of air, rolling and drivetrain resistance.* arXiv:2005.04229. [arxiv.org/abs/2005.04229](https://arxiv.org/abs/2005.04229)
- Danek T, Slawinski MA, Stanoev T (2020). *On modelling bicycle power-meter measurements: Part II. Relations between rates of change of model quantities.* arXiv:2005.04480. [arxiv.org/abs/2005.04480](https://arxiv.org/abs/2005.04480)
- di Prampero PE, Cortili G, Mognoni P, Saibene F (1979). *Equation of motion of a cyclist.* Journal of Applied Physiology 47(1):201–206. [doi:10.1152/jappl.1979.47.1.201](https://doi.org/10.1152/jappl.1979.47.1.201) *(abstract or second-hand only)*
- Faria EW, Parker DL, Faria IE (2005). *The Science of Cycling: Factors Affecting Performance – Part 2.* Sports Medicine 35(4):313–337. [doi:10.2165/00007256-200535040-00003](https://doi.org/10.2165/00007256-200535040-00003)
- Groeskamp S (2017). *Translating Uphill Cycling into a Head-Wind and Vice Versa.* Journal of Science and Cycling 6(1). [doi:10.28985/171231.jsc.06](https://doi.org/10.28985/171231.jsc.06)
- Jeukendrup AE, Martin J (2001). *Improving Cycling Performance: How Should We Spend Our Time and Money.* Sports Medicine 31(7):559–569. [doi:10.2165/00007256-200131070-00009](https://doi.org/10.2165/00007256-200131070-00009) *(abstract or second-hand only)*
- Kyle CR (1988). *The mechanics and aerodynamics of cycling.* In: Burke ER, Newsom MM (eds), Medical and Scientific Aspects of Cycling, pp. 235–252. *(abstract or second-hand only)*
- Kyle CR, Berto F (2001). *The mechanical efficiency of bicycle derailleur and hub-gear transmissions.* Human Power 52:3–11.
- Martin JC, Milliken DL, Cobb JE, McFadden KL, Coggan AR (1998). *Validation of a Mathematical Model for Road Cycling Power.* Journal of Applied Biomechanics 14(3):276–291. [doi:10.1123/jab.14.3.276](https://doi.org/10.1123/jab.14.3.276)
- Olds TS, Norton KI, Craig NP (1993). *Mathematical model of cycling performance.* Journal of Applied Physiology 75(2):730–737. [doi:10.1152/jappl.1993.75.2.730](https://doi.org/10.1152/jappl.1993.75.2.730) *(abstract or second-hand only)*
- Olds TS, Norton KI, Lowe EL, Olive S, Reay F, Ly S (1995). *Modeling road-cycling performance.* Journal of Applied Physiology 78(4):1596–1611. [doi:10.1152/jappl.1995.78.4.1596](https://doi.org/10.1152/jappl.1995.78.4.1596) *(abstract or second-hand only)*
- Rohloff B, Greb P (2003). Rebuttal of Kyle & Berto (2001), with a reply by C.R. Kyle. Human Power 55:11–15.
- Sitko S, López-Laval I, Cirer-Sastre R, Barrajón-Pérez C, Legaz-Arrese A (2026). *From speed to watts: a physics-based model for estimating power output during professional cycling climbs.* The Journal of Sports Medicine and Physical Fitness 66(9):1032–1038. [doi:10.23736/s0022-4707.26.18115-8](https://doi.org/10.23736/s0022-4707.26.18115-8) *(abstract or second-hand only)*
- Slawinski MA, Slawinski RA, Stanoev T (2020). *On modelling bicycle power for velodromes: Part I: Formulation for individual pursuits.* arXiv:2005.04691. [arxiv.org/abs/2005.04691](https://arxiv.org/abs/2005.04691)
- Spicer JB, Richardson CJK, Ehrlich MJ, Bernstein JR, Fukuda M, Terada M (2001). *Effects of Frictional Loss on Bicycle Chain Drive Efficiency.* Journal of Mechanical Design 123(4):598–605. [doi:10.1115/1.1412848](https://doi.org/10.1115/1.1412848) *(abstract or second-hand only)*

**Rolling resistance**

- Baldissera P, Delprete C (2017). *Rolling resistance, vertical load and optimal number of wheels in human-powered vehicle design.* Proceedings of the Institution of Mechanical Engineers, Part P: Journal of Sports Engineering and Technology 231(1):33–42. [doi:10.1177/1754337115625002](https://doi.org/10.1177/1754337115625002) *(abstract or second-hand only)*
- Baldissera P, Delprete C, Rossi M, Zahar A (2021). *Experimental Comparison of Speed-Dependent Rolling Coefficients in Small Cycling Tires.* Tire Science And Technology 49(3):224–241. [doi:10.2346/tire.20.190207](https://doi.org/10.2346/tire.20.190207) *(abstract or second-hand only)*
- Buder J, Fouchard E, Schwanitz S (2025). *The impact of tyre width, pressure and surface condition on rolling resistance and vibration transmission of bicycle tyres.* Journal of Science and Cycling 14(2), conference abstract.
- Buder J, Schwanitz S, Odenwald S (2024). *Benchmarking rolling resistance of bicycle tyres on a laboratory treadmill.* Engineering of Sport 15 (ISEA 2024), Loughborough University. *(abstract or second-hand only)*
- Candau RB, Grappe F, Ménard M, Barbier B, Millet GY, Hoffman MD, et al. (1999). *Simplified deceleration method for assessment of resistive forces in cycling.* Medicine & Science in Sports & Exercise 31(10):1441–1447. [doi:10.1097/00005768-199910000-00013](https://doi.org/10.1097/00005768-199910000-00013) *(abstract or second-hand only)*
- Dell’Orto G, Ballo FM, Mastinu G, Gobbi M, Magnani G (2023). *Racing bicycle tyres – Influence on mechanical characteristics of internal pressure, vertical force, speed and temperature.* European Journal of Mechanics - A/Solids 100:105010. [doi:10.1016/j.euromechsol.2023.105010](https://doi.org/10.1016/j.euromechsol.2023.105010) *(abstract or second-hand only)*
- Ejsmont J, Ronowski G, Ydrefors L, Owczarzak W, Sommer S, Świeczko-Żurek B (2024). *Comparison of Tire Rolling Resistance Measuring Methods for Different Surfaces.* International Journal of Automotive Technology 25(4):965–976. [doi:10.1007/s12239-024-00092-w](https://doi.org/10.1007/s12239-024-00092-w)
- Ejsmont J, Sommer S (2021). *Selected Aspects of Pavement Texture Influence on Tire Rolling Resistance.* Coatings 11(7):776. [doi:10.3390/coatings11070776](https://doi.org/10.3390/coatings11070776)
- Ejsmont JA, Ronowski G, Świeczko-Żurek B, Sommer S (2017). *Road texture influence on tyre rolling resistance.* Road Materials and Pavement Design 18(1):181–198. [doi:10.1080/14680629.2016.1160835](https://doi.org/10.1080/14680629.2016.1160835) *(abstract or second-hand only)*
- Fenre MD, Klein-Paste A (2021). *Bicycle rolling resistance under winter conditions.* Cold Regions Science and Technology 187:103282. [doi:10.1016/j.coldregions.2021.103282](https://doi.org/10.1016/j.coldregions.2021.103282)
- Fenre MD, Klein-Paste A (2021). *Rolling Resistance Measurements on Cycleways Using an Instrumented Bicycle.* Journal of Cold Regions Engineering 35(2):04021001. [doi:10.1061/(asce)cr.1943-5495.0000244](https://doi.org/10.1061/(asce)cr.1943-5495.0000244)
- Grappe F, Candau R, Barbier B, Hoffman MD, Belli A, Rouillon J (1999). *Influence of tyre pressure and vertical load on coefficient of rolling resistance and simulated cycling performance.* Ergonomics 42(10):1361–1371. [doi:10.1080/001401399185009](https://doi.org/10.1080/001401399185009)
- Henchoz Y, Crivelli G, Borrani F, Millet GP (2010). *A new method to measure rolling resistance in treadmill cycling.* Journal of Sports Sciences 28(10):1043–1046. [doi:10.1080/02640414.2010.498483](https://doi.org/10.1080/02640414.2010.498483) *(abstract or second-hand only)*
- Hyttinen J, Rothhämel M, Jerrelind J, Drugge L (2024). *Simulation of transient rolling resistance of bicycle tyres at various ambient temperatures.* PLOS ONE 19(6):e0302821. [doi:10.1371/journal.pone.0302821](https://doi.org/10.1371/journal.pone.0302821)
- Lim AC, Homestead EP, Edwards AG, Carver TC, Kram R, Byrnes WC (2011). *Measuring Changes in Aerodynamic/Rolling Resistances by Cycle-Mounted Power Meters.* Medicine & Science in Sports & Exercise 43(5):853–860. [doi:10.1249/mss.0b013e3181fcb140](https://doi.org/10.1249/mss.0b013e3181fcb140) *(abstract or second-hand only)*
- Mastinu G, Gobbi M, Matrascia G (2019). *Bicycle tyres – rolling resistance.* Bicycle and Motorcycle Dynamics 2019 symposium, University of Padova (extended abstract).
- Nilges P (2004). *Auswirkung unterschiedlicher Mountainbikereifen auf die Rollwiderstandsleistung im Gelände* (effect of different mountain-bike tyres on rolling resistance off road). Thesis, German Sport University Cologne (print only). *(abstract or second-hand only)*
- Reiser R, Watt J, Peterson M (2003). *Cycling on rollers: influence of tyre pressure and cross section on power requirements.* Sports Biomechanics 2(2):237–249. [doi:10.1080/14763140308522821](https://doi.org/10.1080/14763140308522821) *(abstract or second-hand only)*
- Rothhämel M (2023). *On rolling resistance of bicycle tyres with ambient temperature in focus.* International Journal of Vehicle Systems Modelling and Testing 17(1):67–80. [doi:10.1504/ijvsmt.2023.132317](https://doi.org/10.1504/ijvsmt.2023.132317)
- Sellier M, Bellenoue S (2025). *A novel energy imbalance approach applied to rolling resistance assessment in cycling.* Journal of Science and Cycling 14(2), conference abstract.
- Tengattini S, Bigazzi A (2018). *Validation of an Outdoor Coast-Down Test to Measure Bicycle Resistance Parameters.* Journal of Transportation Engineering, Part A: Systems 144(7):04018031. [doi:10.1061/jtepbs.0000152](https://doi.org/10.1061/jtepbs.0000152)
- Tengattini S, Bigazzi AY (2018). *Physical characteristics and resistance parameters of typical urban cyclists.* Journal of Sports Sciences 36(20):2383–2391. [doi:10.1080/02640414.2018.1458587](https://doi.org/10.1080/02640414.2018.1458587)

**Road surface, roughness and vibration**

- Bertucci WM, Rogier S, Reiser RF (2013). *Evaluation of aerodynamic and rolling resistances in mountain-bike field conditions.* Journal of Sports Sciences 31(14):1606–1613. [doi:10.1080/02640414.2013.792945](https://doi.org/10.1080/02640414.2013.792945) *(abstract or second-hand only)*
- Bíl M, Andrášik R, Kubeček J (2015). *How comfortable are your cycling tracks? A new method for objective bicycle vibration measurement.* Transportation Research Part C: Emerging Technologies 56:415–425. [doi:10.1016/j.trc.2015.05.007](https://doi.org/10.1016/j.trc.2015.05.007) *(abstract or second-hand only)*
- Crenna F, Belotti V, Colò A, Morettini S, Tenerini L (2025). *A Measurement System to Characterize the Effects of Tires on Bicycle Vibrations.* Eng 6(9):245. [doi:10.3390/eng6090245](https://doi.org/10.3390/eng6090245)
- Gao J, Sha A, Huang Y, Hu L, Tong Z, Jiang W (2018). *Evaluating the cycling comfort on urban roads based on cyclists' perception of vibration.* Journal of Cleaner Production 192:531–541. [doi:10.1016/j.jclepro.2018.04.275](https://doi.org/10.1016/j.jclepro.2018.04.275)
- Gao J, Sha A, Huang Y, Liu Z, Hu L, Jiang W, et al. (2019). *Cycling comfort on asphalt pavement: Influence of the pavement-tyre interface on vibration.* Journal of Cleaner Production 223:323–341. [doi:10.1016/j.jclepro.2019.03.153](https://doi.org/10.1016/j.jclepro.2019.03.153) *(abstract or second-hand only)*
- Gee-Clough D (1978). *The effect of wheel width on the rolling resistance of rigid wheels in sand.* Journal of Terramechanics 15(4):161–184. [doi:10.1016/0022-4898(78)90002-2](https://doi.org/10.1016/0022-4898(78)90002-2) *(abstract or second-hand only)*
- Lépine J, Champoux Y, Drouet J (2014). *Road bike comfort: on the measurement of vibrations induced to cyclist.* Sports Engineering 17(2):113–122. [doi:10.1007/s12283-013-0145-8](https://doi.org/10.1007/s12283-013-0145-8)
- Lépine J, Champoux Y, Drouet J (2015). *The relative contribution of road bicycle components on vibration induced to the cyclist.* Sports Engineering 18(2):79–91. [doi:10.1007/s12283-014-0168-9](https://doi.org/10.1007/s12283-014-0168-9)
- Li H, Buscheck J, Harvey J, Fitch D, Reger D, Wu R, et al. (2017). *Development of recommended guidelines for preservation treatments for bicycle routes.* UC Pavement Research Center report UCPRC-RR-2016-02 (Caltrans CA17-2693). [PDF](https://dot.ca.gov/-/media/dot-media/programs/research-innovation-system-information/documents/f0016607-ca17-2693-finalreport.pdf) *(partly read)*
- Li H, Harvey JT, Thigpen C, Wu R. *Surface treatment macrotexture and bicycle ride quality.* UC Pavement Research Center report UCPRC-RR-2013-07. [PDF](https://escholarship.org/content/qt3dp663w0/qt3dp663w0.pdf) *(partly read)*
- Macdermid PW, Fink PW, Stannard SR (2015). *The influence of tyre characteristics on measures of rolling performance during cross-country mountain biking.* Journal of Sports Sciences 33(3):277–285. [doi:10.1080/02640414.2014.942682](https://doi.org/10.1080/02640414.2014.942682) *(abstract or second-hand only)*
- Macdermid PW, Miller MC, Macdermid FM, Fink PW (2015). *Tyre Volume and Pressure Effects on Impact Attenuation during Mountain Bike Riding.* Shock and Vibration 2015:191075. [doi:10.1155/2015/191075](https://doi.org/10.1155/2015/191075)
- Meyer D, Kloss G, Senner V (2016). *What is Slowing Me Down? Estimation of Rolling Resistances During Cycling.* Procedia Engineering 147:526–531. [doi:10.1016/j.proeng.2016.06.232](https://doi.org/10.1016/j.proeng.2016.06.232)
- Nielens H, Lejeune T (2004). *Bicycle Shock Absorption Systems and Energy Expended by the Cyclist.* Sports Medicine 34(2):71–80. [doi:10.2165/00007256-200434020-00001](https://doi.org/10.2165/00007256-200434020-00001) *(abstract or second-hand only)*
- Nielens H, Lejeune TM (2001). *Energy Cost of Riding Bicycles with Shock Absorption Systems on a Flat Surface.* International Journal of Sports Medicine 22(6):400–404. [doi:10.1055/s-2001-16242](https://doi.org/10.1055/s-2001-16242) *(abstract or second-hand only)*
- Pelland-Leblanc J, Lépine J, Champoux Y, Drouet J (2014). *Using Power as a Metric to Quantify Vibration Transmitted to the Cyclist.* Procedia Engineering 72:392–397. [doi:10.1016/j.proeng.2014.06.067](https://doi.org/10.1016/j.proeng.2014.06.067)
- Steyn WJvdM, Warnich J (2014). *Comparison of tyre rolling resistance for different mountain bike tyre diameters and surface conditions.* South African Journal for Research in Sport, Physical Education and Recreation 36(2):179–193.
- Toljic M, Brezina T, Emberger G (2021). *Influence of surface roughness on cyclists’ velocity choices.* Proceedings of the Institution of Civil Engineers - Municipal Engineer 174(1):2–13. [doi:10.1680/jmuen.18.00058](https://doi.org/10.1680/jmuen.18.00058) *(abstract or second-hand only)*
- Tomiyama K, Takahasi K, Tachibana K, Akeda T, Hagiwara T (2024). *A Concept of Surface Roughness Index for Cycle Path: Bicycle Ride Index (BRI).* In: Lecture Notes in Civil Engineering (Springer), pp. 67–76. [doi:10.1007/978-3-031-63584-7_8](https://doi.org/10.1007/978-3-031-63584-7_8) *(abstract or second-hand only)*
- Turner MM (2024). *Cycling on rough roads: a model for resistance and vibration.* Vehicle System Dynamics 62(10):2729–2749. [doi:10.1080/00423114.2024.2304031](https://doi.org/10.1080/00423114.2024.2304031)
- Vanwalleghem J, De Baere I, Loccufier M, Van Paepegem W (2013). *Sensor design for outdoor racing bicycle field testing for human vibration comfort evaluation.* Measurement Science and Technology 24(9):095002. [doi:10.1088/0957-0233/24/9/095002](https://doi.org/10.1088/0957-0233/24/9/095002) *(abstract or second-hand only)*
- Vázquez Fernández E, Dell'Orto G, Moore JK (2026). *Vibration-Induced Power Loss in Cycling: Experimental Quantification on a Simulated Cobblestone Surface.* Research Square preprint, not peer reviewed. [doi:10.21203/rs.3.rs-10390782/v1](https://doi.org/10.21203/rs.3.rs-10390782/v1)
- Viellehner J, Potthast W (2021). *The Effect of Cycling-specific Vibration on Neuromuscular Performance.* Medicine & Science in Sports & Exercise 53(5):936–944. [doi:10.1249/mss.0000000000002565](https://doi.org/10.1249/mss.0000000000002565) *(abstract or second-hand only)*

**Aerodynamic drag: frontal area, riding position, wind and drafting**

- Barelle C, Chabroux V, Favier D (2010). *Modeling of the time trial cyclist projected frontal area incorporating anthropometric, postural and helmet characteristics.* Sports Engineering 12(4):199–206. [doi:10.1007/s12283-010-0047-y](https://doi.org/10.1007/s12283-010-0047-y) *(abstract or second-hand only)*
- Barry N, Burton D, Sheridan J, Thompson M, Brown NA (2015). *Aerodynamic performance and riding posture in road cycling and triathlon.* Proceedings of the Institution of Mechanical Engineers, Part P: Journal of Sports Engineering and Technology 229(1):28–38. [doi:10.1177/1754337114549876](https://doi.org/10.1177/1754337114549876) *(abstract or second-hand only)*
- Blocken B, Defraeye T, Koninckx E, Carmeliet J, Hespel P (2013). *CFD simulations of the aerodynamic drag of two drafting cyclists.* Computers & Fluids 71:435–445. [doi:10.1016/j.compfluid.2012.11.012](https://doi.org/10.1016/j.compfluid.2012.11.012)
- Blocken B, van Druenen T, Toparlar Y, Malizia F, Mannion P, Andrianne T, et al. (2018). *Aerodynamic drag in cycling pelotons: New insights by CFD simulation and wind tunnel testing.* Journal of Wind Engineering and Industrial Aerodynamics 179:319–337. [doi:10.1016/j.jweia.2018.06.011](https://doi.org/10.1016/j.jweia.2018.06.011) *(abstract or second-hand only)*
- Brownlie L, Kyle C, Carbo J, Demarest N, Harber E, MacDonald R, et al. (2009). *Streamlining the time trial apparel of cyclists: The Nike swift spin project.* Sports Technology 2(1-2):53–60. [doi:10.1080/19346182.2009.9648499](https://doi.org/10.1080/19346182.2009.9648499) *(abstract or second-hand only)*
- Capelli C, Rosa G, Butti F, Ferretti G, Veicsteinas A, di Prampero PE (1993). *Energy cost and efficiency of riding aerodynamic bicycles.* European Journal of Applied Physiology and Occupational Physiology 67(2):144–149. [doi:10.1007/bf00376658](https://doi.org/10.1007/bf00376658) *(abstract or second-hand only)*
- Crouch TN, Burton D, LaBry ZA, Blair KB (2017). *Riding against the wind: a review of competition cycling aerodynamics.* Sports Engineering 20(2):81–110. [doi:10.1007/s12283-017-0234-1](https://doi.org/10.1007/s12283-017-0234-1)
- Debraux P, Bertucci W, Manolova A, Rogier S, Lodini A (2009). *New Method to Estimate the Cycling Frontal Area.* International Journal of Sports Medicine 30(04):266–272. [doi:10.1055/s-0028-1105940](https://doi.org/10.1055/s-0028-1105940) *(abstract or second-hand only)*
- Debraux P, Grappe F, Manolova AV, Bertucci W (2011). *Aerodynamic drag in cycling: methods of assessment.* Sports Biomechanics 10(3):197–218. [doi:10.1080/14763141.2011.592209](https://doi.org/10.1080/14763141.2011.592209) *(abstract or second-hand only)*
- Defraeye T, Blocken B, Koninckx E, Hespel P, Carmeliet J (2010). *Aerodynamic study of different cyclist positions: CFD analysis and full-scale wind-tunnel tests.* Journal of Biomechanics 43(7):1262–1268. [doi:10.1016/j.jbiomech.2010.01.025](https://doi.org/10.1016/j.jbiomech.2010.01.025)
- Fintelman DM, Hemida H, Sterling M, Li F (2015). *CFD simulations of the flow around a cyclist subjected to crosswinds.* Journal of Wind Engineering and Industrial Aerodynamics 144:31–41. [doi:10.1016/j.jweia.2015.05.009](https://doi.org/10.1016/j.jweia.2015.05.009)
- Fintelman DM, Sterling M, Hemida H, Li F (2014). *The Effect of Crosswinds on Cyclists: An Experimental Study.* Procedia Engineering 72:720–725. [doi:10.1016/j.proeng.2014.06.122](https://doi.org/10.1016/j.proeng.2014.06.122)
- García-López J, Rodríguez-Marroyo JA, Juneau C, Peleteiro J, Martínez AC, Villa JG (2008). *Reference values and improvement of aerodynamic drag in professional cyclists.* Journal of Sports Sciences 26(3):277–286. [doi:10.1080/02640410701501697](https://doi.org/10.1080/02640410701501697)
- Garimella R, Peeters T, Parrilla E, Uriel J, Sels S, Huysmans T, et al. (2020). *Estimating Cycling Aerodynamic Performance Using Anthropometric Measures.* Applied Sciences 10(23):8635. [doi:10.3390/app10238635](https://doi.org/10.3390/app10238635)
- Grappe F, Candau R, Belli A, Rouillon JD (1997). *Aerodynamic drag in field cycling with special reference to the Obree's position.* Ergonomics 40(12):1299–1311. [doi:10.1080/001401397187388](https://doi.org/10.1080/001401397187388) *(abstract or second-hand only)*
- Greenwell DI, Wood NJ, Bridge EKL, Addy RJ (1995). *Aerodynamic characteristics of low-drag bicycle wheels.* The Aeronautical Journal 99(983):109–120. [doi:10.1017/s0001924000028281](https://doi.org/10.1017/s0001924000028281) *(abstract or second-hand only)*
- Heil D (2002). *Body mass scaling of frontal area in competitive cyclists not using aero-handlebars.* European Journal of Applied Physiology 87(6):520–528. [doi:10.1007/s00421-002-0662-9](https://doi.org/10.1007/s00421-002-0662-9) *(abstract or second-hand only)*
- Heil DP (2001). *Body mass scaling of projected frontal area in competitive cyclists.* European Journal of Applied Physiology 85(3-4):358–366. [doi:10.1007/s004210100424](https://doi.org/10.1007/s004210100424) *(abstract or second-hand only)*
- Hopker JG, Barnes C, Fennell CRJ, Gibson S (2025). *Validity and Reliability of an On‐Bike Sensor System for the Determination of Aerodynamic Drag in Cycling.* European Journal of Sport Science 25(12):e70098. [doi:10.1002/ejsc.70098](https://doi.org/10.1002/ejsc.70098)
- Lukes RA, Chin SB, Haake SJ (2005). *The understanding and development of cycling aerodynamics.* Sports Engineering 8(2):59–74. [doi:10.1007/bf02844004](https://doi.org/10.1007/bf02844004) *(abstract or second-hand only)*
- Malizia F, Blocken B (2020). *Bicycle aerodynamics: History, state-of-the-art and future perspectives.* Journal of Wind Engineering and Industrial Aerodynamics 200:104134. [doi:10.1016/j.jweia.2020.104134](https://doi.org/10.1016/j.jweia.2020.104134)
- Malizia F, Blocken B (2021). *Cyclist aerodynamics through time: Better, faster, stronger.* Journal of Wind Engineering and Industrial Aerodynamics 214:104673. [doi:10.1016/j.jweia.2021.104673](https://doi.org/10.1016/j.jweia.2021.104673)
- Martin JC, Gardner AS, Barras M, Martin DT (2006). *Aerodynamic drag area of cyclists determined with field-based measures.* Sportscience 10:68–69.
- Martin JC, Gardner AS, Barras M, Martin DT (2006). *Modeling Sprint Cycling Using Field-Derived Parameters and Forward Integration.* Medicine & Science in Sports & Exercise 38(3):592–597. [doi:10.1249/01.mss.0000193560.34022.04](https://doi.org/10.1249/01.mss.0000193560.34022.04) *(abstract or second-hand only)*
- Oggiano L, Brownlie L, Troynikov O, Bardal LM, Sæter C, Sætran L (2013). *A Review on Skin Suits and Sport Garment Aerodynamics: Guidelines and State of the Art.* Procedia Engineering 60:91–98. [doi:10.1016/j.proeng.2013.07.018](https://doi.org/10.1016/j.proeng.2013.07.018) *(abstract or second-hand only)*
- Padilla S, Mujika I, Angulo F, Goiriena JJ (2000). *Scientific approach to the 1-h cycling world record: a case study.* Journal of Applied Physiology 89(4):1522–1527. [doi:10.1152/jappl.2000.89.4.1522](https://doi.org/10.1152/jappl.2000.89.4.1522)
- Peterman JE, Lim AC, Ignatz RI, Edwards AG, Byrnes WC (2015). *Field-measured drag area is a key correlate of level cycling time trial performance.* PeerJ 3:e1144. [doi:10.7717/peerj.1144](https://doi.org/10.7717/peerj.1144)

**Power meters, elevation data and field measurement**

- Berjisian E, Bigazzi A, Barkh H (2023). *By cyclists, for cyclists: Road grade and elevation estimation from crowd-sourced fitness application data.* PLOS ONE 18(12):e0295027. [doi:10.1371/journal.pone.0295027](https://doi.org/10.1371/journal.pone.0295027)
- Bouillod A, Soto-Romero G, Grappe F, Bertucci W, Brunet E, Cassirame J (2022). *Caveats and Recommendations to Assess the Validity and Reliability of Cycling Power Meters: A Systematic Scoping Review.* Sensors 22(1):386. [doi:10.3390/s22010386](https://doi.org/10.3390/s22010386)
- Chung R (2012). *Estimating CdA with a power meter* (virtual elevation method). Presentation, not peer reviewed.
- Dyer B, Disley BX (2018). *Validation of the virtual elevation field test method when assessing the aerodynamics of para-cyclists with a uni-lateral trans-tibial amputation.* Disability and Rehabilitation: Assistive Technology 13(2):107–111. [doi:10.1080/17483107.2017.1297857](https://doi.org/10.1080/17483107.2017.1297857)
- Maier T, Schmid L, Müller B, Steiner T, Wehrlin J (2017). *Accuracy of Cycling Power Meters against a Mathematical Model of Treadmill Cycling.* International Journal of Sports Medicine 38(06):456–461. [doi:10.1055/s-0043-102945](https://doi.org/10.1055/s-0043-102945) *(abstract or second-hand only)*
- Menaspà P, Haakonssen E, Sharma A, Clark B (2016). *Accuracy in measurement of elevation gain in road cycling.* Journal of Science and Cycling 5(1):10–12. *(abstract or second-hand only)*
- Menaspà P, Impellizzeri FM, Haakonssen EC, Martin DT, Abbiss CR (2014). *Consistency of Commercial Devices for Measuring Elevation Gain.* International Journal of Sports Physiology and Performance 9(5):884–886. [doi:10.1123/ijspp.2013-0232](https://doi.org/10.1123/ijspp.2013-0232) *(abstract or second-hand only)*
